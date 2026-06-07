"""SDR MCP Server — FastMCP instance and tool registration."""

from __future__ import annotations

from fastmcp import FastMCP

from .tools import register_tools
from .tools.agentic import sdr_agentic_assist, sdr_sampling_hint
from .tools.device import sdr_device
from .tools.gnuradio import sdr_gnuradio
from .tools.online import sdr_online
from .tools.spectrum import sdr_spectrum
from .tools.stations import sdr_stations

mcp = FastMCP("sdr-mcp")
register_tools(mcp)

__all__ = [
    "mcp",
    "sdr_agentic_assist",
    "sdr_device",
    "sdr_gnuradio",
    "sdr_online",
    "sdr_sampling_hint",
    "sdr_spectrum",
    "sdr_stations",
]
