# OKX HFT Infrastructure Makefile
# Convenient commands for managing the infrastructure

.PHONY: help start stop clean status migrate test logs

help: ## Show this help message
	@echo "OKX HFT Infrastructure Management"
	@echo "================================="
	@echo ""
	@echo "Available commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

start: ## Start all services
	@echo "🚀 Starting OKX HFT Infrastructure..."
	@chmod +x scripts/*.sh
	@./scripts/start.sh

stop: ## Stop all services
	@echo "🛑 Stopping OKX HFT Infrastructure..."
	@./scripts/stop.sh

clean: ## Remove all containers and data
	@echo "🧹 Cleaning OKX HFT Infrastructure..."
	@./scripts/clean.sh

status: ## Show status of all services
	@./scripts/status.sh

migrate: ## Run database migrations
	@echo "🔄 Running database migrations..."
	@./scripts/migrate.sh

test: ## Run tests
	@echo "🧪 Running tests..."
	@./scripts/test.sh

mlflow-experiments: ## Run MLflow experiments
	@echo "🧪 Running MLflow experiments..."
	@./scripts/run_mlflow_experiments.sh

logs: ## Show logs for all services
	@cd docker-compose && docker-compose logs -f

logs-clickhouse: ## Show ClickHouse logs
	@cd docker-compose && docker-compose logs -f clickhouse

logs-minio: ## Show MinIO logs
	@cd docker-compose && docker-compose logs -f minio

logs-monitoring: ## Show monitoring logs
	@cd docker-compose && docker-compose logs -f prometheus grafana

logs-mlflow: ## Show MLflow logs
	@cd docker-compose && docker-compose logs -f mlflow

install-deps: ## Install Python dependencies
	@echo "📦 Installing Python dependencies..."
	@pip install -r requirements.txt

setup: install-deps start migrate test ## Complete setup (install deps, start, migrate, test)
	@echo "🎉 Setup complete!"

restart: stop start ## Restart all services
