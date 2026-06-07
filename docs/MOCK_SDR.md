# Mock SDR Mode

Synthetic IQ generation for FFT, waterfall, and WebSocket streaming when no RTL-SDR dongle is connected (or when mock is forced for demos/tests).

---

## Behavior

| Setting | Env `SDR_MCP_MOCK` | When active |
|---------|-------------------|-------------|
| **auto** (default) | unset or `auto` | Mock when `RtlSdr` reports zero devices |
| **enabled** | `enable`, `1`, `true` | Always synthetic IQ |
| **disabled** | `disable`, `0`, `false` | Hardware only — spectrum fails without init |

Auto mode is the default: if your dongle is missing, the dashboard still gets live FFT/waterfall via mock IQ.

---

## MCP tools

### `sdr_device(operation='mock_mode')`

| Param | Values | Effect |
|-------|--------|--------|
| *(omit)* | — | Query current mock setting |
| `mock_enabled=True` | force mock | Synthetic device `MOCK-0001` |
| `mock_enabled=False` | force hardware | Requires RTL-SDR + init |
| `mock_enabled=None` | reset to auto | Re-evaluates hardware presence |

### `sdr_spectrum`

Unchanged operations — they automatically use mock capture when active:

- `operation='spectrum'` — 2048-point FFT + analysis
- `operation='waterfall'` — history (auto-captures one spectrum line if empty under mock)
- `operation='start_websocket'` — live stream; falls back to mock if hardware init fails

Chat / Web API also understands: `mock mode`, `enable mock`, `disable mock`, `simulate`.

---

## Implementation

```
MockIQGenerator (mock_iq.py)
    noise + 4 tones (one drifts ±50 kHz)
         ↓
MockSDRCapture (mock_capture.py)  ← duck-types SDRCapture
         ↓
SDRProcessor.compute_spectrum / waterfall history
         ↓
MCP tools + WebSocket :8765 + web UI
```

No extra PyPI dependencies — pure NumPy.

---

## PyPI landscape (research, June 2026)

Nothing on PyPI is a drop-in **mock RTL-SDR**. Closest packages for **synthetic RF / spectrum**:

| Package | PyPI | Fit for mock IQ |
|---------|------|-----------------|
| **[sdr](https://pypi.org/project/sdr/)** (mhostetter) | Yes | AWGN, IQ imbalance, spectrogram plots — best general DSP sim library |
| **[setigen](https://pypi.org/project/setigen/)** | Yes | Synthetic spectrograms + voltage/IQ via polyphase filterbank — SETI/filterbank oriented, heavy |
| **[soapy_power](https://pypi.org/project/soapy_power/)** | Yes | Real-device FFT sweeps via SoapySDR — not mock |
| **[QSpectrumAnalyzer](https://pypi.org/project/QSpectrumAnalyzer/)** | Yes | GUI spectrum/waterfall — real backends |
| **[gri-sigsim](https://pypi.org/project/gri-sigsim/)** | Yes | RF channel simulation — requires Python 3.14+ |
| **MLAB [pysdr-waterfall](https://github.com/MLAB-project/pysdr)** | GitHub only | Live waterfall from stdin/JACK |
| **[PyWASPGEN](https://github.com/vtnsi/pywaspgen)** | GitHub only | Synthetic wideband captures for sensing algo tests |

**Name trap:** PyPI `pysdr` is an unrelated abandoned framework — not MLAB's waterfall tool.

We chose an in-repo generator to keep the MCP server self-contained and offline-friendly. Optional future: plug in `sdr` library tones for richer modulations.

---

## Testing

```powershell
uv run pytest tests/test_mock.py -q
uv run pytest -q
```

Force mock in dev:

```powershell
$env:SDR_MCP_MOCK = "enable"
uv run sdr-mcp serve --http
```

Then open the web dashboard and start WebSocket from Spectrum page, or invoke:

```json
{"tool": "sdr_spectrum", "params": {"operation": "spectrum"}}
```
