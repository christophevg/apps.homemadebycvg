# Podman Reference Guide

A comprehensive guide for working with Podman on macOS.

## What is Podman?

Podman (Pod Manager) is a container runtime that's an alternative to Docker. On macOS, it runs containers inside a Linux virtual machine using Apple's Hypervisor Framework (applehv). Key differences from Docker:

- **Rootless by default** - Runs without root privileges
- **Daemonless** - No background daemon required
- **Compatible with Docker** - Uses OCI-compliant images and can run Dockerfiles

## Architecture on macOS

```
┌─────────────────────────────────────────────────────────────┐
│                        macOS Host                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                    Podman CLI                         │  │
│  └───────────────────────────────────────────────────────┘  │
│                            │                                 │
│                            ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │           Podman Machine (Linux VM)                   │  │
│  │   ┌─────────────────────────────────────────────┐     │  │
│  │   │           podman-machine-default             │     │  │
│  │   │   ┌─────────┐  ┌─────────┐  ┌─────────┐     │     │  │
│  │   │   │Container│  │Container│  │Container│     │     │  │
│  │   │   │   A     │  │   B     │  │   C     │     │     │  │
│  │   │   └─────────┘  └─────────┘  └─────────┘     │     │  │
│  │   │                Images                        │     │  │
│  │   └─────────────────────────────────────────────┘     │  │  │
│  │                                                       │  │
│  │   Disk: ~/.local/share/containers/podman/machine/    │  │  │
│  │         applehv/podman-machine-default-arm64.raw     │  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Essential Commands

### Machine Management

```bash
# List podman machines
podman machine list

# Create a new machine (default: rootless, 100GB disk)
podman machine init

# Create with custom settings
podman machine init --cpus 4 --memory 4096 --disk-size 50

# Start/stop machine
podman machine start
podman machine stop

# SSH into the machine
podman machine ssh

# Remove machine (WARNING: deletes all data)
podman machine rm -f

# Set machine to run as root (for privileged containers)
podman machine set --rootful
```

### Container Management

```bash
# List running containers
podman ps

# List all containers (including stopped)
podman ps -a

# Run a container
podman run -d --name mycontainer nginx

# Run with port mapping
podman run -d --name mycontainer -p 8080:80 nginx

# Run with environment variables
podman run -d --name mycontainer -e MY_VAR=value nginx

# Run with volume mount
podman run -d --name mycontainer -v /host/path:/container/path nginx

# Stop/Start/Restart
podman stop mycontainer
podman start mycontainer
podman restart mycontainer

# Remove container
podman rm mycontainer

# Remove running container
podman rm -f mycontainer

# Execute command in running container
podman exec mycontainer ls /app
podman exec -it mycontainer /bin/bash  # Interactive shell

# View logs
podman logs mycontainer
podman logs -f mycontainer  # Follow (tail)

# Inspect container details
podman inspect mycontainer
```

### Image Management

```bash
# List images
podman images

# List all images including intermediate
podman images -a

# Build image from Dockerfile
podman build -t myimage:latest .

# Build with custom Dockerfile
podman build -t myimage:latest -f Dockerfile.prod .

# Pull image from registry
podman pull nginx:latest
podman pull docker.io/library/nginx:latest

# Push image to registry
podman push myimage:latest docker.io/myuser/myimage:latest

# Tag image
podman tag myimage:latest myimage:v1.0

# Remove image
podman rmi myimage:latest

# Remove all unused images
podman image prune -f

# Show image history
podman history myimage:latest

# Save/load image as tar file
podman save -o myimage.tar myimage:latest
podman load -i myimage.tar

# Inspect image
podman inspect myimage:latest
```

### Cleanup Commands

```bash
# Remove dangling images (untagged)
podman image prune -f

# Remove all unused images (not just dangling)
podman image prune -a -f

# Remove stopped containers
podman container prune -f

# Remove unused volumes
podman volume prune -f

# Remove everything unused (images, containers, volumes, networks)
podman system prune -a -f --volumes

# Show disk usage
podman system df

# Detailed disk usage
podman system df -v
```

### Logs and Debugging

```bash
# Container logs
podman logs mycontainer
podman logs --tail 100 mycontainer    # Last 100 lines
podman logs --since 1h mycontainer     # Last hour

# Follow logs in real-time
podman logs -f mycontainer

# Inspect container state
podman inspect mycontainer

# Show container processes
podman top mycontainer

# Show container resource usage
podman stats mycontainer
podman stats  # All running containers

# Events (audit log)
podman events
```

### Networking

```bash
# List networks
podman network ls

# Inspect network
podman network inspect bridge

# Create network
podman network create mynetwork

# Run container on network
podman run --network mynetwork nginx

# Port forwarding
podman run -p 8080:80 nginx           # Map host 8080 to container 80
podman run -p 127.0.0.1:8080:80 nginx # Bind to specific interface

# Expose port without mapping (for linking)
podman run --expose 8080 nginx
```

### Volumes

```bash
# List volumes
podman volume ls

# Create volume
podman volume create myvolume

# Inspect volume
podman volume inspect myvolume

# Use volume in container
podman run -v myvolume:/data nginx

# Mount host directory
podman run -v /host/path:/container/path nginx

# Remove volume
podman volume rm myvolume

# Remove all unused volumes
podman volume prune -f
```

## Our Project's Makefile Commands

```makefile
# Build container image
make build
# Equivalent to: podman build -t apps-homemadebycvg:container .

# Run container
make run
# Equivalent to: podman run -d --name apps-homemadebycvg --env-file .env.local -p 8080:10000 apps-homemadebycvg:container

# Stop and remove container
make stop
# Equivalent to: podman stop apps-homemadebycvg; podman rm apps-homemadebycvg

# View logs
make logs
# Equivalent to: podman logs -f apps-homemadebycvg

# Shell into container
make shell
# Equivalent to: podman exec -it apps-homemadebycvg /bin/bash

# Check supervisor status
make status
# Equivalent to: podman exec apps-homemadebycvg supervisorctl status

# Rebuild (stop, build, run)
make rebuild
```

## Monitoring Commands

```bash
# Check monitoring stack status
make monitoring-status

# View component logs
make prometheus-logs
make grafana-logs
make loki-logs
make promtail-logs

# Health check all apps
make health-check

# Port forward Grafana to local
make grafana-forward

# Port forward Prometheus to local
make prometheus-forward
```

## Common Workflows

### Rebuilding After Dockerfile Changes

```bash
# Stop and remove old container
make stop

# Prune old images
podman image prune -f

# Rebuild
make build

# Run new container
make run
```

### Debugging a Container

```bash
# Get a shell
make shell

# Check processes
podman exec apps-homemadebycvg supervisorctl status

# View specific process logs
podman exec apps-homemadebycvg tail -f /var/log/supervisor/prometheus*.log

# Test connectivity
podman exec apps-homemadebycvg curl http://127.0.0.1:9090/metrics

# Copy file from container
podman cp apps-homemadebycvg:/opt/monitoring/config/prometheus.yml ./

# Copy file to container
podman cp ./prometheus.yml apps-homemadebycvg:/opt/monitoring/config/
```

### Managing the Podman Machine

```bash
# Check machine status
podman machine list

# Check machine info
podman machine inspect

# SSH into the Linux VM
podman machine ssh

# Inside the VM, check:
# - Disk: df -h
# - Memory: free -m
# - Processes: top

# Restart machine if issues
podman machine stop
podman machine start

# For macOS memory issues
podman machine set --memory 4096  # 4GB RAM
```

## Disk Space Management

### Understanding Podman Disk Usage

```bash
# Show disk usage summary
podman system df

# Show detailed breakdown
podman system df -v
```

Output explained:
```
TYPE           TOTAL    ACTIVE   SIZE        RECLAIMABLE
Images         46       1        2.764GB     2.764GB (100%)
Containers     1        1        31.01MB     0B (0%)
Local Volumes  0        0        0B          0B
```

- **Images**: Downloaded/build images (reclaimable if unused)
- **Containers**: Running container layer (not reclaimable while running)
- **Volumes**: Persistent data (only reclaimable if unused)

### Cleaning Up

```bash
# Remove dangling images (untagged)
podman image prune -f

# Remove ALL unused images (keep only images used by containers)
podman image prune -a -f

# Remove stopped containers
podman container prune -f

# Full cleanup
podman system prune -a -f --volumes
```

### Mac-Specific: Shrinking the VM Disk

The Podman VM disk image is stored at:
```
~/.local/share/containers/podman/machine/applehv/podman-machine-default-arm64.raw
```

Check actual size:
```bash
ls -lh ~/.local/share/containers/podman/machine/applehv/*.raw  # Logical size
du -h ~/.local/share/containers/podman/machine/applehv/*.raw   # Actual size
```

To reclaim space:
1. `podman system prune -a -f --volumes` (inside VM)
2. The VM disk is sparse - unused space should be freed automatically
3. If still large, consider recreating the machine with smaller disk

### Starting Fresh (Nuclear Option)

```bash
# WARNING: This deletes everything!
podman machine rm -f
podman machine init --disk-size 50  # 50GB disk
podman machine start

# Rebuild your images
make build
```

## Configuration Files

### Container Configuration Locations

```
~/.config/containers/          # Podman configuration
├── containers.conf            # Main config
├── storage.conf               # Storage settings
└── auth.json                  # Registry credentials

~/.local/share/containers/     # Container data
├── podman/
│   └── machine/               # VM disk images
│       └── applehv/
│           └── podman-machine-default-arm64.raw  # Main disk image
└── storage/                   # Image/container storage
```

### Environment Variables

```bash
# Use Docker-compatible API socket
export DOCKER_HOST='unix:///var/folders/.../podman/podman-machine-default-api.sock'

# Verbose output
export PODMAN_DEBUG=1

# Log level
export LOG_LEVEL=debug
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
podman logs mycontainer

# Check container state
podman inspect mycontainer

# Try running interactively
podman run -it --rm myimage /bin/bash
```

### Port Already in Use

```bash
# Find what's using port
lsof -i :8080

# Use different host port
podman run -p 8081:80 nginx
```

### Permission Denied

```bash
# For privileged operations, use rootful machine
podman machine set --rootful
podman machine stop
podman machine start
```

### Out of Disk Space

```bash
# Check usage
podman system df -v

# Clean up
podman system prune -a -f --volumes

# If still full, reduce VM disk
podman machine rm -f
podman machine init --disk-size 50
podman machine start
```

### Network Issues

```bash
# List networks
podman network ls

# Recreate default network
podman network rm podman
podman network create podman

# Check DNS inside container
podman exec mycontainer cat /etc/resolv.conf
```

## Useful Aliases

Add to `~/.zshrc` or `~/.bashrc`:

```bash
# Podman shortcuts
alias p='podman'
alias ps='podman ps'
alias psa='podman ps -a'
alias pi='podman images'
alias pia='podman images -a'
alias prm='podman rm -f'
alias prmi='podman rmi -f'
alias plog='podman logs -f'
alias psh='podman exec -it'
alias pprune='podman system prune -a -f --volumes'
alias pbuild='podman build -t'
alias prun='podman run -d --name'

# Make shortcuts (for this project)
alias mkb='make build'
alias mkr='make run'
alias mkst='make stop'
alias mkl='make logs'
alias mkrb='make rebuild'
```

## Comparison: Podman vs Docker

| Feature | Podman | Docker |
|---------|--------|--------|
| Daemon | None (daemonless) | dockerd |
| Root access | Not required (rootless) | Usually required |
| Dockerfile | ✅ Compatible | ✅ Native |
| Docker Compose | Via podman-compose | docker-compose |
| Kubernetes YAML | ✅ `podman play kube` | ❌ |
| Socket | `/var/run/podman/podman.sock` | `/var/run/docker.sock` |
| macOS VM | applehv/qemu | HyperKit |
| Disk location | `~/.local/share/containers/` | `~/Library/Containers/` |

## Resources

- Official Documentation: https://docs.podman.io/
- Podman GitHub: https://github.com/containers/podman
- Podman Compose: https://github.com/containers/podman-compose
- Awesome Podman: https://github.com/containers/awesome-podman