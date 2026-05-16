# Functional Analysis: Roomz App Hosting

## Overview

Add the `roomz` chat application as a hosted service in the apps.homemadebycvg.com container infrastructure.

## Context

- **Source**: roomz package published on PyPI
- **Technology**: Quart + SocketIO (async Python with WebSocket support)
- **Hostname**: roomz.app.homemadebycvg.com
- **Port**: 5011 (next available after current apps using 5000-5010)

## Requirements

### R1: Application Folder Structure
Create a minimal `roomz/` folder that runs the roomz app from the installed PyPI package.

### R2: Supervisord Configuration
Add supervisor entry to run roomz using gunicorn with uvicorn worker (async/WebSocket support).

### R3: Nginx Configuration
Add nginx upstream and server block with WebSocket support for `roomz.app.homemadebycvg.com`.

### R4: App Registry
Add roomz entry to `apps.yaml` for frontpage display.

### R5: Environment Configuration
Add roomz environment variables to `.env.local`:
- `ROOMZ_JWT_SECRET_KEY`: JWT signing key (min 32 chars)
- `ROOMZ_ALLOWED_EMAILS`: Comma-separated allowed email addresses
- `ROOMZ_EMAIL_SENDER`: Email mode (console for dev, resend for production)

## Technical Constraints

1. Roomz uses Quart (async Flask) with SocketIO - requires `uvicorn.workers.UvicornWorker`
2. WebSocket support needed in nginx (same pattern as baseweb-demo)
3. Environment variables must be prefixed with `ROOMZ_` for strip-env.sh compatibility
4. Port allocation: 5011 (next available)

## Implementation Notes

The roomz package exposes entry point `roomz = "app:asgi_app"` in pyproject.toml. The minimal setup should:
- Import and run the app from the installed package
- Configure for container environment (host 127.0.0.1, port 5011)