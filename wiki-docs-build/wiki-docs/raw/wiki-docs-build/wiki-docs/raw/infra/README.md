# Infrastructure Configuration

This directory contains all infrastructure-related configuration files for the project.

## Directory Structure

```
infra/
├── compose/          # Docker Compose configurations
│   ├── local-dev.yml # Local development environment
│   ├── staging.yml   # Staging environment (future)
│   └── prod.yml      # Production environment (future)
├── db/               # Database initialization scripts
│   ├── postgres/     # PostgreSQL init scripts
│   └── mongo/        # MongoDB init scripts
└── monitoring/       # Monitoring configurations
    ├── prometheus.yml
    └── grafana/
```

## Usage

### Local Development

Run the local development environment:

```bash
cd infra/compose
docker compose -f local-dev.yml up -d
```

### Environment Variables

Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

## Services

The local-dev compose file includes:

- **PostgreSQL** (with pgvector): Main database
- **Redis**: Caching and queue management
- **Consul**: Service discovery (optional)
- **Grafana/Prometheus**: Monitoring (in monitoring/)

## Notes

- All paths in compose files are relative to the compose file location
- Database init scripts are automatically executed on first container start
- Health checks are configured for all infrastructure services
