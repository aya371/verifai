open('backend/agents/fact_checker.py', 'w', encoding='utf-8').write('''import os
from anthropic import Anthropic
from typing import Dict, Any
from config import config
from backend.rag.retriever import Retriever
from backend.rag.prompts import build_fact_check_prompt
from backend.rag.web_search import WebSearcher
from backend.utils.logger import logger
import json

class FactChecker:
    def __init__(self, chroma_client, usage_tracker):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.chroma_client = chroma_client
        self.retriever = Retriever(chroma_client)
        self.web_searcher = WebSearcher(chroma_client)
        self.usage_tracker = usage_tracker
        logger.info("FactChecker initialized")

    async def verify(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        claim_text = claim["text"]
        logger.info(f"Verifying: {claim_text[:50]}...")
        self.web_searcher.search_and_index(claim_text, num_results=3)
        evidence_chunks = self.retriever.retrieve(claim_text, top_k=config.RAG_TOP_K)
        if not evidence_chunks:
            return {"claim_text": claim_text, "verdict": "INCONCLUSIVE", "confidence": 0, "reasoning": "No relevant sources found", "sources": [], "flags": ["no_evidence_found"]}
        prompt = build_fact_check_prompt(claim_text, evidence_chunks)
        try:
            message = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=config.CLAUDE_MAX_TOKENS,
                temperature=config.CLAUDE_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = message.content[0].text
            self.usage_tracker.log_request(
                input_tokens=message.usage.input_tokens,
                output_tokens=message.usage.output_tokens,
                model=config.CLAUDE_MODEL
            )
            verdict = self._parse_response(response_text)
            verdict["claim_text"] = claim_text
            verdict["sources"] = [chunk["source"] for chunk in evidence_chunks[:3]]
            return verdict
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {"claim_text": claim_text, "verdict": "ERROR", "confidence": 0, "reasoning": str(e), "sources": [], "flags": ["api_error"]}

    def _parse_response(self, response_text: str) -> Dict:
        try:
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            return json.loads(response_text.strip())
        except:
            if "REFUTED" in response_text.upper() or "FALSE" in response_text.upper():
                verdict = "REFUTED"
            elif "SUPPORTED" in response_text.upper() or "TRUE" in response_text.upper():
                verdict = "SUPPORTED"
            else:
                verdict = "INCONCLUSIVE"
            return {"verdict": verdict, "confidence": 50, "reasoning": response_text[:200], "flags": ["parse_error"]}
''')
print("fact_checker.py written successfully!")
