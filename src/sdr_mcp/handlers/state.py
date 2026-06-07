"""Shared mutable state and constants for handler modules."""

from __future__ import annotations

import asyncio
import os

from ..capture import SDRCapture
from ..processor import SDRProcessor

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

# Mock mode: None=auto (mock when no RTL-SDR), True=force mock, False=force hardware


def _init_mock_from_env() -> bool | None:
    raw = os.getenv("SDR_MCP_MOCK", "").strip().lower()
    if raw in ("1", "true", "yes", "enable", "enabled", "on"):
        return True
    if raw in ("0", "false", "no", "disable", "disabled", "off"):
        return False
    return None


_mock_mode: bool | None = _init_mock_from_env()

# Preset frequencies for longwave stations
LONGWAVE_PRESETS = {
    "orf_longwave": {"name": "ORF Longwave", "frequency": 198000, "description": "Osterreichischer Rundfunk"},
    "bbc_radio4": {"name": "BBC Radio 4", "frequency": 198000, "description": "British Broadcasting Corporation"},
    "france_inter": {"name": "France Inter", "frequency": 162000, "description": "France Inter Longwave"},
    "rtl_luxembourg": {"name": "RTL Luxembourg", "frequency": 234000, "description": "RTL Radio Longwave"},
}


def get_mock_mode_label() -> str:
    """Human-readable mock setting: auto | enabled | disabled."""
    if _mock_mode is True:
        return "enabled"
    if _mock_mode is False:
        return "disabled"
    return "auto"


def set_mock_mode(enabled: bool | None) -> None:
    """Set mock mode and reset the cached capture instance."""
    global _mock_mode, _sdr_capture
    _mock_mode = enabled
    _sdr_capture = None


def should_use_mock() -> bool:
    """Whether the active capture path should use synthetic IQ."""
    if _mock_mode is True:
        return True
    if _mock_mode is False:
        return False
    return not SDRCapture.is_available()


def reset_sdr_capture() -> None:
    """Drop cached capture so the next get picks up mock/hardware changes."""
    global _sdr_capture
    _sdr_capture = None


def get_sdr_capture() -> SDRCapture:
    """Get or create SDR capture instance (hardware or mock)."""
    global _sdr_capture
    if _sdr_capture is None:
        if should_use_mock():
            from ..mock_capture import MockSDRCapture

            _sdr_capture = MockSDRCapture()
        else:
            _sdr_capture = SDRCapture()
    return _sdr_capture


def get_sdr_processor() -> SDRProcessor:
    """Get or create SDR processor instance."""
    global _sdr_processor
    if _sdr_processor is None:
        _sdr_processor = SDRProcessor()
    return _sdr_processor
