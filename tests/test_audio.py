"""FM demod and audio relay tests."""

import numpy as np

from sdr_mcp.fm_demod import demod_fm_mono


class TestFmDemod:
    def test_empty_input(self):
        assert demod_fm_mono(np.array([]), 2.048e6).size == 0

    def test_tone_produces_audio(self):
        sample_rate = 2.048e6
        freq = 100_000.0
        t = np.arange(8192) / sample_rate
        iq = np.exp(2j * np.pi * freq * t).astype(np.complex64)
        audio = demod_fm_mono(iq, sample_rate)
        assert audio.dtype == np.float32
        assert audio.size > 0
        assert float(np.max(np.abs(audio))) <= 1.0

    def test_mock_iq_pipeline(self):
        from sdr_mcp.mock_iq import MockIQGenerator

        gen = MockIQGenerator(sample_rate=2.048e6)
        iq = gen.generate(65_536)
        audio = demod_fm_mono(iq, gen.sample_rate)
        assert audio.size > 1000
