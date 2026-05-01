# MCP Server Tools

All 17 tools exposed by the SDR MCP server. Every tool returns conversational
responses with guidance, next steps, and educational context.

---

## Device Management

### `sdr_list_devices()`
List connected RTL-SDR hardware.
- Returns: device count, serial numbers, conversational guidance
- Demo mode: if no hardware, suggests setup steps

### `sdr_initialize(device_index=0)`
Initialize SDR hardware for capture.
- Configures sample rate (2.048 MHz), center freq (227 MHz), auto gain
- Returns: device info with frequency, sample rate, gain

### `sdr_get_status()`
Current device configuration and health.

### `sdr_check()`
CLI-only — quick hardware detection test.

---

## Frequency Control

### `sdr_set_frequency(frequency_mhz)`
Set center frequency.
- Valid range: 24.0 — 1766.0 MHz (RTL-SDR limits)
- Input validation rejects out-of-range values

### `sdr_set_gain(gain="auto")`
Set receiver gain.
- `"auto"` for automatic gain control
- Numeric values 0 — 49.6 dB for manual

### `sdr_tune_preset(preset_name)`
Tune to known longwave stations.
- Presets: `orf_longwave`, `bbc_radio4`, `france_inter`, `rtl_luxembourg`
- Also accepts DB callsigns: `"BBC LW"`, `"ORF LW"`
- Returns: station personality, signal characteristics, program info

---

## Spectrum Analysis

### `sdr_get_spectrum()`
Real-time FFT spectrum.
- Reads 1M samples, computes 2048-point FFT with Hamming window
- Returns: frequency array, power spectrum (dB), peak/avg power
- Also returns: signal count, dynamic range, conversational analysis

### `sdr_get_waterfall()`
Waterfall history (last 100 FFT lines).
- Returns: list of power spectra for time-varying display

### `sdr_scan_frequencies(start, end, step)`
Automated band scan.
- Background task (`task=True`) — non-blocking
- Detects signals 5-15 dB above noise floor
- Returns: full scan results, band context, signal list

---

## Station Database

### `sdr_search_stations(query, band, country)`
Search local frequency database.
- Searches by name, callsign, description
- Optional band (LW/MW/SW/VHF/UHF) and country filters

### `sdr_get_stations_by_band(band)`
List stations on a frequency band.
- Groups by country, recommends top stations

### `sdr_get_stations_by_country(country)`
List stations from a country.
- Shows band breakdown, station type breakdown

### `sdr_get_program_schedule(callsign, day)`
Program schedule for a station.
- Current playing program, daily/weekly view
- Times in UTC

### `sdr_get_frequency_database_stats()`
Database statistics (11 stations, 6 countries, 4 bands).

---

## Online Databases

### `sdr_query_online_database(query, by, country, language, tag, limit)`
Search radio-browser.info (25k+ stations, open API, no key required).
- Modes: `name`, `country`, `language`, `tag`, `search`, `signal_id`
- Returns: station name, country, language, codec, bitrate, tags, clicks
- `signal_id` mode queries SigID Wiki for signal identification

---

## Streaming

### `sdr_start_websocket_server(host="localhost", port=8765)`
Start real-time spectrum WebSocket server.
- Background task — runs capture loop at 100ms intervals
- Broadcasts FFT data to all connected clients
- Accepts commands: `set_frequency`, `set_gain`, `clear_waterfall`

### `sdr_stop_websocket_server()`
Stop WebSocket streaming and cleanup.
