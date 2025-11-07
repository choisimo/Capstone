# Deprecated Services

**Status**: DEPRECATED - No longer in active development

This directory contains legacy Python-based services that have been migrated to Java.

## Deprecation Information

- **Deprecated Date**: 2025-09-30 (Phase 1 migration completed)
- **Reason**: Migration from Python microservices to Java/Spring Boot for better type safety, performance, and ecosystem integration
- **Replacement**: See `/services/java/` for current Java-based implementations

## Directory Structure

```
deprecated/
├── buildsystem/    # Old build configurations
├── compose/        # Old Docker Compose files
├── docs/           # Legacy documentation
├── scripts/        # Deprecated Python scripts
├── services/       # Deprecated Python microservices
│   └── python/
│       ├── BACKEND-ABSA/
│       ├── BACKEND-ALERT/
│       ├── BACKEND-ANALYSIS/
│       ├── BACKEND-API-GATEWAY/
│       ├── BACKEND-COLLECTOR/
│       ├── BACKEND-OSINT-*/
│       ├── BACKEND-WEB-COLLECTOR/
│       └── BACKEND-WEB-CRAWLER/
├── shared/         # Shared Python utilities
└── tests/          # Legacy test files
```

## Migration Status

All core functionality from these Python services has been migrated to:

- **API Gateway** → `services/java/gateway`
- **Analysis Service** → `services/java/analysis`
- **Collector Service** → `services/java/collector`
- **ABSA Service** → `services/java/absa` (scaffolding complete)
- **Alert Service** → `services/java/alert` (scaffolding complete)
- **OSINT Orchestrator** → `services/java/osint-orchestrator` (scaffolding complete)
- **OSINT Planning** → `services/java/osint-planning` (scaffolding complete)
- **OSINT Source** → `services/java/osint-source` (scaffolding complete)

## Why This Was Deprecated

1. **Type Safety**: Java provides compile-time type checking
2. **Performance**: Better performance for high-throughput services
3. **Ecosystem**: Rich Spring Boot ecosystem for microservices
4. **Maintainability**: Easier to maintain with strong typing and IDE support
5. **Team Expertise**: Better alignment with team skills

## Retention Policy

These files are kept for:

- Historical reference
- Feature comparison during migration
- Recovery of any missed functionality
- Documentation of original implementation decisions

**Do not use these services in production or new development.**

For questions about specific deprecated features, consult the migration documentation in `/docs/architecture/`.
