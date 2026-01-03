"""
Input validation and sanitization utilities.
Provides secure input handling for user prompts and other inputs.
"""
import re
import logging
from typing import Tuple, Optional
from agents import PromptType

logger = logging.getLogger(__name__)

# Configuration constants
MAX_PROMPT_LENGTH = 10000  # Maximum characters in a prompt
MIN_PROMPT_LENGTH = 1  # Minimum characters in a prompt
MAX_USERNAME_LENGTH = 100
MAX_EMAIL_LENGTH = 255


def sanitize_prompt(prompt: str) -> str:
    """
    Sanitize user prompt by removing or escaping harmful characters.
    
    This function:
    - Strips leading/trailing whitespace
    - Removes control characters (except newlines, tabs)
    - Normalizes whitespace
    - Truncates to max length
    
    Args:
        prompt: Raw user input prompt
    
    Returns:
        Sanitized prompt string
    
    Note:
        This is a conservative sanitization that preserves user intent
        while removing potentially harmful content. For prompt optimization,
        we want to preserve most characters to allow creative prompts.
    """
    if not prompt:
        return ""
    
    # Strip leading/trailing whitespace
    sanitized = prompt.strip()
    
    # Remove control characters (keep newlines \n, tabs \t, carriage returns \r)
    # This removes potentially harmful characters while preserving formatting
    sanitized = re.sub(r'[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    # Normalize multiple consecutive newlines (max 2 consecutive)
    sanitized = re.sub(r'\n{3,}', '\n\n', sanitized)
    
    # Truncate to max length (preserve words, don't cut mid-word if possible)
    if len(sanitized) > MAX_PROMPT_LENGTH:
        truncated = sanitized[:MAX_PROMPT_LENGTH]
        # Try to cut at word boundary
        last_space = truncated.rfind(' ')
        if last_space > MAX_PROMPT_LENGTH * 0.9:  # If space is within last 10%
            sanitized = truncated[:last_space] + "..."
        else:
            sanitized = truncated + "..."
        logger.warning(f"Prompt truncated from {len(prompt)} to {len(sanitized)} characters")
    
    return sanitized


def validate_prompt(prompt: str) -> Tuple[bool, Optional[str]]:
    """
    Validate prompt input.
    
    Args:
        prompt: Prompt to validate
    
    Returns:
        Tuple of (is_valid, error_message)
        - is_valid: True if prompt is valid, False otherwise
        - error_message: Error message if invalid, None if valid
    """
    if not prompt:
        return False, "Prompt cannot be empty"
    
    if not isinstance(prompt, str):
        return False, "Prompt must be a string"
    
    # Check length
    if len(prompt) < MIN_PROMPT_LENGTH:
        return False, f"Prompt must be at least {MIN_PROMPT_LENGTH} character(s)"
    
    if len(prompt) > MAX_PROMPT_LENGTH:
        return False, f"Prompt must be no more than {MAX_PROMPT_LENGTH} characters"
    
    # Check for only whitespace
    if not prompt.strip():
        return False, "Prompt cannot be only whitespace"
    
    return True, None


def validate_prompt_type(prompt_type: str) -> Tuple[bool, Optional[PromptType], Optional[str]]:
    """
    Validate and convert prompt type string to enum.
    
    Args:
        prompt_type: Prompt type string from UI
    
    Returns:
        Tuple of (is_valid, PromptType_enum, error_message)
        - is_valid: True if valid, False otherwise
        - PromptType_enum: Valid PromptType enum or None
        - error_message: Error message if invalid, None if valid
    """
    if not prompt_type:
        return False, None, "Prompt type is required"
    
    try:
        prompt_type_enum = PromptType(prompt_type.lower())
        return True, prompt_type_enum, None
    except ValueError:
        valid_types = [pt.value for pt in PromptType]
        return False, None, f"Invalid prompt type. Must be one of: {', '.join(valid_types)}"


def validate_username(username: str) -> Tuple[bool, Optional[str]]:
    """
    Validate username.
    
    Args:
        username: Username to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not username:
        return False, "Username cannot be empty"
    
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    
    if len(username) > MAX_USERNAME_LENGTH:
        return False, f"Username must be no more than {MAX_USERNAME_LENGTH} characters"
    
    # Allow alphanumeric, underscores, hyphens
    if not re.match(r'^[a-zA-Z0-9_-]+$', username):
        return False, "Username can only contain letters, numbers, underscores, and hyphens"
    
    return True, None


def validate_email(email: str) -> Tuple[bool, Optional[str]]:
    """
    Validate email address.
    
    Args:
        email: Email to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not email:
        return False, "Email cannot be empty"
    
    if len(email) > MAX_EMAIL_LENGTH:
        return False, f"Email must be no more than {MAX_EMAIL_LENGTH} characters"
    
    # Basic email regex (RFC 5322 simplified)
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Invalid email format"
    
    return True, None


def sanitize_and_validate_prompt(prompt: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Sanitize and validate prompt in one step.
    
    Args:
        prompt: Raw prompt input
    
    Returns:
        Tuple of (is_valid, sanitized_prompt, error_message)
        - is_valid: True if valid, False otherwise
        - sanitized_prompt: Sanitized prompt or None if invalid
        - error_message: Error message if invalid, None if valid
    """
    # Validate first (before sanitization to catch length issues)
    is_valid, error = validate_prompt(prompt)
    if not is_valid:
        return False, None, error
    
    # Sanitize
    sanitized = sanitize_prompt(prompt)
    
    # Validate again after sanitization (length might have changed)
    is_valid, error = validate_prompt(sanitized)
    if not is_valid:
        return False, None, error
    
    return True, sanitized, None