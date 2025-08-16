#!/bin/bash
# Start server in testing mode (no authentication required)

echo "🚀 Starting Event Planner API in TESTING MODE (No Auth)"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔍 Test the API: http://localhost:8000/"
echo "Press Ctrl+C to stop the server"
echo ""

# Activate virtual environment and start server
source venv/bin/activate && python3 main_no_auth.py