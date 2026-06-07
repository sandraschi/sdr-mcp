"""UDP PCM relay from GNU Radio sidecar to speakers and WebSocket subscribers."""

from __future__ import annotations

import logging
import socket
import threading
from collections.abc import Callable
from typing import Any

import numpy as np

logger = logging.getLogger(__name__)

DEFAULT_AUDIO_HOST = "127.0.0.1"
DEFAULT_AUDIO_PORT = 7355
DEFAULT_AUDIO_RATE = 48_000

_relay: AudioRelay | None = None


class AudioRelay:
    """Listen for float32 mono PCM over UDP; fan out to subscribers and optional playback."""

    def __init__(
        self,
        host: str = DEFAULT_AUDIO_HOST,
        port: int = DEFAULT_AUDIO_PORT,
        sample_rate: int = DEFAULT_AUDIO_RATE,
        playback: bool = True,
    ) -> None:
        self.host = host
        self.port = port
        self.sample_rate = sample_rate
        self.playback = playback
        self._subscribers: list[Callable[[bytes], None]] = []
        self._thread: threading.Thread | None = None
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._output_stream: Any = None

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def subscribe(self, callback: Callable[[bytes], None]) -> None:
        with self._lock:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

    def unsubscribe(self, callback: Callable[[bytes], None]) -> None:
        with self._lock:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._open_playback()
        self._thread = threading.Thread(target=self._listen_loop, name="sdr-audio-relay", daemon=True)
        self._thread.start()
        logger.info("Audio relay listening on udp://%s:%s", self.host, self.port)

    def stop(self) -> None:
        self._stop.set()
        if self._thread:
            self._thread.join(timeout=2.0)
            self._thread = None
        self._close_playback()
        logger.info("Audio relay stopped")

    def _open_playback(self) -> None:
        if not self.playback:
            return
        try:
            import sounddevice as sd

            self._output_stream = sd.OutputStream(
                channels=1,
                samplerate=self.sample_rate,
                dtype="float32",
                blocksize=0,
            )
            self._output_stream.start()
        except Exception as exc:
            logger.warning("Local speaker playback unavailable: %s", exc)
            self._output_stream = None

    def _close_playback(self) -> None:
        if self._output_stream is not None:
            try:
                self._output_stream.stop()
                self._output_stream.close()
            except Exception:
                pass
            self._output_stream = None

    def _listen_loop(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((self.host, self.port))
            sock.settimeout(0.5)
            while not self._stop.is_set():
                try:
                    data, _addr = sock.recvfrom(65_536)
                except TimeoutError:
                    continue
                except OSError:
                    if self._stop.is_set():
                        break
                    continue
                if not data:
                    continue
                self._dispatch(data)
        finally:
            sock.close()

    def _dispatch(self, data: bytes) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for callback in subscribers:
            try:
                callback(data)
            except Exception as exc:
                logger.debug("Audio subscriber error: %s", exc)
        if self._output_stream is not None:
            try:
                pcm = np.frombuffer(data, dtype=np.float32)
                if pcm.size:
                    self._output_stream.write(pcm.reshape(-1, 1))
            except Exception as exc:
                logger.debug("Speaker write failed: %s", exc)


def get_audio_relay() -> AudioRelay:
    global _relay
    if _relay is None:
        _relay = AudioRelay()
    return _relay
