"""Startup health checks (used by sdr_device operation=health and web API)."""

from __future__ import annotations

from typing import Any

from ..capture import SDRCapture
from ..gnuradio_client import GnuradioClient


async def run_health_checks() -> dict[str, Any]:
    """Aggregate RTL-SDR and GNU Radio sidecar health."""
    client = GnuradioClient()
    gnuradio_ok = await client.is_reachable()
    devices = SDRCapture.list_devices()
    hardware_ok = SDRCapture.is_available()

    return {
        "success": True,
        "status": "ok" if hardware_ok or gnuradio_ok else "degraded",
        "rtl_sdr": {
            "available": hardware_ok,
            "device_count": len(devices),
            "devices": devices,
        },
        "gnuradio_sidecar": {
            "reachable": gnuradio_ok,
            "service_url": client.base_url,
        },
    }
