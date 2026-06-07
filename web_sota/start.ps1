param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

$WebPort = 10890
$McpPort = 10891
$WebApiPort = 10892
$ProjectRoot = Split-Path -Parent $PSScriptRoot

$FleetStartPath = Join-Path $ProjectRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath
$FleetStart = Initialize-FleetStartMode @PSBoundParameters
Enter-FleetHeadlessConsole -Headless:$Headless -BackendOnly:$BackendOnly

Stop-FleetPortSquatters -Ports @($WebPort, $McpPort, $WebApiPort) -Label "sdr-mcp"

$PortHelpers = Join-Path $ProjectRoot "scripts\PortHelpers.ps1"
if (Test-Path -LiteralPath $PortHelpers) {
    . $PortHelpers
    Stop-RepoConsoleScriptLock -RepoRoot $ProjectRoot -ScriptNames @("sdr-mcp")
}

Stop-FleetPortSquatters -Ports @($WebPort, $McpPort, $WebApiPort) -Label "sdr-mcp"

if (-not (Assert-FleetPortsAvailable -Ports @($WebPort, $McpPort, $WebApiPort) -Label "sdr-mcp")) { exit 1 }

Start-Sleep -Milliseconds 400

Write-Host "Starting sdr-mcp web dashboard..." -ForegroundColor Cyan

Set-Location $PSScriptRoot
if (-not (Test-Path "node_modules")) {
    Write-Host "Installing frontend dependencies..." -ForegroundColor Yellow
    npm install
}

if ($FleetStart.RunBackend) {
    Write-Host "Starting MCP + Web API (ports $McpPort / $WebApiPort)..." -ForegroundColor Cyan
    $backendCmd = "Set-Location '$ProjectRoot'; `$env:FASTMCP_LOG_LEVEL='WARNING'; uv run sdr-mcp serve --http"
    Start-FleetDetachedShell -Label "sdr-mcp-backend" -Exe "powershell.exe" `
        -Args @("-NoProfile", "-NoExit", "-Command", $backendCmd) `
        -WorkingDirectory $ProjectRoot -WindowStyle $FleetStart.WindowStyle

    $healthUrl = "http://127.0.0.1:$WebApiPort/api/health"
    $attempt = 0
    while ($attempt -lt 45) {
        try {
            $null = Invoke-WebRequest -Uri $healthUrl -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
            Write-Host "Backend ready at $healthUrl" -ForegroundColor Green
            break
        } catch {
            Start-Sleep -Seconds 2
            $attempt++
        }
    }
    if ($attempt -ge 45) {
        Write-Host "Web API did not respond in time. Check the backend window for bind errors." -ForegroundColor Yellow
    }
}

if (-not $FleetStart.RunFrontend) {
    while ($true) { Start-Sleep -Seconds 60 }
}

if (-not $FleetStart.SkipBrowser) {
    $frontendUrl = "http://127.0.0.1:$WebPort/"
    $pollAndOpen = "for (`$i = 0; `$i -lt 60; `$i++) { try { `$null = Invoke-WebRequest -Uri '$frontendUrl' -TimeoutSec 2 -UseBasicParsing -ErrorAction Stop; Start-Process '$frontendUrl'; exit } catch { Start-Sleep -Seconds 1 } }"
    Start-Process powershell -ArgumentList "-NoProfile", "-WindowStyle", "Hidden", "-Command", $pollAndOpen
}

Write-Host "Starting Vite frontend on port $WebPort ..." -ForegroundColor Green
Write-Host "Browser will open automatically when Vite is ready." -ForegroundColor Gray
npm run dev -- --port $WebPort --host 127.0.0.1 --strictPort
