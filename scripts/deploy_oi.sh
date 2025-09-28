#!/bin/bash

# sofIA OI White-label Deployment Script
# This script deploys sofIA configured exclusively for OI customers

echo "🏷️  Deploying sofIA for OI White-label..."

# Check if .env.oi exists
if [ ! -f ".env.oi" ]; then
    echo "❌ Error: .env.oi file not found!"
    echo "Please ensure the OI environment configuration exists."
    exit 1
fi

# Copy OI environment to .env
echo "📋 Configuring OI environment..."
cp .env.oi .env

# Verify Google API key is set
if grep -q "your_google_api_key_here" .env; then
    echo "⚠️  Warning: Please set your actual GOOGLE_API_KEY in .env.oi"
    echo "   Edit .env.oi and replace 'your_google_api_key_here' with your actual API key"
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Run tests for OI configuration
echo "🧪 Running OI-specific tests..."
python -m pytest tests/test_ap2_compliance.py -v

# Start the application
echo "🚀 Starting sofIA OI Payment Agent..."
echo "   Brand: OI (Yellow)"
echo "   Agent: sofIA OI Payment Agent"
echo "   Plans: OI-specific subscription plans only"
echo ""

# Start with OI configuration
python app.py
