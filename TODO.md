# TODO

## Done

- [x] **R1-001: Setup Roomz Hosting Infrastructure** (2025-05-15)
  - Configured supervisord, nginx, and apps.yaml for roomz.app.homemadebycvg.com
  - Added environment configuration (ROOMZ_* variables)
  - Updated Dockerfile to install roomz from PyPI
  - **Satisfies**: R1, R2, R3, R4, R5

- [x] **INFRA-001: Document Scaling Strategy** (2026-05-17)
  - Analyzed hosting options and costs
  - Documented current memory breakdown
  - Defined 3-phase scaling strategy
  - See [docs/SCALING_STRATEGY.md](docs/SCALING_STRATEGY.md)

## Backlog

- [ ] **FP-001: Frontpage App Implementation**
  - Create frontpage app to replace hosted-flasks functionality
  - **Satisfies**: FP-001

- [ ] **INFRA-002: Add Redis Cache for Roomz**
  - Add Redis to container for message caching
  - Configure persistence and sync to MongoDB
  - ~50-100MB memory impact
  - Trigger: When roomz offline message handling needed
