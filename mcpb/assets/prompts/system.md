# SDR-MCP: Software Defined Radio via Model Context Protocol

## Overview

SDR-MCP turns a $35 RTL-SDR USB dongle into an AI-accessible radio receiver. It provides spectrum analysis (FFT), waterfall displays, FM audio demodulation, station databases (pre-loaded + online), and a GNU Radio demod sidecar (Docker). All hardware operations are wrapped in portmanteau MCP tools with an `operation` enum discriminator.

### What It Does

- **RTL-SDR Control**: Auto-detect, initialize, tune (24 MHz - 1.766 GHz), gain (auto or 0-49.6 dB), IQ sample capture.
- **Spectrum Analysis**: 2048-point FFT with Hamming window, peak detection, signal strength analysis, waterfall history (100 lines).
- **FM Audio**: Native Python FM demod streams over WebSocket; GNU Radio sidecar for FM/AM/SSB with UDP PCM relay to speakers.
- **Station Database**: 11 pre-loaded stations across LW/MW/SW/VHF bands with program schedules; online search via radio-browser.info (25k+ stations).
- **Signal Identification**: Look up modulation types and signal formats via sigidwiki.com.
- **Mock Mode**: Synthetic IQ generation when no dongle is present -- FFT, waterfall, WebSocket all work identically.
- **WebSocket Streaming**: Real-time spectrum broadcast to web clients and dashboards.
- **Agentic Sampling**: Multi-step workflow planning via FastMCP `ctx.sample()`.

### Architecture

The server runs as a FastMCP 3.4+ instance exposing seven portmanteau tools. It supports dual transport: STDIO (Claude Desktop) and HTTP Streamable (web dashboards, Cursor). A REST bridge on port 10892 provides a chat API for the React frontend on port 11118.

```
Claude Desktop / Cursor  <--MCP/STDIO-->  sdr-mcp (FastMCP 3.4)
                                              ├── pyrtlsdr (RTL-SDR hardware)
                                              ├── numpy/scipy (FFT processing)
                                              ├── WebSocket server (port 8765)
                                              ├── GNU Radio sidecar (Docker, port 11223)
                                              ├── rtl_tcp (port 1234)
                                              ├── UDP Audio Relay (port 7355)
                                              └── REST Web API (port 10892)
                                                   └── React dashboard (port 11118)
```

When no RTL-SDR is connected, the server automatically switches to `MockSDRCapture`, which generates synthetic IQ samples with drifting tones. The FFT pipeline, waterfall, and WebSocket streaming all work in this mode with no code changes.

### Quick Start

```python
# List available devices
result = await sdr_device(operation="list")
# {"status": "success", "available": True, "device_count": 1, ...}

# Check health of all subsystems
result = await sdr_device(operation="health")
# {"status": "ok", "rtl_sdr": {"available": True, ...}, "gnuradio_sidecar": {...}}

# Get a live spectrum FFT
result = await sdr_spectrum(operation="spectrum")
# {"status": "success", "spectrum_data": {"frequencies": [...], "spectrum": [...]}, ...}

# Tune to a longwave station
result = await sdr_device(operation="tune_preset", preset_name="bbc_radio4")
# {"status": "tuned", "station": "BBC Radio 4", "frequency_mhz": 0.198, ...}
```

---

## Tool Reference

### sdr_device (Portmanteau -- 9 operations)

Consolidated SDR hardware control: device discovery, initialization, frequency tuning, gain control, scanning, and mock mode.

#### Operations

**list** -- List available RTL-SDR devices.
Returns: device count, serial numbers, mock mode indicator when no hardware present.

**initialize** -- Initialize the SDR device for capture.
Returns: device info (center frequency, sample rate, gain, availability).

**status** -- Current device configuration and mock mode state.
Returns: center frequency, sample rate, gain, mock flag.

**health** -- Aggregated health check across RTL-SDR and GNU Radio sidecar.
Returns: RTL-SDR availability, device count, GNU Radio reachability, service URL.

**set_frequency** -- Tune to a specific frequency.
Parameters: `frequency_mhz` (24.0 - 1766.0).
Returns: success flag, frequency set confirmation.

**set_gain** -- Set gain level.
Parameters: `gain` -- "auto" or numeric dB value (0-49.6).
Returns: success flag, gain applied.

**tune_preset** -- Tune to a named station preset.
Parameters: `preset_name` -- station callsign or name (e.g. "bbc_radio4", "orf_longwave", "france_inter", "rtl_luxembourg").
Returns: station metadata, frequency, band, personality section with signal characteristics.

**scan** -- Sweep a frequency range and detect signals.
Parameters: `start_freq`, `end_freq` (MHz), `step_size` (MHz, default 1.0).
Returns: per-frequency power readings, detected signals (strong/moderate), band analysis context.

**mock_mode** -- Enable, disable, or query mock IQ mode.
Parameters: `mock_enabled` (True=force mock, False=force hardware, None=auto query).
Returns: current mock setting, active state, hardware availability.

#### Parameters

| Parameter | Type | Required | Default | Used By |
|-----------|------|----------|---------|---------|
| operation | str | yes | -- | all |
| device_index | int | no | 0 | initialize |
| frequency_mhz | float | no | -- | set_frequency |
| gain | str | no | "auto" | set_gain |
| preset_name | str | no | "" | tune_preset |
| start_freq | float | no | -- | scan |
| end_freq | float | no | -- | scan |
| step_size | float | no | 1.0 | scan |
| mock_enabled | bool | no | -- | mock_mode |

#### Return Format

```python
# Successful device list (live hardware)
{"status": "success", "available": True, "device_count": 1,
 "devices": [{"index": 0, "serial": "RTL-SDR-Blog-V4-..."}],
 "conversation": {"message": "Found 1 RTL-SDR device(s) ready for operation.", ...}}

# Mock mode active
{"status": "success", "available": True, "mock_mode": True,
 "devices": [{"index": 0, "serial": "MOCK-0001", "mock": True}],
 "conversation": {"message": "Mock SDR active -- synthetic IQ drives FFT and waterfall...", ...}}

# No hardware
{"status": "no_devices", "available": False, "device_count": 0,
 "conversation": {"message": "No RTL-SDR devices detected. Let's get you set up!", ...}}

# Frequency set
{"success": True, "frequency_mhz": 101.5, "frequency_hz": 101500000,
 "message": "Frequency set to 101.5 MHz"}

# Health check
{"success": True, "status": "ok",
 "rtl_sdr": {"available": True, "device_count": 1, "devices": [...]},
 "gnuradio_sidecar": {"reachable": True, "service_url": "http://127.0.0.1:11223"}}

# Scan complete
{"status": "scan_complete",
 "scan_results": [{"frequency_mhz": 88.0, "max_power_db": -32.5, ...}],
 "signal_analysis": {"total_signals_detected": 3, "strong_signals": 1, ...},
 "conversation": {"message": "Active band! Found 1 strong and 2 moderate signals.", ...}}

# Mock mode toggle
{"success": True, "mock_setting": "enabled", "mock_active": True,
 "message": "Mock IQ generator active -- spectrum and waterfall work without RTL-SDR."}

# Error: invalid operation
{"success": False, "status": "error",
 "message": "Unknown operation: invalid_op",
 "valid_operations": ["list", "initialize", "status", "health", "set_frequency",
                      "set_gain", "tune_preset", "scan", "mock_mode"]}
```

#### Examples

```python
# Discover hardware
await sdr_device(operation="list")

# Initialize
await sdr_device(operation="initialize")

# Tune to 101.5 MHz
await sdr_device(operation="set_frequency", frequency_mhz=101.5)

# Set auto gain
await sdr_device(operation="set_gain", gain="auto")

# Tune to a longwave preset
await sdr_device(operation="tune_preset", preset_name="orf_longwave")

# Scan 88-108 MHz (FM band)
await sdr_device(operation="scan", start_freq=88.0, end_freq=108.0, step_size=0.1)

# Enable mock mode
await sdr_device(operation="mock_mode", mock_enabled=True)

# Query mock mode status
await sdr_device(operation="mock_mode")
```

---

### sdr_spectrum (Portmanteau -- 6 operations)

Real-time spectrum analysis, waterfall visualization, and WebSocket streaming.

#### Operations

**spectrum** -- Capture and process an FFT of the current RF environment.
Returns: frequency bins, power spectrum (dB), signal count, peak/average power, dynamic range.

**waterfall** -- Retrieve the waterfall history (100 lines of FFT data).
Returns: list of spectrum lines for time-varying signal visualization.

**start_websocket** -- Start the WebSocket broadcast server.
Parameters: `host` (default "localhost"), `port` (default 8765).
Returns: WebSocket URL, server status.

**stop_websocket** -- Stop the WebSocket broadcast server.
Returns: confirmation message.

**websocket_status** -- Report WebSocket server and FM audio relay status.
Returns: running state, connected clients, audio relay status.

**audio_status** -- Describe native FM demod and sidecar audio paths.
Returns: native demod flag, WebSocket audio state, sidecar UDP relay state.

#### Parameters

| Parameter | Type | Required | Default | Used By |
|-----------|------|----------|---------|---------|
| operation | str | yes | -- | all |
| host | str | no | "localhost" | start_websocket |
| port | int | no | 8765 | start_websocket |

#### Return Format

```python
# Spectrum
{"status": "success", "spectrum_data": {"frequencies": [...], "spectrum": [...]},
 "frequency_mhz": 227.0, "mock_mode": False,
 "analysis": {"signal_count": 3, "peak_power": -22.5, "average_power": -45.2, "dynamic_range": 38.7},
 "conversation": {"message": "Found 3 signal(s) in the 227.0 MHz range.", ...}}

# Waterfall
{"success": True, "waterfall_data": [[...], [...]], "lines_count": 100,
 "message": "Waterfall data with 100 lines retrieved"}

# WebSocket started
{"success": True, "websocket_url": "ws://localhost:8765",
 "message": "WebSocket server started on ws://localhost:8765"}

# WebSocket status
{"success": True, "websocket_running": True,
 "websocket_url": "ws://localhost:8765", "connected_clients": 2,
 "audio_relay_running": True}
```

#### Examples

```python
# Get live FFT
await sdr_spectrum(operation="spectrum")

# Get waterfall
await sdr_spectrum(operation="waterfall")

# Start WebSocket for real-time plotting
await sdr_spectrum(operation="start_websocket")

# Stop WebSocket
await sdr_spectrum(operation="stop_websocket")

# Check streaming status
await sdr_spectrum(operation="websocket_status")

# Check audio demod status
await sdr_spectrum(operation="audio_status")
```

---

### sdr_stations (Portmanteau -- 5 operations)

Pre-loaded frequency database with program schedules.

#### Operations

**search** -- Search stations by name, callsign, or description.
Parameters: `query` (string), `band` (optional: LW/MW/SW/VHF/UHF), `country` (optional).
Returns: matching stations with frequency, band, country, power, language.

**by_band** -- List all stations on a given band.
Parameters: `band` (LW/MW/SW/VHF/UHF).
Returns: stations grouped by country, band characteristics, frequency range.

**by_country** -- List all stations from a country.
Parameters: `country` (string).
Returns: stations grouped by band and type, top stations by power.

**schedule** -- Get program schedule for a station.
Parameters: `station_callsign` (string), `day` (optional day name).
Returns: current program, full schedule grouped by day, station metadata.

**stats** -- Frequency database statistics.
Returns: total stations, countries covered, bands, types, languages.

#### Parameters

| Parameter | Type | Required | Default | Used By |
|-----------|------|----------|---------|---------|
| operation | str | yes | -- | all |
| query | str | no | "" | search |
| band | str | no | -- | search, by_band |
| country | str | no | "" | search, by_country |
| station_callsign | str | no | "" | schedule |
| day | str | no | -- | schedule |

#### Return Format

```python
# Search results
{"status": "found", "total_results": 4, "bands": ["LW", "MW"],
 "stations": [{"name": "BBC Radio 4", "callsign": "BBC LW", "frequency_mhz": 0.198, ...}],
 "conversation": {"message": "Found 4 station(s) matching 'BBC' across 2 band(s): LW, MW", ...}}

# By band
{"status": "success", "band": "LW", "total_stations": 4, "countries": 4,
 "stations": [...],
 "conversation": {"band_characteristics": "Longwave stations provide extremely stable...", ...}}

# Schedule
{"status": "success",
 "station": {"name": "BBC Radio 4", "callsign": "BBC LW", "frequency_mhz": 0.198, ...},
 "current_program": {"name": "The World at One", "description": "Lunchtime news", ...},
 "schedule": {"monday": [...], "tuesday": [...], ...},
 "conversation": {"message": "Program schedule for BBC Radio 4 (BBC LW)", ...}}

# Stats
{"status": "success",
 "database_stats": {"total_stations": 11, "countries_covered": 7, ...},
 "breakdown": {"by_band": {"LW": 4, "MW": 3, "SW": 3, "VHF": 1}, ...}}

# No results
{"status": "no_results",
 "conversation": {"message": "No stations found matching 'xyz'", "suggestions": [...], ...}}
```

#### Examples

```python
# Search for BBC stations
await sdr_stations(operation="search", query="BBC")

# Search with band filter
await sdr_stations(operation="search", query="France", band="LW")

# List longwave stations
await sdr_stations(operation="by_band", band="LW")

# List stations from France
await sdr_stations(operation="by_country", country="France")

# Get BBC Radio 4 schedule
await sdr_stations(operation="schedule", station_callsign="BBC LW")

# Get database stats
await sdr_stations(operation="stats")
```

---

### sdr_online (Portmanteau -- 2 operations)

Online station search via radio-browser.info and signal identification via sigidwiki.com.

#### Operations

**search** -- Search radio-browser.info for internet radio stations.
Parameters: `query`, `country`, `language`, `tag`, `limit` (max 100).
Returns: stations with name, country, language, tags, codec, bitrate, URL.

**signal_id** -- Look up a signal/modulation type on the Signal Identification Wiki.
Parameters: `query` (signal name, e.g. "AM", "FM", "DAB", "ATSC").
Returns: signal title, description, wiki page URL.

#### Parameters

| Parameter | Type | Required | Default | Used By |
|-----------|------|----------|---------|---------|
| operation | str | yes | -- | all |
| query | str | no | "" | search, signal_id |
| country | str | no | "" | search |
| language | str | no | "" | search |
| tag | str | no | "" | search |
| limit | int | no | 25 | search |

#### Return Format

```python
# Online station search
{"status": "success", "total": 15,
 "stations": [{"name": "BBC World Service", "country": "United Kingdom", ...}],
 "conversation": {"message": "Found 15 station(s) from radio-browser.info", ...}}

# Signal identification
{"status": "success",
 "signal": {"title": "FM Broadcast", "description": "Frequency modulation for...", "page_url": "https://..."},
 "conversation": {"message": "Signal 'FM Broadcast' identified", ...}}

# Signal not found
{"status": "not_found",
 "message": "No signal info found for 'unknown_signal'",
 "conversation": {"message": "Could not identify signal 'unknown_signal'", ...}}
```

#### Examples

```python
# Search online stations
await sdr_online(operation="search", query="BBC World Service")

# Search by tag
await sdr_online(operation="search", tag="jazz", limit=10)

# Search by country
await sdr_online(operation="search", country="Germany")

# Identify a signal type
await sdr_online(operation="signal_id", query="DAB+")

# Identify FM broadcast
await sdr_online(operation="signal_id", query="FM Broadcast")
```

---

### sdr_gnuradio (Portmanteau -- 5 operations)

Control the GNU Radio demod sidecar (Docker + rtl_tcp) for advanced demodulation.

#### Operations

**health** -- Check if the GNU Radio sidecar is reachable.
Returns: reachability status, service URL, setup steps if unreachable.

**status** -- Query the active demod flowgraph state.
Returns: running flag, demod config.

**start** -- Start a GNU Radio demod flowgraph.
Parameters: `mode` (fm/am/usb/lsb), `source` (rtl_tcp/hackrf), `frequency_mhz`, `rtl_tcp_host`, `rtl_tcp_port`, `gain`.
Returns: demod status, audio relay port, next steps.

**stop** -- Stop the active demod flowgraph.
Returns: confirmation message.

**list_devices** -- List SDR devices available to the sidecar.
Returns: device list, availability, source type.

#### Parameters

| Parameter | Type | Required | Default | Used By |
|-----------|------|----------|---------|---------|
| operation | str | yes | -- | all |
| mode | str | no | "fm" | start |
| source | str | no | "rtl_tcp" | start |
| frequency_mhz | float | no | -- | start |
| rtl_tcp_host | str | no | -- | start |
| rtl_tcp_port | int | no | -- | start |
| gain | float | no | 20.0 | start |

#### Return Format

```python
# Health
{"status": "success", "service_url": "http://127.0.0.1:11223",
 "conversation": {"message": "GNU Radio sidecar is online.", ...}}

# Start demod
{"status": "success",
 "result": {"running": True, "mode": "fm", "frequency_hz": 101500000},
 "audio": {"udp_port": 7355, "playback": "speakers + browser when WebSocket connected"},
 "conversation": {"message": "Started FM demod at 101.5 MHz via GNU Radio (rtl_tcp).", ...}}

# Stop
{"status": "success", "result": {"running": False},
 "conversation": {"message": "GNU Radio demod stopped."}}

# Unreachable
{"status": "unreachable", "service_url": "http://127.0.0.1:11223",
 "conversation": {"message": "GNU Radio sidecar not reachable. Run: just gnuradio-up",
                  "next_steps": ["Start rtl_tcp: scripts/start-rtl-tcp.ps1", ...]}}
```

#### Examples

```python
# Check sidecar health
await sdr_gnuradio(operation="health")

# Start FM demod at 101.5 MHz
await sdr_gnuradio(operation="start", mode="fm", frequency_mhz=101.5)

# Start AM demod
await sdr_gnuradio(operation="start", mode="am", frequency_mhz=909.0)

# Check active demod
await sdr_gnuradio(operation="status")

# Stop demod
await sdr_gnuradio(operation="stop")

# List sidecar devices
await sdr_gnuradio(operation="list_devices")
```

---

### sdr_agentic_assist (Sampling Tool)

Multi-step SDR workflow plan via FastMCP `ctx.sample()`. Requires a sampling-capable MCP host (Cursor with sampling enabled).

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| goal | str | yes | Natural language radio goal (e.g. "Listen to BBC Radio 4") |
| ctx | Context | yes | FastMCP sampling context |

#### Return Format

```python
# Success
{"success": True, "goal": "Listen to BBC Radio 4",
 "plan": "Tune to BBC Radio 4 at 198 kHz...\n1) sdr_device(operation='list')\n2) sdr_device(operation='tune_preset', preset_name='bbc_radio4')\n3) sdr_spectrum(operation='spectrum')"}

# Sampling unavailable
{"success": False, "error": "Sampling not supported", "goal": "...",
 "recovery_options": ["Use a client that supports MCP sampling.", "Run tools manually: sdr_device(operation='list')..."]}
```

#### Examples

```python
# Plan a research workflow
await sdr_agentic_assist(goal="Scan the FM broadcast band and identify active stations")
```

---

### sdr_sampling_hint (Sampling Tool)

Suggest frequencies, bands, and tool sequences for a radio topic via `ctx.sample()`.

#### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| topic | str | yes | Radio topic (e.g. "shortwave broadcasts from Europe") |
| ctx | Context | yes | FastMCP sampling context |

#### Return Format

```python
# Success
{"success": True, "topic": "shortwave broadcasts from Europe",
 "suggestions": "Try the 31m band (9.4-9.9 MHz)...\nsdr_stations(operation='by_band', band='SW')..."}
```

#### Examples

```python
# Get hints for listening to longwave
await sdr_sampling_hint(topic="longwave radio in Central Europe")
```

---

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| SDR_MCP_MOCK | "auto" | Mock mode: "enable", "disable", "auto" (mock when no dongle) |
| MCP_TRANSPORT | "stdio" | Transport mode: "stdio" or "http" |
| MCP_PORT | 11119 | MCP HTTP port |
| MCP_HOST | "127.0.0.1" | MCP HTTP bind address |
| MCP_PATH | "/mcp" | MCP HTTP endpoint path |
| SDR_WEB_API_PORT | 10892 | REST bridge port for web dashboard |
| SDR_WEB_API_HOST | "127.0.0.1" | REST bridge bind address |
| GNURADIO_DEMOD_URL | "http://127.0.0.1:11223" | GNU Radio sidecar HTTP API |
| RTL_TCP_HOST | "127.0.0.1" | rtl_tcp host for GNU Radio sidecar |
| RTL_TCP_PORT | 1234 | rtl_tcp port for GNU Radio sidecar |

### Ports

| Port | Service |
|------|---------|
| 11118 | React frontend dashboard |
| 11119 | MCP HTTP streamable transport |
| 10892 | REST Web API (chat/status bridge) |
| 8765 | WebSocket spectrum streaming |
| 7355 | UDP audio relay (PCM from GNU Radio) |
| 11223 | GNU Radio sidecar HTTP API |
| 1234 | rtl_tcp (IQ samples for GNU Radio) |

### Mock Mode

`SDR_MCP_MOCK` controls whether the server uses synthetic IQ:

- `auto` (default) -- Mock only when no RTL-SDR hardware is detected.
- `enable` -- Force mock mode. FFT, waterfall, WebSocket all work without hardware.
- `disable` -- Force hardware mode. Requires a functional RTL-SDR dongle.

The server starts up immediately even with no hardware connected. In mock mode, `MockIQGenerator` produces complex IQ samples with four drifting tones at configurable offsets and amplitudes. The tones drift slowly so the waterfall shows movement rather than flat lines.

### Frequency Range

RTL-SDR covers 24 MHz to 1.766 GHz. Longwave presets (162-234 kHz) are valid because the dongle can down-convert using direct sampling mode. The database contains stations across LW (150-300 kHz), MW (530-1700 kHz), SW (3-30 MHz), and VHF (30-300 MHz).

### Hardware Requirements

- RTL2832U-based SDR with R820T2 tuner (RTL-SDR Blog v4 recommended, ~$35).
- Windows: WinUSB driver via Zadig (replaces DVB-T driver).
- GNU Radio sidecar: Docker Desktop, rtl_tcp listening on host.

---

## Station Database

The pre-loaded frequency database contains 11 stations:

**Longwave (LW, 150-300 kHz):**
- BBC Radio 4 (198 kHz, United Kingdom, 500 kW)
- ORF Radio Osterreich 1 (198 kHz, Austria, 100 kW)
- France Inter (162 kHz, France, 2000 kW)
- RTL Radio (234 kHz, Luxembourg, 300 kW)

**Medium Wave (MW, 530-1700 kHz):**
- BBC Radio 5 Live (909 kHz, United Kingdom, 50 kW)
- France Info (837 kHz, France, 100 kW)
- Deutsche Welle (943 kHz, Germany, 150 kW)

**Shortwave (SW, 3-30 MHz):**
- BBC World Service (5.975 MHz, United Kingdom, 250 kW)
- Voice of America (5.955 MHz, United States, 250 kW)
- Radio France Internationale (6.165 MHz, France, 500 kW)

**VHF (30-300 MHz):**
- BFBS Radio 1 (89.0 MHz, United Kingdom, 10 kW)

Each station has program schedules with start/end times, descriptions, languages, and genres. The `schedule` operation returns current program (based on local time) and full weekly schedule.

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Protocol | FastMCP 3.4, MCP 2.14+ |
| Backend | Python 3.12, asyncio |
| Hardware | pyrtlsdr, RtlSdr |
| Signal | numpy, scipy (FFT, Hamming window) |
| Streaming | websockets (RFC 6455) |
| Audio | sounddevice, UDP PCM relay |
| Online DB | httpx (radio-browser.info, sigidwiki.com) |
| Sidecar | Docker, GNU Radio, rtl_tcp |
| Frontend | React 19, TypeScript, Vite |
| UI | Tailwind CSS, Radix UI, Lucide icons |
| CLI | click, rich |
