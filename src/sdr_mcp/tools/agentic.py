"""FastMCP 3.4 agentic sampling tools (SEP-1577)."""

from __future__ import annotations

from typing import Any

from fastmcp import Context, FastMCP


async def sdr_agentic_assist(goal: str, ctx: Context) -> dict[str, Any]:
    """Multi-step SDR workflow plan via MCP sampling (ctx.sample).

    Names concrete portmanteau tools: sdr_device, sdr_spectrum, sdr_stations,
    sdr_online, sdr_gnuradio. Requires a sampling-capable MCP host.
    """
    try:
        result = await ctx.sample(
            messages=(
                "You are an assistant for sdr-mcp. Given the user's radio goal, output a compact plan:\n"
                "1) First line: one-line summary\n"
                "Then numbered steps (3-7), each naming concrete MCP tools and operations.\n\n"
                f"Goal:\n{goal[:4000]}"
            ),
            system_prompt=(
                "Plain text only. Prefer sdr_device(operation='list') first when hardware is unknown; "
                "sdr_device(operation='tune_preset') for longwave; sdr_spectrum(operation='spectrum') "
                "for FFT; sdr_gnuradio for FM/AM demod via sidecar; sdr_stations for schedules."
            ),
            max_tokens=800,
        )
        text = getattr(result, "text", None) or str(result)
        return {"success": True, "plan": text.strip(), "goal": goal}
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "error_type": type(exc).__name__,
            "goal": goal,
            "recovery_options": [
                "Use a client that supports MCP sampling (Cursor with sampling enabled).",
                "Run tools manually: sdr_device(operation='list'), sdr_spectrum(operation='spectrum').",
            ],
        }


async def sdr_sampling_hint(topic: str, ctx: Context) -> dict[str, Any]:
    """Suggest frequencies, bands, and tool sequence for a radio topic via ctx.sample."""
    try:
        result = await ctx.sample(
            messages=(
                "Suggest 3-5 concrete SDR actions (tool + operation + example params) for this topic. "
                "Include band hints (LW/MW/FM) when relevant.\n\nTopic:\n" + topic[:2000]
            ),
            system_prompt="Plain text only. Reference sdr_device, sdr_spectrum, sdr_gnuradio portmanteau tools.",
            max_tokens=400,
        )
        text = getattr(result, "text", None) or str(result)
        return {"success": True, "suggestions": text.strip(), "topic": topic}
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "error_type": type(exc).__name__,
            "topic": topic,
            "recovery_options": [
                "Enable MCP sampling on the host.",
                "Try sdr_stations(operation='search', query='BBC') manually.",
            ],
        }


def register(mcp: FastMCP) -> None:
    mcp.tool()(sdr_agentic_assist)
    mcp.tool()(sdr_sampling_hint)
