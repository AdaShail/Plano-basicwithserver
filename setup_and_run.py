#!/usr/bin/env python3
"""
Complete setup and run script for Plano App
Handles backend setup, dependency installation, and app startup
"""
import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=check, 
                              capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.CalledProcessError as e:
        return False, e.stdout, e.stderr

def check_prerequisites():
    """Check if required tools are installed"""
    print("🔍 Checking prerequisites...")
    
    # Check Python
    success, stdout, stderr = run_command("python3 --version", check=False)
    if not success:
        print("❌ Python 3 is not installed")
        return False
    print(f"✅ Python: {stdout.strip()}")
    
    # Check Flutter
    success, stdout, stderr = run_command("flutter --version", check=False)
    if not success:
        print("❌ Flutter is not installed")
        return False
    print("✅ Flutter is installed")
    
    return True

def setup_backend():
    """Setup Python backend environment"""
    print("\n📦 Setting up backend...")
    
    backend_dir = Path("server-plano")
    if not backend_dir.exists():
        print("❌ server-plano directory not found")
        return False
    
    # Create virtual environment
    venv_dir = backend_dir / "venv"
    if not venv_dir.exists():
        print("Creating Python virtual environment...")
        success, stdout, stderr = run_command("python3 -m venv venv", cwd=backend_dir)
        if not success:
            print(f"❌ Failed to create venv: {stderr}")
            return False
    
    # Install dependencies
    print("Installing Python dependencies...")
    if os.name == 'nt':  # Windows
        pip_cmd = "venv\\Scripts\\pip install -r requirements.txt"
    else:  # Unix/Linux/macOS
        pip_cmd = "venv/bin/pip install -r requirements.txt"
    
    success, stdout, stderr = run_command(pip_cmd, cwd=backend_dir)
    if not success:
        print(f"❌ Failed to install dependencies: {stderr}")
        return False
    
    print("✅ Backend setup complete")
    return True

def setup_flutter():
    """Setup Flutter dependencies"""
    print("\n📱 Setting up Flutter...")
    
    # Get Flutter dependencies
    success, stdout, stderr = run_command("flutter pub get")
    if not success:
        print(f"❌ Failed to get Flutter dependencies: {stderr}")
        return False
    
    print("✅ Flutter setup complete")
    return True

def start_backend():
    """Start the backend server"""
    print("\n🖥️  Starting backend server...")
    
    backend_dir = Path("server-plano")
    
    # Start server
    if os.name == 'nt':  # Windows
        python_cmd = "venv\\Scripts\\python"
    else:  # Unix/Linux/macOS
        python_cmd = "venv/bin/python"
    
    cmd = f"{python_cmd} main_no_auth.py"
    
    try:
        process = subprocess.Popen(cmd, shell=True, cwd=backend_dir)
        
        # Wait for server to start
        print("Waiting for server to start...")
        time.sleep(5)
        
        # Test if server is running
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend server is running on http://localhost:8000")
                return process
            else:
                print(f"❌ Server health check failed: {response.status_code}")
                process.terminate()
                return None
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
            process.terminate()
            return None
            
    except Exception as e:
        print(f"❌ Failed to start server: {e}")
        return None

def test_backend():
    """Test backend functionality"""
    print("\n🧪 Testing backend...")
    
    try:
        # Test health endpoint
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code != 200:
            print(f"❌ Health check failed: {response.status_code}")
            return False
        
        # Test event creation
        test_event = {
            "event_type": "birthday",
            "start_date": "2024-06-15",
            "location": "Mumbai, India",
            "budget": 25000
        }
        
        response = requests.post(
            "http://localhost:8000/plan-event",
            json=test_event,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Backend test successful")
            print(f"   Timeline: {len(data.get('timeline', []))} days")
            print(f"   Budget: ₹{data.get('estimated_budget', 'N/A')}")
            return True
        else:
            print(f"❌ Event creation test failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Backend test error: {e}")
        return False

def start_flutter():
    """Start Flutter app"""
    print("\n📱 Starting Flutter app...")
    print("Choose your platform:")
    print("1. Desktop (recommended for development)")
    print("2. Android emulator")
    print("3. iOS simulator")
    print("4. Web browser")
    
    choice = input("Enter choice (1-4) or press Enter for desktop: ").strip()
    
    if choice == "2":
        cmd = "flutter run -d android"
    elif choice == "3":
        cmd = "flutter run -d ios"
    elif choice == "4":
        cmd = "flutter run -d web-server --web-port 3000"
    else:
        cmd = "flutter run -d desktop"
    
    print(f"Running: {cmd}")
    
    try:
        # Run Flutter in foreground
        subprocess.run(cmd, shell=True, check=True)
    except KeyboardInterrupt:
        print("\n🛑 Flutter app stopped by user")
    except subprocess.CalledProcessError as e:
        print(f"❌ Flutter app failed: {e}")

def main():
    """Main setup and run function"""
    print("🚀 Plano App - Complete Setup and Run")
    print("=" * 50)
    
    # Step 1: Check prerequisites
    if not check_prerequisites():
        print("\n❌ Prerequisites check failed. Please install missing tools.")
        sys.exit(1)
    
    # Step 2: Setup backend
    if not setup_backend():
        print("\n❌ Backend setup failed.")
        sys.exit(1)
    
    # Step 3: Setup Flutter
    if not setup_flutter():
        print("\n❌ Flutter setup failed.")
        sys.exit(1)
    
    # Step 4: Start backend
    backend_process = start_backend()
    if not backend_process:
        print("\n❌ Failed to start backend server.")
        sys.exit(1)
    
    # Step 5: Test backend
    if not test_backend():
        print("\n⚠️  Backend tests failed, but continuing...")
    
    try:
        # Step 6: Start Flutter
        print("\n🎉 Setup complete! Starting Flutter app...")
        print("\nBackend API: http://localhost:8000")
        print("API Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop both backend and Flutter app")
        
        start_flutter()
        
    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        if backend_process:
            backend_process.terminate()
            backend_process.wait()
        print("✅ Backend server stopped")

if __name__ == "__main__":
    main()