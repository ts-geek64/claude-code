#!/bin/bash

# Order Enrichment Cloud Function Deployment Script
# 
# This script deploys the order enrichment function to Google Cloud Functions
# Usage: ./scripts/deploy.sh
# 
# Prerequisites:
# - Google Cloud SDK installed and configured
# - .env file with required environment variables
# - Appropriate GCP project and permissions set up

set -euo pipefail

# Script directory and project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function configuration
FUNCTION_NAME="order-enrichment"
ENTRY_POINT="order_enrichment"
RUNTIME="python312"
REGION="us-central1"
MEMORY="512MB"
TIMEOUT="540s"
TRIGGER="http"

# Change to project root directory
cd "$PROJECT_ROOT"

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "Error: .env file not found in $PROJECT_ROOT"
    echo "Please create a .env file with required environment variables"
    echo "Use .env.example as a template"
    exit 1
fi

# Load environment variables from .env file
echo "Loading environment variables from .env file..."
source .env

# Validate required environment variables
required_vars=(
    "DB_HOST"
    "DB_NAME" 
    "DB_USER"
    "DB_PASSWORD"
    "NEO4J_URI"
    "NEO4J_USERNAME"
    "NEO4J_PASSWORD"
    "FERNET_KEY"
)

for var in "${required_vars[@]}"; do
    if [ -z "${!var:-}" ]; then
        echo "Error: Required environment variable $var is not set"
        exit 1
    fi
done

echo "Environment variables validated successfully"

# Convert .env file to deployment format (exclude comments and empty lines)
ENV_VARS=$(grep -v '^#' .env | grep -v '^$' | xargs | tr ' ' ',')

if [ -z "$ENV_VARS" ]; then
    echo "Error: No valid environment variables found in .env file"
    exit 1
fi

echo "Deploying Cloud Function: $FUNCTION_NAME"
echo "Entry point: $ENTRY_POINT" 
echo "Runtime: $RUNTIME"
echo "Region: $REGION"
echo "Memory: $MEMORY"
echo "Timeout: $TIMEOUT"
echo ""

# Deploy the function
gcloud functions deploy "$FUNCTION_NAME" \
    --gen2 \
    --runtime="$RUNTIME" \
    --region="$REGION" \
    --source=. \
    --entry-point="$ENTRY_POINT" \
    --trigger-http \
    --allow-unauthenticated \
    --memory="$MEMORY" \
    --timeout="$TIMEOUT" \
    --set-env-vars="$ENV_VARS" \
    --max-instances=10 \
    --min-instances=0 \
    --cpu=1

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo ""
    echo "Function details:"
    echo "  Name: $FUNCTION_NAME"
    echo "  Region: $REGION"
    echo "  Trigger: HTTPS"
    echo ""
    
    # Get function URL
    FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" --region="$REGION" --format="value(serviceConfig.uri)")
    echo "Function URL: $FUNCTION_URL"
    echo ""
    echo "Test the function with:"
    echo "curl -X POST \"$FUNCTION_URL\" \\"
    echo "  -H \"Content-Type: application/json\" \\"
    echo "  -d '{\"tenant_id\": \"au_vodka\", \"year\": 2025, \"month\": 9}'"
else
    echo ""
    echo "❌ Deployment failed!"
    exit 1
fi