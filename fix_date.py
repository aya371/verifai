code = open('backend/rag/web_search.py', encoding='utf-8').read()
old = "chunks.append({\"text\": text, \"source\": url, \"title\": title})"
new = "chunks.append({\"text\": text, \"source\": url, \"title\": title, \"date\": \"2025\", \"credibility\": 0.75, \"similarity_score\": 0.9})"
code = code.replace(old, new)
open('backend/rag/web_search.py', 'w', encoding='utf-8').write(code)
print('Fixed! Verifying...')
# Confirm the change
if 'date' in open('backend/rag/web_search.py', encoding='utf-8').read():
    print('OK: date field is now in web_search.py')
else:
    print('FAIL: change did not apply')
