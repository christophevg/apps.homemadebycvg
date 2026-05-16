# TODO

## Backlog

- [ ] **MON-001: Monitoring/Observability Setup**
  - Add monitoring/observability to Docker image
  - Investigate best practices (likely Grafana, Prometheus, Loki)
  - Email notifications via Resend account
  - **Context**: Email from Christophe on 2026-05-16
  - **Scope**: System metrics, access logs, application logs

## Done

- [x] **FP-001: Frontpage App Implementation**
  - Create frontpage app to replace hosted-flasks functionality
  - **Satisfies**: FP-001

- [x] **R1-001: Setup Roomz Hosting Infrastructure** (2025-05-15)
  - Configured supervisord, nginx, and apps.yaml for roomz.app.homemadebycvg.com
  - Added environment configuration (ROOMZ_* variables)
  - Updated Dockerfile to install roomz from PyPI
  - **Satisfies**: R1, R2, R3, R4, R5
