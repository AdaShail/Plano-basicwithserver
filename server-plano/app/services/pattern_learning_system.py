"""
Pattern Learning System for intelligent event planning.

This module implements event similarity matching, pattern storage, and learning
from historical event data to improve future recommendations.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
from decimal import Decimal
import math
import json
from collections import defaultdict

from ..models.core import (
    EventContext, EventFeedback, Timeline, BudgetAllocation,
    CategoryAllocation, Alternative
)
from ..models.enums import (
    EventType, VenueType, BudgetTier, Season, CulturalRequirement,
    BudgetCategory, Priority
)


@dataclass
class EventPattern:
    """Stored pattern from a successful event"""
    event_id: str
    context: EventContext
    timeline: Timeline
    budget_allocation: BudgetAllocation
    feedback: EventFeedback
    success_score: float
    created_at: datetime
    usage_count: int = 0
    last_used: Optional[datetime] = None
    
    def validate(self) -> List[str]:
        """Validate event pattern data"""
        errors = []
        
        if not self.event_id or not self.event_id.strip():
            errors.append("Event ID is required")
        
        if self.success_score < 0 or self.success_score > 10:
            errors.append("Success score must be between 0 and 10")
        
        if self.usage_count < 0:
            errors.append("Usage count cannot be negative")
        
        # Validate nested objects
        errors.extend(self.context.validate())
        errors.extend(self.timeline.validate())
        errors.extend(self.budget_allocation.validate())
        errors.extend(self.feedback.validate())
        
        return errors


@dataclass
class SimilarEvent:
    """Event similar to the current context"""
    pattern: EventPattern
    similarity_score: float
    matching_factors: List[str]
    differences: List[str]
    
    def validate(self) -> List[str]:
        """Validate similar event data"""
        errors = []
        
        if self.similarity_score < 0 or self.similarity_score > 1:
            errors.append("Similarity score must be between 0 and 1")
        
        errors.extend(self.pattern.validate())
        
        return errors


@dataclass
class SuccessPattern:
    """Pattern extracted from successful events"""
    pattern_type: str  # "timeline", "budget", "activity_sequence", etc.
    event_types: List[EventType]
    conditions: Dict[str, Any]
    recommendations: Dict[str, Any]
    confidence_score: float
    supporting_events: List[str]
    
    def validate(self) -> List[str]:
        """Validate success pattern data"""
        errors = []
        
        if not self.pattern_type or not self.pattern_type.strip():
            errors.append("Pattern type is required")
        
        if not self.event_types:
            errors.append("At least one event type is required")
        
        if self.confidence_score < 0 or self.confidence_score > 1:
            errors.append("Confidence score must be between 0 and 1")
        
        if not self.supporting_events:
            errors.append("At least one supporting event is required")
        
        return errors


class EventSimilarityMatcher:
    """Matches events based on similarity of characteristics"""
    
    def __init__(self):
        self.feature_weights = {
            'event_type': 0.25,
            'guest_count': 0.20,
            'venue_type': 0.15,
            'cultural_requirements': 0.15,
            'budget_tier': 0.10,
            'season': 0.05,
            'location': 0.05,
            'duration': 0.05
        }
    
    def calculate_similarity(self, context1: EventContext, context2: EventContext) -> float:
        """
        Calculate similarity score between two event contexts.
        
        Args:
            context1: First event context
            context2: Second event context
            
        Returns:
            Similarity score between 0 and 1 (1 being identical)
        """
        total_score = 0.0
        
        # Event type similarity
        event_type_score = 1.0 if context1.event_type == context2.event_type else 0.0
        total_score += event_type_score * self.feature_weights['event_type']
        
        # Guest count similarity (using exponential decay)
        guest_diff = abs(context1.guest_count - context2.guest_count)
        max_guest_diff = max(context1.guest_count, context2.guest_count)
        guest_score = math.exp(-guest_diff / (max_guest_diff * 0.3)) if max_guest_diff > 0 else 1.0
        total_score += guest_score * self.feature_weights['guest_count']
        
        # Venue type similarity
        venue_score = self._calculate_venue_similarity(context1.venue_type, context2.venue_type)
        total_score += venue_score * self.feature_weights['venue_type']
        
        # Cultural requirements similarity
        cultural_score = self._calculate_cultural_similarity(
            context1.cultural_requirements, context2.cultural_requirements
        )
        total_score += cultural_score * self.feature_weights['cultural_requirements']
        
        # Budget tier similarity
        budget_score = self._calculate_budget_tier_similarity(context1.budget_tier, context2.budget_tier)
        total_score += budget_score * self.feature_weights['budget_tier']
        
        # Season similarity
        season_score = 1.0 if context1.season == context2.season else 0.0
        total_score += season_score * self.feature_weights['season']
        
        # Location similarity
        location_score = self._calculate_location_similarity(context1.location, context2.location)
        total_score += location_score * self.feature_weights['location']
        
        # Duration similarity
        duration_diff = abs(context1.duration_days - context2.duration_days)
        max_duration = max(context1.duration_days, context2.duration_days)
        duration_score = math.exp(-duration_diff / (max_duration * 0.5)) if max_duration > 0 else 1.0
        total_score += duration_score * self.feature_weights['duration']
        
        return min(total_score, 1.0)
    
    def _calculate_venue_similarity(self, venue1: VenueType, venue2: VenueType) -> float:
        """Calculate similarity between venue types"""
        if venue1 == venue2:
            return 1.0
        
        # Define venue similarity groups
        indoor_venues = {VenueType.INDOOR, VenueType.BANQUET_HALL, VenueType.HOTEL, 
                        VenueType.RESTAURANT, VenueType.COMMUNITY_CENTER}
        outdoor_venues = {VenueType.OUTDOOR, VenueType.GARDEN, VenueType.BEACH}
        religious_venues = {VenueType.TEMPLE, VenueType.CHURCH}
        
        # Check if both venues are in the same group
        if (venue1 in indoor_venues and venue2 in indoor_venues) or \
           (venue1 in outdoor_venues and venue2 in outdoor_venues) or \
           (venue1 in religious_venues and venue2 in religious_venues):
            return 0.7
        
        # Hybrid venues are somewhat similar to both indoor and outdoor
        if venue1 == VenueType.HYBRID or venue2 == VenueType.HYBRID:
            return 0.5
        
        return 0.0
    
    def _calculate_cultural_similarity(self, cultural1: List[CulturalRequirement], 
                                     cultural2: List[CulturalRequirement]) -> float:
        """Calculate similarity between cultural requirements"""
        if not cultural1 and not cultural2:
            return 1.0
        
        if not cultural1 or not cultural2:
            return 0.0
        
        set1 = set(cultural1)
        set2 = set(cultural2)
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_budget_tier_similarity(self, tier1: BudgetTier, tier2: BudgetTier) -> float:
        """Calculate similarity between budget tiers"""
        if tier1 == tier2:
            return 1.0
        
        # Define tier ordering
        tier_order = {
            BudgetTier.LOW: 0,
            BudgetTier.STANDARD: 1,
            BudgetTier.PREMIUM: 2,
            BudgetTier.LUXURY: 3
        }
        
        diff = abs(tier_order[tier1] - tier_order[tier2])
        return max(0.0, 1.0 - (diff * 0.4))
    
    def _calculate_location_similarity(self, loc1, loc2) -> float:
        """Calculate similarity between locations"""
        if loc1.city == loc2.city and loc1.state == loc2.state:
            return 1.0
        elif loc1.state == loc2.state:
            return 0.7
        elif loc1.country == loc2.country:
            return 0.3
        else:
            return 0.0
    
    def identify_matching_factors(self, context1: EventContext, context2: EventContext) -> List[str]:
        """Identify specific factors that match between two contexts"""
        matching_factors = []
        
        if context1.event_type == context2.event_type:
            matching_factors.append(f"Same event type: {context1.event_type.value}")
        
        guest_diff_percent = abs(context1.guest_count - context2.guest_count) / max(context1.guest_count, context2.guest_count)
        if guest_diff_percent < 0.2:
            matching_factors.append(f"Similar guest count: {context1.guest_count} vs {context2.guest_count}")
        
        if context1.venue_type == context2.venue_type:
            matching_factors.append(f"Same venue type: {context1.venue_type.value}")
        
        common_cultural = set(context1.cultural_requirements).intersection(set(context2.cultural_requirements))
        if common_cultural:
            matching_factors.append(f"Common cultural requirements: {[c.value for c in common_cultural]}")
        
        if context1.budget_tier == context2.budget_tier:
            matching_factors.append(f"Same budget tier: {context1.budget_tier.value}")
        
        if context1.season == context2.season:
            matching_factors.append(f"Same season: {context1.season.value}")
        
        if context1.location.city == context2.location.city:
            matching_factors.append(f"Same city: {context1.location.city}")
        elif context1.location.state == context2.location.state:
            matching_factors.append(f"Same state: {context1.location.state}")
        
        if context1.duration_days == context2.duration_days:
            matching_factors.append(f"Same duration: {context1.duration_days} days")
        
        return matching_factors
    
    def identify_differences(self, context1: EventContext, context2: EventContext) -> List[str]:
        """Identify key differences between two contexts"""
        differences = []
        
        if context1.event_type != context2.event_type:
            differences.append(f"Different event types: {context1.event_type.value} vs {context2.event_type.value}")
        
        guest_diff_percent = abs(context1.guest_count - context2.guest_count) / max(context1.guest_count, context2.guest_count)
        if guest_diff_percent > 0.3:
            differences.append(f"Significantly different guest counts: {context1.guest_count} vs {context2.guest_count}")
        
        if context1.venue_type != context2.venue_type:
            differences.append(f"Different venue types: {context1.venue_type.value} vs {context2.venue_type.value}")
        
        cultural_diff = set(context1.cultural_requirements).symmetric_difference(set(context2.cultural_requirements))
        if cultural_diff:
            differences.append(f"Different cultural requirements: {[c.value for c in cultural_diff]}")
        
        if context1.budget_tier != context2.budget_tier:
            differences.append(f"Different budget tiers: {context1.budget_tier.value} vs {context2.budget_tier.value}")
        
        if context1.season != context2.season:
            differences.append(f"Different seasons: {context1.season.value} vs {context2.season.value}")
        
        if context1.location.state != context2.location.state:
            differences.append(f"Different locations: {context1.location.city}, {context1.location.state} vs {context2.location.city}, {context2.location.state}")
        
        duration_diff = abs(context1.duration_days - context2.duration_days)
        if duration_diff > 1:
            differences.append(f"Different durations: {context1.duration_days} vs {context2.duration_days} days")
        
        return differences


@dataclass
class FeedbackAnalysis:
    """Analysis results from feedback data"""
    average_timeline_rating: float
    average_budget_accuracy: float
    average_overall_satisfaction: float
    common_positive_feedback: List[str]
    common_improvement_areas: List[str]
    budget_variance_analysis: Dict[BudgetCategory, Dict[str, float]]
    timeline_deviation_patterns: List[str]
    success_factors: List[str]
    
    def validate(self) -> List[str]:
        """Validate feedback analysis data"""
        errors = []
        
        for rating_name, rating_value in [
            ("average_timeline_rating", self.average_timeline_rating),
            ("average_budget_accuracy", self.average_budget_accuracy),
            ("average_overall_satisfaction", self.average_overall_satisfaction)
        ]:
            if rating_value < 1 or rating_value > 5:
                errors.append(f"{rating_name} must be between 1 and 5")
        
        return errors


@dataclass
class RecommendationAdjustment:
    """Adjustment to recommendations based on feedback patterns"""
    adjustment_type: str  # "timeline", "budget", "activity", "vendor"
    target_category: str
    adjustment_factor: float
    confidence: float
    reasoning: str
    supporting_feedback_count: int
    
    def validate(self) -> List[str]:
        """Validate recommendation adjustment data"""
        errors = []
        
        if not self.adjustment_type or not self.adjustment_type.strip():
            errors.append("Adjustment type is required")
        
        if not self.target_category or not self.target_category.strip():
            errors.append("Target category is required")
        
        if self.confidence < 0 or self.confidence > 1:
            errors.append("Confidence must be between 0 and 1")
        
        if self.supporting_feedback_count < 1:
            errors.append("Supporting feedback count must be at least 1")
        
        return errors


class PatternLearningSystem:
    """Main pattern learning system for event planning intelligence"""
    
    def __init__(self, use_database: bool = True, use_cache: bool = True):
        self.similarity_matcher = EventSimilarityMatcher()
        self.use_database = use_database
        self.use_cache = use_cache
        
        # In-memory storage (for backward compatibility and caching)
        self.patterns: Dict[str, EventPattern] = {}
        self.success_patterns: List[SuccessPattern] = []
        self.feedback_analyses: Dict[str, FeedbackAnalysis] = {}  # Key: event_type_budget_tier
        self.recommendation_adjustments: List[RecommendationAdjustment] = []
        
        # Cache service
        self.pattern_cache = None
        if self.use_cache:
            try:
                from ..utils.cache_service import get_pattern_cache_service
                self.pattern_cache = get_pattern_cache_service()
            except ImportError:
                print("Warning: Cache service not available, disabling caching")
                self.use_cache = False
        
        # Database client (only initialized if using database)
        self.db_client = None
        if self.use_database:
            try:
                from ..utils.supabase_client import SupabaseClient
                self.db_client = SupabaseClient()
            except ImportError:
                print("Warning: Database client not available, falling back to in-memory storage")
                self.use_database = False
        
        self.min_similarity_threshold = 0.6
        self.min_success_score = 3.5  # Minimum feedback score to consider successful
        self.min_feedback_count = 3  # Minimum feedback count for reliable analysis
    
    def record_event_outcome(self, event_id: str, context: EventContext, 
                           timeline: Timeline, budget_allocation: BudgetAllocation,
                           feedback: EventFeedback, user_id: str = None) -> None:
        """
        Record an event outcome for pattern learning.
        
        Args:
            event_id: Unique identifier for the event
            context: Event context information
            timeline: Generated timeline
            budget_allocation: Budget allocation
            feedback: User feedback on the event
            user_id: User ID for database storage
        """
        # Calculate success score from feedback
        success_score = self._calculate_success_score(feedback)
        
        # Create and store pattern
        pattern = EventPattern(
            event_id=event_id,
            context=context,
            timeline=timeline,
            budget_allocation=budget_allocation,
            feedback=feedback,
            success_score=success_score,
            created_at=datetime.now()
        )
        
        # Store in memory
        self.patterns[event_id] = pattern
        
        # Cache the pattern
        if self.use_cache and self.pattern_cache:
            self.pattern_cache.cache_event_pattern(event_id, pattern)
        
        # Store in database if available
        if self.use_database and self.db_client and user_id:
            pattern_data = {
                "event_id": event_id,
                "event_context": self._serialize_event_context(context),
                "timeline_data": self._serialize_timeline(timeline),
                "budget_allocation": self._serialize_budget_allocation(budget_allocation),
                "feedback_data": self._serialize_feedback(feedback),
                "success_score": float(success_score),
                "complexity_score": float(context.complexity_score),
                "usage_count": 0
            }
            self.db_client.store_event_pattern(user_id, pattern_data)
        
        # Update success patterns if this was a successful event
        if success_score >= self.min_success_score:
            self._update_success_patterns(pattern)
            
        # Invalidate related caches
        if self.use_cache and self.pattern_cache:
            # Invalidate similar events cache for this context type
            context_hash = self.pattern_cache.generate_context_hash(context)
            self.pattern_cache.cache.delete_pattern(f"similar:*")
    
    def find_similar_events(self, context: EventContext, limit: int = 10) -> List[SimilarEvent]:
        """
        Find events similar to the given context.
        
        Args:
            context: Event context to match against
            limit: Maximum number of similar events to return
            
        Returns:
            List of similar events sorted by similarity score
        """
        # Check cache first
        if self.use_cache and self.pattern_cache:
            context_hash = self.pattern_cache.generate_context_hash(context)
            cached_similar = self.pattern_cache.get_similar_events(context_hash)
            if cached_similar:
                return cached_similar[:limit]
        
        similar_events = []
        patterns_to_check = []
        
        # Load patterns from database if available
        if self.use_database and self.db_client:
            try:
                # Search for potentially similar patterns in database
                context_dict = self._serialize_event_context(context)
                db_patterns = self.db_client.search_similar_patterns(context_dict, self.min_similarity_threshold, limit * 2)
                
                # Convert database patterns to EventPattern objects
                for db_pattern in db_patterns:
                    pattern = self._deserialize_event_pattern(db_pattern)
                    if pattern:
                        patterns_to_check.append(pattern)
                        # Cache in memory for future use
                        self.patterns[pattern.event_id] = pattern
                        # Cache individual pattern
                        if self.use_cache and self.pattern_cache:
                            self.pattern_cache.cache_event_pattern(pattern.event_id, pattern)
            except Exception as e:
                print(f"Error loading patterns from database: {e}")
        
        # Also check in-memory patterns
        patterns_to_check.extend(self.patterns.values())
        
        # Remove duplicates based on event_id
        unique_patterns = {}
        for pattern in patterns_to_check:
            unique_patterns[pattern.event_id] = pattern
        
        # Calculate similarity for each pattern
        for pattern in unique_patterns.values():
            similarity_score = self.similarity_matcher.calculate_similarity(context, pattern.context)
            
            if similarity_score >= self.min_similarity_threshold:
                matching_factors = self.similarity_matcher.identify_matching_factors(context, pattern.context)
                differences = self.similarity_matcher.identify_differences(context, pattern.context)
                
                similar_event = SimilarEvent(
                    pattern=pattern,
                    similarity_score=similarity_score,
                    matching_factors=matching_factors,
                    differences=differences
                )
                
                similar_events.append(similar_event)
        
        # Sort by similarity score (descending) and success score (descending)
        similar_events.sort(key=lambda x: (x.similarity_score, x.pattern.success_score), reverse=True)
        
        # Update usage statistics
        for similar_event in similar_events[:limit]:
            similar_event.pattern.usage_count += 1
            similar_event.pattern.last_used = datetime.now()
            
            # Update usage in database if available
            if self.use_database and self.db_client:
                self.db_client.update_pattern_usage(similar_event.pattern.event_id)
        
        # Cache the results
        if self.use_cache and self.pattern_cache:
            context_hash = self.pattern_cache.generate_context_hash(context)
            self.pattern_cache.cache_similar_events(context_hash, similar_events)
        
        return similar_events[:limit]
    
    def get_success_patterns(self, event_type: EventType, filters: Dict[str, Any] = None) -> List[SuccessPattern]:
        """
        Get success patterns for a specific event type with optional filters.
        
        Args:
            event_type: Type of event to get patterns for
            filters: Optional filters to apply
            
        Returns:
            List of relevant success patterns
        """
        # Check cache first
        if self.use_cache and self.pattern_cache and not filters:
            cached_patterns = self.pattern_cache.get_success_patterns(event_type)
            if cached_patterns:
                return cached_patterns
        
        relevant_patterns = []
        
        for pattern in self.success_patterns:
            if event_type in pattern.event_types:
                # Apply filters if provided
                if filters:
                    if not self._pattern_matches_filters(pattern, filters):
                        continue
                
                relevant_patterns.append(pattern)
        
        # Sort by confidence score
        relevant_patterns.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Cache the results if no filters were applied
        if self.use_cache and self.pattern_cache and not filters:
            self.pattern_cache.cache_success_patterns(event_type, relevant_patterns)
        
        return relevant_patterns
    
    def update_recommendations(self, patterns: List[SuccessPattern]) -> Dict[str, Any]:
        """
        Update recommendations based on success patterns.
        
        Args:
            patterns: List of success patterns to incorporate
            
        Returns:
            Updated recommendation adjustments
        """
        recommendations = {
            'timeline_adjustments': {},
            'budget_adjustments': {},
            'activity_suggestions': [],
            'vendor_preferences': {}
        }
        
        for pattern in patterns:
            if pattern.confidence_score >= 0.7:  # High confidence patterns only
                # Merge pattern recommendations
                for key, value in pattern.recommendations.items():
                    if key in recommendations:
                        if isinstance(recommendations[key], dict) and isinstance(value, dict):
                            recommendations[key].update(value)
                        elif isinstance(recommendations[key], list) and isinstance(value, list):
                            recommendations[key].extend(value)
                        else:
                            recommendations[key] = value
        
        return recommendations
    
    def _calculate_success_score(self, feedback: EventFeedback) -> float:
        """Calculate overall success score from feedback"""
        # Weighted average of different feedback metrics
        weights = {
            'timeline_rating': 0.4,
            'budget_accuracy': 0.3,
            'overall_satisfaction': 0.3
        }
        
        score = (
            feedback.timeline_rating * weights['timeline_rating'] +
            feedback.budget_accuracy * weights['budget_accuracy'] +
            feedback.overall_satisfaction * weights['overall_satisfaction']
        )
        
        return score
    
    def _update_success_patterns(self, pattern: EventPattern) -> None:
        """Update success patterns based on a successful event"""
        # Extract timeline patterns
        self._extract_timeline_patterns(pattern)
        
        # Extract budget patterns
        self._extract_budget_patterns(pattern)
        
        # Extract activity sequence patterns
        self._extract_activity_patterns(pattern)
    
    def _extract_timeline_patterns(self, pattern: EventPattern) -> None:
        """Extract timeline-related success patterns"""
        # Example: Extract patterns about activity durations, buffer times, etc.
        timeline_pattern = SuccessPattern(
            pattern_type="timeline_duration",
            event_types=[pattern.context.event_type],
            conditions={
                "guest_count_range": self._get_guest_count_range(pattern.context.guest_count),
                "venue_type": pattern.context.venue_type.value,
                "duration_days": pattern.context.duration_days
            },
            recommendations={
                "total_duration": pattern.timeline.total_duration.total_seconds(),
                "buffer_time_ratio": pattern.timeline.buffer_time.total_seconds() / pattern.timeline.total_duration.total_seconds(),
                "activities_per_day": len(pattern.timeline.days[0].activities) if pattern.timeline.days else 0
            },
            confidence_score=pattern.success_score / 5.0,  # Convert to 0-1 scale
            supporting_events=[pattern.event_id]
        )
        
        # Check if similar pattern exists and merge or add new
        self._merge_or_add_pattern(timeline_pattern)
    
    def _extract_budget_patterns(self, pattern: EventPattern) -> None:
        """Extract budget-related success patterns"""
        budget_pattern = SuccessPattern(
            pattern_type="budget_allocation",
            event_types=[pattern.context.event_type],
            conditions={
                "budget_tier": pattern.context.budget_tier.value,
                "guest_count_range": self._get_guest_count_range(pattern.context.guest_count),
                "venue_type": pattern.context.venue_type.value
            },
            recommendations={
                "category_percentages": {
                    category.value: allocation.percentage 
                    for category, allocation in pattern.budget_allocation.categories.items()
                },
                "per_person_cost": float(pattern.budget_allocation.per_person_cost),
                "contingency_percentage": pattern.budget_allocation.contingency_percentage
            },
            confidence_score=pattern.success_score / 5.0,
            supporting_events=[pattern.event_id]
        )
        
        self._merge_or_add_pattern(budget_pattern)
    
    def _extract_activity_patterns(self, pattern: EventPattern) -> None:
        """Extract activity sequence and timing patterns"""
        if not pattern.timeline.days:
            return
        
        # Extract activity sequences from the first day as an example
        first_day = pattern.timeline.days[0]
        activity_sequence = [activity.activity.activity_type.value for activity in first_day.activities]
        
        activity_pattern = SuccessPattern(
            pattern_type="activity_sequence",
            event_types=[pattern.context.event_type],
            conditions={
                "cultural_requirements": [req.value for req in pattern.context.cultural_requirements],
                "venue_type": pattern.context.venue_type.value
            },
            recommendations={
                "activity_sequence": activity_sequence,
                "activity_durations": {
                    activity.activity.activity_type.value: activity.activity.duration.total_seconds()
                    for activity in first_day.activities
                }
            },
            confidence_score=pattern.success_score / 5.0,
            supporting_events=[pattern.event_id]
        )
        
        self._merge_or_add_pattern(activity_pattern)
    
    def _get_guest_count_range(self, guest_count: int) -> str:
        """Get guest count range category"""
        if guest_count <= 50:
            return "small"
        elif guest_count <= 150:
            return "medium"
        elif guest_count <= 300:
            return "large"
        else:
            return "very_large"
    
    def _merge_or_add_pattern(self, new_pattern: SuccessPattern) -> None:
        """Merge with existing similar pattern or add as new"""
        for existing_pattern in self.success_patterns:
            if (existing_pattern.pattern_type == new_pattern.pattern_type and
                existing_pattern.event_types == new_pattern.event_types and
                existing_pattern.conditions == new_pattern.conditions):
                
                # Merge patterns
                existing_pattern.supporting_events.extend(new_pattern.supporting_events)
                
                # Update confidence score (weighted average)
                total_events = len(existing_pattern.supporting_events)
                existing_weight = (total_events - 1) / total_events
                new_weight = 1 / total_events
                existing_pattern.confidence_score = (
                    existing_pattern.confidence_score * existing_weight +
                    new_pattern.confidence_score * new_weight
                )
                
                # Merge recommendations (take average for numeric values)
                for key, value in new_pattern.recommendations.items():
                    if key in existing_pattern.recommendations:
                        if isinstance(value, (int, float)):
                            existing_pattern.recommendations[key] = (
                                existing_pattern.recommendations[key] * existing_weight +
                                value * new_weight
                            )
                    else:
                        existing_pattern.recommendations[key] = value
                
                return
        
        # No similar pattern found, add as new
        self.success_patterns.append(new_pattern)
    
    def _pattern_matches_filters(self, pattern: SuccessPattern, filters: Dict[str, Any]) -> bool:
        """Check if pattern matches the given filters"""
        for filter_key, filter_value in filters.items():
            if filter_key in pattern.conditions:
                if pattern.conditions[filter_key] != filter_value:
                    return False
        return True
    
    def collect_feedback_batch(self, feedback_list: List[EventFeedback]) -> None:
        """
        Collect multiple feedback entries for batch analysis.
        
        Args:
            feedback_list: List of feedback entries to process
        """
        for feedback in feedback_list:
            # Validate feedback
            errors = feedback.validate()
            if errors:
                continue  # Skip invalid feedback
            
            # Update existing pattern if it exists
            if feedback.event_id in self.patterns:
                pattern = self.patterns[feedback.event_id]
                pattern.feedback = feedback
                pattern.success_score = self._calculate_success_score(feedback)
                
                # Update success patterns if this became successful
                if pattern.success_score >= self.min_success_score:
                    self._update_success_patterns(pattern)
    
    def analyze_feedback_patterns(self, event_type: EventType, budget_tier: BudgetTier = None) -> FeedbackAnalysis:
        """
        Analyze feedback patterns for a specific event type and budget tier.
        
        Args:
            event_type: Type of event to analyze
            budget_tier: Optional budget tier filter
            
        Returns:
            Analysis of feedback patterns
        """
        # Filter patterns by event type and budget tier
        relevant_patterns = []
        for pattern in self.patterns.values():
            if pattern.context.event_type == event_type:
                if budget_tier is None or pattern.context.budget_tier == budget_tier:
                    relevant_patterns.append(pattern)
        
        if len(relevant_patterns) < self.min_feedback_count:
            # Not enough data for reliable analysis
            return self._create_default_feedback_analysis()
        
        # Calculate average ratings
        timeline_ratings = [p.feedback.timeline_rating for p in relevant_patterns]
        budget_ratings = [p.feedback.budget_accuracy for p in relevant_patterns]
        satisfaction_ratings = [p.feedback.overall_satisfaction for p in relevant_patterns]
        
        avg_timeline = sum(timeline_ratings) / len(timeline_ratings)
        avg_budget = sum(budget_ratings) / len(budget_ratings)
        avg_satisfaction = sum(satisfaction_ratings) / len(satisfaction_ratings)
        
        # Analyze common feedback themes
        positive_feedback = []
        improvement_areas = []
        
        for pattern in relevant_patterns:
            positive_feedback.extend(pattern.feedback.what_worked_well)
            improvement_areas.extend(pattern.feedback.what_could_improve)
        
        common_positive = self._find_common_themes(positive_feedback)
        common_improvements = self._find_common_themes(improvement_areas)
        
        # Analyze budget variances
        budget_variance = self._analyze_budget_variances(relevant_patterns)
        
        # Analyze timeline deviations
        timeline_deviations = []
        for pattern in relevant_patterns:
            timeline_deviations.extend(pattern.feedback.timeline_deviations)
        
        deviation_patterns = self._find_common_themes(timeline_deviations)
        
        # Identify success factors
        success_factors = self._identify_success_factors(relevant_patterns)
        
        analysis = FeedbackAnalysis(
            average_timeline_rating=avg_timeline,
            average_budget_accuracy=avg_budget,
            average_overall_satisfaction=avg_satisfaction,
            common_positive_feedback=common_positive,
            common_improvement_areas=common_improvements,
            budget_variance_analysis=budget_variance,
            timeline_deviation_patterns=deviation_patterns,
            success_factors=success_factors
        )
        
        # Cache the analysis
        cache_key = f"{event_type.value}_{budget_tier.value if budget_tier else 'all'}"
        self.feedback_analyses[cache_key] = analysis
        
        return analysis
    
    def extract_recommendation_adjustments(self, analysis: FeedbackAnalysis, 
                                         event_type: EventType) -> List[RecommendationAdjustment]:
        """
        Extract recommendation adjustments based on feedback analysis.
        
        Args:
            analysis: Feedback analysis results
            event_type: Event type being analyzed
            
        Returns:
            List of recommendation adjustments
        """
        adjustments = []
        
        # Timeline adjustments based on common improvement areas
        timeline_adjustments = self._extract_timeline_adjustments(analysis, event_type)
        adjustments.extend(timeline_adjustments)
        
        # Budget adjustments based on variance analysis
        budget_adjustments = self._extract_budget_adjustments(analysis, event_type)
        adjustments.extend(budget_adjustments)
        
        # Activity adjustments based on success factors
        activity_adjustments = self._extract_activity_adjustments(analysis, event_type)
        adjustments.extend(activity_adjustments)
        
        # Vendor adjustments based on feedback patterns
        vendor_adjustments = self._extract_vendor_adjustments(analysis, event_type)
        adjustments.extend(vendor_adjustments)
        
        return adjustments
    
    def apply_recommendation_adjustments(self, adjustments: List[RecommendationAdjustment]) -> Dict[str, Any]:
        """
        Apply recommendation adjustments to improve future recommendations.
        
        Args:
            adjustments: List of adjustments to apply
            
        Returns:
            Updated recommendation parameters
        """
        # Store adjustments for future use
        self.recommendation_adjustments.extend(adjustments)
        
        # Group adjustments by type
        adjustment_groups = defaultdict(list)
        for adjustment in adjustments:
            adjustment_groups[adjustment.adjustment_type].append(adjustment)
        
        updated_params = {
            'timeline_adjustments': {},
            'budget_adjustments': {},
            'activity_adjustments': {},
            'vendor_adjustments': {}
        }
        
        # Apply timeline adjustments
        for adjustment in adjustment_groups.get('timeline', []):
            if adjustment.confidence >= 0.7:  # High confidence only
                updated_params['timeline_adjustments'][adjustment.target_category] = {
                    'factor': adjustment.adjustment_factor,
                    'reasoning': adjustment.reasoning
                }
        
        # Apply budget adjustments
        for adjustment in adjustment_groups.get('budget', []):
            if adjustment.confidence >= 0.7:
                updated_params['budget_adjustments'][adjustment.target_category] = {
                    'factor': adjustment.adjustment_factor,
                    'reasoning': adjustment.reasoning
                }
        
        # Apply activity adjustments
        for adjustment in adjustment_groups.get('activity', []):
            if adjustment.confidence >= 0.6:  # Slightly lower threshold for activities
                updated_params['activity_adjustments'][adjustment.target_category] = {
                    'factor': adjustment.adjustment_factor,
                    'reasoning': adjustment.reasoning
                }
        
        # Apply vendor adjustments
        for adjustment in adjustment_groups.get('vendor', []):
            if adjustment.confidence >= 0.6:
                updated_params['vendor_adjustments'][adjustment.target_category] = {
                    'factor': adjustment.adjustment_factor,
                    'reasoning': adjustment.reasoning
                }
        
        return updated_params
    
    def get_feedback_insights(self, event_type: EventType, budget_tier: BudgetTier = None) -> Dict[str, Any]:
        """
        Get comprehensive feedback insights for an event type.
        
        Args:
            event_type: Event type to get insights for
            budget_tier: Optional budget tier filter
            
        Returns:
            Comprehensive feedback insights
        """
        analysis = self.analyze_feedback_patterns(event_type, budget_tier)
        adjustments = self.extract_recommendation_adjustments(analysis, event_type)
        
        return {
            'analysis': analysis,
            'adjustments': adjustments,
            'recommendations': self.apply_recommendation_adjustments(adjustments),
            'data_quality': {
                'feedback_count': len([p for p in self.patterns.values() 
                                     if p.context.event_type == event_type]),
                'average_success_score': sum([p.success_score for p in self.patterns.values() 
                                            if p.context.event_type == event_type]) / 
                                       max(1, len([p for p in self.patterns.values() 
                                                 if p.context.event_type == event_type])),
                'reliability': 'high' if len([p for p in self.patterns.values() 
                                            if p.context.event_type == event_type]) >= 10 else 'medium'
            }
        }
    
    def _create_default_feedback_analysis(self) -> FeedbackAnalysis:
        """Create default feedback analysis when insufficient data"""
        return FeedbackAnalysis(
            average_timeline_rating=3.0,
            average_budget_accuracy=3.0,
            average_overall_satisfaction=3.0,
            common_positive_feedback=[],
            common_improvement_areas=[],
            budget_variance_analysis={},
            timeline_deviation_patterns=[],
            success_factors=[]
        )
    
    def _find_common_themes(self, feedback_items: List[str], min_frequency: int = 2) -> List[str]:
        """Find common themes in feedback text"""
        if not feedback_items:
            return []
        
        # Simple keyword-based theme extraction
        theme_counts = defaultdict(int)
        
        # Common keywords to look for
        keywords = {
            'timing': ['time', 'timing', 'schedule', 'delay', 'early', 'late'],
            'budget': ['budget', 'cost', 'expensive', 'cheap', 'money', 'price'],
            'venue': ['venue', 'location', 'space', 'hall', 'room'],
            'catering': ['food', 'catering', 'meal', 'dinner', 'lunch', 'snacks'],
            'decoration': ['decoration', 'decor', 'flowers', 'lighting', 'setup'],
            'entertainment': ['music', 'entertainment', 'dance', 'performance'],
            'coordination': ['coordination', 'organization', 'management', 'planning'],
            'communication': ['communication', 'information', 'updates', 'contact']
        }
        
        for item in feedback_items:
            item_lower = item.lower()
            for theme, theme_keywords in keywords.items():
                if any(keyword in item_lower for keyword in theme_keywords):
                    theme_counts[theme] += 1
        
        # Return themes that appear frequently enough
        common_themes = [theme for theme, count in theme_counts.items() 
                        if count >= min_frequency]
        
        return sorted(common_themes, key=lambda x: theme_counts[x], reverse=True)
    
    def _analyze_budget_variances(self, patterns: List[EventPattern]) -> Dict[BudgetCategory, Dict[str, float]]:
        """Analyze budget variances across patterns"""
        variance_analysis = {}
        
        # Group by budget category
        category_data = defaultdict(list)
        
        for pattern in patterns:
            for category, actual_cost in pattern.feedback.actual_costs.items():
                if category in pattern.budget_allocation.categories:
                    planned_cost = pattern.budget_allocation.categories[category].amount
                    variance_percent = float((actual_cost - planned_cost) / planned_cost * 100)
                    category_data[category].append({
                        'planned': float(planned_cost),
                        'actual': float(actual_cost),
                        'variance_percent': variance_percent
                    })
        
        # Calculate statistics for each category
        for category, data_points in category_data.items():
            if len(data_points) >= 2:  # Need at least 2 data points
                variances = [dp['variance_percent'] for dp in data_points]
                variance_analysis[category] = {
                    'average_variance_percent': sum(variances) / len(variances),
                    'max_variance_percent': max(variances),
                    'min_variance_percent': min(variances),
                    'data_points': len(data_points),
                    'trend': 'over_budget' if sum(variances) > 5 else 'under_budget' if sum(variances) < -5 else 'on_budget'
                }
        
        return variance_analysis
    
    def _identify_success_factors(self, patterns: List[EventPattern]) -> List[str]:
        """Identify factors that contribute to successful events"""
        success_factors = []
        
        # Separate high and low success patterns
        high_success = [p for p in patterns if p.success_score >= 4.0]
        low_success = [p for p in patterns if p.success_score < 3.5]
        
        if not high_success or not low_success:
            return success_factors
        
        # Analyze differences in positive feedback
        high_success_feedback = []
        for pattern in high_success:
            high_success_feedback.extend(pattern.feedback.what_worked_well)
        
        high_success_themes = self._find_common_themes(high_success_feedback, min_frequency=1)
        
        # Factors that appear more in successful events
        for theme in high_success_themes:
            success_factors.append(f"Strong {theme} management")
        
        return success_factors[:5]  # Return top 5 factors
    
    def _extract_timeline_adjustments(self, analysis: FeedbackAnalysis, 
                                    event_type: EventType) -> List[RecommendationAdjustment]:
        """Extract timeline-related adjustments from feedback analysis"""
        adjustments = []
        
        # Check for timing-related improvement areas
        if 'timing' in analysis.common_improvement_areas:
            adjustments.append(RecommendationAdjustment(
                adjustment_type="timeline",
                target_category="buffer_time",
                adjustment_factor=1.2,  # Increase buffer time by 20%
                confidence=0.8,
                reasoning="Feedback indicates timing issues, increase buffer time",
                supporting_feedback_count=len([area for area in analysis.common_improvement_areas if 'timing' in area])
            ))
        
        # Check for timeline deviation patterns
        if analysis.timeline_deviation_patterns:
            adjustments.append(RecommendationAdjustment(
                adjustment_type="timeline",
                target_category="activity_duration",
                adjustment_factor=1.1,  # Increase activity durations by 10%
                confidence=0.7,
                reasoning="Common timeline deviations suggest longer activity durations needed",
                supporting_feedback_count=len(analysis.timeline_deviation_patterns)
            ))
        
        return adjustments
    
    def _extract_budget_adjustments(self, analysis: FeedbackAnalysis, 
                                  event_type: EventType) -> List[RecommendationAdjustment]:
        """Extract budget-related adjustments from feedback analysis"""
        adjustments = []
        
        # Analyze budget variances
        for category, variance_data in analysis.budget_variance_analysis.items():
            if variance_data['data_points'] >= 3:  # Reliable data
                if variance_data['trend'] == 'over_budget' and variance_data['average_variance_percent'] > 10:
                    adjustments.append(RecommendationAdjustment(
                        adjustment_type="budget",
                        target_category=category.value,
                        adjustment_factor=1 + (variance_data['average_variance_percent'] / 100),
                        confidence=min(0.9, variance_data['data_points'] / 10),
                        reasoning=f"Historical data shows {category.value} consistently over budget by {variance_data['average_variance_percent']:.1f}%",
                        supporting_feedback_count=variance_data['data_points']
                    ))
        
        return adjustments
    
    def _extract_activity_adjustments(self, analysis: FeedbackAnalysis, 
                                    event_type: EventType) -> List[RecommendationAdjustment]:
        """Extract activity-related adjustments from feedback analysis"""
        adjustments = []
        
        # Check success factors for activity improvements
        for factor in analysis.success_factors:
            if 'coordination' in factor.lower():
                adjustments.append(RecommendationAdjustment(
                    adjustment_type="activity",
                    target_category="coordination_activities",
                    adjustment_factor=1.3,  # Increase coordination activities
                    confidence=0.6,
                    reasoning="Success factors indicate importance of coordination",
                    supporting_feedback_count=1
                ))
        
        return adjustments
    
    def _extract_vendor_adjustments(self, analysis: FeedbackAnalysis, 
                                  event_type: EventType) -> List[RecommendationAdjustment]:
        """Extract vendor-related adjustments from feedback analysis"""
        adjustments = []
        
        # Check for vendor-related feedback
        vendor_themes = ['catering', 'decoration', 'entertainment']
        
        for theme in vendor_themes:
            if theme in analysis.common_improvement_areas:
                adjustments.append(RecommendationAdjustment(
                    adjustment_type="vendor",
                    target_category=theme,
                    adjustment_factor=1.1,  # Slight preference adjustment
                    confidence=0.5,
                    reasoning=f"Feedback indicates {theme} vendor performance issues",
                    supporting_feedback_count=1
                ))
        
        return adjustments
    
    # Database serialization/deserialization methods
    
    def _serialize_event_context(self, context: EventContext) -> Dict[str, Any]:
        """Serialize EventContext to dictionary for database storage"""
        return {
            "event_type": context.event_type.value,
            "guest_count": context.guest_count,
            "venue_type": context.venue_type.value,
            "cultural_requirements": [req.value for req in context.cultural_requirements],
            "budget_tier": context.budget_tier.value,
            "location": {
                "city": context.location.city,
                "state": context.location.state,
                "country": context.location.country,
                "timezone": context.location.timezone,
                "coordinates": context.location.coordinates
            },
            "season": context.season.value,
            "duration_days": context.duration_days,
            "special_requirements": context.special_requirements,
            "accessibility_requirements": [req.value for req in context.accessibility_requirements],
            "complexity_score": context.complexity_score,
            "weather_considerations": [cond.value for cond in context.weather_considerations]
        }
    
    def _serialize_timeline(self, timeline: Timeline) -> Dict[str, Any]:
        """Serialize Timeline to dictionary for database storage"""
        return {
            "days": [
                {
                    "day_number": day.day_number,
                    "date": day.date.isoformat(),
                    "activities": [
                        {
                            "activity": {
                                "id": activity.activity.id,
                                "name": activity.activity.name,
                                "activity_type": activity.activity.activity_type.value,
                                "duration": activity.activity.duration.total_seconds(),
                                "priority": activity.activity.priority.value,
                                "description": activity.activity.description,
                                "required_vendors": activity.activity.required_vendors,
                                "estimated_cost": float(activity.activity.estimated_cost),
                                "cultural_significance": activity.activity.cultural_significance,
                                "setup_time": activity.activity.setup_time.total_seconds(),
                                "cleanup_time": activity.activity.cleanup_time.total_seconds()
                            },
                            "start_time": activity.start_time.isoformat(),
                            "end_time": activity.end_time.isoformat(),
                            "buffer_before": activity.buffer_before.total_seconds(),
                            "buffer_after": activity.buffer_after.total_seconds(),
                            "contingency_plans": activity.contingency_plans
                        }
                        for activity in day.activities
                    ],
                    "estimated_cost": float(day.estimated_cost),
                    "notes": day.notes,
                    "contingency_plans": day.contingency_plans,
                    "weather_backup_plan": day.weather_backup_plan
                }
                for day in timeline.days
            ],
            "total_duration": timeline.total_duration.total_seconds(),
            "critical_path": [
                {
                    "id": activity.id,
                    "name": activity.name,
                    "activity_type": activity.activity_type.value,
                    "duration": activity.duration.total_seconds(),
                    "priority": activity.priority.value
                }
                for activity in timeline.critical_path
            ],
            "buffer_time": timeline.buffer_time.total_seconds(),
            "dependencies": [
                {
                    "predecessor_id": dep.predecessor_id,
                    "successor_id": dep.successor_id,
                    "dependency_type": dep.dependency_type,
                    "lag_time": dep.lag_time.total_seconds()
                }
                for dep in timeline.dependencies
            ],
            "total_estimated_cost": float(timeline.total_estimated_cost)
        }
    
    def _serialize_budget_allocation(self, budget: BudgetAllocation) -> Dict[str, Any]:
        """Serialize BudgetAllocation to dictionary for database storage"""
        return {
            "total_budget": float(budget.total_budget),
            "categories": {
                category.value: {
                    "category": allocation.category.value,
                    "amount": float(allocation.amount),
                    "percentage": allocation.percentage,
                    "justification": allocation.justification,
                    "alternatives": [
                        {
                            "name": alt.name,
                            "description": alt.description,
                            "cost_impact": float(alt.cost_impact),
                            "time_impact": alt.time_impact.total_seconds(),
                            "trade_offs": alt.trade_offs
                        }
                        for alt in allocation.alternatives
                    ],
                    "vendor_suggestions": allocation.vendor_suggestions,
                    "priority": allocation.priority.value
                }
                for category, allocation in budget.categories.items()
            },
            "per_person_cost": float(budget.per_person_cost),
            "contingency_percentage": budget.contingency_percentage,
            "regional_adjustments": budget.regional_adjustments,
            "seasonal_adjustments": {season.value: adjustment for season, adjustment in budget.seasonal_adjustments.items()}
        }
    
    def _serialize_feedback(self, feedback: EventFeedback) -> Dict[str, Any]:
        """Serialize EventFeedback to dictionary for database storage"""
        return {
            "event_id": feedback.event_id,
            "timeline_rating": feedback.timeline_rating,
            "budget_accuracy": feedback.budget_accuracy,
            "overall_satisfaction": feedback.overall_satisfaction,
            "what_worked_well": feedback.what_worked_well,
            "what_could_improve": feedback.what_could_improve,
            "actual_costs": {category.value: float(cost) for category, cost in feedback.actual_costs.items()},
            "timeline_deviations": feedback.timeline_deviations
        }
    
    def _deserialize_event_pattern(self, db_pattern: Dict[str, Any]) -> Optional[EventPattern]:
        """Deserialize database pattern to EventPattern object"""
        try:
            # Deserialize event context
            context_data = db_pattern["event_context"]
            from ..models.core import Location
            from ..models.enums import AccessibilityRequirement, WeatherCondition
            
            location = Location(
                city=context_data["location"]["city"],
                state=context_data["location"]["state"],
                country=context_data["location"]["country"],
                timezone=context_data["location"]["timezone"],
                coordinates=context_data["location"].get("coordinates")
            )
            
            context = EventContext(
                event_type=EventType(context_data["event_type"]),
                guest_count=context_data["guest_count"],
                venue_type=VenueType(context_data["venue_type"]),
                cultural_requirements=[CulturalRequirement(req) for req in context_data["cultural_requirements"]],
                budget_tier=BudgetTier(context_data["budget_tier"]),
                location=location,
                season=Season(context_data["season"]),
                duration_days=context_data["duration_days"],
                special_requirements=context_data.get("special_requirements", []),
                accessibility_requirements=[AccessibilityRequirement(req) for req in context_data.get("accessibility_requirements", [])],
                complexity_score=context_data.get("complexity_score", 0.0),
                weather_considerations=[WeatherCondition(cond) for cond in context_data.get("weather_considerations", [])]
            )
            
            # For simplicity, create minimal timeline and budget objects
            # In a full implementation, you'd deserialize these completely
            from ..models.core import Timeline, BudgetAllocation, EventFeedback
            from decimal import Decimal
            
            # Create a simplified timeline (you might want to fully deserialize this)
            timeline = Timeline(
                days=[],
                total_duration=timedelta(seconds=db_pattern["timeline_data"].get("total_duration", 0)),
                critical_path=[],
                buffer_time=timedelta(seconds=db_pattern["timeline_data"].get("buffer_time", 0)),
                dependencies=[],
                total_estimated_cost=Decimal(str(db_pattern["timeline_data"].get("total_estimated_cost", 0)))
            )
            
            # Create a simplified budget allocation
            budget_allocation = BudgetAllocation(
                total_budget=Decimal(str(db_pattern["budget_allocation"]["total_budget"])),
                categories={},
                per_person_cost=Decimal(str(db_pattern["budget_allocation"]["per_person_cost"])),
                contingency_percentage=db_pattern["budget_allocation"]["contingency_percentage"]
            )
            
            # Create feedback object
            feedback_data = db_pattern["feedback_data"]
            feedback = EventFeedback(
                event_id=feedback_data["event_id"],
                timeline_rating=feedback_data["timeline_rating"],
                budget_accuracy=feedback_data["budget_accuracy"],
                overall_satisfaction=feedback_data["overall_satisfaction"],
                what_worked_well=feedback_data.get("what_worked_well", []),
                what_could_improve=feedback_data.get("what_could_improve", []),
                actual_costs={BudgetCategory(cat): Decimal(str(cost)) for cat, cost in feedback_data.get("actual_costs", {}).items()},
                timeline_deviations=feedback_data.get("timeline_deviations", [])
            )
            
            # Create the pattern
            pattern = EventPattern(
                event_id=db_pattern["event_id"],
                context=context,
                timeline=timeline,
                budget_allocation=budget_allocation,
                feedback=feedback,
                success_score=db_pattern["success_score"],
                created_at=datetime.fromisoformat(db_pattern["created_at"].replace('Z', '+00:00')),
                usage_count=db_pattern.get("usage_count", 0),
                last_used=datetime.fromisoformat(db_pattern["last_used"].replace('Z', '+00:00')) if db_pattern.get("last_used") else None
            )
            
            return pattern
            
        except Exception as e:
            print(f"Error deserializing event pattern: {e}")
            return None