from ddgs import DDGS
from typing import List, Dict, Any
from backend.utils.logger import logger
from anthropic import Anthropic
from config import config
import hashlib, re, requests as http_requests

LANGUAGE_REGIONS = {
    "English":    {"region": "us"},
    "Arabic":     {"region": "ae"},
    "French":     {"region": "fr"},
    "Spanish":    {"region": "es"},
    "German":     {"region": "de"},
    "Italian":    {"region": "it"},
    "Portuguese": {"region": "br"},
    "Russian":    {"region": "ru"},
    "Chinese":    {"region": "cn"},
    "Japanese":   {"region": "jp"},
    "Turkish":    {"region": "tr"},
}

def extract_date(text: str) -> str:
    patterns = [
        r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})',
        r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})',
        r'<meta[^>]+property="article:published_time"[^>]+content="(\d{4}-\d{2}-\d{2})',
        r'<time[^>]+datetime="(\d{4}-\d{2}-\d{2})',
        r'/(\d{4}/\d{1,2}/\d{1,2})/',
        r'(\d{4}-\d{2}-\d{2})',
        r'(\d{4}/\d{1,2}/\d{1,2})',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            raw = m.group(1).strip()
            slash = re.match(r'(\d{4})/(\d{1,2})/(\d{1,2})', raw)
            if slash:
                return f"{slash.group(1)}-{slash.group(2).zfill(2)}-{slash.group(3).zfill(2)}"
            if re.match(r'\d{4}-\d{2}-\d{2}', raw):
                return raw[:10]
    return ""

def fetch_date_from_page(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        resp = http_requests.get(url, timeout=5, headers=headers)
        if resp.status_code == 200:
            return extract_date(resp.text[:8000])
    except Exception:
        pass
    return ""

def ask_claude_for_date(title: str, body: str, url: str) -> str:
    try:
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=20,
            temperature=0,
            messages=[{"role": "user", "content": (
                "Extract publication date. Return ONLY YYYY-MM-DD or 'Unknown'.\n\n"
                f"URL: {url}\nTitle: {title}\nText: {body[:300]}"
            )}]
        )
        result = msg.content[0].text.strip()
        if re.match(r'\d{4}-\d{2}-\d{2}', result):
            return result
    except Exception:
        pass
    return "Unknown"

def translate_text(text: str, target_language: str) -> str:
    if target_language == "English":
        return text
    try:
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=200,
            temperature=0,
            messages=[{"role": "user", "content": f"Translate to {target_language}. Return ONLY the translation:\n\n{text}"}]
        )
        return msg.content[0].text.strip()
    except Exception:
        return text

def translate_to_english(text: str, source_language: str) -> str:
    if source_language == "English":
        return text
    try:
        client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        msg = client.messages.create(
            model=config.CLAUDE_MODEL,
            max_tokens=300,
            temperature=0,
            messages=[{"role": "user", "content": f"Translate from {source_language} to English. Return ONLY the translation:\n\n{text[:500]}"}]
        )
        return msg.content[0].text.strip()
    except Exception:
        return text


class WebSearcher:
    def __init__(self, chroma_client):
        self.chroma = chroma_client
        logger.info("WebSearcher initialized")

    def search_and_index(self, claim: str, num_results: int = 5, language: str = "English") -> List[Dict[str, Any]]:
        logger.info(f"Searching web in {language} for: {claim[:60]}...")

        search_query = translate_text(claim, language)
        lang_config = LANGUAGE_REGIONS.get(language, {"region": "us"})

        chunks = []
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(search_query, max_results=num_results, region=lang_config["region"]))
            logger.info(f"Found {len(results)} results in {language}")

            texts, metadatas, ids = [], [], []
            for result in results:
                body  = result.get("body",  "").strip()
                url   = result.get("href",  "Unknown")
                title = result.get("title", "Unknown")
                if not body or len(body) < 30:
                    continue

                # 4-step date extraction
                pub_date = extract_date(url)
                if not pub_date:
                    pub_date = extract_date(body + " " + title)
                if not pub_date:
                    pub_date = fetch_date_from_page(url)
                if not pub_date:
                    pub_date = ask_claude_for_date(title, body, url)

                logger.info(f"Date for {url[:50]}: {pub_date}")

                if language != "English":
                    body  = translate_to_english(body,  language)
                    title = translate_to_english(title, language)

                chunk_id = "web_" + hashlib.md5(f"{url}{claim}".encode()).hexdigest()[:12]
                texts.append(body)
                metadatas.append({"source": url, "title": title, "date": pub_date, "language": language, "credibility": 0.75})
                ids.append(chunk_id)
                chunks.append({"text": body, "source": url, "title": title, "date": pub_date, "language": language, "credibility": 0.75, "similarity_score": 0.9})

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
