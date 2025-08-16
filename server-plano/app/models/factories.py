"""
Factory methods for creating data model instances with sensible defaults.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Dict

from .core import (
    Location, EventContext, Activity, TimedActivity, TimelineDay, Timeline,
    CategoryAllocation, BudgetAllocation, CriticalFactor
)
from .enums import (
    VenueType, BudgetTier, Season, EventType, CulturalRequirement,
    ActivityType, BudgetCategory, Priority
)


class LocationFactory:
    """Factory for creating Location instances"""
    
    @staticmethod
    def create_indian_location(city: str, state: str) -> Location:
        """Create location for Indian cities"""
        return Location(
            city=city,
            state=state,
            country="India",
            timezone="Asia/Kolkata"
        )
    
    @staticmethod
    def create_us_location(city: str, state: str, timezone: str = "America/New_York") -> Location:
        """Create location for US cities"""
        return Location(
            city=city,
            state=state,
            country="United States",
            timezone=timezone
        )


class EventContextFactory:
    """Factory for creating EventContext instances"""
    
    @staticmethod
    def create_wedding_context(
        guest_count: int,
        venue_type: VenueType = VenueType.BANQUET_HALL,
        cultural_requirements: List[CulturalRequirement] = None,
        budget_tier: BudgetTier = BudgetTier.STANDARD,
        location: Location = None,
        season: Season = Season.WINTER,
        duration_days: int = 3
    ) -> EventContext:
        """Create context for wedding events"""
        if cultural_requirements is None:
            cultural_requirements = [CulturalRequirement.HINDU]
        
        if location is None:
            location = LocationFactory.create_indian_location("Mumbai", "Maharashtra")
        
        return EventContext(
            event_type=EventType.WEDDING,
            guest_count=guest_count,
            venue_type=venue_type,
            cultural_requirements=cultural_requirements,
            budget_tier=budget_tier,
            location=location,
            season=season,
            duration_days=duration_days,
            complexity_score=0.0  # Will be calculated later
        )
    
    @staticmethod
    def create_birthday_context(
        guest_count: int,
        venue_type: VenueType = VenueType.HOME,
        budget_tier: BudgetTier = BudgetTier.STANDARD,
        location: Location = None
    ) -> EventContext:
        """Create context for birthday events"""
        if location is None:
            location = LocationFactory.create_indian_location("Mumbai", "Maharashtra")
        
        return EventContext(
            event_type=EventType.BIRTHDAY,
            guest_count=guest_count,
            venue_type=venue_type,
            cultural_requirements=[CulturalRequirement.SECULAR],
            budget_tier=budget_tier,
            location=location,
            season=Season.WINTER,  # Default, should be calculated from date
            duration_days=1,
            complexity_score=0.0
        )
    
    @staticmethod
    def create_corporate_context(
        guest_count: int,
        venue_type: VenueType = VenueType.HOTEL,
        budget_tier: BudgetTier = BudgetTier.PREMIUM,
        location: Location = None,
        duration_days: int = 1
    ) -> EventContext:
        """Create context for corporate events"""
        if location is None:
            location = LocationFactory.create_indian_location("Mumbai", "Maharashtra")
        
        return EventContext(
            event_type=EventType.CORPORATE,
            guest_count=guest_count,
            venue_type=venue_type,
            cultural_requirements=[CulturalRequirement.SECULAR],
            budget_tier=budget_tier,
            location=location,
            season=Season.WINTER,
            duration_days=duration_days,
            complexity_score=0.0
        )


class ActivityFactory:
    """Factory for creating Activity instances"""
    
    @staticmethod
    def create_ceremony_activity(
        name: str,
        duration_hours: float = 2.0,
        estimated_cost: Decimal = Decimal('15000'),
        cultural_significance: str = ""
    ) -> Activity:
        """Create ceremony activity"""
        return Activity(
            id=f"ceremony_{name.lower().replace(' ', '_')}",
            name=name,
            activity_type=ActivityType.CEREMONY,
            duration=timedelta(hours=duration_hours),
            priority=Priority.CRITICAL,
            description=f"{name} ceremony",
            estimated_cost=estimated_cost,
            cultural_significance=cultural_significance
        )
    
    @staticmethod
    def create_preparation_activity(
        name: str,
        duration_hours: float = 1.0,
        estimated_cost: Decimal = Decimal('5000')
    ) -> Activity:
        """Create preparation activity"""
        return Activity(
            id=f"prep_{name.lower().replace(' ', '_')}",
            name=name,
            activity_type=ActivityType.PREPARATION,
            duration=timedelta(hours=duration_hours),
            priority=Priority.HIGH,
            description=f"{name} preparation",
            estimated_cost=estimated_cost
        )
    
    @staticmethod
    def create_catering_activity(
        name: str,
        duration_hours: float = 1.5,
        estimated_cost: Decimal = Decimal('25000')
    ) -> Activity:
        """Create catering activity"""
        return Activity(
            id=f"catering_{name.lower().replace(' ', '_')}",
            name=name,
            activity_type=ActivityType.CATERING,
            duration=timedelta(hours=duration_hours),
            priority=Priority.HIGH,
            description=f"{name} service",
            estimated_cost=estimated_cost
        )


class BudgetAllocationFactory:
    """Factory for creating BudgetAllocation instances"""
    
    @staticmethod
    def create_wedding_budget(
        total_budget: Decimal,
        guest_count: int,
        budget_tier: BudgetTier = BudgetTier.STANDARD
    ) -> BudgetAllocation:
        """Create budget allocation for wedding"""
        per_person_cost = total_budget / guest_count
        
        # Adjust percentages based on budget tier
        if budget_tier == BudgetTier.LOW:
            percentages = {
                BudgetCategory.VENUE: 20.0,
                BudgetCategory.CATERING: 40.0,
                BudgetCategory.DECORATION: 10.0,
                BudgetCategory.PHOTOGRAPHY: 8.0,
                BudgetCategory.ENTERTAINMENT: 5.0,
                BudgetCategory.TRANSPORTATION: 3.0,
                BudgetCategory.MISCELLANEOUS: 9.0,
                BudgetCategory.CONTINGENCY: 5.0
            }
        elif budget_tier == BudgetTier.PREMIUM:
            percentages = {
                BudgetCategory.VENUE: 25.0,
                BudgetCategory.CATERING: 35.0,
                BudgetCategory.DECORATION: 15.0,
                BudgetCategory.PHOTOGRAPHY: 12.0,
                BudgetCategory.ENTERTAINMENT: 8.0,
                BudgetCategory.TRANSPORTATION: 5.0,
                BudgetCategory.MISCELLANEOUS: 8.0,
                BudgetCategory.CONTINGENCY: 7.0
            }
        else:  # STANDARD
            percentages = {
                BudgetCategory.VENUE: 22.0,
                BudgetCategory.CATERING: 38.0,
                BudgetCategory.DECORATION: 12.0,
                BudgetCategory.PHOTOGRAPHY: 10.0,
                BudgetCategory.ENTERTAINMENT: 6.0,
                BudgetCategory.TRANSPORTATION: 4.0,
                BudgetCategory.MISCELLANEOUS: 2.0,
                BudgetCategory.CONTINGENCY: 6.0
            }
        
        categories = {}
        for category, percentage in percentages.items():
            amount = total_budget * Decimal(str(percentage / 100))
            categories[category] = CategoryAllocation(
                category=category,
                amount=amount,
                percentage=percentage,
                justification=f"{category.value.title()} allocation based on {budget_tier.value} tier"
            )
        
        return BudgetAllocation(
            total_budget=total_budget,
            categories=categories,
            per_person_cost=per_person_cost,
            contingency_percentage=percentages[BudgetCategory.CONTINGENCY]
        )
    
    @staticmethod
    def create_birthday_budget(
        total_budget: Decimal,
        guest_count: int
    ) -> BudgetAllocation:
        """Create budget allocation for birthday party"""
        per_person_cost = total_budget / guest_count
        
        percentages = {
            BudgetCategory.VENUE: 15.0,
            BudgetCategory.CATERING: 45.0,
            BudgetCategory.DECORATION: 20.0,
            BudgetCategory.ENTERTAINMENT: 10.0,
            BudgetCategory.PHOTOGRAPHY: 5.0,
            BudgetCategory.MISCELLANEOUS: 10.0,
            BudgetCategory.CONTINGENCY: 5.0
        }
        
        categories = {}
        for category, percentage in percentages.items():
            amount = total_budget * Decimal(str(percentage / 100))
            categories[category] = CategoryAllocation(
                category=category,
                amount=amount,
                percentage=percentage,
                justification=f"{category.value.title()} allocation for birthday party"
            )
        
        return BudgetAllocation(
            total_budget=total_budget,
            categories=categories,
            per_person_cost=per_person_cost,
            contingency_percentage=5.0
        )


class CriticalFactorFactory:
    """Factory for creating CriticalFactor instances"""
    
    @staticmethod
    def create_weather_factor(season: Season, venue_type: VenueType) -> Optional[CriticalFactor]:
        """Create weather-related critical factor"""
        if venue_type in [VenueType.OUTDOOR, VenueType.GARDEN, VenueType.BEACH]:
            if season == Season.MONSOON:
                return CriticalFactor(
                    name="Monsoon Weather Risk",
                    impact_level=Priority.CRITICAL,
                    description="Heavy rainfall during monsoon season can severely impact outdoor events",
                    mitigation_strategies=[
                        "Arrange waterproof tents/canopies",
                        "Have indoor backup venue ready",
                        "Monitor weather forecasts closely",
                        "Inform guests about weather contingency plans"
                    ]
                )
            elif season == Season.SUMMER:
                return CriticalFactor(
                    name="High Temperature Risk",
                    impact_level=Priority.HIGH,
                    description="Extreme heat can make outdoor events uncomfortable",
                    mitigation_strategies=[
                        "Provide adequate shade and cooling arrangements",
                        "Schedule activities during cooler hours",
                        "Ensure sufficient hydration stations",
                        "Consider air-conditioned backup areas"
                    ]
                )
        return None
    
    @staticmethod
    def create_guest_count_factor(guest_count: int, venue_type: VenueType) -> Optional[CriticalFactor]:
        """Create guest count related critical factor"""
        venue_limits = {
            VenueType.HOME: 50,
            VenueType.RESTAURANT: 200,
            VenueType.COMMUNITY_CENTER: 300
        }
        
        limit = venue_limits.get(venue_type)
        if limit and guest_count > limit * 0.8:  # 80% of capacity
            return CriticalFactor(
                name="Venue Capacity Constraint",
                impact_level=Priority.HIGH,
                description=f"Guest count ({guest_count}) approaching venue capacity limit",
                mitigation_strategies=[
                    "Confirm exact venue capacity with management",
                    "Plan efficient seating arrangements",
                    "Consider overflow areas or alternative venues",
                    "Implement guest list management system"
                ]
            )
        return None