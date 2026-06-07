#!/usr/bin/env python3
"""HTTP control plane for GNU Radio demod flowgraphs."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

SUPPORTED_MODES = {"fm", "am", "usb", "lsb"}
SUPPORTED_SOURCES = {"rtl_tcp", "hackrf"}


class DemodManager:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._config: dict[str, Any] = {}

    def status(self) -> dict[str, Any]:
        with self._lock:
            running = self._process is not None and self._process.poll() is None
            return {
                "running": running,
                "pid": self._process.pid if running and self._process else None,
                "config": dict(self._config),
            }

    def list_devices(self) -> dict[str, Any]:
        devices: list[dict[str, Any]] = []
        try:
            result = subprocess.run(
                ["SoapySDRUtil", "--find"],
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
            if result.stdout.strip():
                devices.append({"backend": "soapy", "details": result.stdout.strip()})
        except Exception as exc:
            devices.append({"backend": "soapy", "error": str(exc)})
        return {"devices": devices, "supported_sources": sorted(SUPPORTED_SOURCES)}

    def start(self, payload: dict[str, Any]) -> dict[str, Any]:
        mode = payload.get("mode", "fm")
        source = payload.get("source", "rtl_tcp")
        if mode not in SUPPORTED_MODES:
            raise ValueError(f"Unsupported mode: {mode}")
        if source not in SUPPORTED_SOURCES:
            raise ValueError(f"Unsupported source: {source}")

        frequency_hz = float(payload["frequency_hz"])
        sample_rate = float(payload.get("sample_rate", 2.0e6))
        gain = float(payload.get("gain", 20.0))

        rtl_tcp_host = payload.get("rtl_tcp_host", os.getenv("RTL_TCP_HOST", "host.docker.internal"))
        rtl_tcp_port = int(payload.get("rtl_tcp_port", os.getenv("RTL_TCP_PORT", "1234")))
        source_addr = f"{rtl_tcp_host}:{rtl_tcp_port}"

        with self._lock:
            self.stop_locked()

            cmd = [
                sys.executable,
                "/app/receiver.py",
                "--mode",
                mode,
                "--source",
                source,
                "--freq",
                str(frequency_hz),
                "--sample-rate",
                str(sample_rate),
                "--gain",
                str(gain),
            ]
            if source == "rtl_tcp":
                cmd.extend(["--source-addr", source_addr])

            self._process = subprocess.Popen(cmd)  # noqa: S603
            self._config = {
                "mode": mode,
                "source": source,
                "frequency_hz": frequency_hz,
                "source_addr": source_addr if source == "rtl_tcp" else "hackrf=0",
                "sample_rate": sample_rate,
                "gain": gain,
            }
            return {"started": True, "pid": self._process.pid, "config": dict(self._config)}

    def stop(self) -> dict[str, Any]:
        with self._lock:
            return self.stop_locked()

    def stop_locked(self) -> dict[str, Any]:
        if self._process is None:
            return {"stopped": False, "message": "No demod process running"}

        if self._process.poll() is None:
            self._process.send_signal(signal.SIGTERM)
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait(timeout=2)

        pid = self._process.pid
        self._process = None
        self._config = {}
        return {"stopped": True, "pid": pid}


MANAGER = DemodManager()


class DemodHandler(BaseHTTPRequestHandler):
    def _send_json(self, status: int, payload: dict[str, Any]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
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
        sys.stderr.write(f"{self.address_string()} - {format % args}\n")

    def do_GET(self) -> None:
        if self.path == "/health":
            self._send_json(200, {"status": "ok", "service": "gnuradio-demod"})
            return
        if self.path == "/status":
            self._send_json(200, MANAGER.status())
            return
        if self.path == "/devices":
            self._send_json(200, MANAGER.list_devices())
            return
        self._send_json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if self.path == "/demod/start":
            try:
                payload = self._read_json()
                result = MANAGER.start(payload)
                self._send_json(200, {"status": "started", **result})
            except Exception as exc:
                self._send_json(400, {"status": "error", "message": str(exc)})
            return
        if self.path == "/demod/stop":
            result = MANAGER.stop()
            self._send_json(200, {"status": "stopped", **result})
            return
        self._send_json(404, {"error": "not_found"})


def main() -> None:
    host = os.getenv("DEMOD_HOST", "0.0.0.0")  # noqa: S104
    port = int(os.getenv("DEMOD_PORT", "8000"))
    server = ThreadingHTTPServer((host, port), DemodHandler)
    print(f"GNU Radio demod service listening on {host}:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
