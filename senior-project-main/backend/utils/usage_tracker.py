import json
from datetime import datetime, date
from pathlib import Path

class UsageTracker:
    """
    Tracks Claude API usage and costs
    Helps you stay within budget!
    """
    
    def __init__(self):
        self.log_file = Path("claude_usage.json")
        self.usage_data = self.load_usage()
    
    def load_usage(self):
        """Load usage from file"""
        try:
            with open(self.log_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "total_requests": 0,
                "total_cost": 0,
                "requests": []
            }
    
    def log_request(self, input_tokens: int, output_tokens: int, model: str = "haiku"):
        """Log API request with cost calculation"""
        # Haiku pricing (per million tokens)
        cost_per_input_million = 0.25
        cost_per_output_million = 1.25
        
        cost = (
            (input_tokens / 1_000_000) * cost_per_input_million +
            (output_tokens / 1_000_000) * cost_per_output_million
        )
        
        request_data = {
            "timestamp": datetime.now().isoformat(),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cost": cost,
            "model": model
        }
        
        self.usage_data["total_requests"] += 1
        self.usage_data["total_cost"] += cost
        self.usage_data["requests"].append(request_data)
        
        self.save_usage()
    
    def save_usage(self):
        """Save usage to file"""
        with open(self.log_file, 'w') as f:
            json.dump(self.usage_data, f, indent=2)
    
    def get_summary(self):
        """Get usage summary"""
        # Count today's requests
        today = date.today().isoformat()
        requests_today = sum(
            1 for r in self.usage_data["requests"]
            if r["timestamp"].startswith(today)
        )
        
        return {
            "total_requests": self.usage_data["total_requests"],
            "total_cost": round(self.usage_data["total_cost"], 4),
            "remaining_credit": round(5.0 - self.usage_data["total_cost"], 2),
            "requests_today": requests_today
        }