"""
Fix script - updates web_search.py to capture real publication dates
and updates dashboard.py timeline to show dates on the axis
Run from: C:\\Users\\aya\\Desktop\\verifai
"""
from datetime import datetime

# 1. Update web_search.py to extract real dates from results
web_search = '''from ddgs import DDGS
from typing import List, Dict, Any
from backend.utils.logger import logger
import hashlib
import re
from datetime import datetime

def extract_date(result: dict) -> str:
    """Try to extract a real publication date from a search result"""
    # DuckDuckGo sometimes returns a 'published' field
    for field in ['published', 'pubdate', 'date']:
        val = result.get(field, "")
        if val:
            return str(val)[:10]

    # Try to find a date pattern in the body or title
    text = result.get("body", "") + " " + result.get("title", "")
    patterns = [
        r'(\\d{4}-\\d{2}-\\d{2})',               # 2024-03-15
        r'(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \\d{1,2},? \\d{4}',
        r'\\d{1,2} (Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \\d{4}',
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)

    return datetime.now().strftime("%Y-%m-%d")

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
                pub_date = extract_date(result)
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

with open('backend/rag/web_search.py', 'w', encoding='utf-8') as f:
    f.write(web_search)
print("OK: web_search.py updated with real date extraction")

# 2. Update the render_timeline function in dashboard.py
dashboard_code = open('frontend/dashboard.py', encoding='utf-8').read()

old_fn = '''def render_timeline(claim_text: str, verdict: str, sources: list, confidence: float):
    """Render a visual timeline for a claim and its evidence"""
    if verdict == "REFUTED":
        ec = "refute"
        vc = "#e17055"
    elif verdict == "SUPPORTED":
        ec = "support"
        vc = "#00b894"
    else:
        ec = "neutral"
        vc = "#6c757d"

    today = datetime.now().strftime("%b %Y")
    num_sources = max(len(sources), 1)

    points = []
    points.append(\'<div class="timeline-point" style="left:5%"><div class="timeline-dot claim"></div><span class="timeline-label bottom">CLAIM</span></div>\')
    for i, source in enumerate(sources[:4]):
        pct = 40 + int(i * 50 / num_sources)
        lc = "top" if i % 2 == 0 else "bottom"
        domain = source.replace("https://","").replace("http://","").split("/")[0][:18]
        points.append(\'<div class="timeline-point" style="left:\' + str(pct) + \'%"><div class="timeline-dot \' + ec + \'"></div><span class="timeline-label \' + lc + \'">\' + domain + \'</span></div>\')
    points.append(\'<div class="timeline-point" style="left:95%"><div class="timeline-dot" style="background:#a29bfe;border-color:#a29bfe;width:12px;height:12px;"></div><span class="timeline-label top">\' + today + \'</span></div>\')

    html = (
        \'<div class="timeline-container">\'
        \'<div style="font-size:12px;color:#adb5bd;font-family:monospace;margin-bottom:8px;">EVIDENCE TIMELINE &nbsp;\'
        \'<span style="background:\' + vc + \';color:white;padding:2px 10px;border-radius:10px;font-size:11px;">\' + verdict + \' - \' + str(int(confidence)) + \'% confidence</span>\'
        \'</div>\'
        \'<div class="timeline-axis">\' + "".join(points) + \'</div>\'
        \'<div class="timeline-legend">\'
        \'<div class="legend-item"><span class="legend-dot" style="background:#e94560;"></span> Claim</div>\'
        \'<div class="legend-item"><span class="legend-dot" style="background:\' + vc + \';"></span> Evidence</div>\'
        \'<div class="legend-item"><span class="legend-dot" style="background:#a29bfe;"></span> Today</div>\'
        \'</div></div>\'
    )
    st.markdown(html, unsafe_allow_html=True)'''

new_fn = '''def render_timeline(claim_text: str, verdict: str, sources: list, confidence: float, source_dates: list = None):
    """Render a publication date timeline for evidence sources"""
    if verdict == "REFUTED":
        ec = "refute"
        vc = "#e17055"
    elif verdict == "SUPPORTED":
        ec = "support"
        vc = "#00b894"
    else:
        ec = "neutral"
        vc = "#6c757d"

    today_str = datetime.now().strftime("%b %Y")
    if not source_dates:
        source_dates = [datetime.now().strftime("%Y-%m-%d")] * len(sources)

    points = []
    points.append(
        \'<div class="timeline-point" style="left:5%">\'
        \'<div class="timeline-dot claim"></div>\'
        \'<span class="timeline-label bottom">YOUR CLAIM</span>\'
        \'</div>\'
    )

    num = max(len(sources), 1)
    for i, (source, date) in enumerate(zip(sources[:4], source_dates[:4])):
        pct = 30 + int(i * 45 / num)
        lc = "top" if i % 2 == 0 else "bottom"
        domain = source.replace("https://","").replace("http://","").split("/")[0][:18]
        label = date + "<br>" + domain if date else domain
        points.append(
            \'<div class="timeline-point" style="left:\' + str(pct) + \'%">\'
            \'<div class="timeline-dot \' + ec + \'"></div>\'
            \'<span class="timeline-label \' + lc + \'">\' + label + \'</span>\'
            \'</div>\'
        )

    points.append(
        \'<div class="timeline-point" style="left:95%">\'
        \'<div class="timeline-dot" style="background:#a29bfe;border-color:#a29bfe;width:12px;height:12px;"></div>\'
        \'<span class="timeline-label top">TODAY<br>\' + today_str + \'</span>\'
        \'</div>\'
    )

    html = (
        \'<div class="timeline-container">\'
        \'<div style="font-size:12px;color:#adb5bd;font-family:monospace;margin-bottom:8px;">\'
        \'SOURCE PUBLICATION TIMELINE &nbsp;\'
        \'<span style="background:\' + vc + \';color:white;padding:2px 10px;border-radius:10px;font-size:11px;">\' + verdict + \' — \' + str(int(confidence)) + \'% confidence</span>\'
        \'</div>\'
        \'<div class="timeline-axis">\' + "".join(points) + \'</div>\'
        \'<div class="timeline-legend">\'
        \'<div class="legend-item"><span class="legend-dot" style="background:#e94560;"></span> Your Claim</div>\'
        \'<div class="legend-item"><span class="legend-dot" style="background:\' + vc + \';"></span> Evidence (with pub. date)</div>\'
        \'<div class="legend-item"><span class="legend-dot" style="background:#a29bfe;"></span> Today</div>\'
        \'</div></div>\'
    )
    st.markdown(html, unsafe_allow_html=True)'''

if old_fn in dashboard_code:
    dashboard_code = dashboard_code.replace(old_fn, new_fn)
    print("OK: render_timeline updated in dashboard.py")
else:
    print("WARNING: Could not find old render_timeline — updating render call only")

# Also update the call to pass dates
old_call = '''                                # Timeline view
                                st.markdown("**Evidence Timeline:**")
                                render_timeline(
                                    claim_text=claim_result[\'claim_text\'],
                                    verdict=claim_result[\'verdict\'],
                                    sources=claim_result.get(\'sources\', []),
                                    confidence=claim_result[\'confidence\']
                                )'''

new_call = '''                                # Timeline view
                                st.markdown("**Source Publication Timeline:**")
                                render_timeline(
                                    claim_text=claim_result[\'claim_text\'],
                                    verdict=claim_result[\'verdict\'],
                                    sources=claim_result.get(\'sources\', []),
                                    confidence=claim_result[\'confidence\'],
                                    source_dates=claim_result.get(\'source_dates\', [])
                                )'''

if old_call in dashboard_code:
    dashboard_code = dashboard_code.replace(old_call, new_call)
    print("OK: Timeline call updated in dashboard.py")

with open('frontend/dashboard.py', 'w', encoding='utf-8') as f:
    f.write(dashboard_code)
print("OK: dashboard.py saved")

# 3. Update fact_checker to pass source dates back in verdict
fact_checker = open('backend/agents/fact_checker.py', encoding='utf-8').read()
old_sources = 'verdict["sources"] = [chunk["source"] for chunk in evidence_chunks[:3]]'
new_sources = (
    'verdict["sources"] = [chunk["source"] for chunk in evidence_chunks[:3]]\n'
    '            verdict["source_dates"] = [chunk.get("date", "") for chunk in evidence_chunks[:3]]'
)
if old_sources in fact_checker:
    fact_checker = fact_checker.replace(old_sources, new_sources)
    with open('backend/agents/fact_checker.py', 'w', encoding='utf-8') as f:
        f.write(fact_checker)
    print("OK: fact_checker.py updated to return source dates")
else:
    print("WARNING: Could not patch fact_checker.py automatically")

print("\nAll done! Run: python run_demo.py")
