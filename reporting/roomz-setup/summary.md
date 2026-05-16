# Roomz Hosting Setup - Summary

**Date**: 2025-05-15
**Task**: R1-001 - Setup Roomz Hosting Infrastructure
**Status**: Complete

## Implementation

Added roomz chat application to the apps.homemadebycvg.com container infrastructure.

### Files Modified

| File | Change |
|------|--------|
| `supervisord.conf` | Added roomz program entry (port 5011) |
| `nginx.conf` | Added upstream + server block with WebSocket support |
| `apps.yaml` | Added roomz entry for frontpage |
| `Dockerfile` | Added `uv pip install roomz` to install from PyPI |
| `.env.local` | Added ROOMZ_* environment variables |

### Configuration Details

**Port**: 5011 (next available after oatk on 5010)

**Entry Point**: `roomz.server:asgi_app` (from installed PyPI package)

**WebSocket Support**: Enabled in nginx with 24-hour timeouts for Socket.IO

### Environment Variables Required

| Variable | Status | Notes |
|----------|--------|-------|
| `ROOMZ_JWT_SECRET_KEY` | Placeholder | Generate with: `python -c "import secrets; print(secrets.token_urlsafe(32))"` |
| `ROOMZ_ALLOWED_EMAILS` | Placeholder | Comma-separated list of allowed email addresses |
| `ROOMZ_EMAIL_SENDER` | `console` | Use `resend` for production |
| `ROOMZ_JWT_EXPIRY_DAYS` | `30` | Default value |
| `ROOMZ_RESEND_API_KEY` | Placeholder | Required if EMAIL_SENDER=resend |
| `ROOMZ_EMAIL_FROM` | `noreply@homemadebycvg.com` | Default sender |

## Package Restructure (2025-05-15)

The roomz package was restructured to avoid module name collisions:
- Old structure: `app/` (generic top-level module)
- New structure: `src/roomz/server/` (namespaced module)
- Entry point changed from `app:asgi_app` to `roomz.server:asgi_app`

## Next Steps

1. **Generate JWT Secret Key**:
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Configure Allowed Emails**:
   Edit `.env.local` and update `ROOMZ_ALLOWED_EMAILS` with actual email addresses

3. **Add Image for Frontpage**:
   Add `roomz.png` to `frontpage/hosted/images/`

4. **Production Email** (optional):
   - Set `ROOMZ_EMAIL_SENDER=resend`
   - Add `ROOMZ_RESEND_API_KEY`

5. **Deploy**:
   ```bash
   # Build and deploy container
   ```

## Requirements Satisfied

- ✅ R1: Application folder structure (runs from installed package)
- ✅ R2: Supervisord configuration (port 5011, uvicorn worker)
- ✅ R3: Nginx configuration (WebSocket support)
- ✅ R4: App registry (apps.yaml entry)
- ✅ R5: Environment configuration (ROOMZ_* variables)