# MCP Server Tools

Five portmanteau tools replace the original 17 individual tools. Each uses an `operation` parameter.

---

## `sdr_device`

| Operation | Params | Description |
|-----------|--------|-------------|
| `list` | — | List RTL-SDR devices |
| `initialize` | `device_index` | Open hardware |
| `status` | — | Current config |
| `health` | — | RTL-SDR + GNU Radio sidecar aggregate |
| `set_frequency` | `frequency_mhz` | Tune (24–1766 MHz) |
| `set_gain` | `gain` | Auto or 0–49.6 dB |
| `tune_preset` | `preset_name` | Longwave presets |
| `scan` | `start_freq`, `end_freq`, `step_size` | Frequency scan |
| `mock_mode` | `mock_enabled` (bool, omit=query) | Synthetic IQ when no dongle |

## `sdr_spectrum`

| Operation | Params | Description |
|-----------|--------|-------------|
| `spectrum` | — | FFT power spectrum (uses mock automatically if no RTL-SDR) |
| `waterfall` | — | Waterfall history |
| `start_websocket` | `host`, `port` | Live stream server (falls back to mock) |
| `stop_websocket` | — | Stop stream server |

See [MOCK_SDR.md](MOCK_SDR.md) for mock mode, PyPI research, and env vars (`SDR_MCP_MOCK`).

## `sdr_stations`

| Operation | Params | Description |
|-----------|--------|-------------|
| `search` | `query`, `band`, `country` | Search local DB |
| `by_band` | `band` | LW/MW/SW/VHF/UHF |
| `by_country` | `country` | Filter by country |
| `schedule` | `station_callsign`, `day` | Program schedule |
| `stats` | — | Database statistics |

## `sdr_online`

| Operation | Params | Description |
|-----------|--------|-------------|
| `search` | `query`, `country`, `language`, `tag`, `limit` | radio-browser.info |
| `signal_id` | `query` | SigID Wiki lookup |

## `sdr_gnuradio`

| Operation | Params | Description |
|-----------|--------|-------------|
| `health` | — | Sidecar reachable? |
| `status` | — | Demod process state |
| `start` | `frequency_mhz`, `mode`, `source`, `gain` | Start demod |
| `stop` | — | Stop demod |
| `list_devices` | — | Local RTL-SDR + Soapy scan |

**Modes:** `fm`, `am`, `usb`, `lsb`  
**Sources:** `rtl_tcp` (Windows host), `hackrf` (Linux/USB)

---

## Web API Bridge (port 10892)

For the dashboard and chat UI:

| Endpoint | Method | Body |
|----------|--------|------|
| `/api/health` | GET | — |
| `/api/status` | GET | Live hardware + sidecar snapshot |
| `/api/chat` | POST | `{ "message": "list devices" }` |
| `/api/invoke` | POST | `{ "tool": "sdr_device", "params": { "operation": "list" } }` |

Started automatically with `just dev` or `sdr-mcp serve --http`.

---

## `sdr_agentic_assist` / `sdr_sampling_hint`

SEP-1577 sampling tools — require MCP host with `ctx.sample` support (Cursor, Claude Desktop with sampling enabled).

| Tool | Params | Description |
|------|--------|-------------|
| `sdr_agentic_assist` | `goal` | Multi-step workflow plan naming portmanteau tools |
| `sdr_sampling_hint` | `topic` | Frequency/band/tool suggestions |

Returns `success: false` with `recovery_options` when sampling is unavailable.

---

## FastMCP 3.4 status

| Feature | Integrated? |
|---------|-------------|
| Portmanteau tools | Yes |
| `ctx.sample` (SEP-1577) | Yes — agentic tools |
| `ToolResult(is_error=True)` | Not yet — dict errors for now |
| `@mcp.probe` | **No** — not in FastMCP 3.4.2 API; use `sdr_device(operation='health')` |
| Prefab UI cards | Partial — `prefab-ui` dep present, not wired to list tools |
| CodeMode | No — only 7 tools, not needed |
| `fastmcp-remote` | Documented in fleet docs; use for stdio→HTTP bridge |

---

- `list devices`
- `tune 101.5 mhz`
- `spectrum`
- `tune bbc longwave`
- `gnuradio health`
- `demod 101.5 fm`
