# Docker Resilience on Windows: Analysis, Alternatives & Hardening

**Date**: 2026-05-04
**Context**: Docker Desktop 29.4.1 + WSL2 backend, running ~50 containers across 15+ projects.
**Symptom**: Daemon hangs or crashes, requiring "Docker triple kill" (kill Docker Desktop, terminate WSL, relaunch).

---

## 1. Root Cause Analysis

### 1.1 Memory Starvation (Primary)

| Metric | Value | Problem |
|--------|-------|---------|
| WSL2 memory cap | 10 GB (`~/.wslconfig`) | Far too low for workload |
| Docker daemon allocatable | ~9.7 GB | Actual usable RAM |
| Estimated workload need | **15-20 GB** | 3×Loki + 4×Grafana + 4×Prometheus + Weaviate + Immich + Postgres + apps |

**Evidence:**
- `wienerlinien-db` exited with code `255` (OOM kill)
- `vllm-windows` exited with code `137` (SIGKILL = OOM killer)
- Loki restarting across **3 projects** simultaneously (memory pressure trigger)
- `docker system df` shows 93.56 GB images + 38.52 GB build cache (disk pressure compounds memory pressure)

### 1.2 WSL2 Pipe Failures (Secondary)

When WSL2 is under memory pressure:
1. The `vsock` bridge between Windows and the WSL2 VM degrades
2. Docker CLI → daemon communication times out
3. `wsl --terminate docker-desktop` hangs (the VM is thrashing swap)
4. Docker Desktop GUI shows "Docker Engine Stopped" but WSL VM is stuck

### 1.3 com.docker.service Not Running

The Windows service `com.docker.service` is set to `StartType: Manual` and is currently `Stopped`. While Docker Desktop manages its own lifecycle, having this service stopped means there's no watchdog.

### 1.4 Fix Applied

Updated `~/.wslconfig`:
```ini
[wsl2]
memory=16GB          # +6 GB headroom
swap=8GB             # +4 GB swap buffer
processors=12        # Cap at half of 24 cores
localhostForwarding=true
kernelCommandLine=sysctl.vm.max_map_count=262144  # Required by Loki/ES/Weaviate

[experimental]
autoMemoryReclaim=gradual   # Return freed pages to Windows host
sparseVhd=true              # Prevent vhdx ballooning
```

**To apply**: `wsl --shutdown` (⚠️ kills all containers — plan maintenance window)

---

## 2. Disk Cleanup

```powershell
# Reclaim 38 GB build cache
docker builder prune -a -f

# Remove dangling images
docker image prune -f

# Aggressive: remove all unused images (not just dangling)
docker image prune -a -f

# Full system cleanup (containers, networks, images, build cache)
docker system prune -a -f --volumes  # ⚠️ deletes unused volumes
```

---

## 3. Docker Desktop Alternatives

### 3.1 Rancher Desktop (Recommended)

| Aspect | Docker Desktop | Rancher Desktop |
|--------|---------------|-----------------|
| License | Proprietary (free tier restricted) | Apache 2.0 |
| Container engine | dockerd only | dockerd **or** containerd |
| Kubernetes | Not included | Built-in (k3s) |
| WSL2 integration | Proprietary bridge | Direct WSL2 distro |
| Resource overhead | Heavy (Electron UI + services) | Lighter (Vue UI) |
| Memory baseline | ~2 GB idle | ~800 MB idle |
| GPU passthrough | Proprietary | Standard WSL2 |
| Rate limits | Docker Hub pull limits apply | Same (uses Docker Hub) |

**Migration path:**
1. Install Rancher Desktop (replaces Docker Desktop entirely)
2. Choose `dockerd` (moby) runtime for compatibility
3. `docker` CLI works identically — zero code changes
4. `docker-compose` files unchanged
5. WSL integration works via the `rancher-desktop` distro

**What you lose:** Docker Scout, Docker Build Cloud, Gordon AI. None of which you're using.

### 3.2 Native Docker Engine in WSL2 Ubuntu

Install Docker CE directly in your existing WSL2 Ubuntu distro:

```bash
# Inside WSL2 Ubuntu:
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER
sudo service docker start
```

Then expose the daemon to Windows:
```powershell
# In Windows: set DOCKER_HOST to WSL2 socket
$env:DOCKER_HOST = "unix:///var/run/docker.sock"
```

Or configure `~/.docker/config.json`:
```json
{
  "contexts": {
    "wsl-native": {
      "Endpoints": { "docker": { "Host": "unix:///var/run/docker.sock" } }
    }
  },
  "currentContext": "wsl-native"
}
```

**Pros:** Zero GUI overhead, full control, no license restrictions
**Cons:** No GUI (dashboard), manual lifecycle management, no Kubernetes

### 3.3 Podman Desktop

| Aspect | Docker Desktop | Podman Desktop |
|--------|---------------|----------------|
| License | Proprietary | Apache 2.0 |
| Daemon | Required (dockerd) | Daemonless (fork/exec) |
| Rootless | Partial | Full support |
| Compatibility | Native Docker API | Docker-compatible API via `podman-docker` |
| Pods | Not native | Native Kubernetes pods |
| WSL2 | Via Docker Desktop | Via Podman machine |

**Cons:** Some Docker Compose features not fully supported, image compatibility edge cases.

### 3.4 Recommendation: Rancher Desktop

For your workload (~50 containers, multiple compose projects), Rancher Desktop is the best drop-in replacement:
- Identical CLI experience
- Lower baseline memory (~1.2 GB saved)
- No Docker license concerns
- Better WSL2 memory management (standard WSL2, no proprietary bridge)

---

## 4. Hardening: Per-Container Memory Limits

### 4.1 Docker Compose Memory Caps

```yaml
# docker-compose.yml
services:
  loki:
    image: grafana/loki:latest
    deploy:
      resources:
        limits:
          memory: 1G     # Cap Loki at 1 GB
        reservations:
          memory: 512M
    command: -config.file=/etc/loki/local-config.yaml -target=all

  grafana:
    image: grafana/grafana:latest
    deploy:
      resources:
        limits:
          memory: 512M

  postgres:
    image: postgres:14-alpine
    deploy:
      resources:
        limits:
          memory: 512M
    command: postgres -c shared_buffers=128MB -c effective_cache_size=384MB
```

### 4.2 CLI Memory Limits

```powershell
docker run --memory=512m --memory-swap=1g my-image
docker update --memory=512m --memory-swap=1g container-name
```

### 4.3 WSL2 Memory Cap per Distro

You can further constrain the docker-desktop distro specifically:
```powershell
wsl --manage docker-desktop --set-memory 14GB
```

---

## 5. Observability Consolidation

Currently running **4 separate observability stacks** (Loki + Prometheus + Grafana each):
- `deepfang` (ports 10961-10963)
- `myconf` 
- `avatar-mcp`
- `tailscale-mcp`
- Plus standalone `grafana`, `loki`, `promtail`

**Recommendation**: Dedicate one stack (e.g., `monitoring-mcp` on ports 10850-10851) as the fleet-wide observability backbone. All other projects send logs/metrics there via:
- Promtail → centralized Loki (port 3100)
- Application metrics → centralized Prometheus (port 9090)
- Grafana reads from both

This alone would free **4-6 GB RAM** and eliminate 8+ containers.

---

## 6. Daemon Polling Script

Located at `scripts/docker-daemon-poll.ps1`.

### Usage

```powershell
# One-shot health check
.\docker-daemon-poll.ps1

# Continuous monitoring + desktop notifications
.\docker-daemon-poll.ps1 -Watch -Interval 30 -Notify

# Monitor specific critical containers
.\docker-daemon-poll.ps1 -CriticalContainers "weaviate,traefik,immich_server"

# Scheduled via Task Scheduler (every 5 minutes)
# Action: powershell.exe -ExecutionPolicy Bypass -File "D:\Dev\repos\sdr-mcp\scripts\docker-daemon-poll.ps1"
```

### What It Does

1. Tests `docker info` reachability
2. If unreachable: checks Docker Desktop process, WSL distro state
3. Recovery sequence:
   - **Gentle**: Start Docker Desktop if not running
   - **Medium**: `wsl --terminate docker-desktop` + wait for restart
   - **Hard**: Kill all Docker processes + full relaunch
4. Checks health of named critical containers
5. Logs to `$env:TEMP\docker-daemon-poll.log`
6. Optional Windows toast notifications on state changes

### Register as Scheduled Task

```powershell
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument '-ExecutionPolicy Bypass -File "D:\Dev\repos\sdr-mcp\scripts\docker-daemon-poll.ps1" -Notify'

$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 5)

Register-ScheduledTask `
    -TaskName "Docker Daemon Poll" `
    -Action $action `
    -Trigger $trigger `
    -RunLevel Highest `
    -Description "Health-checks Docker daemon and attempts auto-recovery"
```

---

## 7. Quick-Reference: Recovery Cheat Sheet

```powershell
# Level 1: Gentle restart
& "${env:ProgramFiles}\Docker\Docker\Docker Desktop.exe"

# Level 2: WSL restart (preserves data)
wsl --terminate docker-desktop
wsl --terminate docker-desktop-data

# Level 3: Full "triple kill"
Get-Process "Docker Desktop", "com.docker.backend", "com.docker.build" | Stop-Process -Force
wsl --shutdown
# Wait 10s, then relaunch Docker Desktop

# Level 4: Nuclear (rarely needed)
wsl --unregister docker-desktop
wsl --unregister docker-desktop-data
# Reinstall Docker Desktop
```

---

## 8. Migration Checklist (Rancher Desktop)

1. [ ] Export Docker Compose files for future reference: `docker compose config > backup-compose.yml`
2. [ ] Stop all containers: `docker compose down` (per project)
3. [ ] Uninstall Docker Desktop
4. [ ] Install Rancher Desktop (`winget install RancherDesktop.RancherDesktop`)
5. [ ] Select `dockerd` (moby) as container runtime
6. [ ] Verify: `docker info`, `docker compose up` in a test project
7. [ ] Re-apply memory limits per Section 4
8. [ ] Consolidate observability per Section 5
9. [ ] Register daemon poll scheduled task per Section 6
