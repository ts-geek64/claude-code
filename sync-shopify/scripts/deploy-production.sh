#!/bin/bash

# AU Vodka Shopify to Neo4j Sync - Production Deployment Script
# This script deploys the AU Vodka Shopify-Neo4j sync function to Google Cloud Functions

set -e  # Exit on error

# Production Configuration for AU Vodka
PROJECT_ID=${GCP_PROJECT_ID:-"auvodka"}
REGION="us-central1"
FUNCTION_NAME="sync-shopify"
RUNTIME="python310"
MEMORY="512MB"
CPU="1"
TIMEOUT="3600s"
ENV_SUFFIX="prod"

echo "Deploying AU Vodka Shopify-Neo4j Sync to Production Environment"
echo "Function: $FUNCTION_NAME"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Environment: Production"

# Check for GCP authentication
if ! gcloud auth list 2>&1 | grep -q 'ACTIVE'; then
  echo "Error: Not authenticated with Google Cloud. Please run 'gcloud auth login' first."
  exit 1
fi

# Check if the project exists
if ! gcloud projects describe "$PROJECT_ID" &>/dev/null; then
  echo "Error: Project $PROJECT_ID does not exist or you don't have access to it."
  exit 1
fi

# Set the GCP project
gcloud config set project "$PROJECT_ID"
echo "Set active project to $PROJECT_ID"

# Clean up deployment files
echo "Cleaning up deployment files..."
if [ -f "./.gcloudignore" ]; then
  echo "Using existing .gcloudignore file"
else
  echo "Creating .gcloudignore file"
  cat > .gcloudignore << EOL
.gcloudignore
.git
.gitignore
__pycache__/
tests/
venv/
.pytest_cache/
.env
deploy.sh
deploy-staging.sh
scripts/
*.log
logs/
EOL
fi

# Create secrets configuration for AU Vodka production
echo "Creating secrets configuration for AU Vodka production..."

SECRETS="DB_HOST=production_postgres_host:latest"
SECRETS="$SECRETS,DB_PORT=production_postgres_port:latest"
SECRETS="$SECRETS,DB_NAME=production_postgres_database:latest"
SECRETS="$SECRETS,DB_USER=production_postgres_user:latest"
SECRETS="$SECRETS,DB_PASSWORD=production_postgres_password:latest"
SECRETS="$SECRETS,FERNET_KEY=fernet_secret_key:latest"

# Create environment variables string
ENV_VARS="DB_POOL_MIN=2"
ENV_VARS="$ENV_VARS,DB_POOL_MAX=10"
ENV_VARS="$ENV_VARS,SHOPIFY_BATCH_SIZE=250"
ENV_VARS="$ENV_VARS,SHOPIFY_REQUEST_TIMEOUT=60"

# Retry & Rate Limiting
ENV_VARS="$ENV_VARS,MAX_RETRIES=3"
ENV_VARS="$ENV_VARS,INITIAL_BACKOFF=1.0"
ENV_VARS="$ENV_VARS,MAX_BACKOFF=60.0"

# Logging
ENV_VARS="$ENV_VARS,LOG_LEVEL=INFO"

# Deploy the function
echo "Deploying AU Vodka production function..."
gcloud functions deploy "$FUNCTION_NAME" \
  --gen2 \
  --region="$REGION" \
  --runtime="$RUNTIME" \
  --memory="$MEMORY" \
  --timeout="$TIMEOUT" \
  --entry-point="sync_shopify" \
  --trigger-http \
  --allow-unauthenticated \
  --set-env-vars="$ENV_VARS" \
  --set-secrets="$SECRETS" \
  --cpu="$CPU"

# Attach Cloud SQL to the underlying Cloud Run service
CLOUD_SQL_INSTANCE="auvodka:us-central1:omnigrowthos"
echo "Attaching Cloud SQL instance to Cloud Run service..."
gcloud run services update "$FUNCTION_NAME" \
  --region="$REGION" \
  --add-cloudsql-instances="$CLOUD_SQL_INSTANCE" \
  --quiet

echo "✅ Cloud SQL instance attached to Cloud Run service."

# Get Cloud Functions URL
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" --region="$REGION" --format="value(url)")
echo "Function URL: $FUNCTION_URL"

echo ""
echo "✅ AU Vodka Production Shopify Sync Function deployed successfully!"
echo "Function URL: $FUNCTION_URL"

# Get default compute service account
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
SCHEDULER_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Verify service account exists
if ! gcloud iam service-accounts describe "$SCHEDULER_SA" &>/dev/null; then
  echo "Error: Default compute service account not found: $SCHEDULER_SA"
  exit 1
fi

echo "Using service account: $SCHEDULER_SA"

# Grant invoker permission on underlying Cloud Run service
gcloud run services add-iam-policy-binding "$FUNCTION_NAME" \
  --region="$REGION" \
  --member="serviceAccount:${SCHEDULER_SA}" \
  --role="roles/run.invoker" \
  --platform=managed \
  --quiet 

echo "✅ Permission granted to scheduler service account for Cloud Run service."