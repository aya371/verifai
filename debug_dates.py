"""
Debug date extraction - run from C:\\Users\\aya\\Desktop\\verifai
"""
import re
import requests

DATE_PATTERNS = [
    r'"datePublished"\s*:\s*"(\d{4}-\d{2}-\d{2})',
    r'"dateModified"\s*:\s*"(\d{4}-\d{2}-\d{2})',
    r'<meta[^>]+property="article:published_time"[^>]+content="(\d{4}-\d{2}-\d{2})',
    r'<meta[^>]+name="pubdate"[^>]+content="(\d{4}-\d{2}-\d{2})',
    r'<meta[^>]+name="date"[^>]+content="(\d{4}-\d{2}-\d{2})',
    r'/(\d{4}/\d{2}/\d{2})/',
    r'/(\d{4}-\d{2}-\d{2})/',
    r'(\d{4}-\d{2}-\d{2})',
    r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
    r'((?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4})',
]

def extract_date(text):
    for pattern in DATE_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return ""

# Test URLs from your last screenshot
test_urls = [
    "https://www.bbc.com/news/articles/c4gq3ykg7pvo",
    "https://www.aljazeera.com/news/2026/3/8/israel-escalates-attacks-across-lebanon-as-two-soldiers-killed",
    "https://www.firstpost.com/explainers/why-is-israel-attacking-lebanon-amid-war-with-iran-everything-to-know-13985408.html",
]

headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

for url in test_urls:
    print(f"\nURL: {url}")
    
    # Test URL itself
    url_date = extract_date(url)
    print(f"  From URL:     {url_date or 'not found'}")
    
    # Test fetching page
    try:
        resp = requests.get(url, timeout=6, headers=headers)
        snippet = resp.text[:10000]
        page_date = extract_date(snippet)
        print(f"  From page:    {page_date or 'not found'}")
        
        # Show what meta date fields exist
        for pattern in DATE_PATTERNS[:5]:
            m = re.search(pattern, snippet, re.IGNORECASE)
            if m:
                print(f"  Pattern hit:  {pattern[:40]} => {m.group(1)}")
                break
    except Exception as e:
        print(f"  Fetch error:  {e}")

print("\n\nNow checking what fact_checker.py actually returns...")
try:
    fc = open("backend/agents/fact_checker.py", encoding="utf-8").read()
    if "source_dates" in fc:
        # Find the lines around source_dates
        lines = fc.split("\n")
        for i, line in enumerate(lines):
            if "source_dates" in line or "sources" in line.lower():
                print(f"  Line {i+1}: {line.strip()}")
    else:
        print("  WARNING: 'source_dates' not found in fact_checker.py!")
        print("  This means dates are never sent to the frontend.")
except Exception as e:
    print(f"  Error reading fact_checker: {e}")

print("\nNow checking what web_search.py date logic looks like...")
try:
    ws = open("backend/rag/web_search.py", encoding="utf-8").read()
    if "extract_date" in ws:
        print("  OK: extract_date function exists")
    if "fetch_date_from_url" in ws:
        print("  OK: fetch_date_from_url function exists")
    if "pub_date" in ws:
        print("  OK: pub_date assignment exists")
    else:
        print("  WARNING: pub_date not found - web_search.py may be old version")
except Exception as e:
    print(f"  Error: {e}")
