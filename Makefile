# Makefile for Socratic AI Benchmarks
# Comprehensive operations for development, testing, and deployment

.PHONY: help install install-dev test test-unit test-integration test-cov lint format clean deploy \
        docker-build docker-test pre-commit validate-config check-security audit docs

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

# Default target - show help
.DEFAULT_GOAL := help

help: ## Show this help message
	@echo "$(BLUE)Socratic AI Benchmarks - Makefile Commands$(NC)"
	@echo ""
	@echo "$(GREEN)Setup & Installation:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /install/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Testing:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /test/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Code Quality:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /lint|format|check|audit/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Deployment:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /deploy|docker/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "$(GREEN)Utilities:$(NC)"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; /clean|validate|docs/ {printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2}'
	@echo ""

# =============================================================================
# Setup & Installation
# =============================================================================

install: ## Install production dependencies
	@echo "$(BLUE)Installing production dependencies...$(NC)"
	cd serverless/lib && pip install -r requirements.txt
	cd serverless/lambdas/planner && pip install -r requirements.txt
	cd serverless/lambdas/runner && pip install -r requirements.txt
	cd serverless/lambdas/judge && pip install -r requirements.txt
	cd serverless/lambdas/curator && pip install -r requirements.txt
	cd serverless/lambdas/api && pip install -r requirements.txt
	cd serverless/infra && pip install -r requirements.txt
	@echo "$(GREEN)✓ Production dependencies installed$(NC)"

install-dev: install ## Install development dependencies (includes testing, linting)
	@echo "$(BLUE)Installing development dependencies...$(NC)"
	cd serverless && pip install -r requirements-dev.txt
	pre-commit install
	@echo "$(GREEN)✓ Development dependencies installed$(NC)"
	@echo "$(GREEN)✓ Pre-commit hooks installed$(NC)"

# =============================================================================
# Testing
# =============================================================================

test: test-unit ## Run all tests (alias for test-unit)

test-unit: ## Run unit tests only (fast, no AWS calls)
	@echo "$(BLUE)Running unit tests...$(NC)"
	cd serverless && pytest tests/unit -v -m unit
	@echo "$(GREEN)✓ Unit tests passed$(NC)"

test-integration: ## Run integration tests (may require AWS credentials)
	@echo "$(BLUE)Running integration tests...$(NC)"
	cd serverless && pytest tests/integration -v -m integration
	@echo "$(GREEN)✓ Integration tests passed$(NC)"

test-all: ## Run all tests (unit + integration)
	@echo "$(BLUE)Running all tests...$(NC)"
	cd serverless && pytest tests/ -v
	@echo "$(GREEN)✓ All tests passed$(NC)"

test-cov: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	cd serverless && pytest tests/ -v --cov=lib/socratic_bench --cov=lambdas \
		--cov-report=term-missing --cov-report=html:htmlcov --cov-report=xml
	@echo "$(GREEN)✓ Coverage report generated in serverless/htmlcov/index.html$(NC)"

test-watch: ## Run tests in watch mode (requires pytest-watch)
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	cd serverless && ptw tests/ -- -v

# =============================================================================
# Code Quality
# =============================================================================

lint: ## Run all linters (ruff, flake8, pylint, mypy)
	@echo "$(BLUE)Running linters...$(NC)"
	@echo "$(YELLOW)→ ruff...$(NC)"
	cd serverless && ruff check lib/ lambdas/ tests/ || true
	@echo "$(YELLOW)→ flake8...$(NC)"
	cd serverless && flake8 lib/ lambdas/ tests/ --max-line-length=100 --ignore=E203,W503 || true
	@echo "$(YELLOW)→ pylint...$(NC)"
	cd serverless && pylint lib/socratic_bench/ --max-line-length=100 || true
	@echo "$(YELLOW)→ mypy...$(NC)"
	cd serverless && mypy lib/socratic_bench/ --ignore-missing-imports || true
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Auto-format code with black and isort
	@echo "$(BLUE)Formatting code...$(NC)"
	cd serverless && black lib/ lambdas/ tests/ --line-length=100
	cd serverless && isort lib/ lambdas/ tests/ --profile=black --line-length=100
	@echo "$(GREEN)✓ Code formatted$(NC)"

check-format: ## Check if code is formatted correctly (CI mode)
	@echo "$(BLUE)Checking code formatting...$(NC)"
	cd serverless && black lib/ lambdas/ tests/ --check --line-length=100
	cd serverless && isort lib/ lambdas/ tests/ --check --profile=black --line-length=100
	@echo "$(GREEN)✓ Code formatting is correct$(NC)"

check-security: ## Run security checks with bandit
	@echo "$(BLUE)Running security checks...$(NC)"
	cd serverless && bandit -r lib/ lambdas/ -c ../.bandit.yml
	@echo "$(GREEN)✓ No security issues found$(NC)"

audit: ## Run comprehensive code audit (lint + security + tests)
	@echo "$(BLUE)Running comprehensive audit...$(NC)"
	$(MAKE) lint
	$(MAKE) check-security
	$(MAKE) test-cov
	@echo "$(GREEN)✓ Audit complete$(NC)"

# =============================================================================
# Pre-commit
# =============================================================================

pre-commit: ## Run pre-commit hooks on all files
	@echo "$(BLUE)Running pre-commit hooks...$(NC)"
	pre-commit run --all-files
	@echo "$(GREEN)✓ Pre-commit checks passed$(NC)"

pre-commit-update: ## Update pre-commit hook versions
	@echo "$(BLUE)Updating pre-commit hooks...$(NC)"
	pre-commit autoupdate
	@echo "$(GREEN)✓ Pre-commit hooks updated$(NC)"

# =============================================================================
# Deployment
# =============================================================================

validate-config: ## Validate configuration files
	@echo "$(BLUE)Validating configuration...$(NC)"
	@test -f serverless/config-24-models.json || (echo "$(RED)✗ Missing config-24-models.json$(NC)" && exit 1)
	@test -f serverless/lib/socratic_bench/model_capabilities.json || (echo "$(RED)✗ Missing model_capabilities.json$(NC)" && exit 1)
	@python3 -c "import json; json.load(open('serverless/config-24-models.json'))" || \
		(echo "$(RED)✗ Invalid JSON in config-24-models.json$(NC)" && exit 1)
	@python3 -c "import json; json.load(open('serverless/lib/socratic_bench/model_capabilities.json'))" || \
		(echo "$(RED)✗ Invalid JSON in model_capabilities.json$(NC)" && exit 1)
	@echo "$(GREEN)✓ Configuration is valid$(NC)"

deploy-check: validate-config test-unit check-format ## Pre-deployment checks
	@echo "$(BLUE)Running pre-deployment checks...$(NC)"
	@echo "$(GREEN)✓ All pre-deployment checks passed$(NC)"
	@echo "$(YELLOW)Ready to deploy! Run 'make deploy' to deploy to AWS.$(NC)"

deploy: deploy-check ## Deploy to AWS (runs checks first)
	@echo "$(BLUE)Deploying to AWS...$(NC)"
	cd serverless && ./DEPLOY.sh
	@echo "$(GREEN)✓ Deployed to AWS$(NC)"

deploy-force: ## Deploy to AWS without running checks (use with caution)
	@echo "$(YELLOW)⚠ Deploying without pre-checks...$(NC)"
	cd serverless && ./DEPLOY.sh
	@echo "$(GREEN)✓ Deployed to AWS$(NC)"

# =============================================================================
# Docker
# =============================================================================

docker-build: ## Build Docker image
	@echo "$(BLUE)Building Docker image...$(NC)"
	docker build -t socratic-runner:latest .
	@echo "$(GREEN)✓ Docker image built: socratic-runner:latest$(NC)"

docker-test: ## Run Docker CLI test
	@echo "$(BLUE)Running Docker CLI test...$(NC)"
	@test -n "$$AWS_REGION" || (echo "$(RED)✗ AWS_REGION not set$(NC)" && exit 1)
	@test -n "$$BEDROCK_MODEL_IDS" || (echo "$(RED)✗ BEDROCK_MODEL_IDS not set$(NC)" && exit 1)
	docker run --rm \
		-e AWS_REGION \
		-e BEDROCK_MODEL_IDS \
		socratic-runner:latest \
		--model anthropic.claude-3-5-sonnet-20241022-v1:0 \
		--prompt "I'm considering a career change but unsure where to start." \
		--turns 3
	@echo "$(GREEN)✓ Docker CLI test passed$(NC)"

docker-shell: ## Open shell in Docker container (for debugging)
	@echo "$(BLUE)Opening Docker shell...$(NC)"
	docker run --rm -it socratic-runner:latest /bin/bash

# =============================================================================
# Documentation
# =============================================================================

docs: ## Validate all documentation
	@echo "$(BLUE)Validating documentation...$(NC)"
	@test -f README.md || (echo "$(RED)✗ Missing: README.md$(NC)" && exit 1)
	@test -f ARCHITECTURE.md || (echo "$(RED)✗ Missing: ARCHITECTURE.md$(NC)" && exit 1)
	@test -f CHANGELOG.md || (echo "$(RED)✗ Missing: CHANGELOG.md$(NC)" && exit 1)
	@test -f CONTRIBUTING.md || (echo "$(RED)✗ Missing: CONTRIBUTING.md$(NC)" && exit 1)
	@test -f docs/architecture.md || (echo "$(RED)✗ Missing: docs/architecture.md$(NC)" && exit 1)
	@test -f docs/runner.md || (echo "$(RED)✗ Missing: docs/runner.md$(NC)" && exit 1)
	@test -f docs/bedrock.md || (echo "$(RED)✗ Missing: docs/bedrock.md$(NC)" && exit 1)
	@test -f docs/benchmark.md || (echo "$(RED)✗ Missing: docs/benchmark.md$(NC)" && exit 1)
	@echo "$(GREEN)✓ All documentation files exist$(NC)"

docs-serve: ## Serve docs locally (simple HTTP server)
	@echo "$(BLUE)Starting local documentation server...$(NC)"
	@echo "$(GREEN)Visit: http://localhost:8000$(NC)"
	python3 -m http.server 8000

# =============================================================================
# Utilities
# =============================================================================

clean: ## Clean temporary files and caches
	@echo "$(BLUE)Cleaning temporary files...$(NC)"
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".pytest_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".mypy_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".ruff_cache" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".DS_Store" -delete 2>/dev/null || true
	rm -rf serverless/htmlcov serverless/.coverage serverless/coverage.xml
	@echo "$(GREEN)✓ Cleaned temporary files$(NC)"

clean-all: clean ## Clean all generated files including virtual environments
	@echo "$(BLUE)Cleaning all generated files...$(NC)"
	find . -name "venv" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name ".venv" -type d -exec rm -rf {} + 2>/dev/null || true
	find . -name "node_modules" -type d -exec rm -rf {} + 2>/dev/null || true
	@echo "$(GREEN)✓ Cleaned all generated files$(NC)"

list-models: ## List all configured models
	@echo "$(BLUE)Configured models:$(NC)"
	@python3 -c "import json; models = json.load(open('serverless/config-24-models.json'))['models']; \
		print('\\n'.join(f\"  {i+1:2d}. {m['model_id']:50s} - {m['name']}\" for i, m in enumerate(models)))"

count-lines: ## Count lines of code
	@echo "$(BLUE)Lines of code:$(NC)"
	@echo "$(YELLOW)Python files:$(NC)"
	@find serverless/lib serverless/lambdas -name "*.py" | xargs wc -l | tail -1
	@echo "$(YELLOW)Test files:$(NC)"
	@find serverless/tests -name "*.py" | xargs wc -l | tail -1 2>/dev/null || echo "  0 total (no tests yet)"

check-env: ## Check required environment variables
	@echo "$(BLUE)Checking environment variables...$(NC)"
	@bash -c 'if [ -z "$$AWS_REGION" ]; then echo "$(YELLOW)⚠ AWS_REGION not set (optional)$(NC)"; fi'
	@bash -c 'if [ -z "$$AWS_PROFILE" ]; then echo "$(YELLOW)⚠ AWS_PROFILE not set (optional)$(NC)"; fi'
	@bash -c 'if [ -z "$$AWS_ACCOUNT_ID" ]; then echo "$(YELLOW)⚠ AWS_ACCOUNT_ID not set (optional)$(NC)"; fi'
	@echo "$(GREEN)✓ Environment check complete$(NC)"

version: ## Show current version
	@echo "$(BLUE)Socratic AI Benchmarks$(NC)"
	@echo "Version: 2.0.0"
	@echo "Status: Deployed and Operational"

# =============================================================================
# CI/CD Targets
# =============================================================================

ci-test: ## CI: Run tests (for GitHub Actions/GitLab CI)
	$(MAKE) test-all

ci-lint: ## CI: Run linters (for GitHub Actions/GitLab CI)
	$(MAKE) lint
	$(MAKE) check-format
	$(MAKE) check-security

ci-build: ## CI: Build and validate (for GitHub Actions/GitLab CI)
	$(MAKE) install
	$(MAKE) validate-config
	$(MAKE) ci-lint
	$(MAKE) ci-test

ci-deploy: ## CI: Deploy to AWS (for GitHub Actions/GitLab CI)
	$(MAKE) ci-build
	$(MAKE) deploy
