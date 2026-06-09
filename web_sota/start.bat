@echo off
TITLE Fleet Launcher - SDR MCP
COLOR 0B
SETLOCAL EnableDelayedExpansion

:: From mcp-central-docs/starts: launch sdr-mcp dashboard (Vite 10890, MCP 10891, Web API 10892)

set "REPO_PATH=D:\Dev\repos\sdr-mcp"
set "START_BAT=%REPO_PATH%\web_sota\start.bat"

if not exist "%START_BAT%" (
    echo [ERROR] SDR MCP start script not found at %START_BAT%
    pause
    exit /b 1
)

cd /d "%REPO_PATH%\web_sota"
call "%START_BAT%" %*
