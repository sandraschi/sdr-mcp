"""SDR spectrum portmanteau tool."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..handlers import get_spectrum, get_waterfall, start_websocket_server, stop_websocket_server


async def sdr_spectrum(
    operation: str,
    host: str = "localhost",
    port: int = 8765,
) -> dict[str, Any]:
    """Portmanteau SDR spectrum and streaming operations."""
    if operation == "spectrum":
        return await get_spectrum()
    if operation == "waterfall":
        return await get_waterfall()
    if operation == "start_websocket":
        return await start_websocket_server(host=host, port=port)
    if operation == "stop_websocket":
        return await stop_websocket_server()
    return {
        "success": False,
        "status": "error",
        "message": f"Unknown operation: {operation}",
        "valid_operations": ["spectrum", "waterfall", "start_websocket", "stop_websocket"],
    }


def register(mcp: FastMCP) -> None:
    mcp.tool()(sdr_spectrum)
