"""
Fixes web_search.py to properly extract real publication dates from articles.
Run from: C:\\Users\\aya\\Desktop\\verifai
"""

code = '''from ddgs import DDGS
from typing import List, Dict, Any
from backend.utils.logger import logger
import hashlib
import re
import requests as http_requests
from datetime import datetime

DATE_PATTERNS = [
    # JSON-LD / meta tags (most reliable)
    r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})',
    r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})',
    r'<meta[^>]+property="article:published_time"[^>]+content="(\d{4}-\d{2}-\d{2})',
    r'<meta[^>]+name="pubdate"[^>]+content="(\d{4}-\d{2}-\d{2})',
    r'<meta[^>]+name="date"[^>]+content="(\d{4}-\d{2}-\d{2})',
    # URL date patterns
    r'/(\d{4}/\d{2}/\d{2})/',
    r'/(\d{4}-\d{2}-\d{2})/',
    # Text patterns
    r'(\d{4}-\d{2}-\d{2})',
    r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
    r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
    r'(\d{1,2}/\d{1,2}/\d{4})',
]

def extract_date(text: str) -> str:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            raw = match.group(1).strip().replace("/", "-")
            # Normalize slashed URLs like 2024/03/15
            raw = re.sub(r"(\d{4})-(\d{2})-(\d{2}).*", r"\\1-\\2-\\3", raw)
            if re.match(r"\\d{4}-\\d{2}-\\d{2}", raw):
                return raw
            return raw
    return ""

def fetch_date_from_url(url: str) -> str:
    """Fetch article page and extract publication date"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        resp = http_requests.get(url, timeout=5, headers=headers, allow_redirects=True)
        if resp.status_code == 200:
            # Search in first 8000 chars where meta tags and JSON-LD usually are
            snippet = resp.text[:8000]
            date = extract_date(snippet)
            if date:
                return date
    except Exception as e:
        logger.debug(f"Could not fetch date from {url}: {e}")
    return ""

class WebSearcher:
    def __init__(self, chroma_client):
        self.chroma = chroma_client
        logger.info("WebSearcher initialized")

    def search_and_index(self, claim: str, num_results: int = 5) -> List[Dict[str, Any]]:
        logger.info(f"Searching web for: {claim[:60]}...")
        chunks = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(claim, max_results=num_results))
            logger.info(f"Found {len(results)} web results")

            texts, metadatas, ids = [], [], []
            for result in results:
                text  = result.get("body", "").strip()
                url   = result.get("href", "Unknown")
                title = result.get("title", "Unknown")
                if not text or len(text) < 30:
                    continue

                # 1. Try extracting date from snippet + title
                pub_date = extract_date(text + " " + title)

                # 2. Try extracting from URL path (e.g. /2024/03/15/)
                if not pub_date:
                    pub_date = extract_date(url)

                # 3. Fetch the actual page to find meta tags / JSON-LD
                if not pub_date:
                    pub_date = fetch_date_from_url(url)

                if not pub_date:
                    pub_date = "Unknown"

                logger.info(f"  Date for {url[:50]}: {pub_date}")

                chunk_id = "web_" + hashlib.md5(f"{url}{claim}".encode()).hexdigest()[:12]
                texts.append(text)
                metadatas.append({
                    "source": url,
                    "title": title,
                    "date": pub_date,
                    "credibility": 0.75
                })
                ids.append(chunk_id)
                chunks.append({
                    "text": text,
                    "source": url,
                    "title": title,
                    "date": pub_date,
                    "credibility": 0.75,
                    "similarity_score": 0.9
                })

            if texts:
                try:
                    self.chroma.collection.delete(ids=ids)
                except Exception:
                    pass
                self.chroma.add_documents(texts=texts, metadatas=metadatas, ids=ids)
                logger.info(f"Indexed {len(texts)} web chunks into ChromaDB")

        except Exception as e:
            logger.error(f"Web search failed: {e}")
        return chunks
'''

with open("backend/rag/web_search.py", "w", encoding="utf-8") as f:
    f.write(code)
print("OK: backend/rag/web_search.py updated with real date extraction")

# Also make sure fact_checker passes source_dates back to the API response
fc_path = "backend/agents/fact_checker.py"
fc = open(fc_path, encoding="utf-8").read()

if "source_dates" not in fc:
    old = 'verdict["sources"] = [chunk["source"] for chunk in evidence_chunks[:3]]'
    new = (
        'verdict["sources"] = [chunk["source"] for chunk in evidence_chunks[:3]]\n'
        '            verdict["source_dates"] = [chunk.get("date", "Unknown") for chunk in evidence_chunks[:3]]'
    )
    if old in fc:
        fc = fc.replace(old, new)
        with open(fc_path, "w", encoding="utf-8") as f:
            f.write(fc)
        print("OK: fact_checker.py updated to return source_dates")
    else:
        print("WARNING: Could not auto-patch fact_checker.py")
        print("         Manually add this line after verdict['sources'] = ...:")
        print("         verdict['source_dates'] = [chunk.get('date','Unknown') for chunk in evidence_chunks[:3]]")
else:
    print("OK: fact_checker.py already returns source_dates")

print("\nDone! Restart with: python run_demo.py")
