"""Tests for online database caching."""

from unittest.mock import AsyncMock, patch

import pytest

from sdr_mcp import online_db
from sdr_mcp.online_db import OnlineStation, search_radio_browser


@pytest.mark.asyncio
async def test_radio_browser_uses_fresh_cache():
    online_db._radio_browser_cache.clear()
    station = OnlineStation(name="Test FM", country="AT", language="German")
    online_db._cache_set_radio("https://cache.test|name|jazz||||25", [station])

    with patch("sdr_mcp.online_db._get_radio_browser_mirror", new=AsyncMock(return_value="https://cache.test")):
        with patch("sdr_mcp.online_db.httpx.AsyncClient") as client_cls:
            results = await search_radio_browser("jazz", limit=25, by="name")
            client_cls.assert_not_called()

    assert len(results) == 1
    assert results[0].name == "Test FM"
