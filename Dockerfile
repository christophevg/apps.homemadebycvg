# Single image containing all Flask/Quart apps + Nginx reverse proxy
# Built with Podman, runs with Docker
#
# This image bundles all apps from the apps.homemadebycvg repository
# into a single container with an Nginx reverse proxy.

FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/log/supervisor \
    && mkdir -p /var/log/nginx \
    && rm -f /etc/nginx/sites-enabled/default \
    && sed -i 's/^daemon .*;/daemon off;/' /etc/nginx/nginx.conf

# Set working directory
WORKDIR /app

# Copy all app source code first (needed for their requirements files)
COPY hello/ /app/apps/hello/
COPY parking/ /app/apps/parking/
COPY nationofpositivity/ /app/apps/nationofpositivity/
COPY homemadebycvg/ /app/apps/homemadebycvg/
COPY getijden/ /app/apps/getijden/
COPY letmelearn/ /app/apps/letmelearn/
COPY baseweb-demo/ /app/apps/baseweb-demo/
COPY howifeel/ /app/apps/howifeel/
COPY oatk/ /app/apps/oatk/

# Install common dependencies
# Pin gunicorn version for eventlet compatibility
RUN pip install --no-cache-dir gunicorn==23.0.0 eventlet

# Install each app's dependencies from their requirements files
# Prefer requirements.base.txt (clean deps) over requirements.txt (frozen with all transitive deps)
RUN set -e; \
    for app in hello parking nationofpositivity homemadebycvg getijden letmelearn baseweb-demo howifeel oatk; do \
        echo "Installing dependencies for $app..."; \
        if [ -f /app/apps/$app/requirements.base.txt ]; then \
            pip install --no-cache-dir -r /app/apps/$app/requirements.base.txt; \
        elif [ -f /app/apps/$app/requirements.txt ]; then \
            pip install --no-cache-dir -r /app/apps/$app/requirements.txt; \
        else \
            echo "No requirements found for $app"; \
        fi; \
    done

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Copy entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Copy strip-env wrapper script
COPY strip-env.sh /strip-env.sh
RUN chmod +x /strip-env.sh

# Create necessary directories
RUN mkdir -p /var/log/nginx /var/log/supervisor /tmp

# Expose port 80 for nginx
EXPOSE 80

# Use entrypoint script to ensure clean startup
CMD ["/entrypoint.sh"]
