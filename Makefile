# Mental Health App Makefile
# Provides common development and deployment tasks

.PHONY: help install install-dev install-prod setup build run run-dev run-prod test clean docker-build docker-run docker-push deploy-k8s backup restore logs status health

# Variables
PYTHON = python3
PIP = pip3
DOCKER_IMAGE = mental-health-app
DOCKER_TAG = latest
REGISTRY = your-registry.com
NAMESPACE = default

# Default target
help:
	@echo "Mental Health App - Available Commands:"
	@echo "==============================================="
	@echo "Development:"
	@echo "  install           Install dependencies"
	@echo "  install-dev       Install dev dependencies"
	@echo "  install-prod      Install production dependencies"
	@echo "  setup            Setup development environment"
	@echo "  run              Run application in development mode"
	@echo "  run-dev          Run with development settings"
	@echo "  run-prod         Run with production settings"
	@echo "  test             Run tests"
	@echo "  clean            Clean temporary files"
	@echo ""
	@echo "Docker:"
	@echo "  docker-build     Build Docker image"
	@echo "  docker-run       Run Docker container"
	@echo "  docker-push      Push image to registry"
	@echo ""
	@echo "Deployment:"
	@echo "  deploy           Deploy with Docker Compose"
	@echo "  deploy-prod      Deploy production with Docker Compose"
	@echo "  deploy-k8s       Deploy to Kubernetes"
	@echo "  backup           Backup application data"
	@echo "  restore          Restore from backup"
	@echo ""
	@echo "Monitoring:"
	@echo "  logs             View application logs"
	@echo "  status           Check application status"
	@echo "  health           Check health endpoints"

# Development setup
install:
	$(PIP) install -r requirements.txt

install-dev:
	$(PIP) install -r requirements.txt
	$(PIP) install pytest pytest-asyncio black flake8 mypy

install-prod:
	$(PIP) install -r requirements.prod.txt

setup: install-dev
	@echo "Setting up development environment..."
	@mkdir -p logs data uploads chat_sessions survey_data processed_docs
	@if [ ! -f .env ]; then cp .env.production .env; fi
	@echo "Development environment setup complete!"
	@echo "Please edit .env file with your configuration."

# Running the application
run:
	@echo "Starting development server..."
	$(PYTHON) start_services.py

run-dev:
	@echo "Starting development server with debug mode..."
	@export FLASK_ENV=development DEBUG=true && $(PYTHON) start_services.py

run-prod:
	@echo "Starting production server..."
	@export FLASK_ENV=production DEBUG=false && $(PYTHON) start_services.py

# Testing
test:
	@echo "Running tests..."
	pytest tests/ -v

test-coverage:
	@echo "Running tests with coverage..."
	pytest --cov=. --cov-report=html tests/

# Code quality
lint:
	@echo "Running linters..."
	flake8 . --exclude=venv,__pycache__,.git
	black --check .

format:
	@echo "Formatting code..."
	black .

type-check:
	@echo "Running type checks..."
	mypy . --ignore-missing-imports

# Docker operations
docker-build:
	@echo "Building Docker image..."
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

docker-run:
	@echo "Running Docker container..."
	docker run -p 5000:5000 -p 8000:8000 $(DOCKER_IMAGE):$(DOCKER_TAG)

docker-push: docker-build
	@echo "Pushing Docker image to registry..."
	docker tag $(DOCKER_IMAGE):$(DOCKER_TAG) $(REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)
	docker push $(REGISTRY)/$(DOCKER_IMAGE):$(DOCKER_TAG)

# Docker Compose deployment
deploy:
	@echo "Deploying with Docker Compose (development)..."
	docker-compose -f docker-compose.dev.yml up -d

deploy-prod:
	@echo "Deploying with Docker Compose (production)..."
	docker-compose up -d

deploy-stop:
	@echo "Stopping Docker Compose deployment..."
	docker-compose down

# Kubernetes deployment
deploy-k8s:
	@echo "Deploying to Kubernetes..."
	kubectl apply -f k8s/pvc.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/deployment.yaml
	kubectl apply -f k8s/ingress.yaml

deploy-k8s-delete:
	@echo "Removing from Kubernetes..."
	kubectl delete -f k8s/

# Database operations
db-init:
	@echo "Initializing database..."
	$(PYTHON) -c "from main import init_db; init_db()"

db-migrate:
	@echo "Running database migrations..."
	# Add migration commands here

# Backup and restore
backup:
	@echo "Creating backup..."
	./deploy.sh backup

restore:
	@if [ -z "$(BACKUP_PATH)" ]; then \
		echo "Please specify BACKUP_PATH: make restore BACKUP_PATH=path/to/backup"; \
		exit 1; \
	fi
	@echo "Restoring from $(BACKUP_PATH)..."
	./deploy.sh restore $(BACKUP_PATH)

# Monitoring and logs
logs:
	@echo "Viewing application logs..."
	docker-compose logs -f

logs-flask:
	@echo "Viewing Flask logs..."
	docker-compose logs -f mental-health-app

logs-k8s:
	@echo "Viewing Kubernetes logs..."
	kubectl logs -f deployment/mental-health-app

status:
	@echo "Checking application status..."
	./deploy.sh status

health:
	@echo "Checking health endpoints..."
	@curl -f http://localhost:5000/ && echo "Flask: OK" || echo "Flask: FAILED"
	@curl -f http://localhost:8000/health && echo "FastAPI: OK" || echo "FastAPI: FAILED"

# Cleanup
clean:
	@echo "Cleaning temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.log" -delete
	rm -rf .pytest_cache
	rm -rf htmlcov
	rm -rf .coverage
	rm -rf dist
	rm -rf build
	rm -rf *.egg-info

clean-docker:
	@echo "Cleaning Docker resources..."
	docker system prune -f
	docker volume prune -f

# Development helpers
dev-reset: clean
	@echo "Resetting development environment..."
	rm -rf data/*.db
	rm -rf logs/*
	rm -rf uploads/*
	$(MAKE) setup

dev-update:
	@echo "Updating development environment..."
	git pull
	$(MAKE) install
	$(MAKE) docker-build

# Production helpers
prod-update:
	@echo "Updating production deployment..."
	git pull
	$(MAKE) docker-build
	$(MAKE) deploy-prod

# Security scan
security-scan:
	@echo "Running security scan..."
	pip-audit
	safety check

# Generate requirements
freeze:
	@echo "Freezing requirements..."
	pip freeze > requirements.freeze.txt

# Environment info
env-info:
	@echo "Environment Information:"
	@echo "======================="
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "Pip: $(shell $(PIP) --version)"
	@echo "Docker: $(shell docker --version)"
	@echo "Docker Compose: $(shell docker-compose --version)"
	@echo "Current directory: $(PWD)"
	@echo "Git branch: $(shell git branch --show-current 2>/dev/null || echo 'Not a git repository')"
