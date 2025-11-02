#!/bin/bash

# Start Backend Script for UAV Log Chatbot
# This script sets up and starts the Python backend

echo "🚀 Starting UAV Log Chatbot Backend..."
echo ""

# Navigate to backend directory
cd backend

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  No .env file found!"
    echo "📝 Creating .env from template..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit backend/.env and add your API keys:"
    echo "   - OPENAI_API_KEY or ANTHROPIC_API_KEY"
    echo ""
    echo "Press Enter to continue after editing .env, or Ctrl+C to exit..."
    read
fi

# Start the server
echo "🎯 Starting FastAPI server..."
echo "📡 API will be available at: http://localhost:8000"
echo "📚 API docs at: http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python main.py
