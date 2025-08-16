"""
Event Context Analyzer for intelligent timeline and budget system.

This module analyzes event parameters to determine complexity, requirements, and constraints
that influence timeline generation and budget allocation.
"""
import math
from typing import List, Dict, Tuple
from datetime import datetime, date

from ..models.core import EventContext, CriticalFactor, Location
from ..models.enums import (
    VenueType, BudgetTier, Season, EventType, CulturalRequirement,
    Priority, WeatherCondition, AccessibilityRequirement
)


class EventContextAnalyzer:
    """
    Analyzes event context to determine complexity scores and critical factors
    that influence timeline and budget planning.
    """
    
    # Base complexity scores for different event types
    EVENT_TYPE_COMPLEXITY = {
        EventType.WEDDING: 4.0,
        EventType.ENGAGEMENT: 3.0,
        EventType.ANNIVERSARY: 2.5,
        EventType.BIRTHDAY: 2.0,
        EventType.CORPORATE: 3.2,
        EventType.CONFERENCE: 3.5,
        EventType.GRADUATION: 2.2,
        EventType.BABY_SHOWER: 1.5,
        EventType.HOUSEWARMING: 1.8,
        EventType.FESTIVAL: 3.8,
    }
    
    # Venue type complexity multipliers
    VENUE_TYPE_MULTIPLIERS = {
        VenueType.OUTDOOR: 1.4,
        VenueType.BEACH: 1.6,
        VenueType.GARDEN: 1.3,
        VenueType.HOME: 1.1,
        VenueType.HYBRID: 1.5,
        VenueType.INDOOR: 1.0,
        VenueType.BANQUET_HALL: 0.9,
        VenueType.HOTEL: 0.8,
        VenueType.RESTAURANT: 0.7,
        VenueType.TEMPLE: 1.2,
        VenueType.CHURCH: 1.1,
        VenueType.COMMUNITY_CENTER: 0.9,
    }
    
    # Cultural requirement complexity additions
    CULTURAL_COMPLEXITY = {
        CulturalRequirement.HINDU: 1.0,
        CulturalRequirement.MUSLIM: 0.9,
        CulturalRequirement.SIKH: 0.95,
        CulturalRequirement.JEWISH: 0.85,
        CulturalRequirement.BUDDHIST: 0.75,
        CulturalRequirement.JAIN: 0.8,
        CulturalRequirement.CHRISTIAN: 0.65,
        CulturalRequirement.SECULAR: 0.2,
        CulturalRequirement.MIXED: 1.2,  # Highest complexity for mixed requirements
    }
    
    # Seasonal complexity adjustments
    SEASONAL_ADJUSTMENTS = {
        Season.SUMMER: 1.15,  # Heat, monsoon preparation
        Season.MONSOON: 1.4,  # Weather unpredictability
        Season.WINTER: 1.1,  # Cold weather considerations
        Season.SPRING: 1.0,  # Ideal season
        Season.AUTUMN: 1.05,  # Generally good but some weather concerns
    }
    
    # Guest count complexity scaling
    GUEST_COUNT_THRESHOLDS = [
        (50, 1.0),
        (100, 1.1),
        (200, 1.3),
        (500, 1.6),
        (1000, 2.0),
        (2000, 2.4),
        (float('inf'), 2.8)
    ]
    
    def analyze_context(self, event_params: Dict) -> EventContext:
        """
        Analyze event parameters and return enriched EventContext with complexity score.
        
        Args:
            event_params: Dictionary containing event parameters
            
        Returns:
            EventContext with calculated complexity score and analysis
        """
        # Create EventContext from parameters
        context = EventContext(
            event_type=EventType(event_params['event_type']),
            guest_count=event_params['guest_count'],
            venue_type=VenueType(event_params['venue_type']),
            cultural_requirements=[CulturalRequirement(req) for req in event_params.get('cultural_requirements', [])],
            budget_tier=BudgetTier(event_params['budget_tier']),
            location=Location(
                city=event_params['location']['city'],
                state=event_params['location']['state'],
                country=event_params['location']['country'],
                timezone=event_params['location']['timezone']
            ),
            season=Season(event_params['season']),
            duration_days=event_params['duration_days'],
            special_requirements=event_params.get('special_requirements', []),
            accessibility_requirements=[
                AccessibilityRequirement(req) for req in event_params.get('accessibility_requirements', [])
            ],
            weather_considerations=[
                WeatherCondition(cond) for cond in event_params.get('weather_considerations', [])
            ]
        )
        
        # Calculate complexity score
        context.complexity_score = self.determine_complexity_score(context)
        
        return context
    
    def determine_complexity_score(self, context: EventContext) -> float:
        """
        Calculate complexity score based on multiple factors.
        
        Args:
            context: EventContext to analyze
            
        Returns:
            Complexity score between 0.0 and 10.0
        """
        # Start with base complexity for event type
        base_score = self.EVENT_TYPE_COMPLEXITY.get(context.event_type, 5.0)
        
        # Apply venue type multiplier
        venue_multiplier = self.VENUE_TYPE_MULTIPLIERS.get(context.venue_type, 1.0)
        score = base_score * venue_multiplier
        
        # Add cultural complexity
        cultural_addition = 0.0
        for cultural_req in context.cultural_requirements:
            cultural_addition += self.CULTURAL_COMPLEXITY.get(cultural_req, 1.0)
        
        # If multiple cultural requirements, add extra complexity for coordination
        if len(context.cultural_requirements) > 1:
            cultural_addition *= 1.3
        
        score += cultural_addition
        
        # Apply guest count scaling
        guest_multiplier = self._get_guest_count_multiplier(context.guest_count)
        score *= guest_multiplier
        
        # Apply seasonal adjustments
        seasonal_multiplier = self.SEASONAL_ADJUSTMENTS.get(context.season, 1.0)
        score *= seasonal_multiplier
        
        # Add complexity for duration
        if context.duration_days > 1:
            duration_multiplier = 1.0 + (context.duration_days - 1) * 0.15
            score *= duration_multiplier
        
        # Add complexity for special requirements
        score += len(context.special_requirements) * 0.15
        
        # Add complexity for accessibility requirements
        score += len(context.accessibility_requirements) * 0.2
        
        # Add complexity for weather considerations
        score += len(context.weather_considerations) * 0.1
        
        # Budget tier adjustments (higher tier = more complexity due to expectations)
        budget_multipliers = {
            BudgetTier.LOW: 0.95,
            BudgetTier.STANDARD: 1.0,
            BudgetTier.PREMIUM: 1.1,
            BudgetTier.LUXURY: 1.2
        }
        score *= budget_multipliers.get(context.budget_tier, 1.0)
        
        # Ensure score is within bounds
        return min(max(score, 0.0), 10.0)
    
    def _get_guest_count_multiplier(self, guest_count: int) -> float:
        """Get complexity multiplier based on guest count."""
        for threshold, multiplier in self.GUEST_COUNT_THRESHOLDS:
            if guest_count <= threshold:
                return multiplier
        return self.GUEST_COUNT_THRESHOLDS[-1][1]
    
    def identify_critical_factors(self, context: EventContext) -> List[CriticalFactor]:
        """
        Identify critical factors that could significantly impact event success.
        
        Args:
            context: EventContext to analyze
            
        Returns:
            List of CriticalFactor objects ordered by impact level
        """
        factors = []
        
        # Weather-related factors for outdoor venues
        if context.venue_type in [VenueType.OUTDOOR, VenueType.BEACH, VenueType.GARDEN, VenueType.HYBRID]:
            if context.season == Season.MONSOON:
                factors.append(CriticalFactor(
                    name="Monsoon Weather Risk",
                    impact_level=Priority.CRITICAL,
                    description="High risk of rain disrupting outdoor activities",
                    mitigation_strategies=[
                        "Arrange waterproof tenting",
                        "Identify indoor backup venue",
                        "Plan flexible timeline with weather buffers",
                        "Communicate backup plans to all vendors"
                    ]
                ))
            elif WeatherCondition.RAINY in context.weather_considerations:
                factors.append(CriticalFactor(
                    name="Rain Contingency",
                    impact_level=Priority.HIGH,
                    description="Potential rain could affect outdoor setup and guest comfort",
                    mitigation_strategies=[
                        "Rent covered areas or tents",
                        "Prepare indoor activity alternatives",
                        "Ensure proper drainage at venue"
                    ]
                ))
        
        # Large guest count logistics
        if context.guest_count > 500:
            factors.append(CriticalFactor(
                name="Large Scale Logistics",
                impact_level=Priority.CRITICAL,
                description=f"Managing {context.guest_count} guests requires extensive coordination",
                mitigation_strategies=[
                    "Hire professional event coordinator",
                    "Implement guest flow management system",
                    "Arrange multiple entry/exit points",
                    "Plan staggered arrival times",
                    "Ensure adequate parking and transportation"
                ]
            ))
        elif context.guest_count > 200:
            factors.append(CriticalFactor(
                name="Medium Scale Coordination",
                impact_level=Priority.HIGH,
                description="Significant coordination needed for guest management",
                mitigation_strategies=[
                    "Designate area coordinators",
                    "Plan clear signage and directions",
                    "Arrange sufficient seating and facilities"
                ]
            ))
        
        # Cultural ceremony complexity
        if len(context.cultural_requirements) > 1:
            factors.append(CriticalFactor(
                name="Multi-Cultural Coordination",
                impact_level=Priority.HIGH,
                description="Balancing multiple cultural requirements and traditions",
                mitigation_strategies=[
                    "Consult with cultural experts for each tradition",
                    "Plan separate ceremony spaces if needed",
                    "Coordinate timing to respect all traditions",
                    "Ensure dietary requirements are met for all cultures"
                ]
            ))
        elif CulturalRequirement.HINDU in context.cultural_requirements:
            factors.append(CriticalFactor(
                name="Hindu Ceremony Timing",
                impact_level=Priority.HIGH,
                description="Hindu ceremonies require specific timing and ritual sequences",
                mitigation_strategies=[
                    "Consult with priest for auspicious timing",
                    "Prepare all ritual items in advance",
                    "Ensure proper ceremony space setup",
                    "Plan for extended ceremony duration"
                ]
            ))
        
        # Multi-day event complexity
        if context.duration_days > 3:
            factors.append(CriticalFactor(
                name="Extended Event Duration",
                impact_level=Priority.HIGH,
                description=f"{context.duration_days}-day event requires sustained coordination",
                mitigation_strategies=[
                    "Plan daily setup and cleanup schedules",
                    "Arrange accommodation for out-of-town guests",
                    "Coordinate vendor schedules across multiple days",
                    "Plan guest energy management and breaks"
                ]
            ))
        
        # Accessibility requirements
        if context.accessibility_requirements:
            factors.append(CriticalFactor(
                name="Accessibility Compliance",
                impact_level=Priority.HIGH,
                description="Ensuring event is accessible to all guests with special needs",
                mitigation_strategies=[
                    "Verify venue accessibility features",
                    "Arrange specialized transportation if needed",
                    "Plan accessible seating arrangements",
                    "Coordinate with accessibility service providers"
                ]
            ))
        
        # Budget tier vs complexity mismatch
        complexity_budget_mismatch = self._check_budget_complexity_mismatch(context)
        if complexity_budget_mismatch:
            factors.append(complexity_budget_mismatch)
        
        # Venue capacity concerns
        venue_capacity_factor = self._check_venue_capacity_concerns(context)
        if venue_capacity_factor:
            factors.append(venue_capacity_factor)
        
        # Sort factors by impact level (Critical first, then High, etc.)
        priority_order = {
            Priority.CRITICAL: 0,
            Priority.HIGH: 1,
            Priority.MEDIUM: 2,
            Priority.LOW: 3,
            Priority.OPTIONAL: 4
        }
        
        factors.sort(key=lambda f: priority_order.get(f.impact_level, 5))
        
        return factors
    
    def _check_budget_complexity_mismatch(self, context: EventContext) -> CriticalFactor:
        """Check if budget tier matches event complexity."""
        if context.complexity_score > 7.0 and context.budget_tier == BudgetTier.LOW:
            return CriticalFactor(
                name="Budget-Complexity Mismatch",
                impact_level=Priority.HIGH,
                description="High complexity event with low budget may compromise quality",
                mitigation_strategies=[
                    "Prioritize essential elements",
                    "Consider reducing guest count or duration",
                    "Explore cost-effective alternatives",
                    "Focus on high-impact, low-cost elements"
                ]
            )
        elif context.complexity_score < 3.0 and context.budget_tier == BudgetTier.LUXURY:
            return CriticalFactor(
                name="Over-budgeting Risk",
                impact_level=Priority.MEDIUM,
                description="Simple event with luxury budget may lead to unnecessary expenses",
                mitigation_strategies=[
                    "Focus on premium quality over quantity",
                    "Invest in memorable experiences",
                    "Consider upgrading key elements like venue or catering"
                ]
            )
        return None
    
    def _check_venue_capacity_concerns(self, context: EventContext) -> CriticalFactor:
        """Check for potential venue capacity issues."""
        # Estimate space requirements based on venue type and guest count
        space_per_guest = {
            VenueType.BANQUET_HALL: 8,  # sq ft per guest
            VenueType.RESTAURANT: 12,
            VenueType.HOTEL: 10,
            VenueType.OUTDOOR: 15,
            VenueType.GARDEN: 20,
            VenueType.BEACH: 25,
            VenueType.HOME: 6,
            VenueType.COMMUNITY_CENTER: 8,
            VenueType.TEMPLE: 5,
            VenueType.CHURCH: 6,
            VenueType.HYBRID: 12
        }
        
        required_space = space_per_guest.get(context.venue_type, 10) * context.guest_count
        
        if required_space > 5000:  # Large space requirement
            return CriticalFactor(
                name="Venue Capacity Planning",
                impact_level=Priority.HIGH,
                description=f"Event requires approximately {required_space} sq ft for {context.guest_count} guests",
                mitigation_strategies=[
                    "Verify venue capacity before booking",
                    "Plan efficient space utilization",
                    "Consider multiple areas or levels",
                    "Arrange overflow areas if needed"
                ]
            )
        
        return None
    
    def get_seasonal_considerations(self, context: EventContext) -> Dict[str, List[str]]:
        """
        Get seasonal considerations that affect planning.
        
        Args:
            context: EventContext to analyze
            
        Returns:
            Dictionary with seasonal considerations categorized by type
        """
        considerations = {
            "weather": [],
            "logistics": [],
            "costs": [],
            "availability": []
        }
        
        if context.season == Season.MONSOON:
            considerations["weather"].extend([
                "High probability of rain",
                "Humidity and heat concerns",
                "Potential flooding in low-lying areas"
            ])
            considerations["logistics"].extend([
                "Waterproof storage for equipment",
                "Covered transportation arrangements",
                "Backup power in case of outages"
            ])
            considerations["costs"].extend([
                "Premium for covered venues",
                "Additional cost for tenting/covering",
                "Higher transportation costs"
            ])
        
        elif context.season == Season.SUMMER:
            considerations["weather"].extend([
                "High temperatures",
                "Intense sunlight",
                "Potential heat waves"
            ])
            considerations["logistics"].extend([
                "Cooling arrangements for guests",
                "Shade structures for outdoor events",
                "Hydration stations"
            ])
            considerations["costs"].extend([
                "Air conditioning costs",
                "Cooling equipment rental",
                "Higher beverage requirements"
            ])
        
        elif context.season == Season.WINTER:
            considerations["weather"].extend([
                "Cold temperatures",
                "Potential fog affecting visibility",
                "Shorter daylight hours"
            ])
            considerations["logistics"].extend([
                "Heating arrangements",
                "Earlier event timing due to daylight",
                "Warm clothing considerations for outdoor portions"
            ])
        
        # Peak season availability and cost considerations
        peak_seasons = [Season.WINTER, Season.SPRING]  # Wedding peak seasons
        if context.season in peak_seasons and context.event_type == EventType.WEDDING:
            considerations["availability"].extend([
                "High demand for popular venues",
                "Limited vendor availability",
                "Need for early booking"
            ])
            considerations["costs"].extend([
                "Peak season pricing premiums",
                "Higher vendor rates",
                "Limited negotiation flexibility"
            ])
        
        return considerations
    
    def get_regional_considerations(self, context: EventContext) -> Dict[str, List[str]]:
        """
        Get regional considerations based on location.
        
        Args:
            context: EventContext to analyze
            
        Returns:
            Dictionary with regional considerations
        """
        considerations = {
            "cultural": [],
            "logistics": [],
            "costs": [],
            "regulations": []
        }
        
        # India-specific considerations
        if context.location.country.lower() == "india":
            considerations["cultural"].extend([
                "Local customs and traditions",
                "Regional language preferences",
                "Local festival calendar conflicts"
            ])
            considerations["logistics"].extend([
                "Traffic patterns in major cities",
                "Local transportation options",
                "Power backup requirements"
            ])
            considerations["regulations"].extend([
                "Local noise regulations",
                "Permit requirements for large gatherings",
                "Fire safety compliance"
            ])
            
            # Metro city specific considerations
            metro_cities = ["mumbai", "delhi", "bangalore", "chennai", "kolkata", "hyderabad", "pune"]
            if context.location.city.lower() in metro_cities:
                considerations["costs"].extend([
                    "Higher venue costs in metro areas",
                    "Premium vendor pricing",
                    "Parking and transportation premiums"
                ])
                considerations["logistics"].extend([
                    "Traffic congestion planning",
                    "Limited parking availability",
                    "Noise restrictions in residential areas"
                ])
        
        return considerations
    
    def analyze_venue_impact(self, context: EventContext) -> Dict[str, any]:
        """
        Analyze venue type impact on event planning.
        
        Args:
            context: EventContext to analyze
            
        Returns:
            Dictionary with venue impact analysis
        """
        venue_analysis = {
            "complexity_multiplier": self.VENUE_TYPE_MULTIPLIERS.get(context.venue_type, 1.0),
            "setup_requirements": [],
            "logistics_considerations": [],
            "cost_implications": [],
            "weather_vulnerability": "low",
            "accessibility_score": 0.0,
            "capacity_constraints": {},
            "vendor_requirements": []
        }
        
        # Venue-specific analysis
        if context.venue_type in [VenueType.OUTDOOR, VenueType.BEACH, VenueType.GARDEN]:
            venue_analysis["weather_vulnerability"] = "high"
            venue_analysis["setup_requirements"].extend([
                "Weather protection (tents/canopies)",
                "Ground covering/flooring",
                "Portable facilities (restrooms, power)",
                "Lighting arrangements",
                "Sound system with weather protection"
            ])
            venue_analysis["logistics_considerations"].extend([
                "Weather contingency planning",
                "Extended setup/breakdown time",
                "Equipment transportation challenges",
                "Guest comfort in outdoor conditions"
            ])
            venue_analysis["cost_implications"].extend([
                "Additional rental costs for weather protection",
                "Higher insurance requirements",
                "Extended vendor time for setup",
                "Backup venue costs"
            ])
            venue_analysis["vendor_requirements"].extend([
                "Weather-resistant equipment suppliers",
                "Tent/canopy rental services",
                "Portable facility providers",
                "Backup power suppliers"
            ])
            
        if context.venue_type == VenueType.BEACH:
            venue_analysis["setup_requirements"].extend([
                "Sand-appropriate flooring",
                "Wind-resistant decorations",
                "Tide schedule consideration",
                "Beach access permits"
            ])
            venue_analysis["logistics_considerations"].extend([
                "Limited vehicle access",
                "Sand cleanup requirements",
                "Tide timing coordination",
                "Guest footwear considerations"
            ])
            
        elif context.venue_type == VenueType.HOME:
            venue_analysis["setup_requirements"].extend([
                "Space optimization planning",
                "Furniture rearrangement",
                "Neighbor notification",
                "Parking arrangements"
            ])
            venue_analysis["logistics_considerations"].extend([
                "Limited space for large guest counts",
                "Noise restrictions",
                "Limited vendor access",
                "Cleanup and restoration"
            ])
            venue_analysis["cost_implications"].extend([
                "Potential damage deposits",
                "Additional cleaning costs",
                "Rental equipment for space expansion"
            ])
            
        elif context.venue_type in [VenueType.BANQUET_HALL, VenueType.HOTEL]:
            venue_analysis["weather_vulnerability"] = "low"
            venue_analysis["setup_requirements"].extend([
                "Venue decoration within guidelines",
                "Audio-visual equipment coordination",
                "Catering coordination with venue"
            ])
            venue_analysis["logistics_considerations"].extend([
                "Venue time restrictions",
                "Vendor coordination with venue staff",
                "Parking availability",
                "Multiple event coordination"
            ])
            venue_analysis["cost_implications"].extend([
                "Venue service charges",
                "Mandatory vendor restrictions",
                "Overtime charges for extended events"
            ])
            
        elif context.venue_type in [VenueType.TEMPLE, VenueType.CHURCH]:
            venue_analysis["setup_requirements"].extend([
                "Religious protocol compliance",
                "Limited decoration options",
                "Ceremony timing restrictions",
                "Sacred space respect"
            ])
            venue_analysis["logistics_considerations"].extend([
                "Religious calendar conflicts",
                "Dress code requirements",
                "Photography restrictions",
                "Ceremony duration limits"
            ])
            venue_analysis["vendor_requirements"].extend([
                "Religious ceremony specialists",
                "Culturally appropriate decorators",
                "Respectful photography services"
            ])
        
        # Calculate accessibility score
        venue_analysis["accessibility_score"] = self._calculate_venue_accessibility_score(context)
        
        # Determine capacity constraints
        venue_analysis["capacity_constraints"] = self._analyze_venue_capacity_constraints(context)
        
        return venue_analysis
    
    def analyze_location_impact(self, context: EventContext) -> Dict[str, any]:
        """
        Analyze location-based impact on event planning.
        
        Args:
            context: EventContext to analyze
            
        Returns:
            Dictionary with location impact analysis
        """
        location_analysis = {
            "cost_multiplier": 1.0,
            "vendor_availability": "standard",
            "logistics_complexity": "medium",
            "transportation_considerations": [],
            "accommodation_requirements": [],
            "local_regulations": [],
            "cultural_factors": [],
            "seasonal_impacts": [],
            "infrastructure_quality": "standard"
        }
        
        # Country-specific analysis
        if context.location.country.lower() == "india":
            location_analysis["cultural_factors"].extend([
                "Local customs and traditions",
                "Regional language preferences",
                "Festival calendar considerations",
                "Religious sensitivities"
            ])
            location_analysis["local_regulations"].extend([
                "Noise pollution guidelines",
                "Fire safety requirements",
                "Large gathering permits",
                "Alcohol serving regulations"
            ])
            
            # Metro city analysis
            metro_cities = ["mumbai", "delhi", "bangalore", "chennai", "kolkata", "hyderabad", "pune", "ahmedabad"]
            if context.location.city.lower() in metro_cities:
                location_analysis["cost_multiplier"] = 1.3
                location_analysis["vendor_availability"] = "high"
                location_analysis["logistics_complexity"] = "high"
                location_analysis["transportation_considerations"].extend([
                    "Traffic congestion planning",
                    "Limited parking availability",
                    "Public transport accessibility",
                    "Peak hour avoidance"
                ])
                location_analysis["accommodation_requirements"].extend([
                    "Hotel booking for out-of-town guests",
                    "Premium accommodation costs",
                    "Early booking requirements"
                ])
                location_analysis["infrastructure_quality"] = "high"
                
            # Tier-2 city analysis
            elif context.location.city.lower() in ["jaipur", "lucknow", "kanpur", "nagpur", "indore", "bhopal", "visakhapatnam", "patna"]:
                location_analysis["cost_multiplier"] = 1.1
                location_analysis["vendor_availability"] = "medium"
                location_analysis["logistics_complexity"] = "medium"
                location_analysis["infrastructure_quality"] = "medium"
                
            # Smaller cities/towns
            else:
                location_analysis["cost_multiplier"] = 0.9
                location_analysis["vendor_availability"] = "limited"
                location_analysis["logistics_complexity"] = "low"
                location_analysis["transportation_considerations"].extend([
                    "Limited vendor options",
                    "Potential vendor travel costs",
                    "Basic infrastructure considerations"
                ])
                location_analysis["infrastructure_quality"] = "basic"
        
        # Seasonal location impacts
        location_analysis["seasonal_impacts"] = self._get_seasonal_location_impacts(context)
        
        return location_analysis
    
    def _calculate_venue_accessibility_score(self, context: EventContext) -> float:
        """Calculate accessibility score for venue type."""
        base_scores = {
            VenueType.BANQUET_HALL: 8.0,
            VenueType.HOTEL: 9.0,
            VenueType.COMMUNITY_CENTER: 7.0,
            VenueType.RESTAURANT: 6.0,
            VenueType.TEMPLE: 5.0,
            VenueType.CHURCH: 6.0,
            VenueType.INDOOR: 7.0,
            VenueType.HOME: 3.0,
            VenueType.OUTDOOR: 2.0,
            VenueType.GARDEN: 3.0,
            VenueType.BEACH: 1.0,
            VenueType.HYBRID: 5.0
        }
        
        score = base_scores.get(context.venue_type, 5.0)
        
        # Adjust based on accessibility requirements
        if context.accessibility_requirements:
            # Venues with better infrastructure can better accommodate accessibility needs
            if context.venue_type in [VenueType.HOTEL, VenueType.BANQUET_HALL]:
                score += 1.0
            elif context.venue_type in [VenueType.OUTDOOR, VenueType.BEACH, VenueType.HOME]:
                score -= 2.0
        
        return min(max(score, 0.0), 10.0)
    
    def _analyze_venue_capacity_constraints(self, context: EventContext) -> Dict[str, any]:
        """Analyze capacity constraints for venue type."""
        # Space requirements per guest (in sq ft)
        space_requirements = {
            VenueType.BANQUET_HALL: {"seated": 8, "cocktail": 6, "dancing": 4},
            VenueType.RESTAURANT: {"seated": 12, "cocktail": 8, "dancing": 6},
            VenueType.HOTEL: {"seated": 10, "cocktail": 7, "dancing": 5},
            VenueType.OUTDOOR: {"seated": 15, "cocktail": 10, "dancing": 8},
            VenueType.GARDEN: {"seated": 20, "cocktail": 12, "dancing": 10},
            VenueType.BEACH: {"seated": 25, "cocktail": 15, "dancing": 12},
            VenueType.HOME: {"seated": 6, "cocktail": 4, "dancing": 3},
            VenueType.COMMUNITY_CENTER: {"seated": 8, "cocktail": 6, "dancing": 4},
            VenueType.TEMPLE: {"seated": 5, "cocktail": 4, "dancing": 3},
            VenueType.CHURCH: {"seated": 6, "cocktail": 5, "dancing": 4},
            VenueType.HYBRID: {"seated": 12, "cocktail": 8, "dancing": 6}
        }
        
        venue_space = space_requirements.get(context.venue_type, {"seated": 10, "cocktail": 7, "dancing": 5})
        
        constraints = {
            "min_space_required": {
                "seated_dinner": venue_space["seated"] * context.guest_count,
                "cocktail_reception": venue_space["cocktail"] * context.guest_count,
                "dancing_area": venue_space["dancing"] * context.guest_count
            },
            "capacity_warnings": [],
            "space_optimization_tips": []
        }
        
        total_space_needed = constraints["min_space_required"]["seated_dinner"]
        
        # Add capacity warnings based on guest count and venue type
        if context.guest_count > 500 and context.venue_type == VenueType.HOME:
            constraints["capacity_warnings"].append("Home venues typically cannot accommodate 500+ guests comfortably")
        elif context.guest_count > 200 and context.venue_type in [VenueType.RESTAURANT, VenueType.TEMPLE, VenueType.CHURCH]:
            constraints["capacity_warnings"].append(f"{context.venue_type.value} venues may have capacity limitations for 200+ guests")
        elif context.guest_count > 1000 and context.venue_type not in [VenueType.OUTDOOR, VenueType.BEACH, VenueType.BANQUET_HALL]:
            constraints["capacity_warnings"].append("Very large events (1000+ guests) require specialized large venues")
        
        # Add space optimization tips
        if total_space_needed > 5000:
            constraints["space_optimization_tips"].extend([
                "Consider multiple areas or levels",
                "Plan staggered seating arrangements",
                "Use outdoor spaces for cocktail reception",
                "Implement efficient traffic flow design"
            ])
        
        return constraints
    
    def _get_seasonal_location_impacts(self, context: EventContext) -> List[str]:
        """Get seasonal impacts specific to location."""
        impacts = []
        
        # India-specific seasonal impacts
        if context.location.country.lower() == "india":
            if context.season == Season.MONSOON:
                impacts.extend([
                    "Monsoon flooding risks in low-lying areas",
                    "Transportation disruptions due to heavy rains",
                    "Higher humidity affecting guest comfort",
                    "Potential power outages during storms"
                ])
            elif context.season == Season.SUMMER:
                impacts.extend([
                    "Extreme heat in northern regions",
                    "Dust storms in desert areas",
                    "Higher air conditioning costs",
                    "Guest comfort challenges for outdoor events"
                ])
            elif context.season == Season.WINTER:
                impacts.extend([
                    "Fog affecting transportation in northern regions",
                    "Cold weather considerations for outdoor events",
                    "Peak wedding season pricing",
                    "Higher demand for indoor venues"
                ])
        
        return impacts