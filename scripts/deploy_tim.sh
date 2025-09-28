#!/bin/bash

# sofIA TIM White-label Deployment Script
# This script deploys sofIA configured exclusively for TIM customers

echo "🏷️  Deploying sofIA for TIM White-label..."

# Check if .env.tim exists
if [ ! -f ".env.tim" ]; then
    echo "❌ Error: .env.tim file not found!"
    echo "Please ensure the TIM environment configuration exists."
    exit 1
fi

# Copy TIM environment to .env
echo "📋 Configuring TIM environment..."
cp .env.tim .env

# Verify Google API key is set
if grep -q "your_google_api_key_here" .env; then
    echo "⚠️  Warning: Please set your actual GOOGLE_API_KEY in .env.tim"
    echo "   Edit .env.tim and replace 'your_google_api_key_here' with your actual API key"
fi

# Install dependencies
echo "📦 Installing dependencies..."
uv sync

# Run tests for TIM configuration
echo "🧪 Running TIM-specific tests..."
python -m pytest tests/test_ap2_compliance.py -v

# Start the application
echo "🚀 Starting sofIA TIM Payment Agent..."
echo "   Brand: TIM (Blue)"
echo "   Agent: sofIA TIM Payment Agent"
echo "   Plans: TIM-specific subscription plans only"
echo ""

# Start with TIM configuration
python app.py
