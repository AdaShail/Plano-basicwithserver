# app/services/timeline_generator.py
from datetime import datetime, timedelta, date
from typing import List, Dict, Optional
import os
import logging

# Optional config import
try:
    import app.config as config
    from app.utils.helpers import days_between
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    # Fallback days_between function
    def days_between(start_date: str, end_date: str) -> int:
        start = datetime.fromisoformat(start_date)
        end = datetime.fromisoformat(end_date)
        return (end - start).days + 1

# Import new intelligence engine
try:
    from app.services.timeline_intelligence_engine import TimelineIntelligenceEngine
    from app.services.event_context_analyzer import EventContextAnalyzer
    from app.services.cultural_templates import CulturalTemplateEngine
    from app.models.core import EventContext
    from app.models.enums import EventType, VenueType, BudgetTier, CulturalRequirement, Season
    from decimal import Decimal
    ENHANCED_ENGINE_AVAILABLE = True
except ImportError as e:
    ENHANCED_ENGINE_AVAILABLE = False
    print(f"Enhanced timeline engine not available: {e}")

logger = logging.getLogger(__name__)

# Optional dependency: openai (only used if AI_MODEL_KEY provided)
USE_AI = False
if CONFIG_AVAILABLE:
    USE_AI = bool(getattr(config, "GEMINI_API_KEY", None))
    if USE_AI:
        try:
            import google.generativeai as genai
            genai.configure(api_key=config.GEMINI_API_KEY)
        except Exception as e:
            print("Gemini import/initialization failed, falling back to heuristic generator:", e)
            USE_AI = False

# Initialize intelligence engine and context analyzer if available
if ENHANCED_ENGINE_AVAILABLE:
    timeline_engine = TimelineIntelligenceEngine()
    context_analyzer = EventContextAnalyzer()
    cultural_template_engine = CulturalTemplateEngine()
else:
    timeline_engine = None
    context_analyzer = None
    cultural_template_engine = None


# --- Helpers / Domain knowledge ---
DEFAULT_WEDDING_DAYS = 3

# Minimal map of ceremonies by religion & event type (extendable)
CEREMONIES = {
    "wedding": {
        "hindu": ["Mehendi", "Haldi", "Sangeet", "Wedding Ceremony", "Reception"],
        "muslim": ["Nikkah", "Mehndi", "Walima"],
        "christian": ["Wedding Ceremony", "Reception"],
        "sikh": ["Anand Karaj", "Sangeet", "Reception"],
        "default": ["Engagement", "Ceremony", "Reception"]
    },
    "birthday": {
        "default": ["Preparation", "Party", "Cake & Games", "Wrap-up"]
    },
    "housewarming": {
        "default": ["Puja/Prayers", "Home Tour", "Lunch/High-tea", "Thanks & Wrap-up"]
    }
}

def _normalize_religion(r: Optional[str]) -> str:
    if not r:
        return "default"
    r = r.strip().lower()
    if r in ["hindu", "hinduism"]:
        return "hindu"
    if r in ["muslim", "islam"]:
        return "muslim"
    if r in ["christian", "christianity"]:
        return "christian"
    if r in ["sikh", "sikhism"]:
        return "sikh"
    return "default"

def _budget_tier(budget_per_day: float) -> str:
    # crude tiers — tune to your locale/currency
    if budget_per_day is None:
        return "standard"
    if budget_per_day < 5000:
        return "low"
    if budget_per_day < 25000:
        return "standard"
    return "premium"

def _create_enhanced_context(event_type: str, guest_count: int, venue_type: str, 
                           location: str, religion: str, budget: float, days_count: int,
                           special_requirements: list, accessibility_requirements: list,
                           weather_considerations: list) -> EventContext:
    """Create enhanced event context for timeline generation"""
    if not ENHANCED_ENGINE_AVAILABLE:
        return None
    
    try:
        # Convert string enums to proper enum values
        event_type_enum = EventType(event_type.lower())
        venue_type_enum = VenueType(venue_type.lower()) if venue_type else VenueType.INDOOR
        
        # Determine cultural requirements
        cultural_reqs = []
        if religion:
            religion_lower = religion.lower()
            if religion_lower in ['hindu', 'hinduism']:
                cultural_reqs.append(CulturalRequirement.HINDU)
            elif religion_lower in ['muslim', 'islam']:
                cultural_reqs.append(CulturalRequirement.MUSLIM)
            elif religion_lower in ['christian', 'christianity']:
                cultural_reqs.append(CulturalRequirement.CHRISTIAN)
            elif religion_lower in ['sikh', 'sikhism']:
                cultural_reqs.append(CulturalRequirement.SIKH)
            else:
                cultural_reqs.append(CulturalRequirement.SECULAR)
        else:
            cultural_reqs.append(CulturalRequirement.SECULAR)
        
        # Determine budget tier
        if budget:
            per_person_budget = budget / guest_count if guest_count > 0 else budget
            if per_person_budget < 2000:
                budget_tier = BudgetTier.LOW
            elif per_person_budget < 5000:
                budget_tier = BudgetTier.STANDARD
            elif per_person_budget < 12000:
                budget_tier = BudgetTier.PREMIUM
            else:
                budget_tier = BudgetTier.LUXURY
        else:
            budget_tier = BudgetTier.STANDARD
        
        # Create location object
        from app.models.core import Location
        location_obj = Location(city=location, state="Unknown", country="India", timezone="Asia/Kolkata")  # Default to India
        
        # Determine season based on current date
        from datetime import datetime
        current_month = datetime.now().month
        if current_month in [12, 1, 2]:
            season = Season.WINTER
        elif current_month in [3, 4, 5]:
            season = Season.SPRING
        elif current_month in [6, 7, 8]:
            season = Season.SUMMER
        elif current_month in [9, 10, 11]:
            season = Season.AUTUMN
        else:
            season = Season.SPRING  # Default
        
        # Create context
        context = EventContext(
            event_type=event_type_enum,
            guest_count=guest_count,
            venue_type=venue_type_enum,
            location=location_obj,
            cultural_requirements=cultural_reqs,
            budget_tier=budget_tier,
            season=season,
            duration_days=days_count,
            special_requirements=special_requirements or [],
            accessibility_requirements=[],  # Convert strings to enums if needed
            weather_considerations=[],  # Convert strings to enums if needed
            complexity_score=0.0
        )
        
        return context
        
    except Exception as e:
        logger.warning(f"Failed to create enhanced context: {e}")
        return None

def _generate_timeline_from_template(context: EventContext, template) -> List[Dict]:
    """Generate timeline from cultural template"""
    if not template or not ENHANCED_ENGINE_AVAILABLE:
        return []
    
    timeline = []
    current_date = datetime.now().date()
    
    # For multi-day events, distribute activities across days
    if context.duration_days > 1:
        activities_per_day = len(template.activities) // context.duration_days
        if activities_per_day == 0:
            activities_per_day = 1
    else:
        activities_per_day = len(template.activities)
    
    day_number = 1
    activity_index = 0
    
    while activity_index < len(template.activities) and day_number <= context.duration_days:
        day_activities = []
        day_cost = 0.0
        
        # Get activities for this day
        end_index = min(activity_index + activities_per_day, len(template.activities))
        for i in range(activity_index, end_index):
            activity_template = template.activities[i]
            activity = activity_template.to_activity(context, f"activity_{i}")
            
            day_activities.append({
                "time": "TBD",  # Will be set by detailed scheduling
                "activity": activity.name,
                "description": activity.description,
                "duration": str(activity.duration),
                "priority": activity.priority.value,
                "vendors_needed": activity.required_vendors,
                "estimated_cost": float(activity.estimated_cost)
            })
            
            day_cost += float(activity.estimated_cost)
        
        # Create day summary
        day_data = {
            "day": day_number,
            "date": (current_date + timedelta(days=day_number-1)).isoformat(),
            "summary": f"Day {day_number} - {template.name}",
            "estimated_cost": day_cost,
            "details": [activity["activity"] for activity in day_activities],
            "notes": [template.cultural_notes] if template.cultural_notes else [],
            "contingency_plans": ["Weather backup plan", "Vendor backup options"]
        }
        
        timeline.append(day_data)
        
        activity_index = end_index
        day_number += 1
    
    return timeline

def _estimate_cost_for_day(event_type: str, tier: str) -> float:
    # heuristics for daily estimated cost — customize
    bases = {"wedding": 30000, "birthday": 5000, "housewarming": 8000}
    base = bases.get(event_type.lower(), 7000)
    if tier == "low":
        return base * 0.5
    if tier == "standard":
        return base
    return base * 1.8

# --- AI prompt helpers ---
def _ai_generate(prompt: str, temperature: float = 0.7) -> Optional[str]:
    if not USE_AI:
        return None
    try:
        # Combine "system" style instruction with the user's prompt
        system_instruction = (
            "You are an expert event planner. "
            "Provide clear schedules, practical tips, and be aware of cultural/religious variations. "
            "Output should be easy for users to follow."
        )
        full_prompt = f"{system_instruction}\n\n{prompt}"

        model = genai.GenerativeModel("gemini-pro")
        response = model.generate_content(
            full_prompt,
            generation_config={"temperature": temperature, "max_output_tokens": 700}
        )

        return response.text.strip() if response.text else None

    except Exception as e:
        print("Gemini call failed, falling back to heuristic generator:", e)
        return None

# --- Public API ---
def generate_timeline(event_type: str, start_date: str, end_date: Optional[str] = None,
                      religion: Optional[str] = None, budget: Optional[float] = None,
                      guest_count: Optional[int] = None, venue_type: Optional[str] = None,
                      location: Optional[str] = None, **kwargs) -> List[Dict]:
    """
    Enhanced timeline generation using cultural templates and TimelineIntelligenceEngine.
    Maintains backward compatibility with existing API contracts.
    
    Returns a list of day-plans:
      - Each day: { day, date, summary, estimated_cost, details }
    
    New enhanced parameters:
      - guest_count: Number of guests (improves duration calculations)
      - venue_type: Type of venue (affects logistics and setup)
      - location: Event location (for regional adjustments)
    """
    
    # Try enhanced generation with cultural templates first
    if ENHANCED_ENGINE_AVAILABLE and cultural_template_engine:
        try:
            # Create enhanced context
            context = _create_enhanced_context(
                event_type=event_type,
                guest_count=guest_count or 100,
                venue_type=venue_type or "indoor",
                location=location or "Mumbai",
                religion=religion,
                budget=budget or 10000,
                days_count=days_between(start_date, end_date) if end_date else 1,
                special_requirements=kwargs.get('special_requirements', []),
                accessibility_requirements=kwargs.get('accessibility_requirements', []),
                weather_considerations=kwargs.get('weather_considerations', [])
            )
            
            if context:
                # Find compatible ceremony template
                template = cultural_template_engine.get_best_template(context)
                
                if template:
                    logger.info(f"Using cultural template: {template.name}")
                    timeline = _generate_timeline_from_template(context, template)
                    if timeline:
                        return timeline
                else:
                    logger.warning(f"No compatible ceremony templates found for {event_type} event")
            
        except Exception as e:
            logger.warning(f"Cultural template generation failed: {str(e)}")
    
    # Try TimelineIntelligenceEngine if cultural templates failed
    if ENHANCED_ENGINE_AVAILABLE and timeline_engine and context_analyzer:
        try:
            # Create enhanced event context for new intelligence engine
            context = _create_event_context(
                event_type=event_type,
                start_date=start_date,
                end_date=end_date,
                religion=religion,
                budget=budget,
                guest_count=guest_count,
                venue_type=venue_type,
                location=location,
                **kwargs
            )
            
            # Use new intelligence engine
            start_date_obj = datetime.fromisoformat(start_date).date()
            timeline_obj = timeline_engine.generate_timeline(context, start_date_obj)
            
            # Convert to backward-compatible format
            timeline = _convert_timeline_to_legacy_format(timeline_obj)
            
            logger.info(f"Generated enhanced timeline with {len(timeline)} days using TimelineIntelligenceEngine")
            return timeline
            
        except Exception as e:
            logger.warning(f"Enhanced timeline generation failed: {str(e)}, falling back to legacy method")
    
    # Generate fallback timeline due to errors
    logger.info("Generating fallback timeline due to errors")
    return _generate_fallback_timeline(event_type, start_date, end_date, religion, budget, guest_count, venue_type, location)


def _create_event_context(event_type: str, start_date: str, end_date: Optional[str] = None,
                         religion: Optional[str] = None, budget: Optional[float] = None,
                         guest_count: Optional[int] = None, venue_type: Optional[str] = None,
                         location: Optional[str] = None, **kwargs):
    """Create EventContext from legacy parameters"""
    if not ENHANCED_ENGINE_AVAILABLE:
        return None
    
    # Parse event type
    try:
        event_type_enum = EventType(event_type.lower())
    except ValueError:
        event_type_enum = EventType.BIRTHDAY  # Default fallback
    
    # Parse venue type
    venue_type_enum = VenueType.INDOOR  # Default
    if venue_type:
        try:
            venue_type_enum = VenueType(venue_type.lower().replace(' ', '_'))
        except ValueError:
            pass
    
    # Parse cultural requirements
    cultural_requirements = []
    if religion:
        religion_normalized = _normalize_religion(religion)
        if religion_normalized != "default":
            try:
                cultural_req = CulturalRequirement(religion_normalized.upper())
                cultural_requirements.append(cultural_req)
            except ValueError:
                pass
    
    # Determine budget tier
    if not end_date:
        if event_type.strip().lower() == "wedding":
            start = datetime.fromisoformat(start_date)
            end = start + timedelta(days=DEFAULT_WEDDING_DAYS - 1)
            end_date = end.date().isoformat()
        else:
            end_date = start_date
    
    try:
        days_count = days_between(start_date, end_date)
    except Exception:
        days_count = 1
    
    per_day_budget = None
    if budget and days_count > 0:
        try:
            per_day_budget = float(budget) / days_count
        except Exception:
            per_day_budget = None
    
    tier_str = _budget_tier(per_day_budget)
    budget_tier = BudgetTier.STANDARD  # Default
    try:
        budget_tier = BudgetTier(tier_str.upper())
    except ValueError:
        pass
    
    # Create context
    context = EventContext(
        event_type=event_type_enum,
        guest_count=guest_count or 100,  # Default guest count
        venue_type=venue_type_enum,
        cultural_requirements=cultural_requirements,
        budget_tier=budget_tier,
        location=location or "Unknown",
        duration_days=days_count,
        total_budget=Decimal(str(budget)) if budget else Decimal('10000.00'),
        special_requirements=[],
        complexity_score=0.0  # Will be calculated by context analyzer
    )
    
    # Analyze context to get complexity score
    analyzed_context = context_analyzer.analyze_context(context)
    return analyzed_context


def _convert_timeline_to_legacy_format(timeline_obj) -> List[Dict]:
    """Convert new Timeline object to legacy format for backward compatibility"""
    legacy_timeline = []
    
    for day in timeline_obj.days:
        # Create summary from activities
        activity_names = [activity.activity.name for activity in day.activities[:3]]  # Top 3 activities
        summary = f"Day {day.day_number}: " + ", ".join(activity_names)
        
        # Create details from activities
        details = []
        for activity in day.activities:
            start_time = activity.start_time.strftime("%H:%M") if activity.start_time != datetime.min else "TBD"
            detail = f"{start_time} - {activity.activity.name}"
            if activity.activity.description:
                detail += f": {activity.activity.description[:50]}..."
            details.append(detail)
        
        # Limit details to 5 items for consistency
        details = details[:5]
        
        legacy_day = {
            "day": day.day_number,
            "date": day.date.isoformat(),
            "summary": summary,
            "estimated_cost": float(day.estimated_cost),
            "details": details
        }
        
        legacy_timeline.append(legacy_day)
    
    return legacy_timeline


def _generate_fallback_timeline(event_type: str, start_date: str, end_date: Optional[str] = None,
                              religion: Optional[str] = None, budget: Optional[float] = None,
                              guest_count: Optional[int] = None, venue_type: Optional[str] = None,
                              location: Optional[str] = None) -> List[Dict]:
    """Generate a basic fallback timeline when enhanced methods fail"""
    
    if not end_date:
        # For birthday/housewarming keep single day. For wedding default to DEFAULT_WEDDING_DAYS
        if event_type.strip().lower() == "wedding":
            start = datetime.fromisoformat(start_date)
            end = start + timedelta(days=DEFAULT_WEDDING_DAYS - 1)
            end_date = end.date().isoformat()
        else:
            end_date = start_date

    # compute number of days
    try:
        days_count = days_between(start_date, end_date)
    except Exception:
        days_count = 1

    # budget per day (if budget provided)
    per_day_budget = None
    if budget and days_count > 0:
        try:
            per_day_budget = float(budget) / days_count
        except Exception:
            per_day_budget = None

    tier_str = _budget_tier(per_day_budget)
    
    # Generate basic timeline based on event type
    timeline = []
    
    for day_num in range(1, days_count + 1):
        current_date = datetime.fromisoformat(start_date) + timedelta(days=day_num - 1)
        
        # Basic activities based on event type
        if event_type.lower() == "wedding":
            if day_num == 1:
                summary = "Pre-wedding ceremonies (Mehendi/Haldi)"
                details = ["Mehendi ceremony", "Haldi ceremony", "Family gathering", "Photography session"]
            elif day_num == 2:
                summary = "Wedding ceremony and reception"
                details = ["Wedding ceremony", "Photo session", "Reception", "Dinner and entertainment"]
            else:
                summary = "Post-wedding celebrations"
                details = ["Family breakfast", "Gift exchange", "Farewell ceremony"]
        elif event_type.lower() == "birthday":
            summary = "Birthday celebration"
            details = ["Guest arrival", "Birthday song and cake cutting", "Games and entertainment", "Food and refreshments", "Gift opening"]
        elif event_type.lower() == "corporate":
            summary = "Corporate event"
            details = ["Registration and welcome", "Opening ceremony", "Presentations", "Networking lunch", "Closing ceremony"]
        elif event_type.lower() == "anniversary":
            summary = "Anniversary celebration"
            details = ["Guest reception", "Anniversary ceremony", "Speeches and toasts", "Dinner", "Entertainment"]
        else:
            summary = f"{event_type.title()} celebration"
            details = ["Event preparation", "Main ceremony", "Refreshments", "Entertainment", "Closing"]
        
        estimated_cost = _estimate_cost_for_day(event_type, tier_str)
        
        day_data = {
            "day": day_num,
            "date": current_date.date().isoformat(),
            "summary": summary,
            "estimated_cost": estimated_cost,
            "details": details,
            "notes": [f"Basic {event_type} timeline - enhance with cultural preferences"],
            "contingency_plans": ["Weather backup plan", "Vendor backup options"]
        }
        
        timeline.append(day_data)
    
    return timeline

def _generate_legacy_timeline(event_type: str, start_date: str, end_date: Optional[str] = None,
                             religion: Optional[str] = None, budget: Optional[float] = None) -> List[Dict]:
    """Legacy timeline generation method as fallback"""
    return _generate_fallback_timeline(event_type, start_date, end_date, religion, budget)


def generate_deep_dive_for_day(event_type: str, start_date: str, end_date: str,
                               religion: Optional[str], day_number: int, budget: Optional[float] = None,
                               guest_count: Optional[int] = None, venue_type: Optional[str] = None,
                               location: Optional[str] = None, **kwargs) -> Dict:
    """
    Enhanced deep dive generation with improved contextual awareness.
    Returns a deeper schedule for a specific day_number (1-based).
    
    New enhanced parameters:
      - guest_count: Number of guests (affects activity timing)
      - venue_type: Type of venue (affects setup and logistics)
      - location: Event location (for regional considerations)
    """
    try:
        # Create enhanced event context
        context = _create_event_context(
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            religion=religion,
            budget=budget,
            guest_count=guest_count,
            venue_type=venue_type,
            location=location,
            **kwargs
        )
        
        # Generate full timeline to get the specific day
        start_date_obj = datetime.fromisoformat(start_date).date()
        timeline_obj = timeline_engine.generate_timeline(context, start_date_obj)
        
        # Find the requested day
        target_day = None
        for day in timeline_obj.days:
            if day.day_number == day_number:
                target_day = day
                break
        
        if not target_day:
            raise ValueError(f"Day {day_number} not found in generated timeline")
        
        # Create enhanced deep dive with contextual awareness
        deep_dive = _create_enhanced_deep_dive(target_day, context)
        
        logger.info(f"Generated enhanced deep dive for day {day_number} using contextual awareness")
        return deep_dive
        
    except Exception as e:
        logger.warning(f"Enhanced deep dive generation failed: {str(e)}, falling back to legacy method")
        # Fallback to legacy deep dive generation
        return _generate_legacy_deep_dive(event_type, start_date, end_date, religion, day_number, budget)


def _create_enhanced_deep_dive(timeline_day, context: EventContext) -> Dict:
    """Create enhanced deep dive with contextual awareness"""
    
    # Create detailed schedule from timeline activities
    schedule = []
    for activity in timeline_day.activities:
        start_time = activity.start_time.strftime("%H:%M") if activity.start_time != datetime.min else "TBD"
        end_time = activity.end_time.strftime("%H:%M") if activity.end_time != datetime.min else "TBD"
        
        # Create detailed activity entry
        activity_entry = {
            "time": f"{start_time} - {end_time}",
            "activity": activity.activity.name,
            "description": activity.activity.description or "",
            "duration": str(activity.activity.duration),
            "priority": activity.activity.priority.value,
            "vendors_needed": activity.activity.required_vendors,
            "estimated_cost": float(activity.activity.estimated_cost)
        }
        
        schedule.append(activity_entry)
    
    # Create contextual notes based on event characteristics
    notes = _generate_contextual_notes(context, timeline_day)
    
    # Create contingency plans based on venue and event type
    contingency_plans = _generate_contingency_plans(context, timeline_day)
    
    # Enhanced deep dive structure
    deep_dive = {
        "day": timeline_day.day_number,
        "date": timeline_day.date.isoformat(),
        "schedule": schedule,
        "notes": notes,
        "contingency_plans": contingency_plans,
        "total_estimated_cost": float(timeline_day.estimated_cost),
        "guest_count_considerations": _get_guest_count_considerations(context.guest_count),
        "venue_specific_tips": _get_venue_specific_tips(context.venue_type),
        "cultural_considerations": _get_cultural_considerations(context.cultural_requirements)
    }
    
    return deep_dive


def _generate_legacy_deep_dive(event_type: str, start_date: str, end_date: str,
                              religion: Optional[str], day_number: int, budget: Optional[float] = None) -> Dict:
    """Generate legacy deep dive as fallback"""
    
    # Basic schedule based on event type
    if event_type.lower() == "wedding":
        schedule = [
            {"time": "07:00 - 09:00", "activity": "Setup and decoration", "description": "Venue preparation and decoration setup"},
            {"time": "09:00 - 11:00", "activity": "Preparation", "description": "Bride/groom preparation and makeup"},
            {"time": "11:00 - 12:00", "activity": "Guest arrival", "description": "Welcome guests and seating"},
            {"time": "12:00 - 14:00", "activity": "Main ceremony", "description": "Wedding ceremony and rituals"},
            {"time": "14:00 - 16:00", "activity": "Lunch", "description": "Wedding feast and socializing"},
            {"time": "16:00 - 18:00", "activity": "Photography", "description": "Photo session with family and friends"},
            {"time": "18:00 - 20:00", "activity": "Evening program", "description": "Entertainment and performances"},
            {"time": "20:00 - 22:00", "activity": "Dinner", "description": "Evening dinner and celebration"},
            {"time": "22:00 - 23:00", "activity": "Wrap-up", "description": "Send-off and cleanup"}
        ]
    else:
        schedule = [
            {"time": "09:00 - 10:00", "activity": "Setup", "description": "Event preparation and setup"},
            {"time": "10:00 - 11:00", "activity": "Guest arrival", "description": "Welcome guests"},
            {"time": "11:00 - 13:00", "activity": "Main event", "description": f"{event_type.title()} celebration"},
            {"time": "13:00 - 14:00", "activity": "Refreshments", "description": "Food and beverages"},
            {"time": "14:00 - 16:00", "activity": "Entertainment", "description": "Activities and entertainment"},
            {"time": "16:00 - 17:00", "activity": "Wrap-up", "description": "Closing and cleanup"}
        ]
    
    return {
        "day": day_number,
        "date": start_date,
        "schedule": schedule,
        "notes": [f"Basic {event_type} schedule for day {day_number}"],
        "contingency_plans": ["Weather backup plan", "Vendor backup options"],
        "total_estimated_cost": _estimate_cost_for_day(event_type, "standard")
    }


# Helper functions for enhanced deep dive
def _generate_contextual_notes(context: EventContext, timeline_day) -> List[str]:
    """Generate contextual notes based on event characteristics"""
    notes = []
    
    if context.guest_count > 200:
        notes.append("Large event: Consider crowd management and multiple entry points")
    
    if context.venue_type == VenueType.OUTDOOR:
        notes.append("Outdoor venue: Have weather backup plans and additional power sources")
    
    if context.budget_tier == BudgetTier.LOW:
        notes.append("Budget-conscious: Focus on essential vendors and DIY where possible")
    
    return notes


def _generate_contingency_plans(context: EventContext, timeline_day) -> List[str]:
    """Generate contingency plans based on venue and event type"""
    plans = []
    
    if context.venue_type == VenueType.OUTDOOR:
        plans.append("Weather contingency: Indoor backup venue or tent rental")
    
    plans.append("Vendor backup: Have secondary vendor contacts ready")
    plans.append("Timeline buffer: Build in 15-30 minute buffers between major activities")
    
    return plans


def _get_guest_count_considerations(guest_count: int) -> List[str]:
    """Get considerations based on guest count"""
    considerations = []
    
    if guest_count > 300:
        considerations.append("Large crowd management needed")
        considerations.append("Multiple service stations recommended")
    elif guest_count < 50:
        considerations.append("Intimate setting allows for personalized touches")
        considerations.append("Single service point sufficient")
    
    return considerations


def _get_venue_specific_tips(venue_type: VenueType) -> List[str]:
    """Get venue-specific tips"""
    tips = {
        VenueType.OUTDOOR: [
            "Check weather forecast 48 hours before",
            "Arrange for additional lighting and power",
            "Have insect repellent available"
        ],
        VenueType.INDOOR: [
            "Ensure adequate ventilation",
            "Check capacity limits",
            "Confirm audio-visual equipment"
        ],
        VenueType.HOME: [
            "Arrange for additional parking",
            "Protect furniture and flooring",
            "Ensure adequate restroom facilities"
        ]
    }
    
    return tips.get(venue_type, ["Standard venue considerations apply"])


def _get_cultural_considerations(cultural_requirements: List[CulturalRequirement]) -> List[str]:
    """Get cultural considerations based on requirements"""
    considerations = []
    
    for req in cultural_requirements:
        if req == CulturalRequirement.HINDU:
            considerations.append("Include traditional rituals and mantras")
            considerations.append("Arrange for priest and puja items")
        elif req == CulturalRequirement.MUSLIM:
            considerations.append("Ensure halal food options")
            considerations.append("Arrange for prayer facilities")
        elif req == CulturalRequirement.CHRISTIAN:
            considerations.append("Include traditional vows and blessings")
            considerations.append("Arrange for officiant")
    
    return considerations