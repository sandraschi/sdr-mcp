"""RDS decoder tests against a synthetic FM broadcast carrying known RDS groups."""

import numpy as np
import pytest

from sdr_mcp.rds import BIT_RATE, OFFSET_WORDS, block_kind, crc10, decode_rds

PI = 0xF214
PS = "TESTFM  "
RADIOTEXT = "HELLO FROM THE SDR-MCP TEST SUITE\r"
PTY = 10  # Pop music


def _block(info: int, offset: str) -> list[int]:
    word = (info << 10) | (crc10(info) ^ OFFSET_WORDS[offset])
    return [(word >> (25 - k)) & 1 for k in range(26)]


def _group(b: int, c: int, d: int) -> list[int]:
    return _block(PI, "A") + _block(b, "B") + _block(c, "C") + _block(d, "D")


def _rds_bits(n_groups: int) -> list[int]:
    text = RADIOTEXT.ljust(4 * ((len(RADIOTEXT) + 3) // 4))
    bits: list[int] = []
    for g in range(n_groups):
        if g % 2 == 0:  # 0A: PS name, two characters per group
            seg = (g // 2) % 4
            b = (0 << 12) | (PTY << 5) | seg
            d = (ord(PS[2 * seg]) << 8) | ord(PS[2 * seg + 1])
            bits += _group(b, PI, d)
        else:  # 2A: RadioText, four characters per group
            seg = (g // 2) % (len(text) // 4)
            chunk = text[4 * seg : 4 * seg + 4]
            b = (2 << 12) | (PTY << 5) | seg
            bits += _group(b, (ord(chunk[0]) << 8) | ord(chunk[1]), (ord(chunk[2]) << 8) | ord(chunk[3]))
    return bits


def _synth_fm_iq(sample_rate: float, offset_hz: float, seconds: float) -> np.ndarray:
    n = int(sample_rate * seconds)
    t = np.arange(n) / sample_rate
    data = np.array(_rds_bits(int(seconds * BIT_RATE / 104) + 2), dtype=np.int8)
    diff = np.bitwise_xor.accumulate(data)  # differential encoding
    half_symbol = (t * 2 * BIT_RATE).astype(np.int64)
    bit = diff[np.minimum(half_symbol // 2, len(diff) - 1)]
    biphase = np.where(bit == 1, 1.0, -1.0) * np.where(half_symbol % 2 == 0, 1.0, -1.0)
    mpx = (
        0.4 * np.sin(2 * np.pi * 1000 * t)  # programme audio
        + 0.09 * np.sin(2 * np.pi * 19e3 * t)  # stereo pilot
        + 0.05 * biphase * np.cos(2 * np.pi * 57e3 * t)  # RDS subcarrier
    )
    phase = 2 * np.pi * 75e3 * np.cumsum(mpx) / sample_rate + 2 * np.pi * offset_hz * t
    rng = np.random.default_rng(1)
    noise = 0.05 * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
    return np.exp(1j * phase) + noise


def test_crc_offsets_roundtrip():
    for name in OFFSET_WORDS:
        word = int("".join(map(str, _block(0x1234, name))), 2)
        assert block_kind(word) == name
    assert block_kind(int("".join(map(str, _block(0x1234, "A"))), 2) ^ 1) is None


@pytest.mark.parametrize("sample_rate", [2.048e6, 1.14e6])
def test_decode_synthetic_station(sample_rate):
    iq = _synth_fm_iq(sample_rate, offset_hz=-250e3, seconds=4.0)
    result = decode_rds(iq, sample_rate, offset_hz=-250e3)

    assert result["groups"] >= 30
    assert result["pi"] == f"{PI:04X}"
    assert result["ps"] == PS
    assert result["ps_dynamic"] is False
    assert result["pty"] == "Pop music"
    assert result["radiotext"] == RADIOTEXT.rstrip("\r")
    assert result["radiotext_complete"] is True


def test_decode_noise_finds_nothing():
    rng = np.random.default_rng(0)
    iq = rng.standard_normal(400_000) + 1j * rng.standard_normal(400_000)
    result = decode_rds(iq, 2.048e6)
    assert result["groups"] == 0
    assert result["ps"] is None


@pytest.mark.asyncio
async def test_rds_operation_validates_frequency():
    from sdr_mcp.tools.device import sdr_device

    assert (await sdr_device(operation="rds"))["success"] is False
    assert (await sdr_device(operation="rds", frequency_mhz=433.92))["success"] is False


def test_auto_mock_mode_follows_active_capture(monkeypatch):
    """Once a hardware capture is open, a re-probe that no longer sees the dongle must not report mock."""
    from sdr_mcp.capture import SDRCapture
    from sdr_mcp.handlers import state
    from sdr_mcp.mock_capture import MockSDRCapture

    monkeypatch.setattr(state, "_mock_mode", None)
    monkeypatch.setattr(SDRCapture, "is_available", staticmethod(lambda: False))

    monkeypatch.setattr(state, "_sdr_capture", SDRCapture())
    assert state.should_use_mock() is False

    monkeypatch.setattr(state, "_sdr_capture", MockSDRCapture())
    assert state.should_use_mock() is True

    monkeypatch.setattr(state, "_sdr_capture", None)
    assert state.should_use_mock() is True


@pytest.mark.asyncio
async def test_list_devices_includes_open_dongle(monkeypatch):
    """A dongle this process has open drops out of enumeration; list must still report it."""
    from sdr_mcp.capture import SDRCapture
    from sdr_mcp.handlers import device, state

    capture = SDRCapture()
    capture.sdr = object()
    capture.serial = "85255996"
    monkeypatch.setattr(state, "_mock_mode", None)
    monkeypatch.setattr(state, "_sdr_capture", capture)
    monkeypatch.setattr(SDRCapture, "is_available", staticmethod(lambda: False))
    monkeypatch.setattr(SDRCapture, "list_devices", staticmethod(lambda: []))

    result = await device.list_devices()
    assert result["available"] is True
    assert result["devices"] == [{"index": 0, "serial": "85255996", "in_use": True}]

    monkeypatch.setattr(SDRCapture, "list_devices", staticmethod(lambda: [{"index": 0, "serial": "85255996"}]))
    result = await device.list_devices()
    assert result["devices"] == [{"index": 0, "serial": "85255996", "in_use": True}]
