from anthropic import Anthropic
from typing import List, Dict
from config import config
from backend.utils.logger import logger
import json

class ClaimExtractor:
    """
    Claim Extraction Agent
    Uses Claude to intelligently extract and understand claims
    from any text, regardless of grammar or spelling mistakes.
    """

    def __init__(self):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        logger.info("ClaimExtractor initialized")

    async def extract(self, text: str) -> List[Dict]:
        """
        Extract claims from text using Claude.
        Handles typos, bad grammar, short questions, and long articles.
        """
        prompt = f"""You are a claim extraction agent. Your job is to understand what the user is asking or claiming, even if they have typos, bad grammar, or write informally.

USER INPUT: "{text}"

Your tasks:
1. Understand what the user means (fix typos/grammar mentally)
2. Extract the core factual claim(s) that need to be verified
3. Rephrase each claim as a clear, grammatically correct statement

Rules:
- Always extract at least 1 claim, even for very short inputs
- For questions like "is X true?" extract the claim "X is true"
- For statements, extract them as-is but cleaned up
- Maximum 3 claims
- If input is a single topic/question, make it one claim

Respond with ONLY a JSON array:
[
  {{
    "claim_id": "claim_1",
    "text": "clear rephrased claim here",
    "original": "original text",
    "claim_type": "factual"
  }}
]

No other text, just the JSON array."""

        try:
            message = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=500,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            response = message.content[0].text.strip()

            # Parse JSON
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            claims = json.loads(response.strip())
            logger.info(f"Extracted {len(claims)} claims using Claude")
            return claims

        except Exception as e:
            logger.warning(f"Claude extraction failed: {e}, falling back to raw input")
            # Fallback: treat entire input as one claim
            return [{
                "claim_id": "claim_1",
                "text": text.strip(),
                "original": text,
                "claim_type": "factual"
            }]
