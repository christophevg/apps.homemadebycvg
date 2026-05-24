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

update: update-submodules rebuild

update-submodules:
	git submodule foreach git pull origin master

# Frontpage

GUNICORN = gunicorn -k uvicorn.workers.UvicornH11Worker
frontpage:
	uv run --project frontpage $(GUNICORN) frontpage:app --reload

format:
	uv run --project frontpage ruff check --fix frontpage/
