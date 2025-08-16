@echo off
REM Start server in testing mode (no authentication required)

echo 🚀 Starting Event Planner API in TESTING MODE (No Auth)
echo 📖 API Documentation: http://localhost:8000/docs
echo 🔍 Test the API: http://localhost:8000/
echo Press Ctrl+C to stop the server
echo.

REM Activate virtual environment and start server
call venv\Scripts\activate && python main_no_auth.py