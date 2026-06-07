# Changelog

All notable changes to this project will be documented in this file.

## [0.4.2] — 2026-06-08

### Added
- **Dashboard hero** — plain-language SDR intro for beginners
- **Help page** — horizontal tabs (hardware, audio, MCP, legal, repo docs)
- **GitHub metadata** — `.github/REPOSITORY.md`, README badges & topics
- **FM audio on WebSocket** — Spectrum/Waterfall pages play demodulated audio (Web Audio API)
- **GNU Radio UDP audio** — sidecar sends PCM to host; `sounddevice` playback + browser relay
- **`fm_demod.py`**, **`audio_stream.py`**, `set_audio` WebSocket command

### Changed
- GNU Radio `receiver.py` uses UDP sink instead of `null_sink` (configurable via `SDR_AUDIO_MODE`)

## [0.4.1] — 2026-06-08

### Added
- **Mock SDR mode** — synthetic IQ for FFT/waterfall/WebSocket without RTL-SDR
- **`sdr_device(operation='mock_mode')`** — enable, disable, or query mock capture
- **`SDR_MCP_MOCK` env** — `auto` (default), `enable`, `disable`
- **Docs:** [MOCK_SDR.md](docs/MOCK_SDR.md) (PyPI landscape), [OSCILLOSCOPE_MCP.md](docs/OSCILLOSCOPE_MCP.md) (scope MCP feasibility)
- **Hardware buying guide** in [HACKRF.md](docs/HACKRF.md) — NESDR SMArt, RTL-SDR Blog v4, HackRF R9/PortaPack tiers

## [0.4.0] — 2026-06-08

### Added
- **`tools/` package** — portmanteau MCP tools separated from `server.py`
- **FastMCP 3.4.2** — dependency bump (`fastmcp>=3.4.2,<4`)
- **`sdr_agentic_assist`** — SEP-1577 sampling workflow planner
- **`sdr_sampling_hint`** — topic → tool/frequency suggestions via `ctx.sample`
- **Startup health** — `sdr_device(operation='health')` ( `@mcp.probe` not in FastMCP 3.4.2 yet)

### Changed
- `server.py` is registration-only; handlers stay in `handlers/`

## [0.3.0] — 2026-06-08

### Added
- **Portmanteau MCP tools** — 5 tools replace 17 individual tools
- **Web API bridge** — REST on :10892 for chat, dashboard, status pages
- **Live dashboard/status** — polls hardware + GNU Radio sidecar state
- **Chat UI** — natural language → MCP tool dispatch
- **AM/USB/LSB demod** in GNU Radio sidecar
- **HackRF source** via gr-osmosdr (Docker + USB) — see [HACKRF.md](docs/HACKRF.md) buying guide
- Unified `docker/gnuradio/receiver.py`

### Changed
- Handlers extracted to `src/sdr_mcp/handlers/`
- `just dev` starts HTTP MCP + Web API + Vite
- Vite proxies `/api` → :10892

## [0.2.2] — 2026-06-08

### Added
- **GNU Radio sidecar** — Dockerized FM demod service (`docker/gnuradio/`)
- **`sdr_gnuradio` MCP tool** — health, status, start, stop via HTTP
- **`just` recipes** — bootstrap, serve, serve-http, dev, rtl-tcp, gnuradio-up/down
- **`scripts/start-rtl-tcp.ps1`** — host-side rtl_tcp launcher
- **Docs** — `GNURADIO.md`, `HACKRF.md` (TX licensing explained)

### Changed
- Version aligned to 0.2.2 across pyproject, CLI, and `__init__.py`
- Removed stale `.bak` files from `src/sdr_mcp/`
- Ruff auto-fix applied (imports, formatting)

## [0.2.1] — 2026-05-01

### Fixed
- **Blocking event loop in `read_samples()`**: `SDRCapture.read_samples()` was
  calling `RtlSdr.read_samples()` directly from an `async` method, blocking the
  event loop for ~0.5s per call. Wrapped with `asyncio.to_thread()`.
- **Invalid `task=True` decorator param**: `@mcp.tool(task=True)` on
  `sdr_start_websocket_server` and `sdr_scan_frequencies` is not a valid FastMCP
  3.2 parameter and caused startup errors. Removed from both; `create_task()`
  inside the tool body handles async dispatch correctly.
- **Deprecated `asyncio.get_event_loop().time()`**: Replaced all three
  occurrences in `sdr_scan_frequencies` with `asyncio.get_running_loop().time()`
  (required in Python 3.12+).
- **Legacy typing imports in `capture.py`**: Removed `from typing import
  Optional, List`; replaced with `np.ndarray | None` and `list[dict]` (PEP 585,
  Python 3.10+).

## [0.2.0] — 2026-05-01

### Fixed
- **Crash on startup**: `if __name__` block in server.py passed `asyncio` module
  instead of `mcp` instance to `run_server_async()`
- **NameError in `sdr_tune_preset`**: referenced undefined `preset` variable
  when station was found via database lookup. Replaced with `station` properties
- **Indentation error** in `capture.py` (mixed tabs/spaces)
- **Looping on serve**: CLI's Click args conflicted with argparse re-parsing
  of `sys.argv`. Restructured `transport.py` to accept explicit params
- **Missing `Band` import** in test file
- **Port conflict**: vite.config.ts hardcoded port 10706 (claimed by robotics-mcp)
- **Missing `app` attribute** in web_sota/start.ps1 (used uvicorn on non-existent
  FastAPI app)

### Added
- **FastMCP 3.2 compliance**: updated dependency, simplified constructor,
  added `task=True` to long-running tools, input validation, rate limiting
- **Startup probe**: `@mcp.probe()` health check
- **Input validation**: frequency range (24-1766 MHz), gain format/range,
  band enum validation
- **Rate limiting**: `asyncio.Semaphore(5)` for SDR hardware operations
- **Error logging**: `exc_info=True` on all `logger.error()` calls across
  all Python files
- **Online database integration**: `online_db.py` with radio-browser.info
  and SigID Wiki API queries
- **`sdr_query_online_database`** MCP tool — search by name/country/language/tag,
  plus signal identification lookup
- **WebSocket hook** (`use-sdr-ws.ts`) — reusable React hook for real-time
  SDR data streaming
- **Spectrum Analyzer page** (`/spectrum`) — Canvas FFT plot with frequency/gain
  controls, WebSocket connection
- **Waterfall page** (`/waterfall`) — color-coded time-frequency display
- **Station Browser page** (`/stations`) — search, LW/MW/SW/VHF band tabs,
  favorites (localStorage), online DB tab, Signal ID tab
- **Self-reference in app catalog**: SDR MCP entry in APPS_CATALOG

### Changed
- **Ports**: frontend 10890, backend 10891 (from 10706/10916). Updated
  `vite.config.ts`, `transport.py`, `start.ps1`, `apps.tsx`
- **Python deps**: `fastmcp>=3.2.0`, added `httpx>=0.27.0`
- **CLI transport**: `sdr-mcp serve` now accepts `--http`, `--port`, `--host`
  options instead of relying on argparse re-parse
- **Removed `server.bak`** — stale duplicate
- **Removed emoji from tool returns** for compatibility

### Infrastructure
- Added docs/ directory with INSTALL, ARCHITECTURE, MCP_SERVER, SDR_TECHNOLOGY,
  RTL_SDR_V4 documentation
- Updated sidebar with Spectrum, Waterfall, Stations navigation
- Fixed app port listings in apps.tsx
- All tool output now uses standard dict types (PEP 585)

## [0.1.0] — Initial Release

- Basic RTL-SDR control (list, initialize, set frequency/gain)
- FFT spectrum processing with waterfall history
- Frequency database with 11 stations, program schedules
- WebSocket streaming server
- React web dashboard with 7 placeholder pages
- CLI with serve/check/test commands
