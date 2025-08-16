from typing import Dict, List, Optional, Any
from app.utils.supabase_client import SupabaseClient
from app.services.timeline_generator import generate_timeline, generate_deep_dive_for_day
from app.services.vendor_search import search_vendors
from app.services.budget_calculator import calculate_budget, calculate_detailed_budget
from app.utils.helpers import days_between
from datetime import datetime
import logging

# Import new intelligence engines
try:
    from app.services.timeline_intelligence_engine import TimelineIntelligenceEngine
    from app.services.budget_allocation_engine import BudgetAllocationEngine
    from app.services.event_context_analyzer import EventContextAnalyzer
    from app.models.core import EventContext, Location
    from app.models.enums import EventType, VenueType, BudgetTier, CulturalRequirement, Season, BudgetCategory
    from decimal import Decimal
    ENHANCED_ENGINES_AVAILABLE = True
except ImportError as e:
    ENHANCED_ENGINES_AVAILABLE = False
    logging.warning(f"Enhanced engines not available: {e}")

logger = logging.getLogger(__name__)

class EventService:
    def __init__(self):
        self.supabase = SupabaseClient()
        
        # Initialize enhanced intelligence engines if available
        if ENHANCED_ENGINES_AVAILABLE:
            self.timeline_engine = TimelineIntelligenceEngine()
            self.budget_engine = BudgetAllocationEngine()
            self.context_analyzer = EventContextAnalyzer()
        else:
            self.timeline_engine = None
            self.budget_engine = None
            self.context_analyzer = None

    async def create_event(self, user_id: str, event_data: Dict) -> Dict:
        """Create a complete event with enhanced timeline and budget intelligence"""
        
        # Extract basic data
        event_type = event_data["event_type"]
        
        # Validate event type
        valid_event_types = [e.value for e in EventType] if ENHANCED_ENGINES_AVAILABLE else [
            'wedding', 'birthday', 'anniversary', 'housewarming', 'corporate', 
            'graduation', 'baby_shower', 'engagement', 'festival', 'conference'
        ]
        
        if event_type not in valid_event_types:
            raise Exception(f"Input validation failed: Invalid event_type: must be one of {valid_event_types}")
        
        start_date = event_data["start_date"]
        end_date = event_data.get("end_date")
        location = event_data["location"]
        religion = event_data.get("religion")
        budget = event_data.get("budget")
        
        # Extract enhanced context parameters
        guest_count = event_data.get("guest_count", 100)
        venue_type = event_data.get("venue_type", "indoor")
        special_requirements = event_data.get("special_requirements", [])
        accessibility_requirements = event_data.get("accessibility_requirements", [])
        weather_considerations = event_data.get("weather_considerations", [])

        # Calculate days
        try:
            days_count = days_between(start_date, end_date) if end_date else 1
        except:
            days_count = 1
        
        # Create enhanced event context if engines are available
        if ENHANCED_ENGINES_AVAILABLE and self.context_analyzer:
            try:
                context = self._create_enhanced_context(
                    event_type=event_type,
                    guest_count=guest_count,
                    venue_type=venue_type,
                    location=location,
                    religion=religion,
                    budget=budget,
                    days_count=days_count,
                    special_requirements=special_requirements,
                    accessibility_requirements=accessibility_requirements,
                    weather_considerations=weather_considerations
                )
                
                # Use enhanced budget calculation
                if budget:
                    estimated_budget = float(budget)
                else:
                    # Use budget engine to estimate realistic budget
                    base_budget = self._estimate_base_budget(context)
                    allocation = self.budget_engine.allocate_budget(base_budget, context)
                    estimated_budget = float(allocation.total_budget)
                
                logger.info(f"Enhanced event creation with complexity score: {context.complexity_score}")
                
            except Exception as e:
                logger.warning(f"Enhanced context creation failed: {str(e)}, using legacy method")
                # Fallback to legacy budget calculation
                estimated_budget = calculate_budget(
                    event_type=event_type, 
                    days=days_count, 
                    base_budget=budget,
                    guest_count=guest_count,
                    venue_type=venue_type,
                    location=location,
                    religion=religion
                )
        else:
            # Use legacy budget calculation
            estimated_budget = calculate_budget(
                event_type=event_type, 
                days=days_count, 
                base_budget=budget,
                guest_count=guest_count,
                venue_type=venue_type,
                location=location,
                religion=religion
            )

        # Create event record with enhanced data
        event_record = self.supabase.create_event(user_id, {
            "event_type": event_type,
            "start_date": start_date,
            "end_date": end_date,
            "location": location,
            "budget": budget,
            "religion": religion,
            "estimated_budget": estimated_budget,
            "guest_count": guest_count,
            "venue_type": venue_type,
            "special_requirements": special_requirements,
            "accessibility_requirements": accessibility_requirements,
            "weather_considerations": weather_considerations
        })

        if not event_record:
            raise Exception("Failed to create event")

        event_id = event_record["id"]

        # Generate enhanced timeline with contextual parameters
        timeline = generate_timeline(
            event_type=event_type,
            start_date=start_date,
            end_date=end_date,
            religion=religion,
            budget=budget,
            guest_count=guest_count,
            venue_type=venue_type,
            location=location,
            special_requirements=special_requirements,
            accessibility_requirements=accessibility_requirements,
            weather_considerations=weather_considerations
        )

        # Save timeline days to database with enhanced formatting
        event_days = []
        for day_data in timeline:
            event_days.append({
                "event_id": event_id,
                "day_number": day_data["day"],
                "date": day_data["date"],
                "summary": day_data["summary"],
                "estimated_cost": day_data.get("estimated_cost"),
                "details": day_data.get("details", []),
                "notes": day_data.get("notes", []),
                "contingency_plans": day_data.get("contingency_plans", [])
            })

        self.supabase.create_event_days(event_days)

        # Search and save vendors
        vendors_raw = search_vendors(event_type, location)
        vendors = []
        if vendors_raw:
            for vendor in vendors_raw:
                vendors.append({
                    "event_id": event_id,
                    "title": vendor.get("title", ""),
                    "url": vendor.get("url"),
                    "snippet": vendor.get("snippet", ""),
                    "search_query": f"{event_type} vendors near {location}",
                    "source": "tavily"
                })
            
            self.supabase.create_vendors(vendors)

        # Create enhanced response with additional context
        response = {
            "event_id": event_id,
            "timeline": timeline,
            "vendors": [{"title": v["title"], "url": v["url"], "snippet": v["snippet"]} for v in vendors],
            "estimated_budget": estimated_budget,
            "event_details": event_record
        }
        
        # Add enhanced context information if available
        if ENHANCED_ENGINES_AVAILABLE and 'context' in locals():
            response["context_analysis"] = {
                "complexity_score": context.complexity_score,
                "critical_factors": [factor.name for factor in self.context_analyzer.identify_critical_factors(context)[:3]],
                "guest_count_category": self._categorize_guest_count(guest_count),
                "venue_complexity": self._get_venue_complexity(venue_type)
            }

        return response

    async def get_event_timeline(self, event_id: int, user_id: str) -> Dict:
        """Get event timeline from database"""
        # Verify ownership
        if not self.supabase.verify_user_owns_event(event_id, user_id):
            raise Exception("Event not found or access denied")

        # Get event details
        event = self.supabase.get_event(event_id, user_id)
        if not event:
            raise Exception("Event not found")

        # Get timeline days
        days = self.supabase.get_event_days(event_id)
        
        # Get vendors
        vendors = self.supabase.get_event_vendors(event_id)

        return {
            "event_id": event_id,
            "event_details": event,
            "timeline": days,
            "vendors": [{"title": v["title"], "url": v["url"], "snippet": v["snippet"]} for v in vendors],
            "estimated_budget": event["estimated_budget"]
        }

    async def get_deep_dive(self, event_id: int, day_number: int, user_id: str) -> Dict:
        """Get or generate deep dive for a specific day"""
        # Verify ownership
        if not self.supabase.verify_user_owns_event(event_id, user_id):
            raise Exception("Event not found or access denied")

        # Get event and day data
        event = self.supabase.get_event(event_id, user_id)
        day_data = self.supabase.get_event_day(event_id, day_number)
        
        if not event or not day_data:
            raise Exception("Event or day not found")

        # Check if deep dive already exists
        if day_data.get("deep_dive_data"):
            return {
                "event_id": event_id,
                "day_number": day_number,
                "deep_dive": day_data["deep_dive_data"]
            }

        # Generate new enhanced deep dive with contextual parameters
        deep_dive = generate_deep_dive_for_day(
            event_type=event["event_type"],
            start_date=event["start_date"],
            end_date=event["end_date"] or event["start_date"],
            religion=event.get("religion"),
            day_number=day_number,
            budget=event.get("budget"),
            guest_count=event.get("guest_count"),
            venue_type=event.get("venue_type"),
            location=event.get("location")
        )

        # Cache the deep dive
        self.supabase.update_event_day_deep_dive(event_id, day_number, deep_dive)

        return {
            "event_id": event_id,
            "day_number": day_number,
            "deep_dive": deep_dive
        }

    async def get_user_events(self, user_id: str) -> List[Dict]:
        """Get all events for a user"""
        return self.supabase.get_user_events(user_id)

    async def get_detailed_budget(self, event_id: int, user_id: str) -> Dict:
        """Get enhanced detailed budget breakdown for an event"""
        # Verify ownership
        if not self.supabase.verify_user_owns_event(event_id, user_id):
            raise Exception("Event not found or access denied")

        # Get event details
        event = self.supabase.get_event(event_id, user_id)
        if not event:
            raise Exception("Event not found")

        # Calculate days
        try:
            days_count = days_between(event["start_date"], event.get("end_date")) if event.get("end_date") else 1
        except:
            days_count = 1

        # Get enhanced detailed budget breakdown
        detailed_budget = calculate_detailed_budget(
            event_type=event["event_type"],
            days=days_count,
            total_budget=float(event.get("budget", event.get("estimated_budget", 10000))),
            guest_count=event.get("guest_count"),
            venue_type=event.get("venue_type"),
            location=event.get("location"),
            religion=event.get("religion"),
            special_requirements=event.get("special_requirements", []),
            accessibility_requirements=event.get("accessibility_requirements", []),
            weather_considerations=event.get("weather_considerations", [])
        )

        # Add enhanced budget analysis if engines are available
        if ENHANCED_ENGINES_AVAILABLE and self.budget_engine and self.context_analyzer:
            try:
                # Create context for enhanced analysis
                context = self._create_enhanced_context(
                    event_type=event["event_type"],
                    guest_count=event.get("guest_count", 100),
                    venue_type=event.get("venue_type", "indoor"),
                    location=event.get("location", "Mumbai"),
                    religion=event.get("religion"),
                    budget=float(event.get("budget", event.get("estimated_budget", 10000))),
                    days_count=days_count,
                    special_requirements=event.get("special_requirements", []),
                    accessibility_requirements=event.get("accessibility_requirements", []),
                    weather_considerations=event.get("weather_considerations", [])
                )
                
                # Add enhanced analysis
                detailed_budget["enhanced_analysis"] = {
                    "complexity_impact": self._analyze_complexity_impact(context),
                    "seasonal_considerations": self.context_analyzer.get_seasonal_considerations(context),
                    "regional_factors": self.context_analyzer.get_regional_considerations(context),
                    "venue_impact": self.context_analyzer.analyze_venue_impact(context),
                    "optimization_suggestions": self._get_budget_optimization_suggestions(context, detailed_budget)
                }
                
                logger.info(f"Enhanced budget analysis completed for event {event_id}")
                
            except Exception as e:
                logger.warning(f"Enhanced budget analysis failed: {str(e)}")

        return {
            "event_id": event_id,
            "event_details": event,
            "detailed_budget": detailed_budget
        }

    def _analyze_complexity_impact(self, context: EventContext) -> Dict[str, Any]:
        """Analyze how complexity affects budget allocation"""
        
        complexity_analysis = {
            "score": context.complexity_score,
            "level": "low" if context.complexity_score < 3 else 
                    "medium" if context.complexity_score < 6 else
                    "high" if context.complexity_score < 8 else "very_high",
            "factors": [],
            "budget_implications": []
        }
        
        # Identify complexity factors
        if context.guest_count > 200:
            complexity_analysis["factors"].append("Large guest count requires extensive coordination")
            complexity_analysis["budget_implications"].append("Higher logistics and coordination costs")
        
        if context.venue_type in [VenueType.OUTDOOR, VenueType.BEACH]:
            complexity_analysis["factors"].append("Outdoor venue increases weather risks")
            complexity_analysis["budget_implications"].append("Additional weather protection and contingency costs")
        
        if len(context.cultural_requirements) > 1:
            complexity_analysis["factors"].append("Multiple cultural requirements need coordination")
            complexity_analysis["budget_implications"].append("Specialized vendors and extended timeline costs")
        
        if context.duration_days > 3:
            complexity_analysis["factors"].append("Extended duration increases coordination complexity")
            complexity_analysis["budget_implications"].append("Multi-day logistics and accommodation costs")
        
        return complexity_analysis

    def _get_budget_optimization_suggestions(self, context: EventContext, 
                                           detailed_budget: Dict[str, Any]) -> List[str]:
        """Get budget optimization suggestions based on context"""
        
        suggestions = []
        
        # Budget tier specific suggestions
        if context.budget_tier == BudgetTier.LOW:
            suggestions.extend([
                "Consider DIY decorations to reduce decoration costs",
                "Opt for buffet-style catering instead of plated service",
                "Use family/friends for coordination to reduce vendor costs",
                "Choose off-peak dates for better vendor rates"
            ])
        elif context.budget_tier == BudgetTier.PREMIUM:
            suggestions.extend([
                "Invest in premium photography for lasting memories",
                "Consider luxury transportation for VIP guests",
                "Upgrade to premium venue with inclusive services",
                "Add signature experiences like live cooking stations"
            ])
        
        # Venue specific suggestions
        if context.venue_type == VenueType.OUTDOOR:
            suggestions.extend([
                "Allocate 15-20% extra budget for weather contingencies",
                "Consider tent rental for weather protection",
                "Budget for additional power and lighting requirements"
            ])
        elif context.venue_type == VenueType.HOME:
            suggestions.extend([
                "Reduce venue costs but increase decoration budget",
                "Consider furniture rental for additional seating",
                "Budget for professional cleaning services"
            ])
        
        # Guest count specific suggestions
        if context.guest_count > 300:
            suggestions.extend([
                "Consider multiple smaller venues instead of one large venue",
                "Implement staggered arrival times to manage crowd flow",
                "Budget for professional crowd management services"
            ])
        elif context.guest_count < 50:
            suggestions.extend([
                "Focus budget on premium experiences rather than scale",
                "Consider intimate venue options for better per-person value",
                "Invest in personalized touches and premium services"
            ])
        
        return suggestions[:6]  # Limit to top 6 suggestions

    # New enhanced API methods for explanations and alternatives

    async def get_budget_explanation(self, event_id: int, user_id: str) -> Dict[str, Any]:
        """Get detailed explanation of budget allocation decisions"""
        # Verify ownership
        if not self.supabase.verify_user_owns_event(event_id, user_id):
            raise Exception("Event not found or access denied")

        # Get event details
        event = self.supabase.get_event(event_id, user_id)
        if not event:
            raise Exception("Event not found")

        # Get detailed budget
        budget_result = await self.get_detailed_budget(event_id, user_id)
        detailed_budget = budget_result["detailed_budget"]

        # Create explanation response
        categories_explanation = []
        if "categories" in detailed_budget:
            for category, details in detailed_budget["categories"].items():
                explanation = {
                    "category": category,
                    "amount": details["amount"],
                    "percentage": details["percentage"],
                    "justification": details["justification"],
                    "priority": details["priority"],
                    "factors_considered": self._get_category_factors(category, event)
                }
                categories_explanation.append(explanation)

        # Get complexity analysis
        complexity_analysis = detailed_budget.get("enhanced_analysis", {}).get("complexity_impact", {})
        regional_factors = detailed_budget.get("enhanced_analysis", {}).get("regional_factors", {})
        seasonal_considerations = detailed_budget.get("enhanced_analysis", {}).get("seasonal_considerations", {})
        optimization_suggestions = detailed_budget.get("enhanced_analysis", {}).get("optimization_suggestions", [])

        return {
            "event_id": event_id,
            "total_budget": detailed_budget["total_budget"],
            "categories": categories_explanation,
            "complexity_analysis": complexity_analysis,
            "regional_factors": regional_factors,
            "seasonal_considerations": seasonal_considerations,
            "optimization_suggestions": optimization_suggestions
        }

    async def get_timeline_reasoning(self, event_id: int, user_id: str) -> Dict[str, Any]:
        """Get detailed reasoning behind timeline activity sequencing"""
        # Verify ownership
        if not self.supabase.verify_user_owns_event(event_id, user_id):
            raise Exception("Event not found or access denied")

        # Get event and timeline data
        event = self.supabase.get_event(event_id, user_id)
        timeline_days = self.supabase.get_event_days(event_id)
        
        if not event or not timeline_days:
            raise Exception("Event or timeline not found")

        # Create timeline explanations
        timeline_explanations = []
        for day in timeline_days:
            # Get deep dive for detailed activity information
            try:
                deep_dive = await self.get_deep_dive(event_id, day["day_number"], user_id)
                deep_dive_data = deep_dive.get("deep_dive", {})
                
                activities = []
                if "schedule" in deep_dive_data:
                    for activity in deep_dive_data["schedule"]:
                        activities.append({
                            "time": activity.get("time", "TBD"),
                            "activity": activity.get("activity", ""),
                            "description": activity.get("description", ""),
                            "duration": activity.get("duration", ""),
                            "priority": activity.get("priority", "medium"),
                            "vendors_needed": activity.get("vendors_needed", []),
                            "estimated_cost": activity.get("estimated_cost", 0.0)
                        })

                explanation = {
                    "day": day["day_number"],
                    "date": day["date"],
                    "activities": activities,
                    "reasoning": self._get_timeline_reasoning(day, event),
                    "dependencies": self._get_activity_dependencies(day),
                    "buffer_time_explanation": self._get_buffer_time_explanation(event),
                    "cultural_considerations": deep_dive_data.get("cultural_considerations", [])
                }
                timeline_explanations.append(explanation)
                
            except Exception as e:
                logger.warning(f"Could not get deep dive for day {day['day_number']}: {str(e)}")
                # Create basic explanation
                explanation = {
                    "day": day["day_number"],
                    "date": day["date"],
                    "activities": [],
                    "reasoning": [f"Day {day['day_number']} activities based on {event['event_type']} requirements"],
                    "dependencies": [],
                    "buffer_time_explanation": "Standard buffer times applied",
                    "cultural_considerations": []
                }
                timeline_explanations.append(explanation)

        return {
            "event_id": event_id,
            "timeline_explanations": timeline_explanations,
            "overall_strategy": self._get_overall_timeline_strategy(event),
            "critical_path": self._get_critical_path_explanation(event),
            "contingency_plans": self._get_contingency_plans(event)
        }

    async def get_alternatives(self, event_id: int, user_id: str) -> Dict[str, Any]:
        """Get alternative timeline and budget options"""
        # Verify ownership
        if not self.supabase.verify_user_owns_event(event_id, user_id):
            raise Exception("Event not found or access denied")

        # Get event details
        event = self.supabase.get_event(event_id, user_id)
        if not event:
            raise Exception("Event not found")

        # Generate timeline alternatives
        timeline_alternatives = self._generate_timeline_alternatives(event)
        
        # Generate budget alternatives
        budget_alternatives = self._generate_budget_alternatives(event)
        
        # Generate recommendations
        recommendations = self._generate_alternative_recommendations(event, timeline_alternatives, budget_alternatives)

        return {
            "event_id": event_id,
            "timeline_alternatives": timeline_alternatives,
            "budget_alternatives": budget_alternatives,
            "recommendations": recommendations
        }

    async def modify_budget_allocation(self, event_id: int, user_id: str, modification_data: Dict[str, Any]) -> Dict[str, Any]:
        """Modify budget allocation and get impact analysis"""
        # Verify ownership
        if not self.supabase.verify_user_owns_event(event_id, user_id):
            raise Exception("Event not found or access denied")

        # Get current budget allocation
        budget_result = await self.get_detailed_budget(event_id, user_id)
        current_allocation = budget_result["detailed_budget"]

        # Apply modifications using budget calculator
        from app.services.budget_calculator import adjust_budget_for_modifications
        
        try:
            updated_allocation = adjust_budget_for_modifications(
                current_allocation, 
                modification_data["category_changes"]
            )
            
            # Generate impact analysis
            impact_analysis = updated_allocation.get("modification_impact", {}).get("impact_analysis", [])
            
            # Check for warnings
            warnings = self._check_modification_warnings(modification_data, current_allocation)
            
            return {
                "event_id": event_id,
                "updated_allocation": updated_allocation,
                "impact_analysis": impact_analysis,
                "warnings": warnings
            }
            
        except Exception as e:
            logger.error(f"Error modifying budget allocation: {str(e)}")
            raise Exception(f"Failed to modify budget allocation: {str(e)}")

    async def submit_feedback(self, event_id: int, user_id: str, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Submit user feedback for pattern learning"""
        # Verify ownership
        if not self.supabase.verify_user_owns_event(event_id, user_id):
            raise Exception("Event not found or access denied")

        try:
            # Store feedback in database
            feedback_record = {
                "event_id": event_id,
                "user_id": user_id,
                "timeline_rating": feedback_data["timeline_rating"],
                "budget_accuracy": feedback_data["budget_accuracy"],
                "vendor_quality": feedback_data["vendor_quality"],
                "overall_satisfaction": feedback_data["overall_satisfaction"],
                "comments": feedback_data.get("comments"),
                "improvements_suggested": feedback_data.get("improvements_suggested", []),
                "would_recommend": feedback_data["would_recommend"],
                "created_at": datetime.now().isoformat()
            }
            
            # Save to database (assuming supabase has a feedback table)
            feedback_id = self.supabase.create_feedback(feedback_record)
            
            # Process feedback for pattern learning if enhanced engines are available
            learning_impact = "Feedback recorded for future improvements"
            if ENHANCED_ENGINES_AVAILABLE and hasattr(self, 'pattern_learning_system'):
                try:
                    # Process feedback through pattern learning system
                    learning_impact = self._process_feedback_for_learning(event_id, feedback_data)
                except Exception as e:
                    logger.warning(f"Pattern learning processing failed: {str(e)}")
            
            return {
                "message": "Feedback submitted successfully",
                "feedback_id": feedback_id,
                "learning_impact": learning_impact
            }
            
        except Exception as e:
            logger.error(f"Error submitting feedback: {str(e)}")
            raise Exception(f"Failed to submit feedback: {str(e)}")

    async def get_timeline_alternatives(self, event_id: int, user_id: str, approach: str) -> Dict[str, Any]:
        """Generate alternative timeline approaches"""
        # Verify ownership
        if not self.supabase.verify_user_owns_event(event_id, user_id):
            raise Exception("Event not found or access denied")

        # Get event details
        event = self.supabase.get_event(event_id, user_id)
        if not event:
            raise Exception("Event not found")

        # Generate alternatives based on approach
        alternatives = self._generate_approach_based_alternatives(event, approach)
        
        return {
            "event_id": event_id,
            "approach": approach,
            "alternatives": alternatives,
            "recommendations": self._get_approach_recommendations(approach)
        }

    async def get_budget_alternatives(self, event_id: int, user_id: str, scenario: str) -> Dict[str, Any]:
        """Generate alternative budget allocation scenarios"""
        # Verify ownership
        if not self.supabase.verify_user_owns_event(event_id, user_id):
            raise Exception("Event not found or access denied")

        # Get event details
        event = self.supabase.get_event(event_id, user_id)
        if not event:
            raise Exception("Event not found")

        # Generate budget scenarios
        scenarios = self._generate_budget_scenarios(event, scenario)
        
        return {
            "event_id": event_id,
            "scenario": scenario,
            "alternatives": scenarios,
            "recommendations": self._get_scenario_recommendations(scenario)
        }

    def _create_enhanced_context(self, event_type: str, guest_count: int, venue_type: str,
                                location: str, religion: Optional[str], budget: Optional[float],
                                days_count: int, special_requirements: List[str],
                                accessibility_requirements: List[str], 
                                weather_considerations: List[str]) -> EventContext:
        """Create enhanced EventContext from event parameters"""
        
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
        location_parts = location.split(',') if isinstance(location, str) else [str(location)]
        location_obj = Location(
            city=location_parts[0].strip() if location_parts else "Mumbai",
            state=location_parts[1].strip() if len(location_parts) > 1 else "Maharashtra",
            country="India",
            timezone="Asia/Kolkata"
        )
        
        # Determine budget tier
        budget_tier = BudgetTier.STANDARD  # Default
        if budget and guest_count:
            per_person_budget = budget / guest_count
            if per_person_budget < 2000:
                budget_tier = BudgetTier.LOW
            elif per_person_budget < 5000:
                budget_tier = BudgetTier.STANDARD
            elif per_person_budget < 12000:
                budget_tier = BudgetTier.PREMIUM
            else:
                budget_tier = BudgetTier.LUXURY
        
        # Determine season based on current date
        current_month = datetime.now().month
        if current_month in [12, 1, 2]:
            season = Season.WINTER
        elif current_month in [3, 4, 5]:
            season = Season.SPRING
        elif current_month in [6, 7, 8]:
            season = Season.SUMMER
        elif current_month in [9, 10, 11]:
            season = Season.AUTUMN
        else:
            season = Season.SPRING  # Default
        
        # Create EventContext object
        context = EventContext(
            event_type=event_type_enum,
            guest_count=guest_count,
            venue_type=venue_type_enum,
            location=location_obj,
            cultural_requirements=cultural_requirements,
            budget_tier=budget_tier,
            season=season,
            duration_days=days_count,
            special_requirements=special_requirements,
            accessibility_requirements=[],  # Convert strings to enums if needed
            weather_considerations=[],  # Convert strings to enums if needed
            complexity_score=0.0
        )
        
        # Use context analyzer to analyze and enhance context
        if self.context_analyzer:
            context = self.context_analyzer.analyze_context(context)
        
        return context

    def _estimate_base_budget(self, context: EventContext) -> Decimal:
        """Estimate base budget based on event context"""
        
        # Base budget rates per person by event type
        base_rates = {
            EventType.WEDDING: 8000,
            EventType.BIRTHDAY: 1500,
            EventType.CORPORATE: 3000,
            EventType.ANNIVERSARY: 4000,
            EventType.ENGAGEMENT: 3500,
            EventType.HOUSEWARMING: 2000
        }
        
        base_rate = base_rates.get(context.event_type, 2000)
        
        # Adjust for guest count
        base_budget = base_rate * context.guest_count
        
        # Adjust for duration
        if context.duration_days > 1:
            base_budget *= (1 + (context.duration_days - 1) * 0.6)
        
        # Adjust for venue type
        venue_multipliers = {
            VenueType.OUTDOOR: 1.3,
            VenueType.HOTEL: 1.4,
            VenueType.BANQUET_HALL: 1.1,
            VenueType.HOME: 0.7,
            VenueType.INDOOR: 1.0
        }
        
        multiplier = venue_multipliers.get(context.venue_type, 1.0)
        base_budget *= multiplier
        
        # Adjust for complexity
        if context.complexity_score > 7:
            base_budget *= 1.3
        elif context.complexity_score > 5:
            base_budget *= 1.15
        
        return Decimal(str(base_budget))

    def _categorize_guest_count(self, guest_count: int) -> str:
        """Categorize guest count for context analysis"""
        if guest_count <= 50:
            return "intimate"
        elif guest_count <= 150:
            return "medium"
        elif guest_count <= 300:
            return "large"
        else:
            return "very_large"

    def _get_venue_complexity(self, venue_type: str) -> str:
        """Get venue complexity level"""
        complexity_map = {
            "outdoor": "high",
            "beach": "very_high",
            "garden": "high",
            "home": "medium",
            "hybrid": "high",
            "indoor": "low",
            "banquet_hall": "low",
            "hotel": "low",
            "restaurant": "low"
        }
        
        return complexity_map.get(venue_type.lower(), "medium")

    # Helper methods for new API endpoints

    def _get_category_factors(self, category: str, event: Dict[str, Any]) -> List[str]:
        """Get factors considered for budget category allocation"""
        factors = []
        
        guest_count = event.get("guest_count", 100)
        venue_type = event.get("venue_type", "indoor")
        event_type = event.get("event_type", "birthday")
        
        if category == "venue":
            factors.extend([
                f"Guest count: {guest_count} people",
                f"Venue type: {venue_type}",
                f"Event type: {event_type}"
            ])
        elif category == "catering":
            factors.extend([
                f"Per-person catering for {guest_count} guests",
                f"Event type dietary requirements: {event_type}",
                "Regional food preferences considered"
            ])
        elif category == "decoration":
            factors.extend([
                f"Venue decoration requirements: {venue_type}",
                f"Event theme: {event_type}",
                "Seasonal decoration availability"
            ])
        elif category == "entertainment":
            factors.extend([
                f"Entertainment suitable for {guest_count} guests",
                f"Event type entertainment: {event_type}",
                "Cultural preferences considered"
            ])
        elif category == "photography":
            factors.extend([
                f"Coverage for {guest_count} guests",
                f"Event duration and complexity",
                "Professional documentation requirements"
            ])
        
        return factors

    def _get_timeline_reasoning(self, day: Dict[str, Any], event: Dict[str, Any]) -> List[str]:
        """Get reasoning for timeline day structure"""
        reasoning = []
        
        day_number = day["day_number"]
        event_type = event.get("event_type", "birthday")
        guest_count = event.get("guest_count", 100)
        
        if day_number == 1:
            reasoning.extend([
                "First day focuses on setup and preparation activities",
                f"Timeline optimized for {event_type} event requirements",
                f"Activities scheduled considering {guest_count} guests"
            ])
        elif day_number == 2:
            reasoning.extend([
                "Main event day with core ceremonies and activities",
                "Peak guest attendance and engagement activities",
                "Critical timeline coordination required"
            ])
        else:
            reasoning.extend([
                "Continuation or wrap-up activities",
                "Cleanup and restoration activities",
                "Guest departure coordination"
            ])
        
        return reasoning

    def _get_activity_dependencies(self, day: Dict[str, Any]) -> List[str]:
        """Get activity dependencies for the day"""
        dependencies = [
            "Venue setup must complete before guest arrival",
            "Photography setup depends on decoration completion",
            "Catering service depends on guest count confirmation",
            "Entertainment setup requires sound system installation"
        ]
        return dependencies

    def _get_buffer_time_explanation(self, event: Dict[str, Any]) -> str:
        """Get explanation for buffer time allocation"""
        guest_count = event.get("guest_count", 100)
        venue_type = event.get("venue_type", "indoor")
        
        if guest_count > 200:
            return f"Extended buffer times for large event ({guest_count} guests) coordination"
        elif venue_type == "outdoor":
            return "Additional buffer time for outdoor venue weather contingencies"
        else:
            return "Standard buffer times for smooth activity transitions"

    def _get_overall_timeline_strategy(self, event: Dict[str, Any]) -> str:
        """Get overall timeline strategy explanation"""
        event_type = event.get("event_type", "birthday")
        guest_count = event.get("guest_count", 100)
        
        if event_type == "wedding":
            return "Multi-day wedding timeline with traditional ceremony sequences and guest experience optimization"
        elif guest_count > 200:
            return "Large-scale event strategy with crowd management and logistics coordination"
        else:
            return f"Intimate {event_type} timeline focused on personal experience and smooth execution"

    def _get_critical_path_explanation(self, event: Dict[str, Any]) -> List[str]:
        """Get critical path activities explanation"""
        return [
            "Venue booking and confirmation",
            "Catering arrangements and menu finalization",
            "Guest invitation and RSVP management",
            "Vendor coordination and timeline synchronization",
            "Day-of event coordination and execution"
        ]

    def _get_contingency_plans(self, event: Dict[str, Any]) -> List[str]:
        """Get contingency plans for the event"""
        plans = [
            "Backup vendor contacts for critical services",
            "Weather contingency for outdoor elements",
            "Timeline flexibility for unexpected delays"
        ]
        
        venue_type = event.get("venue_type", "indoor")
        if venue_type == "outdoor":
            plans.extend([
                "Indoor backup venue arrangement",
                "Weather monitoring and decision protocols"
            ])
        
        return plans

    def _generate_timeline_alternatives(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate timeline alternatives"""
        alternatives = []
        
        # Fast-track alternative
        alternatives.append({
            "name": "Fast-Track Timeline",
            "description": "Compressed timeline with parallel activities",
            "timeline_changes": [
                "Combine setup activities to save 2 hours",
                "Parallel vendor coordination",
                "Streamlined ceremony sequences"
            ],
            "cost_impact": -500.0,
            "time_savings": "4-6 hours total",
            "trade_offs": [
                "Less buffer time for delays",
                "Higher coordination complexity",
                "Potential stress on vendors"
            ]
        })
        
        # Premium alternative
        alternatives.append({
            "name": "Premium Experience Timeline",
            "description": "Extended timeline with luxury touches",
            "timeline_changes": [
                "Extended preparation time for premium setup",
                "Additional entertainment segments",
                "Professional coordination throughout"
            ],
            "cost_impact": 2000.0,
            "time_savings": None,
            "trade_offs": [
                "Higher budget requirements",
                "Longer event duration",
                "Premium vendor requirements"
            ]
        })
        
        return alternatives

    def _generate_budget_alternatives(self, event: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate budget alternatives"""
        alternatives = []
        
        # Budget-conscious alternative
        alternatives.append({
            "name": "Budget-Conscious Allocation",
            "description": "Cost-optimized budget distribution",
            "category_changes": {
                "venue": -1000.0,
                "catering": -1500.0,
                "decoration": -500.0,
                "entertainment": -300.0
            },
            "total_budget_change": -3300.0,
            "impact_analysis": [
                "Simpler venue options",
                "Buffet-style catering",
                "DIY decoration elements",
                "Playlist instead of live entertainment"
            ]
        })
        
        # Premium alternative
        alternatives.append({
            "name": "Premium Experience Allocation",
            "description": "Luxury-focused budget distribution",
            "category_changes": {
                "venue": 2000.0,
                "catering": 3000.0,
                "entertainment": 1500.0,
                "photography": 1000.0
            },
            "total_budget_change": 7500.0,
            "impact_analysis": [
                "Premium venue with full services",
                "Multi-course plated dining",
                "Live entertainment and performances",
                "Professional photography and videography"
            ]
        })
        
        return alternatives

    def _generate_alternative_recommendations(self, event: Dict[str, Any], 
                                           timeline_alternatives: List[Dict[str, Any]], 
                                           budget_alternatives: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations for alternatives"""
        recommendations = []
        
        guest_count = event.get("guest_count", 100)
        budget = event.get("budget", 10000)
        
        if guest_count > 200:
            recommendations.append("Consider fast-track timeline for large events to manage logistics")
        
        if budget and budget < 50000:
            recommendations.append("Budget-conscious allocation recommended for cost optimization")
        elif budget and budget > 100000:
            recommendations.append("Premium experience allocation can enhance guest satisfaction")
        
        recommendations.extend([
            "Review trade-offs carefully before selecting alternatives",
            "Consider hybrid approaches combining elements from different alternatives",
            "Consult with vendors about feasibility of timeline changes"
        ])
        
        return recommendations

    def _check_modification_warnings(self, modification_data: Dict[str, Any], 
                                   current_allocation: Dict[str, Any]) -> List[str]:
        """Check for warnings in budget modifications"""
        warnings = []
        
        category_changes = modification_data.get("category_changes", {})
        
        for category, new_amount in category_changes.items():
            if category in current_allocation.get("categories", {}):
                current_amount = current_allocation["categories"][category]["amount"]
                change_percent = ((new_amount - current_amount) / current_amount) * 100
                
                if change_percent < -50:
                    warnings.append(f"Reducing {category} by {abs(change_percent):.1f}% may significantly impact quality")
                elif change_percent > 100:
                    warnings.append(f"Increasing {category} by {change_percent:.1f}% may be excessive")
        
        return warnings

    def _process_feedback_for_learning(self, event_id: int, feedback_data: Dict[str, Any]) -> str:
        """Process feedback for pattern learning system"""
        # This would integrate with the pattern learning system
        # For now, return a simple message
        overall_rating = feedback_data.get("overall_satisfaction", 3)
        
        if overall_rating >= 4:
            return "Positive feedback will reinforce successful patterns for similar events"
        elif overall_rating <= 2:
            return "Feedback will help identify areas for improvement in future recommendations"
        else:
            return "Feedback will contribute to pattern refinement and optimization"

    def _generate_approach_based_alternatives(self, event: Dict[str, Any], approach: str) -> List[Dict[str, Any]]:
        """Generate alternatives based on specific approach"""
        alternatives = []
        
        if approach == "fast":
            alternatives.extend([
                {
                    "name": "Express Setup",
                    "description": "Minimal setup time with pre-arranged elements",
                    "changes": ["Pre-decorated venue", "Ready-to-serve catering", "Simplified timeline"],
                    "time_saved": "3-4 hours",
                    "trade_offs": ["Limited customization", "Higher per-item costs"]
                }
            ])
        elif approach == "premium":
            alternatives.extend([
                {
                    "name": "Luxury Experience",
                    "description": "High-end services and extended timeline",
                    "changes": ["Premium venue services", "Multi-course dining", "Extended entertainment"],
                    "time_saved": None,
                    "trade_offs": ["Significantly higher budget", "Longer event duration"]
                }
            ])
        elif approach == "budget":
            alternatives.extend([
                {
                    "name": "Cost-Effective Planning",
                    "description": "Optimized for budget consciousness",
                    "changes": ["Simplified decorations", "Buffet catering", "DIY elements"],
                    "time_saved": "1-2 hours",
                    "trade_offs": ["More coordination required", "Simpler aesthetic"]
                }
            ])
        
        return alternatives

    def _get_approach_recommendations(self, approach: str) -> List[str]:
        """Get recommendations for specific approach"""
        recommendations = {
            "fast": [
                "Book vendors who offer express services",
                "Choose venues with built-in amenities",
                "Prepare detailed timeline with all stakeholders"
            ],
            "premium": [
                "Invest in professional event coordination",
                "Book premium vendors well in advance",
                "Consider guest experience at every touchpoint"
            ],
            "budget": [
                "Prioritize essential elements over nice-to-haves",
                "Leverage family and friends for support",
                "Focus on meaningful experiences over expensive items"
            ],
            "balanced": [
                "Balance cost and quality across all categories",
                "Allocate budget based on event priorities",
                "Maintain flexibility for adjustments"
            ]
        }
        
        return recommendations.get(approach, recommendations["balanced"])

    def _generate_budget_scenarios(self, event: Dict[str, Any], scenario: str) -> List[Dict[str, Any]]:
        """Generate budget scenarios"""
        scenarios = []
        
        if scenario == "budget_conscious":
            scenarios.append({
                "name": "Essential Elements Only",
                "description": "Focus on must-have items with cost optimization",
                "adjustments": {
                    "venue": "Choose cost-effective venues",
                    "catering": "Simplified menu with buffet service",
                    "decoration": "DIY and minimal professional decoration",
                    "entertainment": "Playlist and simple activities"
                },
                "savings": "30-40% of original budget"
            })
        elif scenario == "premium":
            scenarios.append({
                "name": "Luxury Experience",
                "description": "Premium services across all categories",
                "adjustments": {
                    "venue": "Premium venues with full service",
                    "catering": "Multi-course plated dining",
                    "decoration": "Professional design and premium flowers",
                    "entertainment": "Live performances and professional MC"
                },
                "additional_cost": "50-70% above standard budget"
            })
        elif scenario == "emergency":
            scenarios.append({
                "name": "Last-Minute Planning",
                "description": "Quick arrangements with available vendors",
                "adjustments": {
                    "venue": "Available venues with flexible booking",
                    "catering": "Ready-to-serve options",
                    "decoration": "Pre-made arrangements",
                    "entertainment": "Available performers or DJ services"
                },
                "premium": "10-20% above standard for urgency"
            })
        
        return scenarios

    def _get_scenario_recommendations(self, scenario: str) -> List[str]:
        """Get recommendations for budget scenarios"""
        recommendations = {
            "budget_conscious": [
                "Focus spending on high-impact elements",
                "Consider off-peak timing for better rates",
                "Leverage personal networks for cost savings"
            ],
            "premium": [
                "Book premium vendors well in advance",
                "Consider package deals for better value",
                "Invest in professional coordination"
            ],
            "emergency": [
                "Be flexible with vendor and venue options",
                "Expect to pay premium for short notice",
                "Focus on essential elements first"
            ],
            "standard": [
                "Balance quality and cost across categories",
                "Plan 3-6 months in advance for best options",
                "Keep 10-15% contingency for unexpected costs"
            ]
        }
        
        return recommendations.get(scenario, recommendations["standard"])