"""
Fallback mechanisms and error recovery for the intelligent timeline and budget system.
"""
import logging
import json
import os
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime, timedelta
from decimal import Decimal
from functools import wraps
import time

from ..models.core import EventContext, Timeline, BudgetAllocation, TimelineDay, Activity, TimedActivity
from ..models.enums import EventType, VenueType, BudgetTier, ActivityType, Priority
from ..services.cultural_templates import CulturalTemplateService
from .error_handling import EventPlanningError, TimelineGenerationError, BudgetAllocationError


# Configure logging
logger = logging.getLogger(__name__)


class FallbackManager:
    """Manages fallback strategies for various system components"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.ensure_cache_directory()
        self._ai_service_available = True
        self._last_ai_check = datetime.now()
        self._ai_check_interval = timedelta(minutes=5)
    
    def ensure_cache_directory(self) -> None:
        """Ensure cache directory exists"""
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir, exist_ok=True)
    
    def is_ai_service_available(self) -> bool:
        """Check if AI service is available with caching"""
        now = datetime.now()
        if now - self._last_ai_check > self._ai_check_interval:
            # In a real implementation, this would ping the AI service
            # For now, we'll simulate availability
            self._ai_service_available = True  # Assume available for testing
            self._last_ai_check = now
        
        return self._ai_service_available
    
    def set_ai_service_status(self, available: bool) -> None:
        """Manually set AI service status (for testing)"""
        self._ai_service_available = available
        self._last_ai_check = datetime.now()


# Global fallback manager instance
fallback_manager = FallbackManager()


def with_fallback(fallback_func: Callable, log_errors: bool = True):
    """
    Decorator to provide fallback functionality for functions.
    
    Args:
        fallback_func: Function to call if primary function fails
        log_errors: Whether to log errors when falling back
    """
    def decorator(primary_func: Callable):
        @wraps(primary_func)
        def wrapper(*args, **kwargs):
            try:
                return primary_func(*args, **kwargs)
            except Exception as e:
                if log_errors:
                    logger.warning(f"Primary function {primary_func.__name__} failed: {str(e)}")
                    logger.info(f"Falling back to {fallback_func.__name__}")
                
                try:
                    return fallback_func(*args, **kwargs)
                except Exception as fallback_error:
                    logger.error(f"Fallback function {fallback_func.__name__} also failed: {str(fallback_error)}")
                    raise EventPlanningError(
                        f"Both primary and fallback methods failed. Primary: {str(e)}, Fallback: {str(fallback_error)}"
                    )
        
        return wrapper
    return decorator


def retry_with_backoff(max_retries: int = 3, base_delay: float = 1.0, max_delay: float = 60.0):
    """
    Decorator to retry function calls with exponential backoff.
    
    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
    """
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt == max_retries:
                        break
                    
                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}")
                    logger.info(f"Retrying in {delay} seconds...")
                    time.sleep(delay)
            
            logger.error(f"All {max_retries + 1} attempts failed for {func.__name__}")
            raise last_exception
        
        return wrapper
    return decorator


class CachedPatternData:
    """Manages cached pattern data for offline operation"""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache_dir = cache_dir
        self.pattern_cache_file = os.path.join(cache_dir, "event_patterns.json")
        self.template_cache_file = os.path.join(cache_dir, "event_templates.json")
        self._pattern_cache = {}
        self._template_cache = {}
        self.load_cached_data()
    
    def load_cached_data(self) -> None:
        """Load cached pattern and template data"""
        try:
            if os.path.exists(self.pattern_cache_file):
                with open(self.pattern_cache_file, 'r') as f:
                    self._pattern_cache = json.load(f)
                logger.info(f"Loaded {len(self._pattern_cache)} cached patterns")
        except Exception as e:
            logger.warning(f"Failed to load pattern cache: {str(e)}")
        
        try:
            if os.path.exists(self.template_cache_file):
                with open(self.template_cache_file, 'r') as f:
                    self._template_cache = json.load(f)
                logger.info(f"Loaded {len(self._template_cache)} cached templates")
        except Exception as e:
            logger.warning(f"Failed to load template cache: {str(e)}")
    
    def save_cached_data(self) -> None:
        """Save pattern and template data to cache"""
        try:
            with open(self.pattern_cache_file, 'w') as f:
                json.dump(self._pattern_cache, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save pattern cache: {str(e)}")
        
        try:
            with open(self.template_cache_file, 'w') as f:
                json.dump(self._template_cache, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save template cache: {str(e)}")
    
    def get_cached_pattern(self, event_key: str) -> Optional[Dict[str, Any]]:
        """Get cached pattern for event type"""
        return self._pattern_cache.get(event_key)
    
    def cache_pattern(self, event_key: str, pattern_data: Dict[str, Any]) -> None:
        """Cache pattern data for event type"""
        self._pattern_cache[event_key] = pattern_data
        self.save_cached_data()
    
    def get_cached_template(self, template_key: str) -> Optional[Dict[str, Any]]:
        """Get cached template"""
        return self._template_cache.get(template_key)
    
    def cache_template(self, template_key: str, template_data: Dict[str, Any]) -> None:
        """Cache template data"""
        self._template_cache[template_key] = template_data
        self.save_cached_data()


# Global cached pattern data instance
cached_data = CachedPatternData()


def fallback_timeline_generation(context: EventContext) -> Timeline:
    """
    Fallback timeline generation using rule-based approach.
    Used when AI-enhanced generation fails.
    """
    logger.info("Using fallback timeline generation")
    
    try:
        # Get basic activities based on event type and cultural requirements
        activities = []
        
        # Add cultural ceremony activities if specified
        cultural_service = CulturalTemplateService()
        primary_ceremony = cultural_service.select_primary_ceremony(context)
        
        if primary_ceremony:
            activity_templates = primary_ceremony.get_activities(context, include_optional=False)
            for template in activity_templates:
                activity = template.to_activity(context, f"activity_{len(activities)}")
                activities.append(activity)
        
        # Add basic event activities if no cultural activities
        if not activities:
            activities = _get_basic_event_activities(context.event_type)
        
        # Create timeline days
        days = []
        activities_per_day = len(activities) // context.duration_days
        if activities_per_day == 0:
            activities_per_day = 1
        
        for day_num in range(1, context.duration_days + 1):
            start_idx = (day_num - 1) * activities_per_day
            end_idx = start_idx + activities_per_day
            if day_num == context.duration_days:
                end_idx = len(activities)  # Include remaining activities on last day
            
            day_activities = activities[start_idx:end_idx]
            timed_activities = _schedule_activities_for_day(day_activities, day_num)
            
            day = TimelineDay(
                day_number=day_num,
                date=datetime.now().date(),  # Placeholder date
                activities=timed_activities,
                estimated_cost=Decimal('1000') * len(timed_activities),
                notes=[f"Day {day_num} activities"],
                contingency_plans=["Weather backup plan", "Vendor backup plan"]
            )
            days.append(day)
        
        timeline = Timeline(
            days=days,
            total_duration=timedelta(days=context.duration_days),
            critical_path=activities[:3],  # First 3 activities as critical path
            buffer_time=timedelta(hours=2),
            dependencies=[],
            total_estimated_cost=sum(day.estimated_cost for day in days)
        )
        
        return timeline
        
    except Exception as e:
        logger.error(f"Fallback timeline generation failed: {str(e)}")
        raise TimelineGenerationError(f"All timeline generation methods failed: {str(e)}", context)


def fallback_budget_allocation(total_budget: Decimal, context: EventContext) -> BudgetAllocation:
    """
    Fallback budget allocation using industry standard percentages.
    Used when intelligent allocation fails.
    """
    logger.info("Using fallback budget allocation")
    
    try:
        # Get standard allocation percentages based on event type
        if context.event_type == EventType.WEDDING:
            percentages = {
                'venue': 25.0,
                'catering': 40.0,
                'decoration': 15.0,
                'photography': 10.0,
                'entertainment': 5.0,
                'contingency': 5.0
            }
        elif context.event_type == EventType.CORPORATE:
            percentages = {
                'venue': 30.0,
                'catering': 35.0,
                'entertainment': 15.0,
                'photography': 5.0,
                'transportation': 10.0,
                'contingency': 5.0
            }
        else:  # Default for other event types
            percentages = {
                'venue': 20.0,
                'catering': 35.0,
                'decoration': 20.0,
                'entertainment': 15.0,
                'contingency': 10.0
            }
        
        # Create category allocations
        from ..models.enums import BudgetCategory
        categories = {}
        
        for category_name, percentage in percentages.items():
            try:
                # Map string names to enum values with proper mapping
                category_mapping = {
                    'venue': BudgetCategory.VENUE,
                    'catering': BudgetCategory.CATERING,
                    'decoration': BudgetCategory.DECORATION,
                    'entertainment': BudgetCategory.ENTERTAINMENT,
                    'photography': BudgetCategory.PHOTOGRAPHY,
                    'transportation': BudgetCategory.TRANSPORTATION,
                    'contingency': BudgetCategory.CONTINGENCY,
                    'miscellaneous': BudgetCategory.MISCELLANEOUS
                }
                
                category_enum = category_mapping.get(category_name.lower())
                if not category_enum:
                    # Skip unknown categories
                    continue
            except Exception:
                # Skip unknown categories
                continue
            
            amount = total_budget * Decimal(str(percentage / 100))
            
            from ..models.core import CategoryAllocation
            allocation = CategoryAllocation(
                category=category_enum,
                amount=amount,
                percentage=percentage,
                justification=f"Standard {percentage}% allocation for {context.event_type.value} events",
                alternatives=[],
                priority=Priority.MEDIUM
            )
            categories[category_enum] = allocation
        
        budget_allocation = BudgetAllocation(
            total_budget=total_budget,
            categories=categories,
            per_person_cost=total_budget / context.guest_count,
            contingency_percentage=5.0,
            regional_adjustments={},
            seasonal_adjustments={}
        )
        
        return budget_allocation
        
    except Exception as e:
        logger.error(f"Fallback budget allocation failed: {str(e)}")
        raise BudgetAllocationError(f"All budget allocation methods failed: {str(e)}", total_budget)


def _get_basic_event_activities(event_type: EventType) -> List[Activity]:
    """Get basic activities for event type"""
    if event_type == EventType.WEDDING:
        return [
            Activity(
                id="setup",
                name="Venue Setup",
                activity_type=ActivityType.PREPARATION,
                duration=timedelta(hours=3),
                priority=Priority.HIGH,
                description="Set up venue decorations and arrangements"
            ),
            Activity(
                id="ceremony",
                name="Wedding Ceremony",
                activity_type=ActivityType.CEREMONY,
                duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Main wedding ceremony"
            ),
            Activity(
                id="reception",
                name="Reception",
                activity_type=ActivityType.ENTERTAINMENT,
                duration=timedelta(hours=4),
                priority=Priority.HIGH,
                description="Wedding reception and dinner"
            )
        ]
    elif event_type == EventType.CORPORATE:
        return [
            Activity(
                id="setup",
                name="Event Setup",
                activity_type=ActivityType.PREPARATION,
                duration=timedelta(hours=2),
                priority=Priority.HIGH,
                description="Set up presentation equipment and seating"
            ),
            Activity(
                id="presentation",
                name="Main Presentation",
                activity_type=ActivityType.CEREMONY,
                duration=timedelta(hours=2),
                priority=Priority.HIGH,
                description="Main corporate presentation"
            ),
            Activity(
                id="networking",
                name="Networking Session",
                activity_type=ActivityType.ENTERTAINMENT,
                duration=timedelta(hours=2),
                priority=Priority.MEDIUM,
                description="Networking and refreshments"
            )
        ]
    else:  # Default activities
        return [
            Activity(
                id="setup",
                name="Event Setup",
                activity_type=ActivityType.PREPARATION,
                duration=timedelta(hours=2),
                priority=Priority.HIGH,
                description="General event setup"
            ),
            Activity(
                id="main_event",
                name="Main Event",
                activity_type=ActivityType.CEREMONY,
                duration=timedelta(hours=3),
                priority=Priority.HIGH,
                description="Main event activities"
            ),
            Activity(
                id="cleanup",
                name="Cleanup",
                activity_type=ActivityType.PREPARATION,
                duration=timedelta(hours=1),
                priority=Priority.LOW,
                description="Event cleanup"
            )
        ]


def _schedule_activities_for_day(activities: List[Activity], day_number: int) -> List[TimedActivity]:
    """Schedule activities for a specific day"""
    timed_activities = []
    current_time = datetime.now().replace(hour=9, minute=0, second=0, microsecond=0)  # Start at 9 AM
    
    for activity in activities:
        end_time = current_time + activity.duration
        
        timed_activity = TimedActivity(
            activity=activity,
            start_time=current_time,
            end_time=end_time,
            buffer_before=timedelta(minutes=15),
            buffer_after=timedelta(minutes=15),
            contingency_plans=[f"Backup plan for {activity.name}"]
        )
        
        timed_activities.append(timed_activity)
        current_time = end_time + timedelta(minutes=30)  # 30-minute buffer between activities
    
    return timed_activities


class SystemMonitor:
    """Monitor system performance and health"""
    
    def __init__(self):
        self.metrics = {
            'timeline_generation_success_rate': 0.0,
            'budget_allocation_success_rate': 0.0,
            'ai_service_availability': 0.0,
            'average_response_time': 0.0,
            'fallback_usage_rate': 0.0
        }
        self.operation_counts = {
            'timeline_generation_attempts': 0,
            'timeline_generation_successes': 0,
            'budget_allocation_attempts': 0,
            'budget_allocation_successes': 0,
            'ai_service_calls': 0,
            'ai_service_successes': 0,
            'fallback_uses': 0,
            'total_operations': 0
        }
        self.response_times = []
    
    def record_operation(self, operation_type: str, success: bool, response_time: float = None, used_fallback: bool = False):
        """Record an operation for monitoring"""
        self.operation_counts['total_operations'] += 1
        
        if operation_type == 'timeline_generation':
            self.operation_counts['timeline_generation_attempts'] += 1
            if success:
                self.operation_counts['timeline_generation_successes'] += 1
        elif operation_type == 'budget_allocation':
            self.operation_counts['budget_allocation_attempts'] += 1
            if success:
                self.operation_counts['budget_allocation_successes'] += 1
        elif operation_type == 'ai_service':
            self.operation_counts['ai_service_calls'] += 1
            if success:
                self.operation_counts['ai_service_successes'] += 1
        
        if used_fallback:
            self.operation_counts['fallback_uses'] += 1
        
        if response_time is not None:
            self.response_times.append(response_time)
            # Keep only last 100 response times
            if len(self.response_times) > 100:
                self.response_times = self.response_times[-100:]
        
        self._update_metrics()
    
    def _update_metrics(self):
        """Update calculated metrics"""
        counts = self.operation_counts
        
        if counts['timeline_generation_attempts'] > 0:
            self.metrics['timeline_generation_success_rate'] = (
                counts['timeline_generation_successes'] / counts['timeline_generation_attempts']
            )
        
        if counts['budget_allocation_attempts'] > 0:
            self.metrics['budget_allocation_success_rate'] = (
                counts['budget_allocation_successes'] / counts['budget_allocation_attempts']
            )
        
        if counts['ai_service_calls'] > 0:
            self.metrics['ai_service_availability'] = (
                counts['ai_service_successes'] / counts['ai_service_calls']
            )
        
        if counts['total_operations'] > 0:
            self.metrics['fallback_usage_rate'] = (
                counts['fallback_uses'] / counts['total_operations']
            )
        
        if self.response_times:
            self.metrics['average_response_time'] = sum(self.response_times) / len(self.response_times)
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get system health status"""
        status = "healthy"
        issues = []
        
        if self.metrics['timeline_generation_success_rate'] < 0.8:
            status = "degraded"
            issues.append("Low timeline generation success rate")
        
        if self.metrics['budget_allocation_success_rate'] < 0.8:
            status = "degraded"
            issues.append("Low budget allocation success rate")
        
        if self.metrics['ai_service_availability'] < 0.7:
            status = "degraded"
            issues.append("AI service availability issues")
        
        if self.metrics['fallback_usage_rate'] > 0.5:
            status = "degraded"
            issues.append("High fallback usage rate")
        
        if self.metrics['average_response_time'] > 10.0:  # 10 seconds
            status = "degraded"
            issues.append("High response times")
        
        return {
            'status': status,
            'issues': issues,
            'metrics': self.metrics,
            'operation_counts': self.operation_counts
        }
    
    def log_health_status(self):
        """Log current health status"""
        health = self.get_health_status()
        logger.info(f"System health: {health['status']}")
        
        if health['issues']:
            logger.warning(f"Health issues: {', '.join(health['issues'])}")
        
        logger.info(f"Metrics: {health['metrics']}")


# Global system monitor instance
system_monitor = SystemMonitor()


def monitored_operation(operation_type: str):
    """Decorator to monitor operations"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            success = False
            used_fallback = False
            
            try:
                result = func(*args, **kwargs)
                success = True
                return result
            except Exception as e:
                # Check if this was a fallback operation
                if 'fallback' in func.__name__.lower():
                    used_fallback = True
                raise
            finally:
                response_time = time.time() - start_time
                system_monitor.record_operation(operation_type, success, response_time, used_fallback)
        
        return wrapper
    return decorator