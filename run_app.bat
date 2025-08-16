@echo off
echo 🚀 Starting Plano App Setup...

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed. Please install Python first.
    pause
    exit /b 1
)

REM Check if Flutter is installed
flutter --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Flutter is not installed. Please install Flutter first.
    pause
    exit /b 1
)

echo ✅ Prerequisites check passed

REM Step 1: Setup Backend
echo 📦 Step 1: Setting up Python backend...
cd server-plano

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating Python virtual environment...
    python -m venv venv
)

REM Activate virtual environment and install dependencies
call venv\Scripts\activate
echo Installing Python dependencies...
pip install -r requirements.txt

echo ✅ Backend setup complete

REM Step 2: Setup Flutter
echo 📱 Step 2: Setting up Flutter app...
cd ..

REM Get Flutter dependencies
echo Getting Flutter dependencies...
flutter pub get

echo ✅ Flutter setup complete

REM Step 3: Start Backend Server
echo 🖥️  Step 3: Starting backend server...
cd server-plano

echo Starting Python backend server on http://localhost:8000...
call venv\Scripts\activate
start "Backend Server" python main_no_auth.py

echo ✅ Backend server started
echo 📖 API Documentation: http://localhost:8000/docs

REM Wait for server to start
timeout /t 3 /nobreak >nul

REM Step 4: Start Flutter App
echo 📱 Step 4: Starting Flutter app...
cd ..

echo 🎉 Setup complete! Starting Flutter app...
echo.
echo Backend API: http://localhost:8000
echo API Docs: http://localhost:8000/docs
echo.

REM Start Flutter app
flutter run

pause