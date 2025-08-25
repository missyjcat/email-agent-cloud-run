# 🚀 Cloud Run Deployment Guide

This guide explains how to deploy the Email Triage Agent to Google Cloud Run using Artifact Registry.

## 📋 Prerequisites

1. **Google Cloud Project** with billing enabled
2. **gcloud CLI** installed and authenticated
3. **OpenAI API Key** ready

## 🔧 Setup Steps

### 1. **Install and Authenticate gcloud CLI**

```bash
# Install gcloud CLI (if not already installed)
# Visit: https://cloud.google.com/sdk/docs/install

# Authenticate
gcloud auth login
gcloud auth application-default login

# Set your project
gcloud config set project YOUR_PROJECT_ID
```

### 2. **Create OpenAI API Key Secret**

```bash
# Create the secret
gcloud secrets create openai-api-key --replication-policy=automatic

# Add your API key (replace YOUR_API_KEY with actual key)
echo -n 'YOUR_API_KEY' | gcloud secrets versions add openai-api-key --data-file=-
```

### 3. **Enable Required APIs**

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
```

## 🐳 Deployment Options

### Option 1: **Automated Deployment (Recommended)**

Use the provided deployment script:

```bash
# Make script executable
chmod +x deploy.sh

# Run deployment
./deploy.sh
```

The script will:
- Create Artifact Registry repository
- Build and push Docker image
- Deploy to Cloud Run
- Test the deployment

### Option 2: **Manual Deployment**

#### Step 1: Create Artifact Registry Repository

```bash
gcloud artifacts repositories create email-triage-agent \
    --repository-format=docker \
    --location=us-central1 \
    --description="Email Triage Agent Docker images"
```

#### Step 2: Build and Push Docker Image

```bash
# Build the image
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/email-triage-agent/email-triage-agent

# Or build locally and push
docker build -t us-central1-docker.pkg.dev/YOUR_PROJECT_ID/email-triage-agent/email-triage-agent .
docker push us-central1-docker.pkg.dev/YOUR_PROJECT_ID/email-triage-agent/email-triage-agent
```

#### Step 3: Deploy to Cloud Run

```bash
gcloud run deploy email-triage-agent \
    --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/email-triage-agent/email-triage-agent \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --memory 4Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 80 \
    --set-env-vars LANGGRAPH_LOG_LEVEL=INFO,PORT=8080 \
    --set-secrets OPENAI_API_KEY=openai-api-key:latest
```

### Option 3: **Cloud Build (CI/CD)**

Use the provided `cloudbuild.yaml`:

```bash
gcloud builds submit --config cloudbuild.yaml
```

## 🔍 Verification

### Check Service Status

```bash
gcloud run services describe email-triage-agent --region us-central1
```

### Test Health Endpoint

```bash
# Get service URL
SERVICE_URL=$(gcloud run services describe email-triage-agent --region us-central1 --format="value(status.url)")

# Test health endpoint
curl $SERVICE_URL/health
```

### View Logs

```bash
gcloud logs tail --service=email-triage-agent --region=us-central1
```

## 🛠️ Configuration

### Environment Variables

- `PORT`: Port to run on (Cloud Run sets this automatically)
- `OPENAI_API_KEY`: Your OpenAI API key (stored as secret)
- `LANGGRAPH_LOG_LEVEL`: Logging level (default: INFO)

### Resource Limits

- **Memory**: 4Gi
- **CPU**: 2 vCPUs
- **Timeout**: 300 seconds
- **Concurrency**: 80 requests

## 🔒 Security

- **Authentication**: Public (unauthenticated) - change if needed
- **Secrets**: OpenAI API key stored securely in Secret Manager
- **User**: Container runs as non-root user

## 📊 Monitoring

### Cloud Run Metrics

- Request count
- Request latency
- Error rates
- Memory/CPU usage

### Custom Metrics

- Email triage decisions
- Response generation times
- Human approval rates

## 🚨 Troubleshooting

### Common Issues

1. **Container Registry Deprecated Error**
   - Solution: Use Artifact Registry (already configured)

2. **Permission Denied**
   - Solution: Ensure proper IAM roles for Cloud Build and Cloud Run

3. **Image Pull Error**
   - Solution: Check Artifact Registry repository exists and is accessible

4. **Secret Not Found**
   - Solution: Create the `openai-api-key` secret in Secret Manager

### Debug Commands

```bash
# Check service logs
gcloud logs tail --service=email-triage-agent --region=us-central1

# Check build logs
gcloud builds log BUILD_ID

# Check service configuration
gcloud run services describe email-triage-agent --region us-central1
```

## 🔄 Updates

### Update Existing Deployment

```bash
# Build and push new image
gcloud builds submit --tag us-central1-docker.pkg.dev/YOUR_PROJECT_ID/email-triage-agent/email-triage-agent

# Deploy update
gcloud run deploy email-triage-agent \
    --image us-central1-docker.pkg.dev/YOUR_PROJECT_ID/email-triage-agent/email-triage-agent \
    --region us-central1
```

### Rollback

```bash
# List revisions
gcloud run revisions list --service=email-triage-agent --region=us-central1

# Rollback to specific revision
gcloud run services update-traffic email-triage-agent \
    --to-revisions=REVISION_NAME=100 \
    --region=us-central1
```

## 💰 Cost Optimization

- **Memory**: Start with 2Gi, scale up if needed
- **CPU**: Start with 1, scale up if needed
- **Concurrency**: Adjust based on traffic patterns
- **Scaling**: Use min-instances=0 for cost savings

## 📚 Additional Resources

- [Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Artifact Registry Documentation](https://cloud.google.com/artifact-registry/docs)
- [Cloud Build Documentation](https://cloud.google.com/cloud-build/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
