"""GNU Radio sidecar portmanteau tool."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..handlers import handle_gnuradio_operation


async def sdr_gnuradio(
    operation: str,
    mode: str = "fm",
    source: str = "rtl_tcp",
    frequency_mhz: float | None = None,
    rtl_tcp_host: str | None = None,
    rtl_tcp_port: int | None = None,
    gain: float = 20.0,
) -> dict[str, Any]:
    """Portmanteau GNU Radio sidecar operations (FM/AM/USB/LSB demod)."""
    return await handle_gnuradio_operation(
        operation=operation,
        mode=mode,
        source=source,
        frequency_mhz=frequency_mhz,
        rtl_tcp_host=rtl_tcp_host,
        rtl_tcp_port=rtl_tcp_port,
        gain=gain,
    )


def register(mcp: FastMCP) -> None:
    mcp.tool()(sdr_gnuradio)
