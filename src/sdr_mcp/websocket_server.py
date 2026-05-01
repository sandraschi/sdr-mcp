"""
SDR WebSocket Server Module

Provides real-time streaming of spectrum data to web clients.
"""

import asyncio
import json
import logging

import websockets
from websockets.exceptions import ConnectionClosed

from .capture import SDRCapture
from .processor import SDRProcessor

logger = logging.getLogger(__name__)


class SDRWebSocketServer:
    """WebSocket server for real-time SDR spectrum streaming."""

    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.sdr_capture = SDRCapture()
        self.processor = SDRProcessor()
        self.connected_clients: set[websockets.WebSocketServerProtocol] = set()
        self.is_running = False
        self.capture_task: asyncio.Task | None = None

    async def initialize_sdr(self) -> bool:
        """Initialize the SDR hardware."""
        return await self.sdr_capture.initialize()

    async def start_capture_loop(self):
        """Main capture and processing loop."""
        logger.info("Starting SDR capture loop")

        while self.is_running:
            try:
                # Read samples from SDR
                samples = await self.sdr_capture.read_samples(1024 * 1024)

                if samples is not None:
                    # Process samples
                    spectrum_data = self.processor.process_samples(samples)

                    # Send to all connected clients
                    if self.connected_clients:
                        message = json.dumps(spectrum_data)
                        await self._broadcast(message)

                # Small delay to prevent overwhelming the system
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error in capture loop: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _broadcast(self, message: str):
        """Broadcast message to all connected clients."""
        disconnected_clients = set()

        for client in self.connected_clients:
            try:
                await client.send(message)
            except ConnectionClosed:
                disconnected_clients.add(client)
            except Exception as e:
                logger.error(f"Error sending to client: {e}", exc_info=True)
                disconnected_clients.add(client)

        # Remove disconnected clients
        self.connected_clients -= disconnected_clients

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """Handle individual WebSocket client connections."""
        logger.info(f"New SDR client connected: {websocket.remote_address}")

        # Add client to connected set
        self.connected_clients.add(websocket)

        try:
            # Send initial configuration
            config = {
                'type': 'config',
                'sdr_info': self.sdr_capture.get_info(),
                'fft_size': self.processor.fft_size,
                'sample_rate': self.processor.sample_rate
            }
            await websocket.send(json.dumps(config))

            # Keep connection alive and handle commands
            async for message in websocket:
                try:
                    data = json.loads(message)

                    # Handle commands from client
                    if data.get('type') == 'command':
                        await self._handle_command(data, websocket)

                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON received: {message}")

        except ConnectionClosed:
            logger.info(f"SDR client disconnected: {websocket.remote_address}")
        except Exception as e:
            logger.error(f"Error handling SDR client: {e}", exc_info=True)
        finally:
            self.connected_clients.discard(websocket)

    async def _handle_command(self, data: dict, websocket: websockets.WebSocketServerProtocol):
        """Handle commands from web clients."""
        command = data.get('command')
        params = data.get('params', {})

        try:
            if command == 'set_frequency':
                frequency = params.get('frequency')
                if frequency:
                    success = await self.sdr_capture.set_frequency(float(frequency))
                    response = {'type': 'response', 'command': command, 'success': success}
                    await websocket.send(json.dumps(response))

            elif command == 'set_gain':
                gain = params.get('gain')
                if gain:
                    success = await self.sdr_capture.set_gain(gain)
                    response = {'type': 'response', 'command': command, 'success': success}
                    await websocket.send(json.dumps(response))

            elif command == 'clear_waterfall':
                self.processor.clear_waterfall()
                response = {'type': 'response', 'command': command, 'success': True}
                await websocket.send(json.dumps(response))

        except Exception as e:
            logger.error(f"Error handling command {command}: {e}", exc_info=True)
            response = {'type': 'error', 'command': command, 'message': str(e)}
            await websocket.send(json.dumps(response))

    async def start(self):
        """Start the WebSocket server."""
        if not await self.initialize_sdr():
            logger.error("Failed to initialize SDR - server not starting")
            return

        self.is_running = True

        # Start capture loop
        self.capture_task = asyncio.create_task(self.start_capture_loop())

        try:
            server = await websockets.serve(
                self.handle_client,
                self.host,
                self.port,
                ping_interval=30,
                ping_timeout=10
            )

            logger.info(f"SDR WebSocket server started on ws://{self.host}:{self.port}")

            # Keep server running
            await server.wait_closed()

        except Exception as e:
            logger.error(f"Error starting SDR WebSocket server: {e}", exc_info=True)
        finally:
            self.is_running = False
            if self.capture_task:
                self.capture_task.cancel()
                try:
                    await self.capture_task
                except asyncio.CancelledError:
                    pass

            await self.sdr_capture.close()

    async def stop(self):
        """Stop the WebSocket server."""
        logger.info("Stopping SDR WebSocket server")
        self.is_running = False

        # Close all client connections
        for client in self.connected_clients.copy():
            try:
                await client.close()
            except Exception:
                pass

        self.connected_clients.clear()

        if self.capture_task:
            self.capture_task.cancel()
            try:
                await self.capture_task
            except asyncio.CancelledError:
                pass

        await self.sdr_capture.close()
