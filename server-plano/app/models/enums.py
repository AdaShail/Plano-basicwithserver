"""
Enums for categorical data in the intelligent timeline and budget system.
"""
from enum import Enum


class VenueType(Enum):
    """Types of venues for events"""
    INDOOR = "indoor"
    OUTDOOR = "outdoor"
    HYBRID = "hybrid"
    HOME = "home"
    BANQUET_HALL = "banquet_hall"
    HOTEL = "hotel"
    RESTAURANT = "restaurant"
    GARDEN = "garden"
    BEACH = "beach"
    TEMPLE = "temple"
    CHURCH = "church"
    COMMUNITY_CENTER = "community_center"


class BudgetTier(Enum):
    """Budget tiers for different service levels"""
    LOW = "low"
    STANDARD = "standard"
    PREMIUM = "premium"
    LUXURY = "luxury"


class Season(Enum):
    """Seasons affecting event planning"""
    SPRING = "spring"
    SUMMER = "summer"
    MONSOON = "monsoon"
    AUTUMN = "autumn"
    WINTER = "winter"


class EventType(Enum):
    """Types of events supported"""
    WEDDING = "wedding"
    BIRTHDAY = "birthday"
    ANNIVERSARY = "anniversary"
    HOUSEWARMING = "housewarming"
    CORPORATE = "corporate"
    GRADUATION = "graduation"
    BABY_SHOWER = "baby_shower"
    ENGAGEMENT = "engagement"
    FESTIVAL = "festival"
    CONFERENCE = "conference"


class CulturalRequirement(Enum):
    """Cultural and religious requirements"""
    HINDU = "hindu"
    MUSLIM = "muslim"
    CHRISTIAN = "christian"
    SIKH = "sikh"
    BUDDHIST = "buddhist"
    JAIN = "jain"
    JEWISH = "jewish"
    SECULAR = "secular"
    MIXED = "mixed"


class ActivityType(Enum):
    """Types of activities in timeline"""
    CEREMONY = "ceremony"
    PREPARATION = "preparation"
    CATERING = "catering"
    ENTERTAINMENT = "entertainment"
    PHOTOGRAPHY = "photography"
    DECORATION = "decoration"
    TRANSPORTATION = "transportation"
    CLEANUP = "cleanup"
    BREAK = "break"
    NETWORKING = "networking"


class BudgetCategory(Enum):
    """Budget allocation categories"""
    VENUE = "venue"
    CATERING = "catering"
    DECORATION = "decoration"
    ENTERTAINMENT = "entertainment"
    PHOTOGRAPHY = "photography"
    TRANSPORTATION = "transportation"
    FLOWERS = "flowers"
    CLOTHING = "clothing"
    JEWELRY = "jewelry"
    INVITATIONS = "invitations"
    GIFTS = "gifts"
    MISCELLANEOUS = "miscellaneous"
    CONTINGENCY = "contingency"


class Priority(Enum):
    """Priority levels for activities and budget items"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    OPTIONAL = "optional"


class WeatherCondition(Enum):
    """Weather conditions affecting outdoor events"""
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    WINDY = "windy"
    HOT = "hot"
    COLD = "cold"
    HUMID = "humid"


class AccessibilityRequirement(Enum):
    """Accessibility requirements for events"""
    WHEELCHAIR_ACCESS = "wheelchair_access"
    HEARING_ASSISTANCE = "hearing_assistance"
    VISUAL_ASSISTANCE = "visual_assistance"
    DIETARY_RESTRICTIONS = "dietary_restrictions"
    MOBILITY_ASSISTANCE = "mobility_assistance"
    SIGN_LANGUAGE = "sign_language"