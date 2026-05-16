# Single image containing all Flask/Quart apps + Nginx reverse proxy
# Built with Podman, runs with Docker
#
# This image bundles all apps from the apps.homemadebycvg repository
# into a single container with an Nginx reverse proxy and monitoring stack.

FROM python:3.11-slim

# Install system dependencies + monitoring tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    supervisor \
    git \
    ca-certificates \
    curl \
    apache2-utils \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/log/supervisor \
    && mkdir -p /var/log/nginx \
    && rm -f /etc/nginx/sites-enabled/default \
    && sed -i 's/^daemon .*;/daemon off;/' /etc/nginx/nginx.conf

# === MONITORING STACK INSTALLATION ===

# Create directories for monitoring configs and data
RUN mkdir -p /opt/monitoring/prometheus/data \
    && mkdir -p /opt/monitoring/grafana/data \
    && mkdir -p /opt/monitoring/grafana/plugins \
    && mkdir -p /opt/monitoring/loki/data \
    && mkdir -p /opt/monitoring/config \
    && mkdir -p /opt/monitoring/bin \
    && mkdir -p /var/log/promtail \
    && mkdir -p /var/log/apps

# Download and install node_exporter (system metrics)
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then NODE_ARCH="arm64"; else NODE_ARCH="amd64"; fi && \
    curl -sSL "https://github.com/prometheus/node_exporter/releases/download/v1.8.0/node_exporter-1.8.0.linux-${NODE_ARCH}.tar.gz" | \
    tar xz -C /tmp/ && \
    mv /tmp/node_exporter-*/node_exporter /opt/monitoring/bin/ && \
    rm -rf /tmp/node_exporter-*

# Download and install nginx-prometheus-exporter
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then NGINX_ARCH="arm64"; else NGINX_ARCH="amd64"; fi && \
    curl -sSL "https://github.com/nginx/nginx-prometheus-exporter/releases/download/v1.1.0/nginx-prometheus-exporter_1.1.0_linux_${NGINX_ARCH}.tar.gz" | \
    tar xz -C /tmp/ && \
    mv /tmp/nginx-prometheus-exporter /opt/monitoring/bin/ && \
    rm -rf /tmp/nginx-prometheus-exporter*

# Download and install Prometheus
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then PROM_ARCH="arm64"; else PROM_ARCH="amd64"; fi && \
    curl -sSL "https://github.com/prometheus/prometheus/releases/download/v2.51.0/prometheus-2.51.0.linux-${PROM_ARCH}.tar.gz" | \
    tar xz -C /tmp/ && \
    mv /tmp/prometheus-*/prometheus /opt/monitoring/bin/ && \
    mv /tmp/prometheus-*/promtool /opt/monitoring/bin/ && \
    rm -rf /tmp/prometheus-*

# Download and install Grafana
RUN ARCH=$(dpkg --print-architecture) && \
    curl -sSL "https://dl.grafana.com/oss/release/grafana_11.0.0_${ARCH}.deb" -o /tmp/grafana.deb && \
    apt-get update && apt-get install -y libfontconfig1 musl && \
    dpkg -i /tmp/grafana.deb && \
    rm /tmp/grafana.deb && \
    apt-get clean

# Download and install Loki
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then LOKI_ARCH="arm64"; else LOKI_ARCH="amd64"; fi && \
    curl -sSL "https://github.com/grafana/loki/releases/download/v2.9.6/loki-linux-${LOKI_ARCH}.zip" -o /tmp/loki.zip && \
    apt-get update && apt-get install -y unzip && \
    unzip /tmp/loki.zip -d /tmp/ && \
    mv /tmp/loki-linux-${LOKI_ARCH} /opt/monitoring/bin/loki && \
    rm /tmp/loki.zip && \
    apt-get remove -y unzip && apt-get autoremove -y

# Download and install Promtail
RUN ARCH=$(dpkg --print-architecture) && \
    if [ "$ARCH" = "arm64" ]; then LOKI_ARCH="arm64"; else LOKI_ARCH="amd64"; fi && \
    curl -sSL "https://github.com/grafana/loki/releases/download/v2.9.6/promtail-linux-${LOKI_ARCH}.zip" -o /tmp/promtail.zip && \
    apt-get update && apt-get install -y unzip && \
    unzip /tmp/promtail.zip -d /tmp/ && \
    mv /tmp/promtail-linux-${LOKI_ARCH} /opt/monitoring/bin/promtail && \
    rm /tmp/promtail.zip && \
    apt-get remove -y unzip && apt-get autoremove -y

# Install prometheus_client for application metrics
RUN pip install --root-user-action=ignore --no-cache-dir prometheus_client

# Copy monitoring configurations
COPY monitoring/prometheus.yml /opt/monitoring/config/prometheus.yml
COPY monitoring/loki-config.yml /opt/monitoring/config/loki-config.yml
COPY monitoring/promtail-config.yml /opt/monitoring/config/promtail-config.yml
COPY monitoring/grafana.ini /opt/monitoring/config/grafana.ini
COPY monitoring/grafana/provisioning /opt/monitoring/config/grafana/provisioning
COPY monitoring/grafana/dashboards /opt/monitoring/grafana/dashboards

# Copy monitoring package for apps
COPY monitoring/ /app/monitoring/

# Set working directory
WORKDIR /app

# Copy all app source code first (needed for their requirements files)
COPY frontpage/ /app/apps/frontpage
COPY hello/ /app/apps/hello/
COPY parking/ /app/apps/parking/
COPY nationofpositivity/ /app/apps/nationofpositivity/
COPY homemadebycvg/ /app/apps/homemadebycvg/
COPY getijden/ /app/apps/getijden/
COPY letmelearn/ /app/apps/letmelearn/
COPY baseweb-demo/ /app/apps/baseweb-demo/
COPY howifeel/ /app/apps/howifeel/
COPY oatk/ /app/apps/oatk/
COPY roomz/ /app/apps/roomz/

# Copy apps.yaml
COPY apps.yaml /app/apps/apps.yaml

# Install common dependencies

# Upgrade pip
RUN pip install --root-user-action=ignore -U pip

# Pin gunicorn version for eventlet compatibility
RUN pip install --root-user-action=ignore --no-cache-dir gunicorn==25.3.0 eventlet

# Install uv
RUN pip install --root-user-action=ignore uv

# Install each app's dependencies from their requirements files
# Prefer requirements.base.txt (clean deps) over requirements.txt (frozen with all transitive deps)
RUN set -e; \
  for app in hello parking nationofpositivity homemadebycvg getijden letmelearn howifeel oatk; do \
    echo "Installing dependencies for $app..."; \
    if [ -f /app/apps/$app/requirements.base.txt ]; then \
        pip install --root-user-action=ignore --no-cache-dir -r /app/apps/$app/requirements.base.txt; \
    elif [ -f /app/apps/$app/requirements.txt ]; then \
        pip install --root-user-action=ignore --no-cache-dir -r /app/apps/$app/requirements.txt; \
    else \
        echo "No requirements found for $app"; \
    fi; \
  done

# Limit baseweb and oatk version
RUN pip install --root-user-action=ignore -U "baseweb<0.5.0"
RUN pip install --root-user-action=ignore -U "oatk<0.2.0"



# Sync uv-based apps
RUN set -e; \
  for app in frontpage baseweb-demo roomz; do \
    if [ -f /app/apps/$app/pyproject.toml ]; then \
      uv --project /app/apps/$app sync; \
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
