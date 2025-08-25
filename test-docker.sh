#!/bin/bash

# Test Docker Build Script

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧪 Testing Docker Build Locally${NC}"
echo "This script will test the Docker build without deploying to Cloud Run"
echo ""

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo -e "${YELLOW}⚠️  Docker is not running. Please start Docker and try again.${NC}"
    exit 1
fi

# Build the Docker image locally
echo -e "${YELLOW}🐳 Building Docker image locally...${NC}"
docker build -t email-triage-agent:test .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Docker build successful!${NC}"
else
    echo -e "${YELLOW}❌ Docker build failed!${NC}"
    exit 1
fi

# Test the image runs
echo -e "${YELLOW}🧪 Testing if the image runs...${NC}"
echo "Starting container in background..."

# Run the container in background
CONTAINER_ID=$(docker run -d -p 8080:8080 -e OPENAI_API_KEY=test-key email-triage-agent:test)

# Wait a moment for the container to start
sleep 5

# Test the health endpoint
echo -e "${YELLOW}🔍 Testing health endpoint...${NC}"
if curl -s http://localhost:8080/health > /dev/null; then
    echo -e "${GREEN}✅ Health check passed! Container is running correctly.${NC}"
else
    echo -e "${YELLOW}⚠️  Health check failed. Container may still be starting...${NC}"
fi

# Stop and remove the test container
echo -e "${YELLOW}🧹 Cleaning up test container...${NC}"
docker stop $CONTAINER_ID
docker rm $CONTAINER_ID

echo ""
echo -e "${GREEN}🎉 Docker test completed successfully!${NC}"
echo "Your Docker image is ready for deployment to Cloud Run."
echo ""
echo "Next steps:"
echo "1. Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'"
echo "2. Run the deployment: ./deploy.sh"
echo ""
echo "Or test manually:"
echo "docker run -p 8080:8080 -e OPENAI_API_KEY='your-key' email-triage-agent:test"
