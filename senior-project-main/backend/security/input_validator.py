def validate_input(text: str, max_length: int = 10000):
    """
    Validate user input
    Prevents injection attacks and malformed data
    """
    if not text or not isinstance(text, str):
        raise ValueError("Input must be a non-empty string")
    
    if len(text) > max_length:
        raise ValueError(f"Input too long. Maximum {max_length} characters")
    
    # Remove potential injection patterns
    forbidden_patterns = ['<script>', 'javascript:', 'onerror=']
    for pattern in forbidden_patterns:
        if pattern.lower() in text.lower():
            raise ValueError(f"Forbidden pattern detected: {pattern}")
    
    return text.strip()