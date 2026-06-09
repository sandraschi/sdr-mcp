"""Online database integration handlers."""

from __future__ import annotations

import logging
from typing import Any

from ..online_db import get_signal_info, search_radio_browser

logger = logging.getLogger(__name__)


async def query_online_database(
    query: str = "",
    by: str = "name",
    country: str = "",
    language: str = "",
    tag: str = "",
    limit: int = 25,
) -> dict[str, Any]:
    """Search online radio station databases (radio-browser.info, sigidwiki)."""
    try:
        if by == "signal_id":
            if not query:
                return {"status": "error", "message": "Signal name required for signal_id lookup"}
            info = await get_signal_info(query)
            if not info:
                return {
                    "status": "not_found",
                    "message": f"No signal info found for '{query}'",
                    "conversation": {
                        "message": f"Could not identify signal '{query}'",
                        "suggestion": "Try sigidwiki.com for manual lookup",
                    },
                }
            return {
                "status": "success",
                "signal": {"title": info.title, "description": info.description, "page_url": info.page_url},
                "conversation": {
                    "message": f"Signal '{info.title}' identified",
                    "details": info.description[:200] if info.description else "",
                    "wiki_url": info.page_url,
                },
            }

        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 1

        stations = await search_radio_browser(
            query=query,
            limit=limit,
            by=by,
            country=country or None,
            language=language or None,
            tag=tag or None,
        )

        if not stations:
            return {
                "status": "no_results",
                "message": f"No stations found for '{query or by}'",
                "conversation": {
                    "message": f"No results for {by}='{query or country or language or tag}'",
                    "try_alternatives": [
                        "Use by='country' for country search",
                        "Use by='tag' for genre search",
                        "Use by='name' for station name",
                    ],
                    "offline_hint": "Results are cached for one hour after a successful lookup when the network is unavailable.",
                },
            }

        return {
            "status": "success",
            "total": len(stations),
            "stations": [
                {
                    "name": s.name,
                    "country": s.country,
                    "language": s.language,
                    "tags": s.tags[:5],
                    "codec": s.codec,
                    "bitrate": s.bitrate,
                    "url": s.url,
                    "clicks": s.clicks,
                }
                for s in stations
            ],
            "conversation": {
                "message": f"Found {len(stations)} station(s) from radio-browser.info",
                "source": "radio-browser.info (open API)",
                "top_countries": list({s.country for s in stations if s.country})[:5],
                "top_tags": list({t for s in stations for t in s.tags[:3]})[:5],
            },
        }

    except Exception as e:
        logger.error("Online DB query failed: %s", e, exc_info=True)
        return {
            "status": "error",
            "message": f"Online database query failed: {e}",
            "conversation": {
                "offline_hint": "Repeat a query you ran while online — radio-browser results are cached for one hour.",
            },
        }
