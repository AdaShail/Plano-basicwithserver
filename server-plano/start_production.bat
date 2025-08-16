@echo off
REM Start server in production mode (full authentication required)

echo 🚀 Starting Event Planner API in PRODUCTION MODE (Full Auth)
echo 📖 API Documentation: http://localhost:8000/docs
echo 🔐 Authentication required for all endpoints
echo Press Ctrl+C to stop the server
echo.

REM Activate virtual environment and start server
call venv\Scripts\activate && python main.py