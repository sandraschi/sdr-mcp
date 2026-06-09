"""Tests for async bridge and web API integration."""

import asyncio

import pytest

from sdr_mcp.async_bridge import run_async, set_main_event_loop
from sdr_mcp.web_api import parse_chat_command


@pytest.mark.asyncio
async def test_run_async_from_background_thread():
    loop = asyncio.get_running_loop()
    set_main_event_loop(loop)

    async def sample() -> str:
        await asyncio.sleep(0)
        return "ok"

    result = await asyncio.to_thread(run_async, sample())
    assert result == "ok"


def test_run_async_fallback_without_loop():
    async def sample() -> int:
        return 42

    set_main_event_loop(None)
    assert run_async(sample()) == 42


def test_parse_chat_demod_frequency():
    tool, params = parse_chat_command("demodulate fm at 98.1")
    assert tool == "sdr_gnuradio"
    assert params["operation"] == "start"
    assert params["frequency_mhz"] == 98.1


def test_parse_chat_whats_on_frequency():
    tool, params = parse_chat_command("what's on 89.5")
    assert tool == "sdr_device"
    assert params["operation"] == "set_frequency"
    assert params["frequency_mhz"] == 89.5
