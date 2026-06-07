Param(
    [int]$Port = 1234,
    [string]$BindAddress = "0.0.0.0",
    [int]$DeviceIndex = 0
)

Write-Host "Starting rtl_tcp on ${BindAddress}:${Port} (device ${DeviceIndex})..." -ForegroundColor Cyan
Write-Host "GNU Radio sidecar should connect via host.docker.internal:${Port}" -ForegroundColor Yellow

$rtlTcp = Get-Command rtl_tcp -ErrorAction SilentlyContinue
if (-not $rtlTcp) {
    Write-Host "rtl_tcp not found in PATH." -ForegroundColor Red
    Write-Host "Install via Zadig + rtl-sdr tools, or: winget install rtl-sdr" -ForegroundColor Yellow
    exit 1
}

& rtl_tcp -a $BindAddress -p $Port -d $DeviceIndex
