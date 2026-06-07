"""Tests for mock IQ capture and mock mode tooling."""

from unittest.mock import patch

import numpy as np
import pytest

from sdr_mcp.handlers.state import get_mock_mode_label, set_mock_mode, should_use_mock
from sdr_mcp.mock_capture import MockSDRCapture
from sdr_mcp.mock_iq import MockIQGenerator
from sdr_mcp.processor import SDRProcessor


class TestMockIQGenerator:
    def test_generates_complex_samples(self):
        gen = MockIQGenerator(sample_rate=2.048e6)
        samples = gen.generate(4096)
        assert samples.dtype == np.complex128
        assert len(samples) == 4096
        assert np.any(np.isfinite(samples))

    def test_time_advances(self):
        gen = MockIQGenerator(sample_rate=1_000_000, seed=1)
        first = gen.generate(1000)
        second = gen.generate(1000)
        assert not np.allclose(first, second)


class TestMockSDRCapture:
    @pytest.mark.asyncio
    async def test_initialize_and_read(self):
        capture = MockSDRCapture()
        assert await capture.initialize() is True
        samples = await capture.read_samples(8192)
        assert samples is not None
        assert len(samples) == 8192

    @pytest.mark.asyncio
    async def test_set_frequency(self):
        capture = MockSDRCapture()
        assert await capture.set_frequency(101.5e6) is True
        assert capture.center_freq == 101.5e6

    def test_get_info_flags_mock(self):
        capture = MockSDRCapture()
        info = capture.get_info()
        assert info["mock"] is True
        assert info["available"] is True


class TestMockSpectrumPipeline:
    @pytest.mark.asyncio
    async def test_spectrum_with_forced_mock(self):
        set_mock_mode(True)
        try:
            from sdr_mcp.server import sdr_spectrum

            result = await sdr_spectrum(operation="spectrum")
            assert result["status"] == "success"
            assert result["mock_mode"] is True
            assert len(result["spectrum_data"]["spectrum"]) == 2048
        finally:
            set_mock_mode(None)

    @pytest.mark.asyncio
    async def test_waterfall_populates_under_mock(self):
        set_mock_mode(True)
        try:
            from sdr_mcp.server import sdr_spectrum

            result = await sdr_spectrum(operation="waterfall")
            assert result["success"] is True
            assert result["mock_mode"] is True
            assert result["lines_count"] >= 1
        finally:
            set_mock_mode(None)

    @pytest.mark.asyncio
    async def test_mock_mode_operation(self):
        from sdr_mcp.server import sdr_device

        set_mock_mode(None)
        with patch("sdr_mcp.handlers.state.SDRCapture.is_available", return_value=False):
            set_mock_mode(None)
            result = await sdr_device(operation="mock_mode", mock_enabled=True)
            assert result["success"] is True
            assert result["mock_active"] is True
            assert get_mock_mode_label() == "enabled"

        set_mock_mode(None)

    def test_processor_accepts_mock_samples(self):
        processor = SDRProcessor()
        gen = MockIQGenerator()
        samples = gen.generate(4096)
        data = processor.process_samples(samples)
        assert len(data["spectrum"]) == 2048
        assert len(data["waterfall"]) >= 1

    def test_should_use_mock_auto_without_hardware(self):
        set_mock_mode(None)
        with patch("sdr_mcp.handlers.state.SDRCapture.is_available", return_value=False):
            assert should_use_mock() is True
        with patch("sdr_mcp.handlers.state.SDRCapture.is_available", return_value=True):
            assert should_use_mock() is False
