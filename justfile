set windows-shell := ["powershell.exe", "-NoProfile", "-Command"]
import 'scripts/just/fleet.just'

# --- Dashboard ---

# Open the interactive recipe dashboard in the browser
default:
    @just --list

# --- Setup  Run ---

# Install Python and web dependencies
bootstrap:
    Set-Location '{{justfile_directory()}}'; uv sync; Set-Location '{{justfile_directory()}}\web_sota'; npm install

# Start MCP server (STDIO)
serve:
    Set-Location '{{justfile_directory()}}'
    uv run sdr-mcp serve

# Start MCP server in HTTP mode
serve-http:
    Set-Location '{{justfile_directory()}}'
    uv run sdr-mcp serve --http

# Start backend + web dashboard
dev:
    Set-Location '{{justfile_directory()}}'
    powershell.exe -NoProfile -File .\start.ps1

# Start rtl_tcp on the Windows host (separate terminal)
rtl-tcp:
    powershell.exe -NoProfile -File '{{justfile_directory()}}\scripts\start-rtl-tcp.ps1'

# Build and start GNU Radio demod sidecar
gnuradio-up:
    Set-Location '{{justfile_directory()}}'
    docker compose up -d --build gnuradio-demod

# Stop GNU Radio demod sidecar
gnuradio-down:
    Set-Location '{{justfile_directory()}}'
    docker compose down

# --- Quality ---

# Execute Ruff SOTA v13.1 linting
lint:
    Set-Location '{{justfile_directory()}}'; uv run ruff check .; Set-Location '{{justfile_directory()}}\web_sota'; npx @biomejs/biome ci .

# Execute Ruff SOTA v13.1 fix and formatting
fix:
    Set-Location '{{justfile_directory()}}'; uv run ruff check . --fix --unsafe-fixes; uv run ruff format .; Set-Location '{{justfile_directory()}}\web_sota'; npx @biomejs/biome check --write .

# --- Hardening ---

# Execute Bandit security audit
check-sec:
    Set-Location '{{justfile_directory()}}'
    uv run bandit -r src/

# Execute safety audit of dependencies
audit-deps:
    Set-Location '{{justfile_directory()}}'
    uv run safety check

# --- MCPB ---

# --- Native  Tauri ---

# Build the Tauri NSIS desktop installer (full pipeline: frontend -> Rust -> NSIS)
build-native:
	$env:Path = "$env:USERPROFILE\.cargo\bin;$env:Path"; Set-Location '{{justfile_directory()}}\native'; pwsh -NoProfile -File '{{justfile_directory()}}\native\build.ps1'


# Bootstrap: install dev deps + pre-commit hook
