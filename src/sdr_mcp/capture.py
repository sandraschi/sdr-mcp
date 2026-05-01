"""
RTL-SDR Signal Capture Module

Handles RTL-SDR hardware interaction and raw IQ sample acquisition.
"""

import asyncio
import logging

import numpy as np

logger = logging.getLogger(__name__)


class SDRCapture:
    """RTL-SDR signal capture and configuration."""

    def __init__(self, device_index: int = 0):
        self.device_index = device_index
        self.sdr = None
        self.is_running = False
        self.sample_rate = 2.048e6  # 2.048 MHz
        self.center_freq = 227e6    # 227 MHz (default)
        self.gain = 'auto'
        self.freq_correction = 60   # PPM

    async def initialize(self) -> bool:
        """Initialize the RTL-SDR device."""
        try:
            from rtlsdr import RtlSdr
            self.sdr = RtlSdr()

            # Configure device
            self.sdr.sample_rate = self.sample_rate
            self.sdr.center_freq = self.center_freq
            self.sdr.gain = self.gain
            self.sdr.freq_correction = self.freq_correction

            logger.info(f"RTL-SDR initialized: {self.center_freq/1e6:.1f} MHz, "
                       f"{self.sample_rate/1e6:.1f} Msps")
            return True

        except ImportError:
            logger.warning("pyrtlsdr not installed - SDR functionality disabled")
            return False
        except Exception as e:
            logger.error(f"Failed to initialize RTL-SDR: {e}", exc_info=True)
            return False

    async def set_frequency(self, frequency: float) -> bool:
        """Set the center frequency in Hz."""
        if self.sdr:
            try:
                self.sdr.center_freq = frequency
                self.center_freq = frequency
                logger.info(f"Frequency set to {frequency/1e6:.1f} MHz")
                return True
            except Exception as e:
                logger.error(f"Failed to set frequency: {e}", exc_info=True)
        return False

    async def set_gain(self, gain: str) -> bool:
        """Set the gain ('auto' or numeric value)."""
        if self.sdr:
            try:
                self.sdr.gain = gain
                self.gain = gain
                logger.info(f"Gain set to {gain}")
                return True
            except Exception as e:
                logger.error(f"Failed to set gain: {e}", exc_info=True)
        return False

    async def read_samples(self, num_samples: int = 1024 * 1024) -> np.ndarray | None:
        """Read IQ samples from the SDR without blocking the event loop."""
        if self.sdr:
            try:
                return await asyncio.to_thread(self.sdr.read_samples, num_samples)
            except Exception as e:
                logger.error(f"Failed to read samples: {e}", exc_info=True)
        return None

    async def close(self):
        """Close the SDR device."""
        if self.sdr:
            try:
                self.sdr.close()
                self.sdr = None
                logger.info("RTL-SDR closed")
            except Exception as e:
                logger.error(f"Error closing SDR: {e}", exc_info=True)

    def get_info(self) -> dict:
        """Get current SDR configuration."""
        return {
            'device_index': self.device_index,
            'center_freq': self.center_freq,
            'sample_rate': self.sample_rate,
            'gain': self.gain,
            'freq_correction': self.freq_correction,
            'available': self.sdr is not None
        }

    @staticmethod
    def list_devices() -> list[dict]:
        """List available RTL-SDR devices."""
        try:
            from rtlsdr import RtlSdr
            devices = RtlSdr.get_device_index_by_serial()
            return [{'index': idx, 'serial': serial}
                   for idx, serial in devices.items()]
        except Exception:
            return []

    @staticmethod
    def is_available() -> bool:
        """Check if RTL-SDR is available."""
        try:
            from rtlsdr import RtlSdr
            devices = RtlSdr.get_device_index_by_serial()
            return len(devices) > 0
        except Exception:
            return False