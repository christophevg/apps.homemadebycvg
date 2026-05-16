-include ~/.claude/Makefile

.PHONY: build run stop logs clean shell frontpage

IMAGE     = apps-homemadebycvg:container
CONTAINER = apps-homemadebycvg
PORT      = 8080:10000

# Build runtime: prefer podman, fallback to docker
ifeq ($(BUILD_RUNTIME),)
    ifneq ($(shell which podman 2>/dev/null),)
        BUILD_RUNTIME = podman
    else ifneq ($(shell which docker 2>/dev/null),)
        BUILD_RUNTIME = docker
    else
        $(error No container runtime found. Install Docker or Podman.)
    endif
endif

# Runtime for running containers: use BUILD_RUNTIME (same for build and run)
RUNTIME = $(BUILD_RUNTIME)

# Build command
BUILD_CMD = $(BUILD_RUNTIME) build -t $(IMAGE) .

# Run command
# Loads environment variables from .env.local if it exists
ENV_FILE = .env.local
ifneq ($(wildcard $(ENV_FILE)),)
    RUN_CMD = $(RUNTIME) run -d --name $(CONTAINER) --env-file $(ENV_FILE) -p $(PORT) $(IMAGE)
else
    RUN_CMD = $(RUNTIME) run -d --name $(CONTAINER) -p $(PORT) $(IMAGE)
endif

build:
	@echo "Building container image with $(BUILD_RUNTIME)..."
	$(BUILD_CMD)
	@echo "Image built: $(IMAGE)"

# Run the container
run: stop
	@echo "Starting container with $(RUNTIME)..."
	$(RUN_CMD)
	@echo ""
	@echo "✅ Container started!"

# Stop and remove the container
stop:
	@echo "Stopping container..."
	-$(RUNTIME) stop $(CONTAINER) 2>/dev/null || true
	-$(RUNTIME) rm $(CONTAINER) 2>/dev/null || true
	@echo "Container stopped."

# View logs
logs:
	$(RUNTIME) logs -f $(CONTAINER)

access-logs:
	$(RUNTIME) exec $(CONTAINER) tail -f /var/log/nginx/access.log

error-logs:
	$(RUNTIME) exec $(CONTAINER) tail -f /var/log/nginx/error.log

# View logs for a specific app
logs-app:
	$(RUNTIME) exec $(CONTAINER) tail -f /var/log/supervisor/$(APP).out.log

# Shell into the running container
shell:
	$(RUNTIME) exec -it $(CONTAINER) /bin/bash

# Check supervisor status inside container
status:
	$(RUNTIME) exec $(CONTAINER) supervisorctl status

# Restart a specific app inside the container
restart-app:
	$(RUNTIME) exec $(CONTAINER) supervisorctl restart $(APP)

# All-in-one target
rebuild: stop build run logs

# Health check
health:
	@echo "Checking container health..."
	@$(RUNTIME) ps --filter "name=$(CONTAINER)" --format "table {{.Names}}\t{{.Status}}"
	@echo ""
	@echo "Testing endpoints..."
	@curl -s http://localhost:8080/hello || echo " (not responding)"

# Submodules Management

init:
	git submodule update --init --recursive

add:
	git submodule add $(REPO)

update:
	git submodule foreach git pull origin master

# Frontpage

GUNICORN = gunicorn -k uvicorn.workers.UvicornH11Worker
frontpage:
	uv run --project frontpage $(GUNICORN) frontpage:app --reload

format:
	uv run --project frontpage ruff check --fix frontpage/

# === MONITORING ===

.PHONY: monitoring-status prometheus-logs grafana-logs loki-logs grafana-open grafana-forward prometheus-forward health-check

# Check monitoring stack status
monitoring-status:
	@echo "=== Monitoring Stack Status ==="
	$(RUNTIME) exec $(CONTAINER) supervisorctl status prometheus grafana loki promtail node_exporter nginx_exporter

# View Prometheus logs
prometheus-logs:
	$(RUNTIME) exec $(CONTAINER) tail -f /var/log/supervisor/prometheus*.log

# View Grafana logs
grafana-logs:
	$(RUNTIME) exec $(CONTAINER) tail -f /var/log/supervisor/grafana*.log

# View Loki logs
loki-logs:
	$(RUNTIME) exec $(CONTAINER) tail -f /var/log/supervisor/loki*.log

# View Promtail logs
promtail-logs:
	$(RUNTIME) exec $(CONTAINER) tail -f /var/log/supervisor/promtail*.log

# Open Grafana dashboard (requires port forward)
grafana-open:
	@echo "Opening Grafana dashboard..."
	@echo "If running locally, visit: http://localhost:3000"
	@echo "If remote, run: make grafana-forward"
	@open http://localhost:3000 2>/dev/null || xdg-open http://localhost:3000 2>/dev/null || true

# Port forward Grafana for external access
grafana-forward:
	@echo "Forwarding Grafana port 3000 to localhost:3000"
	$(RUNTIME) port-forward $(CONTAINER) 3000:3000

# Port forward Prometheus for external access
prometheus-forward:
	@echo "Forwarding Prometheus port 9090 to localhost:9090"
	$(RUNTIME) port-forward $(CONTAINER) 9090:9090

# Health check all apps
health-check:
	@echo "Checking health endpoints..."
	@for port in 5000 5001 5002 5004 5005 5006 5007 5008 5009 5010 5011; do \
		echo -n "Port $$port: "; \
		$(RUNTIME) exec $(CONTAINER) curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:$$port/health 2>/dev/null || echo "N/A"; \
	done
