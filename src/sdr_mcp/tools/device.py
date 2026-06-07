"""SDR device portmanteau tool."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..handlers import (
    configure_mock_mode,
    get_status,
    initialize,
    list_devices,
    scan_frequencies,
    set_frequency,
    set_gain,
    tune_preset,
)
from ..handlers.health import run_health_checks


async def sdr_device(
    operation: str,
    device_index: int = 0,
    frequency_mhz: float | None = None,
    gain: str = "auto",
    preset_name: str = "",
    start_freq: float | None = None,
    end_freq: float | None = None,
    step_size: float = 1.0,
    mock_enabled: bool | None = None,
) -> dict[str, Any]:
    """Portmanteau SDR device operations (list, initialize, tune, scan)."""
    if operation == "list":
        return await list_devices()
    if operation == "initialize":
        return await initialize(device_index=device_index)
    if operation == "status":
        return await get_status()
    if operation == "health":
        return await run_health_checks()
    if operation == "set_frequency":
        if frequency_mhz is None:
            return {"success": False, "message": "frequency_mhz is required for set_frequency"}
        return await set_frequency(frequency_mhz=frequency_mhz)
    if operation == "set_gain":
        return await set_gain(gain=gain)
    if operation == "tune_preset":
        if not preset_name:
            return {"success": False, "message": "preset_name is required for tune_preset"}
        return await tune_preset(preset_name=preset_name)
    if operation == "scan":
        if start_freq is None or end_freq is None:
            return {"success": False, "message": "start_freq and end_freq are required for scan"}
        return await scan_frequencies(start_freq=start_freq, end_freq=end_freq, step_size=step_size)
    if operation == "mock_mode":
        return await configure_mock_mode(mock_enabled=mock_enabled)
    return {
        "success": False,
        "status": "error",
        "message": f"Unknown operation: {operation}",
        "valid_operations": [
            "list",
            "initialize",
            "status",
            "health",
            "set_frequency",
            "set_gain",
            "tune_preset",
            "scan",
            "mock_mode",
        ],
    }


def register(mcp: FastMCP) -> None:
    mcp.tool()(sdr_device)
