"""Bridge sync HTTP handlers to the MCP server's asyncio event loop."""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Coroutine
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

_main_loop: asyncio.AbstractEventLoop | None = None
DEFAULT_TIMEOUT_SEC = 120.0


def set_main_event_loop(loop: asyncio.AbstractEventLoop | None) -> None:
    global _main_loop
    _main_loop = loop


def get_main_event_loop() -> asyncio.AbstractEventLoop | None:
    return _main_loop


def run_async[T](coro: Coroutine[Any, Any, T], timeout: float = DEFAULT_TIMEOUT_SEC) -> T:
    """Run a coroutine on the MCP loop, or fall back to asyncio.run when no loop is registered."""
    loop = _main_loop
    if loop is None or not loop.is_running():
        return asyncio.run(coro)

    future = asyncio.run_coroutine_threadsafe(coro, loop)
    try:
        return future.result(timeout=timeout)
    except TimeoutError as exc:
        future.cancel()
        raise TimeoutError(f"Async operation timed out after {timeout}s") from exc
