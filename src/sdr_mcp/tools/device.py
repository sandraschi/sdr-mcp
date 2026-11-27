"""SDR device portmanteau tool."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..handlers import (
    configure_mock_mode,
    decode_station_rds,
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
    duration_s: float = 10.0,
) -> dict[str, Any]:
    """Portmanteau SDR device operations (list, initialize, tune, scan, rds).

    ## Return Format
    `{"success": bool, "message": str, ...}` - success flag with a human-readable
    message plus operation-specific fields (`devices`, `device_info`, `peaks`).
    Unknown operations return `success: False` with `valid_operations`.

    ## Examples
    `sdr_device(operation="list")` -> `{"success": True, "devices": [...]}`
    `sdr_device(operation="health")` -> RTL-SDR + GNU Radio sidecar health
    `sdr_device(operation="set_frequency", frequency_mhz=101.5)` -> retune
    `sdr_device(operation="scan", start_freq=87.5, end_freq=108, step_size=0.1)` -> FM stations
    `sdr_device(operation="rds", frequency_mhz=88.9, duration_s=10)` -> PI, PS name, PTY, RadioText
    """
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
    if operation == "rds":
        if frequency_mhz is None:
            return {"success": False, "message": "frequency_mhz is required for rds"}
        return await decode_station_rds(frequency_mhz=frequency_mhz, duration_s=duration_s)
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
            "rds",
            "mock_mode",
        ],
    }


def register(mcp: FastMCP) -> None:
    mcp.tool()(sdr_device)
