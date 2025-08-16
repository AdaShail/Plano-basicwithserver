"""
Budget Allocation Engine for intelligent budget distribution across categories.
"""
from decimal import Decimal
from typing import Dict, List, Tuple
import logging

try:
    from ..models.core import EventContext, BudgetAllocation, CategoryAllocation, Alternative
    from ..models.enums import BudgetCategory, EventType, VenueType, BudgetTier, Season, Priority
except ImportError:
    # Fallback imports for when running as standalone
    from app.models.core import EventContext, BudgetAllocation, CategoryAllocation, Alternative
    from app.models.enums import BudgetCategory, EventType, VenueType, BudgetTier, Season, Priority

logger = logging.getLogger(__name__)


class BudgetAllocationEngine:
    """
    Intelligent budget allocation engine that distributes budget across categories
    based on event type, guest count, venue type, and other contextual factors.
    """
    
    # Base percentage allocations by event type
    BASE_ALLOCATIONS = {
        EventType.WEDDING: {
            BudgetCategory.VENUE: 25.0,
            BudgetCategory.CATERING: 40.0,
            BudgetCategory.DECORATION: 12.0,
            BudgetCategory.ENTERTAINMENT: 8.0,
            BudgetCategory.PHOTOGRAPHY: 10.0,
            BudgetCategory.TRANSPORTATION: 3.0,
            BudgetCategory.MISCELLANEOUS: 2.0
        },
        EventType.BIRTHDAY: {
            BudgetCategory.VENUE: 20.0,
            BudgetCategory.CATERING: 35.0,
            BudgetCategory.DECORATION: 15.0,
            BudgetCategory.ENTERTAINMENT: 20.0,
            BudgetCategory.PHOTOGRAPHY: 5.0,
            BudgetCategory.TRANSPORTATION: 3.0,
            BudgetCategory.MISCELLANEOUS: 2.0
        },
        EventType.CORPORATE: {
            BudgetCategory.VENUE: 30.0,
            BudgetCategory.CATERING: 25.0,
            BudgetCategory.DECORATION: 8.0,
            BudgetCategory.ENTERTAINMENT: 15.0,
            BudgetCategory.PHOTOGRAPHY: 10.0,
            BudgetCategory.TRANSPORTATION: 10.0,
            BudgetCategory.MISCELLANEOUS: 2.0
        },
        EventType.ANNIVERSARY: {
            BudgetCategory.VENUE: 22.0,
            BudgetCategory.CATERING: 38.0,
            BudgetCategory.DECORATION: 15.0,
            BudgetCategory.ENTERTAINMENT: 12.0,
            BudgetCategory.PHOTOGRAPHY: 8.0,
            BudgetCategory.TRANSPORTATION: 3.0,
            BudgetCategory.MISCELLANEOUS: 2.0
        },
        EventType.ENGAGEMENT: {
            BudgetCategory.VENUE: 20.0,
            BudgetCategory.CATERING: 35.0,
            BudgetCategory.DECORATION: 18.0,
            BudgetCategory.ENTERTAINMENT: 10.0,
            BudgetCategory.PHOTOGRAPHY: 12.0,
            BudgetCategory.TRANSPORTATION: 3.0,
            BudgetCategory.MISCELLANEOUS: 2.0
        },
        EventType.HOUSEWARMING: {
            BudgetCategory.VENUE: 15.0,  # Often at home, lower venue costs
            BudgetCategory.CATERING: 45.0,  # Food is central to housewarming
            BudgetCategory.DECORATION: 20.0,  # Important for new home showcase
            BudgetCategory.ENTERTAINMENT: 8.0,
            BudgetCategory.PHOTOGRAPHY: 5.0,
            BudgetCategory.TRANSPORTATION: 2.0,
            BudgetCategory.MISCELLANEOUS: 5.0
        },
        EventType.GRADUATION: {
            BudgetCategory.VENUE: 25.0,
            BudgetCategory.CATERING: 35.0,
            BudgetCategory.DECORATION: 15.0,
            BudgetCategory.ENTERTAINMENT: 10.0,
            BudgetCategory.PHOTOGRAPHY: 10.0,
            BudgetCategory.TRANSPORTATION: 3.0,
            BudgetCategory.MISCELLANEOUS: 2.0
        },
        EventType.BABY_SHOWER: {
            BudgetCategory.VENUE: 18.0,
            BudgetCategory.CATERING: 40.0,
            BudgetCategory.DECORATION: 20.0,
            BudgetCategory.ENTERTAINMENT: 8.0,
            BudgetCategory.PHOTOGRAPHY: 8.0,
            BudgetCategory.TRANSPORTATION: 3.0,
            BudgetCategory.MISCELLANEOUS: 3.0
        }
    }
    
    # Venue type impact multipliers
    VENUE_MULTIPLIERS = {
        VenueType.OUTDOOR: {
            BudgetCategory.VENUE: 1.2,  # Higher setup costs
            BudgetCategory.DECORATION: 1.3,  # Weather protection needed
            BudgetCategory.CATERING: 1.1,  # Additional logistics
            BudgetCategory.MISCELLANEOUS: 1.5  # Contingency for weather
        },
        VenueType.INDOOR: {
            BudgetCategory.VENUE: 1.0,
            BudgetCategory.DECORATION: 1.0,
            BudgetCategory.CATERING: 1.0,
            BudgetCategory.MISCELLANEOUS: 1.0
        },
        VenueType.HOME: {
            BudgetCategory.VENUE: 0.3,  # Much lower venue costs
            BudgetCategory.DECORATION: 1.2,  # More decoration needed
            BudgetCategory.CATERING: 1.1,  # Kitchen limitations
            BudgetCategory.TRANSPORTATION: 0.8  # Guests know location
        },
        VenueType.HOTEL: {
            BudgetCategory.VENUE: 1.4,  # Premium pricing
            BudgetCategory.CATERING: 1.3,  # Hotel catering premium
            BudgetCategory.DECORATION: 0.8,  # Some included
            BudgetCategory.TRANSPORTATION: 1.2  # Valet, etc.
        }
    }
    
    # Budget tier adjustments
    TIER_ADJUSTMENTS = {
        BudgetTier.LOW: {
            BudgetCategory.ENTERTAINMENT: 0.7,
            BudgetCategory.PHOTOGRAPHY: 0.8,
            BudgetCategory.DECORATION: 0.8,
            BudgetCategory.MISCELLANEOUS: 1.2  # More contingency needed
        },
        BudgetTier.STANDARD: {
            # No adjustments - base case
        },
        BudgetTier.PREMIUM: {
            BudgetCategory.ENTERTAINMENT: 1.3,
            BudgetCategory.PHOTOGRAPHY: 1.4,
            BudgetCategory.DECORATION: 1.2,
            BudgetCategory.VENUE: 1.2
        },
        BudgetTier.LUXURY: {
            BudgetCategory.ENTERTAINMENT: 1.6,
            BudgetCategory.PHOTOGRAPHY: 1.8,
            BudgetCategory.DECORATION: 1.5,
            BudgetCategory.VENUE: 1.5,
            BudgetCategory.CATERING: 1.3
        }
    }
    
    # Regional cost multipliers (base: Mumbai = 1.0)
    REGIONAL_MULTIPLIERS = {
        # Tier 1 cities (high cost)
        "mumbai": 1.0,  # Base reference
        "delhi": 1.05,
        "bangalore": 0.95,
        "hyderabad": 0.85,
        "chennai": 0.9,
        "pune": 0.8,
        "kolkata": 0.75,
        "ahmedabad": 0.7,
        
        # Tier 2 cities (medium cost)
        "jaipur": 0.65,
        "lucknow": 0.6,
        "kanpur": 0.55,
        "nagpur": 0.6,
        "indore": 0.65,
        "bhopal": 0.6,
        "visakhapatnam": 0.55,
        "vadodara": 0.65,
        
        # Tier 3 cities (lower cost)
        "agra": 0.5,
        "meerut": 0.45,
        "rajkot": 0.5,
        "jabalpur": 0.45,
        "gwalior": 0.4,
        "vijayawada": 0.5,
        "jodhpur": 0.45,
        "madurai": 0.5,
        
        # International (premium pricing)
        "dubai": 1.8,
        "singapore": 1.6,
        "london": 2.0,
        "new york": 2.2,
        "paris": 1.9,
        "sydney": 1.7,
        "toronto": 1.5,
        "bangkok": 1.2
    }
    
    # Seasonal cost adjustments
    SEASONAL_MULTIPLIERS = {
        Season.WINTER: {
            # Peak wedding season in India
            BudgetCategory.VENUE: 1.3,
            BudgetCategory.CATERING: 1.2,
            BudgetCategory.PHOTOGRAPHY: 1.25,
            BudgetCategory.DECORATION: 1.2,
            BudgetCategory.TRANSPORTATION: 1.1
        },
        Season.SPRING: {
            # Good weather, moderate demand
            BudgetCategory.VENUE: 1.1,
            BudgetCategory.CATERING: 1.05,
            BudgetCategory.PHOTOGRAPHY: 1.1,
            BudgetCategory.DECORATION: 1.05
        },
        Season.SUMMER: {
            # Hot weather, lower demand for outdoor events
            BudgetCategory.VENUE: 0.9,
            BudgetCategory.CATERING: 0.95,
            BudgetCategory.DECORATION: 0.9,
            BudgetCategory.MISCELLANEOUS: 1.1  # AC, cooling costs
        },
        Season.MONSOON: {
            # Lowest demand, weather challenges
            BudgetCategory.VENUE: 0.8,
            BudgetCategory.CATERING: 0.9,
            BudgetCategory.DECORATION: 0.85,
            BudgetCategory.TRANSPORTATION: 1.2,  # Weather challenges
            BudgetCategory.MISCELLANEOUS: 1.3   # Weather contingency
        },
        Season.AUTUMN: {
            # Post-monsoon, good weather returning
            BudgetCategory.VENUE: 1.0,
            BudgetCategory.CATERING: 1.0,
            BudgetCategory.PHOTOGRAPHY: 1.05,
            BudgetCategory.DECORATION: 1.0
        }
    }
    
    # Currency conversion rates (to INR, approximate)
    CURRENCY_RATES = {
        "INR": 1.0,
        "USD": 83.0,
        "EUR": 90.0,
        "GBP": 105.0,
        "AED": 22.5,
        "SGD": 62.0,
        "AUD": 55.0,
        "CAD": 61.0,
        "THB": 2.3
    }
    
    def __init__(self):
        """Initialize the budget allocation engine."""
        self.logger = logging.getLogger(__name__)
    
    def allocate_budget(self, total_budget: Decimal, context: EventContext) -> BudgetAllocation:
        """
        Allocate budget across categories based on event context.
        
        Args:
            total_budget: Total budget available
            context: Event context with all relevant parameters
            
        Returns:
            BudgetAllocation with detailed category breakdown
        """
        try:
            # Get base percentages for event type
            base_percentages = self._get_base_percentages(context.event_type)
            
            # Apply venue type adjustments
            adjusted_percentages = self._apply_venue_adjustments(
                base_percentages, context.venue_type
            )
            
            # Apply budget tier adjustments
            adjusted_percentages = self._apply_tier_adjustments(
                adjusted_percentages, context.budget_tier
            )
            
            # Apply guest count scaling
            adjusted_percentages = self._apply_guest_count_scaling(
                adjusted_percentages, context.guest_count
            )
            
            # Apply regional adjustments
            regional_multiplier = self._get_regional_multiplier(context.location)
            
            # Apply seasonal adjustments
            adjusted_percentages = self._apply_seasonal_adjustments(
                adjusted_percentages, context.season
            )
            
            # Normalize percentages to ensure they sum to 100%
            adjusted_percentages = self._normalize_percentages(adjusted_percentages)
            
            # Create category allocations
            categories = {}
            for category, percentage in adjusted_percentages.items():
                # Apply regional multiplier to the amount
                base_amount = total_budget * Decimal(str(percentage / 100))
                adjusted_amount = base_amount * Decimal(str(regional_multiplier))
                
                allocation = CategoryAllocation(
                    category=category,
                    amount=adjusted_amount,
                    percentage=percentage,
                    justification=self._get_justification(category, context, percentage),
                    alternatives=self._generate_alternatives(category, adjusted_amount, context),
                    priority=self._get_category_priority(category, context)
                )
                categories[category] = allocation
            
            # Calculate per-person cost (adjusted for region)
            adjusted_total_budget = total_budget * Decimal(str(regional_multiplier))
            per_person_cost = adjusted_total_budget / Decimal(str(context.guest_count))
            
            # Set contingency percentage based on complexity
            contingency_percentage = self._calculate_contingency_percentage(context)
            
            # Create regional and seasonal adjustment records
            regional_adjustments = {
                "location": f"{context.location.city}, {context.location.country}",
                "multiplier": regional_multiplier
            }
            
            seasonal_adjustments = {
                context.season: self._get_seasonal_impact(context.season)
            }
            
            return BudgetAllocation(
                total_budget=adjusted_total_budget,
                categories=categories,
                per_person_cost=per_person_cost,
                contingency_percentage=contingency_percentage,
                regional_adjustments=regional_adjustments,
                seasonal_adjustments=seasonal_adjustments
            )
            
        except Exception as e:
            self.logger.error(f"Error allocating budget: {str(e)}")
            raise
    
    def _get_base_percentages(self, event_type: EventType) -> Dict[BudgetCategory, float]:
        """Get base percentage allocations for event type."""
        if event_type in self.BASE_ALLOCATIONS:
            return self.BASE_ALLOCATIONS[event_type].copy()
        else:
            # Default to wedding allocations for unknown event types
            self.logger.warning(f"Unknown event type {event_type}, using wedding defaults")
            return self.BASE_ALLOCATIONS[EventType.WEDDING].copy()
    
    def _apply_venue_adjustments(
        self, 
        percentages: Dict[BudgetCategory, float], 
        venue_type: VenueType
    ) -> Dict[BudgetCategory, float]:
        """Apply venue type adjustments to percentages."""
        if venue_type not in self.VENUE_MULTIPLIERS:
            return percentages
        
        multipliers = self.VENUE_MULTIPLIERS[venue_type]
        adjusted = percentages.copy()
        
        for category, multiplier in multipliers.items():
            if category in adjusted:
                adjusted[category] *= multiplier
        
        return adjusted
    
    def _apply_tier_adjustments(
        self, 
        percentages: Dict[BudgetCategory, float], 
        budget_tier: BudgetTier
    ) -> Dict[BudgetCategory, float]:
        """Apply budget tier adjustments to percentages."""
        if budget_tier not in self.TIER_ADJUSTMENTS:
            return percentages
        
        adjustments = self.TIER_ADJUSTMENTS[budget_tier]
        adjusted = percentages.copy()
        
        for category, multiplier in adjustments.items():
            if category in adjusted:
                adjusted[category] *= multiplier
        
        return adjusted
    
    def _apply_guest_count_scaling(
        self, 
        percentages: Dict[BudgetCategory, float], 
        guest_count: int
    ) -> Dict[BudgetCategory, float]:
        """Apply guest count scaling to percentages."""
        adjusted = percentages.copy()
        
        # For larger events, venue and logistics become more important
        if guest_count > 200:
            scale_factor = min(1.2, 1.0 + (guest_count - 200) / 1000)
            adjusted[BudgetCategory.VENUE] *= scale_factor
            adjusted[BudgetCategory.TRANSPORTATION] *= scale_factor
            
            # Reduce decoration percentage for very large events
            if guest_count > 500:
                adjusted[BudgetCategory.DECORATION] *= 0.9
        
        # For smaller events, entertainment and decoration become more important
        elif guest_count < 50:
            adjusted[BudgetCategory.ENTERTAINMENT] *= 1.2
            adjusted[BudgetCategory.DECORATION] *= 1.1
            adjusted[BudgetCategory.VENUE] *= 0.9
        
        return adjusted
    
    def _normalize_percentages(
        self, 
        percentages: Dict[BudgetCategory, float]
    ) -> Dict[BudgetCategory, float]:
        """Normalize percentages to sum to 100%."""
        total = sum(percentages.values())
        if total == 0:
            raise ValueError("Total percentage cannot be zero")
        
        return {category: (percentage / total) * 100 
                for category, percentage in percentages.items()}
    
    def _get_justification(
        self, 
        category: BudgetCategory, 
        context: EventContext, 
        percentage: float
    ) -> str:
        """Generate justification for category allocation."""
        justifications = {
            BudgetCategory.VENUE: f"Venue allocation of {percentage:.1f}% accounts for {context.venue_type.value} venue requirements and {context.guest_count} guests",
            BudgetCategory.CATERING: f"Catering allocation of {percentage:.1f}% covers food and beverages for {context.guest_count} guests with {context.budget_tier.value} tier service",
            BudgetCategory.DECORATION: f"Decoration allocation of {percentage:.1f}% includes floral arrangements, lighting, and ambiance for {context.event_type.value}",
            BudgetCategory.ENTERTAINMENT: f"Entertainment allocation of {percentage:.1f}% covers music, performances, and activities for {context.event_type.value}",
            BudgetCategory.PHOTOGRAPHY: f"Photography allocation of {percentage:.1f}% includes professional documentation of the {context.event_type.value}",
            BudgetCategory.TRANSPORTATION: f"Transportation allocation of {percentage:.1f}% covers guest logistics and vendor coordination",
            BudgetCategory.MISCELLANEOUS: f"Miscellaneous allocation of {percentage:.1f}% provides contingency for unexpected costs and minor items"
        }
        
        return justifications.get(category, f"Allocation of {percentage:.1f}% for {category.value}")
    
    def _generate_alternatives(
        self, 
        category: BudgetCategory, 
        amount: Decimal, 
        context: EventContext
    ) -> List[Alternative]:
        """Generate alternative options for budget category."""
        alternatives = []
        
        # Generate cost-saving alternative
        cost_saving = Alternative(
            name=f"Budget {category.value}",
            description=f"Reduce {category.value} costs by choosing simpler options",
            cost_impact=amount * Decimal('-0.3'),
            trade_offs=[f"Simpler {category.value} options", "May impact overall quality"]
        )
        alternatives.append(cost_saving)
        
        # Generate premium alternative
        premium = Alternative(
            name=f"Premium {category.value}",
            description=f"Upgrade {category.value} with premium options",
            cost_impact=amount * Decimal('0.5'),
            trade_offs=[f"Higher quality {category.value}", "Increased overall budget"]
        )
        alternatives.append(premium)
        
        return alternatives
    
    def _get_category_priority(
        self, 
        category: BudgetCategory, 
        context: EventContext
    ) -> Priority:
        """Determine priority level for budget category."""
        # Critical categories that can't be compromised
        critical_categories = {BudgetCategory.VENUE, BudgetCategory.CATERING}
        
        # High priority categories for most events
        high_priority = {BudgetCategory.PHOTOGRAPHY, BudgetCategory.TRANSPORTATION}
        
        # Event-specific priorities
        if context.event_type == EventType.WEDDING:
            high_priority.add(BudgetCategory.DECORATION)
        elif context.event_type == EventType.CORPORATE:
            high_priority.add(BudgetCategory.ENTERTAINMENT)
        
        if category in critical_categories:
            return Priority.CRITICAL
        elif category in high_priority:
            return Priority.HIGH
        else:
            return Priority.MEDIUM
    
    def _calculate_contingency_percentage(self, context: EventContext) -> float:
        """Calculate appropriate contingency percentage based on event complexity."""
        base_contingency = 10.0  # 10% base contingency
        
        # Increase contingency for complex events
        if context.complexity_score > 7:
            base_contingency += 5.0
        elif context.complexity_score > 5:
            base_contingency += 2.0
        
        # Increase for outdoor venues
        if context.venue_type == VenueType.OUTDOOR:
            base_contingency += 3.0
        
        # Increase for large events
        if context.guest_count > 300:
            base_contingency += 2.0
        
        return min(base_contingency, 20.0)  # Cap at 20%
    
    def _get_regional_multiplier(self, location: 'Location') -> float:
        """Get regional cost multiplier based on location."""
        city_key = location.city.lower()
        
        # Check if city is in our regional multipliers
        if city_key in self.REGIONAL_MULTIPLIERS:
            return self.REGIONAL_MULTIPLIERS[city_key]
        
        # Default multiplier for unknown cities based on country
        country_defaults = {
            "india": 0.6,      # Average for smaller Indian cities
            "uae": 1.5,        # UAE cities tend to be expensive
            "usa": 1.8,        # US cities tend to be expensive
            "uk": 1.7,         # UK cities tend to be expensive
            "singapore": 1.6,   # Singapore is expensive
            "australia": 1.4,   # Australian cities are expensive
            "canada": 1.3,      # Canadian cities are moderately expensive
            "thailand": 1.0     # Thailand is moderate
        }
        
        country_key = location.country.lower()
        return country_defaults.get(country_key, 0.8)  # Default for unknown countries
    
    def _apply_seasonal_adjustments(
        self, 
        percentages: Dict[BudgetCategory, float], 
        season: Season
    ) -> Dict[BudgetCategory, float]:
        """Apply seasonal cost adjustments to percentages."""
        if season not in self.SEASONAL_MULTIPLIERS:
            return percentages
        
        seasonal_adjustments = self.SEASONAL_MULTIPLIERS[season]
        adjusted = percentages.copy()
        
        for category, multiplier in seasonal_adjustments.items():
            if category in adjusted:
                adjusted[category] *= multiplier
        
        return adjusted
    
    def _get_seasonal_impact(self, season: Season) -> float:
        """Get overall seasonal impact factor."""
        seasonal_impacts = {
            Season.WINTER: 1.2,   # Peak season, higher costs
            Season.SPRING: 1.05,  # Good season, slight premium
            Season.SUMMER: 0.95,  # Hot weather, lower demand
            Season.MONSOON: 0.85, # Lowest demand due to weather
            Season.AUTUMN: 1.0    # Neutral season
        }
        
        return seasonal_impacts.get(season, 1.0)
    
    def apply_regional_adjustments(
        self, 
        allocation: BudgetAllocation, 
        location: 'Location'
    ) -> BudgetAllocation:
        """
        Apply regional cost adjustments to an existing allocation.
        This method can be used to adjust budgets for different locations.
        """
        regional_multiplier = self._get_regional_multiplier(location)
        
        # Adjust all category amounts
        adjusted_categories = {}
        for category, cat_allocation in allocation.categories.items():
            adjusted_amount = cat_allocation.amount * Decimal(str(regional_multiplier))
            
            adjusted_cat = CategoryAllocation(
                category=category,
                amount=adjusted_amount,
                percentage=cat_allocation.percentage,  # Percentages stay the same
                justification=f"{cat_allocation.justification} (Adjusted for {location.city})",
                alternatives=self._adjust_alternatives_for_region(
                    cat_allocation.alternatives, regional_multiplier
                ),
                priority=cat_allocation.priority
            )
            adjusted_categories[category] = adjusted_cat
        
        # Adjust total budget
        adjusted_total = allocation.total_budget * Decimal(str(regional_multiplier))
        adjusted_per_person = allocation.per_person_cost * Decimal(str(regional_multiplier))
        
        return BudgetAllocation(
            total_budget=adjusted_total,
            categories=adjusted_categories,
            per_person_cost=adjusted_per_person,
            contingency_percentage=allocation.contingency_percentage,
            regional_adjustments={
                "location": f"{location.city}, {location.country}",
                "multiplier": regional_multiplier
            },
            seasonal_adjustments=allocation.seasonal_adjustments
        )
    
    def _adjust_alternatives_for_region(
        self, 
        alternatives: List['Alternative'], 
        regional_multiplier: float
    ) -> List['Alternative']:
        """Adjust alternative costs for regional differences."""
        adjusted_alternatives = []
        
        for alt in alternatives:
            adjusted_alt = Alternative(
                name=alt.name,
                description=alt.description,
                cost_impact=alt.cost_impact * Decimal(str(regional_multiplier)),
                time_impact=alt.time_impact,
                trade_offs=alt.trade_offs
            )
            adjusted_alternatives.append(adjusted_alt)
        
        return adjusted_alternatives
    
    def get_vendor_availability_by_season(
        self, 
        season: Season, 
        location: 'Location'
    ) -> Dict[BudgetCategory, str]:
        """
        Get vendor availability information by season and location.
        Returns availability status for each budget category.
        """
        # Base availability patterns
        availability = {
            Season.WINTER: {
                BudgetCategory.VENUE: "High demand, book 6+ months ahead",
                BudgetCategory.CATERING: "Premium vendors booked early",
                BudgetCategory.PHOTOGRAPHY: "Top photographers in high demand",
                BudgetCategory.DECORATION: "Flower prices at peak",
                BudgetCategory.ENTERTAINMENT: "Popular artists charge premium"
            },
            Season.SPRING: {
                BudgetCategory.VENUE: "Good availability, moderate pricing",
                BudgetCategory.CATERING: "Seasonal ingredients available",
                BudgetCategory.PHOTOGRAPHY: "Good weather for outdoor shoots",
                BudgetCategory.DECORATION: "Spring flowers in season",
                BudgetCategory.ENTERTAINMENT: "Standard pricing"
            },
            Season.SUMMER: {
                BudgetCategory.VENUE: "Indoor venues preferred, good deals",
                BudgetCategory.CATERING: "AC costs higher, cold menu popular",
                BudgetCategory.PHOTOGRAPHY: "Early morning/evening shoots",
                BudgetCategory.DECORATION: "Heat-resistant decorations needed",
                BudgetCategory.ENTERTAINMENT: "Indoor entertainment preferred"
            },
            Season.MONSOON: {
                BudgetCategory.VENUE: "Indoor venues essential, best deals",
                BudgetCategory.CATERING: "Limited outdoor catering options",
                BudgetCategory.PHOTOGRAPHY: "Weather backup plans needed",
                BudgetCategory.DECORATION: "Waterproof decorations required",
                BudgetCategory.ENTERTAINMENT: "Indoor entertainment only"
            },
            Season.AUTUMN: {
                BudgetCategory.VENUE: "Post-monsoon bookings picking up",
                BudgetCategory.CATERING: "Festival season ingredients available",
                BudgetCategory.PHOTOGRAPHY: "Clear weather, good lighting",
                BudgetCategory.DECORATION: "Post-monsoon fresh flowers",
                BudgetCategory.ENTERTAINMENT: "Festival season performers available"
            }
        }
        
        return availability.get(season, {})
    
    def estimate_currency_impact(
        self, 
        base_budget: Decimal, 
        from_currency: str, 
        to_currency: str = "INR"
    ) -> Decimal:
        """
        Estimate budget in different currency.
        Useful for destination events or international planning.
        """
        if from_currency not in self.CURRENCY_RATES or to_currency not in self.CURRENCY_RATES:
            self.logger.warning(f"Currency conversion not available for {from_currency} to {to_currency}")
            return base_budget
        
        # Convert to INR first, then to target currency
        inr_amount = base_budget * Decimal(str(self.CURRENCY_RATES[from_currency]))
        target_amount = inr_amount / Decimal(str(self.CURRENCY_RATES[to_currency]))
        
        return target_amount
    
    def classify_budget_tier(
        self, 
        total_budget: Decimal, 
        guest_count: int, 
        event_type: EventType
    ) -> BudgetTier:
        """
        Classify budget tier based on per-person cost and event type.
        """
        per_person = total_budget / Decimal(str(guest_count))
        
        # Budget tier thresholds by event type (per person in INR)
        tier_thresholds = {
            EventType.WEDDING: {
                BudgetTier.LOW: Decimal('2000'),
                BudgetTier.STANDARD: Decimal('5000'),
                BudgetTier.PREMIUM: Decimal('12000'),
                BudgetTier.LUXURY: Decimal('25000')
            },
            EventType.CORPORATE: {
                BudgetTier.LOW: Decimal('2000'),
                BudgetTier.STANDARD: Decimal('5000'),
                BudgetTier.PREMIUM: Decimal('10000'),
                BudgetTier.LUXURY: Decimal('20000')
            },
            EventType.BIRTHDAY: {
                BudgetTier.LOW: Decimal('1500'),
                BudgetTier.STANDARD: Decimal('3000'),
                BudgetTier.PREMIUM: Decimal('6000'),
                BudgetTier.LUXURY: Decimal('12000')
            }
        }
        
        # Default to wedding thresholds for unknown event types
        thresholds = tier_thresholds.get(event_type, tier_thresholds[EventType.WEDDING])
        
        if per_person >= thresholds[BudgetTier.LUXURY]:
            return BudgetTier.LUXURY
        elif per_person >= thresholds[BudgetTier.PREMIUM]:
            return BudgetTier.PREMIUM
        elif per_person >= thresholds[BudgetTier.STANDARD]:
            return BudgetTier.STANDARD
        else:
            return BudgetTier.LOW
    
    def handle_budget_constraints(
        self, 
        allocation: BudgetAllocation, 
        constraints: Dict[str, any]
    ) -> BudgetAllocation:
        """
        Handle budget constraints and reallocate funds accordingly.
        
        Args:
            allocation: Original budget allocation
            constraints: Dictionary of constraints like max_venue_cost, min_catering_percentage, etc.
        """
        adjusted_categories = allocation.categories.copy()
        
        # Handle maximum category constraints
        if 'max_venue_cost' in constraints:
            max_venue = Decimal(str(constraints['max_venue_cost']))
            venue_allocation = adjusted_categories[BudgetCategory.VENUE]
            
            if venue_allocation.amount > max_venue:
                excess = venue_allocation.amount - max_venue
                
                # Reduce venue allocation
                adjusted_categories[BudgetCategory.VENUE] = CategoryAllocation(
                    category=BudgetCategory.VENUE,
                    amount=max_venue,
                    percentage=(max_venue / allocation.total_budget) * 100,
                    justification=f"Venue cost capped at ₹{max_venue} due to budget constraint",
                    alternatives=venue_allocation.alternatives,
                    priority=venue_allocation.priority
                )
                
                # Redistribute excess to other categories
                self._redistribute_excess_budget(adjusted_categories, excess, [BudgetCategory.VENUE])
        
        # Handle minimum percentage constraints
        if 'min_catering_percentage' in constraints:
            min_catering_pct = float(constraints['min_catering_percentage'])
            min_catering_amount = allocation.total_budget * Decimal(str(min_catering_pct / 100))
            
            catering_allocation = adjusted_categories[BudgetCategory.CATERING]
            if catering_allocation.amount < min_catering_amount:
                deficit = min_catering_amount - catering_allocation.amount
                
                # Increase catering allocation
                adjusted_categories[BudgetCategory.CATERING] = CategoryAllocation(
                    category=BudgetCategory.CATERING,
                    amount=min_catering_amount,
                    percentage=min_catering_pct,
                    justification=f"Catering increased to minimum {min_catering_pct}% as required",
                    alternatives=catering_allocation.alternatives,
                    priority=catering_allocation.priority
                )
                
                # Reduce other categories to compensate
                self._reduce_other_categories(adjusted_categories, deficit, [BudgetCategory.CATERING])
        
        # Handle total budget constraint (if budget is insufficient)
        if 'max_total_budget' in constraints:
            max_budget = Decimal(str(constraints['max_total_budget']))
            if allocation.total_budget > max_budget:
                # First apply other constraints, then scale down
                temp_allocation = BudgetAllocation(
                    total_budget=allocation.total_budget,
                    categories=adjusted_categories,
                    per_person_cost=allocation.per_person_cost,
                    contingency_percentage=allocation.contingency_percentage,
                    regional_adjustments=allocation.regional_adjustments,
                    seasonal_adjustments=allocation.seasonal_adjustments
                )
                return self._scale_down_allocation(temp_allocation, max_budget)
        
        # Recalculate percentages and validate
        total_amount = sum(cat.amount for cat in adjusted_categories.values())
        for category, cat_allocation in adjusted_categories.items():
            new_percentage = float((cat_allocation.amount / total_amount) * 100)
            adjusted_categories[category] = CategoryAllocation(
                category=cat_allocation.category,
                amount=cat_allocation.amount,
                percentage=new_percentage,
                justification=cat_allocation.justification,
                alternatives=cat_allocation.alternatives,
                priority=cat_allocation.priority
            )
        
        return BudgetAllocation(
            total_budget=total_amount,
            categories=adjusted_categories,
            per_person_cost=total_amount / (allocation.total_budget / allocation.per_person_cost),
            contingency_percentage=allocation.contingency_percentage,
            regional_adjustments=allocation.regional_adjustments,
            seasonal_adjustments=allocation.seasonal_adjustments
        )
    
    def _redistribute_excess_budget(
        self, 
        categories: Dict[BudgetCategory, CategoryAllocation], 
        excess_amount: Decimal, 
        exclude_categories: List[BudgetCategory]
    ):
        """Redistribute excess budget to other categories proportionally."""
        eligible_categories = {k: v for k, v in categories.items() if k not in exclude_categories}
        total_eligible_amount = sum(cat.amount for cat in eligible_categories.values())
        
        if total_eligible_amount == 0:
            return
        
        for category, allocation in eligible_categories.items():
            proportion = allocation.amount / total_eligible_amount
            additional_amount = excess_amount * proportion
            
            categories[category] = CategoryAllocation(
                category=category,
                amount=allocation.amount + additional_amount,
                percentage=allocation.percentage,  # Will be recalculated later
                justification=f"{allocation.justification} (Increased due to venue constraint)",
                alternatives=allocation.alternatives,
                priority=allocation.priority
            )
    
    def _reduce_other_categories(
        self, 
        categories: Dict[BudgetCategory, CategoryAllocation], 
        deficit_amount: Decimal, 
        exclude_categories: List[BudgetCategory]
    ):
        """Reduce other categories proportionally to cover deficit."""
        eligible_categories = {k: v for k, v in categories.items() if k not in exclude_categories}
        total_eligible_amount = sum(cat.amount for cat in eligible_categories.values())
        
        if total_eligible_amount == 0:
            return
        
        for category, allocation in eligible_categories.items():
            proportion = allocation.amount / total_eligible_amount
            reduction_amount = deficit_amount * proportion
            
            new_amount = max(allocation.amount - reduction_amount, Decimal('0'))
            
            categories[category] = CategoryAllocation(
                category=category,
                amount=new_amount,
                percentage=allocation.percentage,  # Will be recalculated later
                justification=f"{allocation.justification} (Reduced to meet catering minimum)",
                alternatives=allocation.alternatives,
                priority=allocation.priority
            )
    
    def _scale_down_allocation(
        self, 
        allocation: BudgetAllocation, 
        target_budget: Decimal
    ) -> BudgetAllocation:
        """Scale down entire allocation to fit target budget."""
        scale_factor = target_budget / allocation.total_budget
        
        scaled_categories = {}
        for category, cat_allocation in allocation.categories.items():
            scaled_amount = cat_allocation.amount * scale_factor
            
            scaled_categories[category] = CategoryAllocation(
                category=category,
                amount=scaled_amount,
                percentage=cat_allocation.percentage,  # Percentages stay the same
                justification=f"{cat_allocation.justification} (Scaled down to fit budget)",
                alternatives=self._scale_alternatives(cat_allocation.alternatives, scale_factor),
                priority=cat_allocation.priority
            )
        
        return BudgetAllocation(
            total_budget=target_budget,
            categories=scaled_categories,
            per_person_cost=target_budget / (allocation.total_budget / allocation.per_person_cost),
            contingency_percentage=allocation.contingency_percentage,
            regional_adjustments=allocation.regional_adjustments,
            seasonal_adjustments=allocation.seasonal_adjustments
        )
    
    def _scale_alternatives(
        self, 
        alternatives: List['Alternative'], 
        scale_factor: Decimal
    ) -> List['Alternative']:
        """Scale alternative costs by the given factor."""
        scaled_alternatives = []
        
        for alt in alternatives:
            scaled_alt = Alternative(
                name=alt.name,
                description=alt.description,
                cost_impact=alt.cost_impact * scale_factor,
                time_impact=alt.time_impact,
                trade_offs=alt.trade_offs
            )
            scaled_alternatives.append(scaled_alt)
        
        return scaled_alternatives
    
    def generate_budget_constrained_alternatives(
        self, 
        original_allocation: BudgetAllocation, 
        target_budget: Decimal
    ) -> List[BudgetAllocation]:
        """
        Generate alternative budget allocations for budget-constrained scenarios.
        """
        alternatives = []
        
        if target_budget >= original_allocation.total_budget:
            return alternatives  # No alternatives needed
        
        reduction_needed = original_allocation.total_budget - target_budget
        reduction_percentage = float((reduction_needed / original_allocation.total_budget) * 100)
        
        # Alternative 1: Proportional reduction across all categories
        proportional_alternative = self._scale_down_allocation(original_allocation, target_budget)
        alternatives.append(proportional_alternative)
        
        # Alternative 2: Prioritize essential categories, cut optional ones more
        priority_alternative = self._create_priority_based_alternative(original_allocation, target_budget)
        alternatives.append(priority_alternative)
        
        # Alternative 3: Minimize venue costs, maintain catering quality
        venue_minimized_alternative = self._create_venue_minimized_alternative(original_allocation, target_budget)
        alternatives.append(venue_minimized_alternative)
        
        return alternatives
    
    def _create_priority_based_alternative(
        self, 
        original_allocation: BudgetAllocation, 
        target_budget: Decimal
    ) -> BudgetAllocation:
        """Create alternative that prioritizes critical categories."""
        reduction_needed = original_allocation.total_budget - target_budget
        
        # Define reduction factors by priority
        priority_reductions = {
            Priority.CRITICAL: 0.05,    # 5% reduction for critical
            Priority.HIGH: 0.15,        # 15% reduction for high
            Priority.MEDIUM: 0.25,      # 25% reduction for medium
            Priority.LOW: 0.40,         # 40% reduction for low
            Priority.OPTIONAL: 0.60     # 60% reduction for optional
        }
        
        adjusted_categories = {}
        total_reduction = Decimal('0')
        
        for category, allocation in original_allocation.categories.items():
            reduction_factor = priority_reductions.get(allocation.priority, 0.25)
            category_reduction = allocation.amount * Decimal(str(reduction_factor))
            new_amount = allocation.amount - category_reduction
            total_reduction += category_reduction
            
            adjusted_categories[category] = CategoryAllocation(
                category=category,
                amount=new_amount,
                percentage=float((new_amount / target_budget) * 100),
                justification=f"{allocation.justification} (Priority-based reduction: {reduction_factor*100:.0f}%)",
                alternatives=allocation.alternatives,
                priority=allocation.priority
            )
        
        # Adjust if total reduction doesn't match target exactly
        actual_total = sum(cat.amount for cat in adjusted_categories.values())
        if actual_total != target_budget:
            scale_factor = target_budget / actual_total
            for category, allocation in adjusted_categories.items():
                new_amount = allocation.amount * scale_factor
                adjusted_categories[category] = CategoryAllocation(
                    category=allocation.category,
                    amount=new_amount,
                    percentage=float((new_amount / target_budget) * 100),
                    justification=allocation.justification,
                    alternatives=allocation.alternatives,
                    priority=allocation.priority
                )
        
        return BudgetAllocation(
            total_budget=target_budget,
            categories=adjusted_categories,
            per_person_cost=target_budget / (original_allocation.total_budget / original_allocation.per_person_cost),
            contingency_percentage=original_allocation.contingency_percentage,
            regional_adjustments=original_allocation.regional_adjustments,
            seasonal_adjustments=original_allocation.seasonal_adjustments
        )
    
    def _create_venue_minimized_alternative(
        self, 
        original_allocation: BudgetAllocation, 
        target_budget: Decimal
    ) -> BudgetAllocation:
        """Create alternative that minimizes venue costs to maintain other quality."""
        reduction_needed = original_allocation.total_budget - target_budget
        
        adjusted_categories = original_allocation.categories.copy()
        
        # Try to take most reduction from venue
        venue_allocation = adjusted_categories[BudgetCategory.VENUE]
        max_venue_reduction = venue_allocation.amount * Decimal('0.6')  # Max 60% reduction
        
        venue_reduction = min(reduction_needed, max_venue_reduction)
        remaining_reduction = reduction_needed - venue_reduction
        
        # Reduce venue
        adjusted_categories[BudgetCategory.VENUE] = CategoryAllocation(
            category=BudgetCategory.VENUE,
            amount=venue_allocation.amount - venue_reduction,
            percentage=venue_allocation.percentage,
            justification="Venue costs minimized to maintain catering and service quality",
            alternatives=venue_allocation.alternatives,
            priority=venue_allocation.priority
        )
        
        # Distribute remaining reduction across non-critical categories
        if remaining_reduction > 0:
            non_critical_categories = {
                k: v for k, v in adjusted_categories.items() 
                if k != BudgetCategory.VENUE and v.priority != Priority.CRITICAL
            }
            
            total_non_critical = sum(cat.amount for cat in non_critical_categories.values())
            
            for category, allocation in non_critical_categories.items():
                if total_non_critical > 0:
                    proportion = allocation.amount / total_non_critical
                    category_reduction = remaining_reduction * proportion
                    
                    adjusted_categories[category] = CategoryAllocation(
                        category=category,
                        amount=allocation.amount - category_reduction,
                        percentage=allocation.percentage,
                        justification=f"{allocation.justification} (Reduced to minimize venue impact)",
                        alternatives=allocation.alternatives,
                        priority=allocation.priority
                    )
        
        # Recalculate percentages
        for category, allocation in adjusted_categories.items():
            new_percentage = float((allocation.amount / target_budget) * 100)
            adjusted_categories[category] = CategoryAllocation(
                category=allocation.category,
                amount=allocation.amount,
                percentage=new_percentage,
                justification=allocation.justification,
                alternatives=allocation.alternatives,
                priority=allocation.priority
            )
        
        return BudgetAllocation(
            total_budget=target_budget,
            categories=adjusted_categories,
            per_person_cost=target_budget / (original_allocation.total_budget / original_allocation.per_person_cost),
            contingency_percentage=original_allocation.contingency_percentage,
            regional_adjustments=original_allocation.regional_adjustments,
            seasonal_adjustments=original_allocation.seasonal_adjustments
        )