# SDR MCP Server

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

**Conversational AI control for Software Defined Radio via the Model Context Protocol.**

Control RTL-SDR hardware through natural dialogue — query spectrum, tune frequencies,
browse station databases, and visualize real-time waterfall displays. Works with
Claude Desktop, any MCP client, or the included web dashboard.

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
# Install
pip install sdr-mcp
# Check hardware
sdr-mcp check
# Start server (STDIO mode for Claude Desktop)
sdr-mcp serve
For the web dashboard:
cd web_sota
npm install
npm run dev

## Documentation

| Document | What it covers |
|----------|---------------|
| [INSTALL.md](docs/INSTALL.md) | Full setup, drivers, configuration |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design, data flow, transport |
| [MCP_SERVER.md](docs/MCP_SERVER.md) | All 17 MCP tools with examples |
| [SDR_TECHNOLOGY.md](docs/SDR_TECHNOLOGY.md) | Radio basics for beginners |
| [RTL_SDR_V4.md](docs/RTL_SDR_V4.md) | Recommended hardware specs |

---

## Features

**Hardware Control**
- Auto-detect RTL-SDR devices, initialize and configure
- Set frequency (24 MHz — 1.766 GHz), gain (auto or manual)
- Real-time IQ sample capture and spectrum processing

**Spectrum Analysis**
- 2048-point FFT with Hamming window
- Peak detection and signal strength analysis
- Waterfall history (100 lines) for time-varying signals

**Frequency Database**
- 11 pre-loaded stations across LW/MW/SW/VHF bands
- Program schedules with current-playing info
- Online search via radio-browser.info (25k+ stations)

**WebSocket Streaming**
- Real-time spectrum broadcast to web clients
- Remote frequency/gain control via WebSocket commands
- Canvas-based spectrum and waterfall visualizations

**Web Dashboard**
- Spectrum Analyzer — live FFT plot with frequency/gain controls
- Waterfall Display — color-coded time-frequency visualization
- Station Browser — search, favorites, band filters
- Online DB — query radio-browser.info by name/country/genre
- Signal ID — lookup signal types on SigID Wiki

---

## Hardware

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
| Protocol | FastMCP 3.2, MCP 2.14+ |
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
