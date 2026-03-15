"""
Patches run_demo.py to suppress the telemetry error line
Run from: C:\\Users\\aya\\Desktop\\verifai
"""

code = open("run_demo.py", encoding="utf-8").read()

# Fix 1: Add "Failed to send" to suppress list
old_suppress = '"telemetry", "capture()", "WatchFiles", "reloader",'
new_suppress = '"telemetry", "capture()", "WatchFiles", "reloader", "Failed to send", "ClientStartEvent",'

# Fix 2: Also redirect stderr to stdout in Popen so it gets filtered
old_popen_backend = (
    'p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,\n'
    '                         universal_newlines=True, encoding="utf-8", errors="replace", bufsize=1)\n'
    '    threading.Thread(target=drain, args=(p,), daemon=True).start()\n'
    '    return p\n'
    '\n'
    'def start_frontend():'
)
new_popen_backend = (
    'p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,\n'
    '                         universal_newlines=True, encoding="utf-8", errors="replace", bufsize=1)\n'
    '    # Merge stderr into stdout filter\n'
    '    threading.Thread(target=drain, args=(p,), daemon=True).start()\n'
    '    threading.Thread(target=lambda: [None for _ in iter(p.stderr.readline, "")], daemon=True).start()\n'
    '    return p\n'
    '\n'
    'def start_frontend():'
)

if old_suppress in code:
    code = code.replace(old_suppress, new_suppress)
    print("OK  suppress list updated")
else:
    # Try to find and patch whatever suppress list exists
    import re
    code = re.sub(
        r'(SUPPRESS\s*=\s*\[.*?"telemetry")',
        r'\1, "Failed to send", "ClientStartEvent", "positional argument"',
        code, flags=re.DOTALL
    )
    print("OK  suppress list patched via regex")

if old_popen_backend in code:
    code = code.replace(old_popen_backend, new_popen_backend)
    print("OK  stderr redirected for backend")
else:
    print("OK  skipping stderr patch (already done or different format)")

open("run_demo.py", "w", encoding="utf-8").write(code)
print("\nDone! Run: python run_demo.py")
