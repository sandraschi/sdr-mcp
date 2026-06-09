# sdr-mcp — Codebase Assessment
_Generated 2026-06-08 by Claude Sonnet 4.6_

---

## Summary

`sdr-mcp` is a mature, well-structured FastMCP 3.4 server for RTL-SDR hardware. The architecture is sound, the portmanteau pattern is consistently applied, and the dual-transport + web API design is solid. The main blockers are hardware dependency friction, a split Python environment (3.12 in venv vs 3.13 on Goliath), a web frontend that only partially connects to the backend, and several incomplete feature areas documented in the code but not yet wired up. This is a functional v0.4.x server — not a stub — but meaningful gaps exist between what the docs promise and what runs.

---

## What Works Well

**Architecture is correct and idiomatic.** The three-layer split — `server.py` → `tools/` (portmanteau) → `handlers/` (business logic) — follows fleet standards cleanly. Adding a new operation to any tool requires touching exactly one handler file; the portmanteau routing is uniform across all six tools.

**Mock mode is a first-class citizen.** `sdr_device(operation='mock_mode')` and the `should_use_mock()` path in `handlers/state.py` mean the server is usable without USB hardware, which matters for CI and for running from Tokyo via RustDesk.

**Dual transport is done right.** `transport.py` is a reusable, well-commented module with proper priority resolution (explicit → CLI → env → default). Port `10891` is registered in WEBAPP_PORTS. The `asyncio.to_thread` wrapping in `capture.py` means blocking pyrtlsdr calls don't freeze the event loop.

**Agentic tools are real.** `sdr_agentic_assist` and `sdr_sampling_hint` use `ctx.sample` (SEP-1577), include proper recovery_options when sampling is unavailable, and reference concrete tool names rather than vague descriptions. These are copy-paste-quality patterns for the rest of the fleet.

**CI is configured and reasonable.** The GitHub Actions workflow runs on `windows-latest`, uses `uv`, covers both Python linting/tests and the web frontend's Biome lint. The concurrency group cancels stale runs.

**Documentation coverage is above average.** `docs/` has nine separate files covering architecture, hardware variants, mock mode, GNU Radio, and the REST API. `AGENTS.md` is present and accurate. The `assets/prompts/` directory has structured examples — a genuine asset for LLM-driven use.

**Web API is surprisingly complete.** `web_api.py` implements a real threaded HTTP server with CORS, `/api/status`, `/api/health`, `/api/chat` (NLU routing), and `/api/invoke`. The `parse_chat_command` NLU function is a reasonable first pass, though brittle.

---

## Gaps and Problems

### Hard gaps (functionality broken or missing)

**1. numpy upper bound too tight.**
`pyproject.toml` pins `numpy>=1.21.0,<2.0.0`. NumPy 2.x is stable and in wide use; this pin will cause dependency conflicts with any downstream package that has moved on. The `processor.py` FFT code uses no deprecated numpy 1.x APIs — the bound should be `<3.0.0`.

**2. Python version mismatch.**
The `.venv` contains CPython 3.12 pyc files (`__init__.cpython-312.pyc` throughout). Goliath's system Python is 3.13, and `pyproject.toml` specifies `requires-python = ">=3.12"` but the `[tool.mypy]` and `[tool.black]` sections target 3.10. This creates three different version targets in one file. The venv was clearly built with 3.12 but production runs 3.13. Either pin `.python-version` to 3.12 and stick to it, or test on 3.13 and update the caps.

**3. `web_api.py` uses `asyncio.run()` inside a `ThreadingHTTPServer` handler.**
`WebApiHandler.do_GET` and `do_POST` call `asyncio.run(...)` synchronously. This creates a new event loop per HTTP request inside a thread. It works, but it means no shared state with the MCP server's event loop, which breaks anything that relies on in-memory shared state between HTTP and MCP (e.g., a live spectrum buffer). The fix is to hold a reference to the main event loop and use `asyncio.run_coroutine_threadsafe()`, or switch to a proper ASGI server (FastAPI/Starlette) as the fleet standard suggests.

**4. `web_sota` frontend is partially connected.**
The React frontend in `web_sota/src/` has pages for `spectrum.tsx`, `waterfall.tsx`, `stations.tsx`, `chat.tsx`, `tools.tsx`, `apps.tsx`, and `dashboard.tsx`. The common API client in `web_sota/src/common/api-client.ts` calls the web API. But `use-sdr-ws.ts` references a WebSocket endpoint, and `websocket_server.py` exists in `src/sdr_mcp/` but the tool registration for `start_websocket` / `stop_websocket` calls `start_websocket_server()` from handlers — whether that handler is actually implemented or throws NotImplementedError is unverified without reading it. This is a likely stub path.

**5. `audio_stream.py` and `fm_demod.py` have no corresponding tool operations.**
Both files exist in `src/sdr_mcp/` with pyc caches, but neither is exposed via any portmanteau tool. `sdr_gnuradio` handles demodulation via the GNU Radio sidecar; the native Python FM demod in `fm_demod.py` appears to be dead code or an unfinished alternative path.

**6. `online.py` tool — online radio browser dependency.**
`sdr_online` calls the Radio Browser API (`api.radio-browser.info`) for live station lookup. The `.llms-fetch-mcp/` cache directory contains fetched API schemas, suggesting this was built at some point, but there is no fallback when the API is unreachable and no caching layer beyond what was fetched during dev. Offline/airplane use will silently fail.

**7. `scan_frequencies` is likely slow and blocking.**
`sdr_device(operation='scan')` calls `scan_frequencies(start_freq, end_freq, step_size)` in `handlers/device.py`. A scan across even a 10 MHz range at 1 MHz steps requires 10 tune-dwell-read cycles. If this isn't async with proper `asyncio.to_thread` wrapping at each step, it will block the MCP server for the entire scan duration. Need to verify the handler implementation.

### Medium gaps (quality / maintainability)

**8. `start.ps1` is a thin passthrough with no Require-Command bootstrap.**
The root `start.ps1` just delegates to `web_sota/start.ps1`. It does not check for `uv`, `python`, or `npm` presence. Fleet standard requires `Require-Command` / winget bootstrap. The `start.bat` exists but is not a substitute for the PS1 standard.

**9. `pyproject.toml` has three formatters configured.**
`black`, `isort`, and `ruff.format` are all present. Ruff subsumes both black and isort; having all three creates confusion about which tool is canonical. CI runs `ruff check` and `ruff format` only, so black/isort are vestigial. They should be removed from `[project.optional-dependencies]` dev section.

**10. Test coverage is unknown and likely low.**
`tests/` has six test files covering basic, audio, gnuradio, mock, agentic, and web_api paths. But given that the hardware tests necessarily use mocks, the actual coverage of the signal processing pipeline (processor.py, capture.py) is uncertain. No coverage report is generated in CI.

**11. `web_api.py` NLU chat routing is regex-based and fragile.**
`parse_chat_command` handles a limited set of exact-ish phrases. Phrases like "what's on 89.5" or "demodulate FM at 98.1" will fall through to the default `sdr_device list`. This is acceptable for now but will confuse users who try the chat page.

**12. `manifest.json` has `"compatibility": {"platforms": ["win32"]}` but the Python code is platform-agnostic.**
RTL-SDR works on Linux too. The platform restriction exists presumably because `web_sota/start.ps1` is Windows-only. The restriction should be in `README.md` as a practical note, not hardcoded in the manifest, unless there's an actual Windows-only dependency.

**13. `dist/sdr-mcp-v0.4.2.mcpb` is checked into git.**
Build artifacts should be in `.gitignore`, not committed. The `.mcpbignore` file exists, suggesting the build tooling is set up, but the artifact snuck in.

### Minor / cosmetic

- `pyproject.toml` `requires-python = ">=3.12"` but classifiers list 3.10 and 3.11, which can't satisfy the constraint.
- `web_sota/start.ps1` and `web_sota/start.bat` duplicate the root-level start scripts; unclear if both are meant to be entry points.
- `docker/gnuradio/` has a Dockerfile and Python scripts for a GNU Radio container, but there's no `docker-compose.yml` service referencing it (the `docker-compose.yml` at root likely covers a different service — needs verification).
- `.llms-fetch-mcp/` is not in `.gitignore` and is committed to the repo, adding noise.

---

## Priority Action List for Cursor

```
P1 — Fix asyncio.run() in web_api.py request handlers (shared event loop or ASGI)
P1 — Verify websocket_server handler is implemented, not stub
P1 — Verify scan_frequencies is properly async
P2 — Relax numpy bound to <3.0.0
P2 — Pin .python-version to 3.12 or update everything to 3.13 consistently
P2 — Add Require-Command bootstrap to start.ps1
P2 — Remove black/isort from dev deps (ruff covers both)
P2 — Add .mcpb and dist/ to .gitignore; delete committed artifact
P3 — Expose audio_stream / fm_demod via sdr_spectrum tool or remove dead code
P3 — Add offline fallback / cache layer to sdr_online handler
P3 — Add coverage report step to CI
P3 — Remove 3.10/3.11 classifiers from pyproject.toml
P3 — Clarify platform restriction in manifest (win32) vs README note
P3 — Add .llms-fetch-mcp/ to .gitignore
```

---

## Version Gap Check

| Dependency | Pinned | Fleet SOTA | Note |
|---|---|---|---|
| fastmcp | `>=3.4.2,<4` | 3.2+ (fleet uses 3.4.x) | Fine |
| numpy | `<2.0.0` | 2.x stable | Too tight |
| websockets | `>=15.0.1` | Current | Fine |
| prefab-ui | `>=0.14.0` | 0.14.0 | Fine |
| pydantic | `<3.0.0` | 2.x | Fine |
| Python runtime | 3.12 (venv) | 3.13 (Goliath) | Mismatch |

---

_End of assessment._
