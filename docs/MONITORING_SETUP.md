# Monitoring Setup Reference

Complete documentation for the monitoring stack implemented in this project.

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Container (apps-homemadebycvg)                    │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          Supervisord                                 │   │
│  │                                                                      │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │   │
│  │  │    nginx    │  │  frontpage  │  │   hello     │  ... (11 apps)    │   │
│  │  │   :10000    │  │   :5000     │  │   :5001     │                   │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                   │   │
│  │                                                                      │   │
│  │  ┌─────────────────────────────────────────────────────────────────┐ │   │
│  │  │                     Monitoring Stack                            │ │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │ │   │
│  │  │  │ Prometheus  │  │   Grafana   │  │    Loki     │              │ │   │
│  │  │  │   :9090     │  │   :3000     │  │   :3100     │              │ │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘              │ │   │
│  │  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │ │   │
│  │  │  │  Promtail   │  │node_exporter│  │nginx_export │              │ │   │
│  │  │  │   :9080     │  │   :9100     │  │   :9114     │              │ │   │
│  │  │  └─────────────┘  └─────────────┘  └─────────────┘              │ │   │
│  │  └─────────────────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

| Component | Port | Purpose |
|-----------|------|---------|
| **Prometheus** | 9090 | Metrics collection and storage |
| **Grafana** | 3000 | Visualization dashboards |
| **Loki** | 3100 | Log aggregation |
| **Promtail** | 9080 | Log shipper (reads logs, sends to Loki) |
| **node_exporter** | 9100 | System metrics (CPU, memory, disk, network) |
| **nginx_exporter** | 9114 | Nginx metrics (connections, requests) |

## Directory Structure

```
apps.homemadebycvg/
├── Dockerfile                    # Container image definition
├── supervisord.conf             # Process manager configuration
├── nginx.conf                   # Reverse proxy configuration
├── Makefile                     # Build/run commands
├── .env.local                    # Environment variables (not in git)
│
├── monitoring/                  # Monitoring package (reusable)
│   ├── __init__.py
│   ├── app_metrics.py          # Flask/Quart/Baseweb metrics module
│   ├── security_monitor.py     # Security monitoring middleware
│   └── README.md               # Package documentation
│
├── monitoring/                   # Infrastructure configs
│   ├── prometheus.yml          # Prometheus scrape config
│   ├── loki-config.yml         # Loki log aggregation config
│   ├── promtail-config.yml    # Promtail log collection config
│   ├── grafana.ini             # Grafana server config
│   └── grafana/
│       ├── provisioning/
│       │   ├── datasources/
│       │   │   └── datasources.yml    # Prometheus & Loki datasources
│       │   └── dashboards/
│       │       └── dashboards.yml     # Dashboard auto-loading config
│       └── dashboards/
│           ├── system-overview.json   # System metrics dashboard
│           ├── applications.json     # App metrics dashboard
│           ├── infrastructure.json    # Nginx/Supervisor dashboard
│           └── security.json          # Security monitoring dashboard
│
└── apps/                         # Application submodules
    ├── frontpage/
    ├── hello/
    ├── parking/
    └── ...
```

## Configuration Files

### Dockerfile

Location: `/Dockerfile`

Key monitoring additions:

```dockerfile
# Install system dependencies + monitoring tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    git \
    ca-certificates \
    curl \
    apache2-utils \
    && rm -rf /var/lib/apt/lists/*

# Create directories for monitoring
RUN mkdir -p /opt/monitoring/prometheus/data \
    && mkdir -p /opt/monitoring/grafana/data \
    && mkdir -p /opt/monitoring/loki/data \
    && mkdir -p /opt/monitoring/config \
    && mkdir -p /opt/monitoring/bin \
    && mkdir -p /var/log/promtail

# Download and install monitoring binaries
RUN curl -sSL ... | tar xz -C /tmp/ && \
    mv /tmp/node_exporter-*/node_exporter /opt/monitoring/bin/ && \
    ...

# Copy monitoring configurations
COPY monitoring/prometheus.yml /opt/monitoring/config/
COPY monitoring/loki-config.yml /opt/monitoring/config/
COPY monitoring/promtail-config.yml /opt/monitoring/config/
COPY monitoring/grafana.ini /opt/monitoring/config/
COPY monitoring/grafana/provisioning /opt/monitoring/config/grafana/provisioning
COPY monitoring/grafana/dashboards /opt/monitoring/grafana/dashboards

# Copy monitoring package for apps
COPY monitoring/ /app/monitoring/
```

### supervisord.conf

Location: `/supervisord.conf`

Monitoring processes configuration:

```ini
# === MONITORING STACK ===

[program:prometheus]
command=/opt/monitoring/bin/prometheus --config.file=/opt/monitoring/config/prometheus.yml --storage.tsdb.path=/opt/monitoring/prometheus/data --web.listen-address=127.0.0.1:9090 --storage.tsdb.retention.time=7d --web.enable-lifecycle
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
priority=5

[program:grafana]
command=/usr/share/grafana/bin/grafana-server --homepath=/usr/share/grafana --config=/opt/monitoring/config/grafana.ini
autostart=true
autorestart=true
environment=GF_SECURITY_ADMIN_PASSWORD="%(ENV_GRAFANA_ADMIN_PASSWORD)s",...
priority=5

[program:loki]
command=/opt/monitoring/bin/loki -config.file=/opt/monitoring/config/loki-config.yml
autostart=true
autorestart=true
priority=5

[program:promtail]
command=/opt/monitoring/bin/promtail -config.file=/opt/monitoring/config/promtail-config.yml
autostart=true
autorestart=true
priority=5

[program:node_exporter]
command=/opt/monitoring/bin/node_exporter --web.listen-address=127.0.0.1:9100 ...
autostart=true
autorestart=true
priority=5

[program:nginx_exporter]
command=/opt/monitoring/bin/nginx-prometheus-exporter --nginx.scrape-uri=http://127.0.0.1:9113/stub_status --web.listen-address=127.0.0.1:9114
autostart=true
autorestart=true
priority=5
```

### Prometheus Configuration

Location: `/monitoring/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['127.0.0.1:9090']

  # System metrics
  - job_name: 'node'
    static_configs:
      - targets: ['127.0.0.1:9100']

  # Nginx metrics
  - job_name: 'nginx'
    static_configs:
      - targets: ['127.0.0.1:9114']

  # Application metrics (each app exposes /metrics)
  - job_name: 'frontpage'
    static_configs:
      - targets: ['127.0.0.1:5000']
    metrics_path: '/metrics'
    
  # ... (one job per application)
```

### Nginx Configuration

Location: `/nginx.conf`

Monitoring endpoints:

```nginx
# Access logging for Promtail
log_format main '$remote_addr - $remote_user [$time_local] "$request" '
                '$status $body_bytes_sent "$http_host" - "$http_referer" '
                '"$http_user_agent" "$http_x_forwarded_for" '
                'rt=$request_time uct="$upstream_connect_time" '
                'uht="$upstream_header_time" urt="$upstream_response_time"';
access_log /var/log/nginx/access.log main;

# Nginx stub_status for nginx-prometheus-exporter
server {
    listen 127.0.0.1:9113;
    server_name localhost;
    
    location /stub_status {
        stub_status;
        access_log off;
    }
}

# Grafana Dashboard - External access
server {
    listen 10000;
    server_name monitor.homemadebycvg.com monitor.homemadebycvg.local;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Loki Configuration

Location: `/monitoring/loki-config.yml`

```yaml
auth_enabled: false

server:
  http_listen_port: 3100

common:
  instance_addr: 127.0.0.1
  path_prefix: /opt/monitoring/loki/data
  storage:
    filesystem:
      chunks_directory: /opt/monitoring/loki/data/chunks
      rules_directory: /opt/monitoring/loki/data/rules
  replication_factor: 1

schema_config:
  configs:
    - from: 2020-10-24
      store: tsdb
      object_store: filesystem
      schema: v13

limits_config:
  retention_period: 168h  # 7 days
```

### Promtail Configuration

Location: `/monitoring/promtail-config.yml`

```yaml
server:
  http_listen_port: 9080

positions:
  filename: /var/log/promtail/positions.yaml

clients:
  - url: http://127.0.0.1:3100/loki/api/v1/push

scrape_configs:
  # Supervisor logs
  - job_name: supervisor
    static_configs:
      - targets: [localhost]
        labels:
          job: supervisor
          __path__: /var/log/supervisor/*.log

  # Nginx access logs
  - job_name: nginx_access
    static_configs:
      - targets: [localhost]
        labels:
          job: nginx
          __path__: /var/log/nginx/access.log
```

### Grafana Configuration

Location: `/monitoring/grafana.ini`

```ini
[server]
http_addr = 127.0.0.1
http_port = 3000

[database]
type = sqlite3
path = /opt/monitoring/grafana/data/grafana.db

[security]
admin_user = admin
admin_password = ${GRAFANA_ADMIN_PASSWORD}  # Set via environment variable

[users]
allow_sign_up = false

[dashboards]
default_home_dashboard_path = /opt/monitoring/grafana/dashboards/system-overview.json
```

## Metrics Available

### System Metrics (node_exporter)

| Metric | Description |
|--------|-------------|
| `node_cpu_seconds_total` | CPU time by mode (idle, user, system, etc.) |
| `node_memory_MemTotal_bytes` | Total memory |
| `node_memory_MemAvailable_bytes` | Available memory |
| `node_filesystem_size_bytes` | Filesystem size |
| `node_filesystem_avail_bytes` | Available filesystem space |
| `node_disk_read_bytes_total` | Disk bytes read |
| `node_disk_written_bytes_total` | Disk bytes written |
| `node_network_receive_bytes_total` | Network bytes received |
| `node_network_transmit_bytes_total` | Network bytes transmitted |
| `node_load1`, `node_load5`, `node_load15` | Load averages |

### Nginx Metrics (nginx-prometheus-exporter)

| Metric | Description |
|--------|-------------|
| `nginx_up` | Nginx process status (1 = up) |
| `nginx_connections_active` | Active connections |
| `nginx_connections_reading` | Connections being read |
| `nginx_connections_writing` | Connections being written |
| `nginx_connections_waiting` | Idle connections |
| `nginx_http_requests_total` | Total HTTP requests |

### Application Metrics (app_metrics.py)

| Metric | Description |
|--------|-------------|
| `app_request_count_total` | Total requests by app, method, endpoint, status |
| `app_request_latency_seconds` | Request latency histogram |
| `app_requests_in_progress` | Currently processing requests |
| `app_info` | Application metadata |
| `app_auth_attempts_total` | Authentication attempts |
| `app_suspicious_requests_total` | Detected suspicious requests |

## Dashboards

### System Overview Dashboard

Panels:
- CPU Usage Gauge
- Memory Usage Gauge
- Disk I/O Graph
- Network Traffic Graph
- Disk Usage Gauge
- Load Average Stats

### Applications Dashboard

Panels:
- Request Rate by App
- Response Time (p95)
- Error Rate (5xx)
- Active Requests by App
- HTTP Status Codes Distribution
- Requests by App Distribution

### Infrastructure Dashboard

Panels:
- Supervisor Process Status (up/down)
- Nginx Request Rate
- Nginx Active Connections
- Nginx HTTP Status Codes
- Supervisor Process Restarts

### Security Dashboard

Panels:
- Failed Authentication Attempts
- Suspicious Requests by Type
- HTTP 4xx Errors
- HTTP 5xx Errors
- Recent Suspicious Activity Logs
- Nginx Error Logs by Status
- Authentication Failures

## Runtime Commands

### Checking Status

```bash
# Check all monitoring processes
make monitoring-status
# Equivalent: podman exec apps-homemadebycvg supervisorctl status prometheus grafana loki promtail node_exporter nginx_exporter

# Check all supervisor processes
podman exec apps-homemadebycvg supervisorctl status

# Check specific process
podman exec apps-homemadebycvg supervisorctl status prometheus
```

### Viewing Logs

```bash
# Follow all logs
make logs

# Follow specific component logs
make prometheus-logs
make grafana-logs
make loki-logs
make promtail-logs

# View nginx access logs
podman exec apps-homemadebycvg tail -f /var/log/nginx/access.log

# View supervisor logs
podman exec apps-homemadebycvg tail -f /var/log/supervisor/prometheus*.log
```

### Health Checks

```bash
# Check app health endpoints
make health-check

# Manual health checks
podman exec apps-homemadebycvg curl -s http://127.0.0.1:5000/health
podman exec apps-homemadebycvg curl -s http://127.0.0.1:5001/health

# Check metrics endpoints
podman exec apps-homemadebycvg curl -s http://127.0.0.1:9090/metrics | head
podman exec apps-homemadebycvg curl -s http://127.0.0.1:9100/metrics | head
podman exec apps-homemadebycvg curl -s http://127.0.0.1:9114/metrics | head

# Check Loki
podman exec apps-homemadebycvg curl -s http://127.0.0.1:3100/ready
```

### Querying Metrics

```bash
# Query Prometheus via API
podman exec apps-homemadebycvg curl -s 'http://127.0.0.1:9090/api/v1/query?query=up' | python3 -m json.tool

# Query specific metric
podman exec apps-homemadebycvg curl -s 'http://127.0.0.1:9090/api/v1/query?query=node_memory_MemTotal_bytes' | python3 -m json.tool

# Query range (last hour)
podman exec apps-homemadebycvg curl -s 'http://127.0.0.1:9090/api/v1/query_range?query=up&start='$(date -u -v-1H +%s)'&end='$(date -u +%s) | python3 -m json.tool
```

### Restarting Components

```bash
# Restart all monitoring
podman exec apps-homemadebycvg supervisorctl restart prometheus grafana loki promtail node_exporter nginx_exporter

# Restart specific component
podman exec apps-homemadebycvg supervisorctl restart prometheus
podman exec apps-homemadebycvg supervisorctl restart grafana
```

### Port Forwarding

```bash
# Access Grafana from local browser
make grafana-forward
# Then open: http://localhost:3000

# Access Prometheus from local browser
make prometheus-forward
# Then open: http://localhost:9090
```

## Grafana Usage

### Accessing the Dashboard

1. Configure DNS or `/etc/hosts`:
   ```
   127.0.0.1 monitor.homemadebycvg.local
   ```

2. Or use port forward:
   ```bash
   make grafana-forward
   ```

3. Open: `http://localhost:3000` or `http://monitor.homemadebycvg.local:8080`

4. Login with:
   - Username: `admin`
   - Password: `${GRAFANA_ADMIN_PASSWORD}` (from `.env.local`)

### Dashboard Navigation

1. **Dashboards** → **Apps** folder
2. Select dashboard:
   - System Overview
   - Application Metrics
   - Infrastructure
   - Security Monitoring

### Creating Custom Dashboards

1. Go to **Dashboards** → **New Dashboard**
2. Add visualization
3. Select Prometheus datasource
4. Write PromQL query, e.g.:
   ```
   rate(app_request_count_total[5m])
   ```
5. Configure visualization options
6. Save dashboard

### PromQL Examples

```promql
# CPU usage (100 - idle)
100 - avg(irate(node_cpu_seconds_total{mode="idle"}[5m])) * 100

# Memory usage
(node_memory_MemTotal_bytes - node_memory_MemAvailable_bytes) / node_memory_MemTotal_bytes * 100

# Disk usage
(node_filesystem_size_bytes - node_filesystem_avail_bytes) / node_filesystem_size_bytes * 100

# Request rate by app
sum by (app) (rate(app_request_count_total[5m]))

# Error rate
sum by (app) (rate(app_request_count_total{http_status=~"5.."}[5m]))

# p95 latency
histogram_quantile(0.95, sum by (app, le) (rate(app_request_latency_seconds_bucket[5m])))

# Active connections (nginx)
nginx_connections_active
```

## Application Integration

### Adding Metrics to Apps

**Flask:**
```python
from flask import Flask
from monitoring.app_metrics import init_flask_metrics

app = Flask(__name__)
init_flask_metrics(app, app_name="myapp", app_version="1.0.0")

# App now has:
# - GET /metrics - Prometheus metrics
# - GET /health - Health check
```

**Quart:**
```python
from quart import Quart
from monitoring.app_metrics import init_quart_metrics

app = Quart(__name__)
await init_quart_metrics(app, app_name="myapp", app_version="1.0.0")
```

**Baseweb:**
```python
from baseweb import Baseweb
from monitoring.app_metrics import init_baseweb_metrics

server = Baseweb("myapp")
init_baseweb_metrics(server, app_name="myapp", app_version="1.0.0")
```

### Security Monitoring

```python
from monitoring.security_monitor import create_flask_security_middleware

app = Flask(__name__)
monitor = create_flask_security_middleware(app, app_name="myapp")

# Tracks:
# - SQL injection patterns
# - XSS attempts
# - Path traversal
# - Command injection
# - Rate limiting
```

## Troubleshooting

### Common Issues

**Prometheus not scraping:**
```bash
# Check Prometheus targets
podman exec apps-homemadebycvg curl -s http://127.0.0.1:9090/api/v1/targets | python3 -m json.tool

# Check if endpoint is reachable
podman exec apps-homemadebycvg curl -s http://127.0.0.1:9100/metrics | head
```

**Grafana shows "No data":**
1. Check datasource: **Connections** → **Data Sources** → **Prometheus** → **Test**
2. Check time range: Top-right time picker
3. Check datasource UID matches dashboard

**Loki not receiving logs:**
```bash
# Check Promtail status
podman exec apps-homemadebycvg supervisorctl status promtail

# Check Loki is up
podman exec apps-homemadebycvg curl -s http://127.0.0.1:3100/ready

# Check logs exist
podman exec apps-homemadebycvg ls -la /var/log/nginx/
podman exec apps-homemadebycvg ls -la /var/log/supervisor/
```

**node_exporter missing metrics:**
```bash
# Check which collectors are enabled
podman exec apps-homemadebycvg supervisorctl status node_exporter

# Check metrics manually
podman exec apps-homemadebycvg curl -s http://127.0.0.1:9100/metrics | grep node_
```

### Log Locations

Inside container:
```
/var/log/nginx/access.log      # Nginx access logs
/var/log/nginx/error.log       # Nginx error logs
/var/log/supervisor/*.log      # Supervisor/app logs
/var/log/promtail/positions.yaml  # Promtail position tracking
/opt/monitoring/prometheus/data/  # Prometheus TSDB
/opt/monitoring/grafana/data/     # Grafana database
/opt/monitoring/loki/data/        # Loki log storage
```

### Useful Queries

```bash
# Get container resource usage
podman stats apps-homemadebycvg

# Check container processes
podman top apps-homemadebycvg

# Inspect container
podman inspect apps-homemadebycvg

# Check container network
podman exec apps-homemadebycvg netstat -tuln
```

## Environment Variables

Required in `.env.local`:

```bash
# Grafana admin password
GRAFANA_ADMIN_PASSWORD=your-secure-password

# Application-specific variables (existing)
# NATIONOFPOSITIVITY_MONGODB_URI=...
# LETMELEARN_MONGODB_URI=...
# etc.
```

## Resource Estimates

| Component | Memory | Disk | CPU |
|-----------|--------|------|-----|
| Prometheus | ~200MB | ~100MB/7d | ~1% |
| Grafana | ~100MB | ~50MB | ~0.5% |
| Loki | ~100MB | ~200MB/7d | ~0.5% |
| Promtail | ~30MB | Negligible | ~0.1% |
| node_exporter | ~20MB | Negligible | ~0.1% |
| nginx_exporter | ~10MB | Negligible | ~0.05% |
| **Total** | ~460MB | ~350MB | ~3% |

## Maintenance

### Log Retention

Default retention: 7 days

To modify:
```yaml
# In prometheus.yml
--storage.tsdb.retention.time=30d

# In loki-config.yml
limits_config:
  retention_period: 720h  # 30 days
```

### Backup

```bash
# Backup Prometheus data
podman exec apps-homemadebycvg tar czf - /opt/monitoring/prometheus/data > prometheus-backup.tar.gz

# Backup Grafana data
podman exec apps-homemadebycvg tar czf - /opt/monitoring/grafana/data > grafana-backup.tar.gz

# Backup Loki data
podman exec apps-homemadebycvg tar czf - /opt/monitoring/loki/data > loki-backup.tar.gz
```

### Upgrading

```bash
# Update binary versions in Dockerfile
# Example: Update Prometheus from 2.51.0 to 2.52.0
sed -i 's/v2.51.0/v2.52.0/g' Dockerfile

# Rebuild
make stop build run
```

## Future Improvements

1. **Alerting**: Add Alertmanager for notifications
2. **Long-term storage**: Configure remote_write to Thanos/Cortex
3. **Custom metrics**: Add application-specific metrics
4. **Log parsing**: Add more structured log parsing rules
5. **Dashboard automation**: Generate dashboards from app configs
