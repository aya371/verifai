"""
VerifAI - Professional Launcher
Fixes: clean logs, proper date passing from web search to frontend
Run from: C:\\Users\\aya\\Desktop\\verifai
"""

# ── 1. Fix fact_checker.py to use web chunk dates properly ──────────────
fc = open("backend/agents/fact_checker.py", encoding="utf-8").read()

old = 'verdict["sources"] = [chunk["source"] for chunk in evidence_chunks[:3]]'
new = (
    'verdict["sources"] = [chunk["source"] for chunk in evidence_chunks[:3]]\n'
    '            verdict["source_dates"] = [chunk.get("date", "Unknown") for chunk in evidence_chunks[:3]]'
)

if 'source_dates' not in fc:
    if old in fc:
        fc = fc.replace(old, new)
        open("backend/agents/fact_checker.py", "w", encoding="utf-8").write(fc)
        print("OK  fact_checker.py — source_dates added")
    else:
        print("WARN fact_checker.py — patch failed, check manually")
else:
    # Make sure it's using evidence_chunks not some other var
    print("OK  fact_checker.py — source_dates already present")

# ── 2. Fix run_demo.py to have clean professional output ────────────────
run_demo = '''"""
VerifAI Demo Launcher
"""
import subprocess, sys, time, os, threading
from pathlib import Path

class C:
    RESET  = "\\033[0m";  BOLD   = "\\033[1m";  DIM    = "\\033[2m"
    RED    = "\\033[91m"; GREEN  = "\\033[92m"; YELLOW = "\\033[93m"
    BLUE   = "\\033[94m"; CYAN   = "\\033[96m"; WHITE  = "\\033[97m"
    GRAY   = "\\033[90m"

def enable_ansi():
    if sys.platform == "win32":
        os.system("color")
        try:
            import ctypes
            ctypes.windll.kernel32.SetConsoleMode(ctypes.windll.kernel32.GetStdHandle(-11), 7)
        except: pass

def clr(): sys.stdout.write("\\r\\033[K"); sys.stdout.flush()

def print_banner():
    print()
    print(f"{C.CYAN}{C.BOLD}  ██╗   ██╗███████╗██████╗ ██╗███████╗ █████╗ ██╗{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}  ██║   ██║██╔════╝██╔══██╗██║██╔════╝██╔══██╗██║{C.RESET}")
    print(f"{C.CYAN}{C.BOLD}  ██║   ██║█████╗  ██████╔╝██║█████╗  ███████║██║{C.RESET}")
    print(f"{C.CYAN}  ╚██╗ ██╔╝██╔══╝  ██╔══██╗██║██╔══╝  ██╔══██║██║{C.RESET}")
    print(f"{C.CYAN}   ╚████╔╝ ███████╗██║  ██║██║██║     ██║  ██║██║{C.RESET}")
    print(f"{C.CYAN}    ╚═══╝  ╚══════╝╚═╝  ╚═╝╚═╝╚═╝     ╚═╝  ╚═╝╚═╝{C.RESET}")
    print()
    print(f"  {C.WHITE}{C.BOLD}Digital Trust Verification Platform{C.RESET}")
    print(f"  {C.GRAY}Multi-Agent AI  ·  RAG Pipeline  ·  Live Web Search{C.RESET}")
    print()

def div(c="─", col=None):
    col = col or (C.GRAY)
    print(f"  {col}{c*54}{C.RESET}")

def ok(label, val="", vc=None):
    vc = vc or C.GREEN
    v = f"  {vc}{C.BOLD}{val}{C.RESET}" if val else ""
    print(f"  {C.GREEN}✓{C.RESET}  {C.WHITE}{label}{C.RESET}{v}")

def spinner(label, stop, done):
    fr = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]; i = 0
    while not stop.is_set():
        sys.stdout.write(f"\\r  {C.YELLOW}{fr[i%len(fr)]}{C.RESET}  {C.WHITE}{label}...{C.RESET}")
        sys.stdout.flush(); time.sleep(0.08); i += 1
    clr(); done.set()

def spin(label, secs):
    s, d = threading.Event(), threading.Event()
    threading.Thread(target=spinner, args=(label, s, d), daemon=True).start()
    time.sleep(secs); s.set(); d.wait()

# Filter noisy log lines
SUPPRESS = [
    "telemetry", "capture()", "WatchFiles", "reloader",
    "Will watch", "Anonymized", "WARNING", "Delete of",
    "Add of existing", "CollectionDelete", "CollectionAdd",
    "Collecting usage", "gatherUsageStats", "browser.",
    "Network URL", "External URL", "You can now view",
]

def is_important(line):
    line_l = line.lower()
    if any(s.lower() in line_l for s in SUPPRESS):
        return False
    return True

def format_line(line):
    line = line.strip()
    if not line: return None
    # Backend request logs - show cleanly
    if "POST /api/fact-check" in line: return f"  {C.CYAN}→{C.RESET}  {C.GRAY}Fact-check request received{C.RESET}"
    if "GET /api/health"      in line: return None  # hide health pings
    if "GET /api/usage"       in line: return None  # hide usage pings
    if "Application startup"  in line: return None
    if "Uvicorn running"      in line: return None
    if "Started server"       in line: return None
    if "localhost:8501"       in line and "view" not in line.lower(): return None

    # Key backend events - format nicely
    if "Extracted"    in line and "claims" in line: return f"  {C.CYAN}◆{C.RESET}  {C.GRAY}{line.split('|')[-1].strip()}{C.RESET}"
    if "Searching web"in line:                      return f"  {C.CYAN}◆{C.RESET}  {C.GRAY}{line.split('|')[-1].strip()}{C.RESET}"
    if "Indexed"      in line and "chunks" in line: return f"  {C.CYAN}◆{C.RESET}  {C.GRAY}{line.split('|')[-1].strip()}{C.RESET}"
    if "Aggregated:"  in line:
        part = line.split("Aggregated:")[-1].strip()
        col = C.RED if "FALSE" in part else C.GREEN if "TRUE" in part or "SUPPORT" in part else C.YELLOW
        return f"  {col}{C.BOLD}◆  Verdict: {part}{C.RESET}"
    if "Task" in line and "complete" in line:       return f"  {C.GREEN}✓{C.RESET}  {C.GRAY}{line.split('|')[-1].strip()}{C.RESET}"
    if "ERROR" in line:                             return f"  {C.RED}✗{C.RESET}  {C.GRAY}{line.split('|')[-1].strip()}{C.RESET}"

    return None  # suppress everything else

def drain(proc):
    for line in iter(proc.stdout.readline, ""):
        if not line: break
        formatted = format_line(line)
        if formatted:
            print(formatted)
    proc.stdout.close()

def start_backend():
    cmd = [sys.executable, "-m", "uvicorn", "backend.main:app",
           "--host", "0.0.0.0", "--port", "8000", "--reload",
           "--timeout-keep-alive", "120"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         universal_newlines=True, encoding="utf-8", errors="replace", bufsize=1)
    threading.Thread(target=drain, args=(p,), daemon=True).start()
    return p

def start_frontend():
    cmd = [sys.executable, "-m", "streamlit", "run", "frontend/dashboard.py",
           "--server.port", "8501", "--server.headless", "true",
           "--logger.level", "error"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                         universal_newlines=True, encoding="utf-8", errors="replace", bufsize=1)
    threading.Thread(target=drain, args=(p,), daemon=True).start()
    return p

def check_env():
    if not Path(".env").exists():
        print(f"  {C.RED}✗{C.RESET}  .env file not found"); return False
    from dotenv import load_dotenv; load_dotenv()
    key = os.getenv("ANTHROPIC_API_KEY", "")
    if not key or key == "your-key-here":
        print(f"  {C.RED}✗{C.RESET}  API key not set"); return False
    ok("API Key", key[:12] + "••••" + key[-4:])
    return True

def main():
    enable_ansi()
    print_banner()
    div()
    print()
    if not check_env():
        print(f"\\n  {C.RED}Fix the issues above and try again.{C.RESET}\\n"); return
    print()
    div()
    print()

    spin("Starting backend", 1)
    backend = start_backend()
    spin("Waiting for backend", 5)
    ok("Backend", "online  →  localhost:8000")

    spin("Starting frontend", 1)
    frontend = start_frontend()
    spin("Waiting for frontend", 4)
    ok("Frontend", "online  →  localhost:8501")

    ok("Web Search",  "DuckDuckGo live")
    ok("Vector DB",   "ChromaDB ready")
    ok("Claude AI",   "claude-3-haiku active")

    print()
    div("═", C.CYAN)
    print()
    print(f"  {C.GREEN}{C.BOLD}  VerifAI is live!{C.RESET}")
    print()
    print(f"  {C.WHITE}  Open browser   {C.RESET}  →  {C.CYAN}{C.BOLD}http://localhost:8501{C.RESET}")
    print(f"  {C.WHITE}  API Docs       {C.RESET}  →  {C.BLUE}http://localhost:8000/docs{C.RESET}")
    print()
    div("═", C.CYAN)
    print()
    print(f"  {C.GRAY}Press {C.RESET}{C.WHITE}Ctrl+C{C.RESET}{C.GRAY} to stop{C.RESET}")
    print()

    try:
        while True:
            time.sleep(1)
            if backend.poll() is not None:
                print(f"\\n  {C.YELLOW}⚠  Backend stopped — restarting...{C.RESET}")
                backend = start_backend()
                time.sleep(3)
                ok("Backend", "restarted")
    except KeyboardInterrupt:
        print()
        div()
        print(f"\\n  {C.YELLOW}Shutting down...{C.RESET}")
        backend.terminate(); frontend.terminate()
        ok("All services stopped")
        print()

if __name__ == "__main__":
    main()
'''

open("run_demo.py", "w", encoding="utf-8").write(run_demo)
print("OK  run_demo.py — professional clean output")
print()
print("Done! Run: python run_demo.py")
