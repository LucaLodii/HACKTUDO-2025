#!/bin/bash

# sofIA WhatsApp Bridge Startup Script
# This script starts the WhatsApp Web.js bridge for the sofIA payment agent

echo "🚀 Starting sofIA WhatsApp Bridge..."
echo "📱 Setting up WhatsApp Web.js integration"
echo "=" * 50

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 16+ and try again."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm and try again."
    exit 1
fi

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing Node.js dependencies..."
    npm install

    if [ $? -ne 0 ]; then
        echo "❌ Failed to install dependencies. Please check your npm configuration."
        exit 1
    fi
fi

# Set environment variables if not already set
export PORT=${PORT:-3001}
export SOFIA_API_URL=${SOFIA_API_URL:-"http://localhost:8000"}

echo "🔧 Configuration:"
echo "   Bridge Port: $PORT"
echo "   sofIA API URL: $SOFIA_API_URL"
echo ""

echo "📱 Starting WhatsApp Web.js bridge..."
echo "⏳ Please wait for QR code to appear..."
echo ""
echo "📋 Instructions:"
echo "   1. Wait for QR code to appear below"
echo "   2. Open WhatsApp on your phone"
echo "   3. Go to Settings > Linked Devices > Link a Device"
echo "   4. Scan the QR code that appears"
echo "   5. Wait for 'WhatsApp client is ready!' message"
echo ""

# Start the bridge
node server.js