"""RDS (Radio Data System) decoder for wideband FM IQ captures.

Pipeline: IQ -> shift station to baseband -> resample to 228 kHz -> FM demod (MPX)
-> mix 57 kHz subcarrier down -> 19 kHz complex baseband -> Costas loop (BPSK carrier)
-> biphase matched filter + early/late bit timing -> differential decode
-> 26-bit block sync via CRC syndromes -> group decode (PI, PS, PTY, RadioText).

Pure numpy/scipy, no hardware access, so it can be tested on synthetic signals.
"""

from __future__ import annotations

import collections
from fractions import Fraction
from typing import Any

import numpy as np
from scipy import signal

MPX_RATE = 228_000.0  # 4 x 57 kHz
DEMOD_RATE = 2 * MPX_RATE
CHANNEL_CUTOFF_HZ = 150_000.0
RDS_RATE = 19_000.0  # 16 samples per RDS bit
SAMPLES_PER_BIT = 16
BIT_RATE = 1187.5
GROUPS_PER_SECOND = BIT_RATE / 104

CRC_POLY = 0x5B9  # x^10 + x^8 + x^7 + x^5 + x^4 + x^3 + 1
OFFSET_WORDS = {"A": 0x0FC, "B": 0x198, "C": 0x168, "C'": 0x350, "D": 0x1B4}

PTY_NAMES = (
    "None", "News", "Current affairs", "Information", "Sport", "Education", "Drama", "Culture",
    "Science", "Varied", "Pop music", "Rock music", "Easy listening", "Light classical",
    "Serious classical", "Other music", "Weather", "Finance", "Children's programmes",
    "Social affairs", "Religion", "Phone-in", "Travel", "Leisure", "Jazz music", "Country music",
    "National music", "Oldies music", "Folk music", "Documentary", "Alarm test", "Alarm",
)  # fmt: skip

# EN 50067 annex E character table, 0x80-0x9F (the rest of 0x20-0x7E is ASCII)
_EXTRA_CHARS = dict(zip(range(0x80, 0xA0), "áàéèíìóòúùÑÇŞßĲ¡âäêëîïôöûüñçşğıĳ", strict=True))


def rds_char(code: int) -> str:
    if 0x20 <= code < 0x7F:
        return chr(code)
    return _EXTRA_CHARS.get(code, "?")


def crc10(info: int) -> int:
    """10-bit RDS checkword (before the offset word is added) for a 16-bit info word."""
    reg = info << 10
    for i in range(25, 9, -1):
        if reg >> i & 1:
            reg ^= CRC_POLY << (i - 10)
    return reg & 0x3FF


def block_kind(word: int) -> str | None:
    """Return the offset name (A/B/C/C'/D) a 26-bit block is valid for, if any."""
    syndrome = (word & 0x3FF) ^ crc10(word >> 10)
    for name, offset in OFFSET_WORDS.items():
        if syndrome == offset:
            return name
    return None


def fm_mpx(iq: np.ndarray, sample_rate: float, offset_hz: float = 0.0) -> np.ndarray:
    """Demodulate a WFM station at `offset_hz` from the capture centre to MPX at 228 kHz."""
    n = np.arange(len(iq))
    baseband = iq * np.exp(-2j * np.pi * offset_hz / sample_rate * n)
    # Demodulate at 2x the MPX rate: WFM with RDS occupies about +/-135 kHz (Carson),
    # so channel-filtering at the 114 kHz Nyquist of 228 kHz would eat the 57 kHz subcarrier.
    ratio = Fraction(DEMOD_RATE / sample_rate).limit_denominator(1000)
    baseband = signal.resample_poly(baseband, ratio.numerator, ratio.denominator)
    baseband = signal.lfilter(signal.firwin(129, CHANNEL_CUTOFF_HZ, fs=DEMOD_RATE), 1, baseband)
    mpx = np.angle(baseband[1:] * np.conj(baseband[:-1]))
    return signal.resample_poly(mpx, 1, int(DEMOD_RATE / MPX_RATE))


def rds_baseband(mpx: np.ndarray) -> np.ndarray:
    """Mix the 57 kHz RDS subcarrier to 0 Hz and decimate to 19 kHz, unit RMS."""
    n = np.arange(len(mpx))
    baseband = mpx * np.exp(-2j * np.pi * 57e3 / MPX_RATE * n)
    baseband = signal.resample_poly(baseband, 1, int(MPX_RATE / RDS_RATE))
    baseband = signal.lfilter(signal.firwin(161, 2400, fs=RDS_RATE), 1, baseband)
    return baseband / (np.sqrt(np.mean(np.abs(baseband) ** 2)) + 1e-12)


def costas(x: np.ndarray, alpha: float = 0.02, beta: float = 1e-4) -> np.ndarray:
    """BPSK Costas loop; returns the in-phase component after carrier correction."""
    phase = freq = 0.0
    out = np.empty(len(x))
    for i, sample in enumerate(x):
        y = sample * complex(np.cos(phase), -np.sin(phase))
        out[i] = y.real
        err = np.sign(y.real) * y.imag
        freq += beta * err
        phase += freq + alpha * err
    return out


def recover_bits(symbols: np.ndarray) -> np.ndarray:
    """Biphase matched filter, early/late timing, then differential decoding."""
    half = SAMPLES_PER_BIT // 2
    mf = np.correlate(symbols, np.r_[np.ones(half), -np.ones(half)], mode="valid")
    if len(mf) < 4 * SAMPLES_PER_BIT:
        return np.zeros(0, dtype=np.uint8)
    mag = np.abs(mf)
    head = min(len(mag) // SAMPLES_PER_BIT, 3000) * SAMPLES_PER_BIT
    pos = float(np.argmax([mag[o:head:SAMPLES_PER_BIT].mean() for o in range(SAMPLES_PER_BIT)]))
    raw = []
    while pos + 3 < len(mf):
        i = round(pos)
        raw.append(mf[i] > 0)
        err = (mag[min(i + 2, len(mag) - 1)] - mag[max(i - 2, 0)]) / (mag[i] + 1e-9)
        # Clamp so the timing can only nudge, never stall or rewind, the bit clock.
        pos += SAMPLES_PER_BIT + 0.4 * float(np.clip(err, -1.0, 1.0))
    bits = np.array(raw, dtype=np.uint8)
    return bits[1:] ^ bits[:-1]


def iter_groups(bits: np.ndarray):
    """Yield (A, B, C|None, D|None) info words for each group whose A and B blocks check out."""
    n = len(bits) - 25
    if n <= 0:
        return
    words = np.zeros(n, dtype=np.int64)
    for k in range(26):
        words = (words << 1) | bits[k : k + n]
    kinds = [block_kind(int(w)) for w in words]
    i = 0
    while i + 78 < n:
        if kinds[i] == "A" and kinds[i + 26] == "B":
            c = int(words[i + 52] >> 10) if kinds[i + 52] in ("C", "C'") else None
            d = int(words[i + 78] >> 10) if kinds[i + 78] == "D" else None
            yield int(words[i] >> 10), int(words[i + 26] >> 10), c, d
            i += 104
        else:
            i += 1


def decode_groups(groups) -> dict[str, Any]:
    """Aggregate RDS groups into station info (majority vote per PS segment)."""
    pi_votes: collections.Counter[int] = collections.Counter()
    pty_votes: collections.Counter[int] = collections.Counter()
    ps_votes = [collections.Counter() for _ in range(4)]
    ps_sequence: list[str] = []
    ps_complete: collections.Counter[str] = collections.Counter()
    current_ps: list[str | None] = [None] * 4
    radiotext: list[str | None] = [None] * 64
    rt_flag = None
    group_types: collections.Counter[str] = collections.Counter()
    count = 0

    for a, b, c, d in groups:
        count += 1
        pi_votes[a] += 1
        gtype, version = b >> 12, (b >> 11) & 1
        group_types[f"{gtype}{'AB'[version]}"] += 1
        pty_votes[(b >> 5) & 31] += 1
        if gtype == 0 and d is not None:
            seg = b & 3
            pair = rds_char(d >> 8) + rds_char(d & 0xFF)
            ps_votes[seg][pair] += 1
            current_ps[seg] = pair
            if seg == 3 and all(current_ps):
                full = "".join(current_ps)  # type: ignore[arg-type]
                ps_complete[full] += 1
                if not ps_sequence or ps_sequence[-1] != full:
                    ps_sequence.append(full)
                current_ps = [None] * 4
        elif gtype == 2:
            flag = (b >> 4) & 1
            if rt_flag is not None and flag != rt_flag:
                radiotext = [None] * 64  # A/B flag toggle = new message
            rt_flag = flag
            seg = b & 15
            if version == 0 and c is not None and d is not None:
                chars, base = [c >> 8, c & 0xFF, d >> 8, d & 0xFF], seg * 4
            elif version == 1 and d is not None:
                chars, base = [d >> 8, d & 0xFF], seg * 2
            else:
                continue
            for j, ch in enumerate(chars):
                if base + j < 64:
                    radiotext[base + j] = "\r" if ch == 0x0D else rds_char(ch)

    # Prefer a PS received whole; per-segment votes mix messages when the PS scrolls.
    if ps_complete:
        ps = ps_complete.most_common(1)[0][0]
    elif any(ps_votes):
        ps = "".join(v.most_common(1)[0][0] if v else "??" for v in ps_votes)
    else:
        ps = None
    # RadioText is space-padded to 64 chars unless ended by CR; missing segments are NULs.
    rt = "".join(ch if ch is not None else "\x00" for ch in radiotext).split("\r")[0].rstrip("\x00 ")
    rt_complete = bool(rt) and "\x00" not in rt
    rt = rt.replace("\x00", "_").strip() or None
    pty_code = pty_votes.most_common(1)[0][0] if pty_votes else None
    return {
        "groups": count,
        "pi": f"{pi_votes.most_common(1)[0][0]:04X}" if pi_votes else None,
        "ps": ps,
        "ps_sequence": ps_sequence,
        "ps_dynamic": len(ps_complete) > 1,
        "pty_code": pty_code,
        "pty": PTY_NAMES[pty_code] if pty_code is not None else None,
        "radiotext": rt,
        "radiotext_complete": rt_complete,
        "group_types": dict(group_types),
    }


def decode_rds(iq: np.ndarray, sample_rate: float, offset_hz: float = 0.0) -> dict[str, Any]:
    """Decode RDS from a wideband IQ capture with the station at `offset_hz` from centre."""
    mpx = fm_mpx(iq, sample_rate, offset_hz)
    bits = recover_bits(costas(rds_baseband(mpx)))
    result = decode_groups(iter_groups(bits))
    result["duration_s"] = round(len(iq) / sample_rate, 2)
    expected = len(iq) / sample_rate * GROUPS_PER_SECOND
    result["group_rate"] = round(result["groups"] / expected, 2) if expected else 0.0
    return result
