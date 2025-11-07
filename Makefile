# MSA Pension Sentiment Analysis Platform
# Spring Boot Microservices Architecture
# NOTE: This Makefile references the main compose file. For local dev, use infra/compose/local-dev.yml

.PHONY: help build start stop restart logs clean test lint check-health

# Default target
help:
	@echo "🏗️  MSA Pension Sentiment Analysis Platform"
	@echo "=========================================="
	@echo ""
	@echo "Available commands:"
	@echo "  build         - Build all microservices"
	@echo "  start         - Start all services"
	@echo "  stop          - Stop all services"
	@echo "  restart       - Restart all services"
	@echo "  logs          - Show logs for all services"
	@echo "  logs-service  - Show logs for specific service (e.g., make logs-service SERVICE=analysis)"
	@echo "  clean         - Clean up containers and volumes"
	@echo "  test          - Run tests for all services"
	@echo "  lint          - Run linting for all services"
	@echo "  check-health  - Check health of all services"
	@echo "  status        - Show status of all services"
	@echo ""
	@echo "Services:"
	@echo "  📊 API Gateway     (Port 8080) - Main entry point"
	@echo "  🧠 Analysis       (Port 8001) - Sentiment analysis & ML"
	@echo "  🕷️  Collector      (Port 8002) - Web scraping & RSS feeds"
	@echo "  🎯 ABSA           (Port 8003) - Aspect-based sentiment analysis"
	@echo "  🚨 Alert          (Port 8004) - Notifications & alerts"
	@echo ""
	@echo "Infrastructure:"
	@echo "  🐘 PostgreSQL     (Port 5432) - Main database with pgvector"
	@echo "  🔥 Redis          (Port 6379) - Caching layer"

# Infrastructure commands
infra-start:
	@echo "🚀 Starting infrastructure services..."
	docker compose -f docker-compose.spring.yml up -d postgres redis

infra-stop:
	@echo "🛑 Stopping infrastructure services..."
	docker compose -f docker-compose.spring.yml stop postgres redis

# Build all services
build:
	@echo "🏗️  Building all microservices..."
	docker compose -f docker-compose.spring.yml build

# Service lifecycle
start:
	@echo "🚀 Starting MSA Pension Sentiment Platform..."
	docker compose -f docker-compose.spring.yml up -d
	@echo "✅ All services started!"
	@echo ""
	@make check-health

stop:
	@echo "🛑 Stopping all services..."
	docker compose -f docker-compose.spring.yml down

restart: stop start

# Logs
logs:
	@echo "📋 Showing logs for all services..."
	docker compose -f docker-compose.spring.yml logs -f

logs-service:
	@echo "📋 Showing logs for $(SERVICE)..."
	docker compose -f docker-compose.spring.yml logs -f $(SERVICE)

# Maintenance
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker compose -f docker-compose.spring.yml down -v --remove-orphans
	docker system prune -f

# Development
test:
	@echo "🧪 Running tests for all services..."
	@for service in analysis-service collector-service absa-service alert-service api-gateway; do \
		echo "Testing $$service..."; \
		docker compose -f docker-compose.spring.yml exec $$service pytest tests/ || echo "⚠️  Tests failed for $$service"; \
	done

lint:
	@echo "🔍 Running linting for all services..."
	@for service in analysis-service collector-service absa-service alert-service api-gateway; do \
		echo "Linting $$service..."; \
		docker compose -f docker-compose.spring.yml exec $$service ruff check app/ || echo "⚠️  Linting issues in $$service"; \
	done

# Health checks
check-health:
	@echo "🏥 Checking health of all services..."
	@echo "API Gateway:     $(shell curl -s http://localhost:8080/actuator/health 2>/dev/null | grep -o '"status":"[^"]*"' || echo '❌ DOWN')"
	@echo "Analysis:        $(shell curl -s http://localhost:8001/actuator/health 2>/dev/null | grep -o '"status":"[^"]*"' || echo '❌ DOWN')"
	@echo "Collector:       $(shell curl -s http://localhost:8002/actuator/health 2>/dev/null | grep -o '"status":"[^"]*"' || echo '❌ DOWN')"
	@echo "ABSA:            $(shell curl -s http://localhost:8003/actuator/health 2>/dev/null | grep -o '"status":"[^"]*"' || echo '❌ DOWN')"
	@echo "Alert:           $(shell curl -s http://localhost:8004/actuator/health 2>/dev/null | grep -o '"status":"[^"]*"' || echo '❌ DOWN')"

status:
	@echo "📊 Service Status:"
	docker compose -f docker-compose.spring.yml ps

# Quick start for development
dev-start: infra-start
	@echo "🔧 Starting development environment..."
	@echo "Infrastructure started. Start individual services with:"
	@echo "  cd services/analysis-service && uvicorn app.main:app --reload --port 8001"
	@echo "  cd services/collector-service && uvicorn app.main:app --reload --port 8002"
	@echo "  cd services/absa-service && uvicorn app.main:app --reload --port 8003"
	@echo "  cd services/alert-service && uvicorn app.main:app --reload --port 8004"
	@echo "  cd services/api-gateway && uvicorn app.main:app --reload --port 8000"

# Database management
db-migrate:
	@echo "🗃️  Running database migrations..."
	docker compose -f docker-compose.spring.yml exec analysis-service alembic upgrade head

db-reset:
	@echo "⚠️  Resetting database (this will delete all data)..."
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose -f docker-compose.spring.yml stop postgres
	docker volume rm capstone_postgres-data
	docker compose -f docker-compose.spring.yml up -d postgres
	@make db-migrate

# API Documentation
docs:
	@echo "📚 API Documentation URLs:"
	@echo "  API Gateway:  http://localhost:8000/docs"
	@echo "  Analysis:     http://localhost:8001/docs"
	@echo "  Collector:    http://localhost:8002/docs"
	@echo "  ABSA:         http://localhost:8003/docs"
	@echo "  Alert:        http://localhost:8004/docs"

# Monitoring
monitor:
	@echo "📈 Starting monitoring dashboard..."
	@echo "Redis: redis-cli -h localhost -p 6379 monitor"
	@echo "PostgreSQL: docker compose -f docker-compose.msa.yml exec postgres psql -U postgres -d pension_sentiment"

# Production deployment helpers
prod-build:
	@echo "🚀 Building for production..."
	docker compose -f docker-compose.spring.yml build --no-cache

prod-deploy: prod-build
	@echo "🌐 Deploying to production..."
	docker compose -f docker-compose.spring.yml up -d --force-recreate

# Security scan
security-scan:
	@echo "🔒 Running security scan..."
	@for service in analysis-service collector-service absa-service alert-service api-gateway; do \
		echo "Scanning $$service..."; \
		docker run --rm -v $(PWD)/services/$$service:/target clair-scanner:latest || echo "⚠️  Security issues in $$service"; \
	done