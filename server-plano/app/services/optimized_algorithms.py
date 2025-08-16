"""
Optimized algorithms for large-scale events.
Provides performance-optimized versions of complexity scoring, timeline generation,
and pattern matching for events with high guest counts and complex requirements.
"""
import math
import numpy as np
from typing import List, Dict, Tuple, Optional, Set
from datetime import datetime, timedelta
from decimal import Decimal
from collections import defaultdict
import bisect
from functools import lru_cache

from ..models.core import EventContext, Timeline, Activity, TimedActivity, TimelineDay
from ..models.enums import (
    EventType, VenueType, BudgetTier, Season, CulturalRequirement,
    ActivityType, Priority
)


class OptimizedEventContextAnalyzer:
    """
    Optimized version of EventContextAnalyzer for large-scale events.
    Uses vectorized operations and caching for improved performance.
    """
    
    def __init__(self):
        # Pre-compute lookup tables for faster access
        self._complexity_lookup = self._build_complexity_lookup()
        self._guest_count_ranges = self._build_guest_count_ranges()
        
    @lru_cache(maxsize=1024)
    def _build_complexity_lookup(self) -> Dict[str, float]:
        """Build pre-computed complexity lookup table"""
        return {
            # Event type base scores
            'wedding': 4.0, 'engagement': 3.0, 'anniversary': 2.5,
            'birthday': 2.0, 'corporate': 3.2, 'conference': 3.5,
            'graduation': 2.2, 'baby_shower': 1.5, 'housewarming': 1.8,
            'festival': 3.8,
            
            # Venue multipliers
            'outdoor': 1.4, 'beach': 1.6, 'garden': 1.3, 'home': 1.1,
            'hybrid': 1.5, 'indoor': 1.0, 'banquet_hall': 0.9,
            'hotel': 0.8, 'restaurant': 0.7, 'temple': 1.2,
            'church': 1.1, 'community_center': 0.9,
            
            # Cultural complexity
            'hindu': 1.0, 'muslim': 0.9, 'sikh': 0.95, 'jewish': 0.85,
            'buddhist': 0.75, 'jain': 0.8, 'christian': 0.65,
            'secular': 0.2, 'mixed': 1.2,
            
            # Seasonal adjustments
            'summer': 1.15, 'monsoon': 1.4, 'winter': 1.1,
            'spring': 1.0, 'autumn': 1.05,
            
            # Budget tier multipliers
            'low': 0.95, 'standard': 1.0, 'premium': 1.1, 'luxury': 1.2
        }
    
    def _build_guest_count_ranges(self) -> List[Tuple[int, float]]:
        """Build optimized guest count ranges for binary search"""
        return [
            (50, 1.0), (100, 1.1), (200, 1.3), (500, 1.6),
            (1000, 2.0), (2000, 2.4), (5000, 2.8), (10000, 3.2)
        ]
    
    def calculate_complexity_score_optimized(self, context: EventContext) -> float:
        """
        Optimized complexity score calculation using lookup tables and vectorized operations.
        
        Args:
            context: EventContext to analyze
            
        Returns:
            Complexity score between 0.0 and 10.0
        """
        # Use lookup table for base score
        base_score = self._complexity_lookup.get(context.event_type.value, 5.0)
        
        # Venue multiplier from lookup
        venue_multiplier = self._complexity_lookup.get(context.venue_type.value, 1.0)
        score = base_score * venue_multiplier
        
        # Vectorized cultural complexity calculation
        cultural_scores = [
            self._complexity_lookup.get(req.value, 1.0) 
            for req in context.cultural_requirements
        ]
        cultural_addition = sum(cultural_scores)
        
        # Multiple cultural requirements penalty
        if len(context.cultural_requirements) > 1:
            cultural_addition *= 1.3
        
        score += cultural_addition
        
        # Optimized guest count scaling using binary search
        guest_multiplier = self._get_guest_multiplier_fast(context.guest_count)
        score *= guest_multiplier
        
        # Seasonal adjustment from lookup
        seasonal_multiplier = self._complexity_lookup.get(context.season.value, 1.0)
        score *= seasonal_multiplier
        
        # Duration scaling (optimized calculation)
        if context.duration_days > 1:
            duration_multiplier = 1.0 + (context.duration_days - 1) * 0.15
            score *= duration_multiplier
        
        # Batch calculate additional complexities
        additional_complexity = (
            len(context.special_requirements) * 0.15 +
            len(getattr(context, 'accessibility_requirements', [])) * 0.2 +
            len(getattr(context, 'weather_considerations', [])) * 0.1
        )
        score += additional_complexity
        
        # Budget tier adjustment from lookup
        budget_multiplier = self._complexity_lookup.get(context.budget_tier.value, 1.0)
        score *= budget_multiplier
        
        return min(max(score, 0.0), 10.0)
    
    def _get_guest_multiplier_fast(self, guest_count: int) -> float:
        """Fast guest count multiplier using binary search"""
        # Binary search for appropriate range
        ranges = self._guest_count_ranges
        idx = bisect.bisect_left([r[0] for r in ranges], guest_count)
        
        if idx < len(ranges):
            return ranges[idx][1]
        return ranges[-1][1]


class OptimizedTimelineGenerator:
    """
    Optimized timeline generator for large-scale events.
    Uses efficient algorithms for activity scheduling and dependency resolution.
    """
    
    def __init__(self):
        self.activity_cache = {}
        self.dependency_graph_cache = {}
    
    def generate_optimized_timeline(self, context: EventContext, 
                                  activities: List[Activity]) -> Timeline:
        """
        Generate timeline using optimized algorithms for large event scales.
        
        Args:
            context: Event context
            activities: List of activities to schedule
            
        Returns:
            Optimized timeline
        """
        # Use topological sort for dependency resolution
        sorted_activities = self._topological_sort_activities(activities)
        
        # Batch process activity durations
        timed_activities = self._batch_calculate_durations(sorted_activities, context)
        
        # Optimized day allocation using bin packing algorithm
        timeline_days = self._optimize_day_allocation(timed_activities, context)
        
        # Calculate critical path efficiently
        critical_path = self._calculate_critical_path_fast(timed_activities)
        
        # Calculate total metrics
        total_duration = sum(
            (day.activities[-1].end_time - day.activities[0].start_time 
             for day in timeline_days if day.activities), 
            timedelta()
        )
        
        buffer_time = self._calculate_optimal_buffer_time(context, total_duration)
        
        return Timeline(
            days=timeline_days,
            total_duration=total_duration,
            critical_path=critical_path,
            buffer_time=buffer_time,
            dependencies=[],
            total_estimated_cost=sum(activity.activity.estimated_cost for activity in timed_activities)
        )
    
    def _topological_sort_activities(self, activities: List[Activity]) -> List[Activity]:
        """
        Efficient topological sort for activity dependencies.
        Uses Kahn's algorithm for O(V + E) complexity.
        """
        # Build adjacency list and in-degree count
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        activity_map = {activity.id: activity for activity in activities}
        
        # Initialize in-degrees
        for activity in activities:
            in_degree[activity.id] = 0
        
        # Build graph from prerequisites
        for activity in activities:
            for prereq in getattr(activity, 'prerequisites', []):
                if prereq in activity_map:
                    graph[prereq].append(activity.id)
                    in_degree[activity.id] += 1
        
        # Kahn's algorithm
        queue = [activity_id for activity_id in in_degree if in_degree[activity_id] == 0]
        sorted_ids = []
        
        while queue:
            current = queue.pop(0)
            sorted_ids.append(current)
            
            for neighbor in graph[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Return activities in topological order
        return [activity_map[activity_id] for activity_id in sorted_ids if activity_id in activity_map]
    
    def _batch_calculate_durations(self, activities: List[Activity], 
                                 context: EventContext) -> List[TimedActivity]:
        """
        Batch calculate activity durations using vectorized operations.
        """
        timed_activities = []
        current_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)
        
        # Pre-calculate scaling factors
        guest_scale_factor = self._calculate_guest_scale_factor(context.guest_count)
        venue_scale_factor = self._calculate_venue_scale_factor(context.venue_type)
        
        for activity in activities:
            # Apply scaling factors
            base_duration = activity.duration
            scaled_duration = timedelta(
                seconds=base_duration.total_seconds() * guest_scale_factor * venue_scale_factor
            )
            
            # Create timed activity
            buffer_time = self._calculate_activity_buffer(activity, context)
            timed_activity = TimedActivity(
                activity=activity,
                start_time=current_time,
                end_time=current_time + scaled_duration,
                buffer_after=buffer_time
            )
            
            timed_activities.append(timed_activity)
            current_time = timed_activity.end_time + timed_activity.buffer_after
        
        return timed_activities
    
    def _calculate_guest_scale_factor(self, guest_count: int) -> float:
        """Calculate guest count scaling factor efficiently"""
        if guest_count <= 100:
            return 1.0
        elif guest_count <= 500:
            return 1.0 + (guest_count - 100) * 0.001
        elif guest_count <= 1000:
            return 1.4 + (guest_count - 500) * 0.0008
        else:
            return 1.8 + min((guest_count - 1000) * 0.0005, 0.5)
    
    def _calculate_venue_scale_factor(self, venue_type: VenueType) -> float:
        """Calculate venue scaling factor"""
        venue_factors = {
            VenueType.OUTDOOR: 1.3,
            VenueType.BEACH: 1.4,
            VenueType.GARDEN: 1.2,
            VenueType.HYBRID: 1.25,
            VenueType.HOME: 1.1,
            VenueType.INDOOR: 1.0,
            VenueType.BANQUET_HALL: 0.95,
            VenueType.HOTEL: 0.9,
            VenueType.RESTAURANT: 0.85
        }
        return venue_factors.get(venue_type, 1.0)
    
    def _optimize_day_allocation(self, timed_activities: List[TimedActivity], 
                               context: EventContext) -> List[TimelineDay]:
        """
        Optimize activity allocation across days using bin packing algorithm.
        """
        max_hours_per_day = 12  # Maximum event hours per day
        days = []
        current_day_activities = []
        current_day_duration = timedelta()
        day_number = 1
        
        for activity in timed_activities:
            activity_duration = activity.end_time - activity.start_time + activity.buffer_after
            
            # Check if activity fits in current day
            if (current_day_duration + activity_duration).total_seconds() / 3600 <= max_hours_per_day:
                current_day_activities.append(activity)
                current_day_duration += activity_duration
            else:
                # Finalize current day
                if current_day_activities:
                    days.append(TimelineDay(
                        day_number=day_number,
                        date=datetime.now().date(),
                        activities=current_day_activities,
                        estimated_cost=sum(a.activity.estimated_cost for a in current_day_activities),
                        notes=[],
                        contingency_plans=[]
                    ))
                    day_number += 1
                
                # Start new day
                current_day_activities = [activity]
                current_day_duration = activity_duration
        
        # Add final day
        if current_day_activities:
            days.append(TimelineDay(
                day_number=day_number,
                date=datetime.now().date(),
                activities=current_day_activities,
                estimated_cost=sum(a.activity.estimated_cost for a in current_day_activities),
                notes=[],
                contingency_plans=[]
            ))
        
        return days
    
    def _calculate_critical_path_fast(self, activities: List[TimedActivity]) -> List[Activity]:
        """
        Fast critical path calculation using dynamic programming.
        """
        # For large events, use simplified critical path based on activity priorities
        critical_activities = [
            activity.activity for activity in activities
            if activity.activity.priority in [Priority.CRITICAL, Priority.HIGH]
        ]
        
        # Sort by priority and duration
        critical_activities.sort(
            key=lambda a: (a.priority.value, -a.duration.total_seconds())
        )
        
        return critical_activities[:10]  # Limit to top 10 for performance
    
    def _calculate_activity_buffer(self, activity: Activity, context: EventContext) -> timedelta:
        """Calculate optimal buffer time for activity"""
        base_buffer = timedelta(minutes=15)
        
        # Scale buffer based on complexity and guest count
        complexity_factor = context.complexity_score / 10.0
        guest_factor = min(context.guest_count / 1000.0, 2.0)
        
        buffer_multiplier = 1.0 + complexity_factor * 0.5 + guest_factor * 0.3
        
        return timedelta(seconds=base_buffer.total_seconds() * buffer_multiplier)
    
    def _calculate_optimal_buffer_time(self, context: EventContext, 
                                     total_duration: timedelta) -> timedelta:
        """Calculate optimal total buffer time"""
        # Base buffer as percentage of total duration
        base_percentage = 0.15  # 15% base buffer
        
        # Adjust based on complexity and scale
        complexity_adjustment = (context.complexity_score - 5.0) / 10.0 * 0.1
        scale_adjustment = min(context.guest_count / 1000.0, 1.0) * 0.05
        
        total_percentage = base_percentage + complexity_adjustment + scale_adjustment
        
        return timedelta(seconds=total_duration.total_seconds() * total_percentage)


class OptimizedPatternMatcher:
    """
    Optimized pattern matching for large datasets using efficient algorithms.
    """
    
    def __init__(self):
        self.similarity_cache = {}
        self.feature_vectors = {}
    
    def find_similar_patterns_optimized(self, target_context: EventContext,
                                      patterns: List[any], limit: int = 10) -> List[any]:
        """
        Find similar patterns using optimized similarity calculation.
        Uses feature vectors and approximate nearest neighbor search.
        """
        # Convert context to feature vector
        target_vector = self._context_to_vector(target_context)
        
        # Calculate similarities using vectorized operations
        similarities = []
        
        for pattern in patterns:
            pattern_vector = self._context_to_vector(pattern.context)
            similarity = self._fast_cosine_similarity(target_vector, pattern_vector)
            
            if similarity >= 0.6:  # Threshold for relevance
                similarities.append((pattern, similarity))
        
        # Sort and return top matches
        similarities.sort(key=lambda x: x[1], reverse=True)
        return [pattern for pattern, _ in similarities[:limit]]
    
    def _context_to_vector(self, context: EventContext) -> np.ndarray:
        """
        Convert EventContext to numerical feature vector for fast similarity calculation.
        """
        # Create feature vector with normalized values
        features = [
            # Event type (one-hot encoded)
            1.0 if context.event_type == EventType.WEDDING else 0.0,
            1.0 if context.event_type == EventType.CORPORATE else 0.0,
            1.0 if context.event_type == EventType.BIRTHDAY else 0.0,
            
            # Guest count (normalized)
            min(context.guest_count / 1000.0, 5.0),
            
            # Venue type (encoded)
            self._encode_venue_type(context.venue_type),
            
            # Budget tier (normalized)
            self._encode_budget_tier(context.budget_tier),
            
            # Season (encoded)
            self._encode_season(context.season),
            
            # Duration (normalized)
            min(context.duration_days / 7.0, 2.0),
            
            # Complexity score (normalized)
            context.complexity_score / 10.0,
            
            # Cultural requirements (binary features)
            1.0 if CulturalRequirement.HINDU in context.cultural_requirements else 0.0,
            1.0 if CulturalRequirement.MUSLIM in context.cultural_requirements else 0.0,
            1.0 if CulturalRequirement.CHRISTIAN in context.cultural_requirements else 0.0,
        ]
        
        return np.array(features, dtype=np.float32)
    
    def _encode_venue_type(self, venue_type: VenueType) -> float:
        """Encode venue type as numerical value"""
        venue_encoding = {
            VenueType.OUTDOOR: 0.9,
            VenueType.BEACH: 0.95,
            VenueType.GARDEN: 0.85,
            VenueType.INDOOR: 0.5,
            VenueType.BANQUET_HALL: 0.3,
            VenueType.HOTEL: 0.2,
            VenueType.RESTAURANT: 0.1,
            VenueType.HOME: 0.7,
            VenueType.HYBRID: 0.8
        }
        return venue_encoding.get(venue_type, 0.5)
    
    def _encode_season(self, season: Season) -> float:
        """Encode season as numerical value"""
        season_encoding = {
            Season.SPRING: 0.2,
            Season.SUMMER: 0.4,
            Season.MONSOON: 0.6,
            Season.AUTUMN: 0.8,
            Season.WINTER: 1.0
        }
        return season_encoding.get(season, 0.5)
    
    def _encode_budget_tier(self, budget_tier: BudgetTier) -> float:
        """Encode budget tier as numerical value"""
        tier_encoding = {
            BudgetTier.LOW: 0.25,
            BudgetTier.STANDARD: 0.5,
            BudgetTier.PREMIUM: 0.75,
            BudgetTier.LUXURY: 1.0
        }
        return tier_encoding.get(budget_tier, 0.5)
    
    def _fast_cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """
        Fast cosine similarity calculation using numpy.
        """
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return dot_product / (norm1 * norm2)


class MemoryOptimizer:
    """
    Memory optimization utilities for large-scale event processing.
    """
    
    @staticmethod
    def optimize_pattern_storage(patterns: List[any]) -> Dict[str, any]:
        """
        Optimize pattern storage by compressing and indexing data.
        """
        # Group patterns by similarity to reduce redundancy
        pattern_groups = defaultdict(list)
        
        for pattern in patterns:
            # Create a key based on major characteristics
            key = f"{pattern.context.event_type.value}_{pattern.context.guest_count//100}_{pattern.context.venue_type.value}"
            pattern_groups[key].append(pattern)
        
        # Store only representative patterns from each group
        optimized_patterns = {}
        for key, group in pattern_groups.items():
            # Sort by success score and take top patterns
            group.sort(key=lambda p: p.success_score, reverse=True)
            optimized_patterns[key] = group[:5]  # Keep top 5 per group
        
        return optimized_patterns
    
    @staticmethod
    def batch_process_contexts(contexts: List[EventContext], 
                             batch_size: int = 100) -> List[List[EventContext]]:
        """
        Batch process contexts to optimize memory usage.
        """
        batches = []
        for i in range(0, len(contexts), batch_size):
            batch = contexts[i:i + batch_size]
            batches.append(batch)
        
        return batches
    
    @staticmethod
    def compress_timeline_data(timeline: Timeline) -> Dict[str, any]:
        """
        Compress timeline data for efficient storage.
        """
        compressed = {
            'total_duration_seconds': timeline.total_duration.total_seconds(),
            'buffer_time_seconds': timeline.buffer_time.total_seconds(),
            'day_count': len(timeline.days),
            'activity_count': sum(len(day.activities) for day in timeline.days),
            'total_cost': float(timeline.total_estimated_cost),
            'critical_path_ids': [activity.id for activity in timeline.critical_path]
        }
        
        return compressed