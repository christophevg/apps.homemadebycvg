#!/bin/bash
# Ensure nginx is not running before supervisord starts it
pkill nginx 2>/dev/null || true
sleep 1

# Start supervisord
exec supervisord -c /etc/supervisor/supervisord.conf
