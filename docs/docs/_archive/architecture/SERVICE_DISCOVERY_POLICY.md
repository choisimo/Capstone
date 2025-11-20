# Service Discovery Policy

**Document Version**: 1.0.0
**Last Updated**: 2025-11-06
**Status**: Active

## Overview

This document defines the service discovery strategy for the Capstone OSINT Platform. It clarifies the current approach and provides guidance for future scaling scenarios.

## Current Strategy: Static Environment-Based Configuration

### Decision

The platform currently uses **static environment variable-based service discovery** instead of dynamic service discovery tools like Eureka or Consul.

### Implementation

**Environment Variables Format**:
```bash
SERVICES_<SERVICE_NAME>_URL=http://<host>:<port>
```

**Example Configuration** (API Gateway):
```yaml
services:
  collector-url: ${SERVICES_COLLECTOR_URL:http://localhost:8002}
  analysis-url: ${SERVICES_ANALYSIS_URL:http://localhost:8001}
  absa-url: ${SERVICES_ABSA_URL:http://localhost:8003}
  alert-url: ${SERVICES_ALERT_URL:http://localhost:8004}
  osint-orchestrator-url: ${SERVICES_OSINT_ORCHESTRATOR_URL:http://localhost:8005}
  osint-planning-url: ${SERVICES_OSINT_PLANNING_URL:http://localhost:8006}
  osint-source-url: ${SERVICES_OSINT_SOURCE_URL:http://localhost:8007}
```

### Rationale

1. **Simplicity**: Easier to configure, debug, and understand for small-to-medium scale deployments
2. **Reduced Infrastructure**: No additional service registry infrastructure to manage
3. **Docker Compose Native**: Works seamlessly with Docker Compose service names
4. **Kubernetes Ready**: Compatible with Kubernetes service discovery via service names
5. **Development Efficiency**: Faster local development setup without registry dependencies

## Architecture Implications

### Current State (Static Configuration)

```
┌─────────────┐
│ API Gateway │ ──── ENV: SERVICES_ANALYSIS_URL ───> Analysis Service
└─────────────┘
      │
      └──────── ENV: SERVICES_COLLECTOR_URL ──> Collector Service
```

### Eureka/Consul Reference (Not Currently Used)

Code references to Eureka and Consul exist in the codebase but are **disabled by default**:

**Python Services** (`shared/config_loader.py`):
```python
CONSUL_ENABLED = os.getenv("CONSUL_ENABLED", "false").lower() == "true"
EUREKA_ENABLED = os.getenv("EUREKA_ENABLED", "false").lower() == "true"
```

**Java Services**:
- Eureka client dependencies present but not activated
- No `@EnableEurekaClient` annotations
- No active Eureka configuration

## Port Standardization

### Service Port Allocation

| Port | Service              | Type   | Status     |
|------|----------------------|--------|------------|
| 8000 | API Gateway          | Java   | Active     |
| 8001 | Analysis Service     | Java   | Active     |
| 8002 | Collector Service    | Java   | Active     |
| 8003 | ABSA Service         | Java   | Active     |
| 8004 | Alert Service        | Python | Active     |
| 8005 | OSINT Orchestrator   | Python | Active     |
| 8006 | OSINT Planning       | Python | Active     |
| 8007 | OSINT Source         | Python | Active     |

**Port Scheme**: 800x (consistent across all services)

## Health Check Standardization

### Endpoints

**Java Services** (Spring Boot with Actuator):
```
GET /actuator/health
```

**Python Services** (FastAPI):
```
GET /health
```

### Health Check Configuration

All services expose health endpoints for:
- Docker Compose health checks
- Kubernetes liveness/readiness probes
- Monitoring systems (Prometheus, Grafana)

**Example Docker Compose Health Check**:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/actuator/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 60s
```

## Future Migration Path

### When to Consider Dynamic Service Discovery

Consider migrating to Eureka or Consul when:

1. **Horizontal Scaling**: Running multiple instances of the same service
2. **Dynamic Instance Management**: Services frequently scale up/down
3. **Multi-Region Deployment**: Services distributed across multiple data centers
4. **Complex Routing**: Need client-side load balancing or circuit breakers
5. **Service Mesh**: Integration with Istio, Linkerd, or similar

### Migration Strategy (If Needed)

#### Phase 1: Preparation
- Enable Eureka client in Spring Boot services
- Configure Consul client in Python services
- Deploy registry infrastructure (Eureka/Consul servers)

#### Phase 2: Dual Mode
- Run static ENV config alongside service registry
- Gradual migration service-by-service
- Validate discovery via monitoring

#### Phase 3: Cutover
- Disable static ENV fallbacks
- Full reliance on service registry
- Update documentation

### Estimated Migration Effort

**Complexity**: Medium
**Estimated Time**: 2-3 weeks
**Prerequisites**:
- Eureka/Consul infrastructure deployed
- Service registry monitoring configured
- Load testing completed

## Configuration Examples

### Docker Compose (Current)

```yaml
api-gateway:
  environment:
    SERVICES_COLLECTOR_URL: http://collector-service:8002
    SERVICES_ANALYSIS_URL: http://analysis-service:8001
```

### Kubernetes (Current)

```yaml
env:
- name: SERVICES_COLLECTOR_URL
  value: "http://collector-service.default.svc.cluster.local:8002"
```

### Eureka (Future, If Needed)

```yaml
# application.yml
eureka:
  client:
    serviceUrl:
      defaultZone: http://eureka-server:8761/eureka/
    enabled: true
```

## References

- [Spring Cloud Netflix Eureka](https://spring.io/projects/spring-cloud-netflix)
- [HashiCorp Consul](https://www.consul.io/)
- [Kubernetes Service Discovery](https://kubernetes.io/docs/concepts/services-networking/service/)

## Revision History

| Version | Date       | Author | Changes                              |
|---------|------------|--------|--------------------------------------|
| 1.0.0   | 2025-11-06 | System | Initial policy document              |

## Related Documents

- [ARCHITECTURE_OVERVIEW.md](./ARCHITECTURE_OVERVIEW.md)
- [INFRASTRUCTURE_CONSISTENCY.md](./INFRASTRUCTURE_CONSISTENCY.md)
- [PORT_STANDARDIZATION.md](./PORT_STANDARDIZATION.md)
