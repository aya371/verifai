"""
Fix script - real date extraction + one timeline row per source
Run from: C:\\Users\\aya\\Desktop\\verifai
"""
import re

# 1. Fix web_search.py with better date extraction
web_search_code = '''from ddgs import DDGS
from typing import List, Dict, Any
from backend.utils.logger import logger
import hashlib
import re
import requests
from datetime import datetime

def extract_date_from_text(text: str) -> str:
    patterns = [
        r"(\\d{4}-\\d{2}-\\d{2})",
        r"(\\d{1,2}[/-]\\d{1,2}[/-]\\d{4})",
        r"((?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\.?\\s+\\d{1,2},?\\s+\\d{4})",
        r"(\\d{1,2}\\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\\s+\\d{4})",
        r\'published[:\\\\s]+([\\\\w\\\\s,]+\\\\d{4})\',
        r\'"datePublished"\\\\s*:\\\\s*"(\\\\d{4}-\\\\d{2}-\\\\d{2})\',
        r\'"dateModified"\\\\s*:\\\\s*"(\\\\d{4}-\\\\d{2}-\\\\d{2})\',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

def fetch_page_date(url: str) -> str:
    try:
        headers = {"User-Agent": "Mozilla/5.0"}
        resp = requests.get(url, timeout=4, headers=headers)
        date = extract_date_from_text(resp.text[:5000])
        return date
    except Exception:
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
                text = result.get("body", "").strip()
                url = result.get("href", "Unknown")
                title = result.get("title", "Unknown")
                if not text or len(text) < 30:
                    continue
                pub_date = extract_date_from_text(text + " " + title)
                if not pub_date:
                    pub_date = fetch_page_date(url)
                if not pub_date:
                    pub_date = "Unknown"
                chunk_id = "web_" + hashlib.md5(f"{url}{claim}".encode()).hexdigest()[:12]
                texts.append(text)
                metadatas.append({"source": url, "title": title, "date": pub_date, "credibility": 0.75})
                ids.append(chunk_id)
                chunks.append({"text": text, "source": url, "title": title, "date": pub_date, "credibility": 0.75, "similarity_score": 0.9})
            if texts:
                try:
                    self.chroma.collection.delete(ids=ids)
                except Exception:
                    pass
                self.chroma.add_documents(texts=texts, metadatas=metadatas, ids=ids)
                logger.info(f"Indexed {len(texts)} web chunks")
        except Exception as e:
            logger.error(f"Web search failed: {e}")
        return chunks
'''

with open('backend/rag/web_search.py', 'w', encoding='utf-8') as f:
    f.write(web_search_code)
print("OK: web_search.py updated")

# 2. Build the new per-source timeline render function
new_render = """def render_source_timeline(sources: list, source_dates: list, verdict: str):
    if verdict == "REFUTED":
        dot_color = "#e17055"
    elif verdict == "SUPPORTED":
        dot_color = "#00b894"
    else:
        dot_color = "#74b9ff"

    if not source_dates:
        source_dates = ["Unknown"] * len(sources)

    rows_html = ""
    for i, (source, date) in enumerate(zip(sources[:5], source_dates[:5])):
        domain = source.replace("https://", "").replace("http://", "").split("/")[0]
        domain = (domain[:40] + "...") if len(domain) > 40 else domain
        date_label = date if date and date != "Unknown" else "Date unknown"
        pct = 15 + int(i * 16)
        rows_html += (
            '<div style="margin-bottom:14px;">'
            '<div style="display:flex;align-items:center;gap:8px;margin-bottom:5px;">'
            '<span style="width:8px;height:8px;border-radius:50%;background:' + dot_color + ';flex-shrink:0;display:inline-block;"></span>'
            '<span style="font-size:12px;font-family:monospace;color:#e0e0e0;flex:1;">' + domain + '</span>'
            '<span style="font-size:11px;font-family:monospace;color:white;background:#1e1e2e;border:1px solid #333;padding:2px 10px;border-radius:4px;flex-shrink:0;">' + date_label + '</span>'
            '</div>'
            '<div style="position:relative;height:6px;background:#1a1a2e;border-radius:3px;">'
            '<div style="position:absolute;left:0;top:0;height:100%;width:' + str(pct) + '%;background:linear-gradient(90deg,#2a2a4e,' + dot_color + '33);border-radius:3px;"></div>'
            '<div style="position:absolute;top:50%;left:' + str(pct) + '%;transform:translate(-50%,-50%);width:12px;height:12px;border-radius:50%;background:' + dot_color + ';border:2px solid #0e0e1a;box-shadow:0 0 6px ' + dot_color + '88;"></div>'
            '</div>'
            '</div>'
        )

    html = (
        '<div style="background:#0e0e1a;border:1px solid #2a2a3e;border-radius:10px;padding:16px 20px;margin-top:14px;">'
        '<div style="font-size:10px;font-family:monospace;color:#555;letter-spacing:2px;margin-bottom:14px;">SOURCE PUBLICATION DATES</div>'
        + rows_html +
        '<div style="display:flex;justify-content:space-between;font-size:10px;font-family:monospace;color:#333;margin-top:6px;border-top:1px solid #1a1a2e;padding-top:8px;">'
        '<span>OLDER</span><span>RECENT</span>'
        '</div>'
        '</div>'
    )
    st.markdown(html, unsafe_allow_html=True)"""

# 3. Update dashboard.py
dashboard = open('frontend/dashboard.py', encoding='utf-8').read()

# Replace old render function
dashboard = re.sub(
    r'def render_(?:timeline|source_timeline)\(.*?st\.markdown\(html, unsafe_allow_html=True\)',
    new_render,
    dashboard,
    flags=re.DOTALL
)

# Replace the render call
dashboard = re.sub(
    r'# (?:Per-source|Timeline|Evidence|Source Publication) timeline.*?render_(?:timeline|source_timeline)\(.*?\)',
    """# Per-source timeline
                                render_source_timeline(
                                    sources=claim_result.get('sources', []),
                                    source_dates=claim_result.get('source_dates', []),
                                    verdict=claim_result['verdict']
                                )""",
    dashboard,
    flags=re.DOTALL
)

with open('frontend/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(dashboard)
print("OK: dashboard.py updated")

# 4. Make sure fact_checker returns source_dates
fc = open('backend/agents/fact_checker.py', encoding='utf-8').read()
if 'source_dates' not in fc:
    fc = fc.replace(
        'verdict["sources"] = [chunk["source"] for chunk in evidence_chunks[:3]]',
        'verdict["sources"] = [chunk["source"] for chunk in evidence_chunks[:3]]\n'
        '            verdict["source_dates"] = [chunk.get("date", "Unknown") for chunk in evidence_chunks[:3]]'
    )
    with open('backend/agents/fact_checker.py', 'w', encoding='utf-8') as f:
        f.write(fc)
    print("OK: fact_checker.py updated")
else:
    print("OK: fact_checker.py already has source_dates")

print("\nAll done! Refresh your browser.")
