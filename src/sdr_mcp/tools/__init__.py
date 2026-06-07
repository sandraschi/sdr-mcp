"""Portmanteau MCP tool registration for sdr-mcp."""

from __future__ import annotations

from fastmcp import FastMCP

from . import agentic, device, gnuradio, online, spectrum, stations


def register_tools(mcp: FastMCP) -> None:
    """Attach all portmanteau tools to the FastMCP instance."""
    device.register(mcp)
    spectrum.register(mcp)
    stations.register(mcp)
    online.register(mcp)
    gnuradio.register(mcp)
    agentic.register(mcp)
