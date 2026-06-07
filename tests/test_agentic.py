"""Tests for FastMCP 3.4 sampling tools."""

from unittest.mock import AsyncMock, MagicMock

import pytest


class TestAgenticTools:
    @pytest.mark.asyncio
    async def test_agentic_assist_success(self):
        from sdr_mcp.tools.agentic import sdr_agentic_assist

        ctx = MagicMock()
        ctx.sample = AsyncMock(return_value=MagicMock(text="1. List devices\n2. Tune BBC LW"))
        result = await sdr_agentic_assist("listen to BBC longwave", ctx)
        assert result["success"] is True
        assert "plan" in result

    @pytest.mark.asyncio
    async def test_agentic_assist_no_sampling(self):
        from sdr_mcp.tools.agentic import sdr_agentic_assist

        ctx = MagicMock()
        ctx.sample = AsyncMock(side_effect=RuntimeError("sampling not supported"))
        result = await sdr_agentic_assist("scan FM band", ctx)
        assert result["success"] is False
        assert "recovery_options" in result
