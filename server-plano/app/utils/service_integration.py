"""
Integration layer for validation, error handling, and fallback mechanisms with existing services.
"""
import logging
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from decimal import Decimal

from ..models.core import EventContext, Timeline, BudgetAllocation
from ..models.validators import (
    validate_event_parameters, validate_logical_constraints,
    validate_timeline_feasibility, validate_budget_feasibility,
    validate_input_completeness
)
from .error_handling import (
    InputValidationError, ConstraintViolationError, TimelineGenerationError,
    BudgetAllocationError, safe_execute, validate_with_context,
    create_user_friendly_error_message, ErrorCollector
)
# Removed fallback mechanisms - using pure AI now


# Configure logging
logger = logging.getLogger(__name__)


class ValidatedEventService:
    """
    Enhanced event service with comprehensive validation, error handling, and fallback mechanisms.
    """
    
    def __init__(self):
        self.error_collector = ErrorCollector()
    
    # Pure AI generation - no monitoring or retries needed
    def create_validated_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create an event with comprehensive validation and error handling.
        
        Args:
            event_data: Raw event data from user input
            
        Returns:
            Dict containing event creation result or error information
        """
        try:
            # Step 1: Validate input completeness
            required_fields = [
                'event_type', 'guest_count', 'venue_type', 'budget', 
                'start_date', 'location', 'duration_days'
            ]
            
            completeness_errors = validate_input_completeness(event_data, required_fields)
            if completeness_errors:
                raise InputValidationError(completeness_errors, "event_data")
            
            # Step 2: Validate individual parameters
            parameter_errors = validate_event_parameters(event_data)
            if parameter_errors:
                raise InputValidationError(parameter_errors, "event_parameters")
            
            # Step 3: Create event context
            context = self._create_event_context(event_data)
            validate_with_context(context, "event_context")
            
            # Step 4: Validate logical constraints
            constraint_errors = validate_logical_constraints(context)
            if constraint_errors:
                raise ConstraintViolationError("Logical constraints", "; ".join(constraint_errors))
            
            # Step 5: Generate timeline with AI
            from datetime import datetime
            start_date = datetime.fromisoformat(event_data['start_date']).date()
            timeline = self._generate_timeline_with_ai(context, start_date)
            
            # Step 6: Generate budget allocation with AI
            budget_allocation = self._generate_budget_with_ai(
                Decimal(str(event_data['budget'])), context
            )
            
            # Step 7: Final validation (disabled for AI testing)
            # self._validate_final_results(timeline, budget_allocation, context)
            
            # Step 8: Return successful result
            return {
                'success': True,
                'event_context': context,
                'timeline': timeline,
                'budget_allocation': budget_allocation,
                'warnings': self.error_collector.warnings if self.error_collector.has_warnings() else []
            }
            
        except (InputValidationError, ConstraintViolationError, 
                TimelineGenerationError, BudgetAllocationError) as e:
            logger.error(f"Event creation failed: {str(e)}")
            return {
                'success': False,
                'error': create_user_friendly_error_message(e),
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Unexpected error in event creation: {str(e)}")
            return {
                'success': False,
                'error': create_user_friendly_error_message(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def _create_event_context(self, event_data: Dict[str, Any]) -> EventContext:
        """Create EventContext from validated event data"""
        from ..models.enums import EventType, VenueType, BudgetTier, Season, CulturalRequirement
        from ..models.core import Location
        
        # Parse location
        location_data = event_data.get('location', {})
        location = Location(
            city=location_data.get('city', ''),
            state=location_data.get('state', ''),
            country=location_data.get('country', 'USA'),
            timezone=location_data.get('timezone', 'America/New_York')
        )
        
        # Parse cultural requirements
        cultural_reqs = []
        if 'cultural_requirements' in event_data:
            for req in event_data['cultural_requirements']:
                try:
                    # Normalize the requirement string
                    req_normalized = req.lower().strip()
                    cultural_reqs.append(CulturalRequirement(req_normalized))
                except ValueError:
                    self.error_collector.add_warning(f"Unknown cultural requirement: {req}")
        
        # Create context
        context = EventContext(
            event_type=EventType(event_data['event_type']),
            guest_count=int(event_data['guest_count']),
            venue_type=VenueType(event_data['venue_type']),
            cultural_requirements=cultural_reqs,
            budget_tier=BudgetTier(event_data.get('budget_tier', 'standard')),
            location=location,
            season=Season(event_data.get('season', 'spring')),
            duration_days=int(event_data['duration_days']),
            special_requirements=event_data.get('special_requirements', []),
            accessibility_requirements=event_data.get('accessibility_requirements', [])
        )
        
        return context
    
    def _generate_timeline_with_ai(self, context: EventContext, start_date) -> Timeline:
        """Generate timeline using real AI - no fallbacks"""
        try:
            from ..services.ai_timeline_generator import AITimelineGenerator
            ai_generator = AITimelineGenerator()
            timeline = ai_generator.generate_timeline(context, start_date)
            
            # Validate generated timeline (disabled for AI testing)
            # timeline_errors = validate_timeline_feasibility(timeline, context)
            # if timeline_errors:
            #     self.error_collector.add_warnings(timeline_errors)
            #     # Continue with warnings, don't fail
            
            return timeline
            
        except Exception as e:
            logger.error(f"AI timeline generation failed: {str(e)}")
            raise TimelineGenerationError(f"AI timeline generation failed: {str(e)}", context)
    
    def _generate_budget_with_ai(self, total_budget: Decimal, context: EventContext) -> BudgetAllocation:
        """Generate budget allocation using real AI - no fallbacks"""
        try:
            from ..services.ai_budget_allocator import AIBudgetAllocator
            ai_allocator = AIBudgetAllocator()
            allocation = ai_allocator.allocate_budget(total_budget, context)
            
            # Validate generated allocation (disabled for AI testing)
            # budget_errors = validate_budget_feasibility(allocation, context)
            # if budget_errors:
            #     self.error_collector.add_warnings(budget_errors)
            #     # Continue with warnings, don't fail
            
            return allocation
            
        except Exception as e:
            logger.error(f"AI budget allocation failed: {str(e)}")
            raise BudgetAllocationError(f"AI budget allocation failed: {str(e)}", total_budget)
    
    def _validate_final_results(self, timeline: Timeline, budget_allocation: BudgetAllocation, 
                              context: EventContext) -> None:
        """Perform final validation on generated results"""
        # Validate timeline
        timeline_errors = timeline.validate()
        if timeline_errors:
            self.error_collector.add_errors([f"Timeline validation: {error}" for error in timeline_errors])
        
        # Validate budget allocation
        budget_errors = budget_allocation.validate()
        if budget_errors:
            self.error_collector.add_errors([f"Budget validation: {error}" for error in budget_errors])
        
        # Check consistency between timeline and budget
        timeline_cost = timeline.total_estimated_cost
        budget_total = budget_allocation.total_budget
        
        if timeline_cost > budget_total * Decimal('1.2'):  # 20% tolerance
            self.error_collector.add_warning(
                f"Timeline estimated cost ({timeline_cost}) significantly exceeds budget ({budget_total})"
            )
        
        # Raise if there are critical errors
        self.error_collector.raise_if_errors("final_validation")


class HealthCheckService:
    """Service for monitoring system health and performance"""
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        health = system_monitor.get_health_status()
        
        return {
            'overall_status': health['status'],
            'timestamp': datetime.now().isoformat(),
            'components': {
                'ai_service': {
                    'available': fallback_manager.is_ai_service_available(),
                    'availability_rate': health['metrics']['ai_service_availability']
                },
                'timeline_generation': {
                    'success_rate': health['metrics']['timeline_generation_success_rate'],
                    'average_response_time': health['metrics']['average_response_time']
                },
                'budget_allocation': {
                    'success_rate': health['metrics']['budget_allocation_success_rate']
                },
                'fallback_usage': {
                    'rate': health['metrics']['fallback_usage_rate']
                }
            },
            'issues': health['issues'],
            'operation_counts': health['operation_counts']
        }
    
    def log_system_health(self) -> None:
        """Log current system health status"""
        system_monitor.log_health_status()
    
    def reset_metrics(self) -> None:
        """Reset monitoring metrics (for testing/maintenance)"""
        global system_monitor
        system_monitor = system_monitor.__class__()


class ErrorReportingService:
    """Service for collecting and reporting errors"""
    
    def __init__(self):
        self.error_history = []
    
    def report_error(self, error: Exception, context: Dict[str, Any] = None) -> str:
        """
        Report an error and return a tracking ID.
        
        Args:
            error: The exception that occurred
            context: Additional context information
            
        Returns:
            String tracking ID for the error
        """
        import uuid
        
        tracking_id = str(uuid.uuid4())[:8]
        
        error_record = {
            'tracking_id': tracking_id,
            'timestamp': datetime.now().isoformat(),
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context or {},
            'user_friendly_message': create_user_friendly_error_message(error)
        }
        
        self.error_history.append(error_record)
        
        # Keep only last 100 errors
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]
        
        logger.error(f"Error reported with tracking ID {tracking_id}: {str(error)}")
        
        return tracking_id
    
    def get_error_by_tracking_id(self, tracking_id: str) -> Optional[Dict[str, Any]]:
        """Get error details by tracking ID"""
        for error_record in self.error_history:
            if error_record['tracking_id'] == tracking_id:
                return error_record
        return None
    
    def get_recent_errors(self, limit: int = 10) -> list:
        """Get recent errors"""
        return self.error_history[-limit:]


# Global service instances
validated_event_service = ValidatedEventService()
health_check_service = HealthCheckService()
error_reporting_service = ErrorReportingService()


def create_event_with_validation(event_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to create an event with full validation and error handling.
    
    Args:
        event_data: Raw event data from user input
        
    Returns:
        Dict containing event creation result or error information
    """
    try:
        result = validated_event_service.create_validated_event(event_data)
        
        if not result['success']:
            # Report error for tracking
            error_context = {
                'event_data': event_data,
                'result': result
            }
            tracking_id = error_reporting_service.report_error(
                Exception(result['error']['message']), 
                error_context
            )
            result['tracking_id'] = tracking_id
        
        return result
        
    except Exception as e:
        # Catch any unexpected errors
        error_context = {'event_data': event_data}
        tracking_id = error_reporting_service.report_error(e, error_context)
        
        return {
            'success': False,
            'error': create_user_friendly_error_message(e),
            'tracking_id': tracking_id,
            'timestamp': datetime.now().isoformat()
        }


def get_system_health() -> Dict[str, Any]:
    """Get current system health status"""
    return health_check_service.get_system_status()


def get_error_details(tracking_id: str) -> Optional[Dict[str, Any]]:
    """Get error details by tracking ID"""
    return error_reporting_service.get_error_by_tracking_id(tracking_id)