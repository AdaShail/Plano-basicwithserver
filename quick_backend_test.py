#!/usr/bin/env python3
"""
Quick test to verify backend is working without complex dependencies
"""
import sys
import os
sys.path.append('server-plano')

def test_basic_functionality():
    """Test basic backend functionality without external dependencies"""
    print("🧪 Testing Basic Backend Functionality...")
    
    try:
        # Test 1: Import core modules
        from app.utils.service_integration import create_event_with_validation
        print(" Core imports successful")
        
        # Test 2: Create a simple event
        test_event = {
            'event_type': 'wedding',
            'guest_count': 150,
            'venue_type': 'banquet_hall',
            'budget': '50000',
            'start_date': '2024-06-15',
            'duration_days': 3,
            'location': {
                'city': 'Mumbai',
                'state': 'Maharashtra',
                'country': 'India',
                'timezone': 'Asia/Kolkata'
            },
            'budget_tier': 'standard',
            'season': 'winter',
            'cultural_requirements': ['hindu']
        }
        
        result = create_event_with_validation(test_event)
        
        if result['success']:
            print("✅ Event creation successful")
            print(f"   Timeline days: {len(result['timeline'].days)}")
            print(f"   Budget categories: {len(result['budget_allocation'].categories)}")
            print(f"   Total budget: ₹{result['budget_allocation'].total_budget}")
        else:
            print(f"❌ Event creation failed: {result['error']}")
            return False
            
        print("\n🎉 Basic backend functionality is working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_server():
    """Test if the API server can start"""
    print("\n🖥️  Testing API Server...")
    
    try:
        import subprocess
        import time
        import requests
        
        # Start server in background
        print("Starting server...")
        process = subprocess.Popen([
            sys.executable, 'server-plano/main_no_auth.py'
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Wait for server to start
        time.sleep(3)
        
        # Test health endpoint
        try:
            response = requests.get('http://localhost:8000/health', timeout=5)
            if response.status_code == 200:
                print("✅ API server is running and responding")
                print(f"   Response: {response.json()}")
            else:
                print(f"❌ Server responded with status: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ Cannot connect to server: {e}")
        
        # Cleanup
        process.terminate()
        process.wait()
        
        return True
        
    except Exception as e:
        print(f"❌ Server test error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Quick Backend Test\n")
    
    # Test 1: Basic functionality
    basic_ok = test_basic_functionality()
    
    # Test 2: API server (optional)
    if basic_ok:
        print("\n" + "="*50)
        api_ok = test_api_server()
    
    print("\n" + "="*50)
    if basic_ok:
        print("✅ Backend is ready for Flutter app connection!")
        print("\nNext steps:")
        print("1. Start backend: cd server-plano && python main_no_auth.py")
        print("2. Start Flutter: flutter run")
    else:
        print("❌ Backend has issues. Check the errors above.")
        sys.exit(1)