#!/bin/bash

# sofIA VIVO White-label Deployment Script
# This script deploys sofIA configured exclusively for VIVO customers

echo "🏷️  Deploying sofIA for VIVO White-label..."

# Check if .env.vivo exists
if [ ! -f ".env.vivo" ]; then
    echo "❌ Error: .env.vivo file not found!"
    echo "Please ensure the VIVO environment configuration exists."
    exit 1
fi

# Copy VIVO environment to .env
echo "📋 Configuring VIVO environment..."
cp .env.vivo .env

# Verify Google API key is set
if grep -q "your_google_api_key_here" .env; then
    echo "⚠️  Warning: Please set your actual GOOGLE_API_KEY in .env.vivo"
    echo "   Edit .env.vivo and replace 'your_google_api_key_here' with your actual API key"
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Run tests for VIVO configuration
echo "🧪 Running VIVO-specific tests..."
python -m pytest tests/test_ap2_compliance.py -v

# Start the application
echo "🚀 Starting sofIA VIVO Payment Agent..."
echo "   Brand: VIVO (Purple)"
echo "   Agent: sofIA VIVO Payment Agent"
echo "   Plans: VIVO-specific subscription plans only"
echo ""

# Start with VIVO configuration
python app.py
