#!/bin/bash

# Milam & Greene Shopify Sync - Cloud Scheduler Deployment Script
# Creates a Cloud Scheduler job to trigger the Shopify sync function daily for Milam & Greene tenant

set -e

# Configuration
PROJECT_ID=${GCP_PROJECT_ID:-"auvodka"}
REGION="us-central1"
TIMEZONE="America/New_York"
SCHEDULE="0 0 * * *"  # Daily at midnight EST
TENANT_ID="milam_and_greene"

echo "Deploying Cloud Scheduler job for Milam & Greene Shopify Sync"
echo "Project: $PROJECT_ID"
echo "Region: $REGION"
echo "Schedule: Daily at midnight EST"
echo "Timezone: $TIMEZONE"
echo "Tenant: $TENANT_ID"

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

FUNCTION_NAME="sync-shopify"
JOB_NAME="milam-sync-shopify"

echo ""
echo "Creating scheduler job..."
echo "Job Name: $JOB_NAME"
echo "Function: $FUNCTION_NAME"

# Try to get the function URL
FUNCTION_URL=$(gcloud functions describe "$FUNCTION_NAME" --region="$REGION" --format="value(url)" 2>/dev/null || echo "")

if [ -z "$FUNCTION_URL" ]; then
  FUNCTION_URL="https://${REGION}-${PROJECT_ID}.cloudfunctions.net/${FUNCTION_NAME}"
  echo "Function $FUNCTION_NAME not found. Using expected URL: $FUNCTION_URL"
  echo "Note: The scheduler job will be created but will fail until the function is deployed."
else
  echo "Function URL: $FUNCTION_URL"
fi

# Get default compute service account
PROJECT_NUMBER=$(gcloud projects describe "$PROJECT_ID" --format='value(projectNumber)')
SCHEDULER_SA="${PROJECT_NUMBER}-compute@developer.gserviceaccount.com"

# Verify service account exists
if ! gcloud iam service-accounts describe "$SCHEDULER_SA" &>/dev/null; then
  echo "Error: Default compute service account not found: $SCHEDULER_SA"
  exit 1
fi

# Delete existing job if exists
gcloud scheduler jobs delete "$JOB_NAME" --location="$REGION" --quiet 2>/dev/null || true

# Create the scheduler job with tenant_id in body
echo "Creating scheduler job: $JOB_NAME"
gcloud scheduler jobs create http "$JOB_NAME" \
  --location="$REGION" \
  --schedule="$SCHEDULE" \
  --time-zone="$TIMEZONE" \
  --uri="$FUNCTION_URL" \
  --http-method="POST" \
  --headers="Content-Type=application/json" \
  --message-body="{\"tenant_id\":\"${TENANT_ID}\"}" \
  --oidc-service-account-email="$SCHEDULER_SA" \
  --oidc-token-audience="$FUNCTION_URL" \
  --description="Daily Milam & Greene Shopify sync - runs at midnight EST"

echo "✅ Scheduler job created successfully"
echo ""
echo "Scheduler: $JOB_NAME"
echo "Target: $FUNCTION_URL"
echo "Service Account: $SCHEDULER_SA"
echo "Tenant: $TENANT_ID"

echo ""
echo "To view all scheduler jobs:"
echo "gcloud scheduler jobs list --location=$REGION"
echo ""
echo "To manually trigger the job:"
echo "gcloud scheduler jobs run $JOB_NAME --location=$REGION"
echo ""
echo "To view job logs:"
echo "gcloud scheduler jobs describe $JOB_NAME --location=$REGION"
