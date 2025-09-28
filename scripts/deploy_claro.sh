#!/bin/bash

# sofIA CLARO White-label Deployment Script
# This script deploys sofIA configured exclusively for CLARO customers

echo "🏷️  Deploying sofIA for CLARO White-label..."

# Check if .env.claro exists
if [ ! -f ".env.claro" ]; then
    echo "❌ Error: .env.claro file not found!"
    echo "Please ensure the CLARO environment configuration exists."
    exit 1
fi

# Copy CLARO environment to .env
echo "📋 Configuring CLARO environment..."
cp .env.claro .env

# Verify Google API key is set
if grep -q "your_google_api_key_here" .env; then
    echo "⚠️  Warning: Please set your actual GOOGLE_API_KEY in .env.claro"
    echo "   Edit .env.claro and replace 'your_google_api_key_here' with your actual API key"
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Run tests for CLARO configuration
echo "🧪 Running CLARO-specific tests..."
python -m pytest tests/test_ap2_compliance.py -v

# Start the application
echo "🚀 Starting sofIA CLARO Payment Agent..."
echo "   Brand: CLARO (Red)"
echo "   Agent: sofIA CLARO Payment Agent"
echo "   Plans: CLARO-specific subscription plans only"
echo ""

# Start with CLARO configuration
python app.py
