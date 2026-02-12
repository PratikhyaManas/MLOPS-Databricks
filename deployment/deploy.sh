#!/bin/bash
# Optimized deployment script for Databricks MLOps bundle

set -euo pipefail

# Configuration
TARGET=${1:-dev}
RUN_JOB=${2:-}

# Color output  
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Validate environment
validate_env() {
    if [[ -z "${DATABRICKS_HOST:-}" ]]; then
        log_error "DATABRICKS_HOST not set"
        return 1
    fi
    if [[ -z "${DATABRICKS_TOKEN:-}" ]]; then
        log_error "DATABRICKS_TOKEN not set"
        return 1
    fi
}

# Main deployment flow
main() {
    log_info "Starting deployment to target: $TARGET"
    
    # Validate prerequisites
    validate_env || return 1
    command -v databricks &>/dev/null || { log_error "Databricks CLI not found"; return 1; }
    
    # Validate bundle configuration
    log_info "Validating bundle configuration..."
    if ! databricks bundle validate -t "$TARGET"; then
        log_error "Bundle validation failed"
        return 1
    fi
    
    # Deploy bundle
    log_info "Deploying bundle to $TARGET..."
    if ! databricks bundle deploy -t "$TARGET"; then
        log_error "Deployment failed"
        return 1
    fi
    
    log_info "Deployment successful!"
    
    # Optionally run job
    if [[ "$RUN_JOB" == "--run-job" ]]; then
        log_info "Running training job..."
        if ! databricks bundle run ml_training_pipeline -t "$TARGET"; then
            log_warn "Job submission completed with warnings"
        else
            log_info "Job executed successfully"
        fi
    fi
}

# Execute main function
main
