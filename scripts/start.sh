#!/bin/bash

# Zalo OA Finance Workflow - Setup & Run Script
# Author: MiniMax Agent

echo "=========================================="
echo "  Zalo OA Finance Workflow Setup"
echo "=========================================="

# Navigate to project directory
cd /workspace/zalo-oa-finance-workflow

# Install Python dependencies
echo "📦 Installing Python dependencies..."
cd backend
pip install -r requirements.txt --quiet

# Go back to root
cd ..

echo "✅ Dependencies installed successfully!"
echo ""
echo "=========================================="
echo "  Starting Server..."
echo "=========================================="
echo ""
echo "🚀 Server will run on: http://localhost:5000"
echo "📝 Default login: admin / admin123"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=========================================="

# Start the server
cd backend
python app.py
