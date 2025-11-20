# MSA Pension Sentiment Analysis Platform
# Spring Boot Microservices Architecture
# NOTE: This Makefile references the unified infrastructure configuration.

COMPOSE_FILE := infrastructure/docker/compose.yml
DEV_FILE := infrastructure/docker/dev.yml
PROD_FILE := infrastructure/docker/prod.yml

.PHONY: help build start stop restart logs clean test lint check-health

# Default target
help:
	@echo "🏗️  MSA Pension Sentiment Analysis Platform"
	@echo "=========================================="
	@echo ""
	@echo "Available commands:"
	@echo "  build         - Build all microservices"
	@echo "  start         - Start all services (Development mode)"
	@echo "  start-prod    - Start all services (Production mode)"
	@echo "  stop          - Stop all services"
	@echo "  restart       - Restart all services"
	@echo "  logs          - Show logs for all services"
	@echo "  logs-service  - Show logs for specific service (e.g., make logs-service SERVICE=analysis)"
	@echo "  clean         - Clean up containers and volumes"
	@echo "  check-health  - Check health of all services"
	@echo "  status        - Show status of all services"
	@echo ""
	@echo "Services:"
	@echo "  📊 API Gateway     (Port 8080) - Main entry point"
	@echo "  🧠 Analysis       (Port 8001) - Sentiment analysis & ML"
	@echo "  🕷️  Collector      (Port 8002) - Web scraping & RSS feeds"
	@echo "  🎯 ABSA           (Port 8003) - Aspect-based sentiment analysis"
	@echo "  🚨 Alert          (Port 8004) - Notifications & alerts"
	@echo "  🖥️  Frontend       (Port 5173) - Dashboard"
	@echo ""
	@echo "Infrastructure:"
	@echo "  🐘 PostgreSQL     (Port 5432) - Main database with pgvector"
	@echo "  🔥 Redis          (Port 6379) - Caching layer"

# Infrastructure commands
infra-start:
	@echo "🚀 Starting infrastructure services..."
	docker compose -f $(COMPOSE_FILE) -f $(DEV_FILE) up -d postgres redis

infra-stop:
	@echo "🛑 Stopping infrastructure services..."
	docker compose -f $(COMPOSE_FILE) -f $(DEV_FILE) stop postgres redis

# Build all services
build:
	@echo "🏗️  Building all microservices..."
	docker compose -f $(COMPOSE_FILE) -f $(DEV_FILE) build

# Service lifecycle
start:
	@echo "🚀 Starting MSA Pension Sentiment Platform (Development)..."
	docker compose -f $(COMPOSE_FILE) -f $(DEV_FILE) up -d
	@echo "✅ All services started!"
	@echo ""
	@make check-health

start-prod:
	@echo "🚀 Starting MSA Pension Sentiment Platform (Production)..."
	docker compose -f $(COMPOSE_FILE) -f $(PROD_FILE) up -d
	@echo "✅ All services started!"

stop:
	@echo "🛑 Stopping all services..."
	docker compose -f $(COMPOSE_FILE) down

restart: stop start

# Logs
logs:
	@echo "📋 Showing logs for all services..."
	docker compose -f $(COMPOSE_FILE) logs -f

logs-service:
	@echo "📋 Showing logs for $(SERVICE)..."
	docker compose -f $(COMPOSE_FILE) logs -f $(SERVICE)

# Maintenance
clean:
	@echo "🧹 Cleaning up containers and volumes..."
	docker compose -f $(COMPOSE_FILE) down -v --remove-orphans
	docker system prune -f

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
	docker compose -f $(COMPOSE_FILE) ps

# Database management
db-reset:
	@echo "⚠️  Resetting database (this will delete all data)..."
	@read -p "Are you sure? [y/N] " confirm && [ "$$confirm" = "y" ] || exit 1
	docker compose -f $(COMPOSE_FILE) stop postgres
	docker volume rm infrastructure_postgres-data || true
	docker compose -f $(COMPOSE_FILE) -f $(DEV_FILE) up -d postgres

# API Documentation
docs:
	@echo "📚 API Documentation URLs:"
	@echo "  API Gateway:  http://localhost:8080/swagger-ui.html"
	@echo "  Analysis:     http://localhost:8001/swagger-ui.html"
	@echo "  Collector:    http://localhost:8002/swagger-ui.html"
	@echo "  ABSA:         http://localhost:8003/swagger-ui.html"
	@echo "  Alert:        http://localhost:8004/swagger-ui.html"