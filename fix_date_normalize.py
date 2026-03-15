"""
Quick fix - patches extract_date_regex in web_search.py to normalize dates
Run from: C:\\Users\\aya\\Desktop\\verifai
"""
import re

code = open("backend/rag/web_search.py", encoding="utf-8").read()

old_fn = '''def extract_date_regex(text: str) -> str:
    """Fast regex extraction — covers most cases"""
    patterns = [
        r'"datePublished"\\s*:\\s*"(\\d{4}-\\d{2}-\\d{2})',
        r'"dateModified"\\s*:\\s*"(\\d{4}-\\d{2}-\\d{2})',
        r\'<meta[^>]+property="article:published_time"[^>]+content="(\\d{4}-\\d{2}-\\d{2})\',
        r\'<time[^>]+datetime="(\\d{4}-\\d{2}-\\d{2})\',
        r\'/( \\d{4}/\\d{2}/\\d{2})/\',
        r\'(\\d{4}-\\d{2}-\\d{2})\',
        r\'(\\d{4}/\\d{2}/\\d{2})\',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            raw = m.group(1).replace("/", "-")
            if re.match(r\'\\d{4}-\\d{2}-\\d{2}\', raw):
                return raw[:10]
    return ""'''

new_fn = '''def extract_date_regex(text: str) -> str:
    """Fast regex extraction with normalization"""
    patterns = [
        r\'"datePublished"\\s*:\\s*"(\\d{4}-\\d{2}-\\d{2})\',
        r\'"dateModified"\\s*:\\s*"(\\d{4}-\\d{2}-\\d{2})\',
        r\'<meta[^>]+property="article:published_time"[^>]+content="(\\d{4}-\\d{2}-\\d{2})\',
        r\'<time[^>]+datetime="(\\d{4}-\\d{2}-\\d{2})\',
        r\'/(\\d{4}/\\d{1,2}/\\d{1,2})/\',
        r\'(\\d{4}-\\d{2}-\\d{2})\',
        r\'(\\d{4}/\\d{1,2}/\\d{1,2})\',
    ]
    for p in patterns:
        m = re.search(p, text)
        if m:
            raw = m.group(1).strip()
            # Normalize YYYY/MM/DD to YYYY-MM-DD
            slash = re.match(r\'(\\d{4})/(\\d{1,2})/(\\d{1,2})\', raw)
            if slash:
                return f"{slash.group(1)}-{slash.group(2).zfill(2)}-{slash.group(3).zfill(2)}"
            if re.match(r\'\\d{4}-\\d{2}-\\d{2}\', raw):
                return raw[:10]
    return ""'''

if old_fn.replace(" ", "") in code.replace(" ", ""):
    # Use a safer replacement approach
    code = re.sub(
        r'def extract_date_regex\(text: str\) -> str:.*?return ""',
        new_fn,
        code,
        flags=re.DOTALL
    )
    print("OK: replaced via regex")
else:
    # Direct patch - just replace the function
    code = re.sub(
        r'def extract_date_regex\(text: str\) -> str:.*?return ""',
        new_fn,
        code,
        flags=re.DOTALL
    )
    print("OK: patched via regex")

open("backend/rag/web_search.py", "w", encoding="utf-8").write(code)
print("Done! Restart with: python run_demo.py")
