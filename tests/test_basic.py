"""
Basic tests for SDR MCP functionality
"""

from unittest.mock import MagicMock, patch

import pytest

from sdr_mcp.capture import SDRCapture
from sdr_mcp.frequency_db import Band
from sdr_mcp.processor import SDRProcessor


class TestSDRCapture:
    """Test SDR capture functionality."""

    def test_device_detection_no_hardware(self):
        """Test device detection when no hardware is present."""
        with patch('sdr_mcp.capture.RtlSdr', side_effect=ImportError):
            available = SDRCapture.is_available()
            devices = SDRCapture.list_devices()

            assert available is False
            assert devices == []

    def test_capture_initialization_mock(self):
        """Test capture initialization with mocked hardware."""
        with patch('sdr_mcp.capture.RtlSdr') as mock_rtl:
            mock_sdr = MagicMock()
            mock_rtl.return_value = mock_sdr

            capture = SDRCapture()
            # Mock the async initialize method
            capture.initialize = MagicMock(return_value=True)

            # Test that we can create the object
            assert capture.device_index == 0
            assert capture.sample_rate == 2.048e6


class TestSDRProcessor:
    """Test SDR signal processing."""

    def test_processor_creation(self):
        """Test processor initialization."""
        processor = SDRProcessor()

        assert processor.fft_size == 2048
        assert processor.sample_rate == 2.048e6
        assert len(processor.window) == 2048

    def test_spectrum_processing_empty_data(self):
        """Test spectrum processing with empty data."""
        processor = SDRProcessor()

        frequencies, spectrum = processor.compute_spectrum([])

        assert len(frequencies) == 0
        assert len(spectrum) == 0

    def test_waterfall_operations(self):
        """Test waterfall data operations."""
        processor = SDRProcessor()

        # Initially empty
        assert len(processor.get_waterfall_data()) == 0

        # Add some fake data
        fake_spectrum = [1.0] * 100
        processor.add_waterfall_line(fake_spectrum)

        waterfall = processor.get_waterfall_data()
        assert len(waterfall) == 1
        assert len(waterfall[0]) == 100

        # Clear waterfall
        processor.clear_waterfall()
        assert len(processor.get_waterfall_data()) == 0


class TestFrequencyDatabase:
    """Test the frequency database functionality."""

    def test_database_loading(self):
        """Test that the database loads correctly."""
        from sdr_mcp.frequency_db import get_frequency_database

        db = get_frequency_database()

        # Check that we have stations loaded
        assert db.get_station_count() > 0

        # Check specific stations exist
        assert "BBC LW" in db.stations
        assert "ORF LW" in db.stations

        # Check band filtering works
        from sdr_mcp.frequency_db import Band
        lw_stations = db.get_stations_by_band(Band.LONGWAVE)
        assert len(lw_stations) > 0
        assert all(s.band == Band.LONGWAVE for s in lw_stations)

    def test_station_search(self):
        """Test station search functionality."""
        from sdr_mcp.frequency_db import get_frequency_database

        db = get_frequency_database()

        # Search for BBC
        bbc_results = db.search_stations("BBC")
        assert len(bbc_results) > 0
        assert any("BBC" in s.name for s in bbc_results)

        # Search for longwave stations
        lw_results = db.search_stations("", band=Band.LONGWAVE)
        assert len(lw_results) > 0

    def test_country_filtering(self):
        """Test country-based station filtering."""
        from sdr_mcp.frequency_db import get_frequency_database

        db = get_frequency_database()

        # Get UK stations
        uk_stations = db.get_stations_by_country("United Kingdom")
        assert len(uk_stations) > 0
        assert all(s.country == "United Kingdom" for s in uk_stations)

        # Get French stations
        fr_stations = db.get_stations_by_country("France")
        assert len(fr_stations) > 0
        assert all(s.country == "France" for s in fr_stations)


class TestSDRTools:
    """Test SDR MCP tools."""

    @pytest.mark.asyncio
    async def test_list_devices_tool_no_hardware(self):
        """Test the list devices tool when no hardware is present."""
        from sdr_mcp.server import sdr_list_devices

        with patch('sdr_mcp.capture.SDRCapture.is_available', return_value=False):
            with patch('sdr_mcp.capture.SDRCapture.list_devices', return_value=[]):
                result = await sdr_list_devices()

                assert result['status'] == "no_devices"
                assert result['available'] is False
                assert result['device_count'] == 0

    @pytest.mark.asyncio
    async def test_tune_preset_valid(self):
        """Test tuning to a valid preset."""
        from sdr_mcp.server import sdr_tune_preset

        with patch('sdr_mcp.server.get_sdr_capture') as mock_get_capture:
            mock_capture = MagicMock()
            mock_capture.set_frequency.return_value = True
            mock_get_capture.return_value = mock_capture

            result = await sdr_tune_preset("BBC LW")

            assert result['status'] == "tuned"
            assert "BBC" in result['station']
            assert result['callsign'] == "BBC LW"

    @pytest.mark.asyncio
    async def test_search_stations(self):
        """Test the station search tool."""
        from sdr_mcp.server import sdr_search_stations

        result = await sdr_search_stations("BBC")

        assert result['status'] == "found"
        assert result['total_results'] > 0
        assert len(result['stations']) > 0
        assert "conversation" in result

    @pytest.mark.asyncio
    async def test_get_stations_by_band(self):
        """Test getting stations by band."""
        from sdr_mcp.server import sdr_get_stations_by_band

        result = await sdr_get_stations_by_band("LW")

        assert result['status'] == "success"
        assert result['band'] == "LW"
        assert result['total_stations'] > 0
        assert "conversation" in result

    @pytest.mark.asyncio
    async def test_get_program_schedule(self):
        """Test getting program schedule."""
        from sdr_mcp.server import sdr_get_program_schedule

        result = await sdr_get_program_schedule("BBC LW")

        assert result['status'] == "success"
        assert "BBC" in result['station']['name']
        assert "schedule" in result

    @pytest.mark.asyncio
    async def test_database_stats(self):
        """Test database statistics."""
        from sdr_mcp.server import sdr_get_frequency_database_stats

        result = await sdr_get_frequency_database_stats()

        assert result['status'] == "success"
        assert result['database_stats']['total_stations'] > 0
        assert "conversation" in result
