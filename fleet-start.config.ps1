# Per-repo fleet start config for sdr-mcp
# Edit ports/backend target here - start.ps1 is fleet-standard.
@{
    Name         = 'sdr-mcp'
    BackendPort  = 11119
    FrontendPort = 11118
    HealthPath   = '/api/health'
    WebRoot      = 'web_sota'
    Backend = @{
        Kind          = 'uvicorn-web-app'
        UvicornTarget = 'server:app'
        WorkDir       = 'web_sota\backend'
        SyncExtras    = @('dev')
        SyncOnStart  = $true
        Env           = @{ WEB_PORT = '11119' }
    }
    Frontend = @{
        Kind           = 'vite-npm'
        PackageManager = 'npm'
        PortEnvVar     = 'VITE_PORT'
        ApiTargetEnv   = 'VITE_API_TARGET'
    }
}
