# SDR MCP Server

<p align="center">
  <a href="https://github.com/sandraschi/sdr-mcp"><img src="https://img.shields.io/github/stars/sandraschi/sdr-mcp?style=flat-square&logo=github&color=7c5cfc" alt="GitHub stars"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22c55e?style=flat-square" alt="MIT License"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.4-7c5cfc?style=flat-square" alt="FastMCP"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-server-0891b2?style=flat-square" alt="MCP"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.12+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://react.dev"><img src="https://img.shields.io/badge/React-19-61DAFB?style=flat-square&logo=react&logoColor=white" alt="React"></a>
  <a href="docker-compose.yml"><img src="https://img.shields.io/badge/GNU_Radio-sidecar-2496ED?style=flat-square&logo=docker&logoColor=white" alt="Docker"></a>
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
</p>

**Listen to radio waves with a USB stick — controlled by AI or a web dashboard.**

[Software Defined Radio](docs/SDR_TECHNOLOGY.md) (SDR) turns RF into data your PC can plot and play.
This repo is a [Model Context Protocol](https://modelcontextprotocol.io) server for RTL-SDR: live **spectrum**,
**waterfall**, **FM audio**, station databases, and a **GNU Radio** demod sidecar. Works with Cursor,
Claude Desktop, or the built-in React dashboard at http://127.0.0.1:10890/.

---

## Quick Start

```powershell
git clone https://github.com/sandraschi/sdr-mcp
cd sdr-mcp
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:

```powershell
pip install sdr-mcp
sdr-mcp check          # needs RTL-SDR + WinUSB on Windows, or use mock mode
sdr-mcp serve          # STDIO for Claude Desktop
```

**Windows + real dongle:** replace the stick's DVB/TV USB driver with **WinUSB** via
[Zadig](https://zadig.akeo.ie/) — see [INSTALL.md](docs/INSTALL.md). You are not replacing
the hardware; only the driver Windows uses to talk to USB.

**No dongle:** mock mode activates automatically (`SDR_MCP_MOCK=auto`). FFT/waterfall still work.
See [MOCK_SDR.md](docs/MOCK_SDR.md).

For the web dashboard:

```powershell
cd web_sota
npm install
npm run dev
```

Or double-click `web_sota\start.bat`.

## Documentation

| Document | What it covers |
|----------|---------------|
| [INSTALL.md](docs/INSTALL.md) | Full setup, drivers, configuration |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, transport |
| [MCP_SERVER.md](docs/MCP_SERVER.md) | Portmanteau MCP tools with examples |
| [SDR_TECHNOLOGY.md](docs/SDR_TECHNOLOGY.md) | Radio basics for beginners |
| [RTL_SDR_V4.md](docs/RTL_SDR_V4.md) | Recommended hardware specs |
| [GNURADIO.md](docs/GNURADIO.md) | GNU Radio sidecar (Docker + rtl_tcp) |
| [HACKRF.md](docs/HACKRF.md) | HackRF TX licensing + **hardware buying guide** |
| [MOCK_SDR.md](docs/MOCK_SDR.md) | Synthetic IQ demo mode (no dongle) |
| [OSCILLOSCOPE_MCP.md](docs/OSCILLOSCOPE_MCP.md) | USB oscilloscope MCP feasibility |

**New to SDR?** Open the dashboard → **Help** (horizontal tabs) or read [SDR_TECHNOLOGY.md](docs/SDR_TECHNOLOGY.md).

### GitHub topics

`sdr` · `software-defined-radio` · `rtl-sdr` · `mcp` · `mcp-server` · `fastmcp` · `gnuradio` · `spectrum-analyzer` · `waterfall` · `websocket` · `python` · `react` · `docker`

See [.github/REPOSITORY.md](.github/REPOSITORY.md) for `gh repo edit` commands.

---

## Features

**Hardware Control**
- Auto-detect RTL-SDR devices, initialize and configure
- **Mock IQ mode** when no dongle — FFT/waterfall/WebSocket still work ([MOCK_SDR.md](docs/MOCK_SDR.md))
- Set frequency (24 MHz — 1.766 GHz), gain (auto or manual)
- Real-time IQ sample capture and spectrum processing

**Spectrum Analysis**
- 2048-point FFT with Hamming window
- Peak detection and signal strength analysis
- Waterfall history (100 lines) for time-varying signals

**GNU Radio Demod (sidecar)**
- FM demod via Dockerized GNU Radio + rtl_tcp
- MCP tool `sdr_gnuradio` for start/stop/status
- HackRF path documented for future SoapySDR integration

**Frequency Database**
- 11 pre-loaded stations across LW/MW/SW/VHF bands
- Program schedules with current-playing info
- Online search via radio-browser.info (25k+ stations)

**WebSocket Streaming**
- Real-time spectrum broadcast to web clients
- Remote frequency/gain control via WebSocket commands
- Canvas-based spectrum and waterfall visualizations

- **Web Dashboard** — noob-friendly hero, tabbed Help, spectrum + waterfall + FM audio
---

## Hardware

**Platform:** Developed and tested on **Windows** (WinUSB via Zadig, fleet launchers, MCPB bundle). Core Python code may run on Linux with librtlsdr, but the dashboard launch scripts and MCPB manifest target Windows only.

**Recommended:** [RTL-SDR Blog v4](docs/RTL_SDR_V4.md) (~$35)
- 24 MHz — 1.766 GHz continuous coverage
- 0.5 ppm TCXO for frequency stability
- SMA connector, aluminum enclosure, bias tee

Any RTL2832U-based SDR with R820T2 tuner works. See [RTL_SDR_V4.md](docs/RTL_SDR_V4.md) for full specs.

---

## Project Structure

```
sdr-mcp/
├── README.md              # This file
├── docs/                  # Documentation
│   ├── INSTALL.md         # Setup guide
│   ├── ARCHITECTURE.md    # System design
│   ├── MCP_SERVER.md      # Tool reference
│   ├── SDR_TECHNOLOGY.md  # Radio primer
│   └── RTL_SDR_V4.md      # Hardware specs
├── pyproject.toml         # Python package config
├── justfile               # Lint, fix, security recipes
├── start.ps1              # Launch backend + webapp
├── src/sdr_mcp/           # Python backend
│   ├── server.py          # FastMCP server, 17 tools
│   ├── capture.py         # RTL-SDR hardware interface
│   ├── processor.py       # FFT / spectrum processing
│   ├── frequency_db.py    # Station database
│   ├── online_db.py       # radio-browser.info API
│   ├── websocket_server.py # Real-time WebSocket stream
│   ├── transport.py       # STDIO / HTTP transport
│   └── cli.py             # Command-line interface
├── web_sota/              # React/TypeScript webapp
│   └── src/
│       ├── pages/         # Spectrum, Waterfall, Stations, etc.
│       └── components/    # Layout, UI components
└── tests/                 # Pytest test suite
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Protocol | FastMCP 3.4, MCP 2.14+ |
| Backend | Python 3.12, asyncio |
| Hardware | pyrtlsdr, RtlSdr |
| Signal | numpy, scipy (FFT) |
| Streaming | websockets (RFC 6455) |
| Frontend | React 19, TypeScript, Vite |
| UI | Tailwind CSS, Radix UI, Lucide icons |
| Standards | Fleet SOTA, ruff, Biome, just |

---

## License

MIT
