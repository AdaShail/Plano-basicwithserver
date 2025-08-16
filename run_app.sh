#!/bin/bash

# Plano App - Complete Setup and Run Script
echo "🚀 Starting Plano App Setup..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Check if Flutter is installed
if ! command -v flutter &> /dev/null; then
    echo "❌ Flutter is not installed. Please install Flutter first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Step 1: Setup Backend
echo "📦 Step 1: Setting up Python backend..."
cd server-plano

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "✅ Backend setup complete"

# Step 2: Setup Flutter
echo "📱 Step 2: Setting up Flutter app..."
cd ..

# Get Flutter dependencies
echo "Getting Flutter dependencies..."
flutter pub get

echo "✅ Flutter setup complete"

# Step 3: Start Backend Server
echo "🖥️  Step 3: Starting backend server..."
cd server-plano

# Start the server in background
echo "Starting Python backend server on http://localhost:8000..."
source venv/bin/activate
python main_no_auth.py &
BACKEND_PID=$!

echo "✅ Backend server started (PID: $BACKEND_PID)"
echo "📖 API Documentation: http://localhost:8000/docs"

# Wait for server to start
sleep 3

# Step 4: Start Flutter App
echo "📱 Step 4: Starting Flutter app..."
cd ..

echo "🎉 Setup complete! Starting Flutter app..."
echo ""
echo "Backend API: http://localhost:8000"
echo "API Docs: http://localhost:8000/docs"
echo ""

# Start Flutter app
flutter run

# Cleanup when Flutter app stops
echo "🧹 Cleaning up..."
kill $BACKEND_PID 2>/dev/null
echo "✅ Backend server stopped"