.PHONY: help build up down logs shell test clean

# Variables
DOCKER_COMPOSE = docker-compose
DOCKER_COMPOSE_DEV = $(DOCKER_COMPOSE) -f docker-compose.yml -f docker-compose.dev.yml
APP_CONTAINER = hybrid-crawler-app

# Colors for output
RED = \033[0;31m
GREEN = \033[0;32m
YELLOW = \033[1;33m
NC = \033[0m # No Color

help: ## Show this help message
	@echo "$(GREEN)Hybrid Crawler Docker Commands$(NC)"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "$(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'

# Development Commands
dev-up: ## Start development environment
	$(DOCKER_COMPOSE_DEV) up -d
	@echo "$(GREEN)Development environment started!$(NC)"
	@echo "Services available at:"
	@echo "  - API: http://localhost:8000"
	@echo "  - Grafana: http://localhost:3000 (admin/admin)"
	@echo "  - Prometheus: http://localhost:9090"
	@echo "  - Kafka UI: http://localhost:8080"
	@echo "  - Adminer: http://localhost:8081"
	@echo "  - RedisInsight: http://localhost:8001"
	@echo "  - Mailhog: http://localhost:8025"

dev-down: ## Stop development environment
	$(DOCKER_COMPOSE_DEV) down
	@echo "$(GREEN)Development environment stopped!$(NC)"

dev-logs: ## Show development logs
	$(DOCKER_COMPOSE_DEV) logs -f $(filter-out $@,$(MAKECMDGOALS))

dev-shell: ## Open shell in development container
	$(DOCKER_COMPOSE_DEV) exec $(APP_CONTAINER) /bin/bash

# Production Commands
up: ## Start production environment
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Production environment started!$(NC)"

down: ## Stop production environment
	$(DOCKER_COMPOSE) down
	@echo "$(GREEN)Production environment stopped!$(NC)"

logs: ## Show production logs
	$(DOCKER_COMPOSE) logs -f $(filter-out $@,$(MAKECMDGOALS))

shell: ## Open shell in production container
	$(DOCKER_COMPOSE) exec $(APP_CONTAINER) /bin/bash

# Build Commands
build: ## Build Docker images
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)Images built successfully!$(NC)"

build-dev: ## Build development Docker images
	$(DOCKER_COMPOSE_DEV) build
	@echo "$(GREEN)Development images built successfully!$(NC)"

rebuild: ## Rebuild and restart containers
	$(DOCKER_COMPOSE) down
	$(DOCKER_COMPOSE) build --no-cache
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)Containers rebuilt and restarted!$(NC)"

# Database Commands
db-migrate: ## Run database migrations
	$(DOCKER_COMPOSE) exec $(APP_CONTAINER) python -m alembic upgrade head
	@echo "$(GREEN)Database migrations completed!$(NC)"

db-reset: ## Reset database
	$(DOCKER_COMPOSE) exec $(APP_CONTAINER) python scripts/reset_db.py
	@echo "$(YELLOW)Database reset completed!$(NC)"

db-backup: ## Backup database
	@mkdir -p backups
	$(DOCKER_COMPOSE) exec postgres pg_dump -U crawler_user hybrid_crawler > backups/backup_$$(date +%Y%m%d_%H%M%S).sql
	@echo "$(GREEN)Database backup created!$(NC)"

db-restore: ## Restore database from backup
	@echo "$(YELLOW)Available backups:$(NC)"
	@ls -1 backups/*.sql 2>/dev/null || echo "No backups found"
	@echo ""
	@read -p "Enter backup filename: " backup; \
	$(DOCKER_COMPOSE) exec -T postgres psql -U crawler_user hybrid_crawler < $$backup
	@echo "$(GREEN)Database restored!$(NC)"

# Testing Commands
test: ## Run tests
	$(DOCKER_COMPOSE_DEV) exec $(APP_CONTAINER) pytest tests/ -v
	@echo "$(GREEN)Tests completed!$(NC)"

test-coverage: ## Run tests with coverage
	$(DOCKER_COMPOSE_DEV) exec $(APP_CONTAINER) pytest tests/ --cov=. --cov-report=html --cov-report=term
	@echo "$(GREEN)Coverage report generated!$(NC)"

test-integration: ## Run integration tests
	$(DOCKER_COMPOSE_DEV) exec $(APP_CONTAINER) pytest tests/test_integration.py -v
	@echo "$(GREEN)Integration tests completed!$(NC)"

# Monitoring Commands
metrics: ## Show current metrics
	@curl -s http://localhost:8000/metrics | head -50

health: ## Check health status
	@curl -s http://localhost:8000/health | python -m json.tool

grafana-export: ## Export Grafana dashboards
	@mkdir -p monitoring/grafana/dashboards/exported
	$(DOCKER_COMPOSE) exec $(APP_CONTAINER) python scripts/export_dashboards.py
	@echo "$(GREEN)Dashboards exported!$(NC)"

# Utility Commands
clean: ## Clean up containers, volumes, and images
	$(DOCKER_COMPOSE) down -v
	docker system prune -f
	@echo "$(GREEN)Cleanup completed!$(NC)"

clean-all: ## Deep clean including all data
	$(DOCKER_COMPOSE) down -v
	docker system prune -af
	rm -rf logs/* data/* cache/*
	@echo "$(YELLOW)All data cleaned!$(NC)"

ps: ## Show container status
	$(DOCKER_COMPOSE) ps

restart: ## Restart all services
	$(DOCKER_COMPOSE) restart
	@echo "$(GREEN)Services restarted!$(NC)"

restart-service: ## Restart specific service
	@read -p "Enter service name: " service; \
	$(DOCKER_COMPOSE) restart $$service
	@echo "$(GREEN)Service restarted!$(NC)"

# Init Commands
init: ## Initialize project (first time setup)
	@echo "$(YELLOW)Initializing Hybrid Crawler...$(NC)"
	cp .env.example .env
	@echo "$(GREEN)✓ Environment file created$(NC)"
	$(DOCKER_COMPOSE) build
	@echo "$(GREEN)✓ Docker images built$(NC)"
	$(DOCKER_COMPOSE) up -d postgres redis
	@echo "Waiting for database..."
	@sleep 10
	$(DOCKER_COMPOSE) exec $(APP_CONTAINER) python scripts/init_db.py
	@echo "$(GREEN)✓ Database initialized$(NC)"
	$(DOCKER_COMPOSE) up -d
	@echo "$(GREEN)✓ All services started$(NC)"
	@echo ""
	@echo "$(GREEN)Initialization complete! 🎉$(NC)"
	@echo "Access the API at: http://localhost:8000"

# Allow passing arguments to commands
%:
	@:
