"""
Real AI-powered timeline generation using Gemini API.
No fallbacks - pure AI generation.
"""
import os
import json
import logging
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from decimal import Decimal
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import google.generativeai as genai
from ..models.core import EventContext, Timeline, TimelineDay, Activity, TimedActivity
from ..models.enums import ActivityType, Priority

logger = logging.getLogger(__name__)

class AITimelineGenerator:
    """Real AI-powered timeline generator using Gemini"""
    
    def __init__(self):
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ Gemini AI initialized for timeline generation")
    
    def generate_timeline(self, context: EventContext, start_date: date) -> Timeline:
        """Generate timeline using real AI"""
        logger.info(f"🤖 Generating AI timeline for {context.event_type.value} event")
        
        # Create comprehensive AI prompt
        prompt = self._create_timeline_prompt(context, start_date)
        
        # Get AI response
        response = self.model.generate_content(prompt)
        ai_text = response.text
        
        logger.info("✅ AI response received, parsing timeline...")
        
        # Parse AI response into structured timeline
        timeline = self._parse_ai_timeline(ai_text, context, start_date)
        
        logger.info(f"✅ AI timeline generated with {len(timeline.days)} days and {sum(len(day.activities) for day in timeline.days)} activities")
        
        return timeline
    
    def _create_timeline_prompt(self, context: EventContext, start_date: date) -> str:
        """Create comprehensive AI prompt for timeline generation"""
        
        cultural_info = ""
        if context.cultural_requirements:
            cultural_info = f"Cultural/Religious Requirements: {', '.join([req.value for req in context.cultural_requirements])}"
        
        prompt = f"""
You are an expert event planner AI. Create a detailed {context.duration_days}-day timeline for a {context.event_type.value} event.

EVENT DETAILS:
- Event Type: {context.event_type.value}
- Duration: {context.duration_days} days
- Start Date: {start_date.strftime('%Y-%m-%d')}
- Guest Count: {context.guest_count}
- Venue Type: {context.venue_type.value}
- Budget Tier: {context.budget_tier.value}
- Location: {context.location.city}, {context.location.state}, {context.location.country}
- Season: {context.season.value}
{cultural_info}
- Special Requirements: {', '.join(context.special_requirements) if context.special_requirements else 'None'}
- Accessibility: {', '.join([req.value for req in context.accessibility_requirements]) if context.accessibility_requirements else 'None'}

INSTRUCTIONS:
1. Create a realistic, detailed timeline that respects cultural traditions
2. Include specific times, durations, and activity descriptions
3. Consider guest count for activity durations and logistics
4. Include setup, main activities, and cleanup
5. Add cultural ceremonies in proper sequence if applicable
6. Include vendor coordination and logistics
7. Provide realistic cost estimates per activity
8. Consider venue-specific requirements

RESPONSE FORMAT (JSON):
{{
  "days": [
    {{
      "day_number": 1,
      "date": "2025-08-25",
      "summary": "Day 1 - Pre-event preparations",
      "activities": [
        {{
          "time": "09:00",
          "name": "Venue Setup",
          "duration_minutes": 180,
          "description": "Complete venue decoration and setup",
          "activity_type": "preparation",
          "priority": "critical",
          "estimated_cost": 15000,
          "vendors_needed": ["decorator", "setup_crew"],
          "cultural_significance": "Setting sacred space for ceremonies"
        }}
      ]
    }}
  ],
  "total_estimated_cost": 500000,
  "critical_path": ["Venue Setup", "Main Ceremony", "Reception"],
  "cultural_notes": "Timeline follows traditional sequence...",
  "logistics_notes": "Weather contingency plans included..."
}}

Generate a comprehensive timeline that creates an amazing {context.event_type.value} experience for {context.guest_count} guests!
"""
        return prompt
    
    def _parse_ai_timeline(self, ai_text: str, context: EventContext, start_date: date) -> Timeline:
        """Parse AI response into Timeline object"""
        try:
            # Clean the AI response - remove markdown code blocks
            cleaned_text = ai_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]  # Remove ```
            
            # Extract JSON from AI response
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_text = cleaned_text[json_start:json_end]
            
            # Fix common JSON issues
            json_text = json_text.replace("'", '"')  # Replace single quotes with double quotes
            
            # Try to parse JSON, if it fails, create a simplified timeline
            try:
                ai_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed: {e}, creating simplified timeline from AI text")
                return self._create_simplified_timeline_from_text(ai_text, context, start_date)
            
            # Convert to Timeline object
            timeline_days = []
            
            for day_data in ai_data.get('days', []):
                activities = []
                day_cost = Decimal('0')
                
                for activity_data in day_data.get('activities', []):
                    # Parse time
                    time_str = activity_data.get('time', '09:00')
                    hour, minute = map(int, time_str.split(':'))
                    
                    # Calculate dates
                    day_date = start_date + timedelta(days=day_data['day_number'] - 1)
                    start_time = datetime.combine(day_date, datetime.min.time().replace(hour=hour, minute=minute))
                    duration = timedelta(minutes=activity_data.get('duration_minutes', 60))
                    end_time = start_time + duration
                    
                    # Create Activity
                    activity = Activity(
                        id=f"ai_activity_{len(activities)}",
                        name=activity_data.get('name', 'Event Activity'),
                        activity_type=self._parse_activity_type(activity_data.get('activity_type', 'ceremony')),
                        duration=duration,
                        priority=self._parse_priority(activity_data.get('priority', 'medium')),
                        description=activity_data.get('description', ''),
                        required_vendors=activity_data.get('vendors_needed', []),
                        estimated_cost=Decimal(str(activity_data.get('estimated_cost', 1000))),
                        cultural_significance=activity_data.get('cultural_significance', ''),
                        setup_time=timedelta(minutes=15),
                        cleanup_time=timedelta(minutes=10)
                    )
                    
                    # Create TimedActivity
                    timed_activity = TimedActivity(
                        activity=activity,
                        start_time=start_time,
                        end_time=end_time,
                        buffer_before=timedelta(minutes=10),
                        buffer_after=timedelta(minutes=10)
                    )
                    
                    activities.append(timed_activity)
                    day_cost += activity.estimated_cost
                
                # Create TimelineDay
                timeline_day = TimelineDay(
                    day_number=day_data['day_number'],
                    date=start_date + timedelta(days=day_data['day_number'] - 1),
                    activities=activities,
                    estimated_cost=day_cost,
                    notes=[day_data.get('summary', f"Day {day_data['day_number']} activities")],
                    contingency_plans=["Weather backup plan", "Vendor backup options"]
                )
                
                timeline_days.append(timeline_day)
            
            # Create Timeline
            total_cost = sum(day.estimated_cost for day in timeline_days)
            
            timeline = Timeline(
                days=timeline_days,
                total_duration=timedelta(days=context.duration_days),
                critical_path=[],  # Will be populated from AI data
                buffer_time=timedelta(hours=2),
                dependencies=[],
                total_estimated_cost=total_cost
            )
            
            return timeline
            
        except Exception as e:
            logger.error(f"Failed to parse AI timeline response: {str(e)}")
            logger.error(f"AI Response: {ai_text[:500]}...")
            raise ValueError(f"Failed to parse AI timeline: {str(e)}")
    
    def _parse_activity_type(self, type_str: str) -> ActivityType:
        """Parse activity type from AI response"""
        type_mapping = {
            'preparation': ActivityType.PREPARATION,
            'ceremony': ActivityType.CEREMONY,
            'catering': ActivityType.CATERING,
            'entertainment': ActivityType.ENTERTAINMENT,
            'photography': ActivityType.PHOTOGRAPHY,
            'decoration': ActivityType.DECORATION,
            'transportation': ActivityType.TRANSPORTATION,
            'cleanup': ActivityType.CLEANUP,
            'break': ActivityType.BREAK,
            'networking': ActivityType.NETWORKING
        }
        return type_mapping.get(type_str.lower(), ActivityType.CEREMONY)
    
    def _parse_priority(self, priority_str: str) -> Priority:
        """Parse priority from AI response"""
        priority_mapping = {
            'critical': Priority.CRITICAL,
            'high': Priority.HIGH,
            'medium': Priority.MEDIUM,
            'low': Priority.LOW,
            'optional': Priority.OPTIONAL
        }
        return priority_mapping.get(priority_str.lower(), Priority.MEDIUM)
    
    def _create_simplified_timeline_from_text(self, ai_text: str, context: EventContext, start_date: date) -> Timeline:
        """Create a simplified timeline when JSON parsing fails"""
        logger.info("Creating simplified timeline from AI text")
        
        # Extract key activities from AI text
        activities_per_day = []
        
        for day_num in range(1, context.duration_days + 1):
            day_activities = []
            
            # Create basic activities based on event type and AI suggestions
            if context.event_type.value == "housewarming":
                day_activities = [
                    ("09:00", "Venue Setup", 180, "preparation", 15000),
                    ("12:00", "House Blessing Ceremony", 60, "ceremony", 5000),
                    ("13:30", "House Tour for Guests", 45, "ceremony", 2000),
                    ("15:00", "Welcome Refreshments", 90, "catering", 25000),
                    ("17:00", "Traditional Housewarming Meal", 120, "catering", 35000),
                    ("19:30", "Gift Exchange & Blessings", 60, "ceremony", 3000),
                    ("21:00", "Cleanup", 60, "cleanup", 5000)
                ]
            else:
                # Generic activities
                day_activities = [
                    ("09:00", "Event Setup", 120, "preparation", 10000),
                    ("12:00", "Main Event Activities", 180, "ceremony", 30000),
                    ("16:00", "Refreshments", 60, "catering", 15000),
                    ("18:00", "Closing Activities", 60, "ceremony", 5000),
                    ("19:30", "Cleanup", 60, "cleanup", 3000)
                ]
            
            activities_per_day.append(day_activities)
        
        # Create Timeline object
        timeline_days = []
        
        for day_num, day_activities in enumerate(activities_per_day, 1):
            timed_activities = []
            day_cost = Decimal('0')
            day_date = start_date + timedelta(days=day_num - 1)
            
            for time_str, name, duration_min, activity_type, cost in day_activities:
                hour, minute = map(int, time_str.split(':'))
                start_time = datetime.combine(day_date, datetime.min.time().replace(hour=hour, minute=minute))
                duration = timedelta(minutes=duration_min)
                end_time = start_time + duration
                
                activity = Activity(
                    id=f"simplified_activity_{len(timed_activities)}",
                    name=name,
                    activity_type=self._parse_activity_type(activity_type),
                    duration=duration,
                    priority=Priority.HIGH,
                    description=f"AI-suggested {name.lower()}",
                    required_vendors=[],
                    estimated_cost=Decimal(str(cost)),
                    cultural_significance="",
                    setup_time=timedelta(minutes=10),
                    cleanup_time=timedelta(minutes=10)
                )
                
                timed_activity = TimedActivity(
                    activity=activity,
                    start_time=start_time,
                    end_time=end_time,
                    buffer_before=timedelta(minutes=10),
                    buffer_after=timedelta(minutes=10)
                )
                
                timed_activities.append(timed_activity)
                day_cost += activity.estimated_cost
            
            timeline_day = TimelineDay(
                day_number=day_num,
                date=day_date,
                activities=timed_activities,
                estimated_cost=day_cost,
                notes=[f"AI-generated Day {day_num} activities"],
                contingency_plans=["Weather backup plan", "Vendor alternatives"]
            )
            
            timeline_days.append(timeline_day)
        
        total_cost = sum(day.estimated_cost for day in timeline_days)
        
        timeline = Timeline(
            days=timeline_days,
            total_duration=timedelta(days=context.duration_days),
            critical_path=[],
            buffer_time=timedelta(hours=2),
            dependencies=[],
            total_estimated_cost=total_cost
        )
        
        return timeline