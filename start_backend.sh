#!/bin/bash

echo "🚀 Starting Plano Backend Server"

# Navigate to server directory
cd server-plano

# Activate virtual environment
if [ -f "venv/bin/activate" ]; then
    echo "📦 Activating virtual environment..."
    source venv/bin/activate
else
    echo "❌ Virtual environment not found. Creating one..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Installing dependencies..."
    pip install -r requirements.txt
fi

# Check if FastAPI is installed
python3 -c "import fastapi" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Installing FastAPI..."
    pip install fastapi uvicorn
fi

echo "🔑 Testing API keys..."
python3 test_api_keys.py

echo ""
echo "🖥️  Starting server on http://localhost:8000"
echo "🛑 Press Ctrl+C to stop"
echo "=" * 50

# Check if Gemini API key is set for real AI
if grep -q "GEMINI_API_KEY=AIza" .env 2>/dev/null; then
    echo "🤖 Starting with REAL AI intelligence..."
    python3 main_no_auth.py
else
    echo "🎭 Starting with MOCK AI (get Gemini API key for real intelligence)..."
    python3 test_server.py
fi