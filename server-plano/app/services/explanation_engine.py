"""
Explanation Engine for providing detailed reasoning behind budget and timeline decisions.
"""
from typing import Dict, List, Any, Optional
from decimal import Decimal
import logging

from ..models.core import EventContext, BudgetAllocation, Timeline, CategoryAllocation
from ..models.enums import BudgetCategory, EventType, VenueType, BudgetTier, Season, Priority

logger = logging.getLogger(__name__)


class ExplanationEngine:
    """
    Generates detailed explanations for budget allocation and timeline decisions.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def explain_budget_allocation(self, allocation: BudgetAllocation, context: EventContext) -> Dict[str, Any]:
        """
        Generate detailed explanation for budget allocation decisions.
        
        Args:
            allocation: The budget allocation to explain
            context: Event context that influenced the allocation
            
        Returns:
            Dictionary with detailed explanations
        """
        try:
            explanation = {
                "total_budget_reasoning": self._explain_total_budget(allocation, context),
                "category_explanations": self._explain_categories(allocation, context),
                "contextual_factors": self._explain_contextual_factors(context),
                "optimization_rationale": self._explain_optimization_decisions(allocation, context),
                "risk_considerations": self._explain_risk_factors(allocation, context),
                "alternative_approaches": self._suggest_alternative_approaches(allocation, context)
            }
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error generating budget explanation: {str(e)}")
            import traceback
            traceback.print_exc()
            # Return a basic explanation structure even on error
            return {
                "error": f"Could not generate explanation: {str(e)}",
                "total_budget_reasoning": {
                    "total_amount": float(allocation.total_budget),
                    "per_person_cost": float(allocation.per_person_cost),
                    "budget_tier": context.budget_tier.value,
                    "tier_explanation": "Error generating detailed explanation"
                },
                "category_explanations": [],
                "contextual_factors": {},
                "optimization_rationale": [],
                "risk_considerations": [],
                "alternative_approaches": []
            }
    
    def explain_timeline_decisions(self, timeline: Timeline, context: EventContext) -> Dict[str, Any]:
        """
        Generate detailed explanation for timeline activity sequencing.
        
        Args:
            timeline: The timeline to explain
            context: Event context that influenced the timeline
            
        Returns:
            Dictionary with detailed explanations
        """
        try:
            explanation = {
                "sequencing_logic": self._explain_activity_sequencing(timeline, context),
                "duration_rationale": self._explain_duration_decisions(timeline, context),
                "cultural_considerations": self._explain_cultural_factors(timeline, context),
                "dependency_analysis": self._explain_dependencies(timeline),
                "buffer_time_reasoning": self._explain_buffer_times(timeline, context),
                "critical_path_explanation": self._explain_critical_path(timeline)
            }
            
            return explanation
            
        except Exception as e:
            self.logger.error(f"Error generating timeline explanation: {str(e)}")
            return {"error": f"Could not generate explanation: {str(e)}"}
    
    def _explain_total_budget(self, allocation: BudgetAllocation, context: EventContext) -> Dict[str, Any]:
        """Explain the total budget and per-person cost reasoning"""
        per_person = allocation.per_person_cost
        
        # Determine budget tier explanation
        tier_explanation = {
            BudgetTier.LOW: "Budget-conscious approach focusing on essential elements",
            BudgetTier.STANDARD: "Balanced approach with good quality across all categories",
            BudgetTier.PREMIUM: "Enhanced experience with premium vendors and services",
            BudgetTier.LUXURY: "Luxury experience with top-tier vendors and exclusive services"
        }
        
        # Regional cost context
        regional_factor = allocation.regional_adjustments.get('multiplier', 1.0)
        regional_explanation = ""
        if regional_factor > 1.1:
            regional_explanation = f"Costs adjusted upward by {(regional_factor-1)*100:.0f}% for {context.location.city} market rates"
        elif regional_factor < 0.9:
            regional_explanation = f"Costs adjusted downward by {(1-regional_factor)*100:.0f}% for {context.location.city} market rates"
        else:
            regional_explanation = f"Standard market rates applied for {context.location.city}"
        
        return {
            "total_amount": float(allocation.total_budget),
            "per_person_cost": float(per_person),
            "budget_tier": context.budget_tier.value,
            "tier_explanation": tier_explanation.get(context.budget_tier, "Standard approach"),
            "regional_context": regional_explanation,
            "guest_count_impact": self._explain_guest_count_impact(context.guest_count),
            "seasonal_impact": self._explain_seasonal_impact(context.season, allocation.seasonal_adjustments)
        }
    
    def _explain_categories(self, allocation: BudgetAllocation, context: EventContext) -> List[Dict[str, Any]]:
        """Explain each budget category allocation"""
        explanations = []
        
        for category, cat_allocation in allocation.categories.items():
            explanation = {
                "category": category.value,
                "amount": float(cat_allocation.amount),
                "percentage": cat_allocation.percentage,
                "priority": cat_allocation.priority.value,
                "reasoning": self._get_category_reasoning(category, cat_allocation, context),
                "factors_considered": self._get_category_factors(category, context),
                "industry_comparison": self._get_industry_comparison(category, cat_allocation.percentage, context.event_type),
                "optimization_notes": self._get_category_optimization_notes(category, context)
            }
            explanations.append(explanation)
        
        return sorted(explanations, key=lambda x: x["amount"], reverse=True)
    
    def _explain_contextual_factors(self, context: EventContext) -> Dict[str, Any]:
        """Explain how context influenced the allocation"""
        factors = {
            "event_type_impact": self._explain_event_type_impact(context.event_type),
            "venue_considerations": self._explain_venue_impact(context.venue_type),
            "guest_count_effects": self._explain_guest_count_effects(context.guest_count),
            "cultural_requirements": self._explain_cultural_impact(context.cultural_requirements),
            "seasonal_factors": self._explain_seasonal_factors(context.season),
            "duration_impact": self._explain_duration_impact(context.duration_days)
        }
        
        if context.special_requirements:
            factors["special_requirements"] = self._explain_special_requirements(context.special_requirements)
        
        if context.accessibility_requirements:
            factors["accessibility_considerations"] = self._explain_accessibility_impact(context.accessibility_requirements)
        
        return factors
    
    def _get_category_reasoning(self, category: BudgetCategory, allocation: CategoryAllocation, context: EventContext) -> str:
        """Get specific reasoning for a category allocation"""
        base_reasoning = {
            BudgetCategory.VENUE: f"Venue allocation reflects {context.venue_type.value} requirements for {context.guest_count} guests",
            BudgetCategory.CATERING: f"Catering budget scaled for {context.guest_count} guests with {context.budget_tier.value} tier service quality",
            BudgetCategory.DECORATION: f"Decoration allocation considers {context.event_type.value} aesthetic requirements and venue enhancement needs",
            BudgetCategory.ENTERTAINMENT: f"Entertainment budget reflects {context.event_type.value} celebration requirements and guest engagement needs",
            BudgetCategory.PHOTOGRAPHY: f"Photography allocation ensures professional documentation of {context.event_type.value} memories",
            BudgetCategory.TRANSPORTATION: f"Transportation budget accounts for guest logistics and vendor coordination needs",
            BudgetCategory.MISCELLANEOUS: f"Contingency allocation provides buffer for unexpected costs and minor items"
        }
        
        reasoning = base_reasoning.get(category, f"Standard allocation for {category.value}")
        
        # Add context-specific adjustments
        if context.venue_type == VenueType.OUTDOOR and category == BudgetCategory.MISCELLANEOUS:
            reasoning += ". Increased for outdoor event weather contingencies"
        
        if context.guest_count > 300 and category == BudgetCategory.TRANSPORTATION:
            reasoning += ". Enhanced for large event logistics coordination"
        
        if len(context.cultural_requirements) > 0 and category == BudgetCategory.DECORATION:
            reasoning += f". Adjusted for {', '.join([req.value for req in context.cultural_requirements])} cultural elements"
        
        return reasoning
    
    def _get_category_factors(self, category: BudgetCategory, context: EventContext) -> List[str]:
        """Get factors that influenced a specific category"""
        factors = []
        
        # Common factors
        factors.append(f"Event type: {context.event_type.value}")
        factors.append(f"Guest count: {context.guest_count}")
        factors.append(f"Budget tier: {context.budget_tier.value}")
        
        # Category-specific factors
        if category == BudgetCategory.VENUE:
            factors.extend([
                f"Venue type: {context.venue_type.value}",
                f"Location: {context.location.city}",
                f"Duration: {context.duration_days} days"
            ])
        
        elif category == BudgetCategory.CATERING:
            factors.extend([
                f"Per-person catering needs",
                f"Service style requirements",
                f"Cultural dietary considerations"
            ])
        
        elif category == BudgetCategory.DECORATION:
            factors.extend([
                f"Venue decoration requirements",
                f"Cultural theme elements",
                f"Seasonal flower availability"
            ])
        
        elif category == BudgetCategory.ENTERTAINMENT:
            factors.extend([
                f"Event celebration style",
                f"Guest demographic preferences",
                f"Cultural entertainment traditions"
            ])
        
        return factors
    
    def _get_industry_comparison(self, category: BudgetCategory, percentage: float, event_type: EventType) -> str:
        """Compare allocation percentage to industry standards"""
        # Industry standard ranges by event type
        standards = {
            EventType.WEDDING: {
                BudgetCategory.VENUE: (20, 30),
                BudgetCategory.CATERING: (35, 45),
                BudgetCategory.DECORATION: (10, 20),
                BudgetCategory.PHOTOGRAPHY: (8, 15),
                BudgetCategory.ENTERTAINMENT: (5, 12),
                BudgetCategory.TRANSPORTATION: (2, 8),
                BudgetCategory.MISCELLANEOUS: (5, 15)
            },
            EventType.CORPORATE: {
                BudgetCategory.VENUE: (25, 35),
                BudgetCategory.CATERING: (20, 35),
                BudgetCategory.ENTERTAINMENT: (10, 20),
                BudgetCategory.PHOTOGRAPHY: (5, 12),
                BudgetCategory.TRANSPORTATION: (8, 15),
                BudgetCategory.MISCELLANEOUS: (5, 10)
            }
        }
        
        if event_type not in standards or category not in standards[event_type]:
            return "Within typical range for this event type"
        
        min_pct, max_pct = standards[event_type][category]
        
        if percentage < min_pct:
            return f"Below typical range ({min_pct}-{max_pct}%) - optimized for budget efficiency"
        elif percentage > max_pct:
            return f"Above typical range ({min_pct}-{max_pct}%) - enhanced allocation for quality"
        else:
            return f"Within industry standard range ({min_pct}-{max_pct}%)"
    
    def _get_category_optimization_notes(self, category: BudgetCategory, context: EventContext) -> List[str]:
        """Get optimization notes for a category"""
        notes = []
        
        if category == BudgetCategory.VENUE and context.venue_type == VenueType.OUTDOOR:
            notes.append("Consider weather protection costs in venue planning")
        
        if category == BudgetCategory.CATERING and context.guest_count > 200:
            notes.append("Bulk catering discounts may be available for large guest count")
        
        if category == BudgetCategory.DECORATION and context.season == Season.WINTER:
            notes.append("Peak season may affect flower and decoration costs")
        
        if category == BudgetCategory.ENTERTAINMENT and len(context.cultural_requirements) > 0:
            notes.append("Cultural entertainment specialists may command premium pricing")
        
        return notes
    
    def _explain_guest_count_impact(self, guest_count: int) -> str:
        """Explain how guest count affects budget"""
        if guest_count < 50:
            return "Small intimate gathering allows focus on premium per-person experiences"
        elif guest_count < 150:
            return "Medium-sized event with balanced cost efficiency and personal attention"
        elif guest_count < 300:
            return "Large event requiring significant coordination and logistics planning"
        else:
            return "Very large event with complex logistics and potential for bulk service discounts"
    
    def _explain_seasonal_impact(self, season: Season, seasonal_adjustments: Dict) -> str:
        """Explain seasonal cost impacts"""
        seasonal_effects = {
            Season.WINTER: "Peak wedding season in India - higher vendor demand and pricing",
            Season.SPRING: "Pleasant weather season with moderate vendor availability",
            Season.SUMMER: "Hot weather season - lower demand for outdoor events, potential savings",
            Season.MONSOON: "Monsoon season - lowest vendor demand, significant cost savings possible",
            Season.AUTUMN: "Post-monsoon season - good weather returning, moderate pricing"
        }
        
        base_explanation = seasonal_effects.get(season, "Standard seasonal pricing")
        
        if seasonal_adjustments:
            adjustment_details = []
            for factor, impact in seasonal_adjustments.items():
                if isinstance(impact, (int, float)) and impact != 1.0:
                    change = (impact - 1) * 100
                    adjustment_details.append(f"{factor}: {change:+.0f}%")
            
            if adjustment_details:
                base_explanation += f". Specific adjustments: {', '.join(adjustment_details)}"
        
        return base_explanation
    
    def _explain_event_type_impact(self, event_type: EventType) -> str:
        """Explain how event type influences allocation"""
        explanations = {
            EventType.WEDDING: "Weddings typically require higher catering and decoration budgets for ceremonial significance",
            EventType.CORPORATE: "Corporate events emphasize venue quality and professional services over decorative elements",
            EventType.BIRTHDAY: "Birthday celebrations focus on entertainment and catering with moderate decoration needs",
            EventType.ANNIVERSARY: "Anniversary events balance intimate atmosphere with celebration requirements"
        }
        
        return explanations.get(event_type, f"{event_type.value} events have specific allocation patterns")
    
    def _explain_venue_impact(self, venue_type: VenueType) -> str:
        """Explain venue type impact on budget"""
        impacts = {
            VenueType.OUTDOOR: "Outdoor venues require additional weather protection, power, and logistics costs",
            VenueType.INDOOR: "Indoor venues provide controlled environment with standard service requirements",
            VenueType.HOME: "Home venues reduce venue costs but increase decoration and setup requirements",
            VenueType.HOTEL: "Hotel venues offer comprehensive services but at premium pricing",
            VenueType.BANQUET_HALL: "Banquet halls provide dedicated event space with standard amenities"
        }
        
        return impacts.get(venue_type, f"{venue_type.value} venues have specific cost implications")
    
    def _explain_guest_count_effects(self, guest_count: int) -> List[str]:
        """Explain specific effects of guest count on different categories"""
        effects = []
        
        if guest_count > 200:
            effects.extend([
                "Venue costs increase due to space requirements",
                "Catering benefits from bulk pricing efficiencies",
                "Transportation coordination becomes more complex",
                "Photography may require multiple professionals"
            ])
        elif guest_count < 50:
            effects.extend([
                "Venue costs optimized for intimate settings",
                "Catering focuses on premium per-person experiences",
                "Decoration can be more detailed and personalized",
                "Single photographer typically sufficient"
            ])
        else:
            effects.append("Moderate guest count allows balanced allocation across categories")
        
        return effects
    
    def _explain_cultural_impact(self, cultural_requirements: List) -> List[str]:
        """Explain how cultural requirements affect budget"""
        if not cultural_requirements:
            return ["No specific cultural requirements - standard allocation applied"]
        
        impacts = []
        for requirement in cultural_requirements:
            if hasattr(requirement, 'value'):
                req_name = requirement.value
                if req_name == "hindu":
                    impacts.extend([
                        "Hindu ceremonies require specialized priests and ritual items",
                        "Traditional decorations with flowers and rangoli increase decoration costs",
                        "Multiple ceremony days may extend venue and catering needs"
                    ])
                elif req_name == "muslim":
                    impacts.extend([
                        "Islamic ceremonies require halal catering considerations",
                        "Nikah ceremony setup requires specific arrangements",
                        "Gender-separated arrangements may affect venue layout"
                    ])
                elif req_name == "christian":
                    impacts.extend([
                        "Church ceremony coordination may require additional planning",
                        "Reception setup follows ceremony requirements",
                        "Traditional music and decoration elements"
                    ])
                else:
                    impacts.append(f"{req_name} cultural requirements considered in planning")
        
        return impacts
    
    def _explain_seasonal_factors(self, season: Season) -> List[str]:
        """Explain seasonal factors affecting budget"""
        factors = {
            Season.WINTER: [
                "Peak wedding season increases vendor demand",
                "Flower prices at seasonal high",
                "Premium venue booking rates",
                "Higher photographer availability costs"
            ],
            Season.SPRING: [
                "Pleasant weather reduces contingency needs",
                "Seasonal flowers available at moderate prices",
                "Good vendor availability",
                "Optimal conditions for outdoor elements"
            ],
            Season.SUMMER: [
                "Hot weather increases cooling costs",
                "Lower demand for outdoor venues creates savings opportunities",
                "Indoor venue preference affects allocation",
                "Hydration and comfort considerations"
            ],
            Season.MONSOON: [
                "Weather contingency planning essential",
                "Indoor venue requirements increase costs",
                "Transportation challenges affect logistics budget",
                "Lowest vendor demand creates cost savings"
            ],
            Season.AUTUMN: [
                "Post-monsoon recovery period",
                "Moderate weather conditions",
                "Festival season affects vendor availability",
                "Good balance of cost and weather factors"
            ]
        }
        
        return factors.get(season, ["Standard seasonal considerations applied"])
    
    def _explain_duration_impact(self, duration_days: int) -> str:
        """Explain how event duration affects budget"""
        if duration_days == 1:
            return "Single-day event allows concentrated resource allocation"
        elif duration_days <= 3:
            return "Multi-day event requires extended venue, catering, and coordination costs"
        else:
            return "Extended duration event requires significant logistics and accommodation planning"
    
    def _explain_special_requirements(self, requirements: List[str]) -> List[str]:
        """Explain impact of special requirements"""
        explanations = []
        for req in requirements:
            if "accessibility" in req.lower():
                explanations.append("Accessibility features may require specialized vendors and equipment")
            elif "dietary" in req.lower():
                explanations.append("Special dietary needs affect catering planning and costs")
            elif "security" in req.lower():
                explanations.append("Security requirements add specialized service costs")
            else:
                explanations.append(f"Special requirement '{req}' considered in planning")
        
        return explanations
    
    def _explain_accessibility_impact(self, requirements: List) -> List[str]:
        """Explain accessibility requirement impacts"""
        impacts = []
        for req in requirements:
            if hasattr(req, 'value'):
                req_name = req.value
                if "wheelchair" in req_name:
                    impacts.append("Wheelchair accessibility requires ramp access and accessible facilities")
                elif "hearing" in req_name:
                    impacts.append("Hearing assistance requires audio equipment and sign language services")
                elif "visual" in req_name:
                    impacts.append("Visual assistance requires tactile guides and audio descriptions")
                else:
                    impacts.append(f"Accessibility requirement '{req_name}' adds specialized service needs")
        
        return impacts
    
    def _explain_optimization_decisions(self, allocation: BudgetAllocation, context: EventContext) -> List[str]:
        """Explain key optimization decisions made"""
        decisions = []
        
        # Analyze allocation patterns
        total_budget = allocation.total_budget
        venue_pct = next((cat_alloc.percentage for cat, cat_alloc in allocation.categories.items() 
                         if cat == BudgetCategory.VENUE), 0)
        catering_pct = next((cat_alloc.percentage for cat, cat_alloc in allocation.categories.items() 
                           if cat == BudgetCategory.CATERING), 0)
        
        if venue_pct > 30:
            decisions.append("Venue allocation prioritized for premium location and facilities")
        elif venue_pct < 15:
            decisions.append("Venue costs optimized to allocate more budget to experience elements")
        
        if catering_pct > 40:
            decisions.append("Catering emphasized as central element of guest experience")
        elif catering_pct < 25:
            decisions.append("Catering optimized to balance cost with other priority areas")
        
        # Context-based decisions
        if context.guest_count > 300:
            decisions.append("Large event logistics prioritized in allocation strategy")
        
        if context.venue_type == VenueType.OUTDOOR:
            decisions.append("Weather contingency planning factored into allocation")
        
        if len(context.cultural_requirements) > 0:
            decisions.append("Cultural authenticity prioritized in vendor and service selection")
        
        return decisions
    
    def _explain_risk_factors(self, allocation: BudgetAllocation, context: EventContext) -> List[str]:
        """Explain risk factors considered in allocation"""
        risks = []
        
        # Budget-based risks
        contingency_pct = allocation.contingency_percentage
        if contingency_pct > 15:
            risks.append("High contingency allocation due to event complexity and uncertainty factors")
        elif contingency_pct < 5:
            risks.append("Low contingency allocation assumes stable conditions and reliable vendors")
        
        # Context-based risks
        if context.venue_type == VenueType.OUTDOOR:
            risks.append("Weather risk mitigation factored into allocation")
        
        if context.season == Season.WINTER:
            risks.append("Peak season vendor availability risk considered")
        elif context.season == Season.MONSOON:
            risks.append("Weather-related logistics risks addressed in planning")
        
        if context.guest_count > 400:
            risks.append("Large event coordination complexity risk managed through enhanced planning")
        
        if context.duration_days > 3:
            risks.append("Extended event duration risks addressed through detailed timeline planning")
        
        return risks
    
    def _suggest_alternative_approaches(self, allocation: BudgetAllocation, context: EventContext) -> List[Dict[str, Any]]:
        """Suggest alternative allocation approaches"""
        alternatives = []
        
        # Budget-conscious alternative
        alternatives.append({
            "name": "Budget-Conscious Approach",
            "description": "Reduce costs while maintaining quality",
            "key_changes": [
                "Optimize venue selection for value",
                "Choose buffet over plated service",
                "Focus on essential photography coverage",
                "Simplify decoration themes"
            ],
            "estimated_savings": "15-25%",
            "trade_offs": ["Reduced luxury elements", "Simpler service style"]
        })
        
        # Premium experience alternative
        alternatives.append({
            "name": "Premium Experience Approach",
            "description": "Enhance guest experience with premium services",
            "key_changes": [
                "Upgrade to luxury venue",
                "Add premium catering options",
                "Include comprehensive photography/videography",
                "Enhance decoration and ambiance"
            ],
            "estimated_cost_increase": "20-35%",
            "benefits": ["Enhanced guest experience", "Premium service quality", "Lasting memories"]
        })
        
        # Balanced reallocation alternative
        if context.event_type == EventType.WEDDING:
            alternatives.append({
                "name": "Experience-Focused Reallocation",
                "description": "Prioritize guest experience over traditional allocations",
                "key_changes": [
                    "Increase entertainment budget for memorable experiences",
                    "Enhance catering with interactive stations",
                    "Reduce venue costs by choosing unique but affordable locations",
                    "Invest in professional coordination services"
                ],
                "philosophy": "Create unforgettable experiences rather than traditional displays"
            })
        
        return alternatives
    
    # Timeline explanation methods
    def _explain_activity_sequencing(self, timeline: Timeline, context: EventContext) -> List[str]:
        """Explain the logic behind activity sequencing"""
        explanations = []
        
        explanations.append("Activities sequenced based on logical dependencies and cultural traditions")
        
        if context.event_type == EventType.WEDDING:
            explanations.extend([
                "Pre-wedding ceremonies scheduled before main wedding day",
                "Setup activities planned with adequate time before guest arrival",
                "Cultural ceremonies follow traditional sequence and timing",
                "Reception activities flow naturally from ceremony conclusion"
            ])
        
        explanations.append("Buffer times included between major activities for smooth transitions")
        explanations.append("Vendor coordination activities scheduled to minimize conflicts")
        
        return explanations
    
    def _explain_duration_decisions(self, timeline: Timeline, context: EventContext) -> List[str]:
        """Explain duration decisions for activities"""
        explanations = []
        
        explanations.append("Activity durations based on guest count and cultural requirements")
        
        if context.guest_count > 200:
            explanations.append("Extended durations for large guest count logistics")
        
        if len(context.cultural_requirements) > 0:
            explanations.append("Cultural ceremony durations follow traditional practices")
        
        explanations.append("Setup and breakdown times calculated for venue and vendor requirements")
        
        return explanations
    
    def _explain_cultural_factors(self, timeline: Timeline, context: EventContext) -> List[str]:
        """Explain cultural considerations in timeline"""
        if not context.cultural_requirements:
            return ["No specific cultural requirements - standard timeline applied"]
        
        factors = []
        for requirement in context.cultural_requirements:
            if hasattr(requirement, 'value'):
                req_name = requirement.value
                if req_name == "hindu":
                    factors.extend([
                        "Hindu ceremonies follow traditional muhurat (auspicious timing)",
                        "Multiple ceremony days accommodate various rituals",
                        "Sacred fire ceremonies require specific setup time"
                    ])
                elif req_name == "muslim":
                    factors.extend([
                        "Nikah ceremony timing follows Islamic traditions",
                        "Prayer times considered in scheduling",
                        "Halal catering preparation time allocated"
                    ])
        
        return factors
    
    def _explain_dependencies(self, timeline: Timeline) -> List[str]:
        """Explain activity dependencies"""
        explanations = [
            "Critical path activities identified and prioritized",
            "Setup activities must complete before guest activities",
            "Vendor coordination scheduled to avoid conflicts",
            "Cleanup activities planned after all guest activities"
        ]
        
        if hasattr(timeline, 'critical_path') and timeline.critical_path:
            explanations.append(f"Critical path contains {len(timeline.critical_path)} essential activities")
        
        return explanations
    
    def _explain_buffer_times(self, timeline: Timeline, context: EventContext) -> List[str]:
        """Explain buffer time reasoning"""
        explanations = []
        
        if context.complexity_score > 7:
            explanations.append("Extended buffer times for high complexity event")
        elif context.complexity_score < 3:
            explanations.append("Standard buffer times for straightforward event")
        else:
            explanations.append("Moderate buffer times for balanced event complexity")
        
        if context.venue_type == VenueType.OUTDOOR:
            explanations.append("Additional buffer time for weather contingencies")
        
        if context.guest_count > 300:
            explanations.append("Extended buffer times for large guest coordination")
        
        return explanations
    
    def _explain_critical_path(self, timeline: Timeline) -> List[str]:
        """Explain critical path activities"""
        explanations = [
            "Critical path represents activities that cannot be delayed without affecting the event",
            "These activities receive priority in resource allocation and scheduling"
        ]
        
        if hasattr(timeline, 'critical_path') and timeline.critical_path:
            critical_activities = [activity.name for activity in timeline.critical_path[:3]]
            explanations.append(f"Key critical activities include: {', '.join(critical_activities)}")
        
        return explanations