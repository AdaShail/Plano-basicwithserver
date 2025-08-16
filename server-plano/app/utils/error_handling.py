"""
Comprehensive error handling utilities for the intelligent timeline and budget system.
"""
import logging
from typing import Dict, Any, List, Optional, Union, Callable
from functools import wraps
from datetime import datetime
from decimal import Decimal, InvalidOperation

from ..models.validators import ValidationError, validate_and_raise
from ..models.core import EventContext, Timeline, BudgetAllocation


# Configure logging
logger = logging.getLogger(__name__)


class EventPlanningError(Exception):
    """Base exception for event planning errors"""
    def __init__(self, message: str, error_code: str = None, details: Dict[str, Any] = None):
        self.message = message
        self.error_code = error_code or "GENERAL_ERROR"
        self.details = details or {}
        self.timestamp = datetime.now()
        super().__init__(message)


class InputValidationError(EventPlanningError):
    """Exception for input validation failures"""
    def __init__(self, validation_errors: List[str], field: str = None):
        self.validation_errors = validation_errors
        self.field = field
        message = f"Input validation failed: {'; '.join(validation_errors)}"
        super().__init__(message, "INPUT_VALIDATION_ERROR", {"errors": validation_errors, "field": field})


class ConstraintViolationError(EventPlanningError):
    """Exception for logical constraint violations"""
    def __init__(self, constraint: str, details: str = None):
        self.constraint = constraint
        message = f"Constraint violation: {constraint}"
        if details:
            message += f" - {details}"
        super().__init__(message, "CONSTRAINT_VIOLATION", {"constraint": constraint, "details": details})


class ResourceLimitError(EventPlanningError):
    """Exception for resource limit violations"""
    def __init__(self, resource: str, limit: Union[int, Decimal], requested: Union[int, Decimal]):
        self.resource = resource
        self.limit = limit
        self.requested = requested
        message = f"Resource limit exceeded for {resource}: requested {requested}, limit {limit}"
        super().__init__(message, "RESOURCE_LIMIT_ERROR", {
            "resource": resource, "limit": str(limit), "requested": str(requested)
        })


class TimelineGenerationError(EventPlanningError):
    """Exception for timeline generation failures"""
    def __init__(self, reason: str, context: EventContext = None):
        self.reason = reason
        self.context = context
        message = f"Timeline generation failed: {reason}"
        super().__init__(message, "TIMELINE_GENERATION_ERROR", {"reason": reason})


class BudgetAllocationError(EventPlanningError):
    """Exception for budget allocation failures"""
    def __init__(self, reason: str, budget_amount: Decimal = None):
        self.reason = reason
        self.budget_amount = budget_amount
        message = f"Budget allocation failed: {reason}"
        super().__init__(message, "BUDGET_ALLOCATION_ERROR", {"reason": reason})


def safe_execute(func: Callable, *args, **kwargs) -> tuple[Any, Optional[Exception]]:
    """
    Safely execute a function and return result and any exception.
    
    Returns:
        tuple: (result, exception) - result is None if exception occurred
    """
    try:
        result = func(*args, **kwargs)
        return result, None
    except Exception as e:
        logger.error(f"Error executing {func.__name__}: {str(e)}")
        return None, e


def validate_with_context(obj: Any, context_name: str = None) -> None:
    """
    Validate an object and provide contextual error information.
    
    Args:
        obj: Object to validate (must have validate() method)
        context_name: Name of the context for better error messages
    
    Raises:
        InputValidationError: If validation fails
    """
    try:
        if hasattr(obj, 'validate'):
            errors = obj.validate()
            if errors:
                context = f" in {context_name}" if context_name else ""
                raise InputValidationError(errors, context_name)
        else:
            raise ValueError(f"Object {type(obj)} does not have a validate method")
    except ValidationError as e:
        raise InputValidationError(e.errors, context_name)


def handle_validation_errors(func):
    """
    Decorator to handle validation errors and convert them to appropriate exceptions.
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValidationError as e:
            raise InputValidationError(e.errors)
        except ValueError as e:
            if "validation" in str(e).lower():
                raise InputValidationError([str(e)])
            raise
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            raise EventPlanningError(f"Unexpected error: {str(e)}")
    
    return wrapper


def safe_decimal_conversion_with_context(value: Any, field_name: str) -> Decimal:
    """
    Safely convert value to Decimal with contextual error information.
    
    Args:
        value: Value to convert
        field_name: Name of the field for error context
    
    Returns:
        Decimal: Converted value
    
    Raises:
        InputValidationError: If conversion fails
    """
    try:
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace('$', '').replace(',', '').strip()
            return Decimal(cleaned)
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise InputValidationError([f"Cannot convert '{value}' to decimal for field '{field_name}'"], field_name)


def safe_int_conversion_with_context(value: Any, field_name: str) -> int:
    """
    Safely convert value to int with contextual error information.
    
    Args:
        value: Value to convert
        field_name: Name of the field for error context
    
    Returns:
        int: Converted value
    
    Raises:
        InputValidationError: If conversion fails
    """
    try:
        return int(value)
    except (ValueError, TypeError):
        raise InputValidationError([f"Cannot convert '{value}' to integer for field '{field_name}'"], field_name)


def check_resource_limits(resource_name: str, requested: Union[int, Decimal], limit: Union[int, Decimal]) -> None:
    """
    Check if requested resource amount is within limits.
    
    Args:
        resource_name: Name of the resource
        requested: Requested amount
        limit: Maximum allowed amount
    
    Raises:
        ResourceLimitError: If limit is exceeded
    """
    if requested > limit:
        raise ResourceLimitError(resource_name, limit, requested)


def validate_event_context_constraints(context: EventContext) -> None:
    """
    Validate event context against business constraints.
    
    Args:
        context: Event context to validate
    
    Raises:
        ConstraintViolationError: If constraints are violated
    """
    # Guest count constraints
    if context.guest_count > 10000:
        raise ConstraintViolationError(
            "Maximum guest count", 
            f"Requested {context.guest_count} guests, maximum allowed is 10,000"
        )
    
    # Duration constraints
    if context.duration_days > 30:
        raise ConstraintViolationError(
            "Maximum event duration", 
            f"Requested {context.duration_days} days, maximum allowed is 30 days"
        )
    
    # Budget tier vs guest count reasonableness
    if context.budget_tier == context.budget_tier.BUDGET and context.guest_count > 500:
        raise ConstraintViolationError(
            "Budget tier compatibility",
            "Budget tier events typically don't support more than 500 guests"
        )


def create_user_friendly_error_message(error: Exception) -> Dict[str, Any]:
    """
    Create user-friendly error message from exception.
    
    Args:
        error: Exception to convert
    
    Returns:
        Dict containing user-friendly error information
    """
    if isinstance(error, InputValidationError):
        return {
            "error_type": "validation_error",
            "message": "Please check your input data",
            "details": error.validation_errors,
            "field": error.field,
            "suggestions": _get_validation_suggestions(error.validation_errors)
        }
    
    elif isinstance(error, ConstraintViolationError):
        return {
            "error_type": "constraint_error",
            "message": f"Event planning constraint violated: {error.constraint}",
            "details": error.details,
            "suggestions": _get_constraint_suggestions(error.constraint)
        }
    
    elif isinstance(error, ResourceLimitError):
        return {
            "error_type": "resource_limit_error",
            "message": f"Resource limit exceeded for {error.resource}",
            "details": {
                "requested": str(error.requested),
                "limit": str(error.limit)
            },
            "suggestions": _get_resource_limit_suggestions(error.resource)
        }
    
    elif isinstance(error, TimelineGenerationError):
        return {
            "error_type": "timeline_error",
            "message": "Unable to generate timeline",
            "details": error.reason,
            "suggestions": [
                "Try reducing the number of activities",
                "Increase the event duration",
                "Simplify cultural requirements"
            ]
        }
    
    elif isinstance(error, BudgetAllocationError):
        return {
            "error_type": "budget_error",
            "message": "Unable to allocate budget",
            "details": error.reason,
            "suggestions": [
                "Increase the total budget",
                "Reduce guest count",
                "Choose a lower budget tier"
            ]
        }
    
    else:
        return {
            "error_type": "general_error",
            "message": "An unexpected error occurred",
            "details": str(error),
            "suggestions": [
                "Please try again",
                "Contact support if the problem persists"
            ]
        }


def _get_validation_suggestions(errors: List[str]) -> List[str]:
    """Get suggestions for validation errors"""
    suggestions = []
    
    for error in errors:
        if "guest count" in error.lower():
            suggestions.append("Ensure guest count is a positive number within reasonable limits")
        elif "budget" in error.lower():
            suggestions.append("Check that budget amount is positive and reasonable for the event size")
        elif "date" in error.lower():
            suggestions.append("Verify dates are in correct format and within reasonable timeframe")
        elif "venue" in error.lower():
            suggestions.append("Ensure venue type is appropriate for the number of guests")
        elif "cultural" in error.lower():
            suggestions.append("Check that cultural requirements are compatible with event type")
    
    if not suggestions:
        suggestions.append("Please review and correct the highlighted fields")
    
    return list(set(suggestions))  # Remove duplicates


def _get_constraint_suggestions(constraint: str) -> List[str]:
    """Get suggestions for constraint violations"""
    if "guest count" in constraint.lower():
        return ["Reduce the number of guests", "Choose a larger venue type"]
    elif "duration" in constraint.lower():
        return ["Reduce event duration", "Split into multiple smaller events"]
    elif "budget" in constraint.lower():
        return ["Increase budget", "Choose a lower budget tier", "Reduce guest count"]
    else:
        return ["Review event parameters for compatibility"]


def _get_resource_limit_suggestions(resource: str) -> List[str]:
    """Get suggestions for resource limit violations"""
    if "guest" in resource.lower():
        return ["Reduce guest count", "Split into multiple events"]
    elif "budget" in resource.lower():
        return ["Reduce budget amount", "Consider a more modest event"]
    elif "duration" in resource.lower():
        return ["Reduce event duration", "Simplify event activities"]
    else:
        return ["Reduce the requested amount", "Consider alternative options"]


class ErrorCollector:
    """Utility class to collect and manage multiple errors"""
    
    def __init__(self):
        self.errors: List[str] = []
        self.warnings: List[str] = []
    
    def add_error(self, error: str) -> None:
        """Add an error message"""
        self.errors.append(error)
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message"""
        self.warnings.append(warning)
    
    def add_errors(self, errors: List[str]) -> None:
        """Add multiple error messages"""
        self.errors.extend(errors)
    
    def add_warnings(self, warnings: List[str]) -> None:
        """Add multiple warning messages"""
        self.warnings.extend(warnings)
    
    def has_errors(self) -> bool:
        """Check if there are any errors"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0
    
    def raise_if_errors(self, context: str = None) -> None:
        """Raise InputValidationError if there are any errors"""
        if self.has_errors():
            raise InputValidationError(self.errors, context)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all errors and warnings"""
        return {
            "errors": self.errors,
            "warnings": self.warnings,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings)
        }