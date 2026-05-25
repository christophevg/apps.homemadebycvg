# Apps Homemade By CVG

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)][python]
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)][uv]
[![Agentic](https://img.shields.io/badge/workflow-agentic-blueviolet?style=flat-square)](https://christophe.vg/about/Agentic-Workflow)

> a frontpage to the apps I make from time to time

This is multi-app/site hosting subdomain offering access to some of the apps I make from time to time. Previously it was using my [Hosted Flasks](https://pypi.org/project/hosted-flasks/) Python module to serve multiple sites from a single server instance. When I decided to move from Flask to Quart (from sync to async Python), I played with the idea to port hosted-flasks to hosted-quarts (and actually started it), until I considered that a [container](README.container.md) would basically be a better approach to my hosting situation 😇

[python]: https://python.org/
[uv]: https://docs.astral.sh/uv/
