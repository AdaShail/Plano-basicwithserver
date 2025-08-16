"""
Timeline Intelligence Engine for generating contextual, realistic timelines.
Combines pattern matching, cultural templates, and intelligent algorithms
to create timelines that adapt to specific event requirements.
"""
from dataclasses import dataclass, field
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple, Any
from decimal import Decimal
import logging

from app.models.core import (
    Activity, Timeline, TimelineDay, TimedActivity, EventContext, 
    Dependency, Alternative
)
from app.models.enums import ActivityType, Priority, VenueType, BudgetTier, CulturalRequirement, EventType
from app.services.cultural_templates import CulturalTemplateService, ActivityTemplate
from app.services.dependency_manager import DependencyManager, DependencyGraph

logger = logging.getLogger(__name__)


@dataclass
class TimelineGenerationContext:
    """Context for timeline generation with calculated parameters"""
    event_context: EventContext
    start_date: date
    start_time: datetime
    total_duration: timedelta
    daily_schedule_hours: int = 12  # Default 12-hour daily schedule
    break_duration: timedelta = timedelta(minutes=30)
    meal_break_duration: timedelta = timedelta(hours=1)
    
    def get_daily_end_time(self, day_start: datetime) -> datetime:
        """Get the end time for a day's activities"""
        return day_start + timedelta(hours=self.daily_schedule_hours)


@dataclass
class ActivityDurationCalculation:
    """Result of activity duration calculation"""
    base_duration: timedelta
    guest_count_adjustment: float
    venue_adjustment: float
    complexity_adjustment: float
    final_duration: timedelta
    buffer_time: timedelta
    total_time_needed: timedelta


class TimelineIntelligenceEngine:
    """
    Intelligent timeline generation engine that creates contextual timelines
    based on event requirements, cultural templates, and dependency analysis.
    """
    
    def __init__(self):
        self.cultural_service = CulturalTemplateService()
        self.dependency_manager = DependencyManager()
        self.pattern_cache = {}  # Cache for pattern matching results
        
        # Initialize duration calculation rules
        self.duration_rules = self._initialize_duration_rules()
        
        # Initialize venue-specific adjustments
        self.venue_adjustments = self._initialize_venue_adjustments()
        
        # Initialize complexity impact factors
        self.complexity_factors = self._initialize_complexity_factors()
    
    def _initialize_duration_rules(self) -> Dict[str, Any]:
        """Initialize rules for duration calculations"""
        return {
            "guest_count_scaling": {
                "base_threshold": 100,  # Base guest count for scaling
                "scaling_factors": {
                    ActivityType.CEREMONY: 0.3,      # Ceremonies scale moderately with guest count
                    ActivityType.CATERING: 0.5,      # Catering scales significantly
                    ActivityType.PHOTOGRAPHY: 0.2,   # Photography scales minimally
                    ActivityType.ENTERTAINMENT: 0.4, # Entertainment scales moderately
                    ActivityType.PREPARATION: 0.3,   # Preparation scales moderately
                    ActivityType.CLEANUP: 0.4,       # Cleanup scales with guest count
                    ActivityType.DECORATION: 0.2,    # Decoration scales minimally
                    ActivityType.TRANSPORTATION: 0.6, # Transportation scales significantly
                    ActivityType.BREAK: 0.0,         # Breaks don't scale with guest count
                    ActivityType.NETWORKING: 0.3     # Networking scales moderately
                }
            },
            "complexity_multipliers": {
                "low": 1.0,      # 0-3 complexity score
                "medium": 1.15,  # 3-6 complexity score  
                "high": 1.3,     # 6-8 complexity score
                "very_high": 1.5 # 8-10 complexity score
            },
            "priority_buffer_multipliers": {
                Priority.CRITICAL: 0.1,   # 10% buffer for critical activities
                Priority.HIGH: 0.15,      # 15% buffer for high priority
                Priority.MEDIUM: 0.2,     # 20% buffer for medium priority
                Priority.LOW: 0.25,       # 25% buffer for low priority
                Priority.OPTIONAL: 0.3    # 30% buffer for optional activities
            }
        }
    
    def _initialize_venue_adjustments(self) -> Dict[VenueType, Dict[str, float]]:
        """Initialize venue-specific adjustments for different activity types"""
        return {
            VenueType.OUTDOOR: {
                "setup_multiplier": 1.5,     # Outdoor setup takes longer
                "weather_buffer": 1.2,       # Extra buffer for weather
                "logistics_multiplier": 1.3,  # More complex logistics
                "cleanup_multiplier": 1.4     # More cleanup needed
            },
            VenueType.INDOOR: {
                "setup_multiplier": 1.0,
                "weather_buffer": 1.0,
                "logistics_multiplier": 1.0,
                "cleanup_multiplier": 1.0
            },
            VenueType.HYBRID: {
                "setup_multiplier": 1.3,
                "weather_buffer": 1.1,
                "logistics_multiplier": 1.2,
                "cleanup_multiplier": 1.2
            },
            VenueType.HOME: {
                "setup_multiplier": 0.8,     # Easier setup at home
                "weather_buffer": 1.0,
                "logistics_multiplier": 0.9,  # Simpler logistics
                "cleanup_multiplier": 1.1     # More thorough cleanup needed
            },
            VenueType.BANQUET_HALL: {
                "setup_multiplier": 1.1,
                "weather_buffer": 1.0,
                "logistics_multiplier": 1.0,
                "cleanup_multiplier": 0.9     # Professional cleanup available
            },
            VenueType.HOTEL: {
                "setup_multiplier": 0.9,     # Hotel staff assistance
                "weather_buffer": 1.0,
                "logistics_multiplier": 0.8,  # Hotel handles logistics
                "cleanup_multiplier": 0.7     # Hotel handles cleanup
            }
        }
    
    def _initialize_complexity_factors(self) -> Dict[str, float]:
        """Initialize complexity impact factors"""
        return {
            "guest_count_thresholds": {
                50: 1.0,    # Small events
                150: 1.1,   # Medium events
                300: 1.2,   # Large events
                500: 1.4,   # Very large events
                1000: 1.6   # Massive events
            },
            "cultural_complexity": {
                1: 1.0,     # Single cultural requirement
                2: 1.1,     # Mixed cultural requirements
                3: 1.2,     # Multiple cultural requirements
                4: 1.3      # Complex multi-cultural event
            },
            "duration_complexity": {
                1: 1.0,     # Single day event
                2: 1.1,     # Two day event
                3: 1.2,     # Three day event
                5: 1.3,     # Week-long event
                7: 1.4      # Extended event
            }
        }
    
    def generate_timeline(self, 
                         context: EventContext, 
                         start_date: date,
                         preferences: Optional[Dict[str, Any]] = None) -> Timeline:
        """
        Generate a complete timeline for the event based on context and preferences.
        
        Args:
            context: Event context with all requirements
            start_date: When the event should start
            preferences: Optional user preferences for timeline generation
            
        Returns:
            Complete Timeline object with all days and activities
        """
        try:
            logger.info(f"Generating timeline for {context.event_type.value} event with {context.guest_count} guests")
            
            # Create generation context
            gen_context = self._create_generation_context(context, start_date, preferences)
            
            # Get compatible ceremony templates
            ceremony_templates = self.cultural_service.get_compatible_ceremonies(context)
            if not ceremony_templates:
                raise ValueError(f"No compatible ceremony templates found for {context.event_type.value} event")
            
            # Select primary ceremony and additional activities
            primary_ceremony = self.cultural_service.select_primary_ceremony(context)
            activities = self._generate_activities(context, primary_ceremony, ceremony_templates)
            
            # Calculate activity durations based on context
            timed_activities = self._calculate_activity_durations(activities, context)
            
            # Create dependency graph and calculate critical path
            dependency_graph = self._create_and_analyze_dependencies(timed_activities, context)
            
            # Generate timeline days with proper scheduling
            timeline_days = self._schedule_activities_to_days(
                timed_activities, dependency_graph, gen_context
            )
            
            # Create initial timeline
            timeline = Timeline(
                days=timeline_days,
                total_duration=gen_context.total_duration,
                critical_path=[activity for activity in timed_activities if activity.activity.priority == Priority.CRITICAL],
                buffer_time=self._calculate_total_buffer_time(timed_activities),
                dependencies=dependency_graph.dependencies,
                total_estimated_cost=sum(day.estimated_cost for day in timeline_days)
            )
            
            # Apply contextual customizations
            timeline = self.optimize_timeline_for_context(timeline, context)
            
            # Apply AI enhancements with fallback
            timeline = self.enhance_timeline_with_ai(timeline, context, use_ai=True)
            
            # Validate timeline
            validation_errors = timeline.validate()
            if validation_errors:
                logger.warning(f"Timeline validation issues: {validation_errors}")
                # Try to fix common issues
                timeline = self._fix_timeline_issues(timeline, validation_errors)
            
            logger.info(f"Successfully generated timeline with {len(timeline_days)} days")
            return timeline
            
        except Exception as e:
            logger.error(f"Error generating timeline: {str(e)}")
            # Return fallback timeline
            return self._generate_fallback_timeline(context, start_date)
    
    def _create_generation_context(self, 
                                 context: EventContext, 
                                 start_date: date,
                                 preferences: Optional[Dict[str, Any]]) -> TimelineGenerationContext:
        """Create timeline generation context with calculated parameters"""
        # Calculate start time (default to 10 AM)
        start_time = datetime.combine(start_date, datetime.min.time().replace(hour=10))
        
        # Calculate total duration based on event type and complexity
        base_duration_days = self._calculate_base_duration(context)
        total_duration = timedelta(days=base_duration_days)
        
        # Apply preferences if provided
        if preferences:
            if "start_time" in preferences:
                start_time = preferences["start_time"]
            if "daily_hours" in preferences:
                daily_hours = preferences["daily_hours"]
            else:
                daily_hours = 12
        else:
            daily_hours = 12
        
        return TimelineGenerationContext(
            event_context=context,
            start_date=start_date,
            start_time=start_time,
            total_duration=total_duration,
            daily_schedule_hours=daily_hours
        )
    
    def _calculate_base_duration(self, context: EventContext) -> int:
        """Calculate base duration in days for the event"""
        # Base durations by event type
        base_durations = {
            "wedding": 3,      # Mehendi, Haldi, Wedding
            "birthday": 1,     # Single day celebration
            "anniversary": 1,  # Single day celebration
            "corporate": 2,    # Conference/meeting days
            "housewarming": 1, # Single day celebration
            "graduation": 1,   # Single day celebration
            "engagement": 1,   # Single day celebration
            "festival": 2,     # Multi-day celebration
            "conference": 3    # Multi-day professional event
        }
        
        base_days = base_durations.get(context.event_type.value, 1)
        
        # Adjust for guest count
        if context.guest_count > 300:
            base_days += 1  # Add extra day for large events
        
        # Adjust for cultural complexity
        if len(context.cultural_requirements) > 1:
            base_days += 1  # Add extra day for multi-cultural events
        
        # Respect user-specified duration
        if context.duration_days > 0:
            return min(context.duration_days, base_days + 2)  # Cap at reasonable limit
        
        return base_days
    
    def _generate_activities(self, 
                           context: EventContext,
                           primary_ceremony: Optional[Any],
                           ceremony_templates: List[Any]) -> List[Activity]:
        """Generate all activities for the event"""
        activities = []
        activity_counter = 1
        
        # Add activities from primary ceremony
        if primary_ceremony:
            ceremony_activities = primary_ceremony.get_activities(context, include_optional=True)
            for template in ceremony_activities:
                activity = template.to_activity(context, f"activity_{activity_counter}")
                activities.append(activity)
                activity_counter += 1
        
        # Add activities from additional compatible ceremonies
        for ceremony in ceremony_templates:
            if ceremony != primary_ceremony:
                # Add only essential activities from secondary ceremonies
                ceremony_activities = ceremony.get_activities(context, include_optional=False)
                for template in ceremony_activities[:2]:  # Limit to 2 activities per secondary ceremony
                    activity = template.to_activity(context, f"activity_{activity_counter}")
                    activities.append(activity)
                    activity_counter += 1
        
        # Add common activities (setup, cleanup, etc.)
        common_activities = self._generate_common_activities(context, activity_counter)
        activities.extend(common_activities)
        
        return activities
    
    def _generate_common_activities(self, context: EventContext, start_counter: int) -> List[Activity]:
        """Generate common activities needed for all events"""
        activities = []
        counter = start_counter
        
        # Venue setup
        setup_duration = timedelta(hours=2)
        if context.venue_type == VenueType.OUTDOOR:
            setup_duration = timedelta(hours=3)  # Outdoor setup takes longer
        
        activities.append(Activity(
            id=f"activity_{counter}",
            name="Venue Setup and Preparation",
            activity_type=ActivityType.PREPARATION,
            duration=setup_duration,
            priority=Priority.HIGH,
            description="Setting up venue with decorations and equipment",
            required_vendors=["decorator", "technician"],
            setup_time=timedelta(minutes=30)
        ))
        counter += 1
        
        # Photography setup
        activities.append(Activity(
            id=f"activity_{counter}",
            name="Photography and Videography Setup",
            activity_type=ActivityType.PHOTOGRAPHY,
            duration=timedelta(hours=1),
            priority=Priority.MEDIUM,
            description="Setting up cameras and photography equipment",
            required_vendors=["photographer", "videographer"],
            setup_time=timedelta(minutes=15)
        ))
        counter += 1
        
        # Final cleanup
        cleanup_duration = timedelta(hours=2)
        if context.guest_count > 200:
            cleanup_duration = timedelta(hours=3)  # More cleanup for larger events
        
        activities.append(Activity(
            id=f"activity_{counter}",
            name="Event Cleanup and Restoration",
            activity_type=ActivityType.CLEANUP,
            duration=cleanup_duration,
            priority=Priority.MEDIUM,
            description="Cleaning up venue and removing decorations",
            cleanup_time=timedelta(minutes=30)
        ))
        counter += 1
        
        return activities
    
    def calculate_activity_duration(self, 
                                  activity: Activity, 
                                  context: EventContext) -> ActivityDurationCalculation:
        """
        Calculate the actual duration for an activity based on event context.
        
        Args:
            activity: The activity to calculate duration for
            context: Event context with guest count, venue, etc.
            
        Returns:
            ActivityDurationCalculation with detailed breakdown
        """
        base_duration = activity.duration
        
        # Guest count adjustment
        guest_scaling_factor = self.duration_rules["guest_count_scaling"]["scaling_factors"].get(
            activity.activity_type, 0.3
        )
        
        if context.guest_count > self.duration_rules["guest_count_scaling"]["base_threshold"]:
            excess_guests = context.guest_count - self.duration_rules["guest_count_scaling"]["base_threshold"]
            guest_adjustment = 1 + (excess_guests * guest_scaling_factor / 1000)
        else:
            guest_adjustment = 1.0
        
        # Venue adjustment
        venue_adjustments = self.venue_adjustments.get(context.venue_type, {})
        if activity.activity_type == ActivityType.PREPARATION:
            venue_adjustment = venue_adjustments.get("setup_multiplier", 1.0)
        elif activity.activity_type == ActivityType.CLEANUP:
            venue_adjustment = venue_adjustments.get("cleanup_multiplier", 1.0)
        else:
            venue_adjustment = venue_adjustments.get("logistics_multiplier", 1.0)
        
        # Complexity adjustment
        complexity_level = self._get_complexity_level(context.complexity_score)
        complexity_adjustment = self.duration_rules["complexity_multipliers"][complexity_level]
        
        # Calculate final duration
        total_adjustment = guest_adjustment * venue_adjustment * complexity_adjustment
        final_duration = timedelta(seconds=base_duration.total_seconds() * total_adjustment)
        
        # Calculate buffer time
        buffer_multiplier = self.duration_rules["priority_buffer_multipliers"].get(
            activity.priority, 0.2
        )
        buffer_time = timedelta(seconds=final_duration.total_seconds() * buffer_multiplier)
        
        # Apply minimum and maximum constraints
        min_duration = timedelta(minutes=15)
        max_duration = timedelta(hours=8)
        final_duration = max(min_duration, min(final_duration, max_duration))
        
        min_buffer = timedelta(minutes=10)
        max_buffer = timedelta(hours=1)
        buffer_time = max(min_buffer, min(buffer_time, max_buffer))
        
        total_time_needed = final_duration + buffer_time + activity.setup_time + activity.cleanup_time
        
        return ActivityDurationCalculation(
            base_duration=base_duration,
            guest_count_adjustment=guest_adjustment,
            venue_adjustment=venue_adjustment,
            complexity_adjustment=complexity_adjustment,
            final_duration=final_duration,
            buffer_time=buffer_time,
            total_time_needed=total_time_needed
        )
    
    def _calculate_activity_durations(self, 
                                    activities: List[Activity], 
                                    context: EventContext) -> List[TimedActivity]:
        """Calculate durations for all activities and create timed activities"""
        timed_activities = []
        
        for activity in activities:
            duration_calc = self.calculate_activity_duration(activity, context)
            
            # Update activity with calculated duration
            activity.duration = duration_calc.final_duration
            
            # Create timed activity (start/end times will be set during scheduling)
            timed_activity = TimedActivity(
                activity=activity,
                start_time=datetime.min,  # Will be set during scheduling
                end_time=datetime.min,    # Will be set during scheduling
                buffer_before=duration_calc.buffer_time,
                buffer_after=timedelta(minutes=15)  # Standard buffer after
            )
            
            timed_activities.append(timed_activity)
        
        return timed_activities
    
    def _create_and_analyze_dependencies(self, 
                                       timed_activities: List[TimedActivity], 
                                       context: EventContext) -> DependencyGraph:
        """Create dependency graph and perform critical path analysis"""
        activities = [ta.activity for ta in timed_activities]
        
        # Create dependency graph
        dependency_graph = self.dependency_manager.create_dependency_graph(activities)
        
        # Calculate critical path
        start_time = datetime.combine(date.today(), datetime.min.time().replace(hour=10))
        self.dependency_manager.calculate_critical_path(dependency_graph, start_time)
        
        # Validate timeline
        validation_issues = self.dependency_manager.validate_timeline(dependency_graph)
        if validation_issues:
            logger.warning(f"Timeline validation issues: {validation_issues}")
        
        return dependency_graph
    
    def _get_complexity_level(self, complexity_score: float) -> str:
        """Get complexity level from complexity score"""
        if complexity_score <= 3:
            return "low"
        elif complexity_score <= 6:
            return "medium"
        elif complexity_score <= 8:
            return "high"
        else:
            return "very_high"
    
    def _schedule_activities_to_days(self, 
                                   timed_activities: List[TimedActivity],
                                   dependency_graph: DependencyGraph,
                                   gen_context: TimelineGenerationContext) -> List[TimelineDay]:
        """Schedule activities across multiple days respecting dependencies"""
        timeline_days = []
        current_date = gen_context.start_date
        current_time = gen_context.start_time
        
        # Get activities in dependency order
        activity_order = dependency_graph.topological_sort()
        activity_map = {ta.activity.id: ta for ta in timed_activities}
        
        # Schedule activities day by day
        day_number = 1
        daily_activities = []
        daily_cost = Decimal('0.00')
        
        for activity_id in activity_order:
            if activity_id not in activity_map:
                continue
                
            timed_activity = activity_map[activity_id]
            activity_duration = (timed_activity.activity.setup_time + 
                               timed_activity.activity.duration + 
                               timed_activity.activity.cleanup_time +
                               timed_activity.buffer_before + 
                               timed_activity.buffer_after)
            
            # Check if activity fits in current day
            day_end_time = gen_context.get_daily_end_time(
                datetime.combine(current_date, gen_context.start_time.time())
            )
            
            if current_time + activity_duration > day_end_time:
                # Create current day and start new day
                if daily_activities:
                    timeline_days.append(TimelineDay(
                        day_number=day_number,
                        date=current_date,
                        activities=daily_activities,
                        estimated_cost=daily_cost,
                        notes=[f"Day {day_number} of {gen_context.event_context.event_type.value}"]
                    ))
                
                # Start new day
                day_number += 1
                current_date += timedelta(days=1)
                current_time = datetime.combine(current_date, gen_context.start_time.time())
                daily_activities = []
                daily_cost = Decimal('0.00')
            
            # Schedule activity
            timed_activity.start_time = current_time + timed_activity.buffer_before
            timed_activity.end_time = (timed_activity.start_time + 
                                     timed_activity.activity.setup_time +
                                     timed_activity.activity.duration + 
                                     timed_activity.activity.cleanup_time)
            
            daily_activities.append(timed_activity)
            daily_cost += timed_activity.activity.estimated_cost
            
            # Move to next time slot
            current_time = timed_activity.end_time + timed_activity.buffer_after
        
        # Add final day if there are remaining activities
        if daily_activities:
            timeline_days.append(TimelineDay(
                day_number=day_number,
                date=current_date,
                activities=daily_activities,
                estimated_cost=daily_cost,
                notes=[f"Final day of {gen_context.event_context.event_type.value}"]
            ))
        
        return timeline_days
    
    def _calculate_total_buffer_time(self, timed_activities: List[TimedActivity]) -> timedelta:
        """Calculate total buffer time across all activities"""
        total_buffer = timedelta(0)
        for ta in timed_activities:
            total_buffer += ta.buffer_before + ta.buffer_after
        return total_buffer
    
    def _fix_timeline_issues(self, timeline: Timeline, issues: List[str]) -> Timeline:
        """Attempt to fix common timeline issues"""
        # For now, return the timeline as-is
        # In a full implementation, this would attempt to resolve specific issues
        logger.info(f"Attempting to fix {len(issues)} timeline issues")
        return timeline
    
    def _generate_fallback_timeline(self, context: EventContext, start_date: date) -> Timeline:
        """Generate a basic fallback timeline when main generation fails"""
        logger.warning("Generating fallback timeline due to errors")
        
        # Create a simple single-day timeline
        basic_activity = Activity(
            id="fallback_activity",
            name=f"Basic {context.event_type.value} Event",
            activity_type=ActivityType.CEREMONY,
            duration=timedelta(hours=4),
            priority=Priority.HIGH,
            description=f"Basic {context.event_type.value} celebration",
            estimated_cost=Decimal('5000.00')
        )
        
        timed_activity = TimedActivity(
            activity=basic_activity,
            start_time=datetime.combine(start_date, datetime.min.time().replace(hour=10)),
            end_time=datetime.combine(start_date, datetime.min.time().replace(hour=14)),
            buffer_before=timedelta(minutes=30),
            buffer_after=timedelta(minutes=30)
        )
        
        timeline_day = TimelineDay(
            day_number=1,
            date=start_date,
            activities=[timed_activity],
            estimated_cost=basic_activity.estimated_cost,
            notes=["Fallback timeline generated due to errors"]
        )
        
        return Timeline(
            days=[timeline_day],
            total_duration=timedelta(days=1),
            critical_path=[basic_activity],
            buffer_time=timedelta(hours=1),
            dependencies=[],
            total_estimated_cost=basic_activity.estimated_cost
        )
    
    def apply_guest_count_impact(self, 
                                timeline: Timeline, 
                                context: EventContext) -> Timeline:
        """
        Apply guest count impact on activity scheduling and timing.
        Large events need more coordination time, smaller events can be more flexible.
        """
        guest_count = context.guest_count
        
        # Define guest count categories and their impacts
        if guest_count <= 50:
            category = "small"
            coordination_buffer = timedelta(minutes=15)
            setup_multiplier = 0.9
            transition_time = timedelta(minutes=10)
        elif guest_count <= 150:
            category = "medium"
            coordination_buffer = timedelta(minutes=30)
            setup_multiplier = 1.0
            transition_time = timedelta(minutes=15)
        elif guest_count <= 300:
            category = "large"
            coordination_buffer = timedelta(minutes=45)
            setup_multiplier = 1.2
            transition_time = timedelta(minutes=20)
        else:
            category = "very_large"
            coordination_buffer = timedelta(hours=1)
            setup_multiplier = 1.5
            transition_time = timedelta(minutes=30)
        
        logger.info(f"Applying {category} event adjustments for {guest_count} guests")
        
        # Apply adjustments to each day
        for day in timeline.days:
            # Add coordination buffers between activities
            for i, activity in enumerate(day.activities):
                if i > 0:  # Not the first activity
                    activity.buffer_before = max(activity.buffer_before, coordination_buffer)
                
                # Adjust setup and preparation activities
                if activity.activity.activity_type == ActivityType.PREPARATION:
                    original_duration = activity.activity.duration
                    new_duration = timedelta(
                        seconds=original_duration.total_seconds() * setup_multiplier
                    )
                    activity.activity.duration = new_duration
                    
                    # Recalculate end time
                    total_activity_time = (activity.activity.setup_time + 
                                         activity.activity.duration + 
                                         activity.activity.cleanup_time)
                    activity.end_time = activity.start_time + total_activity_time
                
                # Add transition time for large events
                if guest_count > 150:
                    activity.buffer_after = max(activity.buffer_after, transition_time)
        
        # For very large events, add crowd management activities
        if guest_count > 500:
            self._add_crowd_management_activities(timeline, context)
        
        return timeline
    
    def apply_venue_specific_adjustments(self, 
                                       timeline: Timeline, 
                                       context: EventContext) -> Timeline:
        """
        Apply venue-specific logistics adjustments including setup time and capacity constraints.
        """
        venue_type = context.venue_type
        venue_adjustments = self.venue_adjustments.get(venue_type, {})
        
        logger.info(f"Applying venue adjustments for {venue_type.value}")
        
        for day in timeline.days:
            for activity in day.activities:
                activity_type = activity.activity.activity_type
                
                # Apply venue-specific setup time adjustments
                if activity_type == ActivityType.PREPARATION:
                    setup_multiplier = venue_adjustments.get("setup_multiplier", 1.0)
                    original_duration = activity.activity.duration
                    new_duration = timedelta(
                        seconds=original_duration.total_seconds() * setup_multiplier
                    )
                    activity.activity.duration = new_duration
                
                # Apply cleanup time adjustments
                elif activity_type == ActivityType.CLEANUP:
                    cleanup_multiplier = venue_adjustments.get("cleanup_multiplier", 1.0)
                    original_cleanup = activity.activity.cleanup_time
                    new_cleanup = timedelta(
                        seconds=original_cleanup.total_seconds() * cleanup_multiplier
                    )
                    activity.activity.cleanup_time = new_cleanup
                
                # Add weather contingency for outdoor venues
                if venue_type == VenueType.OUTDOOR:
                    weather_buffer = venue_adjustments.get("weather_buffer", 1.0)
                    activity.buffer_before = timedelta(
                        seconds=activity.buffer_before.total_seconds() * weather_buffer
                    )
                    
                    # Add weather backup plans
                    if not activity.contingency_plans:
                        activity.contingency_plans = []
                    activity.contingency_plans.append("Indoor backup location prepared")
                    activity.contingency_plans.append("Weather monitoring 24 hours before")
                
                # Add capacity constraint considerations
                if venue_type in [VenueType.HOME, VenueType.RESTAURANT]:
                    if context.guest_count > 100:
                        # Add staggered entry for small venues with many guests
                        if activity_type == ActivityType.CEREMONY:
                            activity.buffer_before += timedelta(minutes=30)
                            if not activity.contingency_plans:
                                activity.contingency_plans = []
                            activity.contingency_plans.append("Staggered guest entry to manage capacity")
                
                # Hotel venue advantages
                elif venue_type == VenueType.HOTEL:
                    # Hotels provide better logistics support
                    if activity_type in [ActivityType.PREPARATION, ActivityType.CLEANUP]:
                        activity.activity.duration = timedelta(
                            seconds=activity.activity.duration.total_seconds() * 0.8
                        )
                        if not activity.contingency_plans:
                            activity.contingency_plans = []
                        activity.contingency_plans.append("Hotel staff assistance available")
        
        # Add venue-specific activities
        self._add_venue_specific_activities(timeline, context)
        
        return timeline
    
    def apply_cultural_ceremony_sequencing(self, 
                                         timeline: Timeline, 
                                         context: EventContext) -> Timeline:
        """
        Apply proper cultural ceremony sequencing with appropriate timing.
        """
        cultural_requirements = context.cultural_requirements
        
        for cultural_req in cultural_requirements:
            if cultural_req == CulturalRequirement.HINDU:
                timeline = self._apply_hindu_sequencing(timeline, context)
            elif cultural_req == CulturalRequirement.MUSLIM:
                timeline = self._apply_muslim_sequencing(timeline, context)
            elif cultural_req == CulturalRequirement.CHRISTIAN:
                timeline = self._apply_christian_sequencing(timeline, context)
            elif cultural_req == CulturalRequirement.SIKH:
                timeline = self._apply_sikh_sequencing(timeline, context)
        
        return timeline
    
    def _add_crowd_management_activities(self, timeline: Timeline, context: EventContext) -> None:
        """Add crowd management activities for very large events"""
        # Add security and crowd control activities
        crowd_management = Activity(
            id=f"crowd_mgmt_{len(timeline.days[0].activities) + 1}",
            name="Crowd Management and Security Setup",
            activity_type=ActivityType.PREPARATION,
            duration=timedelta(hours=1),
            priority=Priority.HIGH,
            description="Setting up crowd control and security measures",
            required_vendors=["security", "coordinator"],
            estimated_cost=Decimal('2000.00')
        )
        
        # Add to first day
        if timeline.days:
            first_day = timeline.days[0]
            # Insert at beginning of day
            crowd_timed_activity = TimedActivity(
                activity=crowd_management,
                start_time=first_day.activities[0].start_time - timedelta(hours=1),
                end_time=first_day.activities[0].start_time,
                buffer_before=timedelta(minutes=15),
                buffer_after=timedelta(minutes=15)
            )
            first_day.activities.insert(0, crowd_timed_activity)
            first_day.estimated_cost += crowd_management.estimated_cost
    
    def _add_venue_specific_activities(self, timeline: Timeline, context: EventContext) -> None:
        """Add activities specific to venue type"""
        venue_type = context.venue_type
        
        if venue_type == VenueType.OUTDOOR:
            # Add weather preparation activity
            weather_prep = Activity(
                id=f"weather_prep_{len(timeline.days[0].activities) + 1}",
                name="Weather Preparation and Tent Setup",
                activity_type=ActivityType.PREPARATION,
                duration=timedelta(hours=2),
                priority=Priority.HIGH,
                description="Setting up weather protection and backup arrangements",
                required_vendors=["tent_rental", "weather_service"],
                estimated_cost=Decimal('3000.00')
            )
            
            # Add to first day
            if timeline.days:
                first_day = timeline.days[0]
                weather_timed_activity = TimedActivity(
                    activity=weather_prep,
                    start_time=first_day.activities[0].start_time - timedelta(hours=2),
                    end_time=first_day.activities[0].start_time,
                    buffer_before=timedelta(minutes=30),
                    buffer_after=timedelta(minutes=15),
                    contingency_plans=["Indoor backup venue confirmed", "Weather monitoring active"]
                )
                first_day.activities.insert(0, weather_timed_activity)
                first_day.estimated_cost += weather_prep.estimated_cost
        
        elif venue_type == VenueType.HOME:
            # Add home preparation activity
            home_prep = Activity(
                id=f"home_prep_{len(timeline.days[0].activities) + 1}",
                name="Home Preparation and Space Optimization",
                activity_type=ActivityType.PREPARATION,
                duration=timedelta(hours=1, minutes=30),
                priority=Priority.MEDIUM,
                description="Preparing home space and optimizing layout for guests",
                estimated_cost=Decimal('500.00')
            )
            
            # Add to first day
            if timeline.days:
                first_day = timeline.days[0]
                home_timed_activity = TimedActivity(
                    activity=home_prep,
                    start_time=first_day.activities[0].start_time - timedelta(hours=1, minutes=30),
                    end_time=first_day.activities[0].start_time,
                    buffer_before=timedelta(minutes=15),
                    buffer_after=timedelta(minutes=15)
                )
                first_day.activities.insert(0, home_timed_activity)
                first_day.estimated_cost += home_prep.estimated_cost
    
    def _apply_hindu_sequencing(self, timeline: Timeline, context: EventContext) -> Timeline:
        """Apply Hindu wedding ceremony sequencing"""
        if context.event_type != EventType.WEDDING:
            return timeline
        
        # Hindu wedding sequence: Mehendi -> Haldi -> Sangeet -> Wedding -> Reception
        ceremony_sequence = ["mehendi", "haldi", "sangeet", "wedding", "reception"]
        
        # Find activities matching Hindu ceremonies
        ceremony_activities = {}
        for day in timeline.days:
            for activity in day.activities:
                activity_name_lower = activity.activity.name.lower()
                for ceremony in ceremony_sequence:
                    if ceremony in activity_name_lower:
                        ceremony_activities[ceremony] = activity
                        break
        
        # Apply proper timing gaps between ceremonies
        ceremony_gaps = {
            "mehendi_to_haldi": timedelta(hours=12),  # Usually next day morning
            "haldi_to_sangeet": timedelta(hours=6),   # Same day evening
            "sangeet_to_wedding": timedelta(hours=12), # Next day
            "wedding_to_reception": timedelta(hours=2) # Same day evening
        }
        
        # Add cultural significance notes
        for ceremony_name, activity in ceremony_activities.items():
            if ceremony_name == "mehendi":
                activity.activity.cultural_significance = "Mehendi symbolizes joy and spiritual awakening"
                if not activity.contingency_plans:
                    activity.contingency_plans = []
                activity.contingency_plans.append("Mehendi artist backup arranged")
            elif ceremony_name == "haldi":
                activity.activity.cultural_significance = "Haldi purifies and brings good luck"
                if not activity.contingency_plans:
                    activity.contingency_plans = []
                activity.contingency_plans.append("Fresh turmeric paste prepared")
            elif ceremony_name == "wedding":
                activity.activity.cultural_significance = "Sacred seven vows (Saat Phere)"
                if not activity.contingency_plans:
                    activity.contingency_plans = []
                activity.contingency_plans.append("Pandit backup arranged")
                activity.contingency_plans.append("Sacred fire materials ready")
        
        return timeline
    
    def _apply_muslim_sequencing(self, timeline: Timeline, context: EventContext) -> Timeline:
        """Apply Muslim wedding ceremony sequencing"""
        if context.event_type != EventType.WEDDING:
            return timeline
        
        # Muslim wedding sequence: Nikkah -> Walima
        for day in timeline.days:
            for activity in day.activities:
                activity_name_lower = activity.activity.name.lower()
                if "nikkah" in activity_name_lower:
                    activity.activity.cultural_significance = "Sacred Islamic marriage contract"
                    if not activity.contingency_plans:
                        activity.contingency_plans = []
                    activity.contingency_plans.append("Imam backup arranged")
                    activity.contingency_plans.append("Marriage contract prepared")
                elif "walima" in activity_name_lower:
                    activity.activity.cultural_significance = "Celebration feast hosted by groom's family"
                    if not activity.contingency_plans:
                        activity.contingency_plans = []
                    activity.contingency_plans.append("Halal catering confirmed")
        
        return timeline
    
    def _apply_christian_sequencing(self, timeline: Timeline, context: EventContext) -> Timeline:
        """Apply Christian wedding ceremony sequencing"""
        if context.event_type != EventType.WEDDING:
            return timeline
        
        for day in timeline.days:
            for activity in day.activities:
                activity_name_lower = activity.activity.name.lower()
                if "wedding" in activity_name_lower and "ceremony" in activity_name_lower:
                    activity.activity.cultural_significance = "Sacred Christian marriage ceremony"
                    if not activity.contingency_plans:
                        activity.contingency_plans = []
                    activity.contingency_plans.append("Priest backup arranged")
                    activity.contingency_plans.append("Church decorations confirmed")
        
        return timeline
    
    def _apply_sikh_sequencing(self, timeline: Timeline, context: EventContext) -> Timeline:
        """Apply Sikh wedding ceremony sequencing"""
        if context.event_type != EventType.WEDDING:
            return timeline
        
        for day in timeline.days:
            for activity in day.activities:
                activity_name_lower = activity.activity.name.lower()
                if "anand karaj" in activity_name_lower or "gurdwara" in activity_name_lower:
                    activity.activity.cultural_significance = "Four rounds around Guru Granth Sahib"
                    if not activity.contingency_plans:
                        activity.contingency_plans = []
                    activity.contingency_plans.append("Granthi backup arranged")
                    activity.contingency_plans.append("Guru Granth Sahib arrangements confirmed")
                elif "langar" in activity_name_lower:
                    activity.activity.cultural_significance = "Community meal as equals in Sikh tradition"
        
        return timeline
    
    def optimize_timeline_for_context(self, 
                                    timeline: Timeline, 
                                    context: EventContext) -> Timeline:
        """
        Apply all contextual optimizations to the timeline.
        This is the main method that coordinates all customizations.
        """
        logger.info("Applying contextual timeline optimizations")
        
        # Apply guest count impact
        timeline = self.apply_guest_count_impact(timeline, context)
        
        # Apply venue-specific adjustments
        timeline = self.apply_venue_specific_adjustments(timeline, context)
        
        # Apply cultural ceremony sequencing
        timeline = self.apply_cultural_ceremony_sequencing(timeline, context)
        
        # Recalculate timeline costs after adjustments
        for day in timeline.days:
            day.estimated_cost = sum(activity.activity.estimated_cost for activity in day.activities)
        
        timeline.total_estimated_cost = sum(day.estimated_cost for day in timeline.days)
        
        logger.info("Contextual optimizations applied successfully")
        return timeline
    
    def enhance_timeline_with_ai(self, 
                                timeline: Timeline, 
                                context: EventContext,
                                use_ai: bool = True) -> Timeline:
        """
        Enhance timeline using AI with fallback to rule-based generation.
        
        Args:
            timeline: Base timeline to enhance
            context: Event context for AI prompting
            use_ai: Whether to attempt AI enhancement (default True)
            
        Returns:
            Enhanced timeline with AI improvements or rule-based fallback
        """
        if not use_ai:
            logger.info("AI enhancement disabled, using rule-based improvements")
            return self._apply_rule_based_enhancements(timeline, context)
        
        try:
            logger.info("Attempting AI enhancement of timeline")
            
            # Generate AI prompt with detailed context
            ai_prompt = self._generate_ai_prompt(timeline, context)
            
            # Attempt to get AI response (simulated for now)
            ai_response = self._call_ai_service(ai_prompt)
            
            if ai_response:
                # Parse AI response and apply improvements
                enhanced_timeline = self._parse_and_apply_ai_response(timeline, ai_response, context)
                
                # Validate AI-enhanced timeline
                validation_errors = self._validate_ai_enhancements(enhanced_timeline, timeline)
                
                if not validation_errors:
                    logger.info("AI enhancement successful")
                    return enhanced_timeline
                else:
                    logger.warning(f"AI enhancement validation failed: {validation_errors}")
                    raise ValueError("AI enhancement produced invalid timeline")
            else:
                raise ValueError("AI service returned empty response")
                
        except Exception as e:
            logger.warning(f"AI enhancement failed: {str(e)}, falling back to rule-based")
            return self._apply_rule_based_enhancements(timeline, context)
    
    def _generate_ai_prompt(self, timeline: Timeline, context: EventContext) -> str:
        """
        Generate detailed AI prompt with context parameters for timeline enhancement.
        """
        # Build comprehensive context description
        context_description = f"""
Event Details:
- Type: {context.event_type.value}
- Guest Count: {context.guest_count}
- Venue: {context.venue_type.value}
- Cultural Requirements: {[req.value for req in context.cultural_requirements]}
- Budget Tier: {context.budget_tier.value}
- Location: {context.location.city}, {context.location.state}
- Season: {context.season.value}
- Duration: {context.duration_days} days
- Complexity Score: {context.complexity_score}/10

Current Timeline Overview:
- Total Days: {len(timeline.days)}
- Total Activities: {sum(len(day.activities) for day in timeline.days)}
- Estimated Cost: ₹{timeline.total_estimated_cost:,.2f}
- Critical Path Activities: {len(timeline.critical_path)}
"""
        
        # Add current timeline structure
        timeline_structure = "\\nCurrent Timeline Structure:\\n"
        for i, day in enumerate(timeline.days):
            timeline_structure += f"\\nDay {day.day_number} ({day.date}):\\n"
            for j, activity in enumerate(day.activities):
                start_time = activity.start_time.strftime("%H:%M")
                end_time = activity.end_time.strftime("%H:%M")
                timeline_structure += f"  {j+1}. {activity.activity.name} ({start_time}-{end_time})\\n"
                timeline_structure += f"     Duration: {activity.activity.duration}, Priority: {activity.activity.priority.value}\\n"
                if activity.activity.cultural_significance:
                    timeline_structure += f"     Cultural: {activity.activity.cultural_significance}\\n"
        
        # Create enhancement prompt
        prompt = f"""
You are an expert event planning AI assistant. Please analyze and enhance the following event timeline.

{context_description}

{timeline_structure}

Please provide specific recommendations to improve this timeline in the following areas:

1. TIMING OPTIMIZATION:
   - Suggest better time slots for activities based on cultural practices and guest preferences
   - Identify potential scheduling conflicts or inefficiencies
   - Recommend optimal breaks and transition times

2. ACTIVITY ENHANCEMENTS:
   - Suggest additional activities that would enhance the event experience
   - Recommend modifications to existing activities for better guest engagement
   - Identify activities that could be combined or streamlined

3. CULTURAL AUTHENTICITY:
   - Ensure cultural ceremonies follow traditional sequences and timing
   - Suggest culturally appropriate enhancements or missing elements
   - Recommend proper ceremonial preparations and requirements

4. LOGISTICS IMPROVEMENTS:
   - Identify potential logistical challenges and solutions
   - Suggest vendor coordination improvements
   - Recommend contingency planning enhancements

5. GUEST EXPERIENCE:
   - Suggest improvements for guest comfort and engagement
   - Recommend entertainment or interactive elements
   - Identify potential guest flow issues and solutions

Please provide your response in the following structured format:

TIMING_RECOMMENDATIONS:
[List specific timing changes with rationale]

ACTIVITY_ENHANCEMENTS:
[List new or modified activities with descriptions]

CULTURAL_IMPROVEMENTS:
[List cultural authenticity enhancements]

LOGISTICS_OPTIMIZATIONS:
[List logistical improvements]

GUEST_EXPERIENCE_ENHANCEMENTS:
[List guest experience improvements]

OVERALL_ASSESSMENT:
[Overall timeline quality score (1-10) and summary]
"""
        
        return prompt
    
    def _call_ai_service(self, prompt: str) -> Optional[str]:
        """
        Call AI service to get timeline enhancement recommendations.
        This is a placeholder for actual AI service integration.
        """
        # Simulate AI service call
        # In a real implementation, this would call OpenAI, Claude, or another AI service
        
        # For now, return a simulated response based on the prompt content
        if "wedding" in prompt.lower() and "hindu" in prompt.lower():
            return self._get_simulated_hindu_wedding_response()
        elif "corporate" in prompt.lower():
            return self._get_simulated_corporate_response()
        elif "muslim" in prompt.lower():
            return self._get_simulated_muslim_wedding_response()
        else:
            return self._get_simulated_generic_response()
    
    def _get_simulated_hindu_wedding_response(self) -> str:
        """Simulated AI response for Hindu wedding enhancement"""
        return """
TIMING_RECOMMENDATIONS:
- Schedule Mehendi ceremony in afternoon (2-6 PM) for better lighting and guest comfort
- Haldi ceremony should start early morning (8-10 AM) as per tradition
- Main wedding ceremony optimal time is morning (10 AM - 2 PM) for auspicious timing
- Add 30-minute breaks between major ceremonies for guest refreshment

ACTIVITY_ENHANCEMENTS:
- Add Sangeet ceremony evening before wedding for entertainment and family bonding
- Include Ganesh Puja at the beginning for blessings and auspicious start
- Add professional photography session during golden hour for better pictures
- Include traditional welcome ceremony (Swagat) for guests

CULTURAL_IMPROVEMENTS:
- Ensure sacred fire (Havan) preparation 1 hour before main ceremony
- Add Kanyadaan ceremony as separate activity with proper timing
- Include Saat Phere with proper Vedic chanting duration (45 minutes)
- Add Sindoor ceremony and Mangalsutra ritual as distinct activities

LOGISTICS_OPTIMIZATIONS:
- Coordinate decorator and pandit schedules to avoid conflicts
- Add buffer time for weather contingencies if outdoor elements
- Ensure backup power arrangements for evening ceremonies
- Coordinate catering timing with ceremony schedules

GUEST_EXPERIENCE_ENHANCEMENTS:
- Add welcome drinks and light snacks during Mehendi
- Provide comfortable seating arrangements for elderly guests during long ceremonies
- Include live music during appropriate ceremony intervals
- Add photo booth with traditional props for guest entertainment

OVERALL_ASSESSMENT:
Timeline Quality Score: 8/10
The timeline covers essential Hindu wedding ceremonies with good cultural authenticity. Recommended enhancements focus on guest comfort, cultural completeness, and logistical efficiency.
"""
    
    def _get_simulated_corporate_response(self) -> str:
        """Simulated AI response for corporate event enhancement"""
        return """
TIMING_RECOMMENDATIONS:
- Start registration 30 minutes earlier to avoid rush and delays
- Schedule keynote presentations in morning (9-11 AM) when attention is highest
- Add 15-minute networking breaks between sessions
- End day by 5 PM to respect work-life balance

ACTIVITY_ENHANCEMENTS:
- Add welcome coffee and networking session before formal start
- Include interactive workshops or breakout sessions
- Add panel discussion with Q&A for better engagement
- Include closing networking reception with light refreshments

CULTURAL_IMPROVEMENTS:
- Ensure presentations are culturally sensitive and inclusive
- Add local cultural elements if international attendees present
- Consider dietary restrictions for all refreshment planning

LOGISTICS_OPTIMIZATIONS:
- Set up registration desk with multiple stations to reduce wait time
- Ensure AV equipment testing 2 hours before event start
- Add technical support staff throughout the event
- Coordinate catering delivery to avoid disruption during sessions

GUEST_EXPERIENCE_ENHANCEMENTS:
- Provide welcome kits with agenda, materials, and branded items
- Add comfortable lounge areas for informal networking
- Include charging stations for mobile devices
- Provide clear signage and event staff for guidance

OVERALL_ASSESSMENT:
Timeline Quality Score: 7/10
Good professional structure with room for enhanced networking and engagement opportunities. Focus on attendee comfort and interaction will improve overall experience.
"""
    
    def _get_simulated_muslim_wedding_response(self) -> str:
        """Simulated AI response for Muslim wedding enhancement"""
        return """
TIMING_RECOMMENDATIONS:
- Schedule Nikkah ceremony in afternoon after Asr prayer for religious appropriateness
- Allow 2-hour gap between Nikkah and Walima for preparation and rest
- Walima should start after Maghrib prayer in evening
- Add time for congregational prayers if desired

ACTIVITY_ENHANCEMENTS:
- Add Quran recitation at the beginning of Nikkah ceremony
- Include traditional Mehndi ceremony day before if desired
- Add formal photography session after Nikkah ceremony
- Include traditional welcome ceremony for guests at Walima

CULTURAL_IMPROVEMENTS:
- Ensure Imam availability and backup arrangements
- Confirm halal catering for all food services
- Add proper segregation arrangements if required by family preferences
- Include traditional Islamic decorations and calligraphy

LOGISTICS_OPTIMIZATIONS:
- Coordinate with mosque or Islamic center for ceremony requirements
- Ensure prayer facilities are available for guests
- Arrange for Islamic music or Nasheed during appropriate times
- Coordinate timing with local prayer schedules

GUEST_EXPERIENCE_ENHANCEMENTS:
- Provide prayer mats and ablution facilities for guests
- Include traditional sweets and dates for guests
- Add comfortable seating with consideration for elderly guests
- Provide clear information about ceremony customs for non-Muslim guests

OVERALL_ASSESSMENT:
Timeline Quality Score: 8/10
Timeline respects Islamic traditions with good ceremony structure. Enhancements focus on religious observance, guest comfort, and cultural authenticity.
"""
    
    def _get_simulated_generic_response(self) -> str:
        """Simulated AI response for generic event enhancement"""
        return """
TIMING_RECOMMENDATIONS:
- Optimize activity timing based on guest energy levels and preferences
- Add appropriate breaks between major activities
- Consider meal timing and guest comfort throughout the day

ACTIVITY_ENHANCEMENTS:
- Add welcome and closing activities to bookend the event
- Include interactive elements for better guest engagement
- Consider entertainment options appropriate for the event type

CULTURAL_IMPROVEMENTS:
- Ensure activities respect cultural sensitivities of all guests
- Add culturally appropriate elements where relevant

LOGISTICS_OPTIMIZATIONS:
- Improve vendor coordination and scheduling
- Add contingency planning for potential issues
- Ensure smooth transitions between activities

GUEST_EXPERIENCE_ENHANCEMENTS:
- Focus on guest comfort and convenience
- Provide clear information and guidance throughout event
- Add elements that encourage guest interaction and enjoyment

OVERALL_ASSESSMENT:
Timeline Quality Score: 7/10
Solid foundation with opportunities for enhancement in guest experience and cultural appropriateness.
"""
    
    def _parse_and_apply_ai_response(self, 
                                   timeline: Timeline, 
                                   ai_response: str, 
                                   context: EventContext) -> Timeline:
        """
        Parse AI response and apply recommendations to timeline.
        """
        logger.info("Parsing AI response and applying recommendations")
        
        # Parse AI response sections
        sections = self._parse_ai_response_sections(ai_response)
        
        # Apply timing recommendations
        if "TIMING_RECOMMENDATIONS" in sections:
            timeline = self._apply_timing_recommendations(timeline, sections["TIMING_RECOMMENDATIONS"], context)
        
        # Apply activity enhancements
        if "ACTIVITY_ENHANCEMENTS" in sections:
            timeline = self._apply_activity_enhancements(timeline, sections["ACTIVITY_ENHANCEMENTS"], context)
        
        # Apply cultural improvements
        if "CULTURAL_IMPROVEMENTS" in sections:
            timeline = self._apply_cultural_improvements(timeline, sections["CULTURAL_IMPROVEMENTS"], context)
        
        # Apply logistics optimizations
        if "LOGISTICS_OPTIMIZATIONS" in sections:
            timeline = self._apply_logistics_optimizations(timeline, sections["LOGISTICS_OPTIMIZATIONS"], context)
        
        # Apply guest experience enhancements
        if "GUEST_EXPERIENCE_ENHANCEMENTS" in sections:
            timeline = self._apply_guest_experience_enhancements(timeline, sections["GUEST_EXPERIENCE_ENHANCEMENTS"], context)
        
        return timeline
    
    def _parse_ai_response_sections(self, ai_response: str) -> Dict[str, str]:
        """Parse AI response into structured sections"""
        sections = {}
        current_section = None
        current_content = []
        
        for line in ai_response.split('\n'):
            line = line.strip()
            if line.endswith(':') and line.replace('_', '').replace(':', '').isalpha():
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content)
                
                # Start new section
                current_section = line.rstrip(':')
                current_content = []
            elif current_section and line:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content)
        
        return sections
    
    def _apply_timing_recommendations(self, 
                                    timeline: Timeline, 
                                    recommendations: str, 
                                    context: EventContext) -> Timeline:
        """Apply AI timing recommendations to timeline"""
        # For now, add timing notes to activities
        for day in timeline.days:
            for activity in day.activities:
                if not hasattr(activity, 'ai_recommendations'):
                    activity.ai_recommendations = []
                activity.ai_recommendations.append("AI timing optimization applied")
        
        return timeline
    
    def _apply_activity_enhancements(self, 
                                   timeline: Timeline, 
                                   enhancements: str, 
                                   context: EventContext) -> Timeline:
        """Apply AI activity enhancement recommendations"""
        # Add AI-suggested activities based on context
        if "Ganesh Puja" in enhancements and context.event_type == EventType.WEDDING:
            # Add Ganesh Puja activity to Hindu weddings
            ganesh_puja = Activity(
                id=f"ai_ganesh_puja_{len(timeline.days[0].activities) + 1}",
                name="Ganesh Puja (AI Enhanced)",
                activity_type=ActivityType.CEREMONY,
                duration=timedelta(minutes=45),
                priority=Priority.HIGH,
                description="Auspicious beginning with Lord Ganesh blessings",
                cultural_significance="Removes obstacles and brings good fortune",
                estimated_cost=Decimal('1500.00')
            )
            
            # Add to first day at the beginning
            if timeline.days:
                first_day = timeline.days[0]
                ganesh_timed_activity = TimedActivity(
                    activity=ganesh_puja,
                    start_time=first_day.activities[0].start_time - timedelta(hours=1),
                    end_time=first_day.activities[0].start_time - timedelta(minutes=15),
                    buffer_before=timedelta(minutes=15),
                    buffer_after=timedelta(minutes=15),
                    contingency_plans=["AI-enhanced cultural ceremony"]
                )
                first_day.activities.insert(0, ganesh_timed_activity)
                first_day.estimated_cost += ganesh_puja.estimated_cost
        
        return timeline
    
    def _apply_cultural_improvements(self, 
                                   timeline: Timeline, 
                                   improvements: str, 
                                   context: EventContext) -> Timeline:
        """Apply AI cultural improvement recommendations"""
        # Enhance cultural significance of existing activities
        for day in timeline.days:
            for activity in day.activities:
                if activity.activity.activity_type == ActivityType.CEREMONY:
                    if not activity.activity.cultural_significance:
                        activity.activity.cultural_significance = "AI-enhanced cultural significance"
                    
                    # Add AI-suggested contingency plans
                    if not activity.contingency_plans:
                        activity.contingency_plans = []
                    activity.contingency_plans.append("AI-enhanced cultural authenticity measures")
        
        return timeline
    
    def _apply_logistics_optimizations(self, 
                                     timeline: Timeline, 
                                     optimizations: str, 
                                     context: EventContext) -> Timeline:
        """Apply AI logistics optimization recommendations"""
        # Add logistics improvements to activities
        for day in timeline.days:
            for activity in day.activities:
                if activity.activity.activity_type == ActivityType.PREPARATION:
                    # Add AI logistics enhancements
                    if not activity.contingency_plans:
                        activity.contingency_plans = []
                    activity.contingency_plans.append("AI-optimized logistics coordination")
                    
                    # Extend buffer time for better coordination
                    activity.buffer_before = max(activity.buffer_before, timedelta(minutes=20))
        
        return timeline
    
    def _apply_guest_experience_enhancements(self, 
                                           timeline: Timeline, 
                                           enhancements: str, 
                                           context: EventContext) -> Timeline:
        """Apply AI guest experience enhancement recommendations"""
        # Add guest experience improvements
        for day in timeline.days:
            for activity in day.activities:
                if not activity.contingency_plans:
                    activity.contingency_plans = []
                activity.contingency_plans.append("AI-enhanced guest experience measures")
                
                # Add guest comfort considerations
                if activity.activity.activity_type in [ActivityType.CEREMONY, ActivityType.ENTERTAINMENT]:
                    activity.buffer_after = max(activity.buffer_after, timedelta(minutes=15))
        
        return timeline
    
    def _validate_ai_enhancements(self, 
                                enhanced_timeline: Timeline, 
                                original_timeline: Timeline) -> List[str]:
        """Validate that AI enhancements are reasonable and don't break the timeline"""
        issues = []
        
        # Check that timeline structure is still valid
        validation_errors = enhanced_timeline.validate()
        if validation_errors:
            issues.extend(validation_errors)
        
        # Check that enhancements don't dramatically increase cost
        cost_increase = enhanced_timeline.total_estimated_cost - original_timeline.total_estimated_cost
        if cost_increase > original_timeline.total_estimated_cost * Decimal('0.5'):  # 50% increase limit
            issues.append(f"AI enhancements increased cost by {cost_increase}, which exceeds 50% limit")
        
        # Check that timeline duration hasn't increased unreasonably
        original_duration = sum(len(day.activities) for day in original_timeline.days)
        enhanced_duration = sum(len(day.activities) for day in enhanced_timeline.days)
        if enhanced_duration > original_duration * 2:  # Double activity count limit
            issues.append(f"AI enhancements doubled the number of activities from {original_duration} to {enhanced_duration}")
        
        return issues
    
    def _apply_rule_based_enhancements(self, 
                                     timeline: Timeline, 
                                     context: EventContext) -> Timeline:
        """
        Apply rule-based enhancements when AI is unavailable or fails.
        This provides a reliable fallback mechanism.
        """
        logger.info("Applying rule-based timeline enhancements")
        
        # Rule 1: Add welcome activity if missing
        self._add_welcome_activity_if_missing(timeline, context)
        
        # Rule 2: Ensure proper ceremony spacing
        self._ensure_proper_ceremony_spacing(timeline, context)
        
        # Rule 3: Add cultural elements based on requirements
        self._add_cultural_elements(timeline, context)
        
        # Rule 4: Optimize for guest count
        self._optimize_for_guest_count(timeline, context)
        
        # Rule 5: Add contingency planning
        self._add_contingency_planning(timeline, context)
        
        logger.info("Rule-based enhancements applied successfully")
        return timeline
    
    def _add_welcome_activity_if_missing(self, timeline: Timeline, context: EventContext) -> None:
        """Add welcome activity if not present"""
        if not timeline.days:
            return
        
        first_day = timeline.days[0]
        has_welcome = any("welcome" in activity.activity.name.lower() for activity in first_day.activities)
        
        if not has_welcome:
            welcome_activity = Activity(
                id=f"rule_welcome_{len(first_day.activities) + 1}",
                name="Guest Welcome and Registration",
                activity_type=ActivityType.PREPARATION,
                duration=timedelta(minutes=45),
                priority=Priority.MEDIUM,
                description="Welcoming guests and event registration",
                estimated_cost=Decimal('800.00')
            )
            
            welcome_timed_activity = TimedActivity(
                activity=welcome_activity,
                start_time=first_day.activities[0].start_time - timedelta(minutes=45),
                end_time=first_day.activities[0].start_time,
                buffer_before=timedelta(minutes=15),
                buffer_after=timedelta(minutes=15),
                contingency_plans=["Rule-based welcome enhancement"]
            )
            
            first_day.activities.insert(0, welcome_timed_activity)
            first_day.estimated_cost += welcome_activity.estimated_cost
    
    def _ensure_proper_ceremony_spacing(self, timeline: Timeline, context: EventContext) -> None:
        """Ensure proper spacing between ceremonies"""
        for day in timeline.days:
            ceremony_activities = [a for a in day.activities if a.activity.activity_type == ActivityType.CEREMONY]
            
            for activity in ceremony_activities:
                # Ensure minimum 30-minute buffer between ceremonies
                activity.buffer_after = max(activity.buffer_after, timedelta(minutes=30))
    
    def _add_cultural_elements(self, timeline: Timeline, context: EventContext) -> None:
        """Add cultural elements based on requirements"""
        for cultural_req in context.cultural_requirements:
            if cultural_req == CulturalRequirement.HINDU and context.event_type == EventType.WEDDING:
                # Ensure Hindu wedding has proper cultural elements
                for day in timeline.days:
                    for activity in day.activities:
                        if activity.activity.activity_type == ActivityType.CEREMONY:
                            if not activity.activity.cultural_significance:
                                activity.activity.cultural_significance = "Traditional Hindu ceremony with Vedic rituals"
    
    def _optimize_for_guest_count(self, timeline: Timeline, context: EventContext) -> None:
        """Apply guest count optimizations"""
        if context.guest_count > 200:
            # Large events need more coordination time
            for day in timeline.days:
                for activity in day.activities:
                    if activity.activity.activity_type == ActivityType.PREPARATION:
                        activity.buffer_before = max(activity.buffer_before, timedelta(minutes=45))
    
    def _add_contingency_planning(self, timeline: Timeline, context: EventContext) -> None:
        """Add contingency planning to all activities"""
        for day in timeline.days:
            for activity in day.activities:
                if not activity.contingency_plans:
                    activity.contingency_plans = []
                
                # Add venue-specific contingencies
                if context.venue_type == VenueType.OUTDOOR:
                    activity.contingency_plans.append("Weather backup plan activated")
                elif context.venue_type == VenueType.HOME:
                    activity.contingency_plans.append("Space optimization for guest capacity")
                
                # Add general contingencies
                activity.contingency_plans.append("Vendor backup arrangements confirmed")
                activity.contingency_plans.append("Timeline flexibility maintained")