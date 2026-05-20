<#
.SYNOPSIS
    Docker daemon health-polling & auto-recovery script.
.DESCRIPTION
    Monitors Docker daemon availability and container health. Attempts recovery
    if the daemon is unreachable. Designed for Task Scheduler or ad-hoc use.
.PARAMETER Watch
    Run continuously, polling every N seconds (default 30).
.PARAMETER Interval
    Poll interval in seconds when in watch mode (default 30).
.PARAMETER MaxRetries
    Recovery attempts before giving up (default 3).
.PARAMETER Notify
    Show Windows toast notification on state changes.
.PARAMETER CriticalContainers
    Comma-separated list of container names that must stay healthy.
.PARAMETER LogPath
    Path to log file (default: $env:TEMP\docker-daemon-poll.log).
.EXAMPLE
    .\docker-daemon-poll.ps1
    # Single health check

    .\docker-daemon-poll.ps1 -Watch -Notify
    # Continuous monitoring with toast notifications

    .\docker-daemon-poll.ps1 -CriticalContainers "weaviate,myconf-redis-1,immich_server"
    # Check specific containers are healthy

.NOTES
    Requires: Docker CLI in PATH, Administrator privileges for restart operations.
#>

[CmdletBinding()]
param(
    [switch]$Watch,
    [int]$Interval = 30,
    [int]$MaxRetries = 3,
    [switch]$Notify,
    [string]$CriticalContainers = "",
    [string]$LogPath = "$env:TEMP\docker-daemon-poll.log"
)

$ErrorActionPreference = "Continue"
$script:StartTime = Get-Date
$script:ConsecutiveFails = 0
$script:LastState = $null

function Write-Log {
    param([string]$Level, [string]$Message)
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $entry = "[$ts] [$Level] $Message"
    Add-Content -Path $LogPath -Value $entry -ErrorAction SilentlyContinue
    $color = @{ INFO = "Gray"; WARN = "Yellow"; ERROR = "Red"; OK = "Green"; RECOVER = "Cyan" }[$Level]
    Write-Host $entry -ForegroundColor $color
}

function Show-Notification {
    param([string]$Title, [string]$Message, [string]$Urgency = "Normal")
    if (-not $Notify) { return }
    try {
        [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] > $null
        $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent(
            [Windows.UI.Notifications.ToastTemplateType]::ToastText02)
        $template.GetElementsByTagName("text")[0].AppendChild(
            $template.CreateTextNode($Title)) > $null
        $template.GetElementsByTagName("text")[1].AppendChild(
            $template.CreateTextNode($Message)) > $null
        $notifier = [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("Docker Monitor")
        $notification = New-Object Windows.UI.Notifications.ToastNotification($template)
        $notifier.Show($notification)
    } catch {
        Write-Log "WARN" "Toast notification failed: $_"
    }
}

function Test-DockerDaemon {
    $sw = [System.Diagnostics.Stopwatch]::StartNew()
    $result = docker info 2>$null
    $sw.Stop()
    if ($LASTEXITCODE -eq 0) {
        $versionLine = ($result | Select-String "Server Version").ToString().Trim()
        $containersLine = ($result | Select-String "Running:").ToString().Trim()
        $memLine = ($result | Select-String "Total Memory").ToString().Trim()
        Write-Log "OK" "Daemon reachable in ${($sw.ElapsedMilliseconds)}ms | $versionLine | $containersLine | $memLine"
        return $true
    }
    Write-Log "ERROR" "Daemon unreachable after ${($sw.ElapsedMilliseconds)}ms (exit=$LASTEXITCODE)"
    return $false
}

function Test-ContainerHealth {
    param([string[]]$Names)
    if (-not $Names) { return @{} }
    $health = @{}
    $containers = docker ps -a --format "{{.Names}}\t{{.Status}}" 2>$null
    foreach ($name in $Names) {
        $line = $containers | Select-String "^$name\b"
        if ($line) {
            $status = $line.ToString().Split("`t")[1]
            if ($status -match "\(healthy\)") {
                $health[$name] = "healthy"
            } elseif ($status -match "\(unhealthy\)") {
                $health[$name] = "unhealthy"
                Write-Log "WARN" "Container $name is UNHEALTHY: $status"
            } elseif ($status -match "\(health:") {
                $health[$name] = "starting"
            } elseif ($status -match "^Up ") {
                $health[$name] = "running"
            } elseif ($status -match "Restarting") {
                $health[$name] = "restarting"
                Write-Log "WARN" "Container $name is restarting: $status"
            } elseif ($status -match "^Exited") {
                $health[$name] = "exited"
                Write-Log "ERROR" "Container $name has EXITED: $status"
            } else {
                $health[$name] = "unknown"
            }
        } else {
            $health[$name] = "missing"
            Write-Log "WARN" "Critical container $name NOT FOUND"
        }
    }
    return $health
}

function Get-DockerDesktopProcess {
    Get-Process "Docker Desktop" -ErrorAction SilentlyContinue
}

function Get-WslState {
    param([string]$Distro = "docker-desktop")
    $output = wsl --list --verbose 2>$null
    if ($output) {
        $line = $output | Select-String $Distro
        if ($line -match "\b(Stopped|Running|Installing|Uninstalling|Converting)\b") {
            return $matches[1]
        }
    }
    return "Unknown"
}

function Start-DockerDesktop {
    $ddPath = "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"
    if (Test-Path $ddPath) {
        Write-Log "RECOVER" "Starting Docker Desktop..."
        Start-Process $ddPath
        return $true
    }
    Write-Log "ERROR" "Docker Desktop.exe not found at $ddPath"
    return $false
}

function Invoke-DaemonRecovery {
    param([int]$Attempt)
    Write-Log "RECOVER" "Recovery attempt $Attempt of $MaxRetries"

    $ddProcess = Get-DockerDesktopProcess
    $wslState = Get-WslState

    Write-Log "INFO" "Docker Desktop process: $(if($ddProcess){'Running PID='+$ddProcess.Id}else{'Not running'})"
    Write-Log "INFO" "WSL docker-desktop state: $wslState"

    if (-not $ddProcess) {
        Write-Log "RECOVER" "Docker Desktop not running — attempting to start..."
        if (Start-DockerDesktop) {
            Write-Log "INFO" "Waiting 60s for Docker Desktop initialization..."
            Start-Sleep -Seconds 60
            if (Test-DockerDaemon) {
                Show-Notification "Docker Recovered" "Docker Desktop started successfully (attempt $Attempt)."
                return $true
            }
        }
    }

    if ($wslState -eq "Running" -and $ddProcess) {
        Write-Log "RECOVER" "Restarting WSL docker-desktop distro..."
        wsl --terminate docker-desktop 2>$null
        wsl --terminate docker-desktop-data 2>$null
        Start-Sleep -Seconds 5
        Write-Log "INFO" "Waiting 30s for WSL restart..."
        Start-Sleep -Seconds 30
        if (Test-DockerDaemon) {
            Show-Notification "Docker Recovered" "WSL restart resolved daemon (attempt $Attempt)."
            return $true
        }
    }

    Write-Log "RECOVER" "Hard restart: killing Docker Desktop and relaunching..."
    Get-Process "Docker Desktop", "com.docker.backend", "com.docker.build" -ErrorAction SilentlyContinue |
        Stop-Process -Force
    Start-Sleep -Seconds 10
    if (Start-DockerDesktop) {
        Write-Log "INFO" "Waiting 90s for full Docker Desktop initialization..."
        Start-Sleep -Seconds 90
        if (Test-DockerDaemon) {
            Show-Notification "Docker Recovered" "Hard restart recovered daemon (attempt $Attempt)."
            return $true
        }
    }

    Write-Log "ERROR" "Recovery attempt $Attempt FAILED"
    return $false
}

# ── Main ────────────────────────────────────────────────────────────────

$criticalList = if ($CriticalContainers) {
    $CriticalContainers -split ',' | ForEach-Object { $_.Trim() } | Where-Object { $_ }
} else { @() }

function Invoke-HealthCheck {
    $healthy = $true

    if (-not (Test-DockerDaemon)) {
        $script:ConsecutiveFails++
        $healthy = $false
        Write-Log "WARN" "Consecutive failures: $script:ConsecutiveFails"

        if ($script:ConsecutiveFails -ge 2) {
            Show-Notification "Docker Daemon Down" "Consecutive failures: $script:ConsecutiveFails. Attempting recovery..."
            for ($i = 1; $i -le $MaxRetries; $i++) {
                if (Invoke-DaemonRecovery -Attempt $i) {
                    $script:ConsecutiveFails = 0
                    $healthy = $true
                    break
                }
                Start-Sleep -Seconds 15
            }
            if (-not $healthy) {
                Show-Notification "Docker Recovery Failed" "Daemon still unreachable after $MaxRetries attempts."
            }
        }
    } else {
        $script:ConsecutiveFails = 0
    }

    if ($healthy -and $criticalList.Count -gt 0) {
        $healthMap = Test-ContainerHealth -Names $criticalList
        $unhealthy = $healthMap.GetEnumerator() | Where-Object { $_.Value -in @("unhealthy", "restarting", "exited", "missing") }
        if ($unhealthy) {
            $names = ($unhealthy | ForEach-Object { "$($_.Key)=$($_.Value)" }) -join ', '
            Write-Log "WARN" "Unhealthy critical containers: $names"
            Show-Notification "Container Health Issue" "Unhealthy: $names"
        }
    }

    if ($script:LastState -ne $healthy) {
        if ($healthy -and $script:LastState -ne $null) {
            Show-Notification "Docker Healthy" "Daemon and critical containers are healthy."
        }
        $script:LastState = $healthy
    }
}

Write-Log "INFO" "=== Docker Daemon Poll started at $script:StartTime ==="
Write-Log "INFO" "Mode: $(if($Watch){'Watch (interval='+$Interval+'s)'}else{'Single check'}) | MaxRetries=$MaxRetries | Notify=$Notify | CriticalContainers=$CriticalContainers"

Invoke-HealthCheck

if ($Watch) {
    while ($true) {
        Start-Sleep -Seconds $Interval
        Invoke-HealthCheck
    }
}
