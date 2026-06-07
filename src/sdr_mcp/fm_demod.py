"""Lightweight FM mono demodulation from IQ samples (for WebSocket audio)."""

from __future__ import annotations

import numpy as np
from scipy import signal


def demod_fm_mono(
    iq: np.ndarray,
    sample_rate: float,
    audio_rate: float = 48_000.0,
    deviation_hz: float = 75_000.0,
) -> np.ndarray:
    """Return mono float32 PCM in [-1, 1] from complex IQ."""
    if iq is None or len(iq) < 8:
        return np.array([], dtype=np.float32)

    samples = np.asarray(iq, dtype=np.complex64)
    phase = np.angle(samples[1:] * np.conj(samples[:-1]))
    quad_gain = sample_rate / (2.0 * np.pi * deviation_hz)
    demod = (phase * quad_gain).astype(np.float64)

    cutoff = min(15_000.0, audio_rate * 0.45)
    sos = signal.butter(4, cutoff, btype="low", fs=sample_rate, output="sos")
    filtered = signal.sosfilt(sos, demod)

    target_len = max(1, int(len(filtered) * audio_rate / sample_rate))
    audio = signal.resample(filtered, target_len).astype(np.float32)
    peak = float(np.max(np.abs(audio))) or 1.0
    return np.clip(audio / peak * 0.85, -1.0, 1.0)
