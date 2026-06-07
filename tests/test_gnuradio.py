"""Tests for GNU Radio sidecar client and MCP tool."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest


class TestGnuradioClient:
    def test_get_gnuradio_config_defaults(self):
        from sdr_mcp.gnuradio_client import get_gnuradio_config

        config = get_gnuradio_config()
        assert config["service_url"] == "http://127.0.0.1:10900"
        assert config["rtl_tcp_port"] == 1234

    @pytest.mark.asyncio
    async def test_is_reachable_true(self):
        from sdr_mcp.gnuradio_client import GnuradioClient

        client = GnuradioClient()
        with patch.object(client, "health", AsyncMock(return_value={"status": "ok"})):
            assert await client.is_reachable() is True

    @pytest.mark.asyncio
    async def test_is_reachable_false(self):
        from sdr_mcp.gnuradio_client import GnuradioClient

        client = GnuradioClient()
        with patch.object(client, "health", AsyncMock(side_effect=ConnectionError("down"))):
            assert await client.is_reachable() is False


class TestGnuradioTool:
    @pytest.mark.asyncio
    async def test_health_unreachable(self):
        from sdr_mcp.server import sdr_gnuradio

        with patch("sdr_mcp.handlers.gnuradio_ops.GnuradioClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.is_reachable = AsyncMock(return_value=False)
            mock_cls.return_value = mock_client
            result = await sdr_gnuradio(operation="health")
            assert result["status"] == "unreachable"

    @pytest.mark.asyncio
    async def test_start_requires_frequency(self):
        from sdr_mcp.server import sdr_gnuradio

        result = await sdr_gnuradio(operation="start")
        assert result["status"] == "error"
        assert "frequency_mhz" in result["message"]

    @pytest.mark.asyncio
    async def test_start_success(self):
        from sdr_mcp.server import sdr_gnuradio

        with patch("sdr_mcp.handlers.gnuradio_ops.GnuradioClient") as mock_cls:
            mock_client = MagicMock()
            mock_client.start_demod = AsyncMock(
                return_value={"started": True, "pid": 42, "config": {"mode": "fm"}}
            )
            mock_cls.return_value = mock_client
            result = await sdr_gnuradio(operation="start", frequency_mhz=101.5)
            assert result["status"] == "success"
            mock_client.start_demod.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_unknown_operation(self):
        from sdr_mcp.server import sdr_gnuradio

        result = await sdr_gnuradio(operation="nope")
        assert result["status"] == "error"
        assert "valid_operations" in result
