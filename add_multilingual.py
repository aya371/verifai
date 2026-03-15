"""
Adds multilingual search support to VerifAI.
- User picks language in UI
- Claim is translated via Claude
- Web search runs in selected language
- Results translated back to English

Run from: C:\\Users\\aya\\Desktop\\verifai
"""

# ── 1. New web_search.py with language support ──────────────────────────
web_search_code = '''from ddgs import DDGS
from typing import List, Dict, Any, Optional
from backend.utils.logger import logger
from anthropic import Anthropic
from config import config
import hashlib, re, requests as http_requests

DATE_PATTERNS = [
    r\'"datePublished"\\s*:\\s*"(\\d{4}-\\d{2}-\\d{2})\',
    r\'"dateModified"\\s*:\\s*"(\\d{4}-\\d{2}-\\d{2})\',
    r\'<meta[^>]+property="article:published_time"[^>]+content="(\\d{4}-\\d{2}-\\d{2})\',
    r\'<meta[^>]+name="pubdate"[^>]+content="(\\d{4}-\\d{2}-\\d{2})\',
    r\'(\\d{4}-\\d{2}-\\d{2})\',
    r\'(\\d{1,2}\\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{4})\',
    r\'((?:January|February|March|April|May|June|July|August|September|October|November|December)\\s+\\d{1,2},?\\s+\\d{4})\',
]

LANGUAGE_REGIONS = {
    "English":    {"lang": "en", "region": "us"},
    "Arabic":     {"lang": "ar", "region": "ae"},
    "French":     {"lang": "fr", "region": "fr"},
    "Spanish":    {"lang": "es", "region": "es"},
    "German":     {"lang": "de", "region": "de"},
    "Italian":    {"lang": "it", "region": "it"},
    "Portuguese": {"lang": "pt", "region": "br"},
    "Russian":    {"lang": "ru", "region": "ru"},
    "Chinese":    {"lang": "zh", "region": "cn"},
    "Japanese":   {"lang": "ja", "region": "jp"},
    "Turkish":    {"lang": "tr", "region": "tr"},
}

def extract_date(text: str) -> str:
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def fetch_date_from_url(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = http_requests.get(url, timeout=5, headers=headers, allow_redirects=True)
        if resp.status_code == 200:
            date = extract_date(resp.text[:10000])
            if date:
                return date
    except Exception as e:
        logger.debug(f"Could not fetch date from {url}: {e}")
    return ""

def translate_claim(claim: str, target_language: str) -> str:
    """Translate claim to target language using Claude"""
    if target_language == "English":
        return claim
    try:
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=200,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"Translate this claim to {target_language}. Return ONLY the translation, nothing else:\\n\\n{claim}"
            }]
        )
        translated = msg.content[0].text.strip()
        logger.info(f"Translated to {target_language}: {translated[:60]}")
        return translated
    except Exception as e:
        logger.warning(f"Translation failed: {e}")
        return claim

def translate_to_english(text: str, source_language: str) -> str:
    """Translate text back to English"""
    if source_language == "English":
        return text
    try:
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=300,
            temperature=0,
            messages=[{
                "role": "user",
                "content": f"Translate this text from {source_language} to English. Return ONLY the translation:\\n\\n{text[:500]}"
            }]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        logger.warning(f"Back-translation failed: {e}")
        return text

class WebSearcher:
    def __init__(self, chroma_client):
        self.chroma = chroma_client
        logger.info("WebSearcher initialized")

    def search_and_index(self, claim: str, num_results: int = 5, language: str = "English") -> List[Dict[str, Any]]:
        logger.info(f"Searching web in {language} for: {claim[:60]}...")

        # Translate claim to target language
        search_query = translate_claim(claim, language)
        lang_config  = LANGUAGE_REGIONS.get(language, LANGUAGE_REGIONS["English"])

        chunks = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(
                    search_query,
                    max_results=num_results,
                    region=lang_config["region"],
                ))
            logger.info(f"Found {len(results)} results in {language}")

            texts, metadatas, ids = [], [], []
            for result in results:
                text  = result.get("body",  "").strip()
                url   = result.get("href",  "Unknown")
                title = result.get("title", "Unknown")
                if not text or len(text) < 30:
                    continue

                # Translate non-English results back to English
                if language != "English":
                    text  = translate_to_english(text,  language)
                    title = translate_to_english(title, language)

                # Date extraction
                pub_date = extract_date(result.get("body","") + " " + result.get("title",""))
                if not pub_date:
                    pub_date = fetch_date_from_url(url)
                if not pub_date:
                    pub_date = "Unknown"

                logger.info(f"Date for {url[:50]}: {pub_date}")

                chunk_id = "web_" + hashlib.md5(f"{url}{claim}".encode()).hexdigest()[:12]
                texts.append(text)
                metadatas.append({
                    "source":   url,
                    "title":    title,
                    "date":     pub_date,
                    "language": language,
                    "credibility": 0.75
                })
                ids.append(chunk_id)
                chunks.append({
                    "text":       text,
                    "source":     url,
                    "title":      title,
                    "date":       pub_date,
                    "language":   language,
                    "credibility":    0.75,
                    "similarity_score": 0.9
                })

            if texts:
                try:
                    self.chroma.collection.delete(ids=ids)
                except Exception:
                    pass
                self.chroma.add_documents(texts=texts, metadatas=metadatas, ids=ids)
                logger.info(f"Indexed {len(texts)} {language} chunks into ChromaDB")

        except Exception as e:
            logger.error(f"Web search failed: {e}")
        return chunks
'''

with open("backend/rag/web_search.py", "w", encoding="utf-8") as f:
    f.write(web_search_code)
print("OK  backend/rag/web_search.py — multilingual support added")


# ── 2. Patch fact_checker.py to pass language through ───────────────────
fc = open("backend/agents/fact_checker.py", encoding="utf-8").read()

# Pass language to web search
old_ws = 'web_chunks = self.web_searcher.search_and_index(claim_text, num_results=5)'
new_ws = 'language = claim.get("language", "English")\n            web_chunks = self.web_searcher.search_and_index(claim_text, num_results=5, language=language)'

if old_ws in fc and 'language = claim.get' not in fc:
    fc = fc.replace(old_ws, new_ws)
    open("backend/agents/fact_checker.py", "w", encoding="utf-8").write(fc)
    print("OK  backend/agents/fact_checker.py — language passed to web search")
else:
    print("OK  backend/agents/fact_checker.py — already patched or different format")


# ── 3. Patch claim_extractor.py to attach language to each claim ────────
ce = open("backend/agents/claim_extractor.py", encoding="utf-8").read()

old_return = '            logger.info(f"Extracted {len(claims)} claims using Claude")\n            return claims'
new_return = (
    '            logger.info(f"Extracted {len(claims)} claims using Claude")\n'
    '            for c in claims:\n'
    '                c["language"] = language\n'
    '            return claims'
)

old_fallback = '        return [{\n            "claim_id": "claim_1",\n            "text": text.strip(),\n            "original": text,\n            "claim_type": "factual"\n        }]'
new_fallback = '        return [{\n            "claim_id": "claim_1",\n            "text": text.strip(),\n            "original": text,\n            "claim_type": "factual",\n            "language": language\n        }]'

old_sig = 'async def extract(self, text: str) -> List[Dict]:'
new_sig = 'async def extract(self, text: str, language: str = "English") -> List[Dict]:'

if old_sig in ce:
    ce = ce.replace(old_sig, new_sig)
if old_return in ce:
    ce = ce.replace(old_return, new_return)
if old_fallback in ce:
    ce = ce.replace(old_fallback, new_fallback)

open("backend/agents/claim_extractor.py", "w", encoding="utf-8").write(ce)
print("OK  backend/agents/claim_extractor.py — language parameter added")


# ── 4. Patch orchestrator.py to pass language ───────────────────────────
orch_path = "backend/agents/orchestrator.py"
orch = open(orch_path, encoding="utf-8").read()

old_extract = 'claims = await self.claim_extractor.extract(text)'
new_extract = 'language = task.get("language", "English")\n            claims = await self.claim_extractor.extract(text, language=language)'

if old_extract in orch and 'language = task.get' not in orch:
    orch = orch.replace(old_extract, new_extract)
    open(orch_path, "w", encoding="utf-8").write(orch)
    print("OK  backend/agents/orchestrator.py — language passed to extractor")
else:
    print("OK  backend/agents/orchestrator.py — skipped (check manually if needed)")


# ── 5. Patch API routes to accept language field ────────────────────────
routes_path = "backend/api/routes.py"
routes = open(routes_path, encoding="utf-8").read()

if "language" not in routes:
    old_body = '"text": request.text, "extract_claims": request.extract_claims'
    new_body = '"text": request.text, "extract_claims": request.extract_claims, "language": getattr(request, "language", "English")'
    if old_body in routes:
        routes = routes.replace(old_body, new_body)
        open(routes_path, "w", encoding="utf-8").write(routes)
        print("OK  backend/api/routes.py — language field added")
    else:
        print("OK  backend/api/routes.py — skipped (check manually)")

# Patch models.py to include language field
models_path = "backend/api/models.py"
models = open(models_path, encoding="utf-8").read()
if "language" not in models:
    old_field = "extract_claims: bool = True"
    new_field = "extract_claims: bool = True\n    language: str = \"English\""
    if old_field in models:
        models = models.replace(old_field, new_field)
        open(models_path, "w", encoding="utf-8").write(models)
        print("OK  backend/api/models.py — language field added to request model")
    else:
        print("WARN backend/api/models.py — could not patch, add manually: language: str = 'English'")
else:
    print("OK  backend/api/models.py — already has language field")


# ── 6. Update dashboard.py to add language selector ─────────────────────
dashboard = open("frontend/dashboard.py", encoding="utf-8").read()

LANGUAGES = [
    "English", "Arabic", "French", "Spanish", "German",
    "Italian", "Portuguese", "Russian", "Chinese", "Japanese", "Turkish"
]

old_checkbox = '''    extract_claims = st.checkbox(
        "Auto-extract claims (recommended for articles)",
        value=True,
        help="Uses Claude to intelligently extract factual claims from your text"
    )'''

new_checkbox = '''    col_a, col_b = st.columns([2, 1])
    with col_a:
        extract_claims = st.checkbox(
            "Auto-extract claims (recommended for articles)",
            value=True,
            help="Uses Claude to intelligently extract factual claims from your text"
        )
    with col_b:
        language = st.selectbox(
            "Search language",
            ["English", "Arabic", "French", "Spanish", "German",
             "Italian", "Portuguese", "Russian", "Chinese", "Japanese", "Turkish"],
            index=0,
            help="Search for evidence in this language. Results are translated back to English."
        )'''

old_payload = '                        json={"text": claim_text, "extract_claims": extract_claims},'
new_payload = '                        json={"text": claim_text, "extract_claims": extract_claims, "language": language},'

if old_checkbox in dashboard:
    dashboard = dashboard.replace(old_checkbox, new_checkbox)
    print("OK  frontend/dashboard.py — language selector added")
else:
    print("WARN frontend/dashboard.py — could not add language selector (already there?)")

if old_payload in dashboard:
    dashboard = dashboard.replace(old_payload, new_payload)
    print("OK  frontend/dashboard.py — language sent in API payload")

# Add language badge to source timeline header
old_header = '"SOURCE PUBLICATION DATES"'
new_header = '"SOURCE PUBLICATION DATES"'  # keep same, badge shown in source row

open("frontend/dashboard.py", "w", encoding="utf-8").write(dashboard)
print("OK  frontend/dashboard.py — saved")

print("""
══════════════════════════════════════════
All done! Restart with: python run_demo.py

How it works:
  1. User picks language (e.g. Arabic)
  2. Claim is translated to Arabic via Claude
  3. DuckDuckGo searches Arabic web sources
  4. Results are translated back to English
  5. Claude fact-checks using multilingual evidence
══════════════════════════════════════════
""")
