#!/bin/bash
# Start server in production mode (full authentication required)

echo "🚀 Starting Event Planner API in PRODUCTION MODE (Full Auth)"
echo "📖 API Documentation: http://localhost:8000/docs"
echo "🔐 Authentication required for all endpoints"
echo "Press Ctrl+C to stop the server"
echo ""

# Activate virtual environment and start server
source venv/bin/activate && python3 main.py