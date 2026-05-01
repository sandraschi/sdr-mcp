"""
Online Frequency Database Integration Module

Integrates with:
- radio-browser.info: Internet radio station metadata (no API key, CORS-enabled)
- sigidwiki.com: Signal identification reference (MediaWiki API, no key)

These are the only open APIs available for radio data.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Optional

import httpx

logger = logging.getLogger(__name__)

RADIO_BROWSER_BASE = "https://de1.api.radio-browser.info"
SIGIDWIKI_BASE = "https://www.sigidwiki.com/api.php"

HTTP_TIMEOUT = 15.0


@dataclass
class OnlineStation:
    name: str
    country: str
    language: str
    tags: list[str] = field(default_factory=list)
    codec: str = ""
    bitrate: int = 0
    url: str = ""
    favicon: str = ""
    geo_lat: Optional[float] = None
    geo_long: Optional[float] = None
    stationuuid: str = ""
    clicks: int = 0


@dataclass
class SignalInfo:
    title: str
    description: str = ""
    page_url: str = ""
    category: str = ""
    image_url: str = ""


async def _get_radio_browser_mirror() -> str:
    """Discover fastest radio-browser.info mirror via DNS."""
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("https://all.api.radio-browser.info")
            if resp.status_code == 200:
                mirrors = resp.json()
                if mirrors:
                    return mirrors[0]
    except Exception as e:
        logger.warning(f"radio-browser mirror discovery failed: {e}", exc_info=True)
    return RADIO_BROWSER_BASE


async def search_radio_browser(
    query: str,
    limit: int = 25,
    by: str = "name",
    country: Optional[str] = None,
    language: Optional[str] = None,
    tag: Optional[str] = None,
) -> list[OnlineStation]:
    """Search radio-browser.info for stations.

    Args:
        query: Search term (ignored for by=country/language/tag).
        limit: Max results per endpoint call (max 100).
        by: Search mode: 'name', 'country', 'language', 'tag', or 'search'.
        country: ISO country code or name (used when by='country').
        language: Language code (used when by='language').
        tag: Genre tag (used when by='tag').

    Returns:
        List of OnlineStation matching the query.
    """
    base = await _get_radio_browser_mirror()
    results: list[OnlineStation] = []

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            if by == "country" and country:
                path = f"{base}/json/stations/bycountry/{_encode(country)}"
            elif by == "language" and language:
                path = f"{base}/json/stations/bylanguage/{_encode(language)}"
            elif by == "tag" and tag:
                path = f"{base}/json/stations/bytag/{_encode(tag)}"
            elif by == "search":
                path = f"{base}/json/stations/search?name={_encode(query)}&limit={limit}"
            else:
                path = f"{base}/json/stations/byname/{_encode(query)}"

            if by in ("country", "language", "tag"):
                path += f"?limit={limit}"

            resp = await client.get(path, headers={"User-Agent": "sdr-mcp/0.1"})
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"radio-browser query failed: {e}", exc_info=True)
            return results

    if not isinstance(data, list):
        return results

    for entry in data[:limit]:
        try:
            tags_raw = entry.get("tags", "")
            tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if isinstance(tags_raw, str) else (tags_raw or [])
            station = OnlineStation(
                name=entry.get("name", "Unknown"),
                country=entry.get("country", ""),
                language=entry.get("language", ""),
                tags=tags,
                codec=entry.get("codec", ""),
                bitrate=entry.get("bitrate", 0) or 0,
                url=entry.get("url", ""),
                favicon=entry.get("favicon", ""),
                geo_lat=entry.get("geo_lat"),
                geo_long=entry.get("geo_long"),
                stationuuid=entry.get("stationuuid", ""),
                clicks=entry.get("clicks", 0) or 0,
            )
            results.append(station)
        except Exception:
            continue

    return results


async def get_signal_info(signal_name: str) -> Optional[SignalInfo]:
    """Look up a signal type on the Signal Identification Wiki.

    Args:
        signal_name: Signal name to search for (e.g. 'AM', 'FM', 'DAB').

    Returns:
        SignalInfo with description and links, or None if not found.
    """
    params = {
        "action": "query",
        "list": "search",
        "srsearch": signal_name,
        "srlimit": 3,
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            resp = await client.get(SIGIDWIKI_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
        except Exception as e:
            logger.error(f"SigID wiki query failed: {e}", exc_info=True)
            return None

    try:
        pages = data.get("query", {}).get("search", [])
        if not pages:
            return None
        top = pages[0]
        page_id = top.get("pageid", 0)
        return SignalInfo(
            title=top.get("title", signal_name),
            description=_strip_html(top.get("snippet", "")),
            page_url=f"https://www.sigidwiki.com/wiki/{_encode(top.get('title', signal_name))}",
            category="",
        )
    except Exception as e:
        logger.warning(f"Error parsing sigidwiki response: {e}")
        return None


async def get_signal_categories() -> list[str]:
    """Get list of signal categories from SigID Wiki."""
    params = {
        "action": "query",
        "list": "categorymembers",
        "cmtitle": "Category:Signal",
        "cmlimit": 50,
        "format": "json",
    }

    async with httpx.AsyncClient(timeout=HTTP_TIMEOUT) as client:
        try:
            resp = await client.get(SIGIDWIKI_BASE, params=params)
            resp.raise_for_status()
            data = resp.json()
            members = data.get("query", {}).get("categorymembers", [])
            return [m.get("title", "").replace("Category:", "") for m in members if "Category:" in m.get("title", "")]
        except Exception as e:
            logger.warning(f"Failed to fetch sigidwiki categories: {e}")
            return []


def _encode(text: str) -> str:
    """URL-encode a string."""
    import urllib.parse
    return urllib.parse.quote(text, safe="")


def _strip_html(text: str) -> str:
    """Rough HTML tag stripping."""
    import re
    return re.sub(r"<[^>]+>", "", text).strip()


__all__ = [
    "OnlineStation",
    "SignalInfo",
    "search_radio_browser",
    "get_signal_info",
    "get_signal_categories",
]
