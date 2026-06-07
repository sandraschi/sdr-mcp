# SDR MCP — User Guide

## Quick start

1. Plug in an RTL-SDR dongle (optional — mock works without hardware).
2. For real hardware on Windows: open Zadig, select the **DVB/TV USB** interface, install **WinUSB**.
3. Ask the assistant to list devices: `sdr_device` with `operation='list'`.
4. Initialize and tune: `initialize`, then `set_frequency` or `tune_preset`.

## Common requests

| Goal | Tool call |
|------|-----------|
| See if a dongle is connected | `sdr_device(operation='list')` |
| Tune ORF longwave | `sdr_device(operation='tune_preset', preset_name='orf_longwave')` |
| Set FM frequency | `sdr_device(operation='set_frequency', frequency_mhz=98.5)` |
| Live spectrum | `sdr_spectrum(operation='spectrum')` |
| Waterfall image | `sdr_spectrum(operation='waterfall')` |
| Find local stations | `sdr_stations(operation='search', query='jazz')` |
| Online station lookup | `sdr_online(operation='radio_browser', query='BBC')` |
| FM demod via sidecar | `sdr_gnuradio(operation='demod_fm')` |

## Mock mode

- **Auto** (default): mock when no RTL-SDR is found.
- **Force mock**: `sdr_device(operation='mock_mode', mock_enabled=True)`.
- **Disable mock**: `mock_enabled=False` or set `SDR_MCP_MOCK=disable`.

Mock mode is ideal for demos, CI, and UI development without USB hardware.

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No devices listed | Check USB, WinUSB via Zadig, try another port |
| Permission / access errors | Close other SDR apps (SDR#, GQRX, rtl_tcp) |
| GNU Radio errors | Run `docker compose up -d gnuradio-demod` from repo root |
| Silent audio | Confirm frequency, gain, and demod mode match signal type |

## Presets

Built-in longwave presets include ORF, BBC Radio 4, France Inter, and RTL Luxembourg — use `tune_preset` with the preset name from the server banner.
