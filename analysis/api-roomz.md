# Roomz Hosting Setup Analysis

**Date**: 2025-05-15
**Context**: Design hosting configuration for roomz (WebSocket-based chat app) on apps.homemadebycvg.com container infrastructure
**Related**: roomz PyPI package, baseweb-demo pattern for Quart + SocketIO apps

## Summary

This document provides the complete hosting configuration for roomz, a real-time chat application using Quart + SocketIO (async Python). The setup follows the established patterns from baseweb-demo, with WebSocket support for real-time messaging.

## 1. Recommended Folder Structure

The roomz app runs from an installed PyPI package, so we need a minimal folder structure:

```
roomz/
├── .env.local          # Environment variables (prefixed with ROOMZ_)
└── pyproject.toml      # Optional: defines dependency on roomz package
```

**Why minimal?** Unlike baseweb-demo which has local source code, roomz is published to PyPI. The container only needs:
1. Install the `roomz` package from PyPI
2. Configure environment variables
3. Run the ASGI app entry point

**Alternative (simpler)**: No roomz folder needed at all - just add configuration to the existing container files. The package is installed in the container's venv and configured via environment variables.

## 2. Supervisord Configuration

Add to `supervisord.conf` (after oatk entry on line 134):

```ini
[program:roomz]
command=/strip-env.sh ROOMZ_ -- uv --project /app run gunicorn -k uvicorn.workers.UvicornWorker -b 127.0.0.1:5011 roomz:asgi_app
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=PYTHONUNBUFFERED="1"
priority=10
```

**Key points:**
- Port: 5011 (next available after oatk on 5010)
- Uses `uv` to run gunicorn with UvicornWorker (async support)
- Entry point: `roomz:asgi_app` (package module, not local file)
- `/strip-env.sh ROOMZ_` removes prefix from environment variables
- No `--project` flag needed since running from installed package

**Note**: The roomz package exports `asgi_app` from `app/__init__.py` via the `roomz` console script entry point. The command runs gunicorn with the ASGI app directly.

## 3. Nginx Configuration

### 3.1 Upstream Definition

Add to the upstream section (after line 46 in nginx.conf):

```nginx
upstream roomz { server 127.0.0.1:5011; }
```

### 3.2 Server Block (with WebSocket support)

Add after the oatk server block (around line 194):

```nginx
# roomz - roomz.app.homemadebycvg.com
server {
    listen 10000;
    server_name roomz.app.homemadebycvg.com roomz.app.homemadebycvg.local;
    access_log /dev/stdout main;
    location / {
        proxy_pass http://roomz;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    location /socket.io {
        proxy_pass http://roomz;
        proxy_set_header Host $http_host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # WebSocket upgrade
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;

        # Timeouts (long-lived WebSocket connections)
        proxy_connect_timeout 60;
        proxy_read_timeout 86400;
        proxy_send_timeout 86400;

        # Buffering (disable for real-time)
        proxy_buffering off;
        proxy_cache off;
    }
}
```

**WebSocket-specific settings:**
- `/socket.io` location handles Socket.IO upgrade
- `Upgrade` and `Connection` headers enable WebSocket protocol
- Long timeouts (86400s = 24h) for persistent connections
- Buffering disabled for real-time message delivery

## 4. Apps.yaml Entry

Add to `apps.yaml` (after oatk-demo entry):

```yaml
roomz:
  title: Roomz
  hostname: roomz.app.homemadebycvg.com
  local: roomz.app.homemadebycvg.local:8080
  github: christophevg/roomz
  docs: https://github.com/christophevg/roomz#readme
  image: /images/roomz.png
  description: |
    Real-time chatroom web service with magic link authentication.
    Secure, invite-only chat using JWT sessions and WebSocket messaging.
    Built with Quart + SocketIO for async Python.
```

**Note**: An image file `roomz.png` will need to be added to `frontpage/hosted/images/` for the frontpage to display correctly.

## 5. Environment Variables

Add to `.env.local`:

```bash
# Roomz Configuration
ROOMZ_JWT_SECRET_KEY=<generate-with-python-secrets-token_urlsafe-32>
ROOMZ_JWT_EXPIRY_DAYS=30
ROOMZ_ALLOWED_EMAILS=user1@example.com,user2@example.com,user3@example.com
ROOMZ_EMAIL_SENDER=resend
ROOMZ_RESEND_API_KEY=<resend-api-key>
ROOMZ_EMAIL_FROM=noreply@homemadebycvg.com
```

### Required Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ROOMZ_JWT_SECRET_KEY` | **Yes** | Secret key for JWT signing (min 32 chars). Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ROOMZ_ALLOWED_EMAILS` | **Yes** | Comma-separated list of allowed email addresses for authentication |
| `ROOMZ_EMAIL_SENDER` | No | Email provider: `console` (dev) or `resend` (prod). Default: `console` |
| `ROOMZ_RESEND_API_KEY` | Conditional | Required if `EMAIL_SENDER=resend` |
| `ROOMZ_EMAIL_FROM` | No | From address for emails |
| `ROOMZ_JWT_EXPIRY_DAYS` | No | JWT expiry in days. Default: `30` |

### Security Considerations

1. **JWT_SECRET_KEY**: Must be at least 32 characters (256 bits). Never commit to version control.

2. **ALLOWED_EMAILS**: This acts as an allowlist for authentication. Only emails in this list can log in. Consider:
   - Store in a more secure location for production (secrets manager)
   - Use environment-specific values (dev/staging/prod)

3. **HTTPS Required**: The app sets `secure=False` on cookies for localhost development. In production with nginx, ensure:
   - X-Forwarded-Proto is set correctly (already in nginx config)
   - Consider adding `X-Forwarded-SSL: on` if needed

4. **Rate Limiting**: Built-in rate limiting for magic link requests (5 per email per hour)

5. **Connection Limits**: Built-in MAX_CLIENTS=1000 limit for WebSocket connections

## 6. Container Dockerfile Updates

The Dockerfile needs to install the roomz package. Add to the pip install section:

```dockerfile
# Install roomz from PyPI
RUN uv pip install roomz
```

Or if using a pyproject.toml in a roomz folder:

```dockerfile
COPY roomz /app/apps/roomz
RUN uv pip install /app/apps/roomz
```

## 7. Summary of Changes

| File | Action |
|------|--------|
| `supervisord.conf` | Add roomz program entry (port 5011) |
| `nginx.conf` | Add upstream + server block with WebSocket support |
| `apps.yaml` | Add roomz app entry for frontpage |
| `.env.local` | Add ROOMZ_* environment variables |
| `Dockerfile` | Add `uv pip install roomz` |
| `frontpage/hosted/images/` | Add `roomz.png` image |

## 8. Testing Checklist

After deployment, verify:

- [ ] App responds at `https://roomz.app.homemadebycvg.com`
- [ ] WebSocket connection works (Socket.IO handshake at `/socket.io`)
- [ ] Magic link authentication flow completes
- [ ] JWT cookie is set correctly
- [ ] Real-time messages broadcast to connected clients
- [ ] Rate limiting works (5 magic link requests per hour per email)
- [ ] Only ALLOWED_EMAILS can authenticate

## 9. Architecture Notes

### App Entry Point

The roomz package exposes `asgi_app` which wraps the Quart + SocketIO server:

```python
# From roomz/app/__init__.py
from baseweb import Baseweb
server = Baseweb("roomz", settings={"main_template": "minimal.html"})
# ... routes and socket handlers ...
asgi_app = server._asgi_app
```

### WebSocket Flow

1. Client connects to `/socket.io`
2. nginx proxies to gunicorn/Uvicorn
3. Socket.IO upgrade to WebSocket
4. Server validates JWT from cookie
5. Connection registered in `connected_clients`
6. Messages broadcast via `server.socketio.emit()`

### Authentication Flow

1. POST `/auth/request-magic-link` with email
2. Rate limit check (5 req/hour per email)
3. Email validation against ALLOWED_EMAILS
4. Magic link sent via email (or logged to console in dev)
5. GET `/auth/verify?token=...` validates token
6. JWT set in httpOnly cookie
7. WebSocket connection uses JWT for authentication