"""
Core data models for the intelligent timeline and budget system.
"""
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from typing import List, Dict, Optional, Any
from decimal import Decimal

from .enums import (
    VenueType, BudgetTier, Season, EventType, CulturalRequirement,
    ActivityType, BudgetCategory, Priority, WeatherCondition, AccessibilityRequirement
)


@dataclass
class Location:
    """Location information for events"""
    city: str
    state: str
    country: str
    timezone: str
    coordinates: Optional[tuple] = None
    
    def validate(self) -> List[str]:
        """Validate location data"""
        errors = []
        if not self.city or not self.city.strip():
            errors.append("City is required")
        if not self.state or not self.state.strip():
            errors.append("State is required")
        if not self.country or not self.country.strip():
            errors.append("Country is required")
        if not self.timezone or not self.timezone.strip():
            errors.append("Timezone is required")
        return errors


@dataclass
class EventContext:
    """Context information for event planning"""
    event_type: EventType
    guest_count: int
    venue_type: VenueType
    cultural_requirements: List[CulturalRequirement]
    budget_tier: BudgetTier
    location: Location
    season: Season
    duration_days: int
    special_requirements: List[str] = field(default_factory=list)
    accessibility_requirements: List[AccessibilityRequirement] = field(default_factory=list)
    complexity_score: float = 0.0
    weather_considerations: List[WeatherCondition] = field(default_factory=list)
    
    def validate(self) -> List[str]:
        """Validate event context data"""
        errors = []
        
        if self.guest_count <= 0:
            errors.append("Guest count must be positive")
        if self.guest_count > 10000:
            errors.append("Guest count exceeds maximum limit (10,000)")
            
        if self.duration_days <= 0:
            errors.append("Duration must be at least 1 day")
        if self.duration_days > 30:
            errors.append("Duration exceeds maximum limit (30 days)")
            
        if self.complexity_score < 0 or self.complexity_score > 10:
            errors.append("Complexity score must be between 0 and 10")
            
        # Validate location
        errors.extend(self.location.validate())
        
        return errors


@dataclass
class Dependency:
    """Dependency between timeline activities"""
    predecessor_id: str
    successor_id: str
    dependency_type: str  # "finish_to_start", "start_to_start", etc.
    lag_time: timedelta = timedelta(0)
    
    def validate(self) -> List[str]:
        """Validate dependency data"""
        errors = []
        if not self.predecessor_id:
            errors.append("Predecessor ID is required")
        if not self.successor_id:
            errors.append("Successor ID is required")
        if self.predecessor_id == self.successor_id:
            errors.append("Activity cannot depend on itself")
        if self.dependency_type not in ["finish_to_start", "start_to_start", "finish_to_finish", "start_to_finish"]:
            errors.append("Invalid dependency type")
        return errors


@dataclass
class Activity:
    """Individual activity in timeline"""
    id: str
    name: str
    activity_type: ActivityType
    duration: timedelta
    priority: Priority
    description: str = ""
    required_vendors: List[str] = field(default_factory=list)
    estimated_cost: Decimal = Decimal('0.00')
    cultural_significance: str = ""
    setup_time: timedelta = timedelta(0)
    cleanup_time: timedelta = timedelta(0)
    
    def validate(self) -> List[str]:
        """Validate activity data"""
        errors = []
        if not self.id or not self.id.strip():
            errors.append("Activity ID is required")
        if not self.name or not self.name.strip():
            errors.append("Activity name is required")
        if self.duration <= timedelta(0):
            errors.append("Duration must be positive")
        if self.estimated_cost < 0:
            errors.append("Estimated cost cannot be negative")
        return errors


@dataclass
class TimedActivity:
    """Activity with specific timing"""
    activity: Activity
    start_time: datetime
    end_time: datetime
    buffer_before: timedelta = timedelta(0)
    buffer_after: timedelta = timedelta(0)
    contingency_plans: List[str] = field(default_factory=list)
    
    def validate(self) -> List[str]:
        """Validate timed activity data"""
        errors = []
        errors.extend(self.activity.validate())
        
        if self.start_time >= self.end_time:
            errors.append("Start time must be before end time")
        
        expected_duration = self.activity.duration + self.activity.setup_time + self.activity.cleanup_time
        actual_duration = self.end_time - self.start_time
        
        if actual_duration < expected_duration:
            errors.append(f"Allocated time ({actual_duration}) is less than required time ({expected_duration})")
            
        return errors


@dataclass
class TimelineDay:
    """Single day in timeline"""
    day_number: int
    date: date
    activities: List[TimedActivity]
    estimated_cost: Decimal
    notes: List[str] = field(default_factory=list)
    contingency_plans: List[str] = field(default_factory=list)
    weather_backup_plan: str = ""
    
    def validate(self) -> List[str]:
        """Validate timeline day data"""
        errors = []
        
        if self.day_number <= 0:
            errors.append("Day number must be positive")
        if self.estimated_cost < 0:
            errors.append("Estimated cost cannot be negative")
        
        # Validate all activities
        for activity in self.activities:
            errors.extend(activity.validate())
        
        # Check for overlapping activities
        sorted_activities = sorted(self.activities, key=lambda a: a.start_time)
        for i in range(len(sorted_activities) - 1):
            current = sorted_activities[i]
            next_activity = sorted_activities[i + 1]
            if current.end_time > next_activity.start_time:
                errors.append(f"Activities '{current.activity.name}' and '{next_activity.activity.name}' overlap")
        
        return errors


@dataclass
class Timeline:
    """Complete timeline for event"""
    days: List[TimelineDay]
    total_duration: timedelta
    critical_path: List[Activity]
    buffer_time: timedelta
    dependencies: List[Dependency]
    total_estimated_cost: Decimal = Decimal('0.00')
    
    def validate(self) -> List[str]:
        """Validate complete timeline"""
        errors = []
        
        if not self.days:
            errors.append("Timeline must have at least one day")
        
        if self.total_duration <= timedelta(0):
            errors.append("Total duration must be positive")
        
        # Validate all days
        for day in self.days:
            errors.extend(day.validate())
        
        # Validate dependencies
        activity_ids = set()
        for day in self.days:
            for timed_activity in day.activities:
                activity_ids.add(timed_activity.activity.id)
        
        for dependency in self.dependencies:
            errors.extend(dependency.validate())
            if dependency.predecessor_id not in activity_ids:
                errors.append(f"Dependency references unknown predecessor: {dependency.predecessor_id}")
            if dependency.successor_id not in activity_ids:
                errors.append(f"Dependency references unknown successor: {dependency.successor_id}")
        
        # Check day sequence
        sorted_days = sorted(self.days, key=lambda d: d.day_number)
        for i, day in enumerate(sorted_days):
            if day.day_number != i + 1:
                errors.append(f"Day numbers must be sequential starting from 1")
                break
        
        return errors


@dataclass
class Alternative:
    """Alternative option for budget or timeline"""
    name: str
    description: str
    cost_impact: Decimal
    time_impact: timedelta = timedelta(0)
    trade_offs: List[str] = field(default_factory=list)
    
    def validate(self) -> List[str]:
        """Validate alternative data"""
        errors = []
        if not self.name or not self.name.strip():
            errors.append("Alternative name is required")
        if not self.description or not self.description.strip():
            errors.append("Alternative description is required")
        return errors


@dataclass
class CategoryAllocation:
    """Budget allocation for a specific category"""
    category: BudgetCategory
    amount: Decimal
    percentage: float
    justification: str
    alternatives: List[Alternative] = field(default_factory=list)
    vendor_suggestions: List[str] = field(default_factory=list)
    priority: Priority = Priority.MEDIUM
    
    def validate(self) -> List[str]:
        """Validate category allocation data"""
        errors = []
        
        if self.amount < 0:
            errors.append("Amount cannot be negative")
        if self.percentage < 0 or self.percentage > 100:
            errors.append("Percentage must be between 0 and 100")
        if not self.justification or not self.justification.strip():
            errors.append("Justification is required")
        
        # Validate alternatives
        for alternative in self.alternatives:
            errors.extend(alternative.validate())
        
        return errors


@dataclass
class BudgetAllocation:
    """Complete budget allocation for event"""
    total_budget: Decimal
    categories: Dict[BudgetCategory, CategoryAllocation]
    per_person_cost: Decimal
    contingency_percentage: float
    regional_adjustments: Dict[str, float] = field(default_factory=dict)
    seasonal_adjustments: Dict[Season, float] = field(default_factory=dict)
    
    def validate(self) -> List[str]:
        """Validate budget allocation"""
        errors = []
        
        if self.total_budget <= 0:
            errors.append("Total budget must be positive")
        if self.per_person_cost < 0:
            errors.append("Per person cost cannot be negative")
        if self.contingency_percentage < 0 or self.contingency_percentage > 50:
            errors.append("Contingency percentage must be between 0 and 50")
        
        # Validate all category allocations
        total_allocated = Decimal('0.00')
        total_percentage = 0.0
        
        for category, allocation in self.categories.items():
            errors.extend(allocation.validate())
            total_allocated += allocation.amount
            total_percentage += float(allocation.percentage)
        
        # Check if total allocation matches budget (within 1% tolerance)
        if abs(total_allocated - self.total_budget) > self.total_budget * Decimal('0.01'):
            errors.append(f"Total allocated ({total_allocated}) doesn't match total budget ({self.total_budget})")
        
        # Check if percentages add up to approximately 100%
        if abs(float(total_percentage) - 100.0) > 3.0:  # Allow 3% tolerance for rounding
            errors.append(f"Category percentages ({total_percentage}%) don't add up to 100%")
        
        return errors


@dataclass
class CriticalFactor:
    """Critical factor affecting event planning"""
    name: str
    impact_level: Priority
    description: str
    mitigation_strategies: List[str] = field(default_factory=list)
    
    def validate(self) -> List[str]:
        """Validate critical factor data"""
        errors = []
        if not self.name or not self.name.strip():
            errors.append("Critical factor name is required")
        if not self.description or not self.description.strip():
            errors.append("Critical factor description is required")
        return errors


@dataclass
class EventFeedback:
    """Feedback data for learning system"""
    event_id: str
    timeline_rating: int  # 1-5 scale
    budget_accuracy: int  # 1-5 scale
    overall_satisfaction: int  # 1-5 scale
    what_worked_well: List[str] = field(default_factory=list)
    what_could_improve: List[str] = field(default_factory=list)
    actual_costs: Dict[BudgetCategory, Decimal] = field(default_factory=dict)
    timeline_deviations: List[str] = field(default_factory=list)
    
    def validate(self) -> List[str]:
        """Validate feedback data"""
        errors = []
        
        if not self.event_id or not self.event_id.strip():
            errors.append("Event ID is required")
        
        for rating_name, rating_value in [
            ("timeline_rating", self.timeline_rating),
            ("budget_accuracy", self.budget_accuracy),
            ("overall_satisfaction", self.overall_satisfaction)
        ]:
            if rating_value < 1 or rating_value > 5:
                errors.append(f"{rating_name} must be between 1 and 5")
        
        # Validate actual costs
        for category, cost in self.actual_costs.items():
            if cost < 0:
                errors.append(f"Actual cost for {category.value} cannot be negative")
        
        return errors