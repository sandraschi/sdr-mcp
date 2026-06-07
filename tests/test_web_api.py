"""Tests for web API chat command parser."""

import os

from sdr_mcp.web_api import get_web_api_config, parse_chat_command


class TestWebApiConfig:
    def test_defaults(self):
        os.environ.pop("SDR_WEB_API_PORT", None)
        host, port = get_web_api_config()
        assert host == "127.0.0.1"
        assert port == 10892

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("SDR_WEB_API_PORT", "10999")
        _, port = get_web_api_config()
        assert port == 10999


class TestChatParser:
    def test_list_devices(self):
        tool, params = parse_chat_command("list devices please")
        assert tool == "sdr_device"
        assert params["operation"] == "list"

    def test_tune_frequency(self):
        tool, params = parse_chat_command("tune to 101.5 mhz")
        assert tool == "sdr_device"
        assert params["operation"] == "set_frequency"
        assert params["frequency_mhz"] == 101.5

    def test_gnuradio_health(self):
        tool, params = parse_chat_command("gnuradio health check")
        assert tool == "sdr_gnuradio"
        assert params["operation"] == "health"

    def test_spectrum(self):
        tool, params = parse_chat_command("show spectrum")
        assert tool == "sdr_spectrum"
        assert params["operation"] == "spectrum"
