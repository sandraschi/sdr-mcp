param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

& (Join-Path $PSScriptRoot "web_sota\start.ps1") @PSBoundParameters
exit $LASTEXITCODE
