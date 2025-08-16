from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.schemas import (
    EventRequest, EventResponse, VendorResult, EventSummary,
    BudgetExplanationResponse, TimelineReasoningResponse, AlternativesResponse,
    UserFeedback, FeedbackResponse, BudgetModificationRequest, BudgetModificationResponse
)
from app.services.event_service import EventService
from app.utils.auth import get_current_user_id
from typing import List

app = FastAPI(title="Event Planner API", version="2.0.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

event_service = EventService()

@app.post("/plan-event", response_model=EventResponse)
async def plan_event(
    request: EventRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new event with AI-generated timeline and vendor search"""
    try:
        result = await event_service.create_event(user_id, request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/events", response_model=List[EventSummary])
async def get_user_events(user_id: str = Depends(get_current_user_id)):
    """Get all events for the authenticated user"""
    try:
        events = await event_service.get_user_events(user_id)
        return events
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/events/{event_id}")
async def get_event(
    event_id: int,
    user_id: str = Depends(get_current_user_id)
):
    """Get full event details including timeline and vendors"""
    try:
        result = await event_service.get_event_timeline(event_id, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/events/{event_id}/deep-dive/{day_number}")
async def get_deep_dive(
    event_id: int,
    day_number: int,
    user_id: str = Depends(get_current_user_id)
):
    """Get detailed schedule for a specific day"""
    try:
        result = await event_service.get_deep_dive(event_id, day_number, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/events/{event_id}/budget")
async def get_detailed_budget(
    event_id: int,
    user_id: str = Depends(get_current_user_id)
):
    """Get detailed budget breakdown for an event"""
    try:
        result = await event_service.get_detailed_budget(event_id, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

# New enhanced API endpoints for explanations and alternatives

@app.get("/events/{event_id}/budget/explanation", response_model=BudgetExplanationResponse)
async def get_budget_explanation(
    event_id: int,
    user_id: str = Depends(get_current_user_id)
):
    """Get detailed explanation of budget allocation decisions"""
    try:
        result = await event_service.get_budget_explanation(event_id, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/events/{event_id}/timeline/reasoning", response_model=TimelineReasoningResponse)
async def get_timeline_reasoning(
    event_id: int,
    user_id: str = Depends(get_current_user_id)
):
    """Get detailed reasoning behind timeline activity sequencing"""
    try:
        result = await event_service.get_timeline_reasoning(event_id, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/events/{event_id}/alternatives", response_model=AlternativesResponse)
async def get_alternatives(
    event_id: int,
    user_id: str = Depends(get_current_user_id)
):
    """Get alternative timeline and budget options"""
    try:
        result = await event_service.get_alternatives(event_id, user_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.post("/events/{event_id}/budget/modify", response_model=BudgetModificationResponse)
async def modify_budget_allocation(
    event_id: int,
    modification_request: BudgetModificationRequest,
    user_id: str = Depends(get_current_user_id)
):
    """Modify budget allocation and get impact analysis"""
    try:
        result = await event_service.modify_budget_allocation(
            event_id, user_id, modification_request.dict()
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/events/{event_id}/feedback", response_model=FeedbackResponse)
async def submit_feedback(
    event_id: int,
    feedback: UserFeedback,
    user_id: str = Depends(get_current_user_id)
):
    """Submit user feedback for pattern learning"""
    try:
        result = await event_service.submit_feedback(event_id, user_id, feedback.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/events/{event_id}/timeline/alternatives")
async def get_timeline_alternatives(
    event_id: int,
    approach: str = "balanced",  # balanced, fast, premium, budget
    user_id: str = Depends(get_current_user_id)
):
    """Generate alternative timeline approaches"""
    try:
        result = await event_service.get_timeline_alternatives(event_id, user_id, approach)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/events/{event_id}/budget/alternatives")
async def get_budget_alternatives(
    event_id: int,
    scenario: str = "standard",  # standard, budget_conscious, premium, emergency
    user_id: str = Depends(get_current_user_id)
):
    """Generate alternative budget allocation scenarios"""
    try:
        result = await event_service.get_budget_alternatives(event_id, user_id, scenario)
        return result
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "version": "2.0.0"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)