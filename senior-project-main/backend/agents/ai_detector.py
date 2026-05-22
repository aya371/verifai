from anthropic import Anthropic
from config import config
from backend.utils.logger import logger
from typing import Dict

AI_DETECTION_PROMPT = """You are an AI-generated content detector. Analyze the following text and determine if it was likely written by an AI (like GPT, Claude, Gemini) or by a human.

Look for these AI writing signals:
- Overly structured and balanced sentences
- Repetitive transitional phrases ("Furthermore", "Additionally", "In conclusion")
- Lack of personal voice, emotion, or unique perspective
- Unnaturally perfect grammar and punctuation
- Generic, non-specific examples
- Hedging language ("It is worth noting", "It is important to consider")
- Suspiciously comprehensive coverage of all angles

TEXT TO ANALYZE:
{text}

Respond ONLY with a JSON object:
{{
    "is_ai_generated": true or false,
    "confidence": 0-100,
    "label": "AI-Generated" | "Likely AI" | "Uncertain" | "Likely Human" | "Human-Written",
    "signals": ["list of detected signals that influenced the decision"],
    "reasoning": "One sentence explanation"
}}
"""

class AIDetector:
    def __init__(self):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        logger.info("AIDetector initialized")

    def detect(self, text: str) -> Dict:
        """Detect if text is AI-generated"""
        if not text or len(text.strip()) < 50:
            return {
                "is_ai_generated": False,
                "confidence": 0,
                "label": "Too short to analyze",
                "signals": [],
                "reasoning": "Text too short for reliable detection"
            }
        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=300,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": AI_DETECTION_PROMPT.format(text=text[:1500])
                }]
            )
            import json, re
            response = msg.content[0].text.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            return json.loads(response.strip())
        except Exception as e:
            logger.error(f"AI detection failed: {e}")
            return {
                "is_ai_generated": False,
                "confidence": 0,
                "label": "Detection failed",
                "signals": [],
                "reasoning": str(e)
            }
