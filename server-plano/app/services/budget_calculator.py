# Enhanced budget calculator using BudgetAllocationEngine
from decimal import Decimal
from typing import Dict, Optional, Any, List
import logging

from app.services.budget_allocation_engine import BudgetAllocationEngine
from app.services.event_context_analyzer import EventContextAnalyzer
from app.models.core import EventContext, Location
from app.models.enums import EventType, VenueType, BudgetTier, CulturalRequirement, Season, BudgetCategory

logger = logging.getLogger(__name__)

# Initialize engines
budget_engine = BudgetAllocationEngine()
context_analyzer = EventContextAnalyzer()


def calculate_budget(event_type: str, days: int, base_budget: Optional[float] = None,
                    guest_count: Optional[int] = None, venue_type: Optional[str] = None,
                    location: Optional[str] = None, religion: Optional[str] = None,
                    **kwargs) -> float:
    """
    Enhanced budget calculation using BudgetAllocationEngine.
    Maintains backward compatibility with existing API contracts.
    
    Args:
        event_type: Type of event
        days: Number of days for the event
        base_budget: Optional base budget (if provided, returns this value for compatibility)
        guest_count: Number of guests (improves budget accuracy)
        venue_type: Type of venue (affects budget distribution)
        location: Event location (for regional adjustments)
        religion: Religious/cultural requirements
        **kwargs: Additional parameters for enhanced calculation
    
    Returns:
        Total estimated budget as float (for backward compatibility)
    """
    try:
        # If base_budget is provided, return it for backward compatibility
        if base_budget:
            return base_budget
        
        # Create enhanced event context for new allocation engine
        context = _create_budget_context(
            event_type=event_type,
            days=days,
            guest_count=guest_count,
            venue_type=venue_type,
            location=location,
            religion=religion,
            **kwargs
        )
        
        # Calculate base budget using legacy rates as starting point
        legacy_budget = _calculate_legacy_budget(event_type, days)
        
        # Use allocation engine to get detailed breakdown
        allocation = budget_engine.allocate_budget(Decimal(str(legacy_budget)), context)
        
        # Return total budget as float for backward compatibility
        total_budget = float(allocation.total_budget)
        
        logger.info(f"Enhanced budget calculation: {total_budget} for {event_type} ({days} days)")
        return total_budget
        
    except Exception as e:
        logger.warning(f"Enhanced budget calculation failed: {str(e)}, falling back to legacy method")
        # Fallback to legacy calculation
        return _calculate_legacy_budget(event_type, days, base_budget)


def calculate_detailed_budget(event_type: str, days: int, total_budget: float,
                             guest_count: Optional[int] = None, venue_type: Optional[str] = None,
                             location: Optional[str] = None, religion: Optional[str] = None,
                             **kwargs) -> Dict[str, Any]:
    """
    Calculate detailed budget breakdown with category explanations.
    New API for enhanced budget features.
    
    Args:
        event_type: Type of event
        days: Number of days for the event
        total_budget: Total budget available
        guest_count: Number of guests
        venue_type: Type of venue
        location: Event location
        religion: Religious/cultural requirements
        **kwargs: Additional parameters
    
    Returns:
        Detailed budget breakdown with categories, explanations, and alternatives
    """
    try:
        # Create enhanced event context
        context = _create_budget_context(
            event_type=event_type,
            days=days,
            guest_count=guest_count,
            venue_type=venue_type,
            location=location,
            religion=religion,
            **kwargs
        )
        
        # Use allocation engine to get detailed breakdown
        allocation = budget_engine.allocate_budget(Decimal(str(total_budget)), context)
        
        # Convert to API-friendly format
        detailed_budget = _convert_allocation_to_api_format(allocation)
        
        logger.info(f"Generated detailed budget breakdown for {event_type}")
        return detailed_budget
        
    except Exception as e:
        logger.error(f"Error calculating detailed budget: {str(e)}")
        # Return basic breakdown as fallback
        return _generate_basic_budget_breakdown(event_type, total_budget)


def adjust_budget_for_modifications(current_allocation: Dict[str, Any], 
                                   modifications: Dict[str, float]) -> Dict[str, Any]:
    """
    Create budget adjustment APIs for user modifications.
    
    Args:
        current_allocation: Current budget allocation
        modifications: Dictionary of category modifications (category -> new_amount)
    
    Returns:
        Adjusted budget allocation with impact analysis
    """
    try:
        # Calculate total of modifications
        total_modifications = sum(modifications.values())
        original_total = current_allocation.get('total_budget', 0)
        
        # Create adjusted allocation
        adjusted_allocation = current_allocation.copy()
        adjusted_categories = adjusted_allocation.get('categories', {}).copy()
        
        # Apply modifications
        for category, new_amount in modifications.items():
            if category in adjusted_categories:
                old_amount = adjusted_categories[category]['amount']
                adjusted_categories[category]['amount'] = new_amount
                adjusted_categories[category]['percentage'] = (new_amount / original_total) * 100
                
                # Add modification note
                adjusted_categories[category]['modification_note'] = (
                    f"Adjusted from {old_amount:.2f} to {new_amount:.2f}"
                )
        
        # Calculate impact on other categories
        budget_difference = total_modifications - sum(
            current_allocation.get('categories', {}).get(cat, {}).get('amount', 0) 
            for cat in modifications.keys()
        )
        
        # Update total budget
        adjusted_allocation['total_budget'] = original_total + budget_difference
        adjusted_allocation['categories'] = adjusted_categories
        
        # Add impact analysis
        adjusted_allocation['modification_impact'] = {
            'budget_change': budget_difference,
            'modified_categories': list(modifications.keys()),
            'impact_analysis': _analyze_modification_impact(modifications, current_allocation)
        }
        
        logger.info(f"Applied budget modifications: {modifications}")
        return adjusted_allocation
        
    except Exception as e:
        logger.error(f"Error adjusting budget: {str(e)}")
        return current_allocation


def _create_budget_context(event_type: str, days: int, guest_count: Optional[int] = None,
                          venue_type: Optional[str] = None, location: Optional[str] = None,
                          religion: Optional[str] = None, **kwargs) -> EventContext:
    """Create EventContext for budget calculation"""
    
    # Parse event type
    try:
        event_type_enum = EventType(event_type.lower())
    except ValueError:
        event_type_enum = EventType.BIRTHDAY  # Default fallback
    
    # Parse venue type
    venue_type_enum = VenueType.INDOOR  # Default
    if venue_type:
        try:
            venue_type_enum = VenueType(venue_type.lower().replace(' ', '_'))
        except ValueError:
            pass
    
    # Parse cultural requirements
    cultural_requirements = []
    if religion:
        religion_normalized = religion.strip().lower()
        if religion_normalized in ["hindu", "hinduism"]:
            cultural_requirements.append(CulturalRequirement.HINDU)
        elif religion_normalized in ["muslim", "islam"]:
            cultural_requirements.append(CulturalRequirement.MUSLIM)
        elif religion_normalized in ["christian", "christianity"]:
            cultural_requirements.append(CulturalRequirement.CHRISTIAN)
        elif religion_normalized in ["sikh", "sikhism"]:
            cultural_requirements.append(CulturalRequirement.SIKH)
    
    # Create location object
    location_obj = Location(
        city=location or "Mumbai",
        state="Maharashtra",
        country="India",
        timezone="Asia/Kolkata"
    )
    
    # Estimate budget tier based on legacy calculation
    legacy_budget = _calculate_legacy_budget(event_type, days)
    per_person_budget = legacy_budget / (guest_count or 100)
    
    if per_person_budget < 2000:
        budget_tier = BudgetTier.LOW
    elif per_person_budget < 5000:
        budget_tier = BudgetTier.STANDARD
    elif per_person_budget < 12000:
        budget_tier = BudgetTier.PREMIUM
    else:
        budget_tier = BudgetTier.LUXURY
    
    # Create context
    context = EventContext(
        event_type=event_type_enum,
        guest_count=guest_count or 100,
        venue_type=venue_type_enum,
        cultural_requirements=cultural_requirements,
        budget_tier=budget_tier,
        location=location_obj,
        season=Season.WINTER,  # Default season
        duration_days=days,
        special_requirements=[],
        accessibility_requirements=[],
        complexity_score=0.0,  # Will be calculated by context analyzer
        weather_considerations=[]
    )
    
    # Return the context directly (complexity score will be calculated later if needed)
    return context


def _calculate_legacy_budget(event_type: str, days: int, base_budget: Optional[float] = None) -> float:
    """Legacy budget calculation method as fallback"""
    if base_budget:
        return base_budget
    
    base_rates = {
        "wedding": 5000,
        "birthday": 1000,
        "housewarming": 2000,
        "corporate": 3000,
        "anniversary": 3500,
        "engagement": 2500
    }
    rate = base_rates.get(event_type.lower(), 1500)
    return rate * days


def _convert_allocation_to_api_format(allocation) -> Dict[str, Any]:
    """Convert BudgetAllocation object to API-friendly format"""
    
    categories_dict = {}
    for category, cat_allocation in allocation.categories.items():
        categories_dict[category.value] = {
            'amount': float(cat_allocation.amount),
            'percentage': cat_allocation.percentage,
            'justification': cat_allocation.justification,
            'priority': cat_allocation.priority.value,
            'alternatives': [
                {
                    'name': alt.name,
                    'description': alt.description,
                    'cost_impact': float(alt.cost_impact),
                    'trade_offs': alt.trade_offs
                }
                for alt in cat_allocation.alternatives
            ]
        }
    
    return {
        'total_budget': float(allocation.total_budget),
        'categories': categories_dict,
        'per_person_cost': float(allocation.per_person_cost),
        'contingency_percentage': allocation.contingency_percentage,
        'regional_adjustments': allocation.regional_adjustments,
        'seasonal_adjustments': allocation.seasonal_adjustments
    }


def _generate_basic_budget_breakdown(event_type: str, total_budget: float) -> Dict[str, Any]:
    """Generate basic budget breakdown as fallback"""
    
    # Basic percentage allocations
    basic_allocations = {
        "wedding": {
            "venue": 25.0,
            "catering": 40.0,
            "decoration": 12.0,
            "entertainment": 8.0,
            "photography": 10.0,
            "transportation": 3.0,
            "miscellaneous": 2.0
        },
        "birthday": {
            "venue": 20.0,
            "catering": 35.0,
            "decoration": 15.0,
            "entertainment": 20.0,
            "photography": 5.0,
            "transportation": 3.0,
            "miscellaneous": 2.0
        }
    }
    
    allocations = basic_allocations.get(event_type.lower(), basic_allocations["birthday"])
    
    categories = {}
    for category, percentage in allocations.items():
        amount = total_budget * (percentage / 100)
        categories[category] = {
            'amount': amount,
            'percentage': percentage,
            'justification': f"Basic allocation for {category}",
            'priority': 'medium',
            'alternatives': []
        }
    
    return {
        'total_budget': total_budget,
        'categories': categories,
        'per_person_cost': total_budget / 100,  # Assume 100 guests
        'contingency_percentage': 10.0,
        'regional_adjustments': {},
        'seasonal_adjustments': {}
    }


def _analyze_modification_impact(modifications: Dict[str, float], 
                                current_allocation: Dict[str, Any]) -> List[str]:
    """Analyze the impact of budget modifications"""
    impact_analysis = []
    
    for category, new_amount in modifications.items():
        if category in current_allocation.get('categories', {}):
            old_amount = current_allocation['categories'][category]['amount']
            change = new_amount - old_amount
            change_percent = (change / old_amount) * 100 if old_amount > 0 else 0
            
            if change > 0:
                impact_analysis.append(
                    f"Increasing {category} by {change:.2f} ({change_percent:.1f}%) may improve quality but increases total budget"
                )
            else:
                impact_analysis.append(
                    f"Reducing {category} by {abs(change):.2f} ({abs(change_percent):.1f}%) may impact quality but saves budget"
                )
    
    return impact_analysis
