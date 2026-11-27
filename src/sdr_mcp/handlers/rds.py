"""RDS decode handler: capture a broadcast FM station and decode its RDS data."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import numpy as np

from ..rds import decode_rds
from .state import _sdr_semaphore, get_sdr_capture, should_use_mock

logger = logging.getLogger(__name__)

FM_MIN_MHZ = 64.0  # includes the OIRT band
FM_MAX_MHZ = 108.0
MIN_DURATION_S = 2.0
MAX_DURATION_S = 60.0
TUNE_OFFSET_HZ = 250e3  # keep the station away from the RTL-SDR DC spike
FLUSH_SAMPLES = 1 << 16


async def decode_station_rds(frequency_mhz: float, duration_s: float = 10.0) -> dict[str, Any]:
    """Tune to an FM station, capture `duration_s` seconds and decode PI, PS, PTY and RadioText."""
    if not FM_MIN_MHZ <= frequency_mhz <= FM_MAX_MHZ:
        return {
            "success": False,
            "frequency_mhz": frequency_mhz,
            "message": f"RDS is carried by FM broadcast stations ({FM_MIN_MHZ:.0f}-{FM_MAX_MHZ:.0f} MHz)",
        }
    duration_s = float(np.clip(duration_s, MIN_DURATION_S, MAX_DURATION_S))

    try:
        capture = get_sdr_capture()
        if getattr(capture, "sdr", None) is None and not await capture.initialize():
            return {"success": False, "message": "SDR device could not be initialized"}

        sample_rate = float(capture.sample_rate)
        total = int(sample_rate * duration_s)
        async with _sdr_semaphore:
            await capture.set_frequency(frequency_mhz * 1e6 + TUNE_OFFSET_HZ)
            await capture.read_samples(FLUSH_SAMPLES)  # drop samples from before the retune
            iq = await capture.read_samples_contiguous(total)
        if iq is None:
            return {"success": False, "frequency_mhz": frequency_mhz, "message": "No samples read from SDR"}

        rds = await asyncio.to_thread(decode_rds, iq, sample_rate, -TUNE_OFFSET_HZ)
    except Exception as e:
        logger.error("RDS decode failed at %.1f MHz: %s", frequency_mhz, e, exc_info=True)
        return {"success": False, "frequency_mhz": frequency_mhz, "message": f"RDS decode failed: {e}"}

    found = rds["groups"] > 0
    if not found:
        message = f"No RDS decoded at {frequency_mhz:.1f} MHz (no station, weak signal, or no RDS)."
    else:
        name = (rds["ps"] or "").strip() or "?"
        message = f"{frequency_mhz:.1f} MHz: {name} (PI {rds['pi']})"
        if rds["radiotext"]:
            message += f" - {rds['radiotext']}"
    return {
        "success": True,
        "rds_found": found,
        "frequency_mhz": frequency_mhz,
        "mock_mode": should_use_mock(),
        "message": message,
        **rds,
    }
