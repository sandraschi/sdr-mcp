# Oscilloscope MCP — Feasibility Notes

Could we build **oscilloscope-mcp** (parallel to sdr-mcp) for USB scopes? **Yes — very plausible**, with the same portmanteau-tool + web-dashboard pattern. Scope choice dominates effort more than MCP plumbing.

---

## USB oscilloscope categories

| Tier | Examples | USB interface | MCP difficulty |
|------|----------|---------------|----------------|
| **Budget “PC scope”** | Hantek 6022BE/BE, Siglent SDS1104X-E (LAN/USB), Owon VDS | USB bulk, often **custom/protocol** or **USBTMC** | Medium — driver layer first |
| **Mid hobby** | Rigol DS1054Z, Siglent SDS series | USBTMC + optional LXI | **Low** — PyVISA/USBTMC well trodden |
| **Premium** | Keysight, R&S, Tektronix | USBTMC, VISA, sometimes IVI | Low API, high license cost |
| **Open hardware** | Red Pitaya, ADALM2000 (M2k) | Ethernet/USB, open stacks | **Lowest** — libiio, Scopy backends |

“Frontend with USB out” usually means either:

1. **USBTMC (IEEE 488.2 over USB)** — Rigol/Siglent class; `:WAV:DATA?` SCPI commands.
2. **Vendor DLL/SDK** — Hantek, some OWON; often Windows-only.
3. **Streaming ADC** — Red Pitaya, ADALM2000; continuous samples like SDR but baseband.

---

## Python / PyPI stack

| Layer | Packages | Role |
|-------|----------|------|
| Transport | [pyusb](https://pypi.org/project/pyusb/), [python-usbtmc](https://pypi.org/project/python-usbtmc/) | Raw USB / USBTMC |
| VISA | [PyVISA](https://pypi.org/project/PyVISA/), [PyVISA-py](https://pypi.org/project/PyVISA-py/) | Unified SCPI for Rigol/Siglent/Tek |
| Open gear | [libiio](https://pypi.org/project/libiio/) (bindings), **pym2k** / libm2k for ADALM2000 | Continuous capture |
| Plot / math | numpy, scipy | FFT, measurements (Pk-Pk, RMS, freq) |
| Mock | Same pattern as **sdr-mcp mock IQ** | Sine/square/chirp + noise for UI without hardware |

There is **no** mature PyPI “mock oscilloscope” package — you'd ship synthetic waveforms in-repo (like we just did for SDR).

---

## Proposed oscilloscope-mcp shape

Mirror sdr-mcp architecture:

```
oscilloscope-mcp/
  server.py              FastMCP registration
  tools/
    scope_device.py      list, connect, channel, timebase, trigger
    scope_capture.py     waveform, fft, measurements, mock_mode
    scope_probe.py       (optional) math channels, cursor readouts
  backends/
    visa_backend.py      Rigol/Siglent SCPI
    libiio_backend.py    ADALM2000 / Red Pitaya
    hantek_backend.py    vendor-specific if needed
    mock_backend.py      synthetic waveforms
  web_sota/              time-domain + FFT + (optional) persistence
  web_api.py             REST bridge for chat UI
```

### Portmanteau tool sketch

**`scope_device`**: `list`, `connect`, `status`, `mock_mode`, `health`  
**`scope_capture`**: `waveform`, `fft`, `measure` (Vpp, Vrms, freq), `start_stream`, `stop_stream`  
**`scope_trigger`**: `set_level`, `set_mode`, `force`, `status`

---

## Mock mode (lessons from sdr-mcp)

Essential for development without bench hardware:

- Sine, square, triangle, noisy ramp
- Trigger-stable repeating buffer
- Multi-channel phase offset
- Env: `SCOPE_MCP_MOCK=auto|enable|disable`

Web dashboard works day one; real backend swapped in per vendor.

---

## Vendor-specific gotchas

1. **Hantek 6022BE** — popular and cheap, but protocol is reverse-engineered (`openhantek`, `libhantek`). Windows-centric; Linux needs kernel driver or libusb work.
2. **Rigol/Siglent USBTMC** — best first real backend; PyVISA examples abound.
3. **ADALM2000** — excellent for MCP demos: 2-channel scope + AWG + logic; libm2k Python bindings.
4. **Bandwidth vs USB** — high sample rates need streaming mode, not single `:WAV:DATA?` polls; WebSocket ring buffer like sdr-mcp.
5. **Safety** — scopes see **direct voltages**; MCP docs should cap allowed ranges and warn about mains/float.

---

## Effort estimate

| Milestone | Scope |
|-----------|--------|
| **M0** | Mock backend + `waveform` + `fft` MCP tools + minimal web plot |
| **M1** | PyVISA backend for one Rigol/Siglent model |
| **M2** | Trigger + measurements + WebSocket stream |
| **M3** | Second backend (libm2k or Hantek) |

M0 is ~1–2 days reusing sdr-mcp patterns. M1 depends on which scope you buy.

---

## Recommendation

If the goal is **broad capability / price range**:

1. **Start mock + web UI** (clone sdr-mcp mock path).
2. **First real device:** pick **USBTMC-native** (Siglent SDS1104X-E or used Rigol DS1054Z) — not the cheapest Hantek unless you're willing to maintain a custom backend.
3. **Best open-platform play:** **ADALM2000** — USB, documented API, scope + generator in one.

oscilloscope-mcp fits the fleet model cleanly: same FastMCP 3.4 portmanteau layout, Web API on `:108xx`, Vite dashboard, `ctx.sample` agentic helpers.

---

## Related repos to study

- [OpenHantek6022](https://github.com/OpenHantek/OpenHantek6022) — Hantek USB protocol
- [pyvisa](https://github.com/pyvisa/pyvisa) — SCPI scopes
- [libm2k](https://github.com/analogdevicesinc/libm2k) — ADALM2000
- [QSpectrumAnalyzer](https://pypi.org/project/QSpectrumAnalyzer/) — GUI pattern for spectrum/waterfall (SDR, but UX reference)
