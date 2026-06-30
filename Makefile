.PHONY: help install dev run test lint format docker-up docker-down clean index

help: ## Show this help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	pip install -r requirements.txt

dev: ## Install development dependencies
	pip install -r requirements.txt
	pip install ruff black pytest pytest-cov pytest-asyncio pytest-mock

run: ## Run the application locally
	python main.py

index: ## Build the FAISS vector index from policy documents
	python scripts/build_index.py

test: ## Run all tests with coverage
	pytest tests/ -v --cov=app --cov-report=term-missing --cov-report=html

lint: ## Run ruff linter
	ruff check app/ tests/ main.py

format: ## Format code with black and ruff
	black app/ tests/ main.py
	ruff check --fix app/ tests/ main.py

docker-up: ## Start all services with Docker Compose
	docker compose up --build -d

docker-down: ## Stop all Docker Compose services
	docker compose down

clean: ## Remove caches, logs, and build artifacts
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name .pytest_cache -exec rm -rf {} + 2>/dev/null || true
	rm -rf htmlcov .coverage coverage.xml
	rm -rf data/faiss_index
	rm -f logs/*.log
