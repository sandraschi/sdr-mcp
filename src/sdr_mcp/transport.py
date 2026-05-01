"""
FastMCP Dual Transport Configuration

Provides unified transport for STDIO, HTTP Streamable, and SSE modes.

Environment Variables:
    MCP_TRANSPORT: Transport mode (stdio, http). Default: stdio
    MCP_HOST: Bind address for HTTP. Default: 127.0.0.1
    MCP_PORT: Port for HTTP. Default: 10891 (fleet)
    MCP_PATH: HTTP endpoint path. Default: /mcp
"""

import argparse
import asyncio
import logging
import os

logger = logging.getLogger(__name__)

TransportType = str  # "stdio" | "http" | "sse"

ENV_TRANSPORT = "MCP_TRANSPORT"
ENV_HOST = "MCP_HOST"
ENV_PORT = "MCP_PORT"
ENV_PATH = "MCP_PATH"


def get_transport_config() -> dict:
    """
    Get transport configuration from environment variables.
    """
    return {
        "transport": os.getenv(ENV_TRANSPORT, "stdio").lower(),
        "host": os.getenv(ENV_HOST, "127.0.0.1"),
        "port": int(os.getenv(ENV_PORT, "10891")),
        "path": os.getenv(ENV_PATH, "/mcp"),
    }


def create_argument_parser(server_name: str) -> argparse.ArgumentParser:
    """
    Create standardized CLI argument parser for MCP servers.
    """
    parser = argparse.ArgumentParser(
        description=f"{server_name} - MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Environment Variables:
  {ENV_TRANSPORT}    Transport mode: stdio, http (default: stdio)
  {ENV_HOST}         Bind address (default: 127.0.0.1)
  {ENV_PORT}         Port number (default: 10891)
  {ENV_PATH}         HTTP endpoint path (default: /mcp)
""",
    )

    transport_group = parser.add_mutually_exclusive_group()
    transport_group.add_argument("--stdio", action="store_true", help="Run in STDIO mode (default)")
    transport_group.add_argument("--http", action="store_true", help="Run in HTTP Streamable mode")
    transport_group.add_argument("--sse", action="store_true", help="Run in SSE mode (deprecated)")

    parser.add_argument("--host", default=None, help="Host to bind to")
    parser.add_argument("--port", type=int, default=None, help="Port to listen on")
    parser.add_argument("--path", default=None, help="HTTP endpoint path")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser


def resolve_transport(args: argparse.Namespace) -> TransportType:
    """Resolve transport type from CLI args with environment fallback."""
    if args.http:
        return "http"
    elif args.sse:
        logger.warning("SSE transport is deprecated. Use --http instead.")
        return "sse"
    elif args.stdio:
        return "stdio"
    else:
        env_transport = os.getenv(ENV_TRANSPORT, "stdio").lower()
        if env_transport not in ("stdio", "http", "sse"):
            logger.warning(f"Invalid {ENV_TRANSPORT}='{env_transport}', defaulting to stdio")
            return "stdio"
        return env_transport


def resolve_config(args: argparse.Namespace) -> dict:
    """Resolve full transport config from CLI args and environment."""
    env_config = get_transport_config()
    return {
        "transport": resolve_transport(args),
        "host": args.host if args.host is not None else env_config["host"],
        "port": args.port if args.port is not None else env_config["port"],
        "path": args.path if args.path is not None else env_config["path"],
    }


def run_server(
    mcp_app,
    args: argparse.Namespace | None = None,
    server_name: str = "mcp-server",
    transport: str | None = None,
    host: str = "127.0.0.1",
    port: int = 10891,
    path: str = "/mcp",
) -> None:
    """
    Unified server runner.

    Args:
        mcp_app: FastMCP application instance.
        args: Parsed CLI arguments (optional, overrides transport/host/port).
        server_name: Server name for logging.
        transport: Explicit transport mode (overrides args/env).
        host: Explicit host (overrides args/env).
        port: Explicit port (overrides args/env).
        path: HTTP endpoint path.
    """
    asyncio.run(run_server_async(mcp_app, args, server_name, transport, host, port, path))


async def run_server_async(
    mcp_app,
    args: argparse.Namespace | None = None,
    server_name: str = "mcp-server",
    transport: str | None = None,
    host: str = "127.0.0.1",
    port: int = 10891,
    path: str = "/mcp",
) -> None:
    """
    Asynchronous unified server runner.

    Priority: explicit params > CLI args > environment > defaults.
    """
    if args is None and transport is None:
        parser = create_argument_parser(server_name)
        args = parser.parse_args()
        config = resolve_config(args)
    elif args is not None:
        config = resolve_config(args)
    else:
        config = {
            "transport": transport or os.getenv(ENV_TRANSPORT, "stdio"),
            "host": host,
            "port": port,
            "path": path,
        }

    t = config["transport"]
    h = config["host"]
    p = config["port"]
    pa = config["path"]

    if args and args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug(f"Debug logging enabled for {server_name}")

    logger.info(f"Starting {server_name}")
    logger.info(f"Transport: {t.upper()}")

    try:
        if t == "stdio":
            logger.info("Running in STDIO mode - Ready for Claude Desktop!")
            await mcp_app.run_stdio_async()

        elif t == "http":
            endpoint = f"http://{h}:{p}{pa}"
            logger.info(f"Running in HTTP Streamable mode: {endpoint}")
            await mcp_app.run_http_async(host=h, port=p, path=pa)

        elif t == "sse":
            logger.warning("SSE mode is deprecated. Migrate to HTTP.")
            logger.info(f"Running in SSE mode: http://{h}:{p}")
            await mcp_app.run_async(transport='sse', host=h, port=p)

    except asyncio.CancelledError:
        logger.info(f"{server_name} task cancelled")
    except Exception as e:
        logger.error(f"{server_name} failed: {e}", exc_info=True)
        raise


__all__ = [
    "TransportType",
    "ENV_TRANSPORT", "ENV_HOST", "ENV_PORT", "ENV_PATH",
    "get_transport_config", "create_argument_parser",
    "resolve_transport", "resolve_config",
    "run_server", "run_server_async",
]
