"""Online radio database portmanteau tool."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP

from ..handlers import query_online_database


async def sdr_online(
    operation: str,
    query: str = "",
    country: str = "",
    language: str = "",
    tag: str = "",
    limit: int = 25,
) -> dict[str, Any]:
    """Portmanteau online station lookup operations.

    ## Return Format
    `{"success": bool, "message": str, ...}` - success flag with a human-readable
    message plus operation-specific fields (`stations`, `signal`).
    Unknown operations return `success: False` with `valid_operations`.

    ## Examples
    `sdr_online(operation="search", query="jazz")` -> radio-browser matches
    `sdr_online(operation="signal_id", query="FT8")` -> signal wiki info
    """
    if operation == "search":
        return await query_online_database(
            query=query,
            by="name",
            country=country,
            language=language,
            tag=tag,
            limit=limit,
        )
    if operation == "signal_id":
        return await query_online_database(query=query, by="signal_id", limit=limit)
    return {
        "success": False,
        "status": "error",
        "message": f"Unknown operation: {operation}",
        "valid_operations": ["search", "signal_id"],
    }


def register(mcp: FastMCP) -> None:
    mcp.tool()(sdr_online)
