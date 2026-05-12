# Container Deployment

This document describes the container-based deployment for apps.homemadebycvg.

## Overview

All apps are bundled into a **single container image** with:
- Multiple Gunicorn workers (one per app, each on a different port)
- Nginx reverse proxy for routing
- Supervisor for process management

## Architecture

```
┌───────────────────────────────────────────────────────────┐
│                    Container Image                        │
│  ┌─────────────────────────────────────────────────────┐  │
│  │              Nginx (port 80)                        │  │
│  │  - Hostname-based routing (production)              │  │
│  │  - Path-based routing (localhost development)       │  │
│  └─────────────────────────────────────────────────────┘  │
│                          │                                │
│         ┌────────────────┼────────────────┐               │
│         │                │                │               │
│    ┌────▼────┐     ┌────▼────┐     ┌────▼────┐            │
│    │ hello   │     │ parking │     │  ...    │            │
│    │ :5001   │     │ :5002   │     │ :5012   │            │
│    └─────────┘     └─────────┘     └─────────┘            │
│                                                           │
│  All managed by Supervisor                                │
└───────────────────────────────────────────────────────────┘
```

## Routing

### Hostname-based (Production)

| Hostname | App |
|----------|-----|
| `hello.app.homemadebycvg.com` | hello |
| `parking.app.homemadebycvg.com` | parking |
| `archiku.com` | parking |
| `nationofpositivity.com` | nationofpositivity |
| `homemadebycvg.com` | homemadebycvg.com |
| `getijden.app.homemadebycvg.com` | getijden |
| `letmelearn.app.homemadebycvg.com` | letmelearn |
| `baseweb-demo.app.homemadebycvg.com` | baseweb-demo |
| `howifeel.app.homemadebycvg.com` | howifeel |
| `oatk-demo.app.homemadebycvg.com` | oatk |

### Path-based (Local Development)

When accessing via `localhost`, use path prefixes:
- `http://localhost:8080/hello`
- `http://localhost:8080/parking`
- etc.

## Building

```bash
make build
```

## Running

```bash
# Start the container
make run

# View logs
make logs

# Check supervisor status
make status

# Stop and cleanup
make stop
```

## Testing

```bash
# Test hello app
curl http://localhost:8080/hello

# Test parking app
curl http://localhost:8080/parking

# Test via hostname (requires /etc/hosts setup)
curl http://hello.local:8080
```

## Troubleshooting

### View app-specific logs

```bash
make logs-app APP=hello
```

### Restart a specific app

```bash
make restart-app APP=hello
```

### Shell into container

```bash
make shell
```

## Port Mapping

| Internal | External (default) | Purpose |
|----------|-------------------|---------|
| 80 | 8080 | Nginx HTTP |
| 5001-5012 | - | App workers (internal only) |

## Notes

- The image is built with Podman but is fully Docker-compatible
- All apps run in a single container (monolithic approach)
- Supervisor manages all processes (nginx + gunicorn workers)
- Nginx handles all routing decisions
