"""
Fix script - rewrites all necessary files to make web search work properly
Run this from: C:\\Users\\aya\\Desktop\\verifai
"""

# 1. Fix web_search.py - fetch live results and use them directly
web_search = '''from ddgs import DDGS
from typing import List, Dict, Any
from backend.utils.logger import logger
import hashlib

class WebSearcher:
    def __init__(self, chroma_client):
        self.chroma = chroma_client
        logger.info("WebSearcher initialized")

    def search_and_store(self, claim: str, num_results: int = 5) -> List[Dict[str, Any]]:
        """Search web, store in ChromaDB, and return chunks directly."""
        logger.info(f"Web searching: {claim[:60]}...")
        chunks = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(claim, max_results=num_results))
            logger.info(f"Got {len(results)} results from web")
            texts, metadatas, ids = [], [], []
            for result in results:
                text = result.get("body", "").strip()
                url = result.get("href", "Unknown")
                title = result.get("title", "Unknown")
                if not text or len(text) < 30:
                    continue
                chunk_id = "web_" + hashlib.md5(f"{url}{claim}".encode()).hexdigest()[:12]
                texts.append(text)
                metadatas.append({"source": url, "title": title, "date": "2025", "credibility": 0.75})
                ids.append(chunk_id)
                chunks.append({"text": text, "source": url, "date": "2025", "credibility": 0.75, "similarity_score": 0.9})
            if texts:
                try:
                    self.chroma.collection.delete(ids=ids)
                except Exception:
                    pass
                self.chroma.add_documents(texts=texts, metadatas=metadatas, ids=ids)
                logger.info(f"Stored {len(texts)} web chunks in ChromaDB")
        except Exception as e:
            logger.error(f"Web search failed: {e}")
        return chunks
'''

# 2. Fix fact_checker.py - use web results directly as evidence
fact_checker = '''from anthropic import Anthropic
from typing import Dict, Any, List
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
        logger.info("FactChecker initialized with live web search")

    async def verify(self, claim: Dict[str, Any]) -> Dict[str, Any]:
        claim_text = claim["text"]
        logger.info(f"Verifying: {claim_text[:60]}...")

        # Step 1: Search web and get fresh evidence directly
        logger.info("Fetching live web evidence...")
        web_chunks = self.web_searcher.search_and_store(claim_text, num_results=5)

        # Step 2: Use web results directly if available, else fall back to ChromaDB
        if web_chunks:
            evidence_chunks = web_chunks[:5]
            logger.info(f"Using {len(evidence_chunks)} live web chunks as evidence")
        else:
            logger.info("No web results, falling back to ChromaDB...")
            evidence_chunks = self.retriever.retrieve(claim_text, top_k=config.RAG_TOP_K)

        if not evidence_chunks:
            return {
                "claim_text": claim_text,
                "verdict": "INCONCLUSIVE",
                "confidence": 0,
                "reasoning": "No evidence found from web or knowledge base",
                "sources": [],
                "flags": ["no_evidence_found"]
            }

        logger.info(f"Building prompt with {len(evidence_chunks)} evidence chunks...")
        prompt = build_fact_check_prompt(claim_text, evidence_chunks)

        try:
            logger.info("Calling Claude API...")
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
            logger.info(f"Verdict: {verdict.get('verdict')} ({verdict.get('confidence')}%)")
            return verdict
        except Exception as e:
            logger.error(f"Claude API error: {e}")
            return {
                "claim_text": claim_text,
                "verdict": "ERROR",
                "confidence": 0,
                "reasoning": str(e),
                "sources": [],
                "flags": ["api_error"]
            }

    def _parse_response(self, response_text: str) -> Dict:
        try:
            response_text = response_text.strip()
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            return json.loads(response_text.strip())
        except Exception:
            if "REFUTED" in response_text.upper() or "FALSE" in response_text.upper():
                verdict = "REFUTED"
            elif "SUPPORTED" in response_text.upper() or "TRUE" in response_text.upper():
                verdict = "SUPPORTED"
            else:
                verdict = "INCONCLUSIVE"
            return {"verdict": verdict, "confidence": 50, "reasoning": response_text[:200], "flags": ["parse_error"]}
'''

with open('backend/rag/web_search.py', 'w', encoding='utf-8') as f:
    f.write(web_search)
print("OK: web_search.py written")

with open('backend/agents/fact_checker.py', 'w', encoding='utf-8') as f:
    f.write(fact_checker)
print("OK: fact_checker.py written")

# Test web search works
print("\nTesting web search...")
try:
    from ddgs import DDGS
    with DDGS() as ddgs:
        r = list(ddgs.text("burj khalifa location", max_results=2))
    if r:
        print(f"OK: Web search works! Got {len(r)} results")
        print(f"   First: {r[0]['href']}")
        print(f"   Body: {r[0]['body'][:100]}")
    else:
        print("FAIL: Web search returned no results")
except Exception as e:
    print(f"FAIL: Web search error: {e}")

print("\nAll done! Run: python run_demo.py")