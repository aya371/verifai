"""
Input Validator
Save to: backend/security/input_validator.py

Validates and sanitizes user text input before processing.
Prevents XSS, script injection, and oversized payloads.
"""
import re
from typing import Optional


# Patterns that indicate injection attempts — case-insensitive
_INJECTION_PATTERNS = [
    # Script injection
    r"<script[\s>]",
    r"</script>",
    r"javascript\s*:",
    r"vbscript\s*:",
    r"data\s*:.*base64",
    # Event handlers (onerror=, onclick=, onload=, etc.)
    r"on\w{2,20}\s*=",
    # HTML tag injection for common dangerous tags
    r"<\s*(iframe|object|embed|form|input|button|link|meta|base|applet)[\s/>]",
    # Template/server-side injection
    r"\{\{.*\}\}",          # Jinja2 / Vue / Angular
    r"\$\{.*\}",            # JS template literals
    r"<%.*%>",              # JSP / EJS
    # SQL injection patterns (basic — SQLite in use)
    r";\s*(drop|delete|insert|update|alter|create|truncate)\s",
    r"--\s*$",              # SQL comment at end of line
    r"'\s*(or|and)\s+'?\d",  # ' OR '1'='1
    # Path traversal
    r"\.\./",
    r"\.\.\\",
]

_COMPILED = [re.compile(p, re.IGNORECASE | re.DOTALL) for p in _INJECTION_PATTERNS]


def validate_input(text: str, max_length: int = 10000) -> str:
    """
    Validate and sanitize user text input.

    - Rejects non-string or empty input
    - Enforces max length
    - Scans for injection / XSS patterns
    - Strips leading/trailing whitespace
    - Returns cleaned string on success, raises ValueError on failure

    Args:
        text:       The raw user-supplied string.
        max_length: Maximum allowed character count (default 10 000).

    Returns:
        Sanitized string.

    Raises:
        ValueError: If input is invalid, too long, or contains forbidden patterns.
    """
    if not text or not isinstance(text, str):
        raise ValueError("Input must be a non-empty string")

    if len(text) > max_length:
        raise ValueError(
            f"Input too long. Maximum {max_length} characters, got {len(text)}."
        )

    for pattern in _COMPILED:
        if pattern.search(text):
            # Don't reveal which pattern matched — avoids giving attackers a map
            raise ValueError("Input contains forbidden patterns and cannot be processed.")

    return text.strip()


def validate_name(name: str, max_length: int = 200) -> str:
    """
    Validate a human name field.
    Allows letters, spaces, hyphens, apostrophes, and Unicode name characters.
    Rejects digits-only strings and injection patterns.

    Args:
        name:       Raw name string.
        max_length: Maximum character count (default 200).

    Returns:
        Stripped name string.

    Raises:
        ValueError: If name is invalid.
    """
    if not name or not isinstance(name, str):
        raise ValueError("Name must be a non-empty string")

    name = name.strip()

    if len(name) > max_length:
        raise ValueError(f"Name too long. Maximum {max_length} characters.")

    if len(name) < 2:
        raise ValueError("Name must be at least 2 characters.")

    # Allow letters (including Unicode), spaces, hyphens, apostrophes, periods
    if not re.match(r"^[\w\s\-'.]+$", name, re.UNICODE):
        raise ValueError(
            "Name contains invalid characters. "
            "Only letters, spaces, hyphens, apostrophes, and periods are allowed."
        )

    # Reject pure-digit names
    if name.replace(" ", "").isdigit():
        raise ValueError("Name cannot consist only of digits.")

    # Still run injection check
    for pattern in _COMPILED:
        if pattern.search(name):
            raise ValueError("Name contains forbidden patterns.")

    return name


def validate_url(url: str, allowed_schemes: Optional[list] = None) -> str:
    """
    Basic URL validation for any user-supplied URLs.
    Prevents javascript:, data:, and vbscript: pseudo-URLs.

    Args:
        url:             Raw URL string.
        allowed_schemes: List of permitted schemes (default: ['http', 'https']).

    Returns:
        Stripped URL.

    Raises:
        ValueError: If URL scheme is not allowed.
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL must be a non-empty string")

    url = url.strip()
    allowed_schemes = allowed_schemes or ["http", "https"]

    scheme_match = re.match(r"^(\w[\w+\-.]*)\s*:", url, re.IGNORECASE)
    if not scheme_match:
        raise ValueError("URL must include a scheme (e.g. https://).")

    scheme = scheme_match.group(1).lower()
    if scheme not in allowed_schemes:
        raise ValueError(
            f"URL scheme '{scheme}' is not allowed. "
            f"Permitted schemes: {', '.join(allowed_schemes)}."
        )

    return url
