"""Mock RTL-SDR capture — synthetic IQ for demo UI and tests without hardware."""

from __future__ import annotations

import logging

import numpy as np

from .mock_iq import MockIQGenerator

logger = logging.getLogger(__name__)


class MockSDRCapture:
    """Drop-in substitute for SDRCapture when hardware is absent or mock is forced."""

    def __init__(self, device_index: int = 0) -> None:
        self.device_index = device_index
        self.sdr = object()  # truthy sentinel — matches SDRCapture after init
        self.is_running = False
        self.sample_rate = 2.048e6
        self.center_freq = 227e6
        self.gain = "auto"
        self.freq_correction = 60
        self._generator = MockIQGenerator(
            sample_rate=self.sample_rate,
            center_freq=self.center_freq,
        )

    async def initialize(self) -> bool:
        self.is_running = True
        logger.info(
            "Mock SDR active: %.1f MHz, %.1f Msps (synthetic IQ)",
            self.center_freq / 1e6,
            self.sample_rate / 1e6,
        )
        return True

    async def set_frequency(self, frequency: float) -> bool:
        self.center_freq = frequency
        self._generator.center_freq = frequency
        logger.info("Mock frequency set to %.1f MHz", frequency / 1e6)
        return True

    async def set_gain(self, gain: str) -> bool:
        self.gain = gain
        logger.info("Mock gain set to %s", gain)
        return True

    async def read_samples(self, num_samples: int = 1024 * 1024) -> np.ndarray:
        return self._generator.generate(num_samples)

    async def close(self) -> None:
        self.is_running = False
        self.sdr = None
        logger.info("Mock SDR closed")

    def get_info(self) -> dict:
        return {
            "device_index": self.device_index,
            "center_freq": self.center_freq,
            "sample_rate": self.sample_rate,
            "gain": self.gain,
            "freq_correction": self.freq_correction,
            "available": True,
            "mock": True,
            "source": "synthetic_iq",
        }

    @staticmethod
    def list_devices() -> list[dict]:
        return [{"index": 0, "serial": "MOCK-0001", "mock": True}]

    @staticmethod
    def is_available() -> bool:
        return True
