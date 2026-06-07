# sdr-mcp fleet zombie kill (START_SCRIPT_STANDARD / FleetStartMode)
# Clears listeners on dashboard ports and stale repo console scripts.
param(
    [int[]]$Ports = @(10890, 10891, 10892)
)

$RepoRoot = Split-Path -Parent $PSScriptRoot
$FleetStartPath = Join-Path $RepoRoot "scripts\FleetStartMode.ps1"
if (-not (Test-Path -LiteralPath $FleetStartPath)) {
    Write-Host "ERROR: Missing vendored launcher helper: $FleetStartPath" -ForegroundColor Red
    exit 1
}
. $FleetStartPath

Stop-FleetPortSquatters -Ports $Ports -Label "sdr-mcp"

$PortHelpers = Join-Path $RepoRoot "scripts\PortHelpers.ps1"
if (Test-Path -LiteralPath $PortHelpers) {
    . $PortHelpers
    Stop-RepoConsoleScriptLock -RepoRoot $RepoRoot -ScriptNames @("sdr-mcp")
}

Stop-FleetPortSquatters -Ports $Ports -Label "sdr-mcp"

if (-not (Assert-FleetPortsAvailable -Ports $Ports -Label "sdr-mcp")) { exit 1 }

Write-Host "Port cleanup complete." -ForegroundColor Green
