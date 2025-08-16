"""
FastAPI server with authentication bypassed for testing purposes.
Use this version to test all functionality without setting up authentication.
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import EventRequest, EventResponse, VendorResult, EventSummary
from app.utils.service_integration import create_event_with_validation, get_system_health
from typing import List, Dict, Any
import json
import logging
from datetime import datetime
import random

logger = logging.getLogger(__name__)

# In-memory storage for events (for testing)
events_storage = {}
event_counter = 1

app = FastAPI(
    title="Event Planner API - Plano (No Auth)", 
    version="2.0.0",
    description="Testing version with authentication bypassed"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "Intelligent Timeline & Budget System API",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/health",
        "test_endpoints": {
            "plan_event": "POST /plan-event",
            "system_health": "GET /system-health",
            "test_validation": "POST /test-validation"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0", "auth": "bypassed"}

@app.get("/system-health")
async def system_health():
    """Get comprehensive system health status"""
    try:
        health = get_system_health()
        return health
    except Exception as e:
        return {"error": str(e), "status": "error"}

def _calculate_duration(start_date: str, end_date: str = None) -> int:
    """Calculate duration in days between start and end date"""
    if not end_date:
        return 1
    
    try:
        from datetime import datetime
        start_date_clean = str(start_date).strip()
        end_date_clean = str(end_date).strip()

        if not start_date_clean or not end_date_clean:
            return 1
        if len(start_date_clean) != 10 or len(end_date_clean) != 10:
            return 1
        
        start = datetime.fromisoformat(start_date_clean)
        end = datetime.fromisoformat(end_date_clean)
        duration = (end - start).days + 1
        
        return max(1, duration)  
        
    except Exception as e:
        logger.warning(f"Duration calculation error: {e}")
        return 1

@app.post("/plan-event")
async def plan_event(request: EventRequest):
    """Create a new event with AI-generated timeline and budget (No Auth)"""
    try:
        # Validate date formats early
        if request.start_date:
            try:
                from datetime import datetime
                datetime.fromisoformat(request.start_date)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid start_date format: {request.start_date}. Expected YYYY-MM-DD format.")
        
        if request.end_date:
            try:
                from datetime import datetime
                datetime.fromisoformat(request.end_date)
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid end_date format: {request.end_date}. Expected YYYY-MM-DD format.")
        
        event_data = {
            'event_type': request.event_type,
            'guest_count': 150,  # Default guest count
            'venue_type': 'banquet_hall',  # Default venue
            'budget': str(request.budget) if request.budget else '50000',
            'start_date': request.start_date,
            'duration_days': _calculate_duration(request.start_date, request.end_date),
            'location': {
                'city': request.location.split(',')[0].strip() if ',' in request.location else request.location,
                'state': request.location.split(',')[1].strip() if ',' in request.location else 'NY',
                'country': 'USA',
                'timezone': 'America/New_York'
            },
            'budget_tier': 'standard',
            'season': 'spring',
            'cultural_requirements': [request.religion.lower()] if request.religion else []
        }
        
        result = create_event_with_validation(event_data)
        
        if result['success']:
            global event_counter
            event_id = event_counter
            event_counter += 1
            timeline_days = []
            for i, day in enumerate(result['timeline'].days):
                timeline_days.append({
                    "day": day.day_number,
                    "date": day.date.isoformat() if hasattr(day.date, 'isoformat') else str(day.date),
                    "summary": f"Day {day.day_number} activities",
                    "estimated_cost": float(day.estimated_cost),
                    "details": [activity.activity.name for activity in day.activities[:3]]  # First 3 activities
                })
            event_record = {
                "id": event_id,
                "event_type": request.event_type,
                "start_date": request.start_date,
                "start_time": getattr(request, 'start_time', '10:00'),
                "end_date": request.end_date,
                "location": request.location,
                "budget": request.budget,
                "religion": request.religion,
                "estimated_budget": float(result['budget_allocation'].total_budget),
                "created_at": datetime.now().isoformat(),
                "timeline": timeline_days,
                "vendors": [
                    {
                        "title": f"Vendor for {request.event_type}",
                        "url": "https://example.com",
                        "snippet": f"Professional {request.event_type} services in {request.location}"
                    }
                ]
            }
            
            events_storage[event_id] = event_record
            
            return {
                "event_id": event_id,
                "timeline": timeline_days,
                "vendors": event_record["vendors"],
                "estimated_budget": event_record["estimated_budget"],
                "event_details": {
                    "event_type": request.event_type,
                    "location": request.location,
                    "duration": len(result['timeline'].days),
                    "categories": len(result['budget_allocation'].categories),
                    "warnings": result.get('warnings', [])
                }
            }
        else:
            raise HTTPException(status_code=400, detail=result['error']['message'])
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/test-validation")
async def test_validation(data: Dict[str, Any]):
    """Test the validation system with any payload"""
    try:
        result = create_event_with_validation(data)
        return {
            "validation_result": result,
            "success": result.get('success', False)
        }
    except Exception as e:
        return {
            "validation_result": {"success": False, "error": str(e)},
            "success": False
        }

@app.get("/events")
async def get_user_events():
    """Get all events for test user (No Auth)"""
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
        for event in events_storage.values()
    ]

@app.get("/events/{event_id}")
async def get_event(event_id: int):
    """Get full event details (No Auth)"""
    if event_id not in events_storage:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event = events_storage[event_id]
    return {
        "event_id": event_id,
        "event_type": event["event_type"],
        "timeline": event["timeline"],
        "vendors": event["vendors"],
        "estimated_budget": event["estimated_budget"]
    }

@app.get("/events/{event_id}/deep-dive/{day_number}")
async def get_deep_dive(event_id: int, day_number: int):
    """Get detailed schedule for a specific day (No Auth)"""
    if event_id not in events_storage:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event = events_storage[event_id]
    
    # Find the timeline day
    timeline_day = None
    for day in event["timeline"]:
        if day["day"] == day_number:
            timeline_day = day
            break
    
    if not timeline_day:
        raise HTTPException(status_code=404, detail="Day not found")
    start_time = event.get("start_time", "10:00")
    start_hour = int(start_time.split(":")[0])
    activities = generate_activities_for_event(event["event_type"], start_hour, event.get("religion"))
    
    return {
        "event_id": event_id,
        "day_number": day_number,
        "date": timeline_day["date"],
        "activities": activities,
        "total_cost": sum(activity["cost"] for activity in activities)
    }

def generate_activities_for_event(event_type: str, start_hour: int, religion: str = None):
    """Generate dynamic activities based on event type and start time"""
    activities = []
    current_hour = start_hour
    
    if event_type == "wedding":
        if religion == "hindu":
            activities = [
                {
                    "time": f"{current_hour:02d}:00",
                    "activity": "Venue decoration and setup",
                    "duration": "2 hours",
                    "cost": random.randint(3000, 5000),
                    "vendors": ["Decoration Team", "Setup Crew"]
                },
                {
                    "time": f"{current_hour + 2:02d}:00",
                    "activity": "Mehendi ceremony",
                    "duration": "3 hours",
                    "cost": random.randint(8000, 12000),
                    "vendors": ["Mehendi Artist", "Catering Service"]
                },
                {
                    "time": f"{current_hour + 5:02d}:00",
                    "activity": "Sangeet preparation",
                    "duration": "2 hours",
                    "cost": random.randint(5000, 8000),
                    "vendors": ["DJ", "Sound System"]
                }
            ]
        else:
            activities = [
                {
                    "time": f"{current_hour:02d}:00",
                    "activity": "Venue setup",
                    "duration": "2 hours",
                    "cost": random.randint(2000, 4000),
                    "vendors": ["Setup Crew"]
                },
                {
                    "time": f"{current_hour + 2:02d}:00",
                    "activity": "Wedding ceremony",
                    "duration": "2 hours",
                    "cost": random.randint(10000, 15000),
                    "vendors": ["Officiant", "Photographer"]
                },
                {
                    "time": f"{current_hour + 4:02d}:00",
                    "activity": "Reception",
                    "duration": "4 hours",
                    "cost": random.randint(15000, 25000),
                    "vendors": ["Catering", "DJ", "Photographer"]
                }
            ]
    elif event_type == "birthday":
        activities = [
            {
                "time": f"{current_hour:02d}:00",
                "activity": "Party setup",
                "duration": "1 hour",
                "cost": random.randint(1000, 2000),
                "vendors": ["Setup Team"]
            },
            {
                "time": f"{current_hour + 1:02d}:00",
                "activity": "Birthday celebration",
                "duration": "3 hours",
                "cost": random.randint(3000, 6000),
                "vendors": ["Catering", "Entertainment"]
            }
        ]
    elif event_type == "corporate":
        activities = [
            {
                "time": f"{current_hour:02d}:00",
                "activity": "Setup and registration",
                "duration": "1 hour",
                "cost": random.randint(2000, 3000),
                "vendors": ["Setup Team", "Registration Desk"]
            },
            {
                "time": f"{current_hour + 1:02d}:00",
                "activity": "Main presentation",
                "duration": "2 hours",
                "cost": random.randint(5000, 8000),
                "vendors": ["AV Equipment", "Speakers"]
            },
            {
                "time": f"{current_hour + 3:02d}:00",
                "activity": "Networking lunch",
                "duration": "2 hours",
                "cost": random.randint(8000, 12000),
                "vendors": ["Catering Service"]
            }
        ]
    else:
        # Default activities for other event types
        activities = [
            {
                "time": f"{current_hour:02d}:00",
                "activity": "Event setup",
                "duration": "1 hour",
                "cost": random.randint(1000, 2000),
                "vendors": ["Setup Team"]
            },
            {
                "time": f"{current_hour + 1:02d}:00",
                "activity": f"{event_type.title()} celebration",
                "duration": "3 hours",
                "cost": random.randint(3000, 8000),
                "vendors": ["Event Organizer", "Catering"]
            }
        ]
    
    return activities
@app.get("/test/timeline/{event_type}")
async def test_timeline_generation(event_type: str):
    """Test timeline generation for different event types"""
    try:
        from app.utils.fallback_mechanisms import fallback_timeline_generation
        from app.models.core import EventContext, Location
        from app.models.enums import EventType, VenueType, BudgetTier, Season
        
        location = Location(city="Test City", state="Kalyan", country="India", timezone="India/Kolkata")
        context = EventContext(
            event_type=EventType(event_type),
            guest_count=150,
            venue_type=VenueType.BANQUET_HALL,
            cultural_requirements=[],
            budget_tier=BudgetTier.STANDARD,
            location=location,
            season=Season.SPRING,
            duration_days=2
        )
        
        timeline = fallback_timeline_generation(context)
        
        return {
            "event_type": event_type,
            "timeline_days": len(timeline.days),
            "total_activities": sum(len(day.activities) for day in timeline.days),
            "estimated_cost": float(timeline.total_estimated_cost),
            "critical_path_activities": len(timeline.critical_path)
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/test/budget/{budget_amount}")
async def test_budget_allocation(budget_amount: float):
    """Test budget allocation for different amounts"""
    try:
        from app.utils.fallback_mechanisms import fallback_budget_allocation
        from app.models.core import EventContext, Location
        from app.models.enums import EventType, VenueType, BudgetTier, Season
        from decimal import Decimal
        
        location = Location(city="Test City", state="NY", country="USA", timezone="America/New_York")
        context = EventContext(
            event_type=EventType.WEDDING,
            guest_count=150,
            venue_type=VenueType.BANQUET_HALL,
            cultural_requirements=[],
            budget_tier=BudgetTier.STANDARD,
            location=location,
            season=Season.SPRING,
            duration_days=2
        )
        
        allocation = fallback_budget_allocation(Decimal(str(budget_amount)), context)
        
        categories = {}
        for category, cat_allocation in allocation.categories.items():
            categories[category.value] = {
                "amount": float(cat_allocation.amount),
                "percentage": cat_allocation.percentage
            }
        
        return {
            "total_budget": float(allocation.total_budget),
            "per_person_cost": float(allocation.per_person_cost),
            "categories": categories,
            "contingency_percentage": allocation.contingency_percentage
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    print(" Starting Event Planner API (No Auth Version)")
    print("📖 API Documentation: http://localhost:8000/docs")
    print("🔍 Test the API: http://localhost:8000/")
    print("Press Ctrl+C to stop the server")
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")