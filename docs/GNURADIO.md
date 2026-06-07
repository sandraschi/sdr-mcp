# GNU Radio Sidecar

sdr-mcp uses a **sidecar architecture** on Windows: the RTL-SDR dongle stays on
the host, GNU Radio runs in Docker, and both connect via `rtl_tcp`.

## Architecture

```
RTL-SDR (USB, Windows host)
    ↓ rtl_tcp :1234
GNU Radio container (WSL2/Docker)
    ↓ HTTP :10900
sdr-mcp MCP tools (sdr_gnuradio)
```

Direct USB passthrough into Docker on Windows is unreliable. `rtl_tcp` avoids that.

## Quick Start

```powershell
# 1. Start rtl_tcp on the host (needs RTL-SDR + Zadig drivers)
just rtl-tcp

# 2. Start GNU Radio demod sidecar
just gnuradio-up

# 3. Verify from MCP
sdr_gnuradio(operation="health")
sdr_gnuradio(operation="start", frequency_mhz=101.5)
sdr_gnuradio(operation="status")
sdr_gnuradio(operation="stop")
```

## Audio output

Demodulated audio is no longer discarded.

| Path | Audio to speakers | Audio in browser |
|------|-------------------|------------------|
| **WebSocket** (`sdr_spectrum` → `start_websocket`) | — | FM demod from IQ → Web Audio on Spectrum/Waterfall pages |
| **GNU Radio sidecar** (`sdr_gnuradio` → `start`) | UDP → `sounddevice` on host | Same UDP relay → WebSocket binary stream |

Sidecar env (set in `docker-compose.yml`):

| Variable | Default | Purpose |
|----------|---------|---------|
| `SDR_AUDIO_MODE` | `udp` | `udp`, `portaudio`, or `off` |
| `SDR_AUDIO_HOST` | `host.docker.internal` | UDP target from container |
| `SDR_AUDIO_PORT` | `7355` | PCM port (float32 mono @ 48 kHz) |

**Typical listen flow (dashboard):**

1. `sdr_spectrum(operation='start_websocket')` or Connect on Spectrum page  
2. Tune to an FM station (e.g. **100.0 MHz** in Vienna/ORF area)  
3. Click **Connect** — browser may require one click to unlock audio  

**Sidecar AM/SSB flow:**

1. `just rtl-tcp` + `just gnuradio-up`  
2. `sdr_gnuradio(operation='start', mode='am', frequency_mhz=101.5)`  
3. Audio plays on PC speakers; dashboard gets it if WebSocket is connected  

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `GNURADIO_DEMOD_URL` | `http://127.0.0.1:10900` | Sidecar HTTP API |
| `RTL_TCP_HOST` | `127.0.0.1` | rtl_tcp host (from sdr-mcp's view) |
| `RTL_TCP_PORT` | `1234` | rtl_tcp port |

Inside the container, `RTL_TCP_HOST` defaults to `host.docker.internal`.

## Supported Modes

| Mode | Status | Typical use |
|------|--------|-------------|
| FM (WFM) | Implemented | Broadcast FM 88-108 MHz |
| AM | Implemented | Longwave/mediumwave AM |
| USB | Implemented | Upper sideband HF |
| LSB | Implemented | Lower sideband HF |

## Supported Sources

| Source | Host | Notes |
|--------|------|-------|
| `rtl_tcp` | Windows | Recommended — dongle stays on host |
| `hackrf` | Linux/WSL + USB | Requires `--privileged` + USB passthrough |

HackRF in Docker on Windows does not get USB reliably. Use WSL2 + `usbipd` or run the sidecar on Linux.

## MCP Usage

```python
sdr_gnuradio(operation="start", mode="am", source="rtl_tcp", frequency_mhz=0.198)
sdr_gnuradio(operation="start", mode="fm", source="rtl_tcp", frequency_mhz=101.5)
sdr_gnuradio(operation="start", mode="usb", source="hackrf", frequency_mhz=14.074)
sdr_gnuradio(operation="list_devices")
```

## Files

```
docker/gnuradio/
├── Dockerfile          # Ubuntu 22.04 + gnuradio + gr-osmosdr
├── demod_service.py    # HTTP control plane
└── receiver.py         # FM/AM/USB/LSB flowgraph → UDP audio

docker-compose.yml      # gnuradio-demod service on port 10900
scripts/start-rtl-tcp.ps1
```

## Troubleshooting

1. **Sidecar unreachable** — `docker compose ps`, then `docker compose logs gnuradio-demod`
2. **Demod starts but no data** — confirm rtl_tcp is running and the dongle is not locked by another app
3. **Docker USB issues** — do not put the dongle in the container; use rtl_tcp on the host
