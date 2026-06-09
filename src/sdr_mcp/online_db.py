"""
Online Frequency Database Integration Module

Integrates with:
- radio-browser.info: Internet radio station metadata (no API key, CORS-enabled)
- sigidwiki.com: Signal identification reference (MediaWiki API, no key)

These are the only open APIs available for radio data.
"""

import logging
import time
from dataclasses import dataclass, field

import httpx

logger = logging.getLogger(__name__)

RADIO_BROWSER_BASE = "https://de1.api.radio-browser.info"
SIGIDWIKI_BASE = "https://www.sigidwiki.com/api.php"

HTTP_TIMEOUT = 15.0
CACHE_TTL_SEC = 3600.0


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
    geo_lat: float | None = None
    geo_long: float | None = None
    stationuuid: str = ""
    clicks: int = 0


@dataclass
class SignalInfo:
    title: str
    description: str = ""
    page_url: str = ""
    category: str = ""
    image_url: str = ""


_radio_browser_cache: dict[str, tuple[float, list[OnlineStation]]] = {}
_signal_info_cache: dict[str, tuple[float, SignalInfo | None]] = {}


def _cache_get_radio(key: str) -> list[OnlineStation] | None:
    entry = _radio_browser_cache.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if time.monotonic() > expires_at:
        _radio_browser_cache.pop(key, None)
        return None
    return value


def _cache_set_radio(key: str, value: list[OnlineStation]) -> None:
    _radio_browser_cache[key] = (time.monotonic() + CACHE_TTL_SEC, value)


def _cache_set_signal(key: str, value: SignalInfo | None) -> None:
    _signal_info_cache[key] = (time.monotonic() + CACHE_TTL_SEC, value)


def _cache_get_signal_stale(key: str) -> SignalInfo | None:
    entry = _signal_info_cache.get(key)
    return entry[1] if entry else None


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
    country: str | None = None,
    language: str | None = None,
    tag: str | None = None,
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
    cache_key = f"{base}|{by}|{query}|{country or ''}|{language or ''}|{tag or ''}|{limit}"
    cached = _cache_get_radio(cache_key)
    if cached is not None:
        return cached

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
            stale = _radio_browser_cache.get(cache_key)
            if stale:
                logger.warning("Returning stale radio-browser cache for offline use")
                return stale[1]
            return results

    if not isinstance(data, list):
        return results

    for entry in data[:limit]:
        try:
            tags_raw = entry.get("tags", "")
            tags = (
                [t.strip() for t in tags_raw.split(",") if t.strip()] if isinstance(tags_raw, str) else (tags_raw or [])
            )
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

    _cache_set_radio(cache_key, results)
    return results


async def get_signal_info(signal_name: str) -> SignalInfo | None:
    """Look up a signal type on the Signal Identification Wiki.

    Args:
        signal_name: Signal name to search for (e.g. 'AM', 'FM', 'DAB').

    Returns:
        SignalInfo with description and links, or None if not found.
    """
    cache_key = signal_name.strip().lower()
    stale_value: SignalInfo | None = None
    entry = _signal_info_cache.get(cache_key)
    if entry:
        expires_at, value = entry
        if time.monotonic() <= expires_at:
            return value
        stale_value = value

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
            if stale_value is not None or cache_key in _signal_info_cache:
                logger.warning("Returning stale SigID cache for offline use")
                return _cache_get_signal_stale(cache_key)
            return None

    try:
        pages = data.get("query", {}).get("search", [])
        if not pages:
            _cache_set_signal(cache_key, None)
            return None
        top = pages[0]
        info = SignalInfo(
            title=top.get("title", signal_name),
            description=_strip_html(top.get("snippet", "")),
            page_url=f"https://www.sigidwiki.com/wiki/{_encode(top.get('title', signal_name))}",
            category="",
        )
        _cache_set_signal(cache_key, info)
        return info
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
    "get_signal_categories",
    "get_signal_info",
    "search_radio_browser",
]
