# Architecture

```
                    +---------------------+
                    |   MCP Client         |
                    | (Claude Desktop /    |
                    |  Web Dashboard /     |
                    |  Any MCP host)       |
                    +----------+----------+
                               |
                    STDIO or HTTP transport
                               |
                    +----------+----------+
                    |   FastMCP 3.2 Core   |
                    |  (sdr_mcp/server.py) |
                    +----------+----------+
                               |
            +------------------+------------------+
            |                  |                  |
    +-------v-------+  +------v-------+  +-------v--------+
    |  SDRCapture   |  | SDRProcessor |  |  WebSocket     |
    |  (capture.py) |  | (processor)  |  |  Server        |
    |  RtlSdr       |  | FFT, window  |  |  (ws server)   |
    |  IQ samples   |  | waterfall    |  |  Live stream   |
    +-------+-------+  +------+-------+  +-------+--------+
            |                  |                  |
            v                  v                  v
     RTL-SDR HW         Spectrum Data         Web clients
     (USB dongle)       (JSON-ready)         (browser JS)
```

## Data Flow

### Spectrum Capture Flow
```
RTL-SDR → IQ samples → FFT (2048 pt) → Power spectrum (dB)
                                      → Waterfall history (100 lines)
                                      → Peak detection → Analysis
```

### Tool Invocation Flow (STDIO)
```
MCP Client → JSON-RPC → stdin/stdout → FastMCP dispatcher → tool fn
                                                                  ↓
Tool fn calls SDRCapture/Processor/DB → returns dict → JSON-RPC response
```

### WebSocket Streaming Flow (Real-time)
```
Browser → ws://localhost:8765 → SDRWebSocketServer
                                      ↓
                           Starts capture loop (100ms intervals)
                                      ↓
                           Reads IQ samples → Process FFT
                                      ↓
                           Broadcasts JSON to all connected clients
```

### Web Dashboard Flow
```
Browser → Vite dev server (10890) → React SPA
                                       ↓
         +----------+----------+----------+----------+
         |          |          |          |          |
    Spectrum   Waterfall   Stations   Online DB   Signal ID
    (WebSocket) (WebSocket) (static)  (CORS API)  (CORS API)
         |          |          |          |          |
         v          v          v          v          v
    ws://8765   ws://8765  MCP tools  radio-    sigidwiki.
                                    browser.info  com
```

## Transport Modes

| Mode | Usage | Port |
|------|-------|------|
| STDIO | Claude Desktop, CLI tools | stdin/stdout |
| HTTP | Web dashboard, REST clients | 10891 |
| WebSocket | Real-time spectrum streaming | 8765 |

The transport module (`transport.py`) supports all three modes. Mode is selected
via CLI flags (`--http`) or the `MCP_TRANSPORT` environment variable.

## Key Design Decisions

1. **Global singletons** for SDRCapture and SDRProcessor — one hardware device,
   one processing pipeline. Avoids conflicts from concurrent tool calls.

2. **Rate limiting** via `asyncio.Semaphore(5)` — prevents hardware overwhelm
   from rapid tool invocations.

3. **Conversational returns** — every tool returns a structured dict with
   `conversation`, `next_steps`, and educational content for AI consumption.

4. **Background tasks** — long-running operations (scan, WebSocket server) use
   `asyncio.create_task()` inside tool handlers to avoid blocking the server.

5. **GNU Radio sidecar** — FM demod runs in a Docker container, connecting to
   rtl_tcp on the Windows host. MCP tool `sdr_gnuradio` controls it via HTTP.
   See [GNURADIO.md](GNURADIO.md).

6. **Browser-side CORS** — radio-browser.info and SigID Wiki are queried
   directly from the browser, no backend proxy needed.
