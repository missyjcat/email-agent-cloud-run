#!/bin/bash

# Simple Email Triage Agent Cloud Run Deployment Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID=${PROJECT_ID:-$(gcloud config get-value project)}
REGION=${REGION:-us-central1}
SERVICE_NAME="email-triage-agent"
IMAGE_NAME="$REGION-docker.pkg.dev/$PROJECT_ID/email-triage-agent/$SERVICE_NAME"

echo -e "${GREEN}🚀 Simple Deployment to Cloud Run${NC}"
echo "Project ID: $PROJECT_ID"
echo "Region: $REGION"
echo "Service Name: $SERVICE_NAME"
echo ""

# Check prerequisites
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI is not installed. Please install it first.${NC}"
    exit 1
fi

if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}⚠️  Not authenticated with gcloud. Please run: gcloud auth login${NC}"
    exit 1
fi

# Set project and enable APIs
echo -e "${YELLOW}📋 Setting up project...${NC}"
gcloud config set project $PROJECT_ID

echo -e "${YELLOW}🔧 Enabling required APIs...${NC}"
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com

# Check/create secret
echo -e "${YELLOW}🔐 Checking OpenAI API key secret...${NC}"
if ! gcloud secrets describe openai-api-key &> /dev/null; then
    echo -e "${YELLOW}⚠️  Secret not found. Please create it:${NC}"
    echo "gcloud secrets create openai-api-key --replication-policy=automatic"
    echo "echo -n 'your-api-key-here' | gcloud secrets versions add openai-api-key --data-file=-"
    echo ""
    read -p "Press Enter after creating the secret, or Ctrl+C to cancel..."
fi

# Create Artifact Registry repository
echo -e "${YELLOW}🏗️  Setting up Artifact Registry...${NC}"
if ! gcloud artifacts repositories describe email-triage-agent --location=$REGION &> /dev/null; then
    gcloud artifacts repositories create email-triage-agent \
        --repository-format=docker \
        --location=$REGION \
        --description="Email Triage Agent Docker images"
fi

# Build and deploy
echo -e "${YELLOW}🐳 Building and deploying...${NC}"
gcloud builds submit --tag $IMAGE_NAME

echo -e "${YELLOW}🚀 Deploying to Cloud Run...${NC}"
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars LANGGRAPH_LOG_LEVEL=INFO\
    --set-secrets OPENAI_API_KEY=openai-api-key:latest

# Handle IAM permissions after deployment
echo -e "${YELLOW}🔐 Setting up permissions...${NC}"
CLOUD_RUN_SA="${PROJECT_ID}-compute@developer.gserviceaccount.com"

# Grant secret access (this should work now that the service account exists)
if gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:${CLOUD_RUN_SA}" \
    --role="roles/secretmanager.secretAccessor" 2>/dev/null; then
    echo -e "${GREEN}✅ Permissions set successfully${NC}"
else
    echo -e "${YELLOW}⚠️  Permissions may already be set${NC}"
fi

# Get service URL and test
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)")

echo ""
echo -e "${GREEN}✅ Deployment successful!${NC}"
echo "Service URL: $SERVICE_URL"
echo ""
echo -e "${YELLOW}🧪 Testing deployment...${NC}"

# Wait a moment for the service to be ready
sleep 10

if curl -s "$SERVICE_URL/health" > /dev/null; then
    echo -e "${GREEN}✅ Health check passed!${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed - service may still be starting${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Email Triage Agent deployed!${NC}"
echo "API Endpoints:"
echo "  Health: $SERVICE_URL/health"
echo "  Triage: $SERVICE_URL/triage_email"
echo "  Approve: $SERVICE_URL/triage_email_response"
