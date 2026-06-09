"""Spectrum and streaming handlers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from . import state
from .state import get_sdr_capture, get_sdr_processor, should_use_mock

logger = logging.getLogger(__name__)


async def get_spectrum() -> dict[str, Any]:
    """Get current spectrum data with conversational analysis and AI sampling."""
    try:
        capture = get_sdr_capture()
        processor = get_sdr_processor()

        if should_use_mock() and getattr(capture, "sdr", None) is None:
            await capture.initialize()

        samples = await capture.read_samples(1024 * 1024)

        if samples is None:
            return {
                "status": "no_data",
                "conversation": {
                    "message": "No signal samples available. The SDR might not be initialized yet.",
                    "suggestions": [
                        "First run: sdr_device(operation='initialize')",
                        "Or enable mock: sdr_device(operation='mock_mode', mock_enabled=True)",
                        "Auto mock activates when no RTL-SDR is detected",
                    ],
                    "educational_note": "Spectrum analysis requires active signal capture. Think of this as tuning a radio before you can hear the stations!",
                },
            }

        spectrum_data = processor.process_samples(samples)
        center_freq = capture.center_freq / 1e6

        if spectrum_data.get("spectrum"):
            spectrum = spectrum_data["spectrum"]
            max_power = max(spectrum)
            avg_power = sum(spectrum) / len(spectrum)
            signal_peaks = sum(1 for p in spectrum if p > avg_power + 10)

            analysis = {
                "signal_count": signal_peaks,
                "peak_power": round(max_power, 1),
                "average_power": round(avg_power, 1),
                "dynamic_range": round(max_power - min(spectrum), 1),
            }

            if signal_peaks > 5:
                conversation_msg = f"Rich spectrum! Detected {signal_peaks} signals around {center_freq:.1f} MHz."
                expertise_level = "advanced"
            elif signal_peaks > 0:
                conversation_msg = f"Found {signal_peaks} signal(s) in the {center_freq:.1f} MHz range."
                expertise_level = "intermediate"
            else:
                conversation_msg = f"Quiet spectrum at {center_freq:.1f} MHz. This might be a good baseline for signal detection."
                expertise_level = "beginner"

            return {
                "status": "success",
                "mock_mode": should_use_mock(),
                "spectrum_data": spectrum_data,
                "frequency_mhz": center_freq,
                "analysis": analysis,
                "conversation": {
                    "message": conversation_msg,
                    "expertise_level": expertise_level,
                    "next_actions": [
                        "Try: sdr_get_waterfall() for time-varying signals",
                        "Tune to: sdr_tune_preset('orf_longwave')",
                        "Scan range: sdr_scan_frequencies(0.15, 0.3, 0.01)",
                    ],
                    "technical_insight": f"This {center_freq:.1f} MHz capture shows a {analysis['dynamic_range']} dB dynamic range. "
                    f"The peak signal is {analysis['peak_power']} dB, suggesting "
                    f"{'strong local signals' if analysis['peak_power'] > -20 else 'distant or weak transmissions'}.",
                },
                "sampling": {
                    "fft_size": processor.fft_size,
                    "sample_rate": capture.sample_rate,
                    "bandwidth": capture.sample_rate / processor.fft_size,
                    "frequency_resolution": capture.sample_rate / processor.fft_size,
                    "data_points": len(spectrum_data.get("spectrum", [])),
                },
            }
        else:
            return {
                "status": "processing_error",
                "conversation": {
                    "message": "Spectrum processing completed but no valid data returned.",
                    "troubleshooting": [
                        "Check SDR initialization",
                        "Verify frequency settings",
                        "Try different gain settings",
                    ],
                },
            }

    except Exception as e:
        logger.error("Error getting spectrum: %s", e, exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Spectrum analysis failed: {e}",
                "recovery_suggestions": [
                    "Reinitialize SDR: sdr_initialize()",
                    "Check hardware connection",
                    "Try different frequency range",
                ],
            },
            "error": str(e),
        }


async def get_waterfall() -> dict[str, Any]:
    """Get current waterfall display data."""
    try:
        processor = get_sdr_processor()
        if not processor.get_waterfall_data() and should_use_mock():
            await get_spectrum()

        waterfall_data = processor.get_waterfall_data()

        return {
            "success": True,
            "mock_mode": should_use_mock(),
            "waterfall_data": waterfall_data,
            "lines_count": len(waterfall_data),
            "message": f"Waterfall data with {len(waterfall_data)} lines retrieved",
        }
    except Exception as e:
        logger.error("Error getting waterfall: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


async def start_websocket_server(host: str = "localhost", port: int = 8765) -> dict[str, Any]:
    """Start the WebSocket server for real-time spectrum streaming."""
    try:
        from ..websocket_server import SDRWebSocketServer

        if state._websocket_server is None:
            state._websocket_server = SDRWebSocketServer(host=host, port=port)

        if state._websocket_task and not state._websocket_task.done():
            return {
                "success": True,
                "already_running": True,
                "websocket_url": f"ws://{host}:{port}",
                "message": f"WebSocket server already running on ws://{host}:{port}",
            }

        state._websocket_task = asyncio.create_task(state._websocket_server.start())

        return {
            "success": True,
            "websocket_url": f"ws://{host}:{port}",
            "message": f"WebSocket server started on ws://{host}:{port}",
        }
    except Exception as e:
        logger.error("Error starting WebSocket server: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


async def stop_websocket_server() -> dict[str, Any]:
    """Stop the WebSocket server for real-time streaming."""
    try:
        if state._websocket_task and not state._websocket_task.done():
            state._websocket_task.cancel()
            try:
                await state._websocket_task
            except asyncio.CancelledError:
                pass
            state._websocket_task = None

        if state._websocket_server:
            await state._websocket_server.stop()
            state._websocket_server = None

        return {"success": True, "message": "WebSocket server stopped"}
    except Exception as e:
        logger.error("Error stopping WebSocket server: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


async def get_websocket_status() -> dict[str, Any]:
    """Report WebSocket server and FM audio relay status."""
    from ..audio_stream import get_audio_relay

    relay = get_audio_relay()
    running = bool(state._websocket_task and not state._websocket_task.done())
    return {
        "success": True,
        "websocket_running": running,
        "websocket_url": f"ws://{state._websocket_server.host}:{state._websocket_server.port}"
        if state._websocket_server
        else None,
        "connected_clients": len(state._websocket_server.connected_clients) if state._websocket_server else 0,
        "audio_relay_running": relay.running,
        "fm_demod": "native Python FM demod streams over WebSocket when sidecar UDP is inactive",
    }


async def get_audio_status() -> dict[str, Any]:
    """Describe native FM demod and sidecar audio paths."""
    from ..audio_stream import get_audio_relay

    relay = get_audio_relay()
    return {
        "success": True,
        "native_fm_demod": True,
        "websocket_audio": bool(state._websocket_task and not state._websocket_task.done()),
        "sidecar_udp_relay": relay.running,
        "sample_rate_hz": 48_000,
        "hint": "Start sdr_spectrum(operation='start_websocket') for browser/dashboard audio",
    }
