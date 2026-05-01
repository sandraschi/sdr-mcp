# Software Defined Radio — A Primer

## What is SDR?

Traditional radios use dedicated hardware circuits (oscillators, filters,
demodulators) tuned to one frequency. A **Software Defined Radio** replaces
most of this with software. The hardware digitizes raw radio signals and the
computer does the rest — filtering, demodulating, decoding.

The core idea: **one piece of hardware can receive any signal, on any frequency,
in any mode, just by changing software.**

## How It Works

```
Antenna → LNA (amplifier) → Mixer → ADC (digitizer) → USB → Software
                     ↑
               Local Oscillator
```

1. **Antenna** captures electromagnetic waves
2. **LNA** (Low Noise Amplifier) boosts the weak signal
3. **Mixer** shifts the signal down to a frequency the ADC can handle
4. **ADC** (Analog to Digital Converter) samples the signal → raw IQ data
5. **USB** sends the IQ samples to your computer
6. **Software** (our FFT pipeline) processes the samples into spectrum

## Key Concepts

### Frequency (Hz)
The number of wave cycles per second. Radio bands:
- **LF/LW** (30-300 kHz): Longwave — AM broadcast, long distance
- **MF/MW** (300-3000 kHz): Medium wave — regional AM radio
- **HF/SW** (3-30 MHz): Shortwave — international broadcasting
- **VHF** (30-300 MHz): FM radio, aviation, police
- **UHF** (300-3000 MHz): TV, mobile, WiFi, satellite

### IQ Samples
The ADC outputs two streams: **I** (in-phase) and **Q** (quadrature).
Together they represent the complete radio signal — both amplitude and phase.
This is why SDR is so powerful: with IQ data you can demodulate AM, FM, SSB,
digital modes, all in software.

### FFT (Fast Fourier Transform)
Converts time-domain IQ samples into frequency-domain spectrum data.
Our server uses a **2048-point FFT with Hamming window** to produce
the spectrum display you see in the web dashboard.

### Waterfall
A scrolling 2D plot where the X-axis is frequency, Y-axis is time,
and color represents signal strength. Blue = quiet, red = strong signal.
Useful for spotting intermittent or moving signals.

## Why RTL-SDR?

The RTL2832U chip was originally designed for DVB-T TV reception. In 2012,
developers discovered it could be hacked to output raw IQ samples. This
turned a $20 USB TV dongle into a wideband SDR receiver, democratizing
radio experimentation. The RTL-SDR Blog v4 is the latest evolution of
this hardware.

## Limitations

- **Receive only** — no transmit capability
- **8-bit ADC** — limited dynamic range (~50 dB)
- **No preselection filters** — strong nearby signals can overload the frontend
- **USB bandwidth** limits maximum sample rate to ~2.56 Msps
- **Direct sampling below 24 MHz** — reduced sensitivity on HF/LW
