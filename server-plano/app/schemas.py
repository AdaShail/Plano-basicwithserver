from pydantic import BaseModel
from typing import List, Optional, Any , Dict
from datetime import date

class EventRequest(BaseModel):
    event_type: str
    start_date: str  # ISO format: YYYY-MM-DD
    start_time: Optional[str] = None  # Format: HH:MM
    end_date: Optional[str] = None
    location: str
    budget: Optional[float] = None
    religion: Optional[str] = None
    guest_count: Optional[int] = None
    venue_type: Optional[str] = None
    special_requirements: Optional[List[str]] = None
    accessibility_requirements: Optional[List[str]] = None
    weather_considerations: Optional[List[str]] = None

class VendorResult(BaseModel):
    title: str
    url: Optional[str] = None
    snippet: Optional[str] = None

class TimelineDay(BaseModel):
    day: int
    date: str
    summary: str
    estimated_cost: Optional[float] = None
    details: Optional[List[str]] = None

class EventResponse(BaseModel):
    event_id: int
    timeline: List[TimelineDay]
    vendors: List[VendorResult]
    estimated_budget: float
    event_details: Dict[str, Any]

class EventSummary(BaseModel):
    id: int
    event_type: str
    start_date: date
    end_date: Optional[date]
    location: str
    estimated_budget: Optional[float]
    created_at: str

# New schemas for enhanced API endpoints

class BudgetCategoryExplanation(BaseModel):
    category: str
    amount: float
    percentage: float
    justification: str
    priority: str
    factors_considered: List[str]

class BudgetAlternative(BaseModel):
    name: str
    description: str
    cost_impact: float
    time_impact: Optional[str] = None
    trade_offs: List[str]

class BudgetExplanationResponse(BaseModel):
    event_id: int
    total_budget: float
    categories: List[BudgetCategoryExplanation]
    complexity_analysis: Dict[str, Any]
    regional_factors: Dict[str, Any]
    seasonal_considerations: Dict[str, Any]
    optimization_suggestions: List[str]

class TimelineActivity(BaseModel):
    time: str
    activity: str
    description: str
    duration: str
    priority: str
    vendors_needed: List[str]
    estimated_cost: float

class TimelineExplanation(BaseModel):
    day: int
    date: str
    activities: List[TimelineActivity]
    reasoning: List[str]
    dependencies: List[str]
    buffer_time_explanation: str
    cultural_considerations: List[str]

class TimelineReasoningResponse(BaseModel):
    event_id: int
    timeline_explanations: List[TimelineExplanation]
    overall_strategy: str
    critical_path: List[str]
    contingency_plans: List[str]

class AlternativeTimelineOption(BaseModel):
    name: str
    description: str
    timeline_changes: List[str]
    cost_impact: float
    time_savings: Optional[str] = None
    trade_offs: List[str]

class AlternativeBudgetOption(BaseModel):
    name: str
    description: str
    category_changes: Dict[str, float]
    total_budget_change: float
    impact_analysis: List[str]

class AlternativesResponse(BaseModel):
    event_id: int
    timeline_alternatives: List[AlternativeTimelineOption]
    budget_alternatives: List[AlternativeBudgetOption]
    recommendations: List[str]

class UserFeedback(BaseModel):
    event_id: int
    timeline_rating: int  # 1-5 scale
    budget_accuracy: int  # 1-5 scale
    vendor_quality: int  # 1-5 scale
    overall_satisfaction: int  # 1-5 scale
    comments: Optional[str] = None
    improvements_suggested: Optional[List[str]] = None
    would_recommend: bool

class FeedbackResponse(BaseModel):
    message: str
    feedback_id: int
    learning_impact: str

class BudgetModificationRequest(BaseModel):
    category_changes: Dict[str, float]  # category -> new_amount
    reason: Optional[str] = None

class BudgetModificationResponse(BaseModel):
    event_id: int
    updated_allocation: Dict[str, Any]
    impact_analysis: List[str]
    warnings: Optional[List[str]] = None