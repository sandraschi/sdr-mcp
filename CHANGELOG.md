# Changelog

All notable changes to this project will be documented in this file.

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
