#!/bin/bash
# Deployment script for Databricks MLOps bundle

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

# Parameters
TARGET=${1:-dev}

echo "Deploying to target: $TARGET"

# Validate bundle
echo "Validating bundle..."
databricks bundle validate -t $TARGET

if [ $? -ne 0 ]; then
    echo "${RED}Bundle validation failed!${NC}"
    exit 1
fi

# Deploy bundle
echo "Deploying bundle..."
databricks bundle deploy -t $TARGET

if [ $? -ne 0 ]; then
    echo "${RED}Deployment failed!${NC}"
    exit 1
fi

echo "${GREEN}Deployment successful!${NC}"

# Optionally run a job
if [ "$2" == "--run-job" ]; then
    echo "Running training job..."
    databricks bundle run ml_training_pipeline -t $TARGET
fi
