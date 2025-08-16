from supabase import create_client, Client
from app.config import Config
from typing import Optional, Dict, List, Any
import json
from datetime import datetime

class SupabaseClient:
    def __init__(self):
        self.client: Client = create_client(
            Config.SUPABASE_URL, 
            Config.SUPABASE_SERVICE_ROLE_KEY
        )

    def create_event(self, user_id: str, event_data: Dict) -> Dict:
        """Create a new event and return the created event with ID"""
        result = self.client.table("events").insert({
            "user_id": user_id,
            **event_data
        }).execute()
        return result.data[0] if result.data else None

    def get_event(self, event_id: int, user_id: str) -> Optional[Dict]:
        """Get event by ID for specific user"""
        result = self.client.table("events").select("*").eq("id", event_id).eq("user_id", user_id).execute()
        return result.data[0] if result.data else None

    def get_user_events(self, user_id: str) -> List[Dict]:
        """Get all events for a user"""
        result = self.client.table("events").select("*").eq("user_id", user_id).order("created_at", desc=True).execute()
        return result.data or []

    def create_event_days(self, event_days: List[Dict]) -> List[Dict]:
        """Batch create event days"""
        result = self.client.table("event_days").insert(event_days).execute()
        return result.data or []

    def get_event_days(self, event_id: int) -> List[Dict]:
        """Get all days for an event"""
        result = self.client.table("event_days").select("*").eq("event_id", event_id).order("day_number").execute()
        return result.data or []

    def get_event_day(self, event_id: int, day_number: int) -> Optional[Dict]:
        """Get specific day for an event"""
        result = self.client.table("event_days").select("*").eq("event_id", event_id).eq("day_number", day_number).execute()
        return result.data[0] if result.data else None

    def update_event_day_deep_dive(self, event_id: int, day_number: int, deep_dive_data: Dict) -> Dict:
        """Update deep dive data for a specific day"""
        result = self.client.table("event_days").update({
            "deep_dive_data": deep_dive_data
        }).eq("event_id", event_id).eq("day_number", day_number).execute()
        return result.data[0] if result.data else None

    def create_vendors(self, vendors: List[Dict]) -> List[Dict]:
        """Batch create vendors"""
        result = self.client.table("vendors").insert(vendors).execute()
        return result.data or []

    def get_event_vendors(self, event_id: int) -> List[Dict]:
        """Get all vendors for an event"""
        result = self.client.table("vendors").select("*").eq("event_id", event_id).execute()
        return result.data or []

    def get_cached_vendors(self, event_type: str, location: str) -> List[Dict]:
        """Get cached vendors for similar events (optional optimization)"""
        # This is optional - you could cache vendors by event_type + location
        # For now, we'll keep it simple and fetch vendors per event
        return []

    def verify_user_owns_event(self, event_id: int, user_id: str) -> bool:
        """Verify that user owns the event"""
        event = self.get_event(event_id, user_id)
        return event is not None

    # Pattern Learning System Database Methods
    
    def store_event_pattern(self, user_id: str, pattern_data: Dict) -> Optional[Dict]:
        """Store an event pattern in the database"""
        try:
            result = self.client.table("event_patterns").insert({
                "event_id": pattern_data["event_id"],
                "user_id": user_id,
                "event_context": pattern_data["event_context"],
                "timeline_data": pattern_data["timeline_data"],
                "budget_allocation": pattern_data["budget_allocation"],
                "feedback_data": pattern_data["feedback_data"],
                "success_score": pattern_data["success_score"],
                "complexity_score": pattern_data.get("complexity_score", 0),
                "usage_count": pattern_data.get("usage_count", 0),
                "last_used": pattern_data.get("last_used")
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error storing event pattern: {e}")
            return None

    def get_event_patterns(self, user_id: str = None, limit: int = 100) -> List[Dict]:
        """Get event patterns, optionally filtered by user"""
        try:
            query = self.client.table("event_patterns").select("*")
            if user_id:
                query = query.eq("user_id", user_id)
            result = query.order("created_at", desc=True).limit(limit).execute()
            return result.data or []
        except Exception as e:
            print(f"Error retrieving event patterns: {e}")
            return []

    def get_event_pattern_by_id(self, event_id: str) -> Optional[Dict]:
        """Get a specific event pattern by event ID"""
        try:
            result = self.client.table("event_patterns").select("*").eq("event_id", event_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error retrieving event pattern: {e}")
            return None

    def update_pattern_usage(self, event_id: str) -> bool:
        """Update usage statistics for a pattern"""
        try:
            result = self.client.table("event_patterns").update({
                "usage_count": self.client.table("event_patterns").select("usage_count").eq("event_id", event_id).execute().data[0]["usage_count"] + 1,
                "last_used": datetime.now().isoformat()
            }).eq("event_id", event_id).execute()
            return bool(result.data)
        except Exception as e:
            print(f"Error updating pattern usage: {e}")
            return False

    def store_success_pattern(self, pattern_data: Dict) -> Optional[Dict]:
        """Store a success pattern in the database"""
        try:
            result = self.client.table("success_patterns").insert({
                "pattern_type": pattern_data["pattern_type"],
                "event_types": pattern_data["event_types"],
                "conditions": pattern_data["conditions"],
                "recommendations": pattern_data["recommendations"],
                "confidence_score": pattern_data["confidence_score"],
                "supporting_event_count": len(pattern_data["supporting_events"]),
                "supporting_events": pattern_data["supporting_events"]
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error storing success pattern: {e}")
            return None

    def get_success_patterns(self, pattern_type: str = None, event_type: str = None) -> List[Dict]:
        """Get success patterns, optionally filtered by type"""
        try:
            query = self.client.table("success_patterns").select("*")
            if pattern_type:
                query = query.eq("pattern_type", pattern_type)
            if event_type:
                query = query.contains("event_types", [event_type])
            result = query.order("confidence_score", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Error retrieving success patterns: {e}")
            return []

    def update_success_pattern(self, pattern_id: str, pattern_data: Dict) -> Optional[Dict]:
        """Update an existing success pattern"""
        try:
            result = self.client.table("success_patterns").update({
                "conditions": pattern_data["conditions"],
                "recommendations": pattern_data["recommendations"],
                "confidence_score": pattern_data["confidence_score"],
                "supporting_event_count": len(pattern_data["supporting_events"]),
                "supporting_events": pattern_data["supporting_events"]
            }).eq("id", pattern_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error updating success pattern: {e}")
            return None

    def store_feedback_analysis(self, analysis_data: Dict) -> Optional[Dict]:
        """Store feedback analysis results"""
        try:
            result = self.client.table("feedback_analyses").upsert({
                "event_type": analysis_data["event_type"],
                "budget_tier": analysis_data.get("budget_tier"),
                "analysis_data": analysis_data["analysis_data"],
                "feedback_count": analysis_data["feedback_count"],
                "reliability_score": analysis_data["reliability_score"]
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error storing feedback analysis: {e}")
            return None

    def get_feedback_analysis(self, event_type: str, budget_tier: str = None) -> Optional[Dict]:
        """Get feedback analysis for event type and budget tier"""
        try:
            query = self.client.table("feedback_analyses").select("*").eq("event_type", event_type)
            if budget_tier:
                query = query.eq("budget_tier", budget_tier)
            else:
                query = query.is_("budget_tier", "null")
            result = query.execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error retrieving feedback analysis: {e}")
            return None

    def store_recommendation_adjustment(self, adjustment_data: Dict) -> Optional[Dict]:
        """Store a recommendation adjustment"""
        try:
            result = self.client.table("recommendation_adjustments").insert({
                "adjustment_type": adjustment_data["adjustment_type"],
                "target_category": adjustment_data["target_category"],
                "adjustment_factor": adjustment_data["adjustment_factor"],
                "confidence": adjustment_data["confidence"],
                "reasoning": adjustment_data["reasoning"],
                "supporting_feedback_count": adjustment_data["supporting_feedback_count"],
                "event_type": adjustment_data["event_type"],
                "is_active": adjustment_data.get("is_active", True)
            }).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            print(f"Error storing recommendation adjustment: {e}")
            return None

    def get_recommendation_adjustments(self, event_type: str = None, adjustment_type: str = None, active_only: bool = True) -> List[Dict]:
        """Get recommendation adjustments, optionally filtered"""
        try:
            query = self.client.table("recommendation_adjustments").select("*")
            if event_type:
                query = query.eq("event_type", event_type)
            if adjustment_type:
                query = query.eq("adjustment_type", adjustment_type)
            if active_only:
                query = query.eq("is_active", True)
            result = query.order("confidence", desc=True).execute()
            return result.data or []
        except Exception as e:
            print(f"Error retrieving recommendation adjustments: {e}")
            return []

    def search_similar_patterns(self, event_context: Dict, similarity_threshold: float = 0.6, limit: int = 10) -> List[Dict]:
        """Search for similar event patterns based on context"""
        try:
            # For now, we'll do a simple search based on event type and guest count range
            # In a production system, you might want to use more sophisticated similarity search
            event_type = event_context.get("event_type")
            guest_count = event_context.get("guest_count", 0)
            venue_type = event_context.get("venue_type")
            
            query = self.client.table("event_patterns").select("*")
            
            # Filter by event type if available
            if event_type:
                query = query.eq("event_context->>event_type", event_type)
            
            # Filter by similar guest count (within 50% range)
            if guest_count > 0:
                min_guests = int(guest_count * 0.5)
                max_guests = int(guest_count * 1.5)
                query = query.gte("event_context->>guest_count", str(min_guests))
                query = query.lte("event_context->>guest_count", str(max_guests))
            
            # Filter by venue type if available
            if venue_type:
                query = query.eq("event_context->>venue_type", venue_type)
            
            result = query.order("success_score", desc=True).limit(limit).execute()
            return result.data or []
        except Exception as e:
            print(f"Error searching similar patterns: {e}")
            return []
