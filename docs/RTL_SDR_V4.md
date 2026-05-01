# RTL-SDR Blog v4

The **recommended SDR receiver** for this project. The v4 is the latest
iteration of the popular RTL-SDR design with significant improvements
over generic dongles and earlier versions.

## Specifications

| Parameter | Value |
|-----------|-------|
| Frequency range | **24 MHz — 1.7 GHz** (direct) |
|               | **0.5 — 24 MHz** (direct sampling mode) |
| Tuner chip | Rafael Micro R828D |
| ADC | RTL2832U (8-bit, ~50 dB dynamic range) |
| Max sample rate | 3.2 Msps (stable at 2.4 Msps) |
| Frequency stability | **0.5 ppm TCXO** (temperature compensated) |
| Connector | **SMA** (female) |
| Enclosure | **Aluminum** with RF shielding |
| Bias Tee | 4.5V, software-switchable |
| Input impedance | 50 ohms |
| Image rejection | Hardware-based (v4 specific) |

## Why v4 Over Generic Dongles

| Feature | Generic $15 dongle | RTL-SDR Blog v4 |
|---------|-------------------|-----------------|
| TCXO | None (50+ ppm drift) | 0.5 ppm (rock stable) |
| Enclosure | Plastic (no shielding) | Aluminum (shielded) |
| Connector | MCX (needs adapter) | SMA (standard) |
| Image rejection | Software only | Hardware + software |
| Bias Tee | Requires soldering | Built-in, switchable |
| HF performance | Poor | Good (direct sampling) |

## Frequency Stability

The v4's **0.5 ppm TCXO** means at 1 GHz the frequency drifts less than
500 Hz regardless of temperature. A generic dongle without TCXO can drift
several kHz as it warms up — enough to lose a narrowband signal entirely.

## Bias Tee

The v4 can power an external LNA (Low Noise Amplifier) or active antenna
through the SMA connector. Enable it via software:

```python
sdr.set_bias(True)  # pyrtlsdr
```

## Direct Sampling Mode

Below 24 MHz the tuner chip stops working. The v4 switches to direct
sampling — connecting the ADC straight to the SMA. This covers the
LW/MW/HF bands (0.5-24 MHz) with reduced but usable sensitivity.

## Where to Buy

- **Official store:** rtl-sdr.com (worldwide shipping, ~$35)
- **Amazon:** Search "RTL-SDR Blog v4" (various sellers)
- **AliExpress:** Official RTL-SDR Blog store

## Alternatives

| Model | Price | Notes |
|-------|-------|-------|
| RTL-SDR Blog v3 | ~$25 | Previous gen, 1 ppm TCXO, no hardware image rejection |
| Nooelec NESDR SMArt | ~$30 | Good build, SMA, bias tee |
| Nooelec NESDR Smartee | ~$45 | v4 equivalent, 0.5 ppm |
| Airspy HF+ Discovery | ~$170 | Much better, but 5x the price |
| HackRF One | ~$300 | Transmit capable, wider bandwidth |
| LimeSDR Mini | ~$200 | Full duplex, 10 MHz bandwidth |
