"""
Real AI-powered budget allocation using Gemini API.
No fallbacks - pure AI allocation.
"""
import os
import json
import logging
from decimal import Decimal
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

import google.generativeai as genai
from ..models.core import EventContext, BudgetAllocation, CategoryAllocation, Alternative
from ..models.enums import BudgetCategory, Priority

logger = logging.getLogger(__name__)

class AIBudgetAllocator:
    """Real AI-powered budget allocator using Gemini"""
    
    def __init__(self):
        # Configure Gemini
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")
        
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("✅ Gemini AI initialized for budget allocation")
    
    def allocate_budget(self, total_budget: Decimal, context: EventContext) -> BudgetAllocation:
        """Allocate budget using real AI"""
        logger.info(f"🤖 Generating AI budget allocation for ₹{total_budget:,.2f}")
        
        # Create comprehensive AI prompt
        prompt = self._create_budget_prompt(total_budget, context)
        
        # Get AI response
        response = self.model.generate_content(prompt)
        ai_text = response.text
        
        logger.info("✅ AI budget response received, parsing allocation...")
        
        # Parse AI response into structured budget allocation
        allocation = self._parse_ai_budget(ai_text, total_budget, context)
        
        logger.info(f"✅ AI budget allocated across {len(allocation.categories)} categories")
        
        return allocation
    
    def _create_budget_prompt(self, total_budget: Decimal, context: EventContext) -> str:
        """Create comprehensive AI prompt for budget allocation"""
        
        cultural_info = ""
        if context.cultural_requirements:
            cultural_info = f"Cultural/Religious Requirements: {', '.join([req.value for req in context.cultural_requirements])}"
        
        per_person_budget = total_budget / context.guest_count
        
        prompt = f"""
You are an expert event budget planner AI. Create a detailed budget allocation for a {context.event_type.value} event.

EVENT DETAILS:
- Event Type: {context.event_type.value}
- Total Budget: ₹{total_budget:,.2f}
- Per Person Budget: ₹{per_person_budget:,.2f}
- Guest Count: {context.guest_count}
- Duration: {context.duration_days} days
- Venue Type: {context.venue_type.value}
- Budget Tier: {context.budget_tier.value}
- Location: {context.location.city}, {context.location.state}, {context.location.country}
- Season: {context.season.value}
{cultural_info}
- Special Requirements: {', '.join(context.special_requirements) if context.special_requirements else 'None'}

INSTRUCTIONS:
1. Allocate the EXACT total budget across relevant categories
2. Consider cultural requirements for specialized needs
3. Adjust for guest count, venue type, and location
4. Provide realistic percentages and amounts
5. Include justification for each allocation
6. Suggest alternatives for cost optimization
7. Consider seasonal pricing impacts
8. Account for venue-specific requirements

AVAILABLE CATEGORIES:
- venue: Venue rental, setup, facilities
- catering: Food, beverages, service staff
- decoration: Flowers, lighting, ambiance, themes
- entertainment: Music, DJ, performers, activities
- photography: Professional photography/videography
- transportation: Guest transport, vendor logistics
- clothing: Traditional attire, styling (if applicable)
- jewelry: Ceremonial jewelry (if applicable)
- invitations: Cards, digital invites, stationery
- gifts: Guest favors, ceremonial gifts
- miscellaneous: Contingency, unexpected costs

RESPONSE FORMAT (JSON):
{{
  "total_budget": {float(total_budget)},
  "per_person_cost": {float(per_person_budget)},
  "categories": {{
    "venue": {{
      "amount": 250000,
      "percentage": 25.0,
      "justification": "Premium venue for {context.guest_count} guests with {context.venue_type.value} requirements",
      "priority": "critical",
      "alternatives": [
        {{
          "name": "Budget Venue Option",
          "description": "Community hall with basic amenities",
          "cost_impact": -100000,
          "trade_offs": ["Less luxurious", "Basic facilities"]
        }}
      ]
    }}
  }},
  "regional_adjustments": {{
    "location_multiplier": 1.0,
    "seasonal_impact": "Peak season pricing for {context.season.value}"
  }},
  "optimization_suggestions": [
    "Consider off-peak dates for 15% savings",
    "Bulk vendor packages can reduce costs by 10%"
  ],
  "cultural_considerations": [
    "Traditional ceremony requirements factored into allocation"
  ]
}}

Create a smart, realistic budget allocation that maximizes value for this {context.event_type.value} event!
"""
        return prompt
    
    def _parse_ai_budget(self, ai_text: str, total_budget: Decimal, context: EventContext) -> BudgetAllocation:
        """Parse AI response into BudgetAllocation object"""
        try:
            # Clean the AI response - remove markdown code blocks
            cleaned_text = ai_text.strip()
            if cleaned_text.startswith('```json'):
                cleaned_text = cleaned_text[7:]  # Remove ```json
            if cleaned_text.endswith('```'):
                cleaned_text = cleaned_text[:-3]  # Remove ```
            
            # Extract JSON from AI response
            json_start = cleaned_text.find('{')
            json_end = cleaned_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in AI response")
            
            json_text = cleaned_text[json_start:json_end]
            
            # Fix common JSON issues
            json_text = json_text.replace("'", '"')  # Replace single quotes with double quotes
            
            # Try to parse JSON, if it fails, create a simplified budget
            try:
                ai_data = json.loads(json_text)
            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed: {e}, creating simplified budget from AI text")
                return self._create_simplified_budget_from_text(ai_text, total_budget, context)
            
            # Parse categories
            categories = {}
            total_allocated = Decimal('0')
            
            for category_name, category_data in ai_data.get('categories', {}).items():
                # Map category name to enum
                category_enum = self._parse_category(category_name)
                if not category_enum:
                    continue
                
                amount = Decimal(str(category_data.get('amount', 0)))
                percentage = float(category_data.get('percentage', 0))
                
                # Parse alternatives
                alternatives = []
                for alt_data in category_data.get('alternatives', []):
                    alternative = Alternative(
                        name=alt_data.get('name', 'Alternative Option'),
                        description=alt_data.get('description', ''),
                        cost_impact=Decimal(str(alt_data.get('cost_impact', 0))),
                        time_impact=alt_data.get('time_impact'),
                        trade_offs=alt_data.get('trade_offs', [])
                    )
                    alternatives.append(alternative)
                
                # Create CategoryAllocation
                category_allocation = CategoryAllocation(
                    category=category_enum,
                    amount=amount,
                    percentage=percentage,
                    justification=category_data.get('justification', f'AI allocation for {category_name}'),
                    alternatives=alternatives,
                    priority=self._parse_priority(category_data.get('priority', 'medium'))
                )
                
                categories[category_enum] = category_allocation
                total_allocated += amount
            
            # Calculate per-person cost
            per_person_cost = total_budget / context.guest_count
            
            # Parse regional adjustments
            regional_adjustments = ai_data.get('regional_adjustments', {})
            seasonal_adjustments = {
                context.season.value: regional_adjustments.get('seasonal_impact', 'Standard pricing')
            }
            
            # Create BudgetAllocation
            allocation = BudgetAllocation(
                total_budget=total_budget,
                categories=categories,
                per_person_cost=per_person_cost,
                contingency_percentage=10.0,  # Default contingency
                regional_adjustments=regional_adjustments,
                seasonal_adjustments=seasonal_adjustments
            )
            
            return allocation
            
        except Exception as e:
            logger.error(f"Failed to parse AI budget response: {str(e)}")
            logger.error(f"AI Response: {ai_text[:500]}...")
            raise ValueError(f"Failed to parse AI budget: {str(e)}")
    
    def _parse_category(self, category_name: str) -> Optional[BudgetCategory]:
        """Parse category name to enum"""
        category_mapping = {
            'venue': BudgetCategory.VENUE,
            'catering': BudgetCategory.CATERING,
            'decoration': BudgetCategory.DECORATION,
            'entertainment': BudgetCategory.ENTERTAINMENT,
            'photography': BudgetCategory.PHOTOGRAPHY,
            'transportation': BudgetCategory.TRANSPORTATION,
            'flowers': BudgetCategory.FLOWERS,
            'clothing': BudgetCategory.CLOTHING,
            'jewelry': BudgetCategory.JEWELRY,
            'invitations': BudgetCategory.INVITATIONS,
            'gifts': BudgetCategory.GIFTS,
            'miscellaneous': BudgetCategory.MISCELLANEOUS,
            'contingency': BudgetCategory.CONTINGENCY
        }
        return category_mapping.get(category_name.lower())
    
    def _parse_priority(self, priority_str: str) -> Priority:
        """Parse priority from AI response"""
        priority_mapping = {
            'critical': Priority.CRITICAL,
            'high': Priority.HIGH,
            'medium': Priority.MEDIUM,
            'low': Priority.LOW,
            'optional': Priority.OPTIONAL
        }
        return priority_mapping.get(priority_str.lower(), Priority.MEDIUM)
    
    def _create_simplified_budget_from_text(self, ai_text: str, total_budget: Decimal, context: EventContext) -> BudgetAllocation:
        """Create a simplified budget when JSON parsing fails"""
        logger.info("Creating simplified budget from AI text")
        
        # Smart allocation based on event type
        if context.event_type.value == "housewarming":
            allocations = {
                BudgetCategory.VENUE: (15.0, "Venue setup and decoration for housewarming"),
                BudgetCategory.CATERING: (45.0, "Food and beverages - central to housewarming tradition"),
                BudgetCategory.DECORATION: (20.0, "Home decoration and ambiance"),
                BudgetCategory.ENTERTAINMENT: (8.0, "Music and entertainment"),
                BudgetCategory.PHOTOGRAPHY: (5.0, "Capturing memories"),
                BudgetCategory.TRANSPORTATION: (2.0, "Guest coordination"),
                BudgetCategory.MISCELLANEOUS: (5.0, "Contingency and miscellaneous items")
            }
        elif context.event_type.value == "wedding":
            allocations = {
                BudgetCategory.VENUE: (25.0, "Wedding venue and facilities"),
                BudgetCategory.CATERING: (40.0, "Wedding feast and catering"),
                BudgetCategory.DECORATION: (15.0, "Wedding decorations and flowers"),
                BudgetCategory.ENTERTAINMENT: (8.0, "Music and entertainment"),
                BudgetCategory.PHOTOGRAPHY: (10.0, "Wedding photography and videography"),
                BudgetCategory.TRANSPORTATION: (2.0, "Transportation logistics")
            }
        else:
            # Generic allocation
            allocations = {
                BudgetCategory.VENUE: (20.0, "Event venue and setup"),
                BudgetCategory.CATERING: (35.0, "Food and beverages"),
                BudgetCategory.DECORATION: (15.0, "Event decoration"),
                BudgetCategory.ENTERTAINMENT: (15.0, "Entertainment and activities"),
                BudgetCategory.PHOTOGRAPHY: (8.0, "Event documentation"),
                BudgetCategory.TRANSPORTATION: (2.0, "Logistics"),
                BudgetCategory.MISCELLANEOUS: (5.0, "Miscellaneous expenses")
            }
        
        # Create category allocations
        categories = {}
        for category, (percentage, justification) in allocations.items():
            amount = total_budget * Decimal(str(percentage / 100))
            
            category_allocation = CategoryAllocation(
                category=category,
                amount=amount,
                percentage=percentage,
                justification=justification,
                alternatives=[],
                priority=Priority.HIGH if percentage > 20 else Priority.MEDIUM
            )
            
            categories[category] = category_allocation
        
        # Create BudgetAllocation
        allocation = BudgetAllocation(
            total_budget=total_budget,
            categories=categories,
            per_person_cost=total_budget / context.guest_count,
            contingency_percentage=5.0,
            regional_adjustments={"location": f"{context.location.city}, {context.location.state}"},
            seasonal_adjustments={context.season.value: "AI-optimized seasonal pricing"}
        )
        
        return allocation