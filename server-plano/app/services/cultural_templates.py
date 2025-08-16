"""
Enhanced cultural and event templates for intelligent timeline generation.
Provides comprehensive ceremony templates with detailed cultural sequences,
activity duration estimates, and template selection logic.
"""
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal

from app.models.core import Activity, EventContext
from app.models.enums import (
    EventType, CulturalRequirement, ActivityType, Priority, VenueType, BudgetTier
)


@dataclass
class ActivityTemplate:
    """Template for a specific activity with cultural context"""
    name: str
    activity_type: ActivityType
    base_duration: timedelta
    priority: Priority
    description: str
    cultural_significance: str = ""
    required_vendors: List[str] = field(default_factory=list)
    setup_time: timedelta = timedelta(0)
    cleanup_time: timedelta = timedelta(0)
    guest_count_scaling: float = 1.0  # Factor to scale duration based on guest count
    venue_adjustments: Dict[VenueType, float] = field(default_factory=dict)
    budget_tier_adjustments: Dict[BudgetTier, float] = field(default_factory=dict)
    prerequisites: List[str] = field(default_factory=list)  # Activities that must happen before
    
    def calculate_duration(self, context: EventContext) -> timedelta:
        """Calculate actual duration based on event context"""
        duration = self.base_duration
        
        # Adjust for guest count
        if context.guest_count > 100:
            guest_factor = 1 + (context.guest_count - 100) * self.guest_count_scaling / 1000
            duration = timedelta(seconds=duration.total_seconds() * guest_factor)
        
        # Adjust for venue type
        venue_adjustment = self.venue_adjustments.get(context.venue_type, 1.0)
        duration = timedelta(seconds=duration.total_seconds() * venue_adjustment)
        
        # Adjust for budget tier
        budget_adjustment = self.budget_tier_adjustments.get(context.budget_tier, 1.0)
        duration = timedelta(seconds=duration.total_seconds() * budget_adjustment)
        
        return duration
    
    def to_activity(self, context: EventContext, activity_id: str) -> Activity:
        """Convert template to concrete activity"""
        duration = self.calculate_duration(context)
        
        # Estimate cost based on duration and context
        base_cost = Decimal('1000')  # Base cost per hour
        hours = duration.total_seconds() / 3600
        estimated_cost = base_cost * Decimal(str(hours))
        
        # Adjust cost for budget tier
        tier_multipliers = {
            BudgetTier.LOW: Decimal('0.6'),
            BudgetTier.STANDARD: Decimal('1.0'),
            BudgetTier.PREMIUM: Decimal('1.5'),
            BudgetTier.LUXURY: Decimal('2.0')
        }
        estimated_cost *= tier_multipliers.get(context.budget_tier, Decimal('1.0'))
        
        return Activity(
            id=activity_id,
            name=self.name,
            activity_type=self.activity_type,
            duration=duration,
            priority=self.priority,
            description=self.description,
            required_vendors=self.required_vendors.copy(),
            estimated_cost=estimated_cost,
            cultural_significance=self.cultural_significance,
            setup_time=self.setup_time,
            cleanup_time=self.cleanup_time
        )


@dataclass
class CeremonyTemplate:
    """Template for a complete ceremony with multiple activities"""
    name: str
    cultural_requirement: CulturalRequirement
    event_type: EventType
    activities: List[ActivityTemplate]
    total_duration_estimate: timedelta
    description: str
    cultural_notes: str = ""
    required_items: List[str] = field(default_factory=list)
    optional_activities: List[ActivityTemplate] = field(default_factory=list)
    
    def is_compatible(self, context: EventContext) -> bool:
        """Check if this ceremony template is compatible with event context"""
        # Check event type compatibility
        if self.event_type != context.event_type:
            return False
        
        # Check cultural requirement compatibility
        if self.cultural_requirement == CulturalRequirement.SECULAR:
            return True  # Secular templates work for all
        
        # If context has no specific cultural requirements, secular templates work
        if not context.cultural_requirements:
            return self.cultural_requirement == CulturalRequirement.SECULAR
        
        # Check if template's cultural requirement matches any of the context requirements
        return self.cultural_requirement in context.cultural_requirements
    
    def get_activities(self, context: EventContext, include_optional: bool = False) -> List[ActivityTemplate]:
        """Get activities for this ceremony, optionally including optional ones"""
        activities = self.activities.copy()
        
        if include_optional:
            # Add optional activities based on budget tier and guest count
            if context.budget_tier in [BudgetTier.PREMIUM, BudgetTier.LUXURY]:
                activities.extend(self.optional_activities)
            elif context.budget_tier == BudgetTier.STANDARD and context.guest_count > 150:
                # Add some optional activities for larger standard events
                activities.extend(self.optional_activities[:len(self.optional_activities)//2])
        
        return activities


class CulturalTemplateEngine:
    """Engine for managing and selecting cultural ceremony templates"""
    
    def __init__(self):
        self.templates = self._initialize_templates()
    
    def _initialize_templates(self) -> List[CeremonyTemplate]:
        """Initialize all ceremony templates"""
        templates = []
        
        # Wedding templates
        templates.extend(self._create_wedding_templates())
        
        # Corporate event templates
        templates.extend(self._create_corporate_templates())
        
        # Birthday templates
        templates.extend(self._create_birthday_templates())
        
        # Other event templates
        templates.extend(self._create_other_event_templates())
        
        return templates
    
    def _create_corporate_templates(self) -> List[CeremonyTemplate]:
        """Create corporate event ceremony templates"""
        templates = []
        
        # Standard Corporate Event Template
        corporate_activities = [
            ActivityTemplate(
                name="Registration & Welcome",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(minutes=30),
                priority=Priority.CRITICAL,
                description="Guest registration and welcome reception",
                required_vendors=["registration_desk", "welcome_staff"],
                setup_time=timedelta(minutes=15),
                guest_count_scaling=0.1
            ),
            ActivityTemplate(
                name="Opening Ceremony",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=45),
                priority=Priority.CRITICAL,
                description="Welcome address and event inauguration",
                required_vendors=["audio_visual", "stage_setup"],
                setup_time=timedelta(minutes=30)
            ),
            ActivityTemplate(
                name="Keynote Presentation",
                activity_type=ActivityType.ENTERTAINMENT,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Main presentation or keynote speech",
                required_vendors=["audio_visual", "presentation_setup"],
                setup_time=timedelta(minutes=15)
            ),
            ActivityTemplate(
                name="Networking Break",
                activity_type=ActivityType.BREAK,
                base_duration=timedelta(minutes=30),
                priority=Priority.MEDIUM,
                description="Coffee break and networking session",
                required_vendors=["catering", "setup_crew"],
                setup_time=timedelta(minutes=10)
            ),
            ActivityTemplate(
                name="Business Lunch",
                activity_type=ActivityType.CATERING,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Formal lunch with networking opportunities",
                required_vendors=["catering", "service_staff"],
                setup_time=timedelta(minutes=20),
                guest_count_scaling=0.05
            ),
            ActivityTemplate(
                name="Closing Ceremony",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=30),
                priority=Priority.HIGH,
                description="Event wrap-up and closing remarks",
                required_vendors=["audio_visual"],
                cleanup_time=timedelta(minutes=30)
            )
        ]
        
        corporate_template = CeremonyTemplate(
            name="Standard Corporate Event",
            cultural_requirement=CulturalRequirement.SECULAR,
            event_type=EventType.CORPORATE,
            activities=corporate_activities,
            total_duration_estimate=timedelta(hours=4, minutes=30),
            description="Standard corporate event with presentations and networking",
            required_items=["audio_visual_equipment", "registration_materials", "name_badges"]
        )
        
        templates.append(corporate_template)
        
        # Conference Template
        conference_activities = [
            ActivityTemplate(
                name="Registration & Check-in",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(minutes=45),
                priority=Priority.CRITICAL,
                description="Attendee registration and material distribution",
                required_vendors=["registration_desk", "welcome_staff"],
                setup_time=timedelta(minutes=20),
                guest_count_scaling=0.15
            ),
            ActivityTemplate(
                name="Opening Keynote",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=1),
                priority=Priority.CRITICAL,
                description="Conference opening and keynote presentation",
                required_vendors=["audio_visual", "stage_setup", "lighting"],
                setup_time=timedelta(minutes=45)
            ),
            ActivityTemplate(
                name="Panel Discussion",
                activity_type=ActivityType.ENTERTAINMENT,
                base_duration=timedelta(hours=1, minutes=30),
                priority=Priority.HIGH,
                description="Expert panel discussion and Q&A",
                required_vendors=["audio_visual", "panel_setup"],
                setup_time=timedelta(minutes=20)
            ),
            ActivityTemplate(
                name="Networking Lunch",
                activity_type=ActivityType.CATERING,
                base_duration=timedelta(hours=1, minutes=15),
                priority=Priority.HIGH,
                description="Lunch with structured networking activities",
                required_vendors=["catering", "service_staff", "networking_facilitator"],
                setup_time=timedelta(minutes=30),
                guest_count_scaling=0.08
            ),
            ActivityTemplate(
                name="Breakout Sessions",
                activity_type=ActivityType.ENTERTAINMENT,
                base_duration=timedelta(hours=2),
                priority=Priority.MEDIUM,
                description="Parallel breakout sessions on specific topics",
                required_vendors=["audio_visual", "room_setup"],
                setup_time=timedelta(minutes=15)
            ),
            ActivityTemplate(
                name="Closing & Awards",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=45),
                priority=Priority.HIGH,
                description="Conference closing and award ceremony",
                required_vendors=["audio_visual", "awards_setup"],
                cleanup_time=timedelta(minutes=45)
            )
        ]
        
        conference_template = CeremonyTemplate(
            name="Professional Conference",
            cultural_requirement=CulturalRequirement.SECULAR,
            event_type=EventType.CONFERENCE,
            activities=conference_activities,
            total_duration_estimate=timedelta(hours=7),
            description="Full-day professional conference with multiple sessions",
            required_items=["conference_materials", "name_badges", "signage", "audio_visual_equipment"]
        )
        
        templates.append(conference_template)
        
        return templates
    
    def _create_wedding_templates(self) -> List[CeremonyTemplate]:
        """Create wedding ceremony templates for different cultures"""
        templates = []
        
        # Hindu Wedding Template
        hindu_activities = [
            ActivityTemplate(
                name="Ganesh Puja",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=30),
                priority=Priority.CRITICAL,
                description="Invocation of Lord Ganesh for auspicious beginning",
                cultural_significance="Removes obstacles and ensures smooth ceremony",
                required_vendors=["priest", "puja_items"],
                setup_time=timedelta(minutes=15)
            ),
            ActivityTemplate(
                name="Baraat Arrival",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Groom's procession arrival with music and celebration",
                cultural_significance="Traditional arrival of groom with family",
                required_vendors=["band", "horse_or_car", "photographer"],
                setup_time=timedelta(minutes=30)
            ),
            ActivityTemplate(
                name="Milni Ceremony",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=30),
                priority=Priority.HIGH,
                description="Meeting and greeting of both families",
                cultural_significance="Formal introduction and bonding of families",
                required_vendors=["photographer"],
                setup_time=timedelta(minutes=10)
            ),
            ActivityTemplate(
                name="Kanyadaan",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=20),
                priority=Priority.CRITICAL,
                description="Father giving away the bride",
                cultural_significance="Sacred ritual of giving daughter in marriage",
                required_vendors=["priest", "photographer"],
                setup_time=timedelta(minutes=5)
            ),
            ActivityTemplate(
                name="Saat Phere",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=45),
                priority=Priority.CRITICAL,
                description="Seven sacred vows around holy fire",
                cultural_significance="Core wedding ritual with seven promises",
                required_vendors=["priest", "fire_setup", "photographer"],
                setup_time=timedelta(minutes=20)
            ),
            ActivityTemplate(
                name="Sindoor & Mangalsutra",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=15),
                priority=Priority.CRITICAL,
                description="Applying sindoor and tying mangalsutra",
                cultural_significance="Symbols of married status",
                required_vendors=["priest", "photographer"],
                setup_time=timedelta(minutes=5)
            )
        ]
        
        hindu_template = CeremonyTemplate(
            name="Traditional Hindu Wedding",
            cultural_requirement=CulturalRequirement.HINDU,
            event_type=EventType.WEDDING,
            activities=hindu_activities,
            total_duration_estimate=timedelta(hours=4),
            description="Complete Hindu wedding ceremony with all traditional rituals",
            cultural_notes="Follows traditional Vedic wedding customs",
            required_items=["mandap", "havan_kund", "puja_items", "flowers", "coconuts"]
        )
        
        templates.append(hindu_template)
        
        # Secular Wedding Template
        secular_activities = [
            ActivityTemplate(
                name="Guest Reception",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(minutes=45),
                priority=Priority.HIGH,
                description="Welcome guests and pre-ceremony gathering",
                required_vendors=["reception_staff", "photographer"],
                setup_time=timedelta(minutes=30)
            ),
            ActivityTemplate(
                name="Wedding Ceremony",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=1),
                priority=Priority.CRITICAL,
                description="Main wedding ceremony with vows and rings",
                required_vendors=["officiant", "photographer", "music"],
                setup_time=timedelta(minutes=20)
            ),
            ActivityTemplate(
                name="Photo Session",
                activity_type=ActivityType.PHOTOGRAPHY,
                base_duration=timedelta(minutes=45),
                priority=Priority.HIGH,
                description="Wedding photography session with couple and families",
                required_vendors=["photographer"],
                setup_time=timedelta(minutes=10)
            ),
            ActivityTemplate(
                name="Reception Dinner",
                activity_type=ActivityType.CATERING,
                base_duration=timedelta(hours=2),
                priority=Priority.CRITICAL,
                description="Wedding reception with dinner and celebration",
                required_vendors=["catering", "service_staff", "music"],
                setup_time=timedelta(minutes=30),
                guest_count_scaling=0.1
            ),
            ActivityTemplate(
                name="Entertainment & Dancing",
                activity_type=ActivityType.ENTERTAINMENT,
                base_duration=timedelta(hours=2),
                priority=Priority.MEDIUM,
                description="Music, dancing, and entertainment for guests",
                required_vendors=["dj", "sound_system"],
                setup_time=timedelta(minutes=15)
            )
        ]
        
        secular_template = CeremonyTemplate(
            name="Modern Wedding Ceremony",
            cultural_requirement=CulturalRequirement.SECULAR,
            event_type=EventType.WEDDING,
            activities=secular_activities,
            total_duration_estimate=timedelta(hours=6),
            description="Modern wedding ceremony suitable for all backgrounds",
            cultural_notes="Flexible ceremony format adaptable to various preferences",
            required_items=["wedding_rings", "flowers", "decorations", "sound_system"]
        )
        
        templates.append(secular_template)
        
        return templates
    
    def _create_birthday_templates(self) -> List[CeremonyTemplate]:
        """Create birthday celebration templates"""
        templates = []
        
        # Standard Birthday Template
        birthday_activities = [
            ActivityTemplate(
                name="Guest Welcome",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(minutes=30),
                priority=Priority.HIGH,
                description="Welcome guests and initial mingling",
                required_vendors=["host", "welcome_setup"],
                setup_time=timedelta(minutes=15)
            ),
            ActivityTemplate(
                name="Birthday Song & Cake Cutting",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=20),
                priority=Priority.CRITICAL,
                description="Traditional birthday song and cake cutting ceremony",
                required_vendors=["photographer", "cake"],
                setup_time=timedelta(minutes=10)
            ),
            ActivityTemplate(
                name="Entertainment & Games",
                activity_type=ActivityType.ENTERTAINMENT,
                base_duration=timedelta(hours=1, minutes=30),
                priority=Priority.HIGH,
                description="Fun activities, games, and entertainment",
                required_vendors=["entertainer", "game_setup"],
                setup_time=timedelta(minutes=20)
            ),
            ActivityTemplate(
                name="Food & Refreshments",
                activity_type=ActivityType.CATERING,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Serving food and refreshments to guests",
                required_vendors=["catering", "service_staff"],
                setup_time=timedelta(minutes=30),
                guest_count_scaling=0.05
            )
        ]
        
        birthday_template = CeremonyTemplate(
            name="Standard Birthday Celebration",
            cultural_requirement=CulturalRequirement.SECULAR,
            event_type=EventType.BIRTHDAY,
            activities=birthday_activities,
            total_duration_estimate=timedelta(hours=3),
            description="Fun birthday celebration with cake, games, and entertainment",
            required_items=["birthday_cake", "decorations", "party_supplies"]
        )
        
        templates.append(birthday_template)
        
        return templates
    
    def _create_other_event_templates(self) -> List[CeremonyTemplate]:
        """Create templates for other event types"""
        templates = []
        
        # Anniversary Template
        anniversary_activities = [
            ActivityTemplate(
                name="Guest Reception",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(minutes=30),
                priority=Priority.HIGH,
                description="Welcome guests and initial gathering",
                required_vendors=["host", "reception_setup"],
                setup_time=timedelta(minutes=15)
            ),
            ActivityTemplate(
                name="Anniversary Celebration",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=45),
                priority=Priority.CRITICAL,
                description="Anniversary ceremony and speeches",
                required_vendors=["photographer", "ceremony_setup"],
                setup_time=timedelta(minutes=15)
            ),
            ActivityTemplate(
                name="Dinner & Entertainment",
                activity_type=ActivityType.CATERING,
                base_duration=timedelta(hours=2),
                priority=Priority.HIGH,
                description="Celebratory dinner with entertainment",
                required_vendors=["catering", "entertainment", "service_staff"],
                setup_time=timedelta(minutes=30)
            )
        ]
        
        anniversary_template = CeremonyTemplate(
            name="Anniversary Celebration",
            cultural_requirement=CulturalRequirement.SECULAR,
            event_type=EventType.ANNIVERSARY,
            activities=anniversary_activities,
            total_duration_estimate=timedelta(hours=3, minutes=15),
            description="Elegant anniversary celebration with dinner and entertainment",
            required_items=["decorations", "anniversary_cake", "flowers"]
        )
        
        templates.append(anniversary_template)
        
        return templates
    
    def find_compatible_templates(self, context: EventContext) -> List[CeremonyTemplate]:
        """Find all ceremony templates compatible with the given context"""
        compatible = []
        
        for template in self.templates:
            if template.is_compatible(context):
                compatible.append(template)
        
        return compatible
    
    def get_best_template(self, context: EventContext) -> Optional[CeremonyTemplate]:
        """Get the best ceremony template for the given context"""
        compatible = self.find_compatible_templates(context)
        
        if not compatible:
            return None
        
        # For now, return the first compatible template
        # In the future, we could add scoring logic here
        return compatible[0]
    
    def get_template_by_name(self, name: str) -> Optional[CeremonyTemplate]:
        """Get a specific template by name"""
        for template in self.templates:
            if template.name == name:
                return template
        return None
        # Check event type compatibility
        if self.event_type != context.event_type:
            return False
        
        # Check cultural requirement compatibility
        if self.cultural_requirement not in context.cultural_requirements and \
           CulturalRequirement.SECULAR not in context.cultural_requirements:
            return False
        
        return True
    
    def get_activities(self, context: EventContext, include_optional: bool = False) -> List[ActivityTemplate]:
        """Get activities for this ceremony, optionally including optional ones"""
        activities = self.activities.copy()
        
        if include_optional:
            # Add optional activities based on budget tier and guest count
            if context.budget_tier in [BudgetTier.PREMIUM, BudgetTier.LUXURY]:
                activities.extend(self.optional_activities)
            elif context.budget_tier == BudgetTier.STANDARD and context.guest_count > 150:
                # Add some optional activities for larger standard events
                activities.extend(self.optional_activities[:len(self.optional_activities)//2])
        
        return activities


class CulturalTemplateService:
    """Service for managing cultural and event templates"""
    
    def __init__(self, use_cache: bool = True):
        self.use_cache = use_cache
        self.pattern_cache = None
        
        if self.use_cache:
            try:
                from ..utils.cache_service import get_pattern_cache_service
                self.pattern_cache = get_pattern_cache_service()
            except ImportError:
                print("Warning: Cache service not available, disabling template caching")
                self.use_cache = False
        
        self._ceremony_templates = self._initialize_ceremony_templates()
        self._activity_templates = self._initialize_activity_templates()
    
    def _initialize_ceremony_templates(self) -> List[CeremonyTemplate]:
        """Initialize comprehensive ceremony templates"""
        templates = []
        
        # Hindu Wedding Templates
        templates.extend(self._create_hindu_wedding_templates())
        
        # Muslim Wedding Templates
        templates.extend(self._create_muslim_wedding_templates())
        
        # Christian Wedding Templates
        templates.extend(self._create_christian_wedding_templates())
        
        # Sikh Wedding Templates
        templates.extend(self._create_sikh_wedding_templates())
        
        # Birthday Templates
        templates.extend(self._create_birthday_templates())
        
        # Corporate Event Templates
        templates.extend(self._create_corporate_templates())
        
        # Other Event Templates
        templates.extend(self._create_other_event_templates())
        
        return templates
    
    def _create_hindu_wedding_templates(self) -> List[CeremonyTemplate]:
        """Create Hindu wedding ceremony templates"""
        templates = []
        
        # Mehendi Ceremony
        mehendi_activities = [
            ActivityTemplate(
                name="Mehendi Setup and Decoration",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(hours=2),
                priority=Priority.HIGH,
                description="Setting up mehendi area with traditional decorations",
                cultural_significance="Mehendi symbolizes joy and spiritual awakening",
                required_vendors=["decorator", "mehendi_artist"],
                setup_time=timedelta(minutes=30),
                venue_adjustments={VenueType.OUTDOOR: 1.3, VenueType.HOME: 0.8}
            ),
            ActivityTemplate(
                name="Mehendi Application",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=4),
                priority=Priority.CRITICAL,
                description="Traditional henna application for bride and female relatives",
                cultural_significance="Mehendi represents the bond of matrimony",
                required_vendors=["mehendi_artist"],
                guest_count_scaling=0.5,
                budget_tier_adjustments={BudgetTier.PREMIUM: 1.2, BudgetTier.LUXURY: 1.5}
            ),
            ActivityTemplate(
                name="Mehendi Entertainment",
                activity_type=ActivityType.ENTERTAINMENT,
                base_duration=timedelta(hours=2),
                priority=Priority.MEDIUM,
                description="Traditional songs, dance, and games during mehendi",
                required_vendors=["musician", "dj"],
                venue_adjustments={VenueType.OUTDOOR: 1.2}
            ),
            ActivityTemplate(
                name="Mehendi Refreshments",
                activity_type=ActivityType.CATERING,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Light snacks and beverages for guests",
                required_vendors=["caterer"],
                guest_count_scaling=0.3
            )
        ]
        
        templates.append(CeremonyTemplate(
            name="Mehendi Ceremony",
            cultural_requirement=CulturalRequirement.HINDU,
            event_type=EventType.WEDDING,
            activities=mehendi_activities,
            total_duration_estimate=timedelta(hours=6),
            description="Traditional pre-wedding henna ceremony",
            cultural_notes="Usually held 1-2 days before wedding, primarily for women",
            required_items=["henna", "traditional_decorations", "cushions", "music_system"]
        ))
        
        # Haldi Ceremony
        haldi_activities = [
            ActivityTemplate(
                name="Haldi Preparation",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Preparing turmeric paste and setting up ceremony area",
                cultural_significance="Haldi purifies and blesses the couple",
                required_vendors=["decorator"],
                setup_time=timedelta(minutes=30)
            ),
            ActivityTemplate(
                name="Haldi Application Ceremony",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=2),
                priority=Priority.CRITICAL,
                description="Application of turmeric paste by family members",
                cultural_significance="Turmeric brings good luck and wards off evil",
                guest_count_scaling=0.2
            ),
            ActivityTemplate(
                name="Haldi Celebration",
                activity_type=ActivityType.ENTERTAINMENT,
                base_duration=timedelta(hours=1),
                priority=Priority.MEDIUM,
                description="Singing, dancing, and celebration after ceremony",
                required_vendors=["musician"]
            )
        ]
        
        templates.append(CeremonyTemplate(
            name="Haldi Ceremony",
            cultural_requirement=CulturalRequirement.HINDU,
            event_type=EventType.WEDDING,
            activities=haldi_activities,
            total_duration_estimate=timedelta(hours=4),
            description="Traditional turmeric ceremony for purification",
            cultural_notes="Held on the morning of wedding or day before",
            required_items=["turmeric", "oil", "flowers", "traditional_clothes"]
        ))
        
        # Main Wedding Ceremony
        wedding_activities = [
            ActivityTemplate(
                name="Mandap Setup",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(hours=3),
                priority=Priority.CRITICAL,
                description="Setting up sacred wedding canopy",
                cultural_significance="Mandap represents the universe where marriage takes place",
                required_vendors=["decorator", "pandit"],
                setup_time=timedelta(hours=1),
                venue_adjustments={VenueType.OUTDOOR: 1.5}
            ),
            ActivityTemplate(
                name="Baraat Arrival",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=1, minutes=30),
                priority=Priority.HIGH,
                description="Groom's procession arrival with music and dance",
                cultural_significance="Celebratory arrival of groom's family",
                required_vendors=["musician", "photographer"],
                guest_count_scaling=0.3
            ),
            ActivityTemplate(
                name="Wedding Rituals",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=3),
                priority=Priority.CRITICAL,
                description="Sacred wedding rituals including saat phere",
                cultural_significance="Seven vows that bind the couple",
                required_vendors=["pandit", "photographer"],
                budget_tier_adjustments={BudgetTier.LUXURY: 1.3}
            ),
            ActivityTemplate(
                name="Wedding Photography",
                activity_type=ActivityType.PHOTOGRAPHY,
                base_duration=timedelta(hours=8),
                priority=Priority.HIGH,
                description="Comprehensive wedding photography and videography",
                required_vendors=["photographer", "videographer"],
                guest_count_scaling=0.2
            )
        ]
        
        templates.append(CeremonyTemplate(
            name="Hindu Wedding Ceremony",
            cultural_requirement=CulturalRequirement.HINDU,
            event_type=EventType.WEDDING,
            activities=wedding_activities,
            total_duration_estimate=timedelta(hours=8),
            description="Main Hindu wedding ceremony with all rituals",
            cultural_notes="Sacred ceremony conducted by pandit with Vedic rituals",
            required_items=["sacred_fire", "flowers", "rice", "coconut", "red_cloth"]
        ))
        
        return templates
    
    def _create_muslim_wedding_templates(self) -> List[CeremonyTemplate]:
        """Create Muslim wedding ceremony templates"""
        templates = []
        
        # Nikkah Ceremony
        nikkah_activities = [
            ActivityTemplate(
                name="Nikkah Setup",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Setting up for Islamic marriage contract ceremony",
                cultural_significance="Preparation for sacred Islamic marriage",
                required_vendors=["decorator"],
                setup_time=timedelta(minutes=30)
            ),
            ActivityTemplate(
                name="Nikkah Ceremony",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=1, minutes=30),
                priority=Priority.CRITICAL,
                description="Islamic marriage contract ceremony with Imam",
                cultural_significance="Sacred Islamic marriage contract",
                required_vendors=["imam", "photographer"]
            ),
            ActivityTemplate(
                name="Nikkah Celebration",
                activity_type=ActivityType.ENTERTAINMENT,
                base_duration=timedelta(hours=2),
                priority=Priority.MEDIUM,
                description="Celebration with family and friends",
                required_vendors=["caterer"]
            )
        ]
        
        templates.append(CeremonyTemplate(
            name="Nikkah Ceremony",
            cultural_requirement=CulturalRequirement.MUSLIM,
            event_type=EventType.WEDDING,
            activities=nikkah_activities,
            total_duration_estimate=timedelta(hours=4),
            description="Islamic marriage contract ceremony",
            cultural_notes="Sacred ceremony conducted by Imam",
            required_items=["quran", "marriage_contract", "flowers"]
        ))
        
        # Walima Reception
        walima_activities = [
            ActivityTemplate(
                name="Walima Setup",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(hours=2),
                priority=Priority.HIGH,
                description="Setting up reception venue",
                required_vendors=["decorator"],
                setup_time=timedelta(hours=1),
                venue_adjustments={VenueType.BANQUET_HALL: 1.2}
            ),
            ActivityTemplate(
                name="Guest Reception",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Welcoming guests to the celebration",
                guest_count_scaling=0.2
            ),
            ActivityTemplate(
                name="Walima Feast",
                activity_type=ActivityType.CATERING,
                base_duration=timedelta(hours=2),
                priority=Priority.CRITICAL,
                description="Traditional feast for wedding celebration",
                cultural_significance="Sharing meal to celebrate marriage",
                required_vendors=["caterer"],
                guest_count_scaling=0.4
            )
        ]
        
        templates.append(CeremonyTemplate(
            name="Walima Reception",
            cultural_requirement=CulturalRequirement.MUSLIM,
            event_type=EventType.WEDDING,
            activities=walima_activities,
            total_duration_estimate=timedelta(hours=5),
            description="Traditional Muslim wedding reception",
            cultural_notes="Celebration feast hosted by groom's family",
            required_items=["traditional_food", "decorations", "seating"]
        ))
        
        return templates
    
    def _create_christian_wedding_templates(self) -> List[CeremonyTemplate]:
        """Create Christian wedding ceremony templates"""
        templates = []
        
        # Church Wedding
        church_activities = [
            ActivityTemplate(
                name="Church Decoration",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(hours=2),
                priority=Priority.HIGH,
                description="Decorating church for wedding ceremony",
                required_vendors=["decorator", "florist"],
                setup_time=timedelta(hours=1)
            ),
            ActivityTemplate(
                name="Wedding Ceremony",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=1, minutes=30),
                priority=Priority.CRITICAL,
                description="Christian wedding ceremony with vows",
                cultural_significance="Sacred Christian marriage ceremony",
                required_vendors=["priest", "musician", "photographer"]
            ),
            ActivityTemplate(
                name="Post-Ceremony Photography",
                activity_type=ActivityType.PHOTOGRAPHY,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Wedding photography after ceremony",
                required_vendors=["photographer"]
            )
        ]
        
        templates.append(CeremonyTemplate(
            name="Christian Wedding Ceremony",
            cultural_requirement=CulturalRequirement.CHRISTIAN,
            event_type=EventType.WEDDING,
            activities=church_activities,
            total_duration_estimate=timedelta(hours=4),
            description="Traditional Christian church wedding",
            cultural_notes="Sacred ceremony conducted by priest",
            required_items=["rings", "flowers", "candles", "bible"]
        ))
        
        return templates
    
    def _create_sikh_wedding_templates(self) -> List[CeremonyTemplate]:
        """Create Sikh wedding ceremony templates"""
        templates = []
        
        # Anand Karaj
        anand_karaj_activities = [
            ActivityTemplate(
                name="Gurdwara Setup",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Preparing Gurdwara for wedding ceremony",
                cultural_significance="Sacred Sikh place of worship",
                required_vendors=["decorator"],
                setup_time=timedelta(minutes=30)
            ),
            ActivityTemplate(
                name="Anand Karaj Ceremony",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=2),
                priority=Priority.CRITICAL,
                description="Sikh wedding ceremony with four rounds",
                cultural_significance="Four rounds around Guru Granth Sahib",
                required_vendors=["granthi", "photographer"]
            ),
            ActivityTemplate(
                name="Langar",
                activity_type=ActivityType.CATERING,
                base_duration=timedelta(hours=1, minutes=30),
                priority=Priority.HIGH,
                description="Community meal served to all guests",
                cultural_significance="Sharing meal as equals in Sikh tradition",
                required_vendors=["caterer"],
                guest_count_scaling=0.3
            )
        ]
        
        templates.append(CeremonyTemplate(
            name="Anand Karaj",
            cultural_requirement=CulturalRequirement.SIKH,
            event_type=EventType.WEDDING,
            activities=anand_karaj_activities,
            total_duration_estimate=timedelta(hours=4),
            description="Traditional Sikh wedding ceremony",
            cultural_notes="Sacred ceremony in presence of Guru Granth Sahib",
            required_items=["guru_granth_sahib", "flowers", "chunni", "kirpan"]
        ))
        
        return templates
    
    def _create_birthday_templates(self) -> List[CeremonyTemplate]:
        """Create birthday celebration templates"""
        templates = []
        
        # Children's Birthday
        kids_activities = [
            ActivityTemplate(
                name="Party Setup",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(hours=1, minutes=30),
                priority=Priority.HIGH,
                description="Setting up decorations and party area",
                required_vendors=["decorator"],
                setup_time=timedelta(minutes=30),
                venue_adjustments={VenueType.HOME: 0.8, VenueType.OUTDOOR: 1.2}
            ),
            ActivityTemplate(
                name="Games and Activities",
                activity_type=ActivityType.ENTERTAINMENT,
                base_duration=timedelta(hours=2),
                priority=Priority.HIGH,
                description="Age-appropriate games and entertainment",
                required_vendors=["entertainer"],
                guest_count_scaling=0.3
            ),
            ActivityTemplate(
                name="Cake Cutting",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=30),
                priority=Priority.CRITICAL,
                description="Birthday cake cutting ceremony",
                required_vendors=["photographer"]
            ),
            ActivityTemplate(
                name="Party Refreshments",
                activity_type=ActivityType.CATERING,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Food and beverages for guests",
                required_vendors=["caterer"],
                guest_count_scaling=0.2
            )
        ]
        
        templates.append(CeremonyTemplate(
            name="Children's Birthday Party",
            cultural_requirement=CulturalRequirement.SECULAR,
            event_type=EventType.BIRTHDAY,
            activities=kids_activities,
            total_duration_estimate=timedelta(hours=4),
            description="Fun birthday party for children",
            required_items=["birthday_cake", "decorations", "games", "party_favors"]
        ))
        
        return templates
    
    def _create_corporate_templates(self) -> List[CeremonyTemplate]:
        """Create corporate event templates"""
        templates = []
        
        # Conference
        conference_activities = [
            ActivityTemplate(
                name="Venue Setup",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(hours=2),
                priority=Priority.HIGH,
                description="Setting up conference venue with AV equipment",
                required_vendors=["av_technician", "decorator"],
                setup_time=timedelta(hours=1)
            ),
            ActivityTemplate(
                name="Registration",
                activity_type=ActivityType.PREPARATION,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Guest registration and welcome",
                guest_count_scaling=0.4
            ),
            ActivityTemplate(
                name="Keynote Presentations",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=4),
                priority=Priority.CRITICAL,
                description="Main conference presentations",
                required_vendors=["av_technician", "photographer"]
            ),
            ActivityTemplate(
                name="Networking Breaks",
                activity_type=ActivityType.NETWORKING,
                base_duration=timedelta(hours=1, minutes=30),
                priority=Priority.MEDIUM,
                description="Coffee breaks and networking sessions",
                required_vendors=["caterer"]
            )
        ]
        
        templates.append(CeremonyTemplate(
            name="Corporate Conference",
            cultural_requirement=CulturalRequirement.SECULAR,
            event_type=EventType.CORPORATE,
            activities=conference_activities,
            total_duration_estimate=timedelta(hours=8),
            description="Professional corporate conference",
            required_items=["av_equipment", "seating", "signage", "materials"]
        ))
        
        return templates
    
    def _create_other_event_templates(self) -> List[CeremonyTemplate]:
        """Create templates for other event types"""
        templates = []
        
        # Housewarming
        housewarming_activities = [
            ActivityTemplate(
                name="House Blessing",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(hours=1),
                priority=Priority.HIGH,
                description="Traditional house blessing ceremony",
                cultural_significance="Blessing new home for prosperity"
            ),
            ActivityTemplate(
                name="House Tour",
                activity_type=ActivityType.CEREMONY,
                base_duration=timedelta(minutes=45),
                priority=Priority.MEDIUM,
                description="Showing guests around the new home",
                guest_count_scaling=0.3
            ),
            ActivityTemplate(
                name="Housewarming Meal",
                activity_type=ActivityType.CATERING,
                base_duration=timedelta(hours=2),
                priority=Priority.HIGH,
                description="Meal served to guests",
                required_vendors=["caterer"],
                guest_count_scaling=0.4
            )
        ]
        
        templates.append(CeremonyTemplate(
            name="Housewarming Celebration",
            cultural_requirement=CulturalRequirement.SECULAR,
            event_type=EventType.HOUSEWARMING,
            activities=housewarming_activities,
            total_duration_estimate=timedelta(hours=4),
            description="Traditional housewarming celebration",
            required_items=["decorations", "food", "gifts"]
        ))
        
        return templates
    
    def _initialize_activity_templates(self) -> Dict[str, ActivityTemplate]:
        """Initialize individual activity templates"""
        templates = {}
        
        # Common preparation activities
        templates["venue_setup"] = ActivityTemplate(
            name="Venue Setup",
            activity_type=ActivityType.PREPARATION,
            base_duration=timedelta(hours=2),
            priority=Priority.HIGH,
            description="General venue setup and preparation",
            required_vendors=["decorator"],
            setup_time=timedelta(minutes=30),
            venue_adjustments={
                VenueType.OUTDOOR: 1.5,
                VenueType.HOME: 0.8,
                VenueType.BANQUET_HALL: 1.2
            }
        )
        
        templates["cleanup"] = ActivityTemplate(
            name="Event Cleanup",
            activity_type=ActivityType.CLEANUP,
            base_duration=timedelta(hours=1, minutes=30),
            priority=Priority.MEDIUM,
            description="Post-event cleanup and restoration",
            guest_count_scaling=0.2,
            venue_adjustments={VenueType.OUTDOOR: 1.3}
        )
        
        return templates
    
    def get_compatible_ceremonies(self, context: EventContext) -> List[CeremonyTemplate]:
        """Get all ceremony templates compatible with the event context"""
        # Check cache first for each cultural requirement
        if self.use_cache and self.pattern_cache:
            cached_results = []
            cache_hit = True
            
            for cultural_req in context.cultural_requirements:
                cached_templates = self.pattern_cache.get_ceremony_templates(context.event_type, cultural_req)
                if cached_templates:
                    cached_results.extend(cached_templates)
                else:
                    cache_hit = False
                    break
            
            if cache_hit and cached_results:
                return cached_results
        
        # Generate templates if not cached
        compatible = []
        templates_by_cultural_req = {}
        
        for template in self._ceremony_templates:
            if template.is_compatible(context):
                compatible.append(template)
                
                # Group by cultural requirement for caching
                cultural_req = template.cultural_requirement
                if cultural_req not in templates_by_cultural_req:
                    templates_by_cultural_req[cultural_req] = []
                templates_by_cultural_req[cultural_req].append(template)
        
        # Cache the results by cultural requirement
        if self.use_cache and self.pattern_cache:
            for cultural_req, templates in templates_by_cultural_req.items():
                self.pattern_cache.cache_ceremony_templates(context.event_type, cultural_req, templates)
        
        return compatible
    
    def select_primary_ceremony(self, context: EventContext) -> Optional[CeremonyTemplate]:
        """Select the most appropriate primary ceremony for the event"""
        compatible = self.get_compatible_ceremonies(context)
        
        if not compatible:
            return None
        
        # For weddings, prioritize based on cultural requirements
        if context.event_type == EventType.WEDDING:
            # Prioritize specific cultural ceremonies over secular ones
            for cultural_req in context.cultural_requirements:
                if cultural_req != CulturalRequirement.SECULAR:
                    for template in compatible:
                        if template.cultural_requirement == cultural_req:
                            return template
        
        # Return the first compatible template
        return compatible[0]
    
    def get_activity_template(self, template_name: str) -> Optional[ActivityTemplate]:
        """Get a specific activity template by name"""
        # Check cache first
        if self.use_cache and self.pattern_cache:
            cached_templates = self.pattern_cache.get_activity_templates("all")
            if cached_templates and template_name in cached_templates:
                return cached_templates[template_name]
        
        # Get from memory
        template = self._activity_templates.get(template_name)
        
        # Cache all templates if not cached
        if self.use_cache and self.pattern_cache and template:
            self.pattern_cache.cache_activity_templates("all", self._activity_templates)
        
        return template
    
    def invalidate_template_cache(self) -> None:
        """Invalidate all cached templates"""
        if self.use_cache and self.pattern_cache:
            self.pattern_cache.invalidate_templates()
    
    def get_activity_template(self, template_name: str) -> Optional[ActivityTemplate]:
        """Get a specific activity template by name"""
        return self._activity_templates.get(template_name)
    
    def validate_cultural_compatibility(self, 
                                      ceremony: CeremonyTemplate, 
                                      context: EventContext) -> List[str]:
        """Validate cultural compatibility and return any issues"""
        issues = []
        
        if not ceremony.is_compatible(context):
            issues.append(f"Ceremony '{ceremony.name}' is not compatible with event context")
        
        # Check for conflicting cultural requirements
        if len(context.cultural_requirements) > 1:
            if CulturalRequirement.MIXED not in context.cultural_requirements:
                issues.append("Multiple cultural requirements specified without MIXED designation")
        
        # Check venue compatibility for religious ceremonies
        religious_ceremonies = [
            CulturalRequirement.HINDU,
            CulturalRequirement.MUSLIM,
            CulturalRequirement.CHRISTIAN,
            CulturalRequirement.SIKH
        ]
        
        if ceremony.cultural_requirement in religious_ceremonies:
            if context.venue_type == VenueType.BEACH:
                issues.append(f"Beach venue may not be suitable for {ceremony.cultural_requirement.value} ceremony")
        
        return issues