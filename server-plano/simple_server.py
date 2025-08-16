#!/usr/bin/env python3
"""
Simple FastAPI server for Flutter app testing
No authentication, no complex dependencies
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import json
from datetime import datetime, timedelta

app = FastAPI(
    title="Plano API (Simple)", 
    version="1.0.0",
    description="Simple server for Flutter app testing"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request/Response Models
class EventRequest(BaseModel):
    event_type: str
    start_date: str
    end_date: Optional[str] = None
    location: str
    budget: Optional[float] = None
    religion: Optional[str] = None

class EventSummary(BaseModel):
    id: int
    event_type: str
    start_date: str
    end_date: Optional[str]
    location: str
    estimated_budget: float
    created_at: str

# In-memory storage for demo
events_db = []
event_counter = 1

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Plano API - Simple Version",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "health": "GET /health",
            "plan_event": "POST /plan-event",
            "events": "GET /events",
            "event_details": "GET /events/{event_id}",
            "deep_dive": "GET /events/{event_id}/deep-dive/{day_number}"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy", 
        "version": "1.0.0", 
        "auth": "disabled",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/plan-event")
async def plan_event(request: EventRequest):
    """Create a new event with mock AI-generated timeline"""
    global event_counter
    
    try:
        # Calculate duration
        start_date = datetime.fromisoformat(request.start_date)
        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date)
            duration = (end_date - start_date).days + 1
        else:
            duration = 1
            end_date = start_date
        
        # Generate mock timeline
        timeline = []
        base_cost = request.budget / duration if request.budget else 10000
        
        for day in range(duration):
            current_date = start_date + timedelta(days=day)
            
            # Generate activities based on event type
            activities = generate_activities(request.event_type, day + 1, request.religion)
            
            timeline.append({
                "day": day + 1,
                "date": current_date.strftime("%Y-%m-%d"),
                "summary": f"Day {day + 1} - {get_day_theme(request.event_type, day + 1)}",
                "estimated_cost": base_cost * (1 + day * 0.1),  # Varying costs
                "details": activities
            })
        
        # Generate mock vendors
        vendors = generate_vendors(request.event_type, request.location)
        
        # Calculate total budget
        total_budget = sum(day["estimated_cost"] for day in timeline)
        
        # Store event
        event_data = {
            "id": event_counter,
            "event_type": request.event_type,
            "start_date": request.start_date,
            "end_date": request.end_date,
            "location": request.location,
            "estimated_budget": total_budget,
            "created_at": datetime.now().isoformat(),
            "timeline": timeline,
            "vendors": vendors
        }
        
        events_db.append(event_data)
        event_counter += 1
        
        return {
            "event_id": event_data["id"],
            "timeline": timeline,
            "vendors": vendors,
            "estimated_budget": total_budget,
            "event_details": {
                "event_type": request.event_type,
                "location": request.location,
                "duration": duration,
                "categories": 5,  # Mock categories
                "religion": request.religion
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating event: {str(e)}")

@app.get("/events")
async def get_user_events():
    """Get all events"""
    return [
        {
            "id": event["id"],
            "event_type": event["event_type"],
            "start_date": event["start_date"],
            "end_date": event["end_date"],
            "location": event["location"],
            "estimated_budget": event["estimated_budget"],
            "created_at": event["created_at"]
        }
        for event in events_db
    ]

@app.get("/events/{event_id}")
async def get_event(event_id: int):
    """Get full event details"""
    event = next((e for e in events_db if e["id"] == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    return {
        "event_id": event["id"],
        "event_type": event["event_type"],
        "timeline": event["timeline"],
        "vendors": event["vendors"],
        "estimated_budget": event["estimated_budget"]
    }

@app.get("/events/{event_id}/deep-dive/{day_number}")
async def get_deep_dive(event_id: int, day_number: int):
    """Get detailed schedule for a specific day"""
    event = next((e for e in events_db if e["id"] == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    day_data = next((d for d in event["timeline"] if d["day"] == day_number), None)
    if not day_data:
        raise HTTPException(status_code=404, detail="Day not found")
    
    # Generate detailed activities with times
    activities = generate_detailed_activities(event["event_type"], day_number)
    
    return {
        "event_id": event_id,
        "day_number": day_number,
        "date": day_data["date"],
        "activities": activities,
        "total_cost": day_data["estimated_cost"]
    }

# Helper functions
def generate_activities(event_type: str, day: int, religion: Optional[str] = None) -> List[str]:
    """Generate mock activities based on event type"""
    activities_map = {
        "wedding": {
            1: ["Mehendi ceremony", "Sangeet preparation", "Venue decoration"],
            2: ["Haldi ceremony", "Baraat preparation", "Photography setup"],
            3: ["Wedding ceremony", "Reception", "Send-off ceremony"]
        },
        "birthday": {
            1: ["Venue setup", "Cake preparation", "Guest reception", "Party activities", "Cleanup"]
        },
        "housewarming": {
            1: ["House blessing", "Guest welcome", "Tour and refreshments", "Gift ceremony"]
        },
        "corporate": {
            1: ["Setup and registration", "Opening ceremony", "Main event", "Networking", "Closing"]
        }
    }
    
    base_activities = activities_map.get(event_type, {}).get(day, ["Event preparation", "Main activities", "Conclusion"])
    
    # Add religious customization
    if religion and event_type == "wedding":
        if religion == "hindu":
            base_activities.extend(["Ganesh puja", "Mandap setup"])
        elif religion == "muslim":
            base_activities.extend(["Nikah ceremony", "Walima preparation"])
        elif religion == "christian":
            base_activities.extend(["Church ceremony", "Reception setup"])
    
    return base_activities

def get_day_theme(event_type: str, day: int) -> str:
    """Get theme for each day"""
    themes = {
        "wedding": {1: "Pre-wedding ceremonies", 2: "Wedding preparations", 3: "Wedding day"},
        "birthday": {1: "Birthday celebration"},
        "housewarming": {1: "House blessing ceremony"},
        "corporate": {1: "Corporate event"}
    }
    return themes.get(event_type, {}).get(day, "Event activities")

def generate_vendors(event_type: str, location: str) -> List[Dict[str, str]]:
    """Generate mock vendor recommendations"""
    vendor_types = {
        "wedding": ["Wedding Photographers", "Catering Services", "Decoration Team", "Music & DJ"],
        "birthday": ["Party Planners", "Cake Designers", "Entertainment", "Photography"],
        "housewarming": ["Catering", "Decoration", "Pandit/Priest", "Photography"],
        "corporate": ["Event Management", "AV Equipment", "Catering", "Photography"]
    }
    
    vendors = []
    for vendor_type in vendor_types.get(event_type, ["Event Services"]):
        vendors.append({
            "title": f"{vendor_type} in {location}",
            "url": "https://example.com",
            "snippet": f"Professional {vendor_type.lower()} services in {location}"
        })
    
    return vendors

def generate_detailed_activities(event_type: str, day: int) -> List[Dict[str, Any]]:
    """Generate detailed activities with times and costs"""
    base_time = 9  # Start at 9 AM
    activities = []
    
    activity_templates = {
        "wedding": [
            {"name": "Venue setup", "duration": 3, "cost": 5000},
            {"name": "Decoration", "duration": 2, "cost": 8000},
            {"name": "Catering setup", "duration": 2, "cost": 3000},
            {"name": "Photography setup", "duration": 1, "cost": 2000},
            {"name": "Main ceremony", "duration": 4, "cost": 15000},
            {"name": "Reception", "duration": 3, "cost": 10000}
        ],
        "birthday": [
            {"name": "Venue setup", "duration": 2, "cost": 2000},
            {"name": "Decoration", "duration": 1, "cost": 3000},
            {"name": "Cake preparation", "duration": 1, "cost": 1500},
            {"name": "Party activities", "duration": 3, "cost": 4000},
            {"name": "Cleanup", "duration": 1, "cost": 1000}
        ]
    }
    
    templates = activity_templates.get(event_type, activity_templates["birthday"])
    
    current_time = base_time
    for template in templates:
        activities.append({
            "time": f"{current_time:02d}:00",
            "activity": template["name"],
            "duration": f"{template['duration']} hours",
            "cost": template["cost"],
            "vendors": [f"{template['name']} Team"]
        })
        current_time += template["duration"]
    
    return activities

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Plano Simple Server")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Test the API: http://localhost:8000/")
    print("💡 This is a simplified server for Flutter app testing")
    print("Press Ctrl+C to stop the server")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")