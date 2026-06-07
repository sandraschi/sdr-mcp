"""GNU Radio sidecar operation handlers."""

from __future__ import annotations

import logging
from typing import Any

from ..audio_stream import get_audio_relay
from ..capture import SDRCapture
from ..gnuradio_client import GnuradioClient, get_gnuradio_config
from .state import MAX_FREQ_MHZ, MIN_FREQ_MHZ, _sdr_semaphore

logger = logging.getLogger(__name__)

SUPPORTED_MODES = {"fm", "am", "usb", "lsb"}
SUPPORTED_SOURCES = {"rtl_tcp", "hackrf"}


async def handle_gnuradio_operation(
    operation: str,
    mode: str = "fm",
    source: str = "rtl_tcp",
    frequency_mhz: float | None = None,
    rtl_tcp_host: str | None = None,
    rtl_tcp_port: int | None = None,
    gain: float = 20.0,
) -> dict[str, Any]:
    """Control the GNU Radio demod sidecar (Docker + rtl_tcp)."""
    client = GnuradioClient()
    config = get_gnuradio_config()

    try:
        if operation == "list_devices":
            devices = SDRCapture.list_devices()
            available = SDRCapture.is_available()
            return {
                "status": "success" if available and devices else "no_devices",
                "available": available,
                "device_count": len(devices),
                "devices": devices,
                "source": source,
            }

        if operation == "health":
            healthy = await client.is_reachable()
            return {
                "status": "success" if healthy else "unreachable",
                "service_url": config["service_url"],
                "conversation": {
                    "message": (
                        "GNU Radio sidecar is online."
                        if healthy
                        else "GNU Radio sidecar not reachable. Run: just gnuradio-up"
                    ),
                    "next_steps": [
                        "Start rtl_tcp: scripts/start-rtl-tcp.ps1",
                        "Start sidecar: just gnuradio-up",
                        "Start demod: sdr_gnuradio(operation='start', frequency_mhz=101.5)",
                    ],
                },
            }

        if operation == "status":
            result = await client.status()
            return {
                "status": "success",
                "demod": result,
                "conversation": {
                    "message": "Demod flowgraph is running." if result.get("running") else "No active GNU Radio demod process."
                },
            }

        if operation == "stop":
            result = await client.stop_demod()
            get_audio_relay().stop()
            return {
                "status": "success",
                "result": result,
                "conversation": {"message": "GNU Radio demod stopped."},
            }

        if operation == "start":
            if frequency_mhz is None:
                return {
                    "status": "error",
                    "message": "frequency_mhz is required for start",
                }
            if not (MIN_FREQ_MHZ <= frequency_mhz <= MAX_FREQ_MHZ):
                return {
                    "status": "error",
                    "message": f"Frequency must be {MIN_FREQ_MHZ}-{MAX_FREQ_MHZ} MHz",
                }
            if mode not in SUPPORTED_MODES:
                return {
                    "status": "error",
                    "message": f"Unsupported mode: {mode}. Supported: {', '.join(sorted(SUPPORTED_MODES))}",
                }
            if source not in SUPPORTED_SOURCES:
                return {
                    "status": "error",
                    "message": f"Unsupported source: {source}. Supported: {', '.join(sorted(SUPPORTED_SOURCES))}",
                }

            async with _sdr_semaphore:
                result = await client.start_demod(
                    mode=mode,
                    source=source,
                    frequency_hz=frequency_mhz * 1e6,
                    rtl_tcp_host=rtl_tcp_host,
                    rtl_tcp_port=rtl_tcp_port,
                    gain=gain,
                )
            get_audio_relay().start()
            return {
                "status": "success",
                "result": result,
                "audio": {
                    "udp_port": get_audio_relay().port,
                    "playback": "speakers + browser when WebSocket connected",
                },
                "conversation": {
                    "message": (
                        f"Started {mode.upper()} demod at {frequency_mhz} MHz "
                        f"via GNU Radio ({source}). Audio streams to speakers and the dashboard."
                    ),
                    "rtl_tcp": {
                        "host": rtl_tcp_host or config["rtl_tcp_host"],
                        "port": rtl_tcp_port or config["rtl_tcp_port"],
                    },
                    "source": source,
                    "next_steps": [
                        "Check status: sdr_gnuradio(operation='status')",
                        "Stop demod: sdr_gnuradio(operation='stop')",
                    ],
                },
            }

        return {
            "status": "error",
            "message": f"Unknown operation: {operation}",
            "valid_operations": ["health", "status", "start", "stop", "list_devices"],
        }
    except Exception as e:
        logger.error("GNU Radio operation failed: %s", e, exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "conversation": {
                "message": f"GNU Radio sidecar error: {e}",
                "setup_steps": [
                    "Start rtl_tcp on host: scripts/start-rtl-tcp.ps1",
                    "Start container: just gnuradio-up",
                    "Verify health: sdr_gnuradio(operation='health')",
                ],
            },
        }
