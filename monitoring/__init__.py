"""
Monitoring package for Flask/Quart applications.

This package provides Prometheus metrics integration for Flask and Quart
applications with minimal code changes.

Usage:
    from monitoring.app_metrics import init_flask_metrics, init_quart_metrics

    # Flask
    app = Flask(__name__)
    init_flask_metrics(app, app_name="myapp")

    # Quart
    app = Quart(__name__)
    await init_quart_metrics(app, app_name="myapp")
"""

__version__ = "0.1.0"
__all__ = [
    "init_flask_metrics",
    "init_quart_metrics",
    "init_baseweb_metrics",
    "track_auth_attempt",
    "track_suspicious_request",
]

from monitoring.app_metrics import (
    init_flask_metrics,
    init_quart_metrics,
    init_baseweb_metrics,
    track_auth_attempt,
    track_suspicious_request,
)