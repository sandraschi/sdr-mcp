"""
Comprehensive tests for SDR MCP Server.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import numpy as np
import pytest

from sdr_mcp.capture import SDRCapture
from sdr_mcp.frequency_db import Band, StationType, get_frequency_database
from sdr_mcp.processor import SDRProcessor

# ── Capture Tests ─────────────────────────────────────────────────────────


class TestSDRCapture:
    def test_device_detection_no_hardware(self):
        """RtlSdr is imported lazily, so we test by patching the method body."""
        capture = SDRCapture()
        with patch.object(capture, "initialize", return_value=False):
            with patch.object(capture, "read_samples", return_value=None):
                assert SDRCapture.is_available() is False
                assert SDRCapture.list_devices() == []

    def test_capture_initialization_mock(self):
        capture = SDRCapture()
        with patch.object(capture, "initialize", return_value=True):
            assert capture.device_index == 0
            assert capture.sample_rate == 2.048e6
            assert capture.center_freq == 227e6
            assert capture.gain == "auto"

    def test_get_info(self):
        capture = SDRCapture()
        info = capture.get_info()
        assert info["device_index"] == 0
        assert info["available"] is False

    @pytest.mark.asyncio
    async def test_initialize_no_rtlsdr(self):
        """The initialize method catches ImportError from pyrtlsdr."""
        capture = SDRCapture()
        # The method catches import errors internally, so calling with no hardware
        # should return False, not raise
        result = await capture.initialize()
        assert result is False

    @pytest.mark.asyncio
    async def test_read_samples_no_sdr(self):
        capture = SDRCapture()
        samples = await capture.read_samples(1024)
        assert samples is None

    @pytest.mark.asyncio
    async def test_set_frequency_no_sdr(self):
        capture = SDRCapture()
        result = await capture.set_frequency(100e6)
        assert result is False

    @pytest.mark.asyncio
    async def test_close_no_sdr(self):
        capture = SDRCapture()
        await capture.close()  # should not raise


# ── Processor Tests ──────────────────────────────────────────────────────


class TestSDRProcessor:
    def test_processor_creation(self):
        processor = SDRProcessor()
        assert processor.fft_size == 2048
        assert processor.sample_rate == 2.048e6
        assert len(processor.window) == 2048

    def test_spectrum_processing_empty_data(self):
        processor = SDRProcessor()
        freqs, spectrum = processor.compute_spectrum([])
        assert len(freqs) == 0
        assert len(spectrum) == 0

    def test_spectrum_with_noise(self):
        processor = SDRProcessor()
        samples = np.random.randn(4096) + 1j * np.random.randn(4096)
        freqs, spectrum = processor.compute_spectrum(samples)
        assert len(freqs) == 2048
        assert len(spectrum) == 2048
        assert np.any(np.isfinite(spectrum))

    def test_spectrum_too_few_samples(self):
        processor = SDRProcessor()
        samples = np.random.randn(100) + 1j * np.random.randn(100)
        freqs, spectrum = processor.compute_spectrum(samples)
        assert len(freqs) == 0
        assert len(spectrum) == 0

    def test_waterfall_operations(self):
        processor = SDRProcessor()
        assert len(processor.get_waterfall_data()) == 0

        fake_spectrum = np.random.randn(2048)
        processor.add_waterfall_line(fake_spectrum)
        waterfall = processor.get_waterfall_data()
        assert len(waterfall) == 1
        assert len(waterfall[0]) == 2048

        processor.clear_waterfall()
        assert len(processor.get_waterfall_data()) == 0

    def test_waterfall_max_history(self):
        processor = SDRProcessor()
        for _ in range(150):
            processor.add_waterfall_line(np.random.randn(2048))
        assert len(processor.get_waterfall_data()) == 100  # max history

    def test_process_samples(self):
        processor = SDRProcessor()
        samples = np.random.randn(4096) + 1j * np.random.randn(4096)
        result = processor.process_samples(samples)
        assert "frequencies" in result
        assert "spectrum" in result
        assert "waterfall" in result
        assert "timestamp" in result
        assert len(result["spectrum"]) > 0

    def test_set_parameters(self):
        processor = SDRProcessor()
        processor.set_parameters(fft_size=1024)
        assert processor.fft_size == 1024
        assert len(processor.window) == 1024

        processor.set_parameters(sample_rate=1e6)
        assert processor.sample_rate == 1e6


# ── Frequency Database Tests ─────────────────────────────────────────────


class TestFrequencyDatabase:
    def test_database_loading(self):
        db = get_frequency_database()
        assert db.get_station_count() > 0
        assert "BBC LW" in db.stations
        assert "ORF LW" in db.stations
        lw = db.get_stations_by_band(Band.LONGWAVE)
        assert len(lw) > 0
        assert all(s.band == Band.LONGWAVE for s in lw)

    def test_station_search(self):
        db = get_frequency_database()
        bbc = db.search_stations("BBC")
        assert len(bbc) > 0
        assert any("BBC" in s.name for s in bbc)

        lw = db.search_stations("", band=Band.LONGWAVE)
        assert len(lw) > 0

    def test_country_filtering(self):
        db = get_frequency_database()
        uk = db.get_stations_by_country("United Kingdom")
        assert len(uk) > 0
        assert all(s.country == "United Kingdom" for s in uk)

        fr = db.get_stations_by_country("France")
        assert len(fr) > 0

    def test_case_insensitive_country(self):
        db = get_frequency_database()
        uk = db.get_stations_by_country("united kingdom")
        assert len(uk) > 0

    def test_get_stations_by_type(self):
        db = get_frequency_database()
        pubs = db.get_stations_by_type(StationType.PUBLIC)
        assert len(pubs) > 0
        assert all(s.station_type == StationType.PUBLIC for s in pubs)

    def test_get_stations_by_frequency_range(self):
        db = get_frequency_database()
        lw = db.get_stations_by_frequency_range(150000, 300000)
        assert len(lw) > 0
        for s in lw:
            assert 150000 <= s.frequency <= 300000

    def test_get_current_program(self):
        db = get_frequency_database()
        prog = db.get_current_program("BBC LW")
        # May be None if off-air, or a ProgramSchedule
        assert prog is None or hasattr(prog, "name")

    def test_get_program_schedule(self):
        db = get_frequency_database()
        schedule = db.get_program_schedule("BBC LW")
        assert len(schedule) > 0

    def test_get_program_schedule_by_day(self):
        db = get_frequency_database()
        schedule = db.get_program_schedule("BBC LW", "monday")
        assert len(schedule) > 0

    def test_nonexistent_station(self):
        db = get_frequency_database()
        assert db.get_current_program("NONEXISTENT") is None
        assert db.get_program_schedule("NONEXISTENT") == []
        assert db.get_stations_by_country("Atlantis") == []

    def test_search_returns_all_with_empty_query(self):
        db = get_frequency_database()
        all_stations = db.search_stations("")
        assert len(all_stations) == db.get_station_count()


# ── Online DB Tests ─────────────────────────────────────────────────────


class TestOnlineDB:
    @pytest.mark.asyncio
    async def test_signal_info_not_found(self):
        from sdr_mcp.online_db import get_signal_info

        result = await get_signal_info("XYZZYX_NONEXISTENT_SIGNAL")
        # Should return None or a SignalInfo with empty fields depending on API
        assert result is None or hasattr(result, "title")

    def test_encode(self):
        from sdr_mcp.online_db import _encode

        assert _encode("hello") == "hello"
        assert "%20" in _encode("hello world")

    def test_strip_html(self):
        from sdr_mcp.online_db import _strip_html

        assert _strip_html("<b>hello</b> world") == "hello world"
        assert _strip_html("no tags") == "no tags"


# ── Transport Tests ─────────────────────────────────────────────────────


class TestTransport:
    def test_get_transport_config_defaults(self):
        from sdr_mcp.transport import get_transport_config

        cfg = get_transport_config()
        assert cfg["transport"] == "stdio"
        assert cfg["host"] == "127.0.0.1"
        assert cfg["port"] == 10891
        assert cfg["path"] == "/mcp"

    def test_create_argument_parser(self):
        from sdr_mcp.transport import create_argument_parser

        parser = create_argument_parser("sdr-mcp")
        assert parser is not None
        args = parser.parse_args([])
        assert args.http is False
        assert args.stdio is False
        assert args.port is None

    def test_resolve_transport_default(self):
        from sdr_mcp.transport import create_argument_parser, resolve_transport

        parser = create_argument_parser("test")
        args = parser.parse_args([])
        transport = resolve_transport(args)
        assert transport in ("stdio", "http", "sse")

    def test_resolve_transport_http(self):
        from sdr_mcp.transport import create_argument_parser, resolve_transport

        parser = create_argument_parser("test")
        args = parser.parse_args(["--http"])
        assert resolve_transport(args) == "http"


# ── CLI Tests ───────────────────────────────────────────────────────────


class TestCLI:
    def test_cli_help(self):
        from click.testing import CliRunner

        from sdr_mcp.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["--help"])
        assert result.exit_code == 0
        assert "SDR MCP" in result.output

    def test_serve_help(self):
        from click.testing import CliRunner

        from sdr_mcp.cli import cli

        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "Start the SDR MCP server" in result.output

    def test_check_no_hardware(self):
        from click.testing import CliRunner

        from sdr_mcp.cli import cli

        with patch("sdr_mcp.capture.SDRCapture.is_available", return_value=False):
            with patch("sdr_mcp.capture.SDRCapture.list_devices", return_value=[]):
                runner = CliRunner()
                result = runner.invoke(cli, ["check"])
                assert result.exit_code == 0


# ── Tool Tests ──────────────────────────────────────────────────────────


class TestSDRTools:
    @pytest.mark.asyncio
    async def test_list_devices_no_hardware(self):
        from sdr_mcp.handlers.state import set_mock_mode
        from sdr_mcp.server import sdr_device

        set_mock_mode(None)
        with patch("sdr_mcp.capture.SDRCapture.is_available", return_value=False):
            with patch("sdr_mcp.capture.SDRCapture.list_devices", return_value=[]):
                result = await sdr_device(operation="list")
                assert result["status"] == "success"
                assert result["mock_mode"] is True

    @pytest.mark.asyncio
    async def test_list_devices_no_hardware_mock_disabled(self):
        from sdr_mcp.handlers.state import set_mock_mode
        from sdr_mcp.server import sdr_device

        set_mock_mode(False)
        try:
            with patch("sdr_mcp.capture.SDRCapture.is_available", return_value=False):
                with patch("sdr_mcp.capture.SDRCapture.list_devices", return_value=[]):
                    result = await sdr_device(operation="list")
                    assert result["status"] == "no_devices"
        finally:
            set_mock_mode(None)

    @pytest.mark.asyncio
    async def test_list_devices_with_hardware(self):
        from sdr_mcp.server import sdr_device

        fake_devices = [{"index": 0, "serial": "0001"}]
        with patch("sdr_mcp.capture.SDRCapture.is_available", return_value=True):
            with patch("sdr_mcp.capture.SDRCapture.list_devices", return_value=fake_devices):
                result = await sdr_device(operation="list")
                assert result["status"] == "success"
                assert result["device_count"] == 1

    @pytest.mark.asyncio
    async def test_tune_preset_valid(self):
        from sdr_mcp.server import sdr_device

        with patch("sdr_mcp.handlers.device.get_sdr_capture") as mock_get:
            mock_cap = MagicMock()
            mock_cap.set_frequency = AsyncMock(return_value=True)
            mock_get.return_value = mock_cap
            result = await sdr_device(operation="tune_preset", preset_name="BBC LW")
            assert result["status"] == "tuned"
            assert result["callsign"] == "BBC LW"

    @pytest.mark.asyncio
    async def test_tune_preset_invalid(self):
        from sdr_mcp.server import sdr_device

        result = await sdr_device(operation="tune_preset", preset_name="NONEXISTENT_PRESET_XYZ")
        assert result["status"] == "station_not_found"

    @pytest.mark.asyncio
    async def test_search_stations(self):
        from sdr_mcp.server import sdr_stations

        result = await sdr_stations(operation="search", query="BBC")
        assert result["status"] == "found"
        assert result["total_results"] > 0

    @pytest.mark.asyncio
    async def test_search_stations_no_results(self):
        from sdr_mcp.server import sdr_stations

        result = await sdr_stations(operation="search", query="XYZZYX_NONEXISTENT")
        assert result["status"] == "no_results"

    @pytest.mark.asyncio
    async def test_get_stations_by_band(self):
        from sdr_mcp.server import sdr_stations

        result = await sdr_stations(operation="by_band", band="LW")
        assert result["status"] == "success"
        assert result["band"] == "LW"

    @pytest.mark.asyncio
    async def test_get_stations_by_invalid_band(self):
        from sdr_mcp.server import sdr_stations

        result = await sdr_stations(operation="by_band", band="INVALID_BAND")
        assert result["status"] == "invalid_band"

    @pytest.mark.asyncio
    async def test_get_program_schedule(self):
        from sdr_mcp.server import sdr_stations

        result = await sdr_stations(operation="schedule", station_callsign="BBC LW")
        assert result["status"] == "success"
        assert "schedule" in result

    @pytest.mark.asyncio
    async def test_get_program_schedule_not_found(self):
        from sdr_mcp.server import sdr_stations

        result = await sdr_stations(operation="schedule", station_callsign="NONEXISTENT")
        assert result["status"] == "station_not_found"

    @pytest.mark.asyncio
    async def test_database_stats(self):
        from sdr_mcp.server import sdr_stations

        result = await sdr_stations(operation="stats")
        assert result["status"] == "success"
        assert result["database_stats"]["total_stations"] > 0

    @pytest.mark.asyncio
    async def test_get_stations_by_country(self):
        from sdr_mcp.server import sdr_stations

        result = await sdr_stations(operation="by_country", country="France")
        assert result["status"] == "success"
        assert result["total_stations"] > 0

    @pytest.mark.asyncio
    async def test_get_stations_by_country_not_found(self):
        from sdr_mcp.server import sdr_stations

        result = await sdr_stations(operation="by_country", country="Atlantis")
        assert result["status"] == "no_stations"

    @pytest.mark.asyncio
    async def test_frequency_set_validation(self):
        from sdr_mcp.server import sdr_device

        result = await sdr_device(operation="set_frequency", frequency_mhz=0.1)  # below 24 MHz min
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_set_gain_invalid(self):
        from sdr_mcp.server import sdr_device

        result = await sdr_device(operation="set_gain", gain="garbage")
        assert result["success"] is False

    @pytest.mark.asyncio
    async def test_get_waterfall_empty(self):
        from sdr_mcp.server import sdr_spectrum

        result = await sdr_spectrum(operation="waterfall")
        assert result["success"] is True
        assert result["lines_count"] >= 0

    @pytest.mark.asyncio
    async def test_query_online_database_empty(self):
        from sdr_mcp.server import sdr_online

        result = await sdr_online(operation="search", query="")
        assert result["status"] in ("no_results", "success", "error")
