"""Synthetic IQ sample generation for mock / demo SDR mode."""

from __future__ import annotations

import numpy as np

# Tone offsets (Hz from center) and relative amplitudes — visible in FFT/waterfall demos.
_DEFAULT_TONES: tuple[tuple[float, float], ...] = (
    (200_000.0, 0.30),
    (-150_000.0, 0.15),
    (500_000.0, 0.08),
    (300_000.0, 0.20),
)


class MockIQGenerator:
    """Generate complex IQ with noise plus drifting tones."""

    def __init__(
        self,
        sample_rate: float = 2.048e6,
        center_freq: float = 227e6,
        seed: int = 42,
    ) -> None:
        self.sample_rate = sample_rate
        self.center_freq = center_freq
        self._rng = np.random.default_rng(seed)
        self._time_offset = 0.0

    def generate(self, num_samples: int) -> np.ndarray:
        if num_samples <= 0:
            return np.array([], dtype=np.complex128)

        sample_rate = self.sample_rate
        t = np.arange(num_samples, dtype=np.float64) / sample_rate + self._time_offset
        self._time_offset += num_samples / sample_rate

        noise = (
            self._rng.standard_normal(num_samples) + 1j * self._rng.standard_normal(num_samples)
        ) * 0.01

        signal = np.zeros(num_samples, dtype=np.complex128)
        for offset_hz, amplitude in _DEFAULT_TONES:
            drift = 0.0
            if offset_hz == 300_000.0:
                drift = 50_000.0 * np.sin(2 * np.pi * 0.2 * t)
            phase = 2 * np.pi * (offset_hz + drift) * t
            signal += amplitude * np.exp(1j * phase)

        return noise + signal
