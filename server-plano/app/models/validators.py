"""
Validation utilities for data models.
"""
from typing import List, Any, Dict
from datetime import datetime, date, timedelta
from decimal import Decimal, InvalidOperation

from .core import EventContext, Timeline, BudgetAllocation
from .enums import VenueType, BudgetTier, Season, EventType, CulturalRequirement, BudgetCategory, AccessibilityRequirement


class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")


def validate_date_range(start_date: date, end_date: date) -> List[str]:
    """Validate date range for events"""
    errors = []
    
    if start_date > end_date:
        errors.append("Start date must be before or equal to end date")
    
    # Check if dates are not too far in the past
    today = date.today()
    if start_date < today - timedelta(days=365):
        errors.append("Start date cannot be more than 1 year in the past")
    
    # Check if dates are not too far in the future
    if start_date > today + timedelta(days=365 * 2):
        errors.append("Start date cannot be more than 2 years in the future")
    
    # Check maximum event duration
    duration = (end_date - start_date).days + 1
    if duration > 30:
        errors.append("Event duration cannot exceed 30 days")
    
    return errors


def validate_budget_amount(budget: Decimal, guest_count: int) -> List[str]:
    """Validate budget amount reasonableness"""
    errors = []
    
    if budget <= 0:
        errors.append("Budget must be positive")
    
    # Check minimum per-person budget (very basic threshold)
    min_per_person = Decimal('100')  # Minimum $100 per person
    if budget / guest_count < min_per_person:
        errors.append(f"Budget appears too low (less than ${min_per_person} per person)")
    
    # Check maximum reasonable budget
    max_per_person = Decimal('50000')  # Maximum $50,000 per person
    if budget / guest_count > max_per_person:
        errors.append(f"Budget appears unreasonably high (more than ${max_per_person} per person)")
    
    return errors


def validate_guest_count_venue_compatibility(guest_count: int, venue_type: VenueType) -> List[str]:
    """Validate guest count is reasonable for venue type"""
    errors = []
    
    venue_capacity_limits = {
        VenueType.HOME: 50,
        VenueType.RESTAURANT: 200,
        VenueType.COMMUNITY_CENTER: 300,
        VenueType.BANQUET_HALL: 1000,
        VenueType.HOTEL: 500,
        VenueType.OUTDOOR: 2000,
        VenueType.GARDEN: 300,
        VenueType.BEACH: 500,
        VenueType.TEMPLE: 200,
        VenueType.CHURCH: 300,
        VenueType.HYBRID: 1000,
        VenueType.INDOOR: 500
    }
    
    max_capacity = venue_capacity_limits.get(venue_type, 1000)
    if guest_count > max_capacity:
        errors.append(f"Guest count ({guest_count}) exceeds typical capacity for {venue_type.value} venues ({max_capacity})")
    
    return errors


def validate_cultural_event_compatibility(event_type: EventType, cultural_requirements: List[CulturalRequirement]) -> List[str]:
    """Validate cultural requirements are compatible with event type"""
    errors = []
    
    # Some basic compatibility checks
    if event_type == EventType.CORPORATE and CulturalRequirement.HINDU in cultural_requirements:
        # This is actually fine, just checking the validation structure works
        pass
    
    # Check for conflicting cultural requirements
    religious_requirements = [
        CulturalRequirement.HINDU, CulturalRequirement.MUSLIM, 
        CulturalRequirement.CHRISTIAN, CulturalRequirement.SIKH,
        CulturalRequirement.BUDDHIST, CulturalRequirement.JAIN,
        CulturalRequirement.JEWISH
    ]
    
    religious_count = sum(1 for req in cultural_requirements if req in religious_requirements)
    if religious_count > 1 and CulturalRequirement.MIXED not in cultural_requirements:
        errors.append("Multiple religious requirements specified without 'mixed' designation")
    
    return errors


def validate_seasonal_venue_compatibility(season: Season, venue_type: VenueType) -> List[str]:
    """Validate season and venue type compatibility"""
    errors = []
    
    if season == Season.MONSOON and venue_type in [VenueType.OUTDOOR, VenueType.GARDEN, VenueType.BEACH]:
        errors.append(f"Outdoor venues may not be suitable during {season.value} season")
    
    if season == Season.WINTER and venue_type == VenueType.BEACH:
        errors.append("Beach venues may not be comfortable during winter season")
    
    return errors


def validate_timeline_logical_sequence(timeline: Timeline) -> List[str]:
    """Validate timeline has logical activity sequence"""
    errors = []
    
    for day in timeline.days:
        activities = sorted(day.activities, key=lambda a: a.start_time)
        
        # Check for setup activities before main activities
        setup_found = False
        main_activities_started = False
        
        for timed_activity in activities:
            activity = timed_activity.activity
            
            if activity.activity_type.value in ['preparation', 'decoration']:
                setup_found = True
            elif activity.activity_type.value in ['ceremony', 'entertainment', 'catering']:
                main_activities_started = True
                if not setup_found:
                    errors.append(f"Day {day.day_number}: Main activities started without setup activities")
                    break
    
    return errors


def validate_budget_category_reasonableness(allocation: BudgetAllocation, event_type: EventType) -> List[str]:
    """Validate budget category allocations are reasonable for event type"""
    errors = []
    
    # Define reasonable percentage ranges for different event types
    wedding_ranges = {
        'venue': (15, 30),
        'catering': (30, 45),
        'decoration': (8, 20),
        'photography': (8, 15),
        'entertainment': (5, 15),
        'transportation': (2, 8),
        'contingency': (5, 15)
    }
    
    corporate_ranges = {
        'venue': (20, 40),
        'catering': (25, 40),
        'entertainment': (10, 25),
        'photography': (3, 10),
        'transportation': (5, 15),
        'contingency': (5, 15)
    }
    
    ranges = wedding_ranges if event_type == EventType.WEDDING else corporate_ranges
    
    for category, allocation_data in allocation.categories.items():
        category_name = category.value
        if category_name in ranges:
            min_pct, max_pct = ranges[category_name]
            if allocation_data.percentage < min_pct or allocation_data.percentage > max_pct:
                errors.append(f"{category_name} allocation ({allocation_data.percentage}%) outside reasonable range ({min_pct}-{max_pct}%)")
    
    return errors


def validate_and_raise(obj: Any) -> None:
    """Validate an object and raise ValidationError if invalid"""
    if hasattr(obj, 'validate'):
        errors = obj.validate()
        if errors:
            raise ValidationError(errors)
    else:
        raise ValueError(f"Object {type(obj)} does not have a validate method")


def safe_decimal_conversion(value: Any) -> Decimal:
    """Safely convert value to Decimal"""
    try:
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace('$', '').replace(',', '').strip()
            return Decimal(cleaned)
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError([f"Cannot convert '{value}' to decimal"])


def validate_time_constraints(start_time: datetime, end_time: datetime, min_duration: timedelta = None) -> List[str]:
    """Validate time constraints for activities"""
    errors = []
    
    if start_time >= end_time:
        errors.append("Start time must be before end time")
    
    if min_duration and (end_time - start_time) < min_duration:
        errors.append(f"Duration must be at least {min_duration}")
    
    # Check for reasonable time bounds (not scheduling at 3 AM unless it's a special event)
    if start_time.hour < 6 or start_time.hour > 23:
        errors.append("Activities should typically be scheduled between 6 AM and 11 PM")
    
    return errors


def validate_event_parameters(event_params: Dict[str, Any]) -> List[str]:
    """Comprehensive validation of event input parameters"""
    errors = []
    
    # Required fields validation
    required_fields = ['event_type', 'guest_count', 'venue_type', 'budget', 'start_date', 'location']
    for field in required_fields:
        if field not in event_params or event_params[field] is None:
            errors.append(f"Required field '{field}' is missing")
    
    # Type validation
    if 'guest_count' in event_params:
        try:
            guest_count = int(event_params['guest_count'])
            if guest_count <= 0:
                errors.append("Guest count must be positive")
            elif guest_count > 50000:
                errors.append("Guest count exceeds maximum limit (50,000)")
        except (ValueError, TypeError):
            errors.append("Guest count must be a valid integer")
    
    # Budget validation
    if 'budget' in event_params:
        try:
            budget = safe_decimal_conversion(event_params['budget'])
            if budget <= 0:
                errors.append("Budget must be positive")
            elif budget > Decimal('10000000'):  # $10M limit
                errors.append("Budget exceeds maximum limit ($10,000,000)")
        except ValidationError as e:
            errors.extend(e.errors)
    
    # Date validation
    if 'start_date' in event_params and 'end_date' in event_params:
        try:
            start_date = event_params['start_date']
            end_date = event_params.get('end_date', start_date)
            
            if isinstance(start_date, str):
                start_date = datetime.fromisoformat(start_date).date()
            if isinstance(end_date, str):
                end_date = datetime.fromisoformat(end_date).date()
                
            errors.extend(validate_date_range(start_date, end_date))
        except (ValueError, TypeError):
            errors.append("Invalid date format")
    
    # Enum validation
    enum_fields = {
        'event_type': EventType,
        'venue_type': VenueType,
        'budget_tier': BudgetTier,
        'season': Season
    }
    
    for field, enum_class in enum_fields.items():
        if field in event_params and event_params[field] is not None:
            try:
                if isinstance(event_params[field], str):
                    enum_class(event_params[field])
            except ValueError:
                valid_values = [e.value for e in enum_class]
                errors.append(f"Invalid {field}: must be one of {valid_values}")
    
    return errors


def validate_logical_constraints(context: EventContext) -> List[str]:
    """Validate logical constraints between event parameters"""
    errors = []
    
    # Guest count vs venue capacity
    errors.extend(validate_guest_count_venue_compatibility(context.guest_count, context.venue_type))
    
    # Cultural requirements vs event type
    errors.extend(validate_cultural_event_compatibility(context.event_type, context.cultural_requirements))
    
    # Season vs venue compatibility
    errors.extend(validate_seasonal_venue_compatibility(context.season, context.venue_type))
    
    # Budget reasonableness
    if hasattr(context, 'total_budget'):
        errors.extend(validate_budget_amount(context.total_budget, context.guest_count))
    
    # Duration vs event type reasonableness (more flexible limits)
    if context.event_type == EventType.WEDDING and context.duration_days > 10:
        errors.append("Wedding events typically don't exceed 10 days")
    elif context.event_type == EventType.CORPORATE and context.duration_days > 7:
        errors.append("Corporate events typically don't exceed 7 days")
    elif context.event_type == EventType.BIRTHDAY and context.duration_days > 3:
        errors.append("Birthday events typically don't exceed 3 days")
    
    # Accessibility requirements validation
    if context.accessibility_requirements:
        if context.venue_type in [VenueType.OUTDOOR, VenueType.BEACH] and any(
            req in context.accessibility_requirements 
            for req in [AccessibilityRequirement.WHEELCHAIR_ACCESS, AccessibilityRequirement.ELEVATOR_ACCESS]
        ):
            errors.append("Outdoor venues may not support all accessibility requirements")
    
    return errors


def validate_timeline_feasibility(timeline: Timeline, context: EventContext) -> List[str]:
    """Validate timeline feasibility and logical constraints"""
    errors = []
    
    # Basic timeline validation
    errors.extend(validate_timeline_logical_sequence(timeline))
    
    # Check total duration matches context
    expected_days = context.duration_days
    actual_days = len(timeline.days)
    if actual_days != expected_days:
        errors.append(f"Timeline has {actual_days} days but context specifies {expected_days} days")
    
    # Validate activity scheduling density
    for day in timeline.days:
        total_activity_time = sum(
            (activity.end_time - activity.start_time).total_seconds() 
            for activity in day.activities
        )
        day_seconds = 24 * 60 * 60
        
        if total_activity_time > day_seconds * 0.8:  # More than 80% of day scheduled
            errors.append(f"Day {day.day_number} is over-scheduled (>80% of day)")
    
    # Check for reasonable gaps between activities
    for day in timeline.days:
        sorted_activities = sorted(day.activities, key=lambda a: a.start_time)
        for i in range(len(sorted_activities) - 1):
            current = sorted_activities[i]
            next_activity = sorted_activities[i + 1]
            gap = (next_activity.start_time - current.end_time).total_seconds() / 60  # minutes
            
            if gap < 0:
                errors.append(f"Day {day.day_number}: Activities overlap")
            elif gap > 240:  # More than 4 hours gap
                errors.append(f"Day {day.day_number}: Large gap ({gap:.0f} minutes) between activities")
    
    # Validate critical path
    if not timeline.critical_path:
        errors.append("Timeline missing critical path")
    
    return errors


def validate_budget_feasibility(allocation: BudgetAllocation, context: EventContext) -> List[str]:
    """Validate budget allocation feasibility"""
    errors = []
    
    # Basic budget validation
    errors.extend(validate_budget_category_reasonableness(allocation, context.event_type))
    
    # Check minimum viable allocations
    min_allocations = {
        BudgetCategory.VENUE: 0.10,  # At least 10%
        BudgetCategory.CATERING: 0.20,  # At least 20%
        BudgetCategory.CONTINGENCY: 0.05  # At least 5%
    }
    
    for category, min_percentage in min_allocations.items():
        if category in allocation.categories:
            actual_percentage = allocation.categories[category].percentage / 100
            if actual_percentage < min_percentage:
                errors.append(f"{category.value} allocation ({actual_percentage:.1%}) below minimum ({min_percentage:.1%})")
    
    # Check per-person cost reasonableness
    per_person = allocation.per_person_cost
    if context.event_type == EventType.WEDDING:
        if per_person < Decimal('200'):
            errors.append("Per-person cost seems low for wedding events")
        elif per_person > Decimal('2000'):
            errors.append("Per-person cost seems very high for wedding events")
    elif context.event_type == EventType.CORPORATE:
        if per_person < Decimal('100'):
            errors.append("Per-person cost seems low for corporate events")
        elif per_person > Decimal('1000'):
            errors.append("Per-person cost seems very high for corporate events")
    
    return errors


def validate_input_completeness(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate that all required input fields are present and non-empty"""
    errors = []
    
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
        elif data[field] is None:
            errors.append(f"Field '{field}' cannot be null")
        elif isinstance(data[field], str) and not data[field].strip():
            errors.append(f"Field '{field}' cannot be empty")
        elif isinstance(data[field], (list, dict)) and len(data[field]) == 0:
            errors.append(f"Field '{field}' cannot be empty")
    
    return errors