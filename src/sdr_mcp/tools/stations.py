"""SDR station database portmanteau tool."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..handlers import (
    get_frequency_database_stats,
    get_program_schedule,
    get_stations_by_band,
    get_stations_by_country,
    search_stations,
)


async def sdr_stations(
    operation: str,
    query: str = "",
    band: str | None = None,
    country: str = "",
    station_callsign: str = "",
    day: str | None = None,
) -> dict[str, Any]:
    """Portmanteau SDR station database operations."""
    if operation == "search":
        return await search_stations(query=query, band=band, country=country or None)
    if operation == "by_band":
        if not band:
            return {"success": False, "message": "band is required for by_band"}
        return await get_stations_by_band(band=band)
    if operation == "by_country":
        if not country:
            return {"success": False, "message": "country is required for by_country"}
        return await get_stations_by_country(country=country)
    if operation == "schedule":
        if not station_callsign:
            return {"success": False, "message": "station_callsign is required for schedule"}
        return await get_program_schedule(station_callsign=station_callsign, day=day)
    if operation == "stats":
        return await get_frequency_database_stats()
    return {
        "success": False,
        "status": "error",
        "message": f"Unknown operation: {operation}",
        "valid_operations": ["search", "by_band", "by_country", "schedule", "stats"],
    }


def register(mcp: FastMCP) -> None:
    mcp.tool()(sdr_stations)
