#!/bin/bash

# Mental Health App Deployment Script
# This script helps deploy the application to various environments

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    log_info "Prerequisites check passed."
}

# Setup environment
setup_environment() {
    log_info "Setting up environment..."
    
    if [ ! -f .env ]; then
        if [ -f .env.production ]; then
            log_warn ".env not found. Copying from .env.production template."
            cp .env.production .env
            log_warn "Please edit .env file with your actual configuration values."
        else
            log_error ".env file not found and no template available."
            exit 1
        fi
    fi
    
    # Create necessary directories
    mkdir -p logs data uploads ssl
    
    log_info "Environment setup completed."
}

# Build application
build_app() {
    log_info "Building application..."
    
    # Build Docker image
    docker-compose build
    
    log_info "Application build completed."
}

# Validate production environment
validate_production() {
    log_info "Validating production environment..."
    
    if [ -f validate_production.py ]; then
        python3 validate_production.py
        if [ $? -ne 0 ]; then
            log_error "Production validation failed. Please fix the issues above."
            exit 1
        fi
    else
        log_warn "Production validation script not found. Skipping validation."
    fi
}

# Deploy application
deploy_app() {
    local environment=${1:-"development"}
    
    log_info "Deploying application for ${environment} environment..."
    
    if [ "$environment" = "production" ]; then
        # Validate production environment first
        validate_production
        
        # Production deployment
        docker-compose -f docker-compose.yml up -d
    else
        # Development deployment
        docker-compose -f docker-compose.dev.yml up -d
    fi
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Health check
    if check_health; then
        log_info "Deployment successful! Application is running."
        show_status
    else
        log_error "Deployment failed. Please check logs."
        exit 1
    fi
}

# Health check
check_health() {
    local flask_url="http://localhost:5000"
    local fastapi_url="http://localhost:8000/health"
    
    # Check Flask service
    if curl -f -s "$flask_url" > /dev/null; then
        log_info "Flask service is healthy"
    else
        log_error "Flask service health check failed"
        return 1
    fi
    
    # Check FastAPI service
    if curl -f -s "$fastapi_url" > /dev/null; then
        log_info "FastAPI service is healthy"
    else
        log_error "FastAPI service health check failed"
        return 1
    fi
    
    return 0
}

# Show application status
show_status() {
    log_info "Application Status:"
    echo "===================="
    echo "Flask App: http://localhost:5000"
    echo "FastAPI Docs: http://localhost:8000/docs"
    echo "Health Check: http://localhost:8000/health"
    echo "===================="
    
    log_info "Running containers:"
    docker-compose ps
}

# Stop application
stop_app() {
    log_info "Stopping application..."
    docker-compose down
    log_info "Application stopped."
}

# Update application
update_app() {
    log_info "Updating application..."
    
    # Pull latest changes (if using git)
    if [ -d .git ]; then
        git pull
    fi
    
    # Rebuild and redeploy
    docker-compose down
    docker-compose build --no-cache
    docker-compose up -d
    
    log_info "Application updated."
}

# View logs
view_logs() {
    local service=${1:-""}
    
    if [ -n "$service" ]; then
        docker-compose logs -f "$service"
    else
        docker-compose logs -f
    fi
}

# Backup data
backup_data() {
    local backup_dir="backups/$(date +%Y%m%d_%H%M%S)"
    
    log_info "Creating backup in $backup_dir..."
    
    mkdir -p "$backup_dir"
    
    # Backup database
    if [ -f data/mental_health_app.db ]; then
        cp data/mental_health_app.db "$backup_dir/"
    fi
    
    # Backup user uploads
    if [ -d uploads ]; then
        cp -r uploads "$backup_dir/"
    fi
    
    # Backup chat sessions
    if [ -d chat_sessions ]; then
        cp -r chat_sessions "$backup_dir/"
    fi
    
    log_info "Backup completed: $backup_dir"
}

# Restore data
restore_data() {
    local backup_path=$1
    
    if [ -z "$backup_path" ]; then
        log_error "Please provide backup path"
        exit 1
    fi
    
    if [ ! -d "$backup_path" ]; then
        log_error "Backup path does not exist: $backup_path"
        exit 1
    fi
    
    log_info "Restoring data from $backup_path..."
    
    # Stop application
    docker-compose down
    
    # Restore files
    if [ -f "$backup_path/mental_health_app.db" ]; then
        cp "$backup_path/mental_health_app.db" data/
    fi
    
    if [ -d "$backup_path/uploads" ]; then
        rm -rf uploads
        cp -r "$backup_path/uploads" .
    fi
    
    if [ -d "$backup_path/chat_sessions" ]; then
        rm -rf chat_sessions
        cp -r "$backup_path/chat_sessions" .
    fi
    
    # Start application
    docker-compose up -d
    
    log_info "Data restoration completed."
}

# Show help
show_help() {
    echo "Mental Health App Deployment Script"
    echo "Usage: $0 [COMMAND] [OPTIONS]"
    echo ""
    echo "Commands:"
    echo "  check         Check prerequisites"
    echo "  setup         Setup environment"
    echo "  build         Build application"
    echo "  deploy [env]  Deploy application (env: development|production)"
    echo "  start         Start application"
    echo "  stop          Stop application"
    echo "  restart       Restart application"
    echo "  update        Update and redeploy application"
    echo "  status        Show application status"
    echo "  health        Check application health"
    echo "  logs [service] View logs (service: optional service name)"
    echo "  backup        Backup application data"
    echo "  restore PATH  Restore data from backup"
    echo "  help          Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 deploy production"
    echo "  $0 logs mental-health-app"
    echo "  $0 backup"
    echo "  $0 restore backups/20241205_143000"
}

# Main script
main() {
    case "${1:-help}" in
        check)
            check_prerequisites
            ;;
        setup)
            setup_environment
            ;;
        build)
            check_prerequisites
            setup_environment
            build_app
            ;;
        deploy)
            check_prerequisites
            setup_environment
            build_app
            deploy_app "${2:-development}"
            ;;
        start)
            docker-compose up -d
            show_status
            ;;
        stop)
            stop_app
            ;;
        restart)
            stop_app
            docker-compose up -d
            show_status
            ;;
        update)
            check_prerequisites
            update_app
            ;;
        status)
            show_status
            ;;
        health)
            check_health
            ;;
        logs)
            view_logs "$2"
            ;;
        backup)
            backup_data
            ;;
        restore)
            restore_data "$2"
            ;;
        help|*)
            show_help
            ;;
    esac
}

# Run main function with all arguments
main "$@"
