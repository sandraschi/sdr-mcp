# Installation Guide

## Requirements

- **Python** 3.12+
- **RTL-SDR** dongle (USB) — see [RTL_SDR_V4.md](RTL_SDR_V4.md)
- **uv** (recommended) or pip
- **Node.js** 20+ (for web dashboard)

---

## 1. Install Python Package

### With uv (recommended)

```bash
uv pip install sdr-mcp
```

Or from source:

```bash
git clone https://github.com/your-org/sdr-mcp.git
cd sdr-mcp
uv pip install -e ".[dev]"
```

### With pip

```bash
pip install sdr-mcp
```

---

## 2. Driver Setup (Windows)

RTL-SDR dongles ship with DVB-T drivers. These must be replaced with WinUSB
for SDR software to access the device.

### Zadig Driver Installer

1. Download [Zadig](https://zadig.akeo.ie/)
2. Plug in your RTL-SDR dongle
3. Open Zadig: **Options → List All Devices**
4. Select your device from the dropdown (usually "Bulk-In, Interface (Interface 0)")
5. Select **WinUSB** as the target driver
6. Click **Replace Driver**
7. Verify: `sdr-mcp check` should detect your device

> **Tip:** Keep the original driver handy. You can revert via
> **Device Manager → Right-click device → Properties → Driver → Roll Back Driver**.

---

## 3. Verify Hardware Connection

```bash
sdr-mcp check
```

Expected output:

```
Checking SDR hardware...
RTL-SDR hardware detected!
Found 1 device(s):
  0: Serial 00000001
```

If no device is detected, check:
- USB connection (try different ports)
- Zadig driver installation
- Device not in use by another application (SDR#, HDSDR, etc.)

---

## 4. Start the Server

### STDIO Mode (Claude Desktop)

```bash
sdr-mcp serve
```

Then add to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "sdr-mcp": {
      "command": "sdr-mcp",
      "args": ["serve"]
    }
  }
}
```

### HTTP Mode (Web Dashboard)

```bash
sdr-mcp serve --http --port 10891
```

---

## 5. Start the Web Dashboard

```bash
cd web_sota
npm install
npm run dev
```

Opens at `http://localhost:10890`. The dashboard connects to:
- WebSocket on `ws://localhost:8765` for real-time spectrum data
- MCP HTTP on `http://localhost:10891/mcp` for tool calls

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| `No RTL-SDR devices detected` | Driver not installed | Run Zadig, select WinUSB |
| `USB error: access denied` | Driver conflict | Re-run Zadig, verify driver |
| `ImportError: no module named rtlsdr` | Missing dependency | `pip install pyrtlsdr[lib]` |
| WebSocket won't connect | Server not running | Start `sdr-mcp serve` first |
| Spectrum shows flat line | No antenna connected | Attach appropriate antenna |
