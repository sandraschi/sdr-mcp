# sdr-mcp — Agent Guide

## Overview
SDR (Software Defined Radio) MCP Server

## Entry Points
- `uv run sdr-mcp` → `sdr_mcp.cli:main`

## Standards
- FastMCP 3.4+ portmanteau tool pattern — tools use `operation` enum param
- Layout: `server.py` (FastMCP instance) → `tools/` (portmanteau + sampling) → `handlers/` (business logic)
- Sampling: `sdr_agentic_assist`, `sdr_sampling_hint` via `ctx.sample` (SEP-1577)
- Probes: `sdr_device(operation='health')` aggregates RTL-SDR + GNU Radio sidecar checks
- Responses: structured dicts with `success`, `message`, domain-specific fields
- Dual transport: stdio (Claude Desktop) + HTTP (`MCP_TRANSPORT=http`)
- See [mcp-central-docs](https://github.com/sandraschi/mcp-central-docs) for fleet-wide coding standards

## Key Files
- `README.md` — full documentation
- `pyproject.toml` — build config and entry points
- `CLAUDE.md` — Claude Code context (if present)

Install docs: follow mcp-central-docs/standards/AGENT_INSTALL_REFERENCE.md
