"""Device-oriented SDR business logic handlers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from ..capture import SDRCapture
from ..frequency_db import Band, get_frequency_database
from .state import (
    MAX_FREQ_MHZ,
    MIN_FREQ_MHZ,
    _sdr_semaphore,
    get_mock_mode_label,
    get_sdr_capture,
    get_sdr_processor,
    set_mock_mode,
    should_use_mock,
)

logger = logging.getLogger(__name__)


async def list_devices() -> dict[str, Any]:
    """List all available RTL-SDR devices with conversational guidance."""
    try:
        devices = SDRCapture.list_devices()
        available = SDRCapture.is_available()

        if should_use_mock():
            return {
                "status": "success",
                "available": True,
                "mock_mode": True,
                "mock_setting": get_mock_mode_label(),
                "hardware_detected": available,
                "device_count": 1,
                "devices": [{"index": 0, "serial": "MOCK-0001", "mock": True}],
                "conversation": {
                    "message": "Mock SDR active — synthetic IQ drives FFT and waterfall without a dongle.",
                    "next_steps": [
                        "Run sdr_spectrum(operation='spectrum') for a demo FFT",
                        "Run sdr_spectrum(operation='start_websocket') for live dashboard plots",
                        "Use sdr_device(operation='mock_mode', mock_enabled=False) when hardware is connected",
                    ],
                    "expert_tip": "Tones drift slowly so the waterfall is not a flat slab. "
                    "Set SDR_MCP_MOCK=enable|disable|auto to control startup behavior.",
                },
                "sampling": {
                    "demo_mode": True,
                    "source": "synthetic_iq",
                    "available_features": [
                        "spectrum",
                        "waterfall",
                        "websocket_stream",
                        "frequency_scan",
                        "station_presets",
                    ],
                },
            }

        if available and devices:
            return {
                "status": "success",
                "available": True,
                "device_count": len(devices),
                "devices": devices,
                "conversation": {
                    "message": f"Found {len(devices)} RTL-SDR device(s) ready for operation.",
                    "next_steps": [
                        "Run 'sdr_initialize()' to prepare the device",
                        "Try 'sdr_tune_preset(\"bbc_radio4\")' to listen to BBC longwave",
                        "Use 'sdr_get_spectrum()' to see real-time spectrum data",
                    ],
                    "expert_tip": "Your RTL-SDR is now ready for spectrum analysis. The device supports frequencies from 24 MHz to 1.766 GHz with excellent sensitivity.",
                },
                "sampling": {
                    "device_specs": {
                        "frequency_range": "24 MHz - 1.766 GHz",
                        "sample_rates": "up to 2.56 Msps",
                        "typical_sensitivity": "-70 dBm",
                    }
                },
            }
        else:
            return {
                "status": "no_devices",
                "available": False,
                "device_count": 0,
                "devices": [],
                "conversation": {
                    "message": "No RTL-SDR devices detected. Let's get you set up!",
                    "setup_steps": [
                        "1. Connect your RTL-SDR dongle via USB",
                        "2. Install Zadig drivers (replace default DVB-T driver with WinUSB)",
                        "3. Restart this SDR session",
                        "4. Run 'sdr_check()' to verify installation",
                    ],
                    "troubleshooting": [
                        "Ensure USB cable is securely connected",
                        "Check device manager for driver conflicts",
                        "Try different USB ports",
                        "Verify RTL-SDR model compatibility",
                    ],
                    "fallback_message": "Don't have hardware? Mock mode activates automatically — try sdr_spectrum(operation='spectrum').",
                },
                "sampling": {
                    "demo_mode": True,
                    "available_features": ["frequency_presets", "signal_analysis_concepts"],
                },
            }
    except Exception as e:
        logger.error("Error listing SDR devices: %s", e, exc_info=True)
        return {
            "status": "error",
            "available": False,
            "device_count": 0,
            "devices": [],
            "conversation": {
                "message": f"Encountered an issue while checking for SDR devices: {e}",
                "suggestions": [
                    "Check USB connections",
                    "Verify driver installation",
                    "Try running as administrator",
                    "Check system logs for USB errors",
                ],
            },
            "error": str(e),
        }


async def initialize(device_index: int = 0) -> dict[str, Any]:
    """Initialize the SDR device for operation."""
    del device_index
    try:
        capture = get_sdr_capture()
        success = await capture.initialize()

        if success:
            info = capture.get_info()
            return {
                "success": True,
                "device_info": info,
                "message": f"SDR device initialized successfully at {info['center_freq'] / 1e6:.1f} MHz",
            }
        else:
            return {
                "success": False,
                "message": "Failed to initialize SDR device. Check hardware connection and drivers.",
            }
    except Exception as e:
        logger.error("Error initializing SDR: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


async def set_frequency(frequency_mhz: float) -> dict[str, Any]:
    """Set the center frequency for SDR capture."""
    try:
        if frequency_mhz < MIN_FREQ_MHZ or frequency_mhz > MAX_FREQ_MHZ:
            return {
                "success": False,
                "frequency_mhz": frequency_mhz,
                "error": f"Frequency {frequency_mhz:.1f} MHz out of range ({MIN_FREQ_MHZ}-{MAX_FREQ_MHZ} MHz)",
                "message": f"Frequency must be between {MIN_FREQ_MHZ} MHz and {MAX_FREQ_MHZ} MHz",
            }
        capture = get_sdr_capture()
        frequency_hz = frequency_mhz * 1e6

        async with _sdr_semaphore:
            success = await capture.set_frequency(frequency_hz)

        return {
            "success": success,
            "frequency_mhz": frequency_mhz,
            "frequency_hz": frequency_hz,
            "message": f"Frequency set to {frequency_mhz:.1f} MHz" if success else "Failed to set frequency",
        }
    except Exception as e:
        logger.error("Error setting frequency: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


async def set_gain(gain: str = "auto") -> dict[str, Any]:
    """Set the SDR gain level."""
    try:
        if gain != "auto":
            try:
                gain_val = float(gain)
                if gain_val < 0 or gain_val > 49.6:
                    return {
                        "success": False,
                        "gain": gain,
                        "error": "Gain value out of range (0-49.6 dB)",
                        "message": "Gain must be 'auto' or between 0 and 49.6 dB",
                    }
            except ValueError:
                return {
                    "success": False,
                    "gain": gain,
                    "error": f"Invalid gain value: {gain}",
                    "message": "Gain must be 'auto' or a numeric value in dB",
                }
        capture = get_sdr_capture()
        async with _sdr_semaphore:
            success = await capture.set_gain(gain)

        return {"success": success, "gain": gain, "message": f"Gain set to {gain}" if success else "Failed to set gain"}
    except Exception as e:
        logger.error("Error setting gain: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


async def tune_preset(preset_name: str) -> dict[str, Any]:
    """Tune to a predefined frequency preset with rich conversational guidance."""
    try:
        db = get_frequency_database()

        station = None
        if preset_name.upper() in db.stations:
            station = db.stations[preset_name.upper()]
        else:
            for s in db.get_all_stations():
                if preset_name.lower() in s.name.lower() or preset_name.lower() in s.callsign.lower():
                    station = s
                    break

        if not station:
            lw_stations = db.get_stations_by_band(Band.LONGWAVE)
            available_presets = [
                {"callsign": s.callsign, "name": s.name, "frequency": f"{s.frequency_mhz:.1f} MHz"}
                for s in lw_stations[:5]
            ]

            return {
                "status": "station_not_found",
                "conversation": {
                    "message": f"I couldn't find '{preset_name}' in our station database.",
                    "longwave_stations": available_presets,
                    "suggestions": [
                        f"Try: sdr_tune_preset('{lw_stations[0].callsign}') for {lw_stations[0].name}" if lw_stations else "",
                        "Use: sdr_search_stations('BBC') to search by name",
                        "Try: sdr_get_stations_by_band('LW') for all longwave stations",
                        "Use: sdr_set_frequency(198.0) for manual tuning to 198 MHz",
                    ],
                    "educational_note": "Our database contains verified frequencies and program schedules for major international broadcasters.",
                },
            }

        frequency_mhz = station.frequency_mhz
        frequency_khz = station.frequency_khz

        capture = get_sdr_capture()
        success = await capture.set_frequency(station.frequency)

        if success:
            station_info = {
                "orf_longwave": {
                    "personality": "ORF (Austrian Broadcasting) - Classical music, news, and cultural programming from Vienna.",
                    "signal_characteristics": "Strong ground wave propagation across Central Europe.",
                    "listening_tips": "Best reception in evenings when ionospheric conditions enhance longwave signals.",
                    "historical_note": "ORF longwave has been broadcasting since 1962, serving as a cultural bridge across the Alps.",
                },
                "bbc_radio4": {
                    "personality": "BBC Radio 4 - Intellectual discourse, drama, comedy, and comprehensive news from the UK's public broadcaster.",
                    "signal_characteristics": "Powerful 500kW transmitter from Droitwich, receivable across Europe and beyond.",
                    "listening_tips": "Excellent for news and current affairs. The longwave signal is remarkably stable.",
                    "historical_note": "BBC longwave service began in 1978, continuing the tradition of the BBC Home Service.",
                },
                "france_inter": {
                    "personality": "France Inter - Eclectic mix of news, culture, music, and intellectual programming.",
                    "signal_characteristics": "Allouis transmitter provides reliable coverage across Western Europe.",
                    "listening_tips": "Features excellent music discovery and in-depth cultural discussions.",
                    "historical_note": "France Inter evolved from Radiodiffusion Francaise, maintaining longwave service since 1963.",
                },
                "rtl_luxembourg": {
                    "personality": "RTL Luxembourg - Entertainment, music, and information in multiple languages.",
                    "signal_characteristics": "Junglinster transmitter covers Luxembourg and surrounding regions.",
                    "listening_tips": "Great for multilingual European news and entertainment.",
                    "historical_note": "RTL began longwave broadcasting in 1955, pioneering commercial radio in Europe.",
                },
            }

            station_data = station_info.get(preset_name, {})

            return {
                "status": "tuned",
                "preset": preset_name,
                "station": station.name,
                "callsign": station.callsign,
                "frequency_khz": frequency_khz,
                "frequency_mhz": frequency_mhz,
                "band": station.band.value,
                "country": station.country,
                "city": station.city,
                "description": station.description,
                "conversation": {
                    "message": f"Tuned to {station.name} at {frequency_mhz:.3f} MHz ({frequency_khz:.0f} kHz)!",
                    "station_personality": station_data.get("personality", ""),
                    "signal_info": station_data.get("signal_characteristics", ""),
                    "listening_guide": station_data.get("listening_tips", ""),
                    "historical_context": station_data.get("historical_note", ""),
                    "next_steps": [
                        "Run: sdr_get_spectrum() to see the signal",
                        "Try: sdr_get_waterfall() for signal stability",
                        "Listen via: sdr_start_websocket_server() for real-time monitoring",
                    ],
                    "technical_details": {
                        "frequency": f"{frequency_mhz:.3f} MHz ({frequency_khz:.0f} kHz)",
                        "band": station.band.value,
                        "propagation": "Ground wave + sky wave at night",
                        "typical_range": "500-2000 km depending on conditions",
                    },
                },
                "sampling": {
                    "expected_signal_strength": "Strong longwave signals typically -30 to -60 dBm",
                    "bandwidth": "9 kHz AM modulation",
                    "modulation": "Amplitude Modulation (AM)",
                    "content_type": "Voice, music, news programming",
                },
            }
        else:
            return {
                "status": "tuning_failed",
                "conversation": {
                    "message": f"Could not tune to {station.name} at {frequency_mhz:.3f} MHz.",
                    "possible_issues": [
                        "SDR device not initialized - try sdr_initialize()",
                        "Hardware connection problem",
                        "Frequency out of device range",
                        "Driver or permissions issue",
                    ],
                    "alternatives": [
                        f"Try manual tuning: sdr_set_frequency({frequency_mhz})",
                        "Check device status: sdr_get_status()",
                        "List devices: sdr_list_devices()",
                    ],
                },
            }
    except Exception as e:
        logger.error("Error tuning preset: %s", e, exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Tuning operation failed: {e}",
                "troubleshooting": [
                    "Ensure SDR is initialized",
                    "Check frequency range compatibility",
                    "Verify hardware connections",
                ],
            },
            "error": str(e),
        }


async def get_status() -> dict[str, Any]:
    """Get current SDR status and configuration."""
    try:
        capture = get_sdr_capture()
        info = capture.get_info()

        return {
            "success": True,
            "device_info": info,
            "mock_mode": bool(info.get("mock")),
            "mock_setting": get_mock_mode_label(),
            "available_presets": {"note": "Use sdr_get_stations_by_band('LW') for longwave presets"},
            "message": "SDR status retrieved successfully",
        }
    except Exception as e:
        logger.error("Error getting status: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


async def configure_mock_mode(mock_enabled: bool | None = None) -> dict[str, Any]:
    """Enable, disable, or query mock IQ mode (None = auto when no dongle)."""
    try:
        if mock_enabled is not None:
            set_mock_mode(mock_enabled)

        active = should_use_mock()
        capture = get_sdr_capture()
        if active:
            await capture.initialize()

        return {
            "success": True,
            "mock_setting": get_mock_mode_label(),
            "mock_active": active,
            "hardware_available": SDRCapture.is_available(),
            "device_info": capture.get_info() if active else None,
            "message": (
                "Mock IQ generator active — spectrum and waterfall work without RTL-SDR."
                if active
                else "Hardware capture path selected — initialize RTL-SDR before spectrum."
            ),
            "env_hint": "Set SDR_MCP_MOCK=enable|disable|auto for startup default",
        }
    except Exception as e:
        logger.error("Error configuring mock mode: %s", e, exc_info=True)
        return {"success": False, "error": str(e)}


async def scan_frequencies(start_freq: float, end_freq: float, step_size: float = 1.0) -> dict[str, Any]:
    """Scan frequency range with AI-powered analysis and conversational reporting."""
    try:
        if start_freq < MIN_FREQ_MHZ or end_freq > MAX_FREQ_MHZ:
            return {
                "status": "invalid_range",
                "conversation": {
                    "message": f"Frequency range {start_freq:.1f}-{end_freq:.1f} MHz exceeds RTL-SDR limits ({MIN_FREQ_MHZ}-{MAX_FREQ_MHZ} MHz)"
                },
            }
        if start_freq >= end_freq:
            return {
                "status": "invalid_range",
                "conversation": {
                    "message": f"Start frequency ({start_freq:.1f} MHz) must be less than end frequency ({end_freq:.1f} MHz)"
                },
            }
        if step_size <= 0:
            return {
                "status": "invalid_range",
                "conversation": {"message": f"Step size must be positive (got {step_size})"},
            }
        capture = get_sdr_capture()
        processor = get_sdr_processor()

        results = []
        scan_start_time = asyncio.get_running_loop().time()
        current_freq = start_freq
        conversation_progress = []
        detected_signals = []

        while current_freq <= end_freq:
            await capture.set_frequency(current_freq * 1e6)
            await asyncio.sleep(0.1)

            samples = await capture.read_samples(512 * 1024)
            if samples is not None:
                spectrum_data = processor.process_samples(samples)
                spectrum = spectrum_data.get("spectrum", [])
                max_power = max(spectrum) if spectrum else -100

                result = {
                    "frequency_mhz": current_freq,
                    "max_power_db": round(max_power, 1),
                    "spectrum_data": spectrum_data,
                    "timestamp": asyncio.get_running_loop().time(),
                }
                results.append(result)

                if spectrum:
                    avg_power = sum(spectrum) / len(spectrum)
                    if max_power > avg_power + 15:
                        detected_signals.append({"frequency": current_freq, "power": max_power, "strength": "strong"})
                        conversation_progress.append(f"Strong signal detected at {current_freq:.1f} MHz")
                    elif max_power > avg_power + 5:
                        detected_signals.append({"frequency": current_freq, "power": max_power, "strength": "moderate"})

            current_freq += step_size

        scan_duration = asyncio.get_running_loop().time() - scan_start_time

        total_signals = len(detected_signals)
        strong_signals = len([s for s in detected_signals if s["strength"] == "strong"])

        if total_signals == 0:
            scan_assessment = "Quiet band - no significant signals detected."
            expertise_level = "beginner"
        elif strong_signals > 0:
            scan_assessment = f"Active band! Found {strong_signals} strong and {total_signals - strong_signals} moderate signals."
            expertise_level = "advanced"
        else:
            scan_assessment = f"Some activity detected - {total_signals} moderate signals found."
            expertise_level = "intermediate"

        band_analysis = {}
        if start_freq >= 0.15 and end_freq <= 0.3:
            band_analysis = {
                "band_name": "Longwave (LW)",
                "typical_use": "AM broadcasting, navigation beacons",
                "propagation": "Ground wave + night sky wave",
                "expected_signals": "International broadcasters, maritime navigation",
            }
        elif start_freq >= 0.5 and end_freq <= 1.6:
            band_analysis = {
                "band_name": "Medium Wave (MW)",
                "typical_use": "AM radio broadcasting",
                "propagation": "Ground wave + sky wave",
                "expected_signals": "Local and regional AM stations",
            }

        return {
            "status": "scan_complete",
            "scan_results": results,
            "scan_parameters": {
                "start_freq_mhz": start_freq,
                "end_freq_mhz": end_freq,
                "step_size_mhz": step_size,
                "total_steps": len(results),
                "scan_duration_seconds": round(scan_duration, 2),
            },
            "signal_analysis": {
                "total_signals_detected": total_signals,
                "strong_signals": strong_signals,
                "moderate_signals": total_signals - strong_signals,
                "detected_signals": detected_signals[:10],
            },
            "conversation": {
                "message": scan_assessment,
                "expertise_level": expertise_level,
                "scan_summary": f"Completed frequency sweep from {start_freq:.1f} to {end_freq:.1f} MHz in {scan_duration:.1f} seconds.",
                "key_findings": conversation_progress[-5:] if conversation_progress else ["Scan completed successfully"],
                "band_context": band_analysis,
                "next_recommendations": [
                    "Focus on strongest signals: " + ", ".join([f"{s['frequency']:.1f} MHz" for s in detected_signals[:3]])
                    if detected_signals
                    else "Try different frequency ranges",
                    "Use sdr_tune_preset() for known stations",
                    "Run sdr_get_waterfall() on interesting frequencies",
                    "Try narrower scan: step_size=0.1 for detailed analysis",
                ],
                "technical_notes": [
                    f"Average scan time per frequency: {scan_duration / len(results):.2f} seconds",
                    f"Dynamic range covered: {max([r['max_power_db'] for r in results]) - min([r['max_power_db'] for r in results]):.1f} dB",
                    "Signal detection threshold: 5-15 dB above average noise",
                ],
            },
            "sampling": {
                "scan_method": "FFT-based spectrum analysis",
                "sample_rate": capture.sample_rate,
                "fft_size": processor.fft_size,
                "frequency_resolution": capture.sample_rate / processor.fft_size,
                "processing_efficiency": f"{len(results) / scan_duration:.1f} frequencies/second",
            },
        }
    except Exception as e:
        logger.error("Error scanning frequencies: %s", e, exc_info=True)
        return {
            "status": "scan_error",
            "conversation": {
                "message": f"Frequency scanning failed: {e}",
                "possible_causes": [
                    "SDR device not initialized",
                    "Frequency range outside device capabilities",
                    "Hardware connection issues",
                    "Insufficient scan timing",
                ],
                "recovery_steps": [
                    "Initialize SDR: sdr_initialize()",
                    "Check device status: sdr_get_status()",
                    "Try smaller frequency ranges",
                    "Increase step delays if needed",
                ],
            },
            "error": str(e),
        }
