"""
HTTP client for the GNU Radio demod sidecar service.

The sidecar runs in Docker and connects to rtl_tcp on the Windows host.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import httpx

logger = logging.getLogger(__name__)

ENV_GNURADIO_URL = "GNURADIO_DEMOD_URL"
DEFAULT_GNURADIO_URL = "http://127.0.0.1:10900"
DEFAULT_RTL_TCP_HOST = "host.docker.internal"
DEFAULT_RTL_TCP_PORT = 1234


def get_gnuradio_config() -> dict[str, Any]:
    """Read GNU Radio sidecar configuration from environment."""
    return {
        "service_url": os.getenv(ENV_GNURADIO_URL, DEFAULT_GNURADIO_URL).rstrip("/"),
        "rtl_tcp_host": os.getenv("RTL_TCP_HOST", "127.0.0.1"),
        "rtl_tcp_port": int(os.getenv("RTL_TCP_PORT", str(DEFAULT_RTL_TCP_PORT))),
    }


class GnuradioClient:
    """Async client for the GNU Radio demod HTTP API."""

    def __init__(self, base_url: str | None = None, timeout: float = 10.0):
        config = get_gnuradio_config()
        self.base_url = (base_url or config["service_url"]).rstrip("/")
        self.timeout = timeout

    async def health(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()

    async def status(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/status")
            response.raise_for_status()
            return response.json()

    async def list_devices(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(f"{self.base_url}/devices")
            response.raise_for_status()
            return response.json()

    async def start_demod(
        self,
        *,
        mode: str,
        source: str = "rtl_tcp",
        frequency_hz: float,
        rtl_tcp_host: str | None = None,
        rtl_tcp_port: int | None = None,
        sample_rate: float = 2.0e6,
        gain: float = 20.0,
    ) -> dict[str, Any]:
        config = get_gnuradio_config()
        payload = {
            "mode": mode,
            "source": source,
            "frequency_hz": frequency_hz,
            "rtl_tcp_host": rtl_tcp_host or config["rtl_tcp_host"],
            "rtl_tcp_port": rtl_tcp_port or config["rtl_tcp_port"],
            "sample_rate": sample_rate,
            "gain": gain,
        }
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/demod/start", json=payload)
            response.raise_for_status()
            return response.json()

    async def stop_demod(self) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(f"{self.base_url}/demod/stop")
            response.raise_for_status()
            return response.json()

    async def is_reachable(self) -> bool:
        try:
            await self.health()
            return True
        except Exception as exc:
            logger.debug("GNU Radio sidecar unreachable: %s", exc)
            return False
