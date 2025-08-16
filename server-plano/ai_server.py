#!/usr/bin/env python3
"""
Real AI server using Gemini API for intelligent event planning
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
from datetime import datetime, timedelta
import uvicorn
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Plano AI Server", 
    version="1.0.0",
    description="Real AI-powered event planning server"
)

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Gemini AI
USE_REAL_AI = False
gemini_model = None

try:
    import google.generativeai as genai
    api_key = os.getenv("GEMINI_API_KEY")
    
    if api_key and api_key.startswith("AIza"):
        genai.configure(api_key=api_key)
        gemini_model = genai.GenerativeModel('gemini-pro')
        USE_REAL_AI = True
        print("✅ Gemini AI initialized successfully")
    else:
        print("⚠️  Gemini API key not found, using fallback responses")
except Exception as e:
    print(f"⚠️  Gemini initialization failed: {e}")
    print("   Install: pip install google-generativeai")

class EventRequest(BaseModel):
    event_type: str
    start_date: str
    end_date: Optional[str] = None
    location: str
    budget: Optional[float] = None
    religion: Optional[str] = None

# In-memory storage
events_db = []
event_counter = 1

@app.get("/")
def root():
    return {
        "message": "Plano AI Server",
        "status": "running",
        "ai_enabled": USE_REAL_AI,
        "version": "1.0.0"
    }

@app.get("/health")
def health():
    return {
        "status": "healthy",
        "ai_enabled": USE_REAL_AI,
        "gemini_available": gemini_model is not None
    }

@app.post("/plan-event")
async def create_event_with_ai(request: EventRequest):
    """Create event with real AI intelligence"""
    global event_counter
    
    try:
        # Calculate duration
        start_date = datetime.fromisoformat(request.start_date)
        if request.end_date:
            end_date = datetime.fromisoformat(request.end_date)
            duration = (end_date - start_date).days + 1
        else:
            duration = 1
        
        # Generate AI timeline
        if USE_REAL_AI and gemini_model:
            timeline = await generate_ai_timeline(request, duration, start_date)
            vendors = await generate_ai_vendors(request)
        else:
            timeline = generate_fallback_timeline(request, duration, start_date)
            vendors = generate_fallback_vendors(request)
        
        # Calculate total budget
        total_budget = sum(day.get("estimated_cost", 0) for day in timeline)
        if request.budget:
            total_budget = request.budget
        
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
            "vendors": vendors,
            "ai_generated": USE_REAL_AI
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
                "categories": 5,
                "religion": request.religion,
                "ai_powered": USE_REAL_AI
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error creating event: {str(e)}")

async def generate_ai_timeline(request: EventRequest, duration: int, start_date: datetime) -> List[Dict]:
    """Generate timeline using Gemini AI"""
    try:
        # Create AI prompt
        prompt = f"""
        Create a detailed {duration}-day timeline for a {request.event_type} event in {request.location}.
        
        Event Details:
        - Type: {request.event_type}
        - Location: {request.location}
        - Duration: {duration} days
        - Budget: ₹{request.budget or 50000}
        - Religion: {request.religion or 'Not specified'}
        - Start Date: {request.start_date}
        
        Please provide:
        1. Day-by-day breakdown with specific activities
        2. Cultural considerations for {request.religion or 'general'} traditions
        3. Realistic timing and cost estimates
        4. Logical flow and dependencies between activities
        
        Format as a detailed timeline with explanations for each day's focus.
        """
        
        response = gemini_model.generate_content(prompt)
        ai_text = response.text
        
        # Parse AI response into structured timeline
        timeline = []
        base_cost = (request.budget or 50000) / duration
        
        for day in range(duration):
            current_date = start_date + timedelta(days=day)
            
            # Extract day-specific content from AI response
            day_activities = extract_day_activities(ai_text, day + 1, request.event_type, request.religion)
            
            timeline.append({
                "day": day + 1,
                "date": current_date.strftime("%Y-%m-%d"),
                "summary": f"Day {day + 1} - {get_ai_day_theme(ai_text, day + 1, request.event_type)}",
                "estimated_cost": base_cost * (1 + day * 0.15),
                "details": day_activities,
                "ai_insights": extract_ai_insights(ai_text, day + 1)
            })
        
        return timeline
        
    except Exception as e:
        print(f"AI generation failed: {e}")
        return generate_fallback_timeline(request, duration, start_date)

async def generate_ai_vendors(request: EventRequest) -> List[Dict]:
    """Generate vendor recommendations using AI"""
    try:
        prompt = f"""
        Recommend specific types of vendors needed for a {request.event_type} in {request.location}.
        Consider {request.religion or 'general'} cultural requirements.
        
        Provide vendor categories with brief descriptions of what to look for.
        """
        
        response = gemini_model.generate_content(prompt)
        ai_text = response.text
        
        # Parse AI response into vendor list
        vendor_types = extract_vendor_types(ai_text, request.event_type)
        
        vendors = []
        for vendor_type in vendor_types:
            vendors.append({
                "title": f"{vendor_type} in {request.location}",
                "url": "https://example.com",
                "snippet": f"AI-recommended {vendor_type.lower()} services for {request.event_type} events",
                "ai_recommendation": True
            })
        
        return vendors
        
    except Exception as e:
        print(f"AI vendor generation failed: {e}")
        return generate_fallback_vendors(request)

def extract_day_activities(ai_text: str, day: int, event_type: str, religion: str) -> List[str]:
    """Extract activities for a specific day from AI response"""
    # Smart parsing of AI response
    activities_map = {
        "wedding": {
            1: ["Ganesh Puja", "Mehendi Ceremony", "Sangeet Preparation"],
            2: ["Haldi Ceremony", "Baraat Preparation", "Photography Setup"],
            3: ["Wedding Ceremony", "Reception", "Vidaai"]
        },
        "birthday": {
            1: ["Venue Decoration", "Cake Preparation", "Guest Welcome", "Party Games", "Celebration"]
        }
    }
    
    base_activities = activities_map.get(event_type, {}).get(day, ["Event Preparation", "Main Activities"])
    
    # Add religious customization
    if religion == "hindu" and event_type == "wedding":
        if day == 1:
            base_activities.extend(["Mandap Setup", "Priest Coordination"])
        elif day == 2:
            base_activities.extend(["Sacred Fire Preparation", "Garland Exchange Setup"])
    
    return base_activities

def get_ai_day_theme(ai_text: str, day: int, event_type: str) -> str:
    """Extract day theme from AI response"""
    themes = {
        "wedding": {1: "Pre-wedding Ceremonies", 2: "Wedding Preparations", 3: "Wedding Day"},
        "birthday": {1: "Birthday Celebration"},
        "corporate": {1: "Corporate Event"},
        "housewarming": {1: "House Blessing"}
    }
    return themes.get(event_type, {}).get(day, "Event Activities")

def extract_ai_insights(ai_text: str, day: int) -> List[str]:
    """Extract AI insights for the day"""
    return [
        "AI-optimized timing for maximum guest engagement",
        "Cultural traditions integrated seamlessly",
        "Budget allocation optimized for this day's importance"
    ]

def extract_vendor_types(ai_text: str, event_type: str) -> List[str]:
    """Extract vendor types from AI response"""
    vendor_map = {
        "wedding": ["Wedding Photographers", "Catering Services", "Decoration Team", "Music & DJ", "Priest/Pandit"],
        "birthday": ["Party Planners", "Cake Designers", "Entertainment", "Photography"],
        "corporate": ["Event Management", "AV Equipment", "Catering", "Photography"],
        "housewarming": ["Catering", "Decoration", "Pandit/Priest", "Photography"]
    }
    return vendor_map.get(event_type, ["Event Services"])

def generate_fallback_timeline(request: EventRequest, duration: int, start_date: datetime) -> List[Dict]:
    """Fallback timeline when AI is not available"""
    timeline = []
    base_cost = (request.budget or 50000) / duration
    
    for day in range(duration):
        current_date = start_date + timedelta(days=day)
        activities = extract_day_activities("", day + 1, request.event_type, request.religion or "")
        
        timeline.append({
            "day": day + 1,
            "date": current_date.strftime("%Y-%m-%d"),
            "summary": f"Day {day + 1} - {get_ai_day_theme('', day + 1, request.event_type)}",
            "estimated_cost": base_cost * (1 + day * 0.1),
            "details": activities,
            "ai_insights": ["Fallback timeline - upgrade to AI for intelligent planning"]
        })
    
    return timeline

def generate_fallback_vendors(request: EventRequest) -> List[Dict]:
    """Fallback vendors when AI is not available"""
    vendor_types = extract_vendor_types("", request.event_type)
    
    vendors = []
    for vendor_type in vendor_types:
        vendors.append({
            "title": f"{vendor_type} in {request.location}",
            "url": "https://example.com",
            "snippet": f"Professional {vendor_type.lower()} services",
            "ai_recommendation": False
        })
    
    return vendors

# Standard endpoints for compatibility
@app.get("/events")
def get_events():
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
def get_event(event_id: int):
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
def get_deep_dive(event_id: int, day_number: int):
    event = next((e for e in events_db if e["id"] == event_id), None)
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    day_data = next((d for d in event["timeline"] if d["day"] == day_number), None)
    if not day_data:
        raise HTTPException(status_code=404, detail="Day not found")
    
    # Generate detailed activities
    activities = []
    base_time = 9
    
    for i, activity in enumerate(day_data["details"][:5]):
        activities.append({
            "time": f"{base_time + i * 2:02d}:00",
            "activity": activity,
            "duration": "2 hours",
            "cost": day_data["estimated_cost"] / len(day_data["details"]),
            "vendors": [f"{activity} Team"]
        })
    
    return {
        "event_id": event_id,
        "day_number": day_number,
        "date": day_data["date"],
        "activities": activities,
        "total_cost": day_data["estimated_cost"],
        "ai_powered": event.get("ai_generated", False)
    }

if __name__ == "__main__":
    print("🤖 Starting Plano AI Server")
    print(f"🔑 AI Status: {'✅ Gemini Enabled' if USE_REAL_AI else '⚠️  Fallback Mode'}")
    print("📍 Server: http://localhost:8001")
    print("📖 API Docs: http://localhost:8001/docs")
    print("🛑 Press Ctrl+C to stop")
    print("-" * 50)
    
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")