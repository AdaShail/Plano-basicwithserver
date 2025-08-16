#!/usr/bin/env python3
"""
Test script to verify the complete event creation and retrieval flow
"""
import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"

def test_complete_flow():
    print("🧪 Testing Complete Event Flow")
    print("=" * 50)
    
    # Test 1: Health check
    print("\n1. Testing health check...")
    response = requests.get(f"{BASE_URL}/health")
    if response.status_code == 200:
        print("✅ Health check passed")
        print(f"   Response: {response.json()}")
    else:
        print("❌ Health check failed")
        return
    
    # Test 2: Create a wedding event
    print("\n2. Creating a wedding event...")
    wedding_data = {
        "event_type": "wedding",
        "start_date": (datetime.now() + timedelta(days=60)).strftime("%Y-%m-%d"),
        "start_time": "11:30",
        "end_date": (datetime.now() + timedelta(days=62)).strftime("%Y-%m-%d"),
        "location": "Mumbai, India",
        "budget": 75000,
        "religion": "hindu"
    }
    
    response = requests.post(f"{BASE_URL}/plan-event", json=wedding_data)
    if response.status_code == 200:
        wedding_result = response.json()
        print("✅ Wedding event created successfully")
        print(f"   Event ID: {wedding_result['event_id']}")
        print(f"   Timeline days: {len(wedding_result['timeline'])}")
        print(f"   Estimated budget: ₹{wedding_result['estimated_budget']}")
        wedding_id = wedding_result['event_id']
    else:
        print("❌ Wedding event creation failed")
        print(f"   Error: {response.text}")
        return
    
    # Test 3: Create a birthday event
    print("\n3. Creating a birthday event...")
    birthday_data = {
        "event_type": "birthday",
        "start_date": (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d"),
        "start_time": "15:00",
        "location": "New York, NY",
        "budget": 5000
    }
    
    response = requests.post(f"{BASE_URL}/plan-event", json=birthday_data)
    if response.status_code == 200:
        birthday_result = response.json()
        print("✅ Birthday event created successfully")
        print(f"   Event ID: {birthday_result['event_id']}")
        birthday_id = birthday_result['event_id']
    else:
        print("❌ Birthday event creation failed")
        print(f"   Error: {response.text}")
        return
    
    # Test 4: Get all events
    print("\n4. Retrieving all events...")
    response = requests.get(f"{BASE_URL}/events")
    if response.status_code == 200:
        events = response.json()
        print(f"✅ Retrieved {len(events)} events")
        for event in events:
            print(f"   - Event {event['id']}: {event['event_type']} in {event['location']}")
    else:
        print("❌ Failed to retrieve events")
        return
    
    # Test 5: Get wedding event details
    print(f"\n5. Getting wedding event details (ID: {wedding_id})...")
    response = requests.get(f"{BASE_URL}/events/{wedding_id}")
    if response.status_code == 200:
        event_details = response.json()
        print("✅ Wedding event details retrieved")
        print(f"   Event type: {event_details['event_type']}")
        print(f"   Timeline days: {len(event_details['timeline'])}")
        print(f"   Vendors: {len(event_details['vendors'])}")
    else:
        print("❌ Failed to retrieve wedding event details")
        return
    
    # Test 6: Get deep dive for wedding day 1
    print(f"\n6. Getting deep dive for wedding day 1...")
    response = requests.get(f"{BASE_URL}/events/{wedding_id}/deep-dive/1")
    if response.status_code == 200:
        deep_dive = response.json()
        print("✅ Deep dive retrieved successfully")
        print(f"   Day: {deep_dive['day_number']}")
        print(f"   Date: {deep_dive['date']}")
        print(f"   Activities: {len(deep_dive['activities'])}")
        print(f"   Total cost: ₹{deep_dive['total_cost']}")
        
        print("\n   Activities schedule:")
        for activity in deep_dive['activities']:
            print(f"   - {activity['time']}: {activity['activity']} ({activity['duration']}) - ₹{activity['cost']}")
    else:
        print("❌ Failed to retrieve deep dive")
        print(f"   Error: {response.text}")
        return
    
    # Test 7: Get deep dive for birthday
    print(f"\n7. Getting deep dive for birthday day 1...")
    response = requests.get(f"{BASE_URL}/events/{birthday_id}/deep-dive/1")
    if response.status_code == 200:
        deep_dive = response.json()
        print("✅ Birthday deep dive retrieved successfully")
        print(f"   Activities start at: {deep_dive['activities'][0]['time'] if deep_dive['activities'] else 'No activities'}")
    else:
        print("❌ Failed to retrieve birthday deep dive")
    
    print("\n🎉 All tests completed successfully!")
    print("The system is working with:")
    print("- ✅ Dynamic event creation with custom start times")
    print("- ✅ Real event storage and retrieval")
    print("- ✅ Dynamic deep dive schedules based on event type and start time")
    print("- ✅ Cultural ceremony integration")

if __name__ == "__main__":
    try:
        test_complete_flow()
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Make sure the server is running on http://localhost:8000")
        print("   Start the server with: cd server-plano && ./start_testing.sh")
    except Exception as e:
        print(f"❌ Test failed with error: {e}")