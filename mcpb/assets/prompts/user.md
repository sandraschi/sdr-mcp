# SDR-MCP User Guide

Welcome to SDR-MCP! This guide walks you through common tasks in natural language, from listening to FM radio to scanning the spectrum and using the GNU Radio sidecar.

---

## Tutorial 1: Listen to Local FM Radio

The most common use case: tune to a known FM broadcast frequency and see the spectrum.

### Step 1: Check hardware

First, see if your RTL-SDR dongle is detected:

```python
sdr_device(operation="list")
```

If you see `"available": true` with device serial numbers, you are ready. If you see `"available": false`, the server falls back to mock mode automatically -- you can still follow along with synthetic signals.

### Step 2: Initialize the SDR

```python
sdr_device(operation="initialize")
```

This prepares the radio for IQ sample capture. The default center frequency is 227 MHz.

### Step 3: Tune to a frequency

Tune to a strong local FM station. In most regions, 88-108 MHz is the FM broadcast band. For example, 101.5 MHz:

```python
sdr_device(operation="set_frequency", frequency_mhz=101.5)
```

Or use a named preset if it is in the database:

```python
sdr_device(operation="tune_preset", preset_name="bbc_radio4")
```

### Step 4: View the spectrum

Capture and display the FFT:

```python
sdr_spectrum(operation="spectrum")
```

The response shows frequency bins, power levels (dB), signal count, peak power, average power, and dynamic range. A strong FM signal typically shows a flat-topped peak about 200 kHz wide centered on the carrier frequency, with the pilot tone at 19 kHz.

### Step 5: Start the WebSocket for real-time display

For continuous spectrum monitoring in the web dashboard:

```python
sdr_spectrum(operation="start_websocket")
```

This starts broadcasting FFT data in real time to browser clients. The dashboard at http://127.0.0.1:11118/ shows a live spectrum and waterfall view.

### Step 6: Check the waterfall

The waterfall shows how the spectrum changes over time. Each line is one FFT slice:

```python
sdr_spectrum(operation="waterfall")
```

---

## Tutorial 2: Scan for Active Frequencies

When you don't know what is broadcasting in your area, sweep a frequency range.

### Scan the FM broadcast band

```python
sdr_device(
    operation="scan",
    start_freq=88.0,
    end_freq=108.0,
    step_size=0.2
)
```

This sweeps the entire FM band (88-108 MHz) in 200 kHz steps. The response includes:

- `scan_results`: Per-frequency power readings.
- `signal_analysis`: Count of strong and moderate signals detected.
- `detected_signals`: Up to 10 signals with frequency and power level.
- `band_context`: Information about the band characteristics and typical usage.
- `conversation.next_recommendations`: Suggestions for next steps.

A "strong" signal is one where the peak power exceeds the average by 15 dB or more. A "moderate" signal exceeds by 5-15 dB.

### Scan with finer resolution

For detailed analysis, use a smaller step size:

```python
sdr_device(
    operation="scan",
    start_freq=88.0,
    end_freq=92.0,
    step_size=0.05
)
```

This scans just the lower part of the FM band at 50 kHz steps. The maximum number of steps is 100 per scan.

### Scan the longwave band

```python
sdr_device(
    operation="scan",
    start_freq=0.15,
    end_freq=0.3,
    step_size=0.01
)
```

Longwave signals (150-300 kHz) propagate via ground wave and are very stable. BBC Radio 4 and ORF broadcast on 198 kHz.

### Understanding scan results

Each data point contains:
- `frequency_mhz`: The tuned frequency.
- `max_power_db`: Peak power in dB (higher = stronger signal).
- `spectrum_data`: Full FFT data for that frequency.

The signal detection logic:
- Look for power spikes that stand out from the noise floor.
- Strong signals are 15 dB above average.
- Moderate signals are 5-15 dB above average.

### Validation checks

- The frequency range must be within 24-1766 MHz.
- start_freq must be less than end_freq.
- step_size must be positive.
- The number of steps cannot exceed 100.

---

## Tutorial 3: Capture a Waterfall Spectrum

The waterfall is a time-frequency representation: frequency on the X axis, time on the Y axis (most recent at the bottom), and signal strength as color intensity.

### Basic waterfall capture

```python
# First, get a spectrum reading to fill the history
sdr_spectrum(operation="spectrum")

# Then retrieve the waterfall
sdr_spectrum(operation="waterfall")
```

The waterfall maintains 100 lines of FFT data. Each call to `spectrum` appends a new line.

### Continuous waterfall via WebSocket

For real-time waterfall visualization:

```python
sdr_spectrum(operation="start_websocket")
```

The WebSocket server broadcasts FFT data as soon as it is captured. The dashboard at http://127.0.0.1:11118/ renders this as a scrolling waterfall with color-coded signal strength.

### What to look for in a waterfall

- **Horizontal lines**: Continuous signals (broadcast stations).
- **Sloping lines**: Signals changing frequency (Doppler shift, drifting oscillators).
- **Bursts**: Intermittent transmissions (weather reports, two-way radio).
- **Wide bands**: FM broadcast (200 kHz wide), TV signals (6-8 MHz).
- **Narrow spikes**: CW (Morse code), unmodulated carriers.

### Stop the WebSocket

```python
sdr_spectrum(operation="stop_websocket")
```

Check the streaming status:

```python
sdr_spectrum(operation="websocket_status")
```

---

## Tutorial 4: Find Radio Stations by Band

Use the station database to discover what is broadcasting on each frequency band.

### List all longwave stations

```python
sdr_stations(operation="by_band", band="LW")
```

This returns stations on the longwave band (150-300 kHz) with their frequency, country, power, and type. Longwave is primarily used by European public broadcasters.

### List other bands

```python
sdr_stations(operation="by_band", band="MW")   # Medium wave, 530-1700 kHz
sdr_stations(operation="by_band", band="SW")   # Shortwave, 3-30 MHz
sdr_stations(operation="by_band", band="VHF")  # VHF, 30-300 MHz
sdr_stations(operation="by_band", band="UHF")  # UHF, 300-3000 MHz
```

### Search for specific stations

By name:

```python
sdr_stations(operation="search", query="BBC")
```

By name with band filter:

```python
sdr_stations(operation="search", query="France", band="LW")
```

By country:

```python
sdr_stations(operation="by_country", country="France")
```

### Get program schedules

See what is currently playing and the full weekly schedule:

```python
sdr_stations(operation="schedule", station_callsign="BBC LW")
```

For a specific day:

```python
sdr_stations(operation="schedule", station_callsign="ORF LW", day="monday")
```

The current program is detected automatically based on your local time.

### Database statistics

```python
sdr_stations(operation="stats")
```

This returns total stations, countries, bands, types, languages, and total transmitter power.

---

## Tutorial 5: Use GNU Radio for Deeper Demodulation

The GNU Radio sidecar (Docker container) provides FM, AM, USB, and LSB demodulation via rtl_tcp. Audio is relayed over UDP to your speakers and the dashboard.

### Prerequisites

- Docker Desktop installed and running.
- rtl_tcp running on the host.
- The GNU Radio container started (`just gnuradio-up`).

### Check sidecar health

```python
sdr_gnuradio(operation="health")
```

If unreachable, follow the setup steps in the response:
1. Start rtl_tcp: `scripts/start-rtl-tcp.ps1`
2. Start sidecar: `just gnuradio-up`

### Start FM demodulation

The GNU Radio sidecar connects to rtl_tcp on the host, receives IQ samples, performs FM demodulation, and streams PCM audio over UDP to port 7355.

```python
sdr_gnuradio(
    operation="start",
    mode="fm",
    frequency_mhz=101.5
)
```

The `mode` parameter supports:
- `fm`: Wideband FM (broadcast, 200 kHz bandwidth).
- `am`: Amplitude Modulation (MW/LW broadcast, shortwave).
- `usb`: Upper Sideband (ham radio, utility stations).
- `lsb`: Lower Sideband (ham radio, shortwave).

The `source` parameter (default `rtl_tcp`) can be set to `hackrf` for HackRF hardware.

### Start AM demodulation

```python
sdr_gnuradio(
    operation="start",
    mode="am",
    frequency_mhz=909.0,
    gain=30.0
)
```

AM is used by medium wave broadcasters (530-1700 kHz) and shortwave international broadcasters (3-30 MHz).

### Check demod status

```python
sdr_gnuradio(operation="status")
```

### Stop demodulation

```python
sdr_gnuradio(operation="stop")
```

### List devices available to the sidecar

```python
sdr_gnuradio(operation="list_devices")
```

### Audio routing

Audio from the GNU Radio sidecar flows through:
1. UDP PCM on port 7355 from the Docker container to the host.
2. The `AudioRelay` module fans out PCM data to:
   - Local speakers via `sounddevice` (if available).
   - WebSocket subscribers (browser dashboard).
3. Native Python FM demod (when sidecar is inactive) streams directly over WebSocket.

### Validation checks for start

- `frequency_mhz` is required and must be within 24-1766 MHz.
- `mode` must be one of: fm, am, usb, lsb.
- `source` must be one of: rtl_tcp, hackrf.

---

## Tutorial 6: Set Up Mock Mode for Testing

Mock mode lets you use all SDR-MCP features without a physical RTL-SDR dongle. The server generates synthetic IQ samples with four drifting tones -- the FFT, waterfall, and WebSocket streaming all work identically.

### Auto mock mode (default)

When `SDR_MCP_MOCK` is unset or set to `"auto"`, the server checks for RTL-SDR hardware. If none is detected, mock mode activates automatically:

```python
sdr_device(operation="list")
# Returns: mock_mode=True, serial="MOCK-0001"
```

### Force enable mock mode

```python
sdr_device(operation="mock_mode", mock_enabled=True)
```

This forces synthetic IQ even when an RTL-SDR is connected. Useful for:
- Testing the dashboard and WebSocket without occupying the radio.
- Demonstrating the software without hardware.
- Developing new features without a dongle.

### Force disable mock mode

```python
sdr_device(operation="mock_mode", mock_enabled=False)
```

This forces hardware capture mode. Returns an error if no dongle is connected.

### Query mock mode status

```python
sdr_device(operation="mock_mode")
```

Omitting `mock_enabled` returns the current mode without changing it.

### Using mock mode

All tools work identically in mock mode:

```python
# Initialize (always succeeds in mock)
sdr_device(operation="initialize")

# Get spectrum with synthetic tones
sdr_spectrum(operation="spectrum")
# You will see 3-4 peaks in the FFT from the synthetic tones

# Get waterfall
sdr_spectrum(operation="waterfall")

# Start WebSocket for real-time dashboard
sdr_spectrum(operation="start_websocket")
```

The synthetic IQ generator creates tones at specific offsets from center frequency:
- +200 kHz at 0.30 amplitude (strong)
- -150 kHz at 0.15 amplitude (moderate)
- +500 kHz at 0.08 amplitude (weak)
- +300 kHz at 0.20 amplitude (moderate, slowly drifting)

### Environment variable control

Set `SDR_MCP_MOCK` at startup:

```powershell
$env:SDR_MCP_MOCK = "enable"
uv run sdr-mcp serve
```

Or for the session:
```powershell
$env:SDR_MCP_MOCK = "disable"
uv run sdr-mcp serve
```

### Tips for mock mode

- The drifting tone at +300 kHz varies by +-50 kHz at 0.2 Hz, creating a moving peak in the waterfall. This helps test time-varying signal visualization.
- Change the mock mode at runtime with `sdr_device(operation="mock_mode", mock_enabled=True/False)` -- no restart needed.
- Mock mode status is included in every spectrum and waterfall response.

---

## Tutorial 7: Search Online Radio Databases

For stations not in the local database, SDR-MCP queries radio-browser.info (25k+ stations, no API key needed).

### Search by station name

```python
sdr_online(operation="search", query="BBC World Service")
```

Returns up to 25 results with name, country, language, tags, codec, bitrate, stream URL, and popularity (clicks).

### Search by tag

```python
sdr_online(operation="search", tag="jazz", limit=10)
```

### Search by country

```python
sdr_online(operation="search", country="Germany")
```

### Search by language

```python
sdr_online(operation="search", language="French")
```

### Search with multiple filters

```python
sdr_online(operation="search", tag="classical", country="United Kingdom", limit=5)
```

### Identify a signal type

The Signal Identification Wiki lookup tells you what a modulation or signal format is:

```python
sdr_online(operation="signal_id", query="DAB+")
sdr_online(operation="signal_id", query="ATSC 3.0")
sdr_online(operation="signal_id", query="NOAA APT")
```

### Caching

radio-browser.info results are cached for one hour. sigidwiki.com results are also cached for one hour. Stale cache is returned when the network is unavailable.

---

## Tutorial 8: Use the Agentic Sampling Tools

If your MCP host supports FastMCP sampling (Cursor with sampling enabled), you can use the agentic tools for multi-step workflow planning.

### Get a research plan

```python
sdr_agentic_assist(goal="Listen to BBC Radio 4 on longwave and capture the spectrum")
```

Returns a step-by-step plan referencing concrete MCP tools and operations.

### Get frequency suggestions

```python
sdr_sampling_hint(topic="shortwave broadcasts from Europe at night")
```

Returns recommended frequencies, bands, and tool sequences.

### Fallback

If sampling is not available, the response includes `recovery_options` with manual tool call suggestions.

```python
{"success": False, "error": "Sampling not supported",
 "recovery_options": ["Run tools manually: sdr_device(operation='list'), sdr_spectrum(operation='spectrum')"]}
```

---

## Tutorial 9: End-to-End Workflow -- FM Radio Discovery

A complete workflow to discover and listen to FM radio:

### Step 1: Hardware check

```python
sdr_device(operation="list")
```

If no hardware, enable mock mode to follow along with synthetic signals:

```python
sdr_device(operation="mock_mode", mock_enabled=True)
```

### Step 2: Initialize

```python
sdr_device(operation="initialize")
```

### Step 3: Scan the FM band

```python
sdr_device(operation="scan", start_freq=88.0, end_freq=108.0, step_size=0.2)
```

Note the detected frequencies and their signal strengths.

### Step 4: Tune to the strongest signal

```python
sdr_device(operation="set_frequency", frequency_mhz=101.5)
```

### Step 5: Capture spectrum

```python
sdr_spectrum(operation="spectrum")
```

### Step 6: Start WebSocket streaming

```python
sdr_spectrum(operation="start_websocket")
```

### Step 7: (Optional) Start GNU Radio FM demod

```python
sdr_gnuradio(operation="start", mode="fm", frequency_mhz=101.5)
```

### Step 8: Check the waterfall

```python
sdr_spectrum(operation="waterfall")
```

---

## Tutorial 10: End-to-End Workflow -- Longwave DX

Longwave (150-300 kHz) provides extremely stable signals that travel hundreds of kilometers. This is ideal for receiving European public broadcasters.

### Step 1: Initialize and tune

```python
sdr_device(operation="initialize")
sdr_device(operation="tune_preset", preset_name="bbc_radio4")
```

### Step 2: Check the schedule

```python
sdr_stations(operation="schedule", station_callsign="BBC LW")
```

### Step 3: Capture spectrum

```python
sdr_spectrum(operation="spectrum")
```

### Step 4: Scan the longwave band

```python
sdr_device(operation="scan", start_freq=0.15, end_freq=0.3, step_size=0.01)
```

### Step 5: Search for more stations

```python
sdr_stations(operation="by_band", band="LW")
sdr_stations(operation="search", query="ORF")
```

---

## Troubleshooting

### No RTL-SDR hardware detected

1. Is the dongle plugged in? Try a different USB port.
2. Are the drivers installed? On Windows, use Zadig to replace the DVB-T driver with WinUSB.
3. Is another application using the device? Close SDR#, GQRX, or other SDR software.
4. Try mock mode: `sdr_device(operation="mock_mode", mock_enabled=True)`.

### "Failed to initialize SDR device"

1. Check hardware: `sdr_device(operation="list")`.
2. Restart the server: `uv run sdr-mcp serve`.
3. Try a different USB port.
4. Check Windows Device Manager for driver conflicts.

### WebSocket server won't start

1. Port 8765 may be in use. Stop other applications using that port.
2. Check status: `sdr_spectrum(operation="websocket_status")`.
3. If already running, connect to it rather than starting a new one.

### GNU Radio sidecar unreachable

1. Is Docker running? `docker ps`.
2. Is the sidecar container running? `docker ps | findstr gnuradio`.
3. Start it: `just gnuradio-up`.
4. Is rtl_tcp running on the host? `scripts/start-rtl-tcp.ps1`.
5. Check the health: `sdr_gnuradio(operation="health")`.

### Frequency out of range

The RTL-SDR operates from 24 MHz to 1.766 GHz. Some frequencies below 24 MHz may be accessible via direct sampling mode on certain dongles (e.g., RTL-SDR Blog v4). If you get a range error, check the frequency is within 24-1766 MHz.

### Gain errors

Gain must be "auto" or a numeric value between 0 and 49.6 dB. Values outside this range are rejected.

### "Scan would take too many steps"

The scan operation is limited to 100 steps. Increase `step_size` or narrow the frequency range. For example, scanning 88-108 MHz at 1 MHz steps (20 steps) works, but scanning at 0.01 MHz steps (2000 steps) does not.

### Online database returns no results

1. Check your internet connection.
2. radio-browser.info may be temporarily unavailable.
3. Try a simpler query: `sdr_online(operation="search", query="BBC")`.
4. Results are cached for one hour. Stale results are returned when offline.

### Spectrum data shows no signals

1. The SDR may not be initialized: `sdr_device(operation="initialize")`.
2. Noise floor too high: check the gain setting.
3. No signals on the current frequency: try a scan.
4. In mock mode, synthetic tones should always be visible.

### Dashboard not loading

1. Is the frontend dev server running? `cd web_sota && npm run dev`.
2. Is the REST bridge running? Check that `--no-web-api` was not passed.
3. Default frontend URL: http://127.0.0.1:11118/.
4. Default REST bridge: http://127.0.0.1:10892/.

### Port conflicts

The server uses ports 11118-10892. If any are in use:
1. Kill the conflicting process: `Get-NetTCPConnection -LocalPort 11118 | Stop-Process`.
2. Override with environment variables: `MCP_PORT=10895 SDR_WEB_API_PORT=10896`.
3. The `start.ps1` script clears ports automatically.

### Mock mode not activating

1. Check `SDR_MCP_MOCK` environment variable: `$env:SDR_MCP_MOCK` should not be "disable".
2. Force it: `sdr_device(operation="mock_mode", mock_enabled=True)`.
3. Verify the response shows `"mock_active": True`.

### GNU Radio demod audio not playing

1. Audio relay status: `sdr_spectrum(operation="audio_status")`.
2. The `AudioRelay` listens on UDP port 7355 for PCM float32 mono.
3. Local speaker playback requires `sounddevice` and working audio drivers.
4. Browser audio flows through the WebSocket connection.

### CLI commands

```powershell
# Check hardware
uv run sdr-mcp check

# Start server (STDIO mode, for Claude Desktop)
uv run sdr-mcp serve

# Start server (HTTP mode, for web dashboard)
uv run sdr-mcp serve --http

# Quick hardware test
uv run sdr-mcp test --frequency 101.5

# Test with specific gain
uv run sdr-mcp test --frequency 101.5 --gain 20.0
```

### WebSocket data format

The WebSocket server broadcasts JSON messages:

```python
{
    "type": "spectrum",
    "frequencies": [-1024000.0, ..., 1024000.0],  # Hz offsets from center
    "spectrum": [-45.2, ..., -50.1],               # dB values
    "waterfall": [[...], [...]],                   # Last 100 lines
    "center_freq": 101500000,                       # Center frequency in Hz
    "timestamp": 1700000000.0
}
```

Clients can also send commands over WebSocket:
```python
{"command": "set_frequency", "frequency": 101.5}
{"command": "set_gain", "gain": "auto"}
```

### Longwave presets at a glance

| Preset Name | Station | Frequency | Country | Power |
|-------------|---------|-----------|---------|-------|
| orf_longwave | ORF Radio Osterreich 1 | 198 kHz | Austria | 100 kW |
| bbc_radio4 | BBC Radio 4 | 198 kHz | United Kingdom | 500 kW |
| france_inter | France Inter | 162 kHz | France | 2000 kW |
| rtl_luxembourg | RTL Radio | 234 kHz | Luxembourg | 300 kW |

Note: BBC Radio 4 and ORF both broadcast on 198 kHz but at different transmitter sites (Droitwich vs. Moosbrunn). Depending on your location, one will dominate.

#---

## Tutorial 11: Use the Web API REST Bridge

The web dashboard at http://127.0.0.1:11118/ communicates with the backend through a REST API bridge on port 10892. You can send natural language chat commands or direct tool invocations to this API.

### Chat endpoint

Send a plain-text command and the server maps it to the correct tool:

```python
POST /api/chat
{"message": "tune to 101.5 MHz"}
```

The server's `parse_chat_command` function recognizes these patterns:

- "list devices", "find device", "check hardware" -> `sdr_device(operation="list")`
- "initialize", "init sdr" -> `sdr_device(operation="initialize")`
- "spectrum", "fft" -> `sdr_spectrum(operation="spectrum")`
- "waterfall" -> `sdr_spectrum(operation="waterfall")`
- "tune to 101.5 MHz" -> `sdr_device(operation="set_frequency", frequency_mhz=101.5)`
- "whats on 101.5" -> `sdr_device(operation="set_frequency", frequency_mhz=101.5)`
- "bbc", "longwave", "preset" -> `sdr_device(operation="tune_preset", preset_name="bbc_radio4")`
- "enable mock" -> `sdr_device(operation="mock_mode", mock_enabled=True)`
- "disable mock" -> `sdr_device(operation="mock_mode", mock_enabled=False)`
- "search stations BBC" -> `sdr_stations(operation="search", query="BBC")`
- "demod 101.5" -> `sdr_gnuradio(operation="start", frequency_mhz=101.5, mode="fm")`
- "stop demod" -> `sdr_gnuradio(operation="stop")`
- "gnuradio health" -> `sdr_gnuradio(operation="health")`
- "gnuradio status" -> `sdr_gnuradio(operation="status")`

### Direct invoke endpoint

For precise control, send the exact tool name and parameters:

```python
POST /api/invoke
{"tool": "sdr_device", "params": {"operation": "scan", "start_freq": 88.0, "end_freq": 108.0, "step_size": 0.2}}
```

### Status endpoint

Get a full hardware + mock + GNU Radio snapshot:

```
GET /api/status
```

Returns MCP status, hardware availability and initialization state, mock mode status, and GNU Radio reachability with demod state.

### Health endpoint

```
GET /api/health
{"status": "ok", "service": "sdr-mcp-web-api"}
```

### Using curl to test the REST bridge

```powershell
# Health check
curl http://127.0.0.1:10892/api/health

# Status snapshot
curl http://127.0.0.1:10892/api/status

# Send a chat command
curl -X POST http://127.0.0.1:10892/api/chat -H "Content-Type: application/json" -d '{"message": "spectrum"}'

# Invoke a tool directly
curl -X POST http://127.0.0.1:10892/api/invoke -H "Content-Type: application/json" -d '{"tool": "sdr_device", "params": {"operation": "health"}}'
```

---

## Tutorial 12: Understanding FFT and Spectrum Data

The 2048-point FFT is the core of SDR-MCP's spectrum analysis. Here is what the data means and how to interpret it.

### How spectrum capture works

1. The RTL-SDR captures 1 million complex IQ samples at 2.048 MHz sample rate.
2. The processor takes the latest 2048 samples and applies a Hamming window (reduces spectral leakage).
3. An FFT converts the time-domain samples to frequency-domain power levels.
4. The result is shifted so DC (0 Hz) is at the center.
5. Power is converted to dB scale: `20 * log10(|FFT|)`.

### Understanding the return data

```python
{
    "frequencies": [-1024000.0, -1023000.0, ..., 1023000.0, 1024000.0],
    # 2048 frequency bins, each 1000 Hz apart (2.048 MHz / 2048)
    # Values are offsets from the center frequency in Hz

    "spectrum": [-45.2, -44.8, ..., -50.1, -48.3],
    # Power in dB for each frequency bin
    # Higher values = stronger signals

    "waterfall": [[...], [...]],
    # Last 100 spectrum captures for time-varying display
}
```

### Reading the analysis section

```python
"analysis": {
    "signal_count": 3,       # Number of peaks >10 dB above average
    "peak_power": -22.5,     # Highest power level in dB
    "average_power": -45.2,  # Average noise floor
    "dynamic_range": 38.7    # Peak-to-peak range in dB
}
```

- **signal_count**: How many potential signals are visible. Each peak 10 dB above the noise floor counts as one signal.
- **peak_power**: The strongest signal in the current capture. FM broadcast typically peaks at -20 to -40 dB.
- **average_power**: The noise floor. Lower values (more negative) mean cleaner reception.
- **dynamic_range**: The difference between the weakest and strongest signals. Higher is better.

### Frequency resolution

Resolution = sample_rate / fft_size = 2.048 MHz / 2048 = 1 kHz per bin

This means each FFT bin represents a 1 kHz slice of spectrum. FM broadcast signals (200 kHz wide) span about 200 bins. Longwave AM (9 kHz) spans about 9 bins.

### Waterfall interpretation

The waterfall has 100 horizontal lines. Each is one FFT capture:
- The newest capture is at the bottom (or top, depending on the viewer).
- Frequency runs left to right.
- Color intensity represents signal power.
- Moving signals appear as diagonal or wavy patterns.

---

## Tutorial 13: Setting Up the GNU Radio Sidecar

The GNU Radio sidecar provides professional-grade demodulation through a Docker container.

### Docker setup

The sidecar consists of:
1. **rtl_tcp**: Runs on the Windows host, serves IQ samples over TCP port 1234.
2. **GNU Radio container**: Connects to rtl_tcp, processes IQ samples, outputs demodulated PCM audio over UDP port 7355.

### Step 1: Start rtl_tcp

Run this on the Windows host (not in Docker -- it needs direct USB access):

```powershell
# From the repo root
scripts/start-rtl-tcp.ps1
```

Or manually:
```powershell
rtl_tcp -a 127.0.0.1 -p 1234
```

### Step 2: Start the GNU Radio container

```powershell
just gnuradio-up
```

This starts the Docker container with the GNU Radio demod service listening on http://127.0.0.1:11223/.

### Step 3: Verify connectivity

```python
sdr_gnuradio(operation="health")
# Expected: {"status": "success", "service_url": "http://127.0.0.1:11223"}
```

### Step 4: Start demodulation

```python
sdr_gnuradio(operation="start", mode="fm", frequency_mhz=101.5)
```

Audio flows from: rtl_tcp -> GNU Radio container (FM demod) -> UDP port 7355 -> AudioRelay -> speakers + WebSocket.

### Supported demodulation modes

| Mode | Bandwidth | Typical Use |
|------|-----------|-------------|
| fm | 200 kHz | FM broadcast (88-108 MHz) |
| am | 9-10 kHz | MW/LW broadcast, shortwave |
| usb | 2.4 kHz | Ham radio, utility stations |
| lsb | 2.4 kHz | Ham radio, shortwave |

### Environment variables for the sidecar

| Variable | Default | Description |
|----------|---------|-------------|
| GNURADIO_DEMOD_URL | http://127.0.0.1:11223 | GNU Radio HTTP API |
| RTL_TCP_HOST | 127.0.0.1 | rtl_tcp host address |
| RTL_TCP_PORT | 1234 | rtl_tcp TCP port |

### When rtl_tcp runs in Docker with host networking

If rtl_tcp runs inside Docker with `--network host`, set:

```python
sdr_gnuradio(
    operation="start",
    mode="fm",
    frequency_mhz=101.5,
    source="rtl_tcp",
    rtl_tcp_host="host.docker.internal",
    rtl_tcp_port=1234
)
```

---

## Tutorial 14: Multi-Step Radio Research

Combine tools for a complete radio monitoring session.

### Scenario: Explore the FM band and identify unknown signals

```python
# 1. Check hardware and initialize
sdr_device(operation="list")
sdr_device(operation="initialize")

# 2. Scan the full FM band
sdr_device(operation="scan", start_freq=88.0, end_freq=108.0, step_size=0.2)

# 3. Tune to each detected frequency and capture spectrum
sdr_device(operation="set_frequency", frequency_mhz=95.3)
sdr_spectrum(operation="spectrum")

# 4. Look up FM broadcast signal info
sdr_online(operation="signal_id", query="FM broadcast")

# 5. Start WebSocket for real-time waterfall
sdr_spectrum(operation="start_websocket")

# 6. Start FM demod on the strongest signal
sdr_gnuradio(operation="start", mode="fm", frequency_mhz=95.3)

# 7. Check the audio relay
sdr_spectrum(operation="audio_status")

# 8. Stop when done
sdr_gnuradio(operation="stop")
sdr_spectrum(operation="stop_websocket")
```

### Scenario: Longwave DX session

```python
# 1. Initialize and tune to BBC Radio 4
sdr_device(operation="initialize")
sdr_device(operation="tune_preset", preset_name="bbc_radio4")

# 2. Get current program
sdr_stations(operation="schedule", station_callsign="BBC LW")

# 3. Capture spectrum
sdr_spectrum(operation="spectrum")

# 4. Scan the full longwave band
sdr_device(operation="scan", start_freq=0.15, end_freq=0.3, step_size=0.01)

# 5. Check other stations on longwave
sdr_stations(operation="by_band", band="LW")
```

### Scenario: Mock mode demonstration

```python
# 1. Enable mock mode
sdr_device(operation="mock_mode", mock_enabled=True)

# 2. Initialize the mock device
sdr_device(operation="initialize")

# 3. Get spectrum (shows synthetic tones)
sdr_spectrum(operation="spectrum")

# 4. Get waterfall
sdr_spectrum(operation="waterfall")

# 5. Start WebSocket and show live streaming
sdr_spectrum(operation="start_websocket")

# 6. Change frequency in mock mode
sdr_device(operation="set_frequency", frequency_mhz=500.0)
sdr_spectrum(operation="spectrum")

# 7. Disable mock mode when done
sdr_device(operation="mock_mode", mock_enabled=False)
```

## Quick reference: all valid operations

```
sdr_device:     list | initialize | status | health | set_frequency | set_gain |
                tune_preset | scan | mock_mode
sdr_spectrum:   spectrum | waterfall | start_websocket | stop_websocket |
                websocket_status | audio_status
sdr_stations:   search | by_band | by_country | schedule | stats
sdr_online:     search | signal_id
sdr_gnuradio:   health | status | start | stop | list_devices
sdr_agentic_assist:  (goal, ctx)
sdr_sampling_hint:   (topic, ctx)
```

### Common error responses

```python
# Unknown operation
{"success": False, "status": "error",
 "message": "Unknown operation: invalid_op",
 "valid_operations": ["list", "initialize", "status", ...]}

# Missing required parameter
{"success": False, "message": "frequency_mhz is required for set_frequency"}

# Frequency out of range
{"success": False, "frequency_mhz": 2000.0,
 "error": "Frequency 2000.0 MHz out of range (24.0-1766.0 MHz)"}

# Invalid gain
{"success": False, "gain": "abc",
 "error": "Invalid gain value: abc",
 "message": "Gain must be 'auto' or a numeric value in dB"}

# Mock mode when hardware needed
{"status": "error", "message": "SDR device not initialized",
 "conversation": {"recovery_suggestions": ["Reinitialize SDR: sdr_initialize()", ...]}}
```

### Advanced: direct CLI invocation

For scripting or troubleshooting, invoke the CLI directly:

```powershell
# List devices
sdr-mcp check

# Start in HTTP mode on custom port
sdr-mcp serve --http --port 10895

# Start with web API on custom port
sdr-mcp serve --http --web-api-port 10896

# Start without web API
sdr-mcp serve --http --no-web-api

# Test with specific parameters
sdr-mcp test --frequency 101.5 --gain 20.0
```
