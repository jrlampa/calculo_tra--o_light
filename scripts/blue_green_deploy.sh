#!/bin/bash
# Blue-Green Deployment Script for calculo_tração_light
# This script implements blue-green deployment strategy for zero-downtime deployments

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$(dirname "$SCRIPT_DIR")")"
ENVIRONMENT="${ENVIRONMENT:-production}"
DEPLOYMENT_TYPE="${DEPLOYMENT_TYPE:-blue-green}"
HEALTH_CHECK_TIMEOUT=300
HEALTH_CHECK_INTERVAL=10

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration loading
load_config() {
    local config_file="$1"
    if [[ -f "$config_file" ]]; then
        source "$config_file"
        log_info "Configuration loaded from $config_file"
    else
        log_error "Configuration file not found: $config_file"
        exit 1
    fi
}

# Health check function
health_check() {
    local url="$1"
    local timeout="$2"
    local interval="$3"
    local start_time=$(date +%s)
    
    log_info "Starting health check for $url"
    
    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))
        
        if [[ $elapsed -gt $timeout ]]; then
            log_error "Health check timeout after ${timeout}s"
            return 1
        fi
        
        if curl -f -s "$url" > /dev/null 2>&1; then
            log_success "Health check passed for $url"
            return 0
        fi
        
        log_info "Health check failed, retrying in ${interval}s... (${elapsed}s elapsed)"
        sleep $interval
    done
}

# Database backup function
backup_database() {
    local backup_name="backup_$(date +%Y%m%d_%H%M%S)"
    local backup_dir="/tmp/backups"
    
    mkdir -p "$backup_dir"
    
    log_info "Creating database backup: $backup_name"
    
    if pg_dump "$DATABASE_URL" > "$backup_dir/$backup_name.sql"; then
        log_success "Database backup created: $backup_dir/$backup_name.sql"
        echo "$backup_dir/$backup_name.sql"
    else
        log_error "Database backup failed"
        return 1
    fi
}

# Blue-Green deployment strategy
deploy_blue_green() {
    local current_env="$1"
    local target_env="$2"
    local app_version="$3"
    
    log_info "Starting blue-green deployment"
    log_info "Current environment: $current_env"
    log_info "Target environment: $target_env"
    log_info "Application version: $app_version"
    
    # 1. Prepare target environment
    log_info "Preparing target environment: $target_env"
    
    # Stop target environment if running
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "${target_env}" down || true
    
    # Update environment variables for target environment
    export COMPOSE_PROJECT_NAME="${target_env}"
    export APP_VERSION="$app_version"
    export APP_ENV="$target_env"
    
    # 2. Deploy to target environment
    log_info "Deploying to target environment: $target_env"
    
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "${target_env}" up -d
    
    # 3. Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # 4. Health check target environment
    local health_url="http://localhost:808${target_env: -1}/health"
    if ! health_check "$health_url" "$HEALTH_CHECK_TIMEOUT" "$HEALTH_CHECK_INTERVAL"; then
        log_error "Target environment health check failed"
        
        # Rollback: stop target environment
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "${target_env}" down
        
        # Restart current environment
        export COMPOSE_PROJECT_NAME="${current_env}"
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "${current_env}" up -d
        
        return 1
    fi
    
    # 5. Run smoke tests
    log_info "Running smoke tests on target environment"
    if ! run_smoke_tests "$target_env"; then
        log_error "Smoke tests failed"
        
        # Rollback
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "${target_env}" down
        export COMPOSE_PROJECT_NAME="${current_env}"
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "${current_env}" up -d
        
        return 1
    fi
    
    # 6. Switch traffic (update load balancer configuration)
    log_info "Switching traffic to target environment: $target_env"
    update_load_balancer "$target_env"
    
    # 7. Monitor for issues
    log_info "Monitoring target environment for issues..."
    sleep 60
    
    # 8. Cleanup old environment
    log_info "Cleaning up old environment: $current_env"
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "${current_env}" down
    
    log_success "Blue-green deployment completed successfully"
}

# Rolling deployment strategy
deploy_rolling() {
    local app_version="$1"
    local instances="${INSTANCES:-3}"
    
    log_info "Starting rolling deployment"
    log_info "Application version: $app_version"
    log_info "Number of instances: $instances"
    
    # Backup database
    local backup_file
    backup_file=$(backup_database)
    
    # Deploy to each instance one by one
    for i in $(seq 1 $instances); do
        log_info "Deploying to instance $i"
        
        # Stop instance
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "app_instance_$i" stop app
        
        # Update image
        export APP_VERSION="$app_version"
        export INSTANCE_ID="$i"
        
        # Start instance with new version
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "app_instance_$i" up -d app
        
        # Health check
        local health_url="http://localhost:808$i/health"
        if ! health_check "$health_url" 120 5; then
            log_error "Instance $i health check failed"
            
            # Rollback this instance
            export APP_VERSION="$CURRENT_VERSION"
            docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "app_instance_$i" up -d app
            
            # Restore database if this is the first failed instance
            if [[ $i -eq 1 ]]; then
                restore_database "$backup_file"
            fi
            
            return 1
        fi
        
        log_success "Instance $i deployed successfully"
        sleep 10
    done
    
    log_success "Rolling deployment completed successfully"
}

# Canary deployment strategy
deploy_canary() {
    local app_version="$1"
    local canary_percentage="${CANARY_PERCENTAGE:-10}"
    
    log_info "Starting canary deployment"
    log_info "Application version: $app_version"
    log_info "Canary percentage: $canary_percentage%"
    
    # Deploy canary instance
    log_info "Deploying canary instance"
    export COMPOSE_PROJECT_NAME="canary"
    export APP_VERSION="$app_version"
    export CANARY=true
    
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "canary" up -d
    
    # Health check canary
    if ! health_check "http://localhost:8090/health" 120 5; then
        log_error "Canary health check failed"
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "canary" down
        return 1
    fi
    
    # Update load balancer to route canary traffic
    update_load_balancer "canary" "$canary_percentage"
    
    # Monitor canary metrics
    log_info "Monitoring canary metrics for 10 minutes..."
    sleep 600
    
    if check_canary_metrics; then
        log_success "Canary metrics are healthy, promoting to full deployment"
        deploy_blue_green "production" "green" "$app_version"
    else
        log_error "Canary metrics indicate issues, rolling back"
        docker-compose -f "$PROJECT_ROOT/docker-compose.yml" -p "canary" down
        return 1
    fi
}

# Helper functions
run_smoke_tests() {
    local environment="$1"
    local test_url="http://localhost:808${environment: -1}"
    
    log_info "Running smoke tests on $environment"
    
    # Test basic endpoints
    local endpoints=(
        "/health"
        "/api/v1/status"
        "/api/v1/version"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if ! curl -f -s "$test_url$endpoint" > /dev/null; then
            log_error "Smoke test failed for endpoint: $endpoint"
            return 1
        fi
        log_info "Smoke test passed for endpoint: $endpoint"
    done
    
    log_success "All smoke tests passed"
    return 0
}

update_load_balancer() {
    local target_env="$1"
    local percentage="${2:-100}"
    
    log_info "Updating load balancer configuration"
    
    # Update nginx configuration
    cat > "/tmp/nginx_upstream.conf" << EOF
upstream app_backend {
    least_conn;
    server app_${target_env}:8000 max_fails=3 fail_timeout=30s;
    # Add other instances if needed for rolling deployment
}

server {
    listen 80;
    server_name localhost;
    
    location / {
        proxy_pass http://app_backend;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF
    
    # Reload nginx
    docker exec nginx_container nginx -s reload
    
    log_success "Load balancer updated for $target_env"
}

check_canary_metrics() {
    log_info "Checking canary metrics"
    
    # Check error rate
    local error_rate
    error_rate=$(curl -s "http://localhost:9090/api/v1/query?query=rate(http_requests_total{status=~\"5..\"}[5m])" | jq -r '.data.result[0].value[1] // "0"')
    
    if (( $(echo "$error_rate > 0.05" | bc -l) )); then
        log_error "Canary error rate too high: $error_rate"
        return 1
    fi
    
    # Check response time
    local response_time
    response_time=$(curl -s "http://localhost:9090/api/v1/query?query=histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))" | jq -r '.data.result[0].value[1] // "0"')
    
    if (( $(echo "$response_time > 1.0" | bc -l) )); then
        log_error "Canary response time too high: $response_time"
        return 1
    fi
    
    log_success "Canary metrics are within acceptable ranges"
    return 0
}

restore_database() {
    local backup_file="$1"
    
    log_info "Restoring database from backup: $backup_file"
    
    if [[ -f "$backup_file" ]]; then
        if psql "$DATABASE_URL" < "$backup_file"; then
            log_success "Database restored successfully"
        else
            log_error "Database restore failed"
            return 1
        fi
    else
        log_error "Backup file not found: $backup_file"
        return 1
    fi
}

# Main deployment function
main() {
    local app_version="${1:-latest}"
    local deployment_strategy="${DEPLOYMENT_STRATEGY:-blue-green}"
    
    log_info "Starting deployment process"
    log_info "Application version: $app_version"
    log_info "Deployment strategy: $deployment_strategy"
    log_info "Environment: $ENVIRONMENT"
    
    # Load configuration
    load_config "$PROJECT_ROOT/.env"
    
    # Pre-deployment checks
    log_info "Running pre-deployment checks"
    
    # Check if Docker is running
    if ! docker info > /dev/null 2>&1; then
        log_error "Docker is not running"
        exit 1
    fi
    
    # Check if required environment variables are set
    if [[ -z "${DATABASE_URL:-}" ]] || [[ -z "${REDIS_URL:-}" ]]; then
        log_error "Required environment variables not set"
        exit 1
    fi
    
    # Execute deployment strategy
    case "$deployment_strategy" in
        "blue-green")
            deploy_blue_green "blue" "green" "$app_version"
            ;;
        "rolling")
            deploy_rolling "$app_version"
            ;;
        "canary")
            deploy_canary "$app_version"
            ;;
        *)
            log_error "Unknown deployment strategy: $deployment_strategy"
            exit 1
            ;;
    esac
    
    log_success "Deployment completed successfully"
}

# Script entry point
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi