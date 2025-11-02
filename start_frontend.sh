#!/bin/bash

# Start Frontend Script for UAV Log Viewer
# This script sets up and starts the Vue.js frontend

echo "🚀 Starting UAV Log Viewer Frontend..."
echo ""

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo "📦 Installing npm dependencies..."
    npm install
    echo "✅ Dependencies installed"
    echo ""
fi

# Start the development server
echo "🎯 Starting development server..."
echo "🌐 App will be available at: http://localhost:8080"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

npm run dev
