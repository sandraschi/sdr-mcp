# HackRF and Transmit Licensing

## The Short Answer

**HackRF can transmit, but that does not mean you can transmit legally without authorization.**

Buying a HackRF requires no radio license. **Operating it on the air** is regulated
like any other transmitter. What you can do depends on frequency, power, location,
and purpose.

## Why People Think "No License Needed"

Several things get conflated:

1. **Purchase vs operation** — you can buy test equipment without a license; transmitting is separate.
2. **Receive vs transmit** — listening is broadly legal; transmitting is restricted.
3. **ISM band folklore** — some bands (e.g. 2.4 GHz, 868 MHz in EU) allow unlicensed use, but only within strict power and duty-cycle limits. HackRF at full output exceeds those limits.
4. **"For research/education"** — seller disclaimers do not override telecom law.
5. **Shielded testing** — transmitting inside a RF-shielded enclosure is legal; open-air use is not automatically legal.
6. **Amateur radio** — licensed amateurs may transmit on ham bands with their license class limits. The HackRF is not a substitute for a license.

## Austria / EU (relevant for Vienna)

Regulated by **RTR** (Rundfunk und Telekom Regulierungs-GmbH) under EU/CEPT framework.

| Activity | License needed? |
|----------|----------------|
| Receive only (SDR scanning) | Generally yes, legal |
| Transmit on amateur bands (e.g. 144 MHz, 430 MHz) | **Amateur radio license** (ÖVSV) |
| Transmit on ISM bands (868 MHz, 2.4 GHz) | No license, but **strict EIRP/power limits** apply |
| Transmit on FM broadcast, aviation, cellular, emergency | **Illegal** without authorization |
| Testing in shielded lab | Legal with proper setup |

HackRF One specs: 1 MHz–6 GHz, up to ~8 dBm (6 mW) output — enough to violate ISM limits or interfere with licensed services if used carelessly.

## HackRF vs RTL-SDR in sdr-mcp

| Device | TX | RX | sdr-mcp today |
|--------|----|----|---------------|
| RTL-SDR | No | Yes | Native (`pyrtlsdr`) |
| HackRF | Yes | Yes | GNU Radio sidecar (`source=hackrf`) — awkward on Windows USB |

HackRF integration path:

```
HackRF (USB) → SoapySDR → GNU Radio sidecar → sdr-mcp tools
```

Same Docker sidecar pattern as rtl_tcp, but with `source=hackrf` instead. See [GNURADIO.md](GNURADIO.md).

---

## Hardware Buying Guide (for sdr-mcp)

What to buy depends on **receive vs transmit**, **PC dashboard vs portable**, and **budget**.
All tiers below work with sdr-mcp for **spectrum/waterfall** once drivers are installed; only RTL-class
dongles plug into the native `pyrtlsdr` path without the GNU Radio sidecar.

### Quick pick

| You want… | Buy | Typical DE price | sdr-mcp path |
|-----------|-----|------------------|--------------|
| **Cheap RX, good enough** | [NooElec NESDR SMArt](https://www.amazon.de/-/en/NooElec-NESDR-SMArt-Bundle-R820T2-Based-black/dp/B01GDN1T4S) | ~€30–45 | Native RTL (`sdr_device` → `pyrtlsdr`) |
| **Best RX for this repo** | [RTL-SDR Blog v4](https://rtl-sdr.com) / Amazon “RTL-SDR Blog v4” | ~€35–50 | Native RTL — see [RTL_SDR_V4.md](RTL_SDR_V4.md) |
| **No hardware yet** | Nothing — use **mock mode** | €0 | [MOCK_SDR.md](MOCK_SDR.md) |
| **TX + wide band + portable** | [HamGeek R9 + PortaPack H2M](https://www.amazon.de/-/en/R9-PortaPackH2M-Antennas-Plastic-Mounted-Black-White/dp/B0CSJTTN9D) | ~€250–350+ | Sidecar `source=hackrf` + Mayhem offline |
| **Serious TX on ham bands** | Authentic HackRF One (GSG) or vetted clone + **ÖVSV license** | ~€300+ | Sidecar + legal compliance |

### Tier 1 — Standard budget receive-only: NooElec NESDR SMArt

The usual **“cheapo that actually works”** — not the €8 bare PCB sticks.

| Spec | NESDR SMArt (v4/v5 family) |
|------|----------------------------|
| Chipset | RTL2832U + **R820T2** tuner |
| Range | ~100 kHz – 1.75 GHz (HF via direct sampling) |
| Stability | **0.5 ppm TCXO** |
| Connector | **SMA** (female) |
| Enclosure | Aluminum, bias tee (software switchable) |
| TX | **No** (receive only) |

**Why it’s the default budget pick:** SMA, TCXO, shielded case, bias tee — skips the pain of
generic DVB-T dongles (MCX adapters, drift, no HF). Amazon listing
[B01GDN1T4S](https://www.amazon.de/-/en/NooElec-NESDR-SMArt-Bundle-R820T2-Based-black/dp/B01GDN1T4S)
often ships as **v5** with improved HF SNR; same software stack as v4-class RTL-SDRs.

**sdr-mcp:** plug in → Zadig WinUSB → `sdr-mcp check` → `sdr_device(operation='initialize')` →
spectrum/waterfall/WebSocket. No Docker required for basic FFT.

**vs RTL-SDR Blog v4:** NooElec is fine for FM/VHF/scanner use. Blog v4 wins on **hardware image
rejection** and is the repo’s documented reference — worth ~€5–15 extra if you care about UHF
cleanliness and long-term support from rtl-sdr.com.

### Tier 2 — Recommended receive-only: RTL-SDR Blog v4

Project default — full rationale in [RTL_SDR_V4.md](RTL_SDR_V4.md).

- 0.5 ppm TCXO, SMA, bias tee, **hardware image rejection**
- Native `pyrtlsdr` — best fit for `sdr_device`, scan, WebSocket dashboard
- **Receive only** — no legal TX concerns

### Tier 3 — HackRF + PortaPack bundles (e.g. HamGeek R9 + H2M)

Example:
[HamGeek R9 V2.2.0 + PortaPack H2M](https://www.amazon.de/-/en/R9-PortaPackH2M-Antennas-Plastic-Mounted-Black-White/dp/B0CSJTTN9D).

| Component | Role |
|-----------|------|
| **R9** | HackRF One–compatible board (clone; newer “R9” revision) |
| **PortaPack H2M** | Touch UI, battery, speaker — **standalone** Mayhem firmware |
| **Bundle** | Often Mayhem preinstalled, 5 antennas, USB cable |

| Spec | HackRF-class |
|------|--------------|
| Range | ~1 MHz – 6 GHz |
| Bandwidth | up to ~20 MHz |
| TX | **Yes** (~8 dBm) — **license/rules still apply** |
| RX | Yes |

**When it’s worth the money:** transmit experiments (licensed), wideband capture, portable field
tools (Mayhem), ADS-B/POCSAG/etc. on one device — **not** as a cheap RTL replacement.

**sdr-mcp caveats:**

- PC path: `sdr_gnuradio(..., source="hackrf")` via GNU Radio sidecar — **not** native MCP capture
- **Windows:** USB passthrough to Docker is unreliable; run sidecar on host or WSL2 + usbipd
- **PortaPack mounted:** great offline; USB to PC can be finicky (hub sensitivity reported in reviews)
- **Clone QC:** HamGeek/third-party — mixed reviews (shell damage, missing cable, button issues)

Seller also lists **R10 + H4M** as newer — compare revision and price before buying.

### What to skip (for sdr-mcp)

| Item | Why |
|------|-----|
| Bare €8 RTL2832 sticks | MCX, drift, poor HF, driver roulette |
| HackRF bundle **only** for FFT dashboard | Overpriced vs NESDR SMArt; use mock mode until dongle arrives |
| TX without reading RTR/ÖVSV rules | Illegal on most bands — see sections above |

### After purchase (Windows)

1. **RTL dongle:** Zadig → WinUSB on `Bulk-In, Interface 0` ([INSTALL.md](INSTALL.md))
2. **Verify:** `uv run sdr-mcp check`
3. **No dongle yet:** `$env:SDR_MCP_MOCK = "auto"` or mock via `sdr_device(operation='mock_mode')`
4. **HackRF demod:** GNU Radio sidecar up, then `sdr_gnuradio(operation='start', source='hackrf', ...)`

---

- Spectrum **receive** and analysis
- **Shielded** bench testing
- **Licensed amateur** operation on authorized bands
- **Authorized** lab/development with proper permits
- ISM-band experiments at **certified low power** within regulatory limits

## Illegal / Risky Uses

- Jamming (WiFi, GPS, cellular, emergency services)
- Broadcasting on FM/AM without authorization
- Transmitting on aviation or maritime frequencies
- "Because it's open source / educational"

## Bottom Line

HackRF being sold as a development platform does not grant a blanket transmit right.
**License requirements depend on what frequency you use, how much power you emit, and
whether that band is allocated for unlicensed use in your country.**

For sdr-mcp, start with **receive-only RTL-SDR**. Add HackRF later via the GNU Radio
sidecar when you need TX — and only for authorized bands and power levels.
