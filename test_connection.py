#!/usr/bin/env python3
"""
Simple script to test if the backend is running and responding correctly.
"""
import requests
import json
import sys

def test_backend():
    base_url = "http://localhost:8000"
    
    print("🧪 Testing Plano Backend Connection...")
    
    # Test 1: Health check
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Health check passed")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to backend: {e}")
        print("   Make sure the backend server is running on http://localhost:8000")
        return False
    
    # Test 2: Root endpoint
    try:
        response = requests.get(f"{base_url}/", timeout=5)
        if response.status_code == 200:
            print("✅ Root endpoint accessible")
        else:
            print(f"⚠️  Root endpoint returned: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"⚠️  Root endpoint error: {e}")
    
    # Test 3: Test event creation
    test_event = {
        "event_type": "wedding",
        "start_date": "2024-06-15",
        "end_date": "2024-06-17",
        "location": "Mumbai, India",
        "budget": 50000,
        "religion": "hindu"
    }
    
    try:
        response = requests.post(
            f"{base_url}/plan-event",
            json=test_event,
            timeout=30
        )
        if response.status_code == 200:
            print("✅ Event creation test passed")
            data = response.json()
            print(f"   Generated timeline with {len(data.get('timeline', []))} days")
            print(f"   Estimated budget: ₹{data.get('estimated_budget', 'N/A')}")
        else:
            print(f"❌ Event creation test failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Event creation test error: {e}")
        return False
    
    print("\n🎉 All tests passed! Backend is working correctly.")
    print("📱 You can now start the Flutter app.")
    return True

if __name__ == "__main__":
    success = test_backend()
    sys.exit(0 if success else 1)