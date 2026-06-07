"""
SDR WebSocket Server Module

Provides real-time streaming of spectrum data and FM audio to web clients.
"""

from __future__ import annotations

import asyncio
import json
import logging

import websockets
from websockets.exceptions import ConnectionClosed

from .audio_stream import get_audio_relay
from .fm_demod import demod_fm_mono
from .handlers.state import get_sdr_capture, get_sdr_processor, set_mock_mode, should_use_mock
from .processor import SDRProcessor

logger = logging.getLogger(__name__)

AUDIO_SAMPLE_RATE = 48_000


class SDRWebSocketServer:
    """WebSocket server for real-time SDR spectrum and audio streaming."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.connected_clients: set[websockets.WebSocketServerProtocol] = set()
        self.is_running = False
        self.capture_task: asyncio.Task | None = None
        self.audio_task: asyncio.Task | None = None
        self.audio_enabled = True
        self._loop: asyncio.AbstractEventLoop | None = None
        self._audio_queue: asyncio.Queue[bytes] = asyncio.Queue(maxsize=32)
        self._relay = get_audio_relay()
        self._relay_subscribed = False

    @property
    def sdr_capture(self):
        return get_sdr_capture()

    @property
    def processor(self) -> SDRProcessor:
        return get_sdr_processor()

    def _on_sidecar_audio(self, data: bytes) -> None:
        if not self.audio_enabled or not self._loop:
            return
        try:
            self._loop.call_soon_threadsafe(self._enqueue_audio, data)
        except RuntimeError:
            pass

    def _enqueue_audio(self, data: bytes) -> None:
        try:
            self._audio_queue.put_nowait(data)
        except asyncio.QueueFull:
            try:
                self._audio_queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                self._audio_queue.put_nowait(data)
            except asyncio.QueueFull:
                pass

    def _ensure_relay_subscription(self) -> None:
        if not self._relay_subscribed:
            self._relay.subscribe(self._on_sidecar_audio)
            self._relay_subscribed = True

    async def initialize_sdr(self) -> bool:
        """Initialize SDR hardware or fall back to mock IQ."""
        capture = self.sdr_capture
        if should_use_mock():
            return await capture.initialize()

        if await capture.initialize():
            return True

        logger.warning("RTL-SDR init failed — enabling mock IQ for WebSocket stream")
        set_mock_mode(True)
        return await get_sdr_capture().initialize()

    async def start_capture_loop(self):
        """Main capture and processing loop."""
        logger.info("Starting SDR capture loop with FM audio")

        while self.is_running:
            try:
                samples = await self.sdr_capture.read_samples(1024 * 1024)

                if samples is not None:
                    spectrum_data = self.processor.process_samples(samples)

                    if self.connected_clients:
                        await self._broadcast(json.dumps(spectrum_data))

                    if (
                        self.audio_enabled
                        and self.connected_clients
                        and not self._relay.running
                    ):
                        pcm = demod_fm_mono(samples, float(self.sdr_capture.sample_rate))
                        if pcm.size:
                            await self._broadcast_binary(pcm.tobytes())

                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error("Error in capture loop: %s", e, exc_info=True)
                await asyncio.sleep(1)

    async def start_audio_loop(self):
        """Drain sidecar UDP audio into WebSocket clients."""
        while self.is_running:
            try:
                data = await asyncio.wait_for(self._audio_queue.get(), timeout=0.2)
            except TimeoutError:
                continue
            if self.audio_enabled and self.connected_clients:
                await self._broadcast_binary(data)

    async def _broadcast(self, message: str):
        disconnected_clients = set()

        for client in self.connected_clients:
            try:
                await client.send(message)
            except ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error("Error sending to client: %s", e, exc_info=True)
                disconnected_clients.add(client)

        self.connected_clients -= disconnected_clients

    async def _broadcast_binary(self, payload: bytes):
        disconnected_clients = set()

        for client in self.connected_clients:
            try:
                await client.send(payload)
            except ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error("Error sending audio to client: %s", e, exc_info=True)
                disconnected_clients.add(client)

        self.connected_clients -= disconnected_clients

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        logger.info("New SDR client connected: %s", websocket.remote_address)
        self.connected_clients.add(websocket)

        try:
            config = {
                "type": "config",
                "sdr_info": self.sdr_capture.get_info(),
                "mock_mode": should_use_mock(),
                "fft_size": self.processor.fft_size,
                "sample_rate": self.processor.sample_rate,
                "audio": {
                    "enabled": self.audio_enabled,
                    "sample_rate": AUDIO_SAMPLE_RATE,
                    "mode": "fm",
                    "sidecar_active": self._relay.running,
                },
            }
            await websocket.send(json.dumps(config))

            async for message in websocket:
                try:
                    data = json.loads(message)
                    if data.get("type") == "command":
                        await self._handle_command(data, websocket)
                except json.JSONDecodeError:
                    logger.warning("Invalid JSON received: %s", message)

        except ConnectionClosed:
            logger.info("SDR client disconnected: %s", websocket.remote_address)
        except Exception as e:
            logger.error("Error handling SDR client: %s", e, exc_info=True)
        finally:
            self.connected_clients.discard(websocket)

    async def _handle_command(self, data: dict, websocket: websockets.WebSocketServerProtocol):
        command = data.get("command")
        params = data.get("params", {})

        try:
            if command == "set_frequency":
                frequency = params.get("frequency")
                if frequency:
                    success = await self.sdr_capture.set_frequency(float(frequency))
                    response = {"type": "response", "command": command, "success": success}
                    await websocket.send(json.dumps(response))

            elif command == "set_gain":
                gain = params.get("gain")
                if gain:
                    success = await self.sdr_capture.set_gain(gain)
                    response = {"type": "response", "command": command, "success": success}
                    await websocket.send(json.dumps(response))

            elif command == "clear_waterfall":
                self.processor.clear_waterfall()
                response = {"type": "response", "command": command, "success": True}
                await websocket.send(json.dumps(response))

            elif command == "set_audio":
                enabled = params.get("enabled")
                if enabled is not None:
                    self.audio_enabled = bool(enabled)
                    response = {
                        "type": "response",
                        "command": command,
                        "success": True,
                        "audio_enabled": self.audio_enabled,
                    }
                    await websocket.send(json.dumps(response))

        except Exception as e:
            logger.error("Error handling command %s: %s", command, e, exc_info=True)
            response = {"type": "error", "command": command, "message": str(e)}
            await websocket.send(json.dumps(response))

    async def start(self):
        if not await self.initialize_sdr():
            logger.error("Failed to initialize SDR - server not starting")
            return

        self._loop = asyncio.get_running_loop()
        self._ensure_relay_subscription()
        self.is_running = True
        self.capture_task = asyncio.create_task(self.start_capture_loop())
        self.audio_task = asyncio.create_task(self.start_audio_loop())

        try:
            server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10,
            )

            logger.info(
                "SDR WebSocket server started on ws://%s:%s (spectrum + FM audio)",
                self.host,
                self.port,
            )

            await server.wait_closed()

        except Exception as e:
            logger.error("Error starting SDR WebSocket server: %s", e, exc_info=True)
        finally:
            self.is_running = False
            for task in (self.capture_task, self.audio_task):
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass

            await self.sdr_capture.close()

    async def stop(self):
        logger.info("Stopping SDR WebSocket server")
        self.is_running = False

        for client in self.connected_clients.copy():
            try:
                await client.close()
            except Exception:
                pass

        self.connected_clients.clear()

        for task in (self.capture_task, self.audio_task):
            if task:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

        await self.sdr_capture.close()
