"""
SDR MCP Server

FastMCP server providing SDR (Software Defined Radio) tools for spectrum analysis,
frequency tuning, and real-time data streaming.
"""

import asyncio
import logging
from typing import Any

from fastmcp import FastMCP

from .transport import run_server_async
from .capture import SDRCapture
from .processor import SDRProcessor
from .frequency_db import get_frequency_database, Band, StationType
from .online_db import search_radio_browser, get_signal_info

logger = logging.getLogger(__name__)

# Rate limiter for SDR hardware operations
_sdr_semaphore = asyncio.Semaphore(5)

# Valid frequency range for RTL-SDR (24 MHz - 1.766 GHz)
MIN_FREQ_MHZ = 24.0
MAX_FREQ_MHZ = 1766.0
VALID_BANDS = {"LW", "MW", "SW", "VHF", "UHF"}

# Global SDR instances for tools
_sdr_capture: SDRCapture | None = None
_sdr_processor: SDRProcessor | None = None
_websocket_server = None

# Preset frequencies for longwave stations
LONGWAVE_PRESETS = {
    "orf_longwave": {"name": "ORF Longwave", "frequency": 198000, "description": "Osterreichischer Rundfunk"},
    "bbc_radio4": {"name": "BBC Radio 4", "frequency": 198000, "description": "British Broadcasting Corporation"},
    "france_inter": {"name": "France Inter", "frequency": 162000, "description": "France Inter Longwave"},
    "rtl_luxembourg": {"name": "RTL Luxembourg", "frequency": 234000, "description": "RTL Radio Longwave"},
}


def get_sdr_capture() -> SDRCapture:
    """Get or create SDR capture instance."""
    global _sdr_capture
    if _sdr_capture is None:
        _sdr_capture = SDRCapture()
    return _sdr_capture


def get_sdr_processor() -> SDRProcessor:
    """Get or create SDR processor instance."""
    global _sdr_processor
    if _sdr_processor is None:
        _sdr_processor = SDRProcessor()
    return _sdr_processor


# Create FastMCP server (FastMCP 3.2+)
mcp = FastMCP("sdr-mcp")


@mcp.tool()
async def sdr_list_devices() -> dict[str, Any]:
    """List all available RTL-SDR devices with conversational guidance.

    Returns conversational response with device discovery results and next steps.
    """
    try:
        devices = SDRCapture.list_devices()
        available = SDRCapture.is_available()

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
                        "Use 'sdr_get_spectrum()' to see real-time spectrum data"
                    ],
                    "expert_tip": "Your RTL-SDR is now ready for spectrum analysis. The device supports frequencies from 24 MHz to 1.766 GHz with excellent sensitivity."
                },
                "sampling": {
                    "device_specs": {
                        "frequency_range": "24 MHz - 1.766 GHz",
                        "sample_rates": "up to 2.56 Msps",
                        "typical_sensitivity": "-70 dBm"
                    }
                }
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
                        "4. Run 'sdr_check()' to verify installation"
                    ],
                    "troubleshooting": [
                        "Ensure USB cable is securely connected",
                        "Check device manager for driver conflicts",
                        "Try different USB ports",
                        "Verify RTL-SDR model compatibility"
                    ],
                    "fallback_message": "Don't have hardware? You can still explore SDR concepts and presets!"
                },
                "sampling": {
                    "demo_mode": True,
                    "available_features": ["frequency_presets", "signal_analysis_concepts"]
                }
            }
    except Exception as e:
        logger.error(f"Error listing SDR devices: {e}", exc_info=True)
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
                    "Check system logs for USB errors"
                ]
            },
            "error": str(e)
        }


@mcp.tool()
async def sdr_initialize(device_index: int = 0) -> dict[str, Any]:
    """Initialize the SDR device for operation.

    Args:
        device_index: Index of the SDR device to use (default: 0)
    """
    try:
        capture = get_sdr_capture()
        success = await capture.initialize()

        if success:
            info = capture.get_info()
            return {
                "success": True,
                "device_info": info,
                "message": f"SDR device initialized successfully at {info['center_freq']/1e6:.1f} MHz"
            }
        else:
            return {
                "success": False,
                "message": "Failed to initialize SDR device. Check hardware connection and drivers."
            }
    except Exception as e:
        logger.error(f"Error initializing SDR: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def sdr_set_frequency(frequency_mhz: float) -> dict[str, Any]:
    """Set the center frequency for SDR capture.

    Args:
        frequency_mhz: Center frequency in MHz (e.g., 198.0 for longwave)
    """
    try:
        if frequency_mhz < MIN_FREQ_MHZ or frequency_mhz > MAX_FREQ_MHZ:
            return {
                "success": False,
                "frequency_mhz": frequency_mhz,
                "error": f"Frequency {frequency_mhz:.1f} MHz out of range ({MIN_FREQ_MHZ}-{MAX_FREQ_MHZ} MHz)",
                "message": f"Frequency must be between {MIN_FREQ_MHZ} MHz and {MAX_FREQ_MHZ} MHz"
            }
        capture = get_sdr_capture()
        frequency_hz = frequency_mhz * 1e6

        async with _sdr_semaphore:
            success = await capture.set_frequency(frequency_hz)

        return {
            "success": success,
            "frequency_mhz": frequency_mhz,
            "frequency_hz": frequency_hz,
            "message": f"Frequency set to {frequency_mhz:.1f} MHz" if success else "Failed to set frequency"
        }
    except Exception as e:
        logger.error(f"Error setting frequency: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def sdr_set_gain(gain: str = "auto") -> dict[str, Any]:
    """Set the SDR gain level.

    Args:
        gain: Gain setting ('auto' or numeric value like '19.7')
    """
    try:
        if gain != "auto":
            try:
                gain_val = float(gain)
                if gain_val < 0 or gain_val > 49.6:
                    return {
                        "success": False,
                        "gain": gain,
                        "error": "Gain value out of range (0-49.6 dB)",
                        "message": "Gain must be 'auto' or between 0 and 49.6 dB"
                    }
            except ValueError:
                return {
                    "success": False,
                    "gain": gain,
                    "error": f"Invalid gain value: {gain}",
                    "message": "Gain must be 'auto' or a numeric value in dB"
                }
        capture = get_sdr_capture()
        async with _sdr_semaphore:
            success = await capture.set_gain(gain)

        return {
            "success": success,
            "gain": gain,
            "message": f"Gain set to {gain}" if success else "Failed to set gain"
        }
    except Exception as e:
        logger.error(f"Error setting gain: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def sdr_get_spectrum() -> dict[str, Any]:
    """Get current spectrum data with conversational analysis and AI sampling.

    Returns rich conversational response with spectrum analysis, signal detection,
    and expert commentary for AI-assisted radio exploration.
    """
    try:
        capture = get_sdr_capture()
        processor = get_sdr_processor()

        samples = await capture.read_samples(1024 * 1024)

        if samples is None:
            return {
                "status": "no_data",
                "conversation": {
                    "message": "No signal samples available. The SDR might not be initialized yet.",
                    "suggestions": [
                        "First run: sdr_initialize()",
                        "Then try: sdr_tune_preset('bbc_radio4')",
                        "Or manually set: sdr_set_frequency(198.0)"
                    ],
                    "educational_note": "Spectrum analysis requires active signal capture. Think of this as tuning a radio before you can hear the stations!"
                }
            }

        spectrum_data = processor.process_samples(samples)
        center_freq = capture.center_freq / 1e6

        if spectrum_data.get('spectrum'):
            spectrum = spectrum_data['spectrum']
            max_power = max(spectrum)
            avg_power = sum(spectrum) / len(spectrum)
            signal_peaks = sum(1 for p in spectrum if p > avg_power + 10)

            analysis = {
                "signal_count": signal_peaks,
                "peak_power": round(max_power, 1),
                "average_power": round(avg_power, 1),
                "dynamic_range": round(max_power - min(spectrum), 1)
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
                "spectrum_data": spectrum_data,
                "frequency_mhz": center_freq,
                "analysis": analysis,
                "conversation": {
                    "message": conversation_msg,
                    "expertise_level": expertise_level,
                    "next_actions": [
                        "Try: sdr_get_waterfall() for time-varying signals",
                        "Tune to: sdr_tune_preset('orf_longwave')",
                        "Scan range: sdr_scan_frequencies(0.15, 0.3, 0.01)"
                    ],
                    "technical_insight": f"This {center_freq:.1f} MHz capture shows a {analysis['dynamic_range']} dB dynamic range. "
                                       f"The peak signal is {analysis['peak_power']} dB, suggesting "
                                       f"{'strong local signals' if analysis['peak_power'] > -20 else 'distant or weak transmissions'}."
                },
                "sampling": {
                    "fft_size": processor.fft_size,
                    "sample_rate": capture.sample_rate,
                    "bandwidth": capture.sample_rate / processor.fft_size,
                    "frequency_resolution": capture.sample_rate / processor.fft_size,
                    "data_points": len(spectrum_data.get('spectrum', []))
                }
            }
        else:
            return {
                "status": "processing_error",
                "conversation": {
                    "message": "Spectrum processing completed but no valid data returned.",
                    "troubleshooting": [
                        "Check SDR initialization",
                        "Verify frequency settings",
                        "Try different gain settings"
                    ]
                }
            }

    except Exception as e:
        logger.error(f"Error getting spectrum: {e}", exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Spectrum analysis failed: {e}",
                "recovery_suggestions": [
                    "Reinitialize SDR: sdr_initialize()",
                    "Check hardware connection",
                    "Try different frequency range"
                ]
            },
            "error": str(e)
        }


@mcp.tool()
async def sdr_get_waterfall() -> dict[str, Any]:
    """Get current waterfall display data."""
    try:
        processor = get_sdr_processor()
        waterfall_data = processor.get_waterfall_data()

        return {
            "success": True,
            "waterfall_data": waterfall_data,
            "lines_count": len(waterfall_data),
            "message": f"Waterfall data with {len(waterfall_data)} lines retrieved"
        }
    except Exception as e:
        logger.error(f"Error getting waterfall: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def sdr_tune_preset(preset_name: str) -> dict[str, Any]:
    """Tune to a predefined frequency preset with rich conversational guidance.

    Args:
        preset_name: Name of the preset (orf_longwave, bbc_radio4, france_inter, rtl_luxembourg)
    """
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
                        "Use: sdr_set_frequency(198.0) for manual tuning to 198 MHz"
                    ],
                    "educational_note": "Our database contains verified frequencies and program schedules for major international broadcasters."
                }
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
                    "historical_note": "ORF longwave has been broadcasting since 1962, serving as a cultural bridge across the Alps."
                },
                "bbc_radio4": {
                    "personality": "BBC Radio 4 - Intellectual discourse, drama, comedy, and comprehensive news from the UK's public broadcaster.",
                    "signal_characteristics": "Powerful 500kW transmitter from Droitwich, receivable across Europe and beyond.",
                    "listening_tips": "Excellent for news and current affairs. The longwave signal is remarkably stable.",
                    "historical_note": "BBC longwave service began in 1978, continuing the tradition of the BBC Home Service."
                },
                "france_inter": {
                    "personality": "France Inter - Eclectic mix of news, culture, music, and intellectual programming.",
                    "signal_characteristics": "Allouis transmitter provides reliable coverage across Western Europe.",
                    "listening_tips": "Features excellent music discovery and in-depth cultural discussions.",
                    "historical_note": "France Inter evolved from Radiodiffusion Francaise, maintaining longwave service since 1963."
                },
                "rtl_luxembourg": {
                    "personality": "RTL Luxembourg - Entertainment, music, and information in multiple languages.",
                    "signal_characteristics": "Junglinster transmitter covers Luxembourg and surrounding regions.",
                    "listening_tips": "Great for multilingual European news and entertainment.",
                    "historical_note": "RTL began longwave broadcasting in 1955, pioneering commercial radio in Europe."
                }
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
                        "Listen via: sdr_start_websocket_server() for real-time monitoring"
                    ],
                    "technical_details": {
                        "frequency": f"{frequency_mhz:.3f} MHz ({frequency_khz:.0f} kHz)",
                        "band": station.band.value,
                        "propagation": "Ground wave + sky wave at night",
                        "typical_range": "500-2000 km depending on conditions"
                    }
                },
                "sampling": {
                    "expected_signal_strength": "Strong longwave signals typically -30 to -60 dBm",
                    "bandwidth": "9 kHz AM modulation",
                    "modulation": "Amplitude Modulation (AM)",
                    "content_type": "Voice, music, news programming"
                }
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
                        "Driver or permissions issue"
                    ],
                    "alternatives": [
                        f"Try manual tuning: sdr_set_frequency({frequency_mhz})",
                        "Check device status: sdr_get_status()",
                        "List devices: sdr_list_devices()"
                    ]
                }
            }
    except Exception as e:
        logger.error(f"Error tuning preset: {e}", exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Tuning operation failed: {e}",
                "troubleshooting": [
                    "Ensure SDR is initialized",
                    "Check frequency range compatibility",
                    "Verify hardware connections"
                ]
            },
            "error": str(e)
        }


@mcp.tool()
async def sdr_get_status() -> dict[str, Any]:
    """Get current SDR status and configuration."""
    try:
        capture = get_sdr_capture()
        info = capture.get_info()

        return {
            "success": True,
            "device_info": info,
            "available_presets": {"note": "Use sdr_get_stations_by_band('LW') for longwave presets"},
            "message": "SDR status retrieved successfully"
        }
    except Exception as e:
        logger.error(f"Error getting status: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def sdr_start_websocket_server(host: str = "localhost", port: int = 8765) -> dict[str, Any]:
    """Start the WebSocket server for real-time spectrum streaming.

    Args:
        host: Host address to bind to (default: localhost)
        port: Port to bind to (default: 8765)
    """
    try:
        from .websocket_server import SDRWebSocketServer

        global _websocket_server
        if _websocket_server is None:
            _websocket_server = SDRWebSocketServer(host=host, port=port)

        asyncio.create_task(_websocket_server.start())

        return {
            "success": True,
            "websocket_url": f"ws://{host}:{port}",
            "message": f"WebSocket server started on ws://{host}:{port}"
        }
    except Exception as e:
        logger.error(f"Error starting WebSocket server: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def sdr_stop_websocket_server() -> dict[str, Any]:
    """Stop the WebSocket server for real-time streaming."""
    try:
        global _websocket_server
        if _websocket_server:
            await _websocket_server.stop()
            _websocket_server = None

        return {
            "success": True,
            "message": "WebSocket server stopped"
        }
    except Exception as e:
        logger.error(f"Error stopping WebSocket server: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def sdr_search_stations(query: str, band: str | None = None, country: str | None = None) -> dict[str, Any]:
    """Search for radio stations by name, callsign, or description with intelligent matching.

    Args:
        query: Search term (station name, callsign, or keywords)
        band: Optional band filter (LW, MW, SW, VHF, UHF)
        country: Optional country filter
    """
    try:
        db = get_frequency_database()

        band_enum = None
        if band:
            try:
                band_enum = Band(band.upper())
            except ValueError:
                pass

        results = db.search_stations(query, band_enum, country)

        if not results:
            return {
                "status": "no_results",
                "conversation": {
                    "message": f"No stations found matching '{query}'" + (f" in {country}" if country else "") + (f" on {band} band" if band else ""),
                    "suggestions": [
                        "Try broader search terms",
                        "Check spelling of station names",
                        "Search by country or region",
                        "Use frequency ranges instead: sdr_scan_frequencies()"
                    ],
                    "popular_searches": ["BBC", "France Inter", "ORF", "Voice of America", "BBC World Service", "Radio France Internationale"]
                }
            }

        by_band = {}
        for station in results:
            band_name = station.band.value
            if band_name not in by_band:
                by_band[band_name] = []
            by_band[band_name].append(station)

        total_found = len(results)
        bands_found = list(by_band.keys())
        top_recommendations = results[:3]

        return {
            "status": "found",
            "total_results": total_found,
            "bands": bands_found,
            "stations": [
                {
                    "name": s.name,
                    "callsign": s.callsign,
                    "frequency_mhz": s.frequency_mhz,
                    "frequency_khz": s.frequency_khz,
                    "band": s.band.value,
                    "country": s.country,
                    "city": s.city,
                    "type": s.station_type.value,
                    "language": s.language,
                    "description": s.description[:100] + "..." if len(s.description) > 100 else s.description,
                    "power_kw": s.power,
                    "website": s.website
                }
                for s in results
            ],
            "conversation": {
                "message": f"Found {total_found} station(s) matching '{query}' across {len(bands_found)} band(s): {', '.join(bands_found)}",
                "top_recommendations": [
                    {
                        "name": s.name,
                        "callsign": s.callsign,
                        "frequency": f"{s.frequency_mhz:.1f} MHz ({s.frequency_khz:.0f} kHz)",
                        "reason": f"{'Strong signal' if s.power > 100 else 'Reliable'} {s.band.value} station from {s.country}"
                    }
                    for s in top_recommendations
                ],
                "next_steps": [
                    f"Tune to top result: sdr_tune_frequency({top_recommendations[0].frequency_mhz})" if top_recommendations else None,
                    "Get program schedule: sdr_get_program_schedule('" + (top_recommendations[0].callsign if top_recommendations else "STATION") + "')",
                    "Search by country: sdr_search_stations('', country='France')",
                    "Explore band: sdr_get_stations_by_band('LW')"
                ],
                "search_insights": {
                    "total_database_size": db.get_station_count(),
                    "bands_available": [b.value for b in Band],
                    "countries_covered": len(set(s.country for s in db.get_all_stations())),
                    "languages_supported": len(set(s.language for s in db.get_all_stations()))
                }
            }
        }

    except Exception as e:
        logger.error(f"Error searching stations: {e}", exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Station search failed: {e}",
                "troubleshooting": [
                    "Check search query format",
                    "Try without filters first",
                    "Use simpler search terms"
                ]
            },
            "error": str(e)
        }


@mcp.tool()
async def sdr_get_stations_by_band(band: str) -> dict[str, Any]:
    """Get all stations on a specific frequency band with detailed information.

    Args:
        band: Frequency band (LW, MW, SW, VHF, UHF)
    """
    try:
        band_upper = band.upper()
        if band_upper not in VALID_BANDS:
            return {
                "status": "invalid_band",
                "conversation": {
                    "message": f"'{band}' is not a valid band. Available bands: {', '.join(sorted(VALID_BANDS))}",
                    "band_guide": {
                        "LW": "Longwave (150-300 kHz) - BBC, ORF, France Inter",
                        "MW": "Medium Wave (530-1700 kHz) - Regional AM stations",
                        "SW": "Shortwave (3-30 MHz) - BBC World Service, VOA, RFI",
                        "VHF": "VHF (30-300 MHz) - FM radio, military communications",
                        "UHF": "UHF (300-3000 MHz) - Digital radio, satellite"
                    }
                }
            }

        db = get_frequency_database()
        band_enum = Band(band_upper)
        stations = db.get_stations_by_band(band_enum)

        if not stations:
            return {
                "status": "no_stations",
                "conversation": {
                    "message": f"No stations found on {band} band in our database.",
                    "band_info": {
                        "LW": "Longwave (150-300 kHz) - Long distance, stable signals",
                        "MW": "Medium Wave (530-1700 kHz) - Regional AM broadcasting",
                        "SW": "Shortwave (3-30 MHz) - International broadcasting",
                        "VHF": "VHF (30-300 MHz) - Local FM, aviation",
                        "UHF": "UHF (300-3000 MHz) - Digital, satellite"
                    },
                    "suggestions": [
                        "Try other bands: LW, MW, SW",
                        "Use general search: sdr_search_stations('')",
                        "Search by country: sdr_get_stations_by_country('France')"
                    ]
                }
            }

        by_country = {}
        for station in stations:
            if station.country not in by_country:
                by_country[station.country] = []
            by_country[station.country].append(station)

        sorted_countries = sorted(by_country.items(), key=lambda x: len(x[1]), reverse=True)

        return {
            "status": "success",
            "band": band.upper(),
            "total_stations": len(stations),
            "countries": len(by_country),
            "stations": [
                {"name": s.name, "callsign": s.callsign, "frequency_mhz": s.frequency_mhz,
                 "frequency_khz": s.frequency_khz, "country": s.country, "city": s.city,
                 "type": s.station_type.value, "power_kw": s.power, "language": s.language,
                 "description": s.description}
                for s in stations
            ],
            "conversation": {
                "message": f"Found {len(stations)} station(s) on {band.upper()} band across {len(by_country)} countries.",
                "band_characteristics": {
                    "LW": "Longwave stations provide extremely stable, long-distance signals perfect for news and cultural programming.",
                    "MW": "Medium wave offers regional coverage with AM broadcasting, great for local news and entertainment.",
                    "SW": "Shortwave enables international broadcasting, reaching across continents with high power transmitters.",
                    "VHF": "VHF band includes local FM stations and specialized communications.",
                    "UHF": "UHF covers modern digital broadcasting and satellite communications."
                }.get(band.upper(), ""),
                "top_countries": [
                    {"country": country, "station_count": len(stations_list), "examples": [s.name for s in stations_list[:2]]}
                    for country, stations_list in sorted_countries[:3]
                ],
                "frequency_range": {
                    "LW": "150-300 kHz", "MW": "530-1700 kHz",
                    "SW": "3-30 MHz", "VHF": "30-300 MHz", "UHF": "300-3000 MHz"
                }.get(band.upper(), ""),
                "recommended_stations": [
                    s.callsign for s in stations
                    if s.station_type == StationType.INTERNATIONAL or s.power > 100
                ][:3]
            }
        }

    except ValueError:
        return {
            "status": "invalid_band",
            "conversation": {
                "message": f"'{band}' is not a valid band. Available bands: LW, MW, SW, VHF, UHF",
                "band_guide": {
                    "LW": "Longwave (150-300 kHz) - BBC, ORF, France Inter",
                    "MW": "Medium Wave (530-1700 kHz) - Regional AM stations",
                    "SW": "Shortwave (3-30 MHz) - BBC World Service, VOA, RFI",
                    "VHF": "VHF (30-300 MHz) - FM radio, military communications",
                    "UHF": "UHF (300-3000 MHz) - Digital radio, satellite"
                }
            }
        }
    except Exception as e:
        logger.error(f"Error getting stations by band: {e}", exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Failed to retrieve {band} band stations: {e}",
                "fallback": "Try: sdr_search_stations('') for all available stations"
            },
            "error": str(e)
        }


@mcp.tool()
async def sdr_get_program_schedule(station_callsign: str, day: str | None = None) -> dict[str, Any]:
    """Get program schedule for a specific radio station.

    Args:
        station_callsign: Station callsign (e.g., 'BBC LW', 'ORF LW')
        day: Optional day of week (monday, tuesday, etc.)
    """
    try:
        db = get_frequency_database()
        station = db.stations.get(station_callsign)

        if not station:
            possible_matches = [s for s in db.get_all_stations()
                              if station_callsign.lower() in s.callsign.lower() or
                                 station_callsign.lower() in s.name.lower()]

            return {
                "status": "station_not_found",
                "conversation": {
                    "message": f"Station '{station_callsign}' not found in database.",
                    "possible_matches": [
                        {"callsign": s.callsign, "name": s.name, "frequency": f"{s.frequency_mhz:.1f} MHz"}
                        for s in possible_matches[:3]
                    ] if possible_matches else [],
                    "suggestions": [
                        "Use: sdr_search_stations('BBC') to find BBC stations",
                        "Try: sdr_get_stations_by_band('LW') for longwave stations",
                        "Check callsign spelling"
                    ]
                }
            }

        current_program = db.get_current_program(station_callsign)
        schedule = db.get_program_schedule(station_callsign, day)

        schedule_by_day = {}
        for program in schedule:
            for day_name in program.days:
                if day_name not in schedule_by_day:
                    schedule_by_day[day_name] = []
                schedule_by_day[day_name].append({
                    "name": program.name,
                    "description": program.description,
                    "start_time": program.start_time.strftime("%H:%M"),
                    "end_time": program.end_time.strftime("%H:%M"),
                    "language": program.language,
                    "genre": program.genre
                })

        for day_programs in schedule_by_day.values():
            day_programs.sort(key=lambda x: x["start_time"])

        return {
            "status": "success",
            "station": {
                "name": station.name, "callsign": station.callsign,
                "frequency_mhz": station.frequency_mhz, "frequency_khz": station.frequency_khz,
                "band": station.band.value, "country": station.country,
                "language": station.language, "description": station.description
            },
            "current_program": {
                "name": current_program.name if current_program else "Off-air/Unknown",
                "description": current_program.description if current_program else "",
                "start_time": current_program.start_time.strftime("%H:%M") if current_program else "",
                "end_time": current_program.end_time.strftime("%H:%M") if current_program else "",
                "language": current_program.language if current_program else "",
                "genre": current_program.genre if current_program else ""
            } if current_program or schedule else None,
            "schedule": schedule_by_day,
            "conversation": {
                "message": f"Program schedule for {station.name} ({station.callsign})",
                "current_status": f"Currently playing: {current_program.name}" if current_program else "Current program information not available",
                "schedule_summary": {
                    "total_programs": len(schedule),
                    "days_scheduled": len(schedule_by_day),
                    "languages": list(set(p.language for p in schedule)) if schedule else [],
                    "genres": list(set(p.genre for p in schedule)) if schedule else []
                },
                "next_steps": [
                    f"Listen now: sdr_tune_preset('{station.callsign.lower().replace(' ', '_')}')",
                    "Get real-time spectrum: sdr_get_spectrum()",
                    "Search similar stations: sdr_get_stations_by_country('" + station.country + "')"
                ],
                "schedule_note": "Times shown in UTC. Local time may vary. Program schedules are subject to change."
            }
        }

    except Exception as e:
        logger.error(f"Error getting program schedule: {e}", exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Failed to retrieve program schedule: {e}",
                "suggestions": [
                    "Check station callsign spelling",
                    "Try station search first: sdr_search_stations('')",
                    "Some stations may not have schedule data available"
                ]
            },
            "error": str(e)
        }


@mcp.tool()
async def sdr_get_stations_by_country(country: str) -> dict[str, Any]:
    """Get all radio stations from a specific country.

    Args:
        country: Country name (e.g., 'France', 'United Kingdom', 'Germany')
    """
    try:
        db = get_frequency_database()
        stations = db.get_stations_by_country(country)

        if not stations:
            all_countries = list(set(s.country for s in db.get_all_stations()))
            similar_countries = [c for c in all_countries
                               if country.lower() in c.lower() or
                                  any(word in c.lower() for word in country.lower().split())]

            return {
                "status": "no_stations",
                "conversation": {
                    "message": f"No stations found for '{country}' in our database.",
                    "available_countries": all_countries[:10],
                    "similar_countries": similar_countries[:5] if similar_countries else [],
                    "suggestions": [
                        "Check country name spelling",
                        "Try major countries: France, Germany, United Kingdom",
                        "Use general search: sdr_search_stations('')"
                    ]
                }
            }

        by_band = {}
        for station in stations:
            band_name = station.band.value
            if band_name not in by_band:
                by_band[band_name] = []
            by_band[band_name].append(station)

        by_type = {}
        for station in stations:
            type_name = station.station_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(station)

        sorted_stations = sorted(stations, key=lambda x: x.power, reverse=True)

        return {
            "status": "success",
            "country": country,
            "total_stations": len(stations),
            "bands": list(by_band.keys()),
            "station_types": list(by_type.keys()),
            "stations": [
                {"name": s.name, "callsign": s.callsign, "frequency_mhz": s.frequency_mhz,
                 "frequency_khz": s.frequency_khz, "band": s.band.value, "city": s.city,
                 "type": s.station_type.value, "power_kw": s.power, "language": s.language,
                 "description": s.description[:150] + "..." if len(s.description) > 150 else s.description}
                for s in stations
            ],
            "conversation": {
                "message": f"Found {len(stations)} station(s) broadcasting from {country} across {len(by_band)} frequency bands.",
                "band_breakdown": {band: len(lst) for band, lst in by_band.items()},
                "type_breakdown": {stype: len(lst) for stype, lst in by_type.items()},
                "top_stations": [
                    {"name": s.name, "callsign": s.callsign, "band": s.band.value,
                     "power": f"{s.power} kW",
                     "reason": "High power international broadcaster" if s.station_type == StationType.INTERNATIONAL
                              else "Major national station" if s.power > 100 else "Regional broadcaster"}
                    for s in sorted_stations[:3]
                ],
                "cultural_insights": {
                    "United Kingdom": "Home of the BBC, with extensive public broadcasting and international services.",
                    "France": "Strong public broadcasting tradition with cultural focus and international reach.",
                    "Germany": "Diverse broadcasting landscape with strong regional and international services.",
                    "Austria": "Rich cultural broadcasting with emphasis on classical music and public service."
                }.get(country, f"{country} has a diverse broadcasting landscape with various station types."),
                "next_steps": [
                    "Tune to top station: sdr_tune_frequency(" + str(sorted_stations[0].frequency_mhz) + ")",
                    "Get program schedule: sdr_get_program_schedule('" + sorted_stations[0].callsign + "')",
                    "Explore by band: sdr_get_stations_by_band('LW')",
                    "Search within country: sdr_search_stations('', country='" + country + "')"
                ]
            }
        }

    except Exception as e:
        logger.error(f"Error getting stations by country: {e}", exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Failed to retrieve stations for {country}: {e}",
                "fallback": "Try: sdr_search_stations('') for all available stations"
            },
            "error": str(e)
        }


@mcp.tool()
async def sdr_get_frequency_database_stats() -> dict[str, Any]:
    """Get comprehensive statistics about the frequency database."""
    try:
        db = get_frequency_database()
        all_stations = db.get_all_stations()

        by_band = {}
        by_country = {}
        by_type = {}
        languages = set()
        total_power = 0

        for station in all_stations:
            band_name = station.band.value
            by_band[band_name] = by_band.get(band_name, 0) + 1
            by_country[station.country] = by_country.get(station.country, 0) + 1
            type_name = station.station_type.value
            by_type[type_name] = by_type.get(type_name, 0) + 1
            languages.add(station.language)
            total_power += station.power

        return {
            "status": "success",
            "database_stats": {
                "total_stations": len(all_stations),
                "countries_covered": len(by_country),
                "bands_covered": len(by_band),
                "station_types": len(by_type),
                "languages_supported": len(languages),
                "total_transmitter_power": total_power,
                "average_power_per_station": round(total_power / len(all_stations), 1) if all_stations else 0
            },
            "breakdown": {
                "by_band": by_band,
                "by_country": dict(sorted(by_country.items(), key=lambda x: x[1], reverse=True)),
                "by_type": by_type,
                "languages": sorted(list(languages)),
            },
            "top_countries": [
                {"country": country, "stations": count}
                for country, count in sorted(by_country.items(), key=lambda x: x[1], reverse=True)[:5]
            ],
            "conversation": {
                "message": f"SDR Frequency Database contains {len(all_stations)} stations from {len(by_country)} countries.",
                "key_insights": [
                    f"Most active band: {max(by_band.items(), key=lambda x: x[1])[0]} with {max(by_band.items(), key=lambda x: x[1])[1]} stations",
                    f"Best represented country: {max(by_country.items(), key=lambda x: x[1])[0]} with {max(by_country.items(), key=lambda x: x[1])[1]} stations",
                    f"Total transmitter power: {total_power} kW across all stations",
                    f"Languages supported: {len(languages)} ({', '.join(sorted(list(languages))[:3])}...)"
                ],
                "historical_context": "This database eliminates the traditional SDR challenge of manually tracking frequencies and schedules.",
                "capabilities": [
                    "Real-time station lookup by name, frequency, or location",
                    "Program schedules with current playing information",
                    "Signal strength expectations and propagation guidance",
                    "Cultural and historical context for each station"
                ]
            }
        }

    except Exception as e:
        logger.error(f"Error getting database stats: {e}", exc_info=True)
        return {
            "status": "error",
            "conversation": {
                "message": f"Failed to retrieve database statistics: {e}",
                "note": "The frequency database provides comprehensive station information."
            },
            "error": str(e)
        }


@mcp.tool()
async def sdr_scan_frequencies(start_freq: float, end_freq: float, step_size: float = 1.0) -> dict[str, Any]:
    """Scan frequency range with AI-powered analysis and conversational reporting.

    Args:
        start_freq: Starting frequency in MHz
        end_freq: Ending frequency in MHz
        step_size: Step size in MHz (default: 1.0)
    """
    try:
        if start_freq < MIN_FREQ_MHZ or end_freq > MAX_FREQ_MHZ:
            return {
                "status": "invalid_range",
                "conversation": {
                    "message": f"Frequency range {start_freq:.1f}-{end_freq:.1f} MHz exceeds RTL-SDR limits ({MIN_FREQ_MHZ}-{MAX_FREQ_MHZ} MHz)"
                }
            }
        if start_freq >= end_freq:
            return {
                "status": "invalid_range",
                "conversation": {
                    "message": f"Start frequency ({start_freq:.1f} MHz) must be less than end frequency ({end_freq:.1f} MHz)"
                }
            }
        if step_size <= 0:
            return {
                "status": "invalid_range",
                "conversation": {
                    "message": f"Step size must be positive (got {step_size})"
                }
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
                spectrum = spectrum_data.get('spectrum', [])
                max_power = max(spectrum) if spectrum else -100

                result = {
                    "frequency_mhz": current_freq,
                    "max_power_db": round(max_power, 1),
                    "spectrum_data": spectrum_data,
                    "timestamp": asyncio.get_running_loop().time()
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
                "expected_signals": "International broadcasters, maritime navigation"
            }
        elif start_freq >= 0.5 and end_freq <= 1.6:
            band_analysis = {
                "band_name": "Medium Wave (MW)",
                "typical_use": "AM radio broadcasting",
                "propagation": "Ground wave + sky wave",
                "expected_signals": "Local and regional AM stations"
            }

        return {
            "status": "scan_complete",
            "scan_results": results,
            "scan_parameters": {
                "start_freq_mhz": start_freq,
                "end_freq_mhz": end_freq,
                "step_size_mhz": step_size,
                "total_steps": len(results),
                "scan_duration_seconds": round(scan_duration, 2)
            },
            "signal_analysis": {
                "total_signals_detected": total_signals,
                "strong_signals": strong_signals,
                "moderate_signals": total_signals - strong_signals,
                "detected_signals": detected_signals[:10]
            },
            "conversation": {
                "message": scan_assessment,
                "expertise_level": expertise_level,
                "scan_summary": f"Completed frequency sweep from {start_freq:.1f} to {end_freq:.1f} MHz in {scan_duration:.1f} seconds.",
                "key_findings": conversation_progress[-5:] if conversation_progress else ["Scan completed successfully"],
                "band_context": band_analysis,
                "next_recommendations": [
                    "Focus on strongest signals: " + ", ".join([f"{s['frequency']:.1f} MHz" for s in detected_signals[:3]]) if detected_signals else "Try different frequency ranges",
                    "Use sdr_tune_preset() for known stations",
                    "Run sdr_get_waterfall() on interesting frequencies",
                    "Try narrower scan: step_size=0.1 for detailed analysis"
                ],
                "technical_notes": [
                    f"Average scan time per frequency: {scan_duration/len(results):.2f} seconds",
                    f"Dynamic range covered: {max([r['max_power_db'] for r in results]) - min([r['max_power_db'] for r in results]):.1f} dB",
                    "Signal detection threshold: 5-15 dB above average noise"
                ]
            },
            "sampling": {
                "scan_method": "FFT-based spectrum analysis",
                "sample_rate": capture.sample_rate,
                "fft_size": processor.fft_size,
                "frequency_resolution": capture.sample_rate / processor.fft_size,
                "processing_efficiency": f"{len(results)/scan_duration:.1f} frequencies/second"
            }
        }
    except Exception as e:
        logger.error(f"Error scanning frequencies: {e}", exc_info=True)
        return {
            "status": "scan_error",
            "conversation": {
                "message": f"Frequency scanning failed: {e}",
                "possible_causes": [
                    "SDR device not initialized",
                    "Frequency range outside device capabilities",
                    "Hardware connection issues",
                    "Insufficient scan timing"
                ],
                "recovery_steps": [
                    "Initialize SDR: sdr_initialize()",
                    "Check device status: sdr_get_status()",
                    "Try smaller frequency ranges",
                    "Increase step delays if needed"
                ]
            },
            "error": str(e)
        }


@mcp.tool()
async def sdr_query_online_database(
    query: str = "",
    by: str = "name",
    country: str = "",
    language: str = "",
    tag: str = "",
    limit: int = 25,
) -> dict:
    """Search online radio station databases (radio-browser.info, sigidwiki).

    Queries the only open radio frequency/station API available.
    Returns station name, country, language, codec, bitrate, tags.

    Args:
        query: Station name to search for (used with by='name' or 'search').
        by: Search mode: 'name', 'country', 'language', 'tag', 'search', or 'signal_id'.
        country: Filter by country name (used with by='country').
        language: Filter by language (used with by='language').
        tag: Filter by genre tag (used with by='tag').
        limit: Max results (1-100).
    """
    try:
        if by == "signal_id":
            if not query:
                return {"status": "error", "message": "Signal name required for signal_id lookup"}
            info = await get_signal_info(query)
            if not info:
                return {
                    "status": "not_found",
                    "message": f"No signal info found for '{query}'",
                    "conversation": {
                        "message": f"Could not identify signal '{query}'",
                        "suggestion": "Try sigidwiki.com for manual lookup",
                    },
                }
            return {
                "status": "success",
                "signal": {"title": info.title, "description": info.description, "page_url": info.page_url},
                "conversation": {
                    "message": f"Signal '{info.title}' identified",
                    "details": info.description[:200] if info.description else "",
                    "wiki_url": info.page_url,
                },
            }

        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 1

        stations = await search_radio_browser(
            query=query,
            limit=limit,
            by=by,
            country=country or None,
            language=language or None,
            tag=tag or None,
        )

        if not stations:
            return {
                "status": "no_results",
                "message": f"No stations found for '{query or by}'",
                "conversation": {
                    "message": f"No results for {by}='{query or country or language or tag}'",
                    "try_alternatives": [
                        "Use by='country' for country search",
                        "Use by='tag' for genre search",
                        "Use by='name' for station name",
                    ],
                },
            }

        return {
            "status": "success",
            "total": len(stations),
            "stations": [
                {"name": s.name, "country": s.country, "language": s.language,
                 "tags": s.tags[:5], "codec": s.codec, "bitrate": s.bitrate,
                 "url": s.url, "clicks": s.clicks}
                for s in stations
            ],
            "conversation": {
                "message": f"Found {len(stations)} station(s) from radio-browser.info",
                "source": "radio-browser.info (open API)",
                "top_countries": list({s.country for s in stations if s.country})[:5],
                "top_tags": list({t for s in stations for t in s.tags[:3]})[:5],
            },
        }

    except Exception as e:
        logger.error(f"Online DB query failed: {e}", exc_info=True)
        return {"status": "error", "message": f"Online database query failed: {e}"}
