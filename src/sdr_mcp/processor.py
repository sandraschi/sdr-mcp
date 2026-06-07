"""
SDR Signal Processing Module

Handles FFT calculations, spectrum analysis, and waterfall data generation.
"""

import logging
import time

import numpy as np

logger = logging.getLogger(__name__)


class SDRProcessor:
    """Signal processing for SDR spectrum analysis."""

    def __init__(self, fft_size: int = 2048, sample_rate: float = 2.048e6):
        self.fft_size = fft_size
        self.sample_rate = sample_rate
        self.window = np.hamming(fft_size)
        self.waterfall_history = []
        self.max_history = 100  # Keep 100 waterfall lines

    def compute_spectrum(self, samples: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        """
        Compute power spectrum from IQ samples.

        Returns:
            frequencies: Array of frequency bins
            power_spectrum: Power spectrum in dB
        """
        try:
            # Ensure we have enough samples
            if len(samples) < self.fft_size:
                return np.array([]), np.array([])

            # Take the most recent samples
            iq_data = samples[-self.fft_size :]

            # Apply window function
            windowed = iq_data * self.window

            # Compute FFT
            fft_result = np.fft.fft(windowed)

            # Shift to center DC
            fft_shifted = np.fft.fftshift(fft_result)

            # Compute power spectrum
            power_spectrum = 20 * np.log10(np.abs(fft_shifted) + 1e-12)

            # Generate frequency axis
            freq_step = self.sample_rate / self.fft_size
            frequencies = np.arange(-self.fft_size // 2, self.fft_size // 2) * freq_step

            return frequencies, power_spectrum

        except Exception as e:
            logger.error(f"Error computing spectrum: {e}", exc_info=True)
            return np.array([]), np.array([])

    def add_waterfall_line(self, power_spectrum: np.ndarray):
        """Add a new line to the waterfall history."""
        if len(power_spectrum) > 0:
            # Keep only the most recent lines
            self.waterfall_history.append(power_spectrum.copy())
            if len(self.waterfall_history) > self.max_history:
                self.waterfall_history.pop(0)

    def get_waterfall_data(self) -> list[list[float]]:
        """Get waterfall data as list of lists for JSON serialization."""
        return [line.tolist() for line in self.waterfall_history]

    def get_latest_spectrum(self) -> tuple[list[float], list[float]]:
        """Get the latest spectrum data."""
        if self.waterfall_history:
            latest = self.waterfall_history[-1]
            freq_step = self.sample_rate / self.fft_size
            frequencies = np.arange(-self.fft_size // 2, self.fft_size // 2) * freq_step
            return frequencies.tolist(), latest.tolist()
        return [], []

    def process_samples(self, samples: np.ndarray) -> dict:
        """
        Process IQ samples and return spectrum data for the web interface.

        Returns:
            Dictionary with frequencies, spectrum, and waterfall data
        """
        frequencies, power_spectrum = self.compute_spectrum(samples)

        if len(frequencies) > 0 and len(power_spectrum) > 0:
            self.add_waterfall_line(power_spectrum)

            return {
                "frequencies": frequencies.tolist(),
                "spectrum": power_spectrum.tolist(),
                "waterfall": self.get_waterfall_data(),
                "timestamp": time.time(),
            }

        return {"frequencies": [], "spectrum": [], "waterfall": self.get_waterfall_data(), "timestamp": time.time()}

    def clear_waterfall(self):
        """Clear the waterfall history."""
        self.waterfall_history.clear()

    def set_parameters(self, fft_size: int | None = None, sample_rate: float | None = None):
        """Update processing parameters."""
        if fft_size:
            self.fft_size = fft_size
            self.window = np.hamming(fft_size)
        if sample_rate:
            self.sample_rate = sample_rate
