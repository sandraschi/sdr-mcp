"""Simple REST bridge for the web dashboard and chat UI."""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from .capture import SDRCapture
from .gnuradio_client import GnuradioClient, get_gnuradio_config
from .handlers.device import get_status
from .handlers.state import get_mock_mode_label, should_use_mock

logger = logging.getLogger(__name__)

DEFAULT_WEB_API_HOST = "127.0.0.1"
DEFAULT_WEB_API_PORT = 10892
ENV_WEB_API_HOST = "SDR_WEB_API_HOST"
ENV_WEB_API_PORT = "SDR_WEB_API_PORT"


def get_web_api_config() -> tuple[str, int]:
    host = os.getenv(ENV_WEB_API_HOST, DEFAULT_WEB_API_HOST)
    port = int(os.getenv(ENV_WEB_API_PORT, str(DEFAULT_WEB_API_PORT)))
    return host, port


class ReusableThreadingHTTPServer(ThreadingHTTPServer):
    allow_reuse_address = True
    allow_reuse_port = True


def parse_chat_command(message: str) -> tuple[str, dict[str, Any]]:
    """Map natural-ish chat commands to portmanteau tool calls."""
    text = message.strip().lower()
    freq_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:mhz|m)?", text)

    if any(word in text for word in ("list device", "find device", "detect sdr", "check hardware")):
        return "sdr_device", {"operation": "list"}
    if "initialize" in text or "init sdr" in text:
        return "sdr_device", {"operation": "initialize"}
    if "status" in text and "gnuradio" not in text and "sidecar" not in text:
        return "sdr_device", {"operation": "status"}
    if "spectrum" in text or "fft" in text:
        return "sdr_spectrum", {"operation": "spectrum"}
    if "waterfall" in text:
        return "sdr_spectrum", {"operation": "waterfall"}
    if "mock" in text and ("mode" in text or "simulate" in text or "demo" in text):
        if any(word in text for word in ("disable", "off", "hardware", "real")):
            return "sdr_device", {"operation": "mock_mode", "mock_enabled": False}
        if any(word in text for word in ("enable", "on", "simulate", "demo")):
            return "sdr_device", {"operation": "mock_mode", "mock_enabled": True}
        return "sdr_device", {"operation": "mock_mode"}
    if "bbc" in text or "longwave" in text or "preset" in text:
        preset = "bbc_radio4" if "bbc" in text else "orf_longwave"
        return "sdr_device", {"operation": "tune_preset", "preset_name": preset}
    if freq_match and ("tune" in text or "frequency" in text or "mhz" in text):
        return "sdr_device", {"operation": "set_frequency", "frequency_mhz": float(freq_match.group(1))}
    if "gnuradio" in text or "demod" in text:
        if "stop" in text:
            return "sdr_gnuradio", {"operation": "stop"}
        if "health" in text or "sidecar" in text:
            return "sdr_gnuradio", {"operation": "health"}
        if freq_match:
            mode = "am" if " am " in f" {text} " else "fm"
            return "sdr_gnuradio", {
                "operation": "start",
                "frequency_mhz": float(freq_match.group(1)),
                "mode": mode,
            }
        return "sdr_gnuradio", {"operation": "status"}
    if "search" in text and "station" in text:
        query = text.replace("search", "").replace("station", "").replace("stations", "").strip()
        return "sdr_stations", {"operation": "search", "query": query or "BBC"}

    return "sdr_device", {"operation": "list"}


async def invoke_tool(tool: str, params: dict[str, Any]) -> dict[str, Any]:
    if tool == "sdr_device":
        from .server import sdr_device

        return await sdr_device(**params)
    if tool == "sdr_spectrum":
        from .server import sdr_spectrum

        return await sdr_spectrum(**params)
    if tool == "sdr_stations":
        from .server import sdr_stations

        return await sdr_stations(**params)
    if tool == "sdr_online":
        from .server import sdr_online

        return await sdr_online(**params)
    if tool == "sdr_gnuradio":
        from .server import sdr_gnuradio

        return await sdr_gnuradio(**params)
    if tool == "sdr_agentic_assist":
        from .server import sdr_agentic_assist

        return await sdr_agentic_assist(**params)
    if tool == "sdr_sampling_hint":
        from .server import sdr_sampling_hint

        return await sdr_sampling_hint(**params)
    return {"success": False, "message": f"Unknown tool: {tool}"}


async def build_status_snapshot() -> dict[str, Any]:
    devices = SDRCapture.list_devices()
    device_status = await get_status()
    gnuradio = GnuradioClient()
    gnuradio_ok = await gnuradio.is_reachable()
    gnuradio_state = await gnuradio.status() if gnuradio_ok else {"running": False}

    return {
        "success": True,
        "mcp": {"online": True},
        "hardware": {
            "available": SDRCapture.is_available(),
            "device_count": len(devices),
            "devices": devices,
            "initialized": device_status.get("device_info", {}).get("available", False),
            "center_freq_mhz": round(
                (device_status.get("device_info", {}).get("center_freq", 0) or 0) / 1e6,
                3,
            ),
        },
        "mock": {
            "active": should_use_mock(),
            "setting": get_mock_mode_label(),
        },
        "gnuradio": {
            "reachable": gnuradio_ok,
            "service_url": get_gnuradio_config()["service_url"],
            "demod_running": gnuradio_state.get("running", False),
            "config": gnuradio_state.get("config", {}),
        },
    }


class WebApiHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _read_json(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length)
        return json.loads(raw.decode("utf-8"))

    def log_message(self, format: str, *args: Any) -> None:
        logger.debug("%s - %s", self.address_string(), format % args)

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/health":
            self._send_json(200, {"status": "ok", "service": "sdr-mcp-web-api"})
            return
        if parsed.path == "/api/status":
            result = asyncio.run(build_status_snapshot())
            self._send_json(200, result)
            return
        self._send_json(404, {"success": False, "message": "not_found"})

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/chat":
            payload = self._read_json()
            message = str(payload.get("message", "")).strip()
            if not message:
                self._send_json(400, {"success": False, "message": "message is required"})
                return
            tool, params = parse_chat_command(message)
            result = asyncio.run(invoke_tool(tool, params))
            self._send_json(200, {"success": True, "tool": tool, "params": params, "result": result})
            return
        if parsed.path == "/api/invoke":
            payload = self._read_json()
            tool = str(payload.get("tool", ""))
            params = payload.get("params", {})
            if not tool:
                self._send_json(400, {"success": False, "message": "tool is required"})
                return
            result = asyncio.run(invoke_tool(tool, params if isinstance(params, dict) else {}))
            self._send_json(200, {"success": True, "result": result})
            return
        self._send_json(404, {"success": False, "message": "not_found"})


def run_web_api(
    host: str | None = None,
    port: int | None = None,
    *,
    ready: threading.Event | None = None,
    error_box: list[BaseException] | None = None,
) -> None:
    bind_host, bind_port = get_web_api_config()
    if host is not None:
        bind_host = host
    if port is not None:
        bind_port = port

    try:
        server = ReusableThreadingHTTPServer((bind_host, bind_port), WebApiHandler)
        logger.info("Web API listening on http://%s:%s", bind_host, bind_port)
        if ready is not None:
            ready.set()
        server.serve_forever()
    except OSError as exc:
        logger.error("Web API failed to bind http://%s:%s — %s", bind_host, bind_port, exc)
        if error_box is not None:
            error_box.append(exc)
        if ready is not None:
            ready.set()
        raise


def start_web_api_thread(
    host: str | None = None,
    port: int | None = None,
) -> threading.Thread:
    """Start Web API in a daemon thread; raises OSError if the port cannot bind."""
    ready = threading.Event()
    errors: list[BaseException] = []
    bind_host, bind_port = get_web_api_config()
    if host is not None:
        bind_host = host
    if port is not None:
        bind_port = port

    thread = threading.Thread(
        target=run_web_api,
        kwargs={"host": bind_host, "port": bind_port, "ready": ready, "error_box": errors},
        daemon=True,
        name="sdr-web-api",
    )
    thread.start()
    if not ready.wait(timeout=5.0):
        raise TimeoutError(f"Web API thread did not bind on http://{bind_host}:{bind_port} within 5s")
    if errors:
        raise errors[0]
    return thread
