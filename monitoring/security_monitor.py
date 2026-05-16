"""
Security monitoring module for detecting suspicious requests.

This module provides passive security monitoring that detects and logs
potentially malicious requests without blocking them. Use in conjunction
with rate limiters and WAFs for active protection.

Features:
- Pattern-based detection (SQL injection, XSS, path traversal, etc.)
- Rate limiting tracking
- Integration with app_metrics for Prometheus metrics
- Flask and Quart middleware support

Usage:

Flask:
    from monitoring.security_monitor import create_flask_security_middleware
    monitor = create_flask_security_middleware(app, app_name="myapp")

Quart:
    from monitoring.security_monitor import create_quart_security_middleware
    monitor = create_quart_security_middleware(app, app_name="myapp")
"""

import logging
import os
import re
import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Dict, List, Optional

logger = logging.getLogger(__name__)

# Environment variable to enable/disable security monitoring
SECURITY_MONITORING_ENABLED = os.environ.get("SECURITY_MONITORING_ENABLED", "true").lower() in (
    "true",
    "1",
    "yes",
)

# Suspicious patterns for detection
SUSPICIOUS_PATTERNS = {
    "path_traversal": [
        re.compile(r"\.\./", re.IGNORECASE),
        re.compile(r"\.\.\\", re.IGNORECASE),
        re.compile(r"%2e%2e", re.IGNORECASE),
        re.compile(r"%252e%252e", re.IGNORECASE),  # Double-encoded
        re.compile(r"\.\.%2f", re.IGNORECASE),
        re.compile(r"\.\.%5c", re.IGNORECASE),
    ],
    "sql_injection": [
        re.compile(r"(\%27)|(\')|(\-\-)|(\%23)|(#)", re.IGNORECASE),
        re.compile(
            r"((\%3D)|(=))[^\n]*((\%27)|(\')|(\-\-)|(\%3B)|(;))", re.IGNORECASE
        ),
        re.compile(
            r"\w*((\%27)|(\'))((\%6F)|o|(\%4F))((\%72)|r|(\%52))", re.IGNORECASE
        ),
        re.compile(r"union.*select", re.IGNORECASE),
        re.compile(r"exec(\s|\+)+", re.IGNORECASE),
        re.compile(r"concat\s*\(", re.IGNORECASE),
    ],
    "xss": [
        re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE),
        re.compile(r"javascript:", re.IGNORECASE),
        re.compile(r"on\w+\s*=", re.IGNORECASE),
        re.compile(r"<iframe", re.IGNORECASE),
        re.compile(r"<object", re.IGNORECASE),
        re.compile(r"<embed", re.IGNORECASE),
        re.compile(r"expression\s*\(", re.IGNORECASE),
    ],
    "command_injection": [
        re.compile(r";\s*(ls|cat|rm|wget|curl|bash|sh|nc|netcat|python|perl|ruby)\s", re.IGNORECASE),
        re.compile(r"\|\s*(ls|cat|rm|wget|curl|bash|sh|nc|netcat|python|perl|ruby)\s", re.IGNORECASE),
        re.compile(r"`[^`]+`", re.IGNORECASE),
        re.compile(r"\$\([^)]+\)", re.IGNORECASE),
        re.compile(r"\$\{[^}]+\}", re.IGNORECASE),
    ],
    "ssrf": [
        re.compile(r"https?://(localhost|127\.0\.0\.1|0\.0\.0\.0|::1)", re.IGNORECASE),
        re.compile(r"https?://(10|172|192\.168)\.\d+\.\d+", re.IGNORECASE),
        re.compile(r"file://", re.IGNORECASE),
        re.compile(r"gopher://", re.IGNORECASE),
    ],
    "ldap_injection": [
        re.compile(r"\*\)", re.IGNORECASE),
        re.compile(r"\(\|", re.IGNORECASE),
        re.compile(r"\(\&", re.IGNORECASE),
    ],
}


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""

    requests_per_minute: int = 60
    burst_size: int = 10
    per_ip: bool = True


class SecurityMonitor:
    """
    Passive security monitor for detecting suspicious requests.

    This monitor logs and tracks suspicious activity without blocking.
    Use with rate limiters and WAFs for active protection.
    """

    def __init__(
        self,
        app_name: str,
        rate_limit_config: Optional[RateLimitConfig] = None,
        custom_patterns: Optional[Dict[str, List[re.Pattern]]] = None,
    ):
        """
        Initialize security monitor.

        Args:
            app_name: Application name for logging/metrics
            rate_limit_config: Optional rate limiting configuration
            custom_patterns: Optional custom patterns to detect
        """
        self.app_name = app_name
        self.rate_limit_config = rate_limit_config or RateLimitConfig()
        self._request_counts: Dict[str, List[float]] = defaultdict(list)
        self._patterns = SUSPICIOUS_PATTERNS.copy()

        if custom_patterns:
            self._patterns.update(custom_patterns)

        logger.info(f"Security monitor initialized for {app_name}")

    def inspect_request(
        self,
        path: str,
        query_string: str = "",
        headers: Optional[Dict[str, str]] = None,
        ip_address: str = "unknown",
        body: Optional[str] = None,
    ) -> List[str]:
        """
        Inspect a request for suspicious patterns.

        Args:
            path: Request path
            query_string: Query string (URL-encoded)
            headers: Request headers dict
            ip_address: Client IP address
            body: Request body (optional)

        Returns:
            List of detected suspicious pattern types
        """
        detected = []

        # Build full request string for inspection
        full_request = path
        if query_string:
            full_request = f"{full_request}?{query_string}"
        if body:
            full_request = f"{full_request} {body}"

        # Add headers to inspection (values only, not header names)
        if headers:
            header_values = " ".join(str(v) for v in headers.values() if v)
            full_request = f"{full_request} {header_values}"

        # Check for suspicious patterns
        for pattern_type, patterns in self._patterns.items():
            for pattern in patterns:
                if pattern.search(full_request):
                    detected.append(pattern_type)
                    logger.warning(
                        f"Suspicious request detected: app={self.app_name} "
                        f"ip={ip_address} path={path} type={pattern_type}"
                    )
                    break  # Only report each type once per request

        # Check rate limiting
        if self._is_rate_limited(ip_address):
            detected.append("rate_limit")
            logger.warning(
                f"Rate limit exceeded: app={self.app_name} "
                f"ip={ip_address} requests/min={len(self._request_counts[ip_address])}"
            )

        return detected

    def _is_rate_limited(self, ip_address: str) -> bool:
        """Check if IP address is rate limited."""
        now = time.time()
        minute_ago = now - 60

        # Clean old requests
        self._request_counts[ip_address] = [
            t for t in self._request_counts[ip_address] if t > minute_ago
        ]

        # Check current count
        return len(self._request_counts[ip_address]) > self.rate_limit_config.requests_per_minute

    def record_request(self, ip_address: str):
        """Record a request for rate limiting tracking."""
        self._request_counts[ip_address].append(time.time())

    def get_stats(self) -> Dict:
        """Get current monitoring statistics."""
        now = time.time()
        minute_ago = now - 60

        # Clean old requests
        for ip in list(self._request_counts.keys()):
            self._request_counts[ip] = [t for t in self._request_counts[ip] if t > minute_ago]
            if not self._request_counts[ip]:
                del self._request_counts[ip]

        return {
            "active_ips": len(self._request_counts),
            "total_requests_tracked": sum(len(v) for v in self._request_counts.values()),
        }


def create_flask_security_middleware(
    app, app_name: str, rate_limit_config: Optional[RateLimitConfig] = None
) -> SecurityMonitor:
    """
    Create security monitoring middleware for Flask.

    Args:
        app: Flask application instance
        app_name: Application name
        rate_limit_config: Optional rate limiting configuration

    Returns:
        SecurityMonitor instance for manual tracking if needed

    Usage:
        from monitoring.security_monitor import create_flask_security_middleware
        app = Flask(__name__)
        monitor = create_flask_security_middleware(app, app_name="myapp")
    """
    if not SECURITY_MONITORING_ENABLED:
        logger.info(f"Security monitoring disabled for {app_name}")
        return None

    monitor = SecurityMonitor(app_name, rate_limit_config)

    @app.before_request
    def _security_check():
        from flask import request

        detected = monitor.inspect_request(
            path=request.path,
            query_string=request.query_string.decode("utf-8", errors="ignore"),
            headers=dict(request.headers),
            ip_address=request.remote_addr,
        )

        if detected:
            # Track in metrics if available
            try:
                from monitoring.app_metrics import track_suspicious_request

                for pattern_type in detected:
                    track_suspicious_request(app_name, pattern_type)
            except ImportError:
                pass

        monitor.record_request(request.remote_addr)

    return monitor


def create_quart_security_middleware(
    app, app_name: str, rate_limit_config: Optional[RateLimitConfig] = None
) -> SecurityMonitor:
    """
    Create security monitoring middleware for Quart.

    Args:
        app: Quart application instance
        app_name: Application name
        rate_limit_config: Optional rate limiting configuration

    Returns:
        SecurityMonitor instance for manual tracking if needed

    Usage:
        from monitoring.security_monitor import create_quart_security_middleware
        app = Quart(__name__)
        monitor = create_quart_security_middleware(app, app_name="myapp")
    """
    if not SECURITY_MONITORING_ENABLED:
        logger.info(f"Security monitoring disabled for {app_name}")
        return None

    monitor = SecurityMonitor(app_name, rate_limit_config)

    @app.before_request
    async def _security_check():
        from quart import request

        detected = monitor.inspect_request(
            path=request.path,
            query_string=request.query_string.decode("utf-8", errors="ignore"),
            headers=dict(request.headers),
            ip_address=request.remote_addr,
        )

        if detected:
            # Track in metrics if available
            try:
                from monitoring.app_metrics import track_suspicious_request

                for pattern_type in detected:
                    track_suspicious_request(app_name, pattern_type)
            except ImportError:
                pass

        monitor.record_request(request.remote_addr)

    return monitor


def create_baseweb_security_middleware(
    server, app_name: str, rate_limit_config: Optional[RateLimitConfig] = None
) -> Optional[SecurityMonitor]:
    """
    Create security monitoring middleware for Baseweb applications.

    Works with both Flask-based and Quart-based Baseweb variants.

    Args:
        server: Baseweb server instance
        app_name: Application name
        rate_limit_config: Optional rate limiting configuration

    Returns:
        SecurityMonitor instance for manual tracking if needed
    """
    # Detect Baseweb variant
    is_quart = hasattr(server, "_asgi_app") or "quart" in str(
        type(getattr(server, "app", None))
    ).lower()

    # Get underlying app
    if hasattr(server, "app"):
        app = server.app
    else:
        logger.warning(f"Could not find underlying app in Baseweb server for {app_name}")
        return None

    if is_quart:
        return create_quart_security_middleware(app, app_name, rate_limit_config)
    else:
        return create_flask_security_middleware(app, app_name, rate_limit_config)