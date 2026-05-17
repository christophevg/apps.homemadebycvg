# Apps Homemade By CVG

> a frontpage to the apps I make from time to time

This is multi-app/site hosting subdomain offering access to some of the apps I make from time to time. Previously it was using my [Hosted Flasks](https://pypi.org/project/hosted-flasks/) Python module to serve multiple sites from a single server instance. When I decided to move from Flask to Quart (from sync to async Python), I played with the idea to port hosted-flasks to hosted-quarts (and actually started it), until I considered that a [container](README.container.md) would basically be a better approach to my hosting situation 😇

## Documentation

- [Container Setup](README.container.md) - Docker/Podman container configuration
- [Scaling Strategy](docs/SCALING_STRATEGY.md) - Infrastructure scaling and cost analysis
- [Monitoring Setup](docs/MONITORING_SETUP.md) - Prometheus, Grafana, and logging
- [Podman Reference](docs/PODMAN_REFERENCE.md) - Podman commands and workflows
