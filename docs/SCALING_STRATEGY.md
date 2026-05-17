# Scaling Strategy

This document outlines the scaling strategy for the apps.homemadebycvg container hosting setup, including rationale, cost analysis, and migration paths.

## Current State (May 2026)

### Infrastructure

| Component | Details |
|-----------|---------|
| **Hosting Plan** | Standard ($25/month) |
| **RAM** | 2GB |
| **CPU** | 1 vCPU |
| **Current Usage** | ~1.2GB (60%) |
| **Headroom** | ~800MB |

### Apps Running (11)

| App | Type | Est. Memory |
|-----|------|-------------|
| frontpage | Quart/uvicorn | ~70MB |
| hello | Flask/eventlet | ~50MB |
| parking | Flask/eventlet | ~50MB |
| nationofpositivity | Flask/eventlet | ~70MB |
| homemadebycvg | Flask/eventlet | ~70MB |
| getijden | Flask/eventlet | ~70MB |
| letmelearn | Flask/eventlet | ~80MB |
| baseweb-demo | Quart/uvicorn | ~80MB |
| howifeel | Flask/eventlet | ~70MB |
| oatk | Flask/eventlet | ~70MB |
| roomz | Quart/uvicorn | ~70MB |

### Monitoring Stack Memory Usage

| Component | Memory |
|-----------|--------|
| Prometheus | ~150MB |
| Grafana | ~150MB |
| Loki | ~50MB |
| Promtail | ~20MB |
| node_exporter | ~10MB |
| nginx_exporter | ~10MB |
| **Total** | ~400MB |

### Base Container Overhead

| Component | Memory |
|-----------|--------|
| Python runtime + dependencies | ~100MB |
| nginx | ~30MB |
| supervisor | ~20MB |
| **Total** | ~150MB |

### Total Memory Breakdown

```
Base overhead:        ~150MB
Monitoring stack:     ~400MB
11 apps:              ~700MB
────────────────────────────
Total:                ~1250MB (of 2048MB)
Headroom:             ~800MB
```

## Hosting Options

| Plan | RAM | CPU | Monthly Cost |
|------|-----|-----|--------------|
| Starter | 512MB | 0.5 | $7 |
| Standard | 2GB | 1 | $25 |
| Pro | 4GB | 2 | $85 |

## Why Multi-Starter Doesn't Work

Splitting across multiple Starter containers ($7 × 3 = $21/month) seems cheaper, but:

### Per-Container Overhead Problem

Each container requires:
- Base runtime + nginx + supervisor: ~150MB
- If monitoring duplicated: +400MB
- If monitoring centralized: separate container needed

### Capacity Analysis

| Setup | Total RAM | Overhead | Available for Apps |
|-------|-----------|----------|-------------------|
| 3× Starters | 1.5GB | ~450MB (3 containers) | ~600MB (if no monitoring) |
| 1× Standard | 2GB | ~550MB (monitoring + base) | ~750MB |

**Result**: 3× Starters provides **less** capacity than 1× Standard, despite costing less.

### Hidden Costs

1. Monitoring must run on at least one container (400MB)
2. Each app container needs nginx for routing
3. DNS/routing complexity between containers
4. Separate deployment pipelines
5. Fragmented observability

## Scaling Strategy

### Phase 1: Current (Now)

**Configuration**: Single Standard container @ $25/month

```
┌─────────────────────────────────────────────────────────────────┐
│                    Standard Container (2GB)                     │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Base overhead: ~150MB                                      │  │
│  │ Monitoring: ~400MB                                        │  │
│  │ 11 apps: ~700MB                                           │  │
│  │ ────────────────────────────────────────────────────────  │  │
│  │ Used: ~1250MB (61%)                                       │  │
│  │ Headroom: ~800MB (39%)                                     │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

**Capacity**: ~750MB for new apps/features

**Additions possible**:
- Redis cache: ~50-100MB ✓
- Local MongoDB: ~200MB (tight, prefer Atlas free tier)

**Trigger for Phase 2**: When RAM usage reaches ~80% (~1.6GB)

### Phase 2: Dual Standard Containers

**Configuration**: 2× Standard containers @ $50/month

```
┌────────────────────────────────────────┐  ┌────────────────────────────────────────┐
│  Container 1: Core + Monitoring (2GB)  │  │  Container 2: Apps + Data (2GB)        │
│  ┌────────────────────────────────────┐│  │  ┌────────────────────────────────────┐│
│  │ Base: ~150MB                       ││  │  │ Base: ~150MB                       ││
│  │ Monitoring: ~400MB                 ││  │  │ Heavy apps: ~700MB                 ││
│  │ Light apps: ~300MB (3-4 apps)      ││  │  │ Redis: ~100MB                       ││
│  │ ──────────────────────────────────││  │  │ MongoDB: ~200MB (optional)          ││
│  │ Used: ~850MB (42%)                 ││  │  │ ──────────────────────────────────  ││
│  │ Headroom: ~1.15GB (58%)             ││  │  │ Used: ~1.15GB (56%)                ││
│  └────────────────────────────────────┘│  │  │ Headroom: ~900MB (44%)              ││
│                                        │  │  └────────────────────────────────────┘│
│  Apps: hello, parking, frontpage, etc  │  │  Apps: roomz, letmelearn, howifeel, etc │
└────────────────────────────────────────┘  └────────────────────────────────────────┘
```

**Cost**: $50/month (vs $85 for single Pro)

**Benefits**:
- 4GB total capacity for $35 less than Pro
- Isolation between monitoring and heavy apps
- Redis and MongoDB fit comfortably
- Failure isolation (one container down doesn't take everything)

**Trigger for Phase 3**: When combined usage reaches ~75% (~3GB)

### Phase 3: Pro Container

**Configuration**: Single Pro container @ $85/month

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         Pro Container (4GB)                              │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ Base overhead: ~150MB                                                ││
│  │ Monitoring: ~400MB                                                   ││
│  │ 11 apps: ~700MB                                                      ││
│  │ Redis: ~100MB                                                        ││
│  │ MongoDB: ~200MB (optional)                                           ││
│  │ Future apps: ~500MB                                                   ││
│  │ ─────────────────────────────────────────────────────────────────────││
│  │ Used: ~2.05GB (51%)                                                  ││
│  │ Headroom: ~1.95GB (49%)                                               ││
│  └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

**Cost**: $85/month

**Benefits**:
- Single container to manage
- 2 CPU for compute-heavy operations
- ~2GB headroom for growth
- Simpler architecture

**Trade-off**: $35/month premium for simplicity vs dual Standard

## Future Additions

### Redis Cache

**Purpose**: Fast in-memory caching for roomz chat messages

**Implementation**:
```yaml
# Add to supervisord.conf
[program:redis]
command=/usr/bin/redis-server --bind 127.0.0.1 --port 6379 --maxmemory 100mb --maxmemory-policy allkeys-lru
autostart=true
autorestart=true
```

**Memory**: ~50-100MB typical, scales with active users

**Use case for roomz**:
- Store recent messages for offline user delivery
- Pub/sub for real-time message distribution
- Periodic sync to MongoDB for persistence

### MongoDB

**Options**:

| Option | Cost | Storage | Notes |
|--------|------|---------|-------|
| Atlas Free Tier | $0 | 512MB | Sufficient for current needs |
| Atlas Flex | $8-30/mo | Variable | Scales with usage |
| Local in container | RAM overhead | Disk space | No egress costs, need backups |

**Recommendation**: Start with Atlas Free Tier. Migrate to Flex or local when:
- Storage exceeds 512MB
- Query performance requires local proximity
- Cost of egress exceeds Atlas pricing

## Decision Matrix

| Criteria | Standard (now) | 2× Standard | Pro |
|----------|-----------------|-------------|-----|
| Monthly cost | $25 | $50 | $85 |
| Total RAM | 2GB | 4GB | 4GB |
| Management complexity | Low | Medium | Low |
| Failure isolation | None | Partial | None |
| Cost per GB | $12.50 | $12.50 | $21.25 |
| Best for | Current state | Growth phase | Simplicity priority |

## Monitoring Thresholds

Set alerts in Grafana for:

| Metric | Warning | Critical | Action |
|--------|---------|----------|--------|
| Memory usage | 75% | 85% | Review Phase 2 migration |
| Memory usage | 85% | 90% | Reduce non-essential apps |
| CPU usage | 70% | 85% | Consider compute upgrade |
| App response time | 500ms | 1000ms | Scale or optimize |

## Migration Checklist (Phase 1 → Phase 2)

When reaching ~80% memory usage:

1. **Prepare second container**
   - [ ] Create new container instance
   - [ ] Install base dependencies
   - [ ] Configure nginx for routing

2. **Split apps**
   - [ ] Identify apps to migrate (heaviest first)
   - [ ] Update supervisord.conf for each container
   - [ ] Update nginx.conf routing rules
   - [ ] Test each app on new container

3. **Add data services**
   - [ ] Install Redis on apps container
   - [ ] Configure Redis persistence settings
   - [ ] Update app configs for Redis connection
   - [ ] (Optional) Install MongoDB

4. **Update monitoring**
   - [ ] Configure Prometheus to scrape both containers
   - [ ] Update Grafana dashboards for multi-container view
   - [ ] Set up cross-container log aggregation

5. **DNS/Routing**
   - [ ] Update DNS records for split apps
   - [ ] Configure load balancer if needed
   - [ ] Test all app endpoints

## History

| Date | Change | RAM Impact |
|------|--------|------------|
| 2026-05 | Added monitoring stack | +400MB |
| 2026-05 | Baseline (11 apps) | ~850MB |
| 2026-05 | Total | ~1.25GB |

---

*Document created: 2026-05-17*
*Last updated: 2026-05-17*