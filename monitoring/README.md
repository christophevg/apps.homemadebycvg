# Monitoring Package

Standalone Prometheus metrics integration for Flask, Quart, and Baseweb applications.

## Features

- **Zero Dependencies** (except `prometheus_client`)
- **Works with Flask, Quart, and Baseweb** (both Flask v0.4.x and Quart v0.5.x)
- **Single Import Line** to enable metrics
- **Graceful Degradation** when `prometheus_client` is not installed
- **Environment Variable Toggle** via `MONITORING_ENABLED=true/false`
- **Security Monitoring** with pattern detection for SQL injection, XSS, etc.

## Installation

Add to your requirements:

```txt
prometheus_client>=0.15.0
```

## Usage

### Flask Applications

```python
from flask import Flask
from monitoring.app_metrics import init_flask_metrics

app = Flask(__name__)
init_flask_metrics(app, app_name="hello", app_version="1.0.0")

# App now has:
# - GET /metrics - Prometheus metrics endpoint
# - GET /health  - Health check endpoint

@app.route("/")
def hello():
    return "Hello, World!"
```

### Quart Applications

```python
from quart import Quart
from monitoring.app_metrics import init_quart_metrics

app = Quart(__name__)
init_quart_metrics(app, app_name="frontpage", app_version="1.0.0")

@app.route("/")
async def hello():
    return "Hello, World!"
```

### Baseweb Applications

```python
from baseweb import Baseweb
from monitoring.app_metrics import init_baseweb_metrics

server = Baseweb("myapp")
init_baseweb_metrics(server, app_name="myapp", app_version="1.0.0")

# Works with both Flask-based (v0.4.x) and Quart-based (v0.5.x) Baseweb
```

## Security Monitoring

Enable passive security monitoring to detect suspicious requests:

```python
from monitoring.security_monitor import create_flask_security_middleware

app = Flask(__name__)
monitor = create_flask_security_middleware(app, app_name="myapp")

# Tracks:
# - SQL injection patterns
# - XSS patterns
# - Path traversal attempts
# - Command injection
# - SSRF attempts
# - Rate limiting
```

For Quart:

```python
from monitoring.security_monitor import create_quart_security_middleware

app = Quart(__name__)
monitor = create_quart_security_middleware(app, app_name="myapp")
```

## Metrics Exposed

| Metric | Type | Labels | Description |
|--------|------|--------|-------------|
| `app_request_count_total` | Counter | app, method, endpoint, http_status | Total HTTP requests |
| `app_request_latency_seconds` | Histogram | app, method, endpoint | Request latency |
| `app_requests_in_progress` | Gauge | app, method | Active requests |
| `app_info` | Gauge | app, version, type | Application metadata |
| `app_auth_attempts_total` | Counter | app, provider, status | Auth attempts |
| `app_suspicious_requests_total` | Counter | app, type | Suspicious requests |

## Manual Tracking

Track custom metrics:

```python
from monitoring.app_metrics import track_auth_attempt, track_suspicious_request

# Track authentication
track_auth_attempt("myapp", "google", success=True)
track_auth_attempt("myapp", "password", success=False)

# Track suspicious requests
track_suspicious_request("myapp", "sql_injection")
track_suspicious_request("myapp", "rate_limit")
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `MONITORING_ENABLED` | `true` | Enable/disable metrics collection |
| `SECURITY_MONITORING_ENABLED` | `true` | Enable/disable security monitoring |
| `PROMETHEUS_MULTIPROC_DIR` | - | Directory for multiprocess metrics (gunicorn) |

## Integration with baseweb

To make this part of baseweb foundation:

```python
# In baseweb/__init__.py
class Baseweb:
    def __init__(self, name, enable_monitoring=True, **kwargs):
        # ... existing setup ...

        if enable_monitoring:
            try:
                from monitoring.app_metrics import init_baseweb_metrics
                init_baseweb_metrics(self, app_name=name)
            except ImportError:
                pass  # Monitoring not available
```

## Prometheus Configuration

Add to your `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'myapp'
    static_configs:
      - targets: ['127.0.0.1:5000']
        labels:
          app: 'myapp'
          type: 'flask'  # or 'quart'
```

## Health Checks

The `/health` endpoint returns:

```json
{
  "status": "healthy",
  "app": "myapp",
  "version": "1.0.0"
}
```

## Requirements

- Python >= 3.8
- `prometheus_client >= 0.15.0`

## License

MIT