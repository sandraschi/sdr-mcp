#!/usr/bin/env python3
"""Unified GNU Radio receiver supporting FM/AM/SSB and rtl_tcp or HackRF sources."""

from __future__ import annotations

import argparse
import os
import signal
import sys

from gnuradio import analog, blocks, filter, gr
from osmosdr import source


def build_audio_sink(audio_rate: float):
    """Route demodulated audio to UDP (default), PortAudio, or discard."""
    mode = os.getenv("SDR_AUDIO_MODE", "udp").lower()
    if mode in {"off", "none", "null"}:
        return blocks.null_sink(gr.sizeof_float)

    if mode == "portaudio":
        try:
            from gnuradio import audio

            return audio.sink(int(audio_rate), "")
        except Exception:
            pass

    host = os.getenv("SDR_AUDIO_HOST", "127.0.0.1")
    port = int(os.getenv("SDR_AUDIO_PORT", "7355"))
    return blocks.udp_sink(gr.sizeof_float, 1, host, port)


def build_receiver(
    mode: str,
    center_freq_hz: float,
    sample_rate: float,
    gain: float,
    source_type: str,
    source_addr: str,
) -> gr.top_block:
    tb = gr.top_block(f"{source_type}_{mode}_receiver")

    if source_type == "rtl_tcp":
        src = source(args=f"numchan=1 rtl_tcp={source_addr}")
    elif source_type == "hackrf":
        src = source(args="numchan=1 hackrf=0")
    else:
        raise ValueError(f"Unsupported source: {source_type}")

    src.set_sample_rate(sample_rate)
    src.set_center_freq(center_freq_hz)
    src.set_freq_corr(0)
    src.set_gain_mode(False)
    src.set_gain(gain)
    src.set_if_gain(20)
    src.set_bb_gain(20)
    src.set_antenna("")

    channel_width = 200e3 if mode == "fm" else 10e3
    taps = filter.firdes.low_pass(1, sample_rate, channel_width / 2, channel_width / 4)
    lpf = filter.fir_filter_ccf(1, taps)

    audio_decim = max(1, int(sample_rate / 48_000))
    audio_rate = sample_rate / audio_decim
    audio_taps = filter.firdes.low_pass(1, audio_rate, 12e3, 3e3)
    audio_lpf = filter.fir_filter_fff(1, audio_taps)
    resampler = filter.rational_resampler_fff(1, audio_decim)
    sink = build_audio_sink(audio_rate)

    if mode == "fm":
        deviation = 75e3
        quad_gain = sample_rate / (2 * 3.14159 * deviation)
        demod = analog.quadrature_demod_cf(quad_gain)
        tb.connect(src, lpf, demod, audio_lpf, resampler, sink)
    elif mode == "am":
        mag = blocks.complex_to_mag()
        dc = filter.dc_blocker_ff(32)
        tb.connect(src, lpf, mag, dc, audio_lpf, resampler, sink)
    elif mode in {"usb", "lsb"}:
        shift = -2.5e3 if mode == "usb" else 2.5e3
        rotator = blocks.rotator_cc(2 * 3.14159 * shift / sample_rate)
        real = blocks.complex_to_real()
        tb.connect(src, lpf, rotator, real, audio_lpf, resampler, sink)
    else:
        raise ValueError(f"Unsupported mode: {mode}")

    return tb


def main() -> int:
    parser = argparse.ArgumentParser(description="GNU Radio demod receiver")
    parser.add_argument("--mode", choices=["fm", "am", "usb", "lsb"], default="fm")
    parser.add_argument("--source", choices=["rtl_tcp", "hackrf"], default="rtl_tcp")
    parser.add_argument("--freq", type=float, required=True, help="Center frequency in Hz")
    parser.add_argument("--source-addr", default="", help="rtl_tcp host:port when source=rtl_tcp")
    parser.add_argument("--sample-rate", type=float, default=2.0e6)
    parser.add_argument("--gain", type=float, default=20.0)
    args = parser.parse_args()

    if args.source == "rtl_tcp" and not args.source_addr:
        raise SystemExit("--source-addr required for rtl_tcp")

    tb = build_receiver(
        mode=args.mode,
        center_freq_hz=args.freq,
        sample_rate=args.sample_rate,
        gain=args.gain,
        source_type=args.source,
        source_addr=args.source_addr,
    )

    def handle_signal(_signum, _frame):
        tb.stop()
        tb.wait()
        sys.exit(0)

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    tb.start()
    tb.wait()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
