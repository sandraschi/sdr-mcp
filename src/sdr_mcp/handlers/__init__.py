"""Business-logic handlers for SDR MCP tools."""

from .device import (
    configure_mock_mode,
    get_status,
    initialize,
    list_devices,
    scan_frequencies,
    set_frequency,
    set_gain,
    tune_preset,
)
from .gnuradio_ops import handle_gnuradio_operation
from .online import query_online_database
from .spectrum import get_spectrum, get_waterfall, start_websocket_server, stop_websocket_server
from .stations import (
    get_frequency_database_stats,
    get_program_schedule,
    get_stations_by_band,
    get_stations_by_country,
    search_stations,
)

__all__ = [
    "configure_mock_mode",
    "get_frequency_database_stats",
    "get_program_schedule",
    "get_spectrum",
    "get_stations_by_band",
    "get_stations_by_country",
    "get_status",
    "get_waterfall",
    "handle_gnuradio_operation",
    "initialize",
    "list_devices",
    "query_online_database",
    "scan_frequencies",
    "search_stations",
    "set_frequency",
    "set_gain",
    "start_websocket_server",
    "stop_websocket_server",
    "tune_preset",
]
