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

console = Console()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """SDR MCP Server - Software Defined Radio tools via Model Context Protocol"""
    pass


@cli.command()
@click.option("--http", "http_mode", is_flag=True, help="Run in HTTP Streamable mode")
@click.option("--port", type=int, default=None, help="Port for HTTP mode (default: 10891)")
@click.option("--host", default=None, help="Host for HTTP mode (default: 127.0.0.1)")
def serve(http_mode: bool, port: int | None, host: str | None):
    """Start the SDR MCP server"""
    console.print(Panel.fit(
        Text("SDR MCP Server Starting", style="bold blue"),
        title="SDR MCP",
        border_style="blue"
    ))

    console.print("Available SDR tools:", style="cyan")
    console.print("  - sdr_list_devices - List connected RTL-SDR devices")
    console.print("  - sdr_initialize - Initialize SDR hardware")
    console.print("  - sdr_set_frequency - Tune to specific frequency")
    console.print("  - sdr_set_gain - Adjust receiver gain")
    console.print("  - sdr_get_spectrum - Get real-time spectrum data")
    console.print("  - sdr_get_waterfall - Get waterfall display data")
    console.print("  - sdr_tune_preset - Tune to longwave presets")
    console.print("  - sdr_get_status - Get current SDR status")
    console.print("  - sdr_start_websocket_server - Start real-time streaming")
    console.print("  - sdr_scan_frequencies - Scan frequency range")
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
        console.print(f"Starting MCP server in HTTP mode on http://{host or '127.0.0.1'}:{port or 10891}/mcp ...", style="yellow")
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
        raise click.Abort()


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
