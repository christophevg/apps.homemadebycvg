"""
Application metrics module for Flask, Quart, and Baseweb applications.

This module provides unified Prometheus metrics for all hosted applications
with minimal integration code. Designed to be standalone and reusable
across multiple projects.

Features:
- Request counting, latency tracking, in-progress gauges
- Authentication attempt tracking for security monitoring
- Suspicious request detection and tracking
- Health check endpoints
- Graceful degradation when prometheus_client is not installed
- Environment variable toggle (MONITORING_ENABLED)

Usage:

Flask apps:
    from monitoring.app_metrics import init_flask_metrics
    app = Flask(__name__)
    init_flask_metrics(app, app_name="hello")

Quart apps:
    from monitoring.app_metrics import init_quart_metrics
    app = Quart(__name__)
    init_quart_metrics(app, app_name="frontpage")

Baseweb apps:
    from monitoring.app_metrics import init_baseweb_metrics
    server = Baseweb("myapp")
    init_baseweb_metrics(server, app_name="myapp")
"""

import logging
import os
import time
from functools import wraps
from typing import Optional, Callable

logger = logging.getLogger(__name__)

# Check if monitoring is enabled
MONITORING_ENABLED = os.environ.get("MONITORING_ENABLED", "true").lower() in ("true", "1", "yes")

# Lazy import prometheus_client
_prometheus_available = None
_REGISTRY = None
_CONTENT_TYPE_LATEST = None


def _get_prometheus():
    """Lazy load prometheus_client module."""
    global _prometheus_available, _REGISTRY, _CONTENT_TYPE_LATEST
    if _prometheus_available is None:
        try:
            from prometheus_client import (
                CONTENT_TYPE_LATEST,
                Counter,
                Gauge,
                Histogram,
                REGISTRY,
            )
            _prometheus_available = True
            _REGISTRY = REGISTRY
            _CONTENT_TYPE_LATEST = CONTENT_TYPE_LATEST
            return Counter, Gauge, Histogram
        except ImportError:
            _prometheus_available = False
            logger.warning(
                "prometheus_client not installed. Metrics collection disabled. "
                "Install with: pip install prometheus_client"
            )
            return None, None, None
    if _prometheus_available:
        from prometheus_client import Counter, Gauge, Histogram
        return Counter, Gauge, Histogram
    return None, None, None


# Metrics instances (created lazily)
_metrics = {}


def _get_or_create_metric(metric_type, name, documentation, labelnames=None):
    """Get or create a Prometheus metric instance."""
    if not MONITORING_ENABLED or not _prometheus_available:
        return None

    key = (metric_type.__name__, name) if metric_type else name
    if key in _metrics:
        return _metrics[key]

    Counter, Gauge, Histogram = _get_prometheus()
    if Counter is None:
        return None

    if metric_type == Counter:
        metric = Counter(name, documentation, labelnames or [], registry=_REGISTRY)
    elif metric_type == Gauge:
        metric = Gauge(name, documentation, labelnames or [], registry=_REGISTRY)
    elif metric_type == Histogram:
        metric = Histogram(name, documentation, labelnames or [], registry=_REGISTRY)
    else:
        return None

    _metrics[key] = metric
    return metric


def _ensure_metrics():
    """Ensure all metrics are created."""
    if not MONITORING_ENABLED:
        return False

    Counter, Gauge, Histogram = _get_prometheus()
    if Counter is None:
        return False

    # Request metrics
    _metrics["request_count"] = Counter(
        "app_request_count_total",
        "Total number of HTTP requests",
        ["app", "method", "endpoint", "http_status"],
        registry=_REGISTRY,
    )
    _metrics["request_latency"] = Histogram(
        "app_request_latency_seconds",
        "HTTP request latency in seconds",
        ["app", "method", "endpoint"],
        registry=_REGISTRY,
    )
    _metrics["requests_in_progress"] = Gauge(
        "app_requests_in_progress",
        "Number of HTTP requests currently being processed",
        ["app", "method"],
        registry=_REGISTRY,
    )

    # Application info
    _metrics["app_info"] = Gauge(
        "app_info",
        "Application information",
        ["app", "version", "type"],
        registry=_REGISTRY,
    )

    # Security metrics
    _metrics["auth_attempts"] = Counter(
        "app_auth_attempts_total",
        "Total authentication attempts",
        ["app", "provider", "status"],
        registry=_REGISTRY,
    )
    _metrics["suspicious_requests"] = Counter(
        "app_suspicious_requests_total",
        "Total suspicious requests detected",
        ["app", "type"],
        registry=_REGISTRY,
    )

    return True


def init_flask_metrics(app, app_name: str, app_version: str = "1.0.0"):
    """
    Initialize Prometheus metrics for a Flask application.

    Args:
        app: Flask application instance
        app_name: Unique application name for labeling
        app_version: Application version string

    Returns:
        The Flask app with metrics middleware installed

    Usage:
        app = Flask(__name__)
        init_flask_metrics(app, app_name="hello")
        # App now has /metrics and /health endpoints
    """
    if not MONITORING_ENABLED:
        logger.info(f"Monitoring disabled for {app_name}")
        return app

    if not _ensure_metrics():
        logger.warning(f"Could not initialize metrics for {app_name}")
        return app

    from flask import request, Response

    # Set app info
    _metrics["app_info"].labels(app=app_name, version=app_version, type="flask").set(1)

    @app.before_request
    def _before_request():
        request._prometheus_start_time = time.time()
        endpoint = request.endpoint or "unknown"
        _metrics["requests_in_progress"].labels(app=app_name, method=request.method).inc()

    @app.after_request
    def _after_request(response):
        if hasattr(request, "_prometheus_start_time"):
            latency = time.time() - request._prometheus_start_time
        else:
            latency = 0

        endpoint = request.endpoint or "unknown"

        _metrics["request_count"].labels(
            app=app_name,
            method=request.method,
            endpoint=endpoint,
            http_status=response.status_code,
        ).inc()

        _metrics["request_latency"].labels(
            app=app_name,
            method=request.method,
            endpoint=endpoint,
        ).observe(latency)

        _metrics["requests_in_progress"].labels(
            app=app_name,
            method=request.method,
        ).dec()

        return response

    @app.route("/metrics")
    def _metrics_endpoint():
        """Prometheus metrics endpoint."""
        from prometheus_client import generate_latest

        return Response(generate_latest(_REGISTRY), mimetype=_CONTENT_TYPE_LATEST)

    @app.route("/health")
    def _health_endpoint():
        """Health check endpoint."""
        return {"status": "healthy", "app": app_name, "version": app_version}, 200

    logger.info(f"Metrics initialized for Flask app: {app_name}")
    return app


def init_quart_metrics(app, app_name: str, app_version: str = "1.0.0"):
    """
    Initialize Prometheus metrics for a Quart application.

    Args:
        app: Quart application instance
        app_name: Unique application name for labeling
        app_version: Application version string

    Returns:
        The Quart app with metrics middleware installed

    Usage:
        app = Quart(__name__)
        init_quart_metrics(app, app_name="frontpage")
        # App now has /metrics and /health endpoints
    """
    if not MONITORING_ENABLED:
        logger.info(f"Monitoring disabled for {app_name}")
        return app

    if not _ensure_metrics():
        logger.warning(f"Could not initialize metrics for {app_name}")
        return app

    from quart import request, Response

    # Set app info
    _metrics["app_info"].labels(app=app_name, version=app_version, type="quart").set(1)

    @app.before_request
    async def _before_request():
        request._prometheus_start_time = time.time()
        endpoint = request.endpoint or "unknown"
        _metrics["requests_in_progress"].labels(app=app_name, method=request.method).inc()

    @app.after_request
    async def _after_request(response):
        if hasattr(request, "_prometheus_start_time"):
            latency = time.time() - request._prometheus_start_time
        else:
            latency = 0

        endpoint = request.endpoint or "unknown"

        _metrics["request_count"].labels(
            app=app_name,
            method=request.method,
            endpoint=endpoint,
            http_status=response.status_code,
        ).inc()

        _metrics["request_latency"].labels(
            app=app_name,
            method=request.method,
            endpoint=endpoint,
        ).observe(latency)

        _metrics["requests_in_progress"].labels(
            app=app_name,
            method=request.method,
        ).dec()

        return response

    @app.route("/metrics")
    async def _metrics_endpoint():
        """Prometheus metrics endpoint."""
        from prometheus_client import generate_latest

        return Response(generate_latest(_REGISTRY), mimetype=_CONTENT_TYPE_LATEST)

    @app.route("/health")
    async def _health_endpoint():
        """Health check endpoint."""
        return {"status": "healthy", "app": app_name, "version": app_version}, 200

    logger.info(f"Metrics initialized for Quart app: {app_name}")
    return app


def init_baseweb_metrics(server, app_name: str, app_version: str = "1.0.0"):
    """
    Initialize Prometheus metrics for a Baseweb application.

    Works with both Flask-based (v0.4.x) and Quart-based (v0.5.x) Baseweb.

    Args:
        server: Baseweb server instance
        app_name: Unique application name for labeling
        app_version: Application version string

    Usage:
        server = Baseweb("myapp")
        init_baseweb_metrics(server, app_name="myapp")
    """
    if not MONITORING_ENABLED:
        logger.info(f"Monitoring disabled for {app_name}")
        return

    # Detect Baseweb variant
    is_quart = hasattr(server, "_asgi_app") or "quart" in str(type(getattr(server, "app", None))).lower()

    # Get the underlying Flask/Quart app
    if hasattr(server, "app"):
        app = server.app
    else:
        logger.warning(f"Could not find underlying app in Baseweb server for {app_name}")
        return

    if is_quart:
        init_quart_metrics(app, app_name, app_version)
        logger.info(f"Metrics initialized for Baseweb/Quart app: {app_name}")
    else:
        init_flask_metrics(app, app_name, app_version)
        logger.info(f"Metrics initialized for Baseweb/Flask app: {app_name}")


def track_auth_attempt(app_name: str, provider: str, success: bool):
    """
    Track an authentication attempt.

    Args:
        app_name: Application name
        provider: Auth provider (e.g., "google", "github", "password")
        success: Whether authentication succeeded

    Usage:
        track_auth_attempt("myapp", "google", success=True)
    """
    if not MONITORING_ENABLED or "auth_attempts" not in _metrics:
        return

    status = "success" if success else "failure"
    _metrics["auth_attempts"].labels(app=app_name, provider=provider, status=status).inc()


def track_suspicious_request(app_name: str, request_type: str):
    """
    Track a suspicious request.

    Args:
        app_name: Application name
        request_type: Type of suspicious activity
            (e.g., "path_traversal", "sql_injection", "xss", "rate_limit")

    Usage:
        track_suspicious_request("myapp", "sql_injection")
    """
    if not MONITORING_ENABLED or "suspicious_requests" not in _metrics:
        return

    _metrics["suspicious_requests"].labels(app=app_name, type=request_type).inc()