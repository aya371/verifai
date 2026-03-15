from datetime import datetime, timedelta
from typing import Dict

# In-memory rate limit tracker (use Redis in production)
user_requests: Dict[str, list] = {}

def check_rate_limit(user_id: str, max_requests: int = 10, window_minutes: int = 1):
    """
    Rate limit: 10 requests per minute per user
    """
    now = datetime.now()
    
    if user_id not in user_requests:
        user_requests[user_id] = []
    
    # Remove old requests outside window
    user_requests[user_id] = [
        req_time for req_time in user_requests[user_id]
        if now - req_time < timedelta(minutes=window_minutes)
    ]
    
    # Check limit
    if len(user_requests[user_id]) >= max_requests:
        raise Exception(f"Rate limit exceeded. Max {max_requests} requests per {window_minutes} minute(s)")
    
    # Log this request
    user_requests[user_id].append(now)