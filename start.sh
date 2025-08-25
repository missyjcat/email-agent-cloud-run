#!/bin/bash

# Email Triage Agent Startup Script

echo "Starting Email Triage Agent..."

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating one..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install/upgrade dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Check if OPENAI_API_KEY is set
if [ -z "$OPENAI_API_KEY" ]; then
    echo "Warning: OPENAI_API_KEY environment variable is not set."
    echo "Please set it before running the application:"
    echo "export OPENAI_API_KEY='your_api_key_here'"
    echo ""
    echo "Or create a .env file with your configuration."
fi

# Start the server
echo "Starting FastAPI server..."
python main.py
