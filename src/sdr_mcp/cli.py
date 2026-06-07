"""
CLI interface for SDR MCP Server
"""

import asyncio

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from .server import mcp
from .transport import run_server
from .web_api import get_web_api_config, start_web_api_thread

console = Console()


@click.group()
@click.version_option(version="0.4.0")
def cli():
    """SDR MCP Server - Software Defined Radio tools via Model Context Protocol"""
    pass


@cli.command()
@click.option("--http", "http_mode", is_flag=True, help="Run in HTTP Streamable mode")
@click.option("--port", type=int, default=None, help="Port for HTTP mode (default: 10891)")
@click.option("--host", default=None, help="Host for HTTP mode (default: 127.0.0.1)")
@click.option("--web-api-port", type=int, default=None, help="REST bridge port (default: 10892 or SDR_WEB_API_PORT)")
@click.option("--no-web-api", is_flag=True, help="Disable REST bridge for dashboard (HTTP mode only)")
def serve(http_mode: bool, port: int | None, host: str | None, no_web_api: bool, web_api_port: int | None):
    """Start the SDR MCP server"""
    console.print(Panel.fit(Text("SDR MCP Server Starting", style="bold blue"), title="SDR MCP", border_style="blue"))

    console.print("Portmanteau MCP tools:", style="cyan")
    console.print("  - sdr_device - list, initialize, status, tune, scan")
    console.print("  - sdr_spectrum - spectrum, waterfall, websocket")
    console.print("  - sdr_stations - search, by_band, schedule, stats")
    console.print("  - sdr_online - radio-browser, signal_id")
    console.print("  - sdr_gnuradio - FM/AM/SSB demod sidecar")
    console.print()

    console.print("Longwave presets available:", style="green")
    console.print("  - orf_longwave - ORF Longwave (198 kHz)")
    console.print("  - bbc_radio4 - BBC Radio 4 (198 kHz)")
    console.print("  - france_inter - France Inter (162 kHz)")
    console.print("  - rtl_luxembourg - RTL Luxembourg (234 kHz)")
    console.print()

    import os

    transport_mode = "http" if http_mode else os.getenv("MCP_TRANSPORT", "stdio")
    if transport_mode == "http":
        console.print(
            f"Starting MCP server in HTTP mode on http://{host or '127.0.0.1'}:{port or 10891}/mcp ...", style="yellow"
        )
        if not no_web_api:
            api_host, default_api_port = get_web_api_config()
            api_port = web_api_port or default_api_port
            try:
                start_web_api_thread(host=api_host, port=api_port)
            except OSError as exc:
                console.print(
                    f"\nWeb API could not bind http://{api_host}:{api_port} — {exc}",
                    style="bold red",
                )
                console.print(
                    "Port likely in use. Close other sdr-mcp windows or run start.ps1 "
                    "(it clears ports 10890-10892).",
                    style="yellow",
                )
                console.print(
                    "Override: set SDR_WEB_API_PORT or use --web-api-port.",
                    style="yellow",
                )
                raise click.Abort() from exc
            console.print(f"Web API bridge started on http://{api_host}:{api_port}", style="green")
    else:
        console.print("Starting MCP server in STDIO mode - Ready for Claude Desktop!", style="yellow")

    try:
        run_server(
            mcp,
            server_name="sdr-mcp",
            transport=transport_mode,
            host=host or "127.0.0.1",
            port=port or 10891,
        )
    except KeyboardInterrupt:
        console.print("\nSDR MCP Server stopped", style="red")
    except Exception as e:
        console.print(f"\nError: {e}", style="red")
        raise click.Abort() from e


@cli.command()
def check():
    """Check SDR hardware availability"""
    console.print("Checking SDR hardware...", style="cyan")

    try:
        from .capture import SDRCapture

        available = SDRCapture.is_available()
        devices = SDRCapture.list_devices()

        if available:
            console.print("RTL-SDR hardware detected!", style="green")
            console.print(f"Found {len(devices)} device(s):", style="blue")

            for i, device in enumerate(devices):
                console.print(f"  {i}: Serial {device['serial']}", style="cyan")
        else:
            console.print("No RTL-SDR hardware detected", style="red")
            console.print("\nMake sure:", style="yellow")
            console.print("  1. RTL-SDR dongle is connected")
            console.print("  2. Zadig drivers are installed")
            console.print("  3. Device is not in use by other software")

    except ImportError:
        console.print("pyrtlsdr library not installed", style="red")
        console.print("Run: pip install pyrtlsdr[lib]", style="yellow")

    except Exception as e:
        console.print(f"Error checking hardware: {e}", style="red")


@cli.command()
@click.option("--frequency", "-f", type=float, help="Frequency in MHz")
@click.option("--gain", "-g", default="auto", help="Gain setting (auto or dB)")
def test(frequency: float, gain: str):
    """Quick test of SDR functionality"""
    console.print("Testing SDR functionality...", style="cyan")

    try:
        from .capture import SDRCapture
        from .processor import SDRProcessor

        if not SDRCapture.is_available():
            console.print("No RTL-SDR hardware detected", style="red")
            return

        capture = SDRCapture()
        processor = SDRProcessor()

        console.print("Initializing SDR...", style="yellow")
        success = asyncio.run(capture.initialize())

        if not success:
            console.print("Failed to initialize SDR", style="red")
            return

        console.print("SDR initialized successfully", style="green")

        if frequency:
            console.print(f"Setting frequency to {frequency} MHz...", style="yellow")
            asyncio.run(capture.set_frequency(frequency * 1e6))

        if gain != "auto":
            console.print(f"Setting gain to {gain} dB...", style="yellow")
            asyncio.run(capture.set_gain(gain))

        console.print("Capturing spectrum data...", style="yellow")
        samples = asyncio.run(capture.read_samples(1024 * 1024))

        if samples is not None:
            spectrum_data = processor.process_samples(samples)
            console.print("Spectrum captured successfully!", style="green")
            console.print(f"Data points: {len(spectrum_data.get('spectrum', []))}", style="blue")
            center_freq = capture.center_freq / 1e6
            console.print(f"Center frequency: {center_freq:.1f} MHz", style="blue")
        else:
            console.print("Failed to capture samples", style="red")

        asyncio.run(capture.close())

    except Exception as e:
        console.print(f"Test failed: {e}", style="red")


def main():
    """Main CLI entry point"""
    cli()


if __name__ == "__main__":
    main()
