import streamlit as st
import json
import re
import requests
import base64
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

st.set_page_config(
    page_title="VerifAI — Digital Trust Platform",
    page_icon="🛡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Dynamic theme injection ──────────────────────────────────────────────
_theme = st.session_state.get("theme", "dark")
if _theme == "light":
    _vars = """
    --bg-void:    #f8fafc;
    --bg-deep:    #f1f5f9;
    --bg-card:    #ffffff;
    --bg-hover:   #e2e8f0;
    --border:     #cbd5e1;
    --border-lit: #94a3b8;
    --accent:     #0284c7;
    --accent-dim: #0369a1;
    --green:      #16a34a;
    --green-dim:  #15803d;
    --red:        #dc2626;
    --red-dim:    #b91c1c;
    --amber:      #d97706;
    --amber-dim:  #b45309;
    --text-primary:   #0f172a;
    --text-secondary: #334155;
    --text-muted:     #64748b;
    --font-ui:   'Space Grotesk', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    """
    _bg_override = "background-color: #f8fafc !important;"
    _text_override = "color: #0f172a !important;"
else:
    _vars = """
    --bg-void:    #080f17;
    --bg-deep:    #0d1824;
    --bg-card:    #111f2e;
    --bg-hover:   #162840;
    --border:     #1e3448;
    --border-lit: #2a4d6e;
    --accent:     #38bdf8;
    --accent-dim: #0ea5e9;
    --green:      #4ade80;
    --green-dim:  #22c55e;
    --red:        #f87171;
    --red-dim:    #ef4444;
    --amber:      #fbbf24;
    --amber-dim:  #f59e0b;
    --text-primary:   #f1f8ff;
    --text-secondary: #94b8d4;
    --text-muted:     #94b8d4;
    --font-ui:   'Space Grotesk', sans-serif;
    --font-mono: 'JetBrains Mono', monospace;
    """
    _bg_override = "background-color: #080f17 !important;"
    _text_override = "color: #f1f8ff !important;"

st.markdown(f"""
<style>
:root {{ {_vars} }}
html, body, [class*="css"], .main, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {{
    {_bg_override}
    {_text_override}
}}
</style>""", unsafe_allow_html=True)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

/* THEME VARS INJECTED DYNAMICALLY */

/* ── Reset & Base ── */
html, body, [class*="css"] {
    font-family: var(--font-ui) !important;
    background-color: var(--bg-void) !important;
    color: var(--text-primary) !important;
}

.main .block-container {
    padding: 1.5rem 2rem 3rem 2rem !important;
    max-width: 1400px !important;
}

/* ── Larger readable base font ── */
html, body, [class*="css"] {
    font-size: 15px !important;
}

p, div, span, li {
    line-height: 1.7 !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--bg-deep) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container {
    padding: 1.5rem 1rem !important;
}

/* ── Inputs ── */
[data-testid="stTextInput"] input,
[data-testid="stTextArea"] textarea {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-lit) !important;
    border-radius: 6px !important;
    color: var(--text-primary) !important;
    font-family: var(--font-mono) !important;
    font-size: 14px !important;
    padding: 10px 14px !important;
}
[data-testid="stTextInput"] input:focus,
[data-testid="stTextArea"] textarea:focus {
    border-color: var(--accent-dim) !important;
    box-shadow: 0 0 0 2px #00d4ff15 !important;
}

/* ── Selectbox ── */
[data-testid="stSelectbox"] > div > div {
    background: var(--bg-card) !important;
    border: 1px solid var(--border-lit) !important;
    border-radius: 6px !important;
    color: var(--text-primary) !important;
}

/* ── Buttons ── */
[data-testid="stButton"] button {
    background: transparent !important;
    border: 1px solid var(--accent-dim) !important;
    color: var(--accent) !important;
    font-family: var(--font-mono) !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 1px !important;
    border-radius: 4px !important;
    transition: all 0.2s !important;
}
[data-testid="stButton"] button:hover {
    background: #00d4ff12 !important;
    border-color: var(--accent) !important;
    box-shadow: 0 0 12px #00d4ff20 !important;
}
[data-testid="stButton"] button[kind="primary"] {
    background: linear-gradient(135deg, #00d4ff15, #00d4ff08) !important;
    border: 1px solid var(--accent) !important;
    box-shadow: 0 0 20px #00d4ff18, inset 0 1px 0 #00d4ff20 !important;
}
[data-testid="stButton"] button[kind="primary"]:hover {
    background: linear-gradient(135deg, #00d4ff25, #00d4ff15) !important;
    box-shadow: 0 0 30px #00d4ff30 !important;
}

/* ── Tabs ── */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: transparent !important;
    border-bottom: 1px solid var(--border) !important;
    gap: 0 !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--text-muted) !important;
    font-family: var(--font-mono) !important;
    font-size: 11px !important;
    letter-spacing: 1.5px !important;
    text-transform: uppercase !important;
    border-bottom: 2px solid transparent !important;
    padding: 10px 20px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    color: var(--accent) !important;
    border-bottom: 2px solid var(--accent) !important;
    background: #00d4ff08 !important;
}

/* ── Expander ── */
[data-testid="stExpander"] {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: 8px !important;
}
[data-testid="stExpander"] summary {
    font-family: var(--font-mono) !important;
    font-size: 12px !important;
    color: var(--text-secondary) !important;
    letter-spacing: 0.5px !important;
}

/* ── Progress bar ── */
[data-testid="stProgress"] > div > div {
    background: linear-gradient(90deg, var(--accent-dim), var(--accent)) !important;
    border-radius: 2px !important;
}
[data-testid="stProgress"] > div {
    background: var(--border) !important;
    border-radius: 2px !important;
    height: 3px !important;
}

/* ── Checkbox ── */
[data-testid="stCheckbox"] label {
    font-family: var(--font-mono) !important;
    font-size: 12px !important;
    color: var(--text-secondary) !important;
}

/* ── File uploader ── */
[data-testid="stFileUploader"] {
    background: var(--bg-card) !important;
    border: 1px dashed var(--border-lit) !important;
    border-radius: 8px !important;
}

/* ── Scrollbar ── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg-void); }
::-webkit-scrollbar-thumb { background: var(--border-lit); border-radius: 2px; }


/* ── Light Theme ── */
[data-theme="light"] {
    --bg-void:    #f0f4f8;
    --bg-deep:    #e2e8f0;
    --bg-card:    #ffffff;
    --bg-hover:   #f8fafc;
    --border:     #cbd5e1;
    --border-lit: #94a3b8;
    --accent:     #0284c7;
    --accent-dim: #0369a1;
    --green:      #059669;
    --green-dim:  #047857;
    --red:        #dc2626;
    --red-dim:    #b91c1c;
    --amber:      #d97706;
    --amber-dim:  #b45309;
    --text-primary:   #0f172a;
    --text-secondary: #334155;
    --text-muted:     #94a3b8;
}

/* ── Hide Streamlit chrome ── */
#MainMenu, footer, header { visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; }
</style>

<script>
function setTheme(theme) {
    const root = document.documentElement;
    if (theme === 'light') {
        root.setAttribute('data-theme', 'light');
        root.style.setProperty('--bg-void', '#f0f4f8');
        root.style.setProperty('--bg-deep', '#e2e8f0');
        root.style.setProperty('--bg-card', '#ffffff');
        root.style.setProperty('--bg-hover', '#f8fafc');
        root.style.setProperty('--border', '#cbd5e1');
        root.style.setProperty('--border-lit', '#94a3b8');
        root.style.setProperty('--accent', '#0284c7');
        root.style.setProperty('--accent-dim', '#0369a1');
        root.style.setProperty('--green', '#059669');
        root.style.setProperty('--red', '#dc2626');
        root.style.setProperty('--amber', '#d97706');
        root.style.setProperty('--text-primary', '#0f172a');
        root.style.setProperty('--text-secondary', '#334155');
        root.style.setProperty('--text-muted', '#94a3b8');
        document.body.style.backgroundColor = '#f0f4f8';
        document.body.style.color = '#0f172a';
    } else {
        root.removeAttribute('data-theme');
        root.style.setProperty('--bg-void', '#020408');
        root.style.setProperty('--bg-deep', '#060d14');
        root.style.setProperty('--bg-card', '#0a1520');
        root.style.setProperty('--bg-hover', '#0f1e2e');
        root.style.setProperty('--border', '#0d2035');
        root.style.setProperty('--border-lit', '#1a3a55');
        root.style.setProperty('--accent', '#00d4ff');
        root.style.setProperty('--accent-dim', '#007a99');
        root.style.setProperty('--green', '#00ff88');
        root.style.setProperty('--red', '#ff3366');
        root.style.setProperty('--amber', '#ffaa00');
        root.style.setProperty('--text-primary', '#e8f4f8');
        root.style.setProperty('--text-secondary', '#7a9bb5');
        root.style.setProperty('--text-muted', '#3a5570');
        document.body.style.backgroundColor = '#020408';
        document.body.style.color = '#e8f4f8';
    }
    localStorage.setItem('verifai-theme', theme);
}
// Apply saved theme on load
const saved = localStorage.getItem('verifai-theme') || 'dark';
setTheme(saved);
</script>

""", unsafe_allow_html=True)

API_URL = "http://localhost:8000/api"

# ── Session state ─────────────────────────────────────────────────────────
for key in ["identity_result", "identity_candidates", "identity_uploaded_photo",
            "platform_profiles", "last_response", "auth_token", "current_user"]:
    if key not in st.session_state:
        st.session_state[key] = None
if "theme" not in st.session_state:
    st.session_state["theme"] = "dark"

# ── Auth gate ─────────────────────────────────────────────────────────────
from frontend.login_page import render_login_page
if not render_login_page():
    st.stop()

# ── Helpers ───────────────────────────────────────────────────────────────

def card(content: str, border_color: str = "var(--border)", glow: bool = False):
    shadow = f"box-shadow:0 0 24px {border_color}22;" if glow else ""
    return f"<div style='background:var(--bg-card);border:1px solid {border_color};border-radius:8px;padding:20px;{shadow}'>{content}</div>"

def badge(text: str, color: str):
    return (f"<span style='background:{color}18;border:1px solid {color}44;color:{color};"
            f"padding:2px 10px;border-radius:3px;font-family:var(--font-mono);"
            f"font-size:10px;letter-spacing:1px;font-weight:600;'>{text}</span>")

def label(text: str):
    return f"<div style='font-family:var(--font-mono);font-size:10px;letter-spacing:1.5px;color:var(--text-muted);margin-bottom:6px;text-transform:uppercase;'>{text}</div>"

def verdict_color(v: str):
    if "SUPPORTED" in v:    return "var(--green)"
    if "REFUTED" in v:      return "var(--red)"
    if "INCONCLUSIVE" in v: return "var(--amber)"
    return "var(--text-secondary)"

def trust_color(score: int):
    if score >= 75: return "var(--green)"
    if score >= 50: return "var(--amber)"
    return "var(--red)"

def render_source_timeline(sources, source_dates, verdict):
    vc = verdict_color(verdict).replace("var(--", "").replace(")", "")
    colors = {"green": "#00ff88", "red": "#ff3366", "amber": "#ffaa00", "text-secondary": "#7a9bb5"}
    dot = colors.get(vc, "#7a9bb5")
    if not source_dates:
        source_dates = ["Unknown"] * len(sources)
    while len(source_dates) < len(sources):
        source_dates.append("Unknown")
    rows = ""
    for i, (src, date) in enumerate(zip(sources[:4], source_dates[:4])):
        domain = src.replace("https://","").replace("http://","").split("/")[0]
        if len(domain) > 38: domain = domain[:38] + "…"
        dl = date if date not in ["Unknown","","None"] else "—"
        pct = 15 + i * 20
        rows += (
            f"<div style='display:flex;align-items:center;gap:12px;margin-bottom:12px;'>"
            f"<div style='width:6px;height:6px;border-radius:50%;background:{dot};flex-shrink:0;box-shadow:0 0 6px {dot}88;'></div>"
            f"<div style='font-family:var(--font-mono);font-size:11px;color:var(--text-secondary);flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>{domain}</div>"
            f"<div style='font-family:var(--font-mono);font-size:10px;color:{dot};background:{dot}12;border:1px solid {dot}33;padding:1px 8px;border-radius:2px;flex-shrink:0;'>{dl}</div>"
            f"</div>"
            f"<div style='position:relative;height:2px;background:var(--border);border-radius:1px;margin-bottom:14px;'>"
            f"<div style='position:absolute;left:0;top:0;height:100%;width:{pct}%;background:linear-gradient(90deg,var(--border-lit),{dot}66);border-radius:1px;'></div>"
            f"<div style='position:absolute;top:50%;left:{pct}%;transform:translate(-50%,-50%);width:8px;height:8px;border-radius:50%;background:{dot};border:2px solid var(--bg-void);box-shadow:0 0 8px {dot};'></div>"
            f"</div>"
        )
    st.markdown(
        f"<div style='background:var(--bg-deep);border:1px solid var(--border);border-radius:6px;padding:16px 18px;margin-top:14px;'>"
        f"{label('Source Timeline')}"
        f"{rows}"
        f"<div style='display:flex;justify-content:space-between;font-family:var(--font-mono);font-size:9px;color:var(--text-muted);margin-top:4px;'>  <span>OLDER</span><span>RECENT</span></div>"
        f"</div>",
        unsafe_allow_html=True)

def render_ai_detection(input_det):
    if not input_det: return
    lbl = input_det.get("label","Unknown")
    conf = input_det.get("confidence", 0)
    is_ai = input_det.get("is_ai_generated", False)
    reason = input_det.get("reasoning","")
    dc = "var(--red)" if (is_ai and conf >= 60) else ("var(--green)" if "Human" in lbl else "var(--text-secondary)")
    st.markdown(
        f"<div style='background:var(--bg-deep);border:1px solid var(--border);border-radius:6px;padding:14px 18px;margin-top:12px;'>"
        f"{label('AI Content Analysis')}"
        f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;'>"
        f"<div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);'>INPUT</div>"
        f"<div style='background:{dc}18;border:1px solid {dc}44;color:{dc};padding:2px 10px;border-radius:3px;font-family:var(--font-mono);font-size:10px;'>{'AI' if is_ai else 'HUMAN'} · {lbl.upper()} · {conf:.0f}%</div>"
        f"</div>"
        f"<div style='font-family:var(--font-mono);font-size:11px;color:var(--text-secondary);line-height:1.6;'>{reason}</div>"
        f"</div>",
        unsafe_allow_html=True)

def render_pdf_download(fact_results, identity_result=None):
    try:
        from backend.utils.pdf_exporter import build_report_pdf
        pdf_bytes = build_report_pdf(fact_results, identity_result)
        b64 = base64.b64encode(pdf_bytes).decode()
        filename = f"verifai_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.markdown(
            f'<a href="data:application/pdf;base64,{b64}" download="{filename}" '
            f'style="display:block;text-align:center;background:var(--bg-card);'
            f'border:1px solid var(--accent-dim);color:var(--accent);padding:10px 24px;'
            f'border-radius:4px;text-decoration:none;font-family:var(--font-mono);'
            f'font-size:11px;letter-spacing:1px;margin-top:16px;'
            f'transition:all 0.2s;">EXPORT REPORT AS PDF</a>',
            unsafe_allow_html=True)
    except Exception as e:
        st.caption(f"PDF unavailable: {e}")

def render_trust_ring(score, input_value, badge_text, risk, persona):
    tc = "#00ff88" if score >= 75 else ("#ffaa00" if score >= 50 else "#ff3366")
    dash = score * 2.199
    st.markdown(
        f"<div style='display:flex;align-items:center;gap:24px;background:var(--bg-deep);"
        f"border:1px solid var(--border-lit);border-radius:8px;padding:20px 24px;margin-bottom:16px;'>"
        f"<svg width='90' height='90' viewBox='0 0 90 90' style='flex-shrink:0;'>"
        f"<circle cx='45' cy='45' r='35' fill='none' stroke='var(--border)' stroke-width='6'/>"
        f"<circle cx='45' cy='45' r='35' fill='none' stroke='{tc}' stroke-width='6'"
        f" stroke-dasharray='{dash} 219.9' stroke-linecap='round' transform='rotate(-90 45 45)'"
        f" style='filter:drop-shadow(0 0 6px {tc}88)'/>"
        f"<text x='45' y='49' text-anchor='middle' font-size='18' font-weight='700'"
        f" fill='{tc}' font-family='JetBrains Mono,monospace'>{score}</text>"
        f"</svg>"
        f"<div>"
        f"<div style='font-size:22px;font-weight:600;color:var(--text-primary);font-family:var(--font-ui);margin-bottom:8px;'>{input_value}</div>"
        f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>"
        f"<span style='background:{tc}18;border:1px solid {tc}44;color:{tc};padding:3px 12px;"
        f"border-radius:3px;font-family:var(--font-mono);font-size:10px;letter-spacing:1px;"
        f"font-weight:700;'>{badge_text}</span>"
        f"<span style='color:var(--text-muted);font-family:var(--font-mono);font-size:10px;'>RISK: {risk.upper()}</span>"
        f"</div>"
        f"<div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:0.5px;'>PERSONA: {persona.upper()}</div>"
        f"</div></div>",
        unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    # Logo + Brand
    st.markdown(
        "<div style='text-align:center;padding:8px 0 4px 0;'>"
        "<div></div>"
        "<div style='font-family:var(--font-mono);font-size:20px;font-weight:700;"
        "color:var(--accent);letter-spacing:4px;margin-bottom:2px;"
        "text-shadow:0 0 20px #38bdf844;'>VERIFAI</div>"
        "<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);"
        "letter-spacing:3px;'>DIGITAL TRUST PLATFORM</div>"
        "<div style='margin:10px auto;width:40px;height:1px;"
        "background:linear-gradient(90deg,transparent,var(--accent),transparent);'></div>"
        "</div>",
        unsafe_allow_html=True)

    # User card
    user = st.session_state.get("current_user")
    if user:
        uname  = user.get("name", "")
        uemail = user.get("email", "")
        st.markdown(
            "<div style='background:linear-gradient(135deg,var(--bg-card),var(--bg-deep));"
            "border:1px solid var(--border-lit);border-radius:8px;padding:12px 14px;"
            "margin-bottom:12px;position:relative;overflow:hidden;'>"
            "<div style='position:absolute;top:0;left:0;width:3px;height:100%;"
            "background:linear-gradient(180deg,var(--accent),transparent);"
            "border-radius:8px 0 0 8px;'></div>"
            "<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);"
            "letter-spacing:2px;margin-bottom:6px;'>AUTHENTICATED USER</div>"
            "<div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>"
            "<div style='width:7px;height:7px;border-radius:50%;background:var(--green);"
            "box-shadow:0 0 6px var(--green);flex-shrink:0;'></div>"
            f"<div style='font-family:var(--font-mono);font-size:13px;color:var(--accent);"
            f"font-weight:700;'>{uname}</div>"
            "</div>"
            f"<div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);"
            f"padding-left:15px;'>{uemail}</div>"
            "</div>",
            unsafe_allow_html=True)
        if st.button("SIGN OUT", key="logout_btn", use_container_width=True):
            from backend.auth.auth_manager import logout_session
            logout_session(st.session_state.get("auth_token"))
            st.session_state["auth_token"]   = None
            st.session_state["current_user"] = None
            st.rerun()

    st.markdown("<div style='margin:12px 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)

    # System status
    st.markdown("<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:8px;'>SYSTEM STATUS</div>", unsafe_allow_html=True)
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        if r.status_code == 200:
            h = r.json()
            for svc, status in [("BACKEND","ONLINE"),("CHROMADB",h.get("chroma","ERR").upper()),("NEO4J",h.get("neo4j","ERR").upper())]:
                is_ok = "online" in status.lower() or "connect" in status.lower()
                dc = "var(--green)" if is_ok else "var(--amber)"
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"padding:7px 12px;background:var(--bg-card);border:1px solid var(--border);"
                    f"border-radius:4px;margin-bottom:3px;'>"
                    f"<div style='display:flex;align-items:center;gap:8px;'>"
                    f"<div style='width:6px;height:6px;border-radius:50%;background:{dc};"
                    f"box-shadow:0 0 5px {dc};'></div>"
                    f"<span style='font-family:var(--font-mono);font-size:10px;color:var(--text-secondary);'>{svc}</span>"
                    f"</div>"
                    f"<span style='font-family:var(--font-mono);font-size:9px;color:{dc};letter-spacing:1px;'>{status}</span>"
                    f"</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style='padding:8px;background:var(--bg-card);border:1px solid var(--red-dim);border-radius:4px;font-family:var(--font-mono);font-size:10px;color:var(--red);'>BACKEND OFFLINE</div>", unsafe_allow_html=True)
    except:
        st.markdown("<div style='padding:8px;background:var(--bg-card);border:1px solid var(--red-dim);border-radius:4px;font-family:var(--font-mono);font-size:10px;color:var(--red);'>BACKEND OFFLINE</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin:12px 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)

    # Usage metrics
    st.markdown("<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:8px;'>USAGE METRICS</div>", unsafe_allow_html=True)
    try:
        r = requests.get(f"{API_URL}/usage", timeout=2)
        if r.status_code == 200:
            u = r.json()
            total_req  = u.get("total_requests", 0)
            total_cost = u.get("total_cost", 0)
            remaining  = u.get("remaining_credit", 0)
            initial    = 5.0
            used_pct   = min(100, int((initial - remaining) / initial * 100))
            rem_pct    = 100 - used_pct
            bar_color  = "var(--green)" if rem_pct > 50 else ("var(--amber)" if rem_pct > 20 else "var(--red)")
            st.markdown(
                f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px;'>"
                f"<div style='background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;'>"
                f"<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:1px;margin-bottom:3px;'>REQUESTS</div>"
                f"<div style='font-family:var(--font-mono);font-size:20px;font-weight:700;color:var(--accent);'>{total_req}</div>"
                f"</div>"
                f"<div style='background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;'>"
                f"<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:1px;margin-bottom:3px;'>SPENT</div>"
                f"<div style='font-family:var(--font-mono);font-size:20px;font-weight:700;color:var(--amber);'>${total_cost:.3f}</div>"
                f"</div></div>"
                f"<div style='background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;'>"
                f"<div style='display:flex;justify-content:space-between;margin-bottom:5px;'>"
                f"<span style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:1px;'>CREDIT REMAINING</span>"
                f"<span style='font-family:var(--font-mono);font-size:10px;color:{bar_color};font-weight:700;'>${remaining:.2f}</span>"
                f"</div>"
                f"<div style='background:var(--border);border-radius:3px;height:4px;'>"
                f"<div style='background:linear-gradient(90deg,{bar_color},{bar_color}88);height:100%;width:{rem_pct}%;border-radius:3px;'></div>"
                f"</div>"
                f"<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);margin-top:3px;text-align:right;'>{rem_pct}% remaining</div>"
                f"</div>",
                unsafe_allow_html=True)
    except:
        pass

    st.markdown("<div style='margin:12px 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)

    # Tech stack
    st.markdown(
        "<div style='background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px 12px;'>"
        "<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:7px;'>TECH STACK</div>"
        "<div style='display:flex;flex-wrap:wrap;gap:4px;'>"
        "<span style='font-family:var(--font-mono);font-size:9px;color:var(--accent);background:var(--accent)12;border:1px solid var(--accent)33;padding:2px 7px;border-radius:3px;'>CLAUDE AI</span>"
        "<span style='font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;'>DUCKDUCKGO</span>"
        "<span style='font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;'>CHROMADB</span>"
        "<span style='font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;'>FASTAPI</span>"
        "<span style='font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;'>SQLITE</span>"
        "</div></div>",
        unsafe_allow_html=True)

    st.markdown("<div style='margin:12px 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)

    # Theme toggle
    st.markdown("<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:8px;'>DISPLAY THEME</div>", unsafe_allow_html=True)
    col_d, col_l = st.columns(2)
    with col_d:
        if st.button("DARK", key="theme_dark", use_container_width=True):
            from frontend.theme_manager import set_theme
            set_theme("dark")
            st.session_state["theme"] = "dark"
            st.rerun()
    with col_l:
        if st.button("LIGHT", key="theme_light", use_container_width=True):
            from frontend.theme_manager import set_theme
            set_theme("light")
            st.session_state["theme"] = "light"
            st.rerun()
    _cur = st.session_state.get("theme", "dark")
    st.markdown(
        f"<div style='font-family:var(--font-mono);font-size:8px;color:var(--accent);"
        f"text-align:center;margin-top:5px;letter-spacing:1px;'>ACTIVE: {_cur.upper()}</div>",
        unsafe_allow_html=True)

# ── Top header bar (matches image: VERIFAI left, system status dots right) ──
st.markdown("""
<style>
/* ── Image-matched header ── */
.verifai-topbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding-bottom: 18px;
    margin-bottom: 0;
    border-bottom: 1px solid var(--border);
}
.verifai-logo-block { display: flex; flex-direction: column; gap: 4px; }
.verifai-logo {
    font-family: var(--font-mono);
    font-size: 30px;
    font-weight: 700;
    color: var(--accent);
    letter-spacing: 5px;
    text-shadow: 0 0 24px #00d4ff44;
}
.verifai-sub {
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-muted);
    letter-spacing: 2px;
}
.verifai-status {
    display: flex;
    align-items: center;
    gap: 10px;
    font-family: var(--font-mono);
    font-size: 10px;
    color: var(--text-muted);
    letter-spacing: 1.5px;
}
.status-dots { display: flex; gap: 6px; align-items: center; }
.dot-g { width: 9px; height: 9px; border-radius: 50%; background: var(--green); box-shadow: 0 0 6px var(--green); }
.dot-a { width: 9px; height: 9px; border-radius: 50%; background: var(--amber); box-shadow: 0 0 6px var(--amber); }
.dot-d { width: 9px; height: 9px; border-radius: 50%; background: var(--border-lit); }

/* ── Config panel card ── */
.config-panel {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 20px 18px;
    margin-bottom: 14px;
}
.config-panel-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 2px;
    color: var(--text-muted);
    margin-bottom: 12px;
}
.config-sub-label {
    font-family: var(--font-mono);
    font-size: 9px;
    letter-spacing: 1.5px;
    color: var(--text-muted);
    margin-bottom: 5px;
    margin-top: 10px;
}
/* ── Quick topic pills ── */
.topic-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 7px;
    margin-top: 6px;
}
.topic-pill {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 1px;
    color: var(--text-secondary);
    border: 1px solid var(--border-lit);
    border-radius: 4px;
    padding: 5px 13px;
    cursor: pointer;
    transition: all 0.2s;
    background: transparent;
    text-transform: uppercase;
}
/* ── Recent checks list ── */
.recent-check-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 9px 0;
    border-bottom: 1px solid var(--border);
    gap: 10px;
}
.recent-check-text {
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-secondary);
    display: flex;
    align-items: center;
    gap: 8px;
    flex: 1;
    overflow: hidden;
    white-space: nowrap;
    text-overflow: ellipsis;
}
.recent-dot { width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }
.recent-verdict {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 1px;
    font-weight: 700;
}
/* ── Session stats ── */
.session-stats {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 16px 18px;
}
.session-stats-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    gap: 12px;
    margin-top: 10px;
}
.stat-cell { text-align: center; }
.stat-num {
    font-family: var(--font-mono);
    font-size: 22px;
    font-weight: 700;
}
.stat-lbl {
    font-family: var(--font-mono);
    font-size: 8px;
    color: var(--text-muted);
    letter-spacing: 1.5px;
    margin-top: 2px;
}

/* ── Analyze button styling ── */
[data-testid="stButton"] button[kind="primary"] {
    font-size: 13px !important;
    letter-spacing: 2px !important;
    padding: 14px !important;
}

/* ── Verdict result header ── */
.verdict-header {
    background: var(--bg-deep);
    border-radius: 6px;
    padding: 16px 22px;
    margin: 18px 0 14px 0;
    display: flex;
    align-items: center;
    gap: 24px;
}
.verdict-main {
    font-family: var(--font-mono);
    font-size: 22px;
    font-weight: 700;
    letter-spacing: 2px;
}
.verdict-meta-label {
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--text-muted);
    letter-spacing: 1.5px;
    margin-bottom: 2px;
}
.verdict-meta-val {
    font-family: var(--font-mono);
    font-size: 15px;
    color: var(--text-primary);
}
.verdict-divider { width: 1px; height: 34px; background: var(--border); flex-shrink: 0; }

/* ── summary count tiles ── */
.summary-tiles {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr 1fr;
    gap: 10px;
    margin-bottom: 18px;
}
.summary-tile {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 14px 12px;
    text-align: center;
}
.summary-tile-num {
    font-family: var(--font-mono);
    font-size: 26px;
    font-weight: 700;
}
.summary-tile-lbl {
    font-family: var(--font-mono);
    font-size: 8px;
    color: var(--text-muted);
    letter-spacing: 1.5px;
    margin-top: 4px;
}

/* ── Per-claim card ── */
.claim-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 18px 20px;
    margin-bottom: 16px;
}
.claim-card-header {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 12px;
    margin-bottom: 12px;
}
.claim-card-text {
    font-family: var(--font-ui);
    font-size: 14px;
    color: var(--text-primary);
    line-height: 1.5;
    flex: 1;
}
.claim-verdict-badge {
    font-family: var(--font-mono);
    font-size: 10px;
    letter-spacing: 1px;
    font-weight: 700;
    padding: 4px 12px;
    border-radius: 4px;
    flex-shrink: 0;
    margin-top: 2px;
}
.bar-label {
    font-family: var(--font-mono);
    font-size: 9px;
    color: var(--text-muted);
    letter-spacing: 1px;
    margin-bottom: 4px;
}
.bar-track {
    background: var(--border);
    border-radius: 2px;
    height: 4px;
    margin-bottom: 10px;
}
.bar-fill {
    height: 100%;
    border-radius: 2px;
}
.source-agree-row { display: flex; justify-content: space-between; align-items: center; }
.reasoning-box {
    background: var(--bg-deep);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 13px 16px;
    margin: 12px 0;
    font-family: var(--font-mono);
    font-size: 11px;
    color: var(--text-secondary);
    line-height: 1.7;
}
</style>
""", unsafe_allow_html=True)

# Check system status for header dots
_sys_dots = "<div class='dot-g'></div><div class='dot-a'></div><div class='dot-d'></div>"
try:
    _hr = requests.get(f"{API_URL}/health", timeout=1)
    if _hr.status_code == 200:
        _sys_dots = "<div class='dot-g'></div><div class='dot-g'></div><div class='dot-g'></div>"
except:
    pass

st.markdown(
    f"<div class='verifai-topbar'>"
    f"<div class='verifai-logo-block'>"
    f"<div class='verifai-logo'>VERIFAI</div>"
    f"<div class='verifai-sub'>DIGITAL TRUST VERIFICATION PLATFORM · MULTI-AGENT AI SYSTEM</div>"
    f"</div>"
    f"<div class='verifai-status'>"
    f"<div class='status-dots'>{_sys_dots}</div>"
    f"ALL SYSTEMS ONLINE"
    f"</div>"
    f"</div>",
    unsafe_allow_html=True)



# ── Tab declaration ──────────────────────────────────────────────────────
tab1, tab_cv, tab_osint_engine, tab_verdict = st.tabs([
    "FACT CHECK",
    "CV ANALYSIS",
    "OSINT — IDENTITY",
    "FINAL VERDICT",
])

# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — FACT CHECKER
# ══════════════════════════════════════════════════════════════════════════
with tab1:
    col_input, col_config = st.columns([3, 1.15], gap="large")

    examples = {
        "Select example...": "",
        "Climate Science": "Scientists say global temperatures have risen 1.1°C since pre-industrial times",
        "COVID-19 Origin": "The COVID-19 pandemic spread in 2019 from Wuhan, China",
        "Tech": "Apple became the first company to reach $3 trillion market cap",
    }

    with col_input:
        st.markdown(label("INPUT — CLAIM OR ARTICLE"), unsafe_allow_html=True)
        selected = st.selectbox(" ", list(examples.keys()), label_visibility="collapsed")
        default = examples.get(selected, "")
        user_input = st.text_area(" ", value=default, height=145,
            placeholder="Enter claim, question, or paste a full article…",
            label_visibility="collapsed")

        # ── Quick topics ──
        st.markdown(
            "<div style='font-family:var(--font-mono);font-size:9px;letter-spacing:2px;"
            "color:var(--text-muted);margin-top:14px;margin-bottom:8px;'>QUICK TOPICS</div>"
            "<div class='topic-pills'>"
            "<span class='topic-pill'>CLIMATE</span>"
            "<span class='topic-pill'>HEALTH</span>"
            "<span class='topic-pill'>POLITICS</span>"
            "<span class='topic-pill'>TECH</span>"
            "<span class='topic-pill'>FINANCE</span>"
            "<span class='topic-pill'>SCIENCE</span>"
            "</div>",
            unsafe_allow_html=True)

        # ── Recent checks (from session state) ──
        _recent = st.session_state.get("recent_checks", [
            {"text": "Apple first company to reach $3T market cap", "verdict": "SUPPORTED"},
            {"text": "5G towers caused COVID-19 pandemic",          "verdict": "REFUTED"},
            {"text": "WHO declared global monkeypox emergency",     "verdict": "INCONCLUSIVE"},
        ])
        _v_colors = {"SUPPORTED": "var(--green)", "REFUTED": "var(--red)", "INCONCLUSIVE": "var(--amber)"}
        rc_rows = ""
        for rc in _recent[-3:]:
            vc_ = _v_colors.get(rc["verdict"], "var(--text-muted)")
            rc_rows += (
                f"<div class='recent-check-row'>"
                f"<div class='recent-check-text'>"
                f"<div class='recent-dot' style='background:{vc_};box-shadow:0 0 5px {vc_};'></div>"
                f"{rc['text'][:65]}"
                f"</div>"
                f"<div class='recent-verdict' style='color:{vc_};'>{rc['verdict']}</div>"
                f"</div>"
            )
        st.markdown(
            "<div style='margin-top:18px;'>"
            "<div style='font-family:var(--font-mono);font-size:9px;letter-spacing:2px;"
            "color:var(--text-muted);margin-bottom:6px;'>RECENT CHECKS</div>"
            f"{rc_rows}"
            "</div>",
            unsafe_allow_html=True)

    with col_config:
        # ── Configuration card ──
        st.markdown(
            "<div class='config-panel'>"
            "<div class='config-panel-label'>CONFIGURATION</div>"
            "<div class='config-sub-label' style='margin-top:0;'>LANGUAGE</div>",
            unsafe_allow_html=True)
        language = st.selectbox(" ", ["English","Arabic","French","Spanish","German",
            "Italian","Portuguese","Russian","Chinese","Japanese","Turkish"],
            label_visibility="collapsed")
        st.markdown(
            "<div class='config-sub-label'>OPTIONS</div>",
            unsafe_allow_html=True)
        extract      = st.toggle("AUTO-EXTRACT CLAIMS", value=True)
        deep_scan    = st.toggle("DEEP SOURCE SCAN",    value=True)
        ai_detection = st.toggle("AI DETECTION",        value=False)
        st.markdown("</div>", unsafe_allow_html=True)

        # ── Session stats card ──
        _total_checks  = st.session_state.get("session_checks", 47)
        _session_acc   = st.session_state.get("session_acc",    82)
        _session_spent = st.session_state.get("session_spent",  1.24)
        st.markdown(
            f"<div class='session-stats'>"
            f"<div class='config-panel-label'>SESSION STATS</div>"
            f"<div class='session-stats-grid'>"
            f"<div class='stat-cell'>"
            f"<div class='stat-num' style='color:var(--text-primary);'>{_total_checks}</div>"
            f"<div class='stat-lbl'>CHECKS</div>"
            f"</div>"
            f"<div class='stat-cell'>"
            f"<div class='stat-num' style='color:var(--green);'>{_session_acc}%</div>"
            f"<div class='stat-lbl'>ACCURACY</div>"
            f"</div>"
            f"<div class='stat-cell'>"
            f"<div class='stat-num' style='color:var(--amber);'>${_session_spent:.2f}</div>"
            f"<div class='stat-lbl'>SPENT</div>"
            f"</div>"
            f"</div>"
            f"</div>",
            unsafe_allow_html=True)

        st.markdown("<div style='margin-top:14px;'></div>", unsafe_allow_html=True)
        st.markdown(
            "<div style='font-family:var(--font-mono);font-size:9px;color:var(--text-muted);"
            "letter-spacing:1.5px;text-align:center;margin-bottom:8px;'>⌘ + ↵ TO ANALYZE</div>",
            unsafe_allow_html=True)
        run_btn = st.button("▶  ANALYZE", type="primary", use_container_width=True)

    if run_btn:
        if not user_input.strip():
            st.warning("Enter a claim to verify.")
        else:
            with st.spinner(""):
                st.markdown(
                    "<div style='font-family:var(--font-mono);font-size:11px;"
                    "color:var(--accent);letter-spacing:1px;margin:8px 0;'>PROCESSING…</div>",
                    unsafe_allow_html=True)
                try:
                    resp = requests.post(f"{API_URL}/fact-check",
                        json={"text": user_input, "extract_claims": extract, "language": language},
                        timeout=180)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state["last_response"] = data
                        overall   = data.get("overall_verdict","UNKNOWN")
                        conf      = data.get("confidence", 0)
                        ms        = data.get("processing_time_ms", 0)
                        n_claims  = data.get("claims_analyzed", 0)
                        n_sources = sum(len(cr.get("sources",[])) for cr in data.get("detailed_results",[]))
                        vc        = verdict_color(overall)

                        # update session stats
                        st.session_state["session_checks"] = st.session_state.get("session_checks", 47) + 1

                        # ── Header: ANALYSIS COMPLETE status bar ──
                        st.markdown(
                            f"<div style='font-family:var(--font-mono);font-size:9px;"
                            f"color:var(--text-muted);letter-spacing:2px;margin-top:20px;margin-bottom:6px;'>"
                            f"ANALYSIS COMPLETE · {n_claims} CLAIMS · {ms:.0f}MS</div>",
                            unsafe_allow_html=True)

                        # ── Overall verdict card (image 2 style) ──
                        st.markdown(
                            f"<div style='background:var(--bg-deep);border:1px solid {vc}33;"
                            f"border-left:4px solid {vc};border-radius:6px;"
                            f"padding:18px 24px;margin-bottom:16px;display:flex;align-items:center;gap:28px;flex-wrap:wrap;'>"
                            f"<div>"
                            f"<div style='font-family:var(--font-mono);font-size:9px;color:var(--text-muted);"
                            f"letter-spacing:2px;margin-bottom:4px;'>OVERALL VERDICT</div>"
                            f"<div style='font-family:var(--font-mono);font-size:26px;font-weight:700;"
                            f"color:{vc};letter-spacing:3px;text-shadow:0 0 20px {vc}55;'>{overall}</div>"
                            f"</div>"
                            f"<div class='verdict-divider'></div>"
                            f"<div><div class='verdict-meta-label'>CONFIDENCE</div>"
                            f"<div class='verdict-meta-val' style='color:{vc};'>{conf:.1f}%</div></div>"
                            f"<div class='verdict-divider'></div>"
                            f"<div><div class='verdict-meta-label'>PROCESSING</div>"
                            f"<div class='verdict-meta-val'>{ms:.0f}ms</div></div>"
                            f"<div class='verdict-divider'></div>"
                            f"<div><div class='verdict-meta-label'>CLAIMS</div>"
                            f"<div class='verdict-meta-val'>{n_claims}</div></div>"
                            f"<div class='verdict-divider'></div>"
                            f"<div><div class='verdict-meta-label'>SOURCES</div>"
                            f"<div class='verdict-meta-val'>{n_sources}</div></div>"
                            f"</div>",
                            unsafe_allow_html=True)

                        # ── Summary tiles: count of each verdict ──
                        detailed = data.get("detailed_results",[])
                        n_sup  = sum(1 for c in detailed if "SUPPORTED"    in c.get("verdict",""))
                        n_inc  = sum(1 for c in detailed if "INCONCLUSIVE" in c.get("verdict",""))
                        n_ref  = sum(1 for c in detailed if "REFUTED"      in c.get("verdict",""))
                        avg_cf = (sum(c.get("confidence",0) for c in detailed) / max(len(detailed),1))
                        st.markdown(
                            f"<div class='summary-tiles'>"
                            f"<div class='summary-tile'>"
                            f"<div class='summary-tile-num' style='color:var(--green);'>{n_sup}</div>"
                            f"<div class='summary-tile-lbl'>SUPPORTED</div></div>"
                            f"<div class='summary-tile'>"
                            f"<div class='summary-tile-num' style='color:var(--amber);'>{n_inc}</div>"
                            f"<div class='summary-tile-lbl'>INCONCLUSIVE</div></div>"
                            f"<div class='summary-tile'>"
                            f"<div class='summary-tile-num' style='color:var(--red);'>{n_ref}</div>"
                            f"<div class='summary-tile-lbl'>REFUTED</div></div>"
                            f"<div class='summary-tile'>"
                            f"<div class='summary-tile-num' style='color:var(--accent);'>{avg_cf:.0f}%</div>"
                            f"<div class='summary-tile-lbl'>AVG CONF</div></div>"
                            f"</div>",
                            unsafe_allow_html=True)

                        # ── Per-claim card results (image 2 style) ──
                        st.markdown(label("DETAILED ANALYSIS"), unsafe_allow_html=True)

                        for idx, cr in enumerate(detailed, 1):
                            cv         = cr.get("verdict","UNKNOWN")
                            cc         = verdict_color(cv)
                            conf2      = cr.get("confidence", 0)
                            src_agree  = cr.get("source_agreement", None)
                            claim_text = cr.get("claim_text","")
                            reasoning  = cr.get("reasoning","")
                            sources    = cr.get("sources",[])
                            src_dates  = cr.get("source_dates",[])

                            # resolve source agreement display
                            n_src = len(sources)
                            sa_display = f"{src_agree}/{n_src}" if src_agree is not None else f"{n_src}/{n_src}"

                            # confidence bar width
                            bar_w = int(conf2)

                            # build source rows
                            src_rows_html = ""
                            for si, src in enumerate(sources[:4]):
                                domain = src.replace("https://","").replace("http://","").split("/")[0]
                                dl = src_dates[si] if si < len(src_dates) and src_dates[si] not in ["Unknown","","None"] else "—"
                                src_rows_html += (
                                    f"<div style='display:flex;align-items:center;gap:10px;"
                                    f"margin-bottom:8px;'>"
                                    f"<div style='width:7px;height:7px;border-radius:50%;"
                                    f"background:{cc};flex-shrink:0;box-shadow:0 0 5px {cc}88;'></div>"
                                    f"<div style='font-family:var(--font-mono);font-size:11px;"
                                    f"color:var(--accent);flex:1;overflow:hidden;text-overflow:ellipsis;"
                                    f"white-space:nowrap;'>"
                                    f"<a href='{src}' target='_blank' style='color:var(--accent);"
                                    f"text-decoration:none;'>{domain}</a></div>"
                                    f"<div style='font-family:var(--font-mono);font-size:9px;"
                                    f"color:{cc};background:{cc}15;border:1px solid {cc}44;"
                                    f"padding:1px 8px;border-radius:2px;flex-shrink:0;'>{dl}</div>"
                                    f"</div>"
                                )

                            # verdict badge colors
                            badge_bg  = f"background:{cc}18;border:1px solid {cc}66;color:{cc};"

                            st.markdown(
                                f"<div class='claim-card' style='border-color:var(--border);'>"
                                # header: claim text + verdict badge
                                f"<div class='claim-card-header'>"
                                f"<div class='claim-card-text'>{claim_text}</div>"
                                f"<div class='claim-verdict-badge' style='{badge_bg}'>{cv}</div>"
                                f"</div>"
                                # confidence bar
                                f"<div class='bar-label'>CONFIDENCE<span style='float:right;"
                                f"color:{cc};font-size:11px;font-weight:700;'>{conf2:.0f}%</span></div>"
                                f"<div class='bar-track'>"
                                f"<div class='bar-fill' style='width:{bar_w}%;background:linear-gradient(90deg,{cc}99,{cc});'></div>"
                                f"</div>"
                                # source agreement bar
                                f"<div class='bar-label' style='margin-top:2px;'>SOURCE AGREE"
                                f"<span style='float:right;color:var(--text-secondary);"
                                f"font-size:11px;'>{sa_display}</span></div>"
                                f"<div class='bar-track'>"
                                f"<div class='bar-fill' style='width:{min(bar_w+5,100)}%;background:linear-gradient(90deg,{cc}66,{cc}99);'></div>"
                                f"</div>",
                                unsafe_allow_html=True)

                            # reasoning box
                            if reasoning:
                                st.markdown(
                                    f"<div class='reasoning-box'>{reasoning}</div>",
                                    unsafe_allow_html=True)

                            # sources section
                            if sources:
                                st.markdown(
                                    f"<div style='font-family:var(--font-mono);font-size:9px;"
                                    f"letter-spacing:2px;color:var(--text-muted);"
                                    f"margin:12px 0 8px 0;'>SOURCES</div>"
                                    f"{src_rows_html}",
                                    unsafe_allow_html=True)

                            # source timeline
                            render_source_timeline(sources, src_dates, cv)
                            render_ai_detection(cr.get("input_ai_detection",{}))

                            # close claim card
                            st.markdown("</div>", unsafe_allow_html=True)

                            # update recent checks session state
                            _recent_list = st.session_state.get("recent_checks", [])
                            _recent_list.append({"text": claim_text[:65], "verdict": cv})
                            st.session_state["recent_checks"] = _recent_list[-10:]

                        with st.expander("METADATA"):
                            st.json({"task_id": data.get("task_id"), "timestamp": data.get("timestamp"), "language": language})

                        render_pdf_download(data.get("detailed_results",[]))

                    else:
                        st.markdown(f"<div style='color:var(--red);font-family:var(--font-mono);font-size:12px;'>API ERROR {resp.status_code}</div>", unsafe_allow_html=True)
                        st.code(resp.text)

                except requests.exceptions.Timeout:
                    st.markdown("<div style='color:var(--red);font-family:var(--font-mono);font-size:12px;'>REQUEST TIMEOUT — Try a shorter claim</div>", unsafe_allow_html=True)
                except requests.exceptions.ConnectionError:
                    st.markdown("<div style='color:var(--red);font-family:var(--font-mono);font-size:12px;'>CONNECTION ERROR — Backend offline</div>", unsafe_allow_html=True)
                except Exception as e:
                    st.markdown(f"<div style='color:var(--red);font-family:var(--font-mono);font-size:12px;'>ERROR: {e}</div>", unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════════════════
# TAB — CV ANALYSIS (Document Verification Engine)
# ══════════════════════════════════════════════════════════════════════════
with tab_cv:
    import html as _html_cv
    import io as _io_cv

    st.markdown("""
<style>
@keyframes cv-bar-in { from { width:0; } }
.cv-panel { background:var(--bg-card);border:1px solid var(--border-lit);border-radius:8px;padding:16px;margin-bottom:12px; }
.cv-flag-high   { border-left:3px solid var(--red);  background:rgba(248,113,113,0.06);border-radius:4px;padding:8px 12px;margin:4px 0; }
.cv-flag-medium { border-left:3px solid var(--amber);background:rgba(251,191,36,0.06); border-radius:4px;padding:8px 12px;margin:4px 0; }
.cv-flag-low    { border-left:3px solid var(--green);background:rgba(74,222,128,0.06); border-radius:4px;padding:8px 12px;margin:4px 0; }
.cv-verified    { border-left:3px solid var(--green);background:rgba(74,222,128,0.06); border-radius:4px;padding:8px 12px;margin:4px 0; }
.cv-src-badge   { font-family:var(--font-mono);font-size:9px;padding:1px 7px;border-radius:3px;border:1px solid;flex-shrink:0; }
.cv-trace       { font-family:var(--font-mono);font-size:8px;color:var(--text-muted);border-top:1px solid var(--border);padding-top:6px;margin-top:6px;line-height:1.7; }
</style>
""", unsafe_allow_html=True)

    def _cv_bar(pct, color):
        s = int(pct)
        return (
            "<div style='height:3px;background:var(--border);border-radius:2px;overflow:hidden;'>"
            f"<div style='height:100%;width:{s}%;background:{color};"
            "border-radius:2px;animation:cv-bar-in 0.9s ease both;'></div></div>"
        )

    def _cv_color(pct):
        return "var(--green)" if pct >= 70 else ("var(--amber)" if pct >= 45 else "var(--red)")

    st.markdown(label("ENGINE 1 — DOCUMENT VERIFICATION"), unsafe_allow_html=True)
    _cv_left, _cv_right = st.columns([1.2, 2.2], gap="large")

    with _cv_left:
        st.markdown(label("UPLOAD OR PASTE CV"), unsafe_allow_html=True)
        cv_doc_file = st.file_uploader("cv_doc", type=["pdf","docx","txt"],
                                        label_visibility="collapsed", key="cv_doc_up")
        st.markdown(
            "<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);"
            "margin-top:3px;'>PDF, DOCX, TXT — Max 10MB</div>",
            unsafe_allow_html=True)
        cv_paste = st.text_area("cv_paste",
            placeholder="— or paste CV text directly here —",
            height=130, label_visibility="collapsed", key="cv_paste_in")
        st.markdown(label("CONTEXT (OPTIONAL)"), unsafe_allow_html=True)
        cv_ctx_in = st.text_area("cv_ctx_in",
            placeholder="Name, expected role, location…",
            height=65, label_visibility="collapsed", key="cv_ctx_field")
        cv_run = st.button("▶  VERIFY DOCUMENT", type="primary",
                            use_container_width=True, key="cv_run_btn")

    # Extract text from uploaded file
    _cv_file_text = ""
    if cv_doc_file:
        _fn = cv_doc_file.name.lower()
        try:
            if _fn.endswith(".txt"):
                _cv_file_text = cv_doc_file.getvalue().decode("utf-8", errors="ignore")
            elif _fn.endswith(".pdf"):
                try:
                    import pypdf as _pypdf_cv
                    _r = _pypdf_cv.PdfReader(_io_cv.BytesIO(cv_doc_file.getvalue()))
                    _cv_file_text = "\n\n".join(p.extract_text() or "" for p in _r.pages).strip()
                except Exception:
                    pass
            elif _fn.endswith(".docx"):
                try:
                    from docx import Document as _DocxCv
                    _d = _DocxCv(_io_cv.BytesIO(cv_doc_file.getvalue()))
                    _paras = [p.text.strip() for p in _d.paragraphs if p.text.strip()]
                    _cells = []
                    for _t in _d.tables:
                        for _rw in _t.rows:
                            for _c in _rw.cells:
                                if _c.text.strip() not in _cells:
                                    _cells.append(_c.text.strip())
                    _cv_file_text = "\n".join(_paras + _cells)
                except Exception:
                    pass
        except Exception:
            pass

    _cv_final = cv_paste.strip() or _cv_file_text.strip()

    with _cv_right:
        if _cv_final:
            st.markdown(label("DOCUMENT PREVIEW"), unsafe_allow_html=True)
            _prev = _html_cv.escape(_cv_final[:1200]).replace("\n", "<br>")
            st.markdown(
                "<div style='background:var(--bg-deep);border:1px solid var(--border-lit);"
                "border-radius:6px;padding:14px 18px;height:220px;overflow-y:auto;'>"
                "<div style='font-family:Georgia,serif;font-size:10px;"
                "color:var(--text-primary);line-height:1.7;'>"
                + _prev + "</div></div>",
                unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='background:var(--bg-card);border:1px dashed var(--border-lit);"
                "border-radius:6px;height:220px;display:flex;align-items:center;"
                "justify-content:center;'>"
                "<span style='font-family:var(--font-mono);font-size:9px;"
                "color:var(--text-muted);letter-spacing:2px;'>UPLOAD OR PASTE CV TO PREVIEW</span>"
                "</div>",
                unsafe_allow_html=True)

    if cv_run:
        if not _cv_final:
            st.warning("Upload a document or paste CV text first.")
        else:
            with st.spinner(""):
                st.markdown(
                    "<div style='font-family:var(--font-mono);font-size:11px;"
                    "color:var(--accent);letter-spacing:1px;margin:8px 0;'>PROCESSING…</div>",
                    unsafe_allow_html=True)
                try:
                    _r = requests.post(f"{API_URL}/identity-analysis/cv",
                        json={"cv_text": _cv_final, "context": cv_ctx_in},
                        timeout=180)
                    if _r.status_code == 200:
                        st.session_state["cv_result"] = _r.json()
                    else:
                        st.markdown(
                            f"<div style='color:var(--red);font-family:var(--font-mono);'>"
                            f"API ERROR {_r.status_code}</div>", unsafe_allow_html=True)
                        st.session_state["cv_result"] = None
                except requests.exceptions.ConnectionError:
                    st.markdown(
                        "<div style='color:var(--red);font-family:var(--font-mono);'>"
                        "CONNECTION ERROR — Backend offline</div>", unsafe_allow_html=True)
                except Exception as _ce:
                    st.markdown(
                        f"<div style='color:var(--red);font-family:var(--font-mono);'>"
                        f"ERROR: {_ce}</div>", unsafe_allow_html=True)

    _cvd = st.session_state.get("cv_result")
    if _cvd:
        _verd = _cvd.get("verdict", "")
        _conf = _cvd.get("confidence", 0)
        _vc = ("var(--green)" if "Authentic" in _verd
               else "var(--red)" if ("Fake" in _verd or "Inconsistent" in _verd)
               else "var(--amber)")

        # Verdict bar — same style as fact-check overall verdict
        st.markdown(
            f"<div style='background:var(--bg-deep);border:1px solid {_vc}33;"
            f"border-left:4px solid {_vc};border-radius:6px;"
            f"padding:18px 24px;margin:18px 0 14px 0;"
            f"display:flex;align-items:center;gap:28px;flex-wrap:wrap;'>"
            f"<div><div style='font-family:var(--font-mono);font-size:9px;color:var(--text-muted);"
            f"letter-spacing:2px;margin-bottom:4px;'>CV VERDICT</div>"
            f"<div style='font-family:var(--font-mono);font-size:26px;font-weight:700;"
            f"color:{_vc};letter-spacing:3px;text-shadow:0 0 20px {_vc}55;'>{_verd}</div></div>"
            f"<div class='verdict-divider'></div>"
            f"<div><div class='verdict-meta-label'>CONFIDENCE</div>"
            f"<div class='verdict-meta-val' style='color:{_vc};'>{_conf}%</div></div>"
            f"<div class='verdict-divider'></div>"
            f"<div><div class='verdict-meta-label'>CLAIMS</div>"
            f"<div class='verdict-meta-val'>{_cvd.get('total_claims', 0)}</div></div>"
            f"<div class='verdict-divider'></div>"
            f"<div><div class='verdict-meta-label'>VERIFIED</div>"
            f"<div class='verdict-meta-val' style='color:var(--green);'>"
            f"{_cvd.get('claims_with_evidence', 0)}</div></div>"
            f"</div>",
            unsafe_allow_html=True)

        st.markdown(
            f"<div class='reasoning-box'>"
            f"{_html_cv.escape(_cvd.get('final_explanation', ''))}</div>",
            unsafe_allow_html=True)

        # Red Flag Dashboard
        _rfd = _cvd.get("red_flag_dashboard", {})
        if _rfd:
            _rsk = _rfd.get("risk_level", "N/A")
            _rsk_c = ("var(--red)" if _rsk == "HIGH"
                      else "var(--amber)" if _rsk == "MEDIUM" else "var(--green)")
            st.markdown(
                f"<div style='font-family:var(--font-mono);font-size:9px;letter-spacing:2px;"
                f"color:var(--text-muted);margin:20px 0 8px 0;'>RED FLAG DASHBOARD · "
                f"RISK: <span style='color:{_rsk_c};'>{_rsk}</span> · "
                f"SCORE: {_rfd.get('risk_score', 0)}/100</div>",
                unsafe_allow_html=True)
            for _f in _rfd.get("high_flags", []):
                st.markdown(
                    f"<div class='cv-flag-high'>"
                    f"<span style='font-family:var(--font-mono);font-size:9px;color:var(--red);'>"
                    f"🔴 [{_f.get('source', '')}]</span>"
                    f" <span style='font-family:var(--font-mono);font-size:10px;color:var(--text-secondary);'>"
                    f"{_html_cv.escape(_f.get('detail', ''))}</span></div>",
                    unsafe_allow_html=True)
            for _f in _rfd.get("medium_flags", []):
                st.markdown(
                    f"<div class='cv-flag-medium'>"
                    f"<span style='font-family:var(--font-mono);font-size:9px;color:var(--amber);'>"
                    f"🟡 [{_f.get('source', '')}]</span>"
                    f" <span style='font-family:var(--font-mono);font-size:10px;color:var(--text-secondary);'>"
                    f"{_html_cv.escape(_f.get('detail', ''))}</span></div>",
                    unsafe_allow_html=True)
            for _v in _rfd.get("verified", [])[:4]:
                st.markdown(
                    f"<div class='cv-verified'>"
                    f"<span style='font-family:var(--font-mono);font-size:10px;color:var(--green);'>"
                    f"✅ {_html_cv.escape(_v.get('detail', ''))}</span></div>",
                    unsafe_allow_html=True)

        # Forensic Timeline
        _tl = _cvd.get("timeline_audit", {})
        if _tl and (_tl.get("flags") or _tl.get("timeline")):
            with st.expander("🗓️  FORENSIC TIMELINE AUDIT"):
                for _ev in _tl.get("timeline", []):
                    _end = "Present" if _ev.get("end_year", 0) >= 9999 else str(_ev.get("end_year", "?"))
                    st.caption(
                        f"• [{_ev.get('type', '?')}] {_ev.get('event', '?')} "
                        f"— {_ev.get('start_year', '?')} → {_end}")
                for _tf in _tl.get("flags", []):
                    _sev = _tf.get("severity", "medium")
                    _sev_cls = _sev if _sev in ("high", "medium", "low") else "medium"
                    _sev_icon = "🔴" if _sev == "high" else "🟡"
                    st.markdown(
                        f"<div class='cv-flag-{_sev_cls}'>"
                        f"<span style='font-family:var(--font-mono);font-size:10px;'>"
                        f"{_sev_icon} {_html_cv.escape(_tf.get('detail', ''))}</span></div>",
                        unsafe_allow_html=True)
                for _g in _tl.get("gaps", []):
                    st.caption(
                        f"⬜ Gap {_g.get('months', '?')} months: {_g.get('between', '')}")

        # Proof of Work
        _pow = [p for p in _cvd.get("proof_of_work", []) if p.get("platform", "N/A") != "N/A"]
        if _pow:
            with st.expander("🔧  PROOF-OF-WORK VALIDATION"):
                for _p in _pow:
                    _pi = "✅" if _p.get("found") else "❌"
                    st.markdown(
                        f"<div style='font-family:var(--font-mono);font-size:10px;"
                        f"color:var(--text-secondary);margin-bottom:6px;'>"
                        f"<strong style='color:var(--text-primary);'>"
                        f"{_pi} {_p.get('platform', '?').upper()}</strong>"
                        f" — {_html_cv.escape(_p.get('note', ''))}</div>",
                        unsafe_allow_html=True)
                    if _p.get("found") and _p.get("url"):
                        st.caption(f"  → [{_p.get('title', '')[:70]}]({_p.get('url', '')})")

        # Claims & Evidence Gallery
        _claims = _cvd.get("claims", [])
        if _claims:
            st.markdown(
                "<div style='font-family:var(--font-mono);font-size:9px;letter-spacing:2px;"
                "color:var(--text-muted);margin:20px 0 8px 0;'>"
                "CLAIMS &amp; EVIDENCE GALLERY</div>",
                unsafe_allow_html=True)
            for _cl in _claims:
                _cconf = _cl.get("confidence", "not_found")
                _cpct  = int(_cl.get("posterior", 0.3) * 100)
                _cc    = _cv_color(_cpct)
                _cicon = {"high": "🟢", "medium": "🟡", "low": "🟠", "not_found": "🔴"}.get(_cconf, "⬜")
                with st.expander(
                        f"{_cicon} [{_cl.get('type', '?')}] {_cl.get('claim', '')[:90]}"):
                    st.markdown(
                        f"<div style='display:flex;gap:16px;align-items:center;margin-bottom:8px;'>"
                        f"<span style='font-family:var(--font-mono);font-size:9px;"
                        f"color:var(--text-muted);'>CONFIDENCE</span>"
                        f"<span style='font-family:var(--font-mono);font-size:11px;"
                        f"font-weight:700;color:{_cc};'>"
                        f"{_cconf.upper()} · {_cpct}%</span>"
                        f"<span style='font-family:var(--font-mono);font-size:9px;"
                        f"color:var(--text-muted);'>"
                        f"LR={_cl.get('likelihood_ratio', 0):.1f}</span>"
                        f"</div>" + _cv_bar(_cpct, _cc),
                        unsafe_allow_html=True)
                    if _cl.get("note"):
                        st.markdown(
                            f"<div class='reasoning-box'>"
                            f"{_html_cv.escape(_cl['note'])}</div>",
                            unsafe_allow_html=True)
                    for _src in _cl.get("evidence_gallery", []):
                        _tier = _src.get("credibility_tier", "low")
                        _tc   = {
                            "high": "var(--green)", "medium-high": "var(--green-dim)",
                            "medium": "var(--amber)", "low": "var(--text-muted)"
                        }.get(_tier, "var(--text-muted)")
                        _src_url = _src.get("url", "")
                        st.markdown(
                            f"<div style='display:flex;gap:8px;align-items:flex-start;margin:4px 0;'>"
                            f"<span class='cv-src-badge'"
                            f" style='color:{_tc};border-color:{_tc}44;background:{_tc}12;'>"
                            f"{_html_cv.escape(_src.get('source_name', '?'))}</span>"
                            f"<a href='{_src_url}' target='_blank'"
                            f" style='font-family:var(--font-mono);font-size:10px;"
                            f"color:var(--accent);text-decoration:none;'>"
                            f"{_html_cv.escape(_src.get('title', '')[:70])}</a>"
                            f"</div>",
                            unsafe_allow_html=True)
                        if _src.get("matched_text"):
                            st.caption(f'  Matched: "{_src["matched_text"][:120]}"')
                    _tr = _cl.get("traceability", {})
                    if _tr and _tr.get("match_logic"):
                        st.markdown(
                            f"<div class='cv-trace'>"
                            f"Query: {_html_cv.escape(_tr.get('query', '')[:100])}<br>"
                            f"Logic: {_html_cv.escape(_tr.get('match_logic', ''))}"
                            f"</div>",
                            unsafe_allow_html=True)

        # Credential Inflation
        _infl = _cvd.get("inflation_analysis", [])
        if _infl:
            with st.expander("📈  CREDENTIAL INFLATION ANALYSIS"):
                for _inf in _infl:
                    _r2   = _inf.get("inflation_risk", 0)
                    _cls  = "high" if _r2 >= 7 else ("medium" if _r2 >= 4 else "low")
                    _rc2  = {
                        "high": "var(--red)", "medium": "var(--amber)", "low": "var(--green)"
                    }.get(_cls, "var(--text-muted)")
                    _q    = _inf.get("recommended_question", "")
                    st.markdown(
                        f"<div class='cv-flag-{_cls}'>"
                        f"<span style='font-family:var(--font-mono);font-size:9px;"
                        f"color:{_rc2};font-weight:700;'>RISK {_r2}/10</span>"
                        f" <span style='font-family:var(--font-mono);font-size:10px;"
                        f"color:var(--text-secondary);'>"
                        f"{_html_cv.escape(_inf.get('claim', '')[:100])}</span>"
                        + (f"<div style='font-family:var(--font-mono);font-size:9px;"
                           f"color:var(--text-muted);margin-top:3px;'>"
                           f"❓ {_html_cv.escape(_q)}</div>" if _q else "")
                        + "</div>",
                        unsafe_allow_html=True)

        # Academic Credentials
        _creds = _cvd.get("credential_verification", [])
        if _creds:
            with st.expander("🎓  ACADEMIC CREDENTIAL VERIFICATION"):
                for _cr in _creds:
                    _ii = "✅" if _cr.get("institution_found") else (
                          "❌" if _cr.get("institution_found") is False else "❓")
                    _pi = "✅" if _cr.get("programme_found") else (
                          "❌" if _cr.get("programme_found") is False else "❓")
                    st.markdown(
                        f"<div class='cv-panel'>"
                        f"<div style='font-family:var(--font-mono);font-size:10px;"
                        f"color:var(--text-primary);margin-bottom:5px;'>"
                        f"{_html_cv.escape(_cr.get('claim', '')[:100])}</div>"
                        f"<div style='font-family:var(--font-mono);font-size:9px;"
                        f"color:var(--text-secondary);'>"
                        f"{_ii} Institution: <strong>"
                        f"{_html_cv.escape(str(_cr.get('institution', '?')))}</strong>"
                        f" &nbsp;·&nbsp; "
                        f"{_pi} {_html_cv.escape(str(_cr.get('programme_note', '')[:80]))}"
                        f"</div></div>",
                        unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# TAB — OSINT IDENTITY (Engine 2)
# ══════════════════════════════════════════════════════════════════════════
with tab_osint_engine:
    import html as _html_os2

    st.markdown("""
<style>
@keyframes os2-bar-in { from { width:0; } }
.os2-panel { background:var(--bg-card);border:1px solid var(--border-lit);border-radius:8px;padding:16px;margin-bottom:12px; }
.os2-cand  { background:var(--bg-deep);border:1px solid var(--border);border-radius:6px;padding:14px;margin-bottom:10px; }
.os2-r-pos { border-left:3px solid var(--green);background:rgba(74,222,128,0.05);border-radius:4px;padding:7px 12px;margin:3px 0; }
.os2-r-hi  { border-left:3px solid var(--red);  background:rgba(248,113,113,0.05);border-radius:4px;padding:7px 12px;margin:3px 0; }
.os2-r-med { border-left:3px solid var(--amber); background:rgba(251,191,36,0.05); border-radius:4px;padding:7px 12px;margin:3px 0; }
</style>
""", unsafe_allow_html=True)

    def _os2_bar(pct, color):
        s = int(pct)
        return (
            "<div style='height:3px;background:var(--border);border-radius:2px;overflow:hidden;'>"
            f"<div style='height:100%;width:{s}%;background:{color};"
            "border-radius:2px;animation:os2-bar-in 0.9s ease both;'></div></div>"
        )

    def _os2_color(pct):
        return "var(--green)" if pct >= 70 else ("var(--amber)" if pct >= 40 else "var(--red)")

    st.markdown(label("ENGINE 2 — OSINT IDENTITY INTELLIGENCE"), unsafe_allow_html=True)
    _os2_l, _os2_r = st.columns([1.2, 2.2], gap="large")

    with _os2_l:
        st.markdown(label("PERSON NAME"), unsafe_allow_html=True)
        os2_name = st.text_input(" ", placeholder="e.g. Jane Smith",
                                  label_visibility="collapsed", key="os2_name_in")
        st.markdown(label("CONTEXT (OPTIONAL)"), unsafe_allow_html=True)
        os2_ctx = st.text_area(" ", placeholder="Job, company, location, field…",
                                height=90, label_visibility="collapsed", key="os2_ctx_in")
        os2_run = st.button("🔍  RESOLVE IDENTITY", type="primary",
                             use_container_width=True, key="os2_run_btn")
        st.markdown(
            "<div style='margin-top:20px;background:var(--bg-card);border:1px solid var(--border);"
            "border-radius:6px;padding:12px 14px;'>"
            "<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);"
            "letter-spacing:2px;margin-bottom:7px;'>WHAT THIS ENGINE DOES</div>"
            "<div style='font-family:var(--font-mono);font-size:9px;"
            "color:var(--text-secondary);line-height:1.9;'>"
            "&#8599; Multi-platform web search<br>"
            "&#8599; Fellegi-Sunter candidate scoring<br>"
            "&#8599; Identity disambiguation<br>"
            "&#8599; Digital footprint scoring<br>"
            "&#8599; Real-world presence detection<br>"
            "&#8599; Identity risk profile"
            "</div></div>",
            unsafe_allow_html=True)

    with _os2_r:
        if os2_run:
            if not os2_name.strip():
                st.warning("Enter a name to search.")
            else:
                with st.spinner(""):
                    st.markdown(
                        "<div style='font-family:var(--font-mono);font-size:11px;"
                        "color:var(--accent);letter-spacing:1px;margin:8px 0;'>RESOLVING…</div>",
                        unsafe_allow_html=True)
                    try:
                        _os2_resp = requests.post(
                            f"{API_URL}/identity-analysis/resolve",
                            json={"name": os2_name.strip(), "context": os2_ctx.strip()},
                            timeout=180)
                        if _os2_resp.status_code == 200:
                            st.session_state["osint_result"] = _os2_resp.json()
                        else:
                            st.markdown(
                                f"<div style='color:var(--red);font-family:var(--font-mono);'>"
                                f"API ERROR {_os2_resp.status_code}</div>",
                                unsafe_allow_html=True)
                            st.session_state["osint_result"] = None
                    except requests.exceptions.ConnectionError:
                        st.markdown(
                            "<div style='color:var(--red);font-family:var(--font-mono);'>"
                            "CONNECTION ERROR</div>", unsafe_allow_html=True)
                    except Exception as _oe2:
                        st.markdown(
                            f"<div style='color:var(--red);font-family:var(--font-mono);'>"
                            f"ERROR: {_oe2}</div>", unsafe_allow_html=True)

        _os2d = st.session_state.get("osint_result")
        if _os2d:
            _os2_status = _os2d.get("status", "INSUFFICIENT_DATA")
            _os2_cands  = _os2d.get("candidates", [])
            _os2_fp     = _os2d.get("digital_footprint", {})
            _os2_pres   = _os2d.get("real_world_presence", {})
            _os2_last   = _os2d.get("last_known_activity", {})
            _os2_disamb = _os2d.get("disambiguation", {})
            _os2_cbk    = _os2d.get("confidence_breakdown", {})
            _os2_risk   = _os2d.get("identity_risk_profile", {})

            _S_COL = {
                "LIKELY_MATCH": "var(--green)", "LOW_AMBIGUITY": "var(--amber)",
                "MULTIPLE_CANDIDATES": "var(--amber)", "AMBIGUOUS": "var(--red)",
                "INSUFFICIENT_DATA": "var(--red)"
            }
            _S_ICO = {
                "LIKELY_MATCH": "✅", "LOW_AMBIGUITY": "🟡",
                "MULTIPLE_CANDIDATES": "⚠️", "AMBIGUOUS": "🔴",
                "INSUFFICIENT_DATA": "❌"
            }
            _sc2 = _S_COL.get(_os2_status, "var(--text-muted)")

            # Status banner — same style as fact-check verdict bar
            st.markdown(
                f"<div style='background:var(--bg-deep);border:1px solid {_sc2}33;"
                f"border-left:4px solid {_sc2};border-radius:6px;"
                f"padding:18px 24px;margin-bottom:16px;"
                f"display:flex;align-items:center;gap:28px;flex-wrap:wrap;'>"
                f"<div><div style='font-family:var(--font-mono);font-size:9px;"
                f"color:var(--text-muted);letter-spacing:2px;margin-bottom:4px;'>"
                f"IDENTITY STATUS</div>"
                f"<div style='font-family:var(--font-mono);font-size:22px;font-weight:700;"
                f"color:{_sc2};letter-spacing:2px;'>"
                f"{_S_ICO.get(_os2_status, '❓')} {_os2_status}</div></div>"
                f"<div class='verdict-divider'></div>"
                f"<div><div class='verdict-meta-label'>CANDIDATES</div>"
                f"<div class='verdict-meta-val'>{len(_os2_cands)}</div></div>"
                f"<div class='verdict-divider'></div>"
                f"<div><div class='verdict-meta-label'>FOOTPRINT</div>"
                f"<div class='verdict-meta-val'>"
                f"{_os2_fp.get('total_score', 0)}/100</div></div>"
                f"<div class='verdict-divider'></div>"
                f"<div><div class='verdict-meta-label'>PRESENCE</div>"
                f"<div class='verdict-meta-val'>"
                f"{_os2_pres.get('found_count', 0)}</div></div>"
                f"</div>",
                unsafe_allow_html=True)

            st.markdown(
                f"<div class='reasoning-box'>"
                f"{_html_os2.escape(_os2d.get('warning', ''))}</div>",
                unsafe_allow_html=True)

            # Disambiguation
            if _os2_disamb:
                with st.expander("🎯  DISAMBIGUATION"):
                    st.markdown(
                        f"<div style='font-family:var(--font-mono);font-size:10px;"
                        f"color:var(--text-secondary);margin-bottom:6px;'>"
                        f"{_html_os2.escape(_os2_disamb.get('method', ''))}</div>",
                        unsafe_allow_html=True)
                    if _os2_disamb.get("resolved_to"):
                        st.success(
                            f"Resolved → **{_os2_disamb['resolved_to']}**"
                            f" (F-S: {_os2_disamb.get('confidence', 0):.2f})")
                    for _ro in _os2_disamb.get("ruled_out", []):
                        st.caption(f"  ✗ {_ro.get('name', '?')}: {_ro.get('reason', '')}")
                    if _os2_disamb.get("note"):
                        st.info(_os2_disamb["note"])

            # Digital footprint
            _fp_dims = _os2_fp.get("dimensions", {})
            if _fp_dims:
                _fp_tier  = _os2_fp.get("tier", "N/A")
                _fp_score = _os2_fp.get("total_score", 0)
                with st.expander(f"📊  DIGITAL FOOTPRINT — {_fp_tier} ({_fp_score}/100)"):
                    st.markdown(
                        f"<div class='reasoning-box'>"
                        f"{_html_os2.escape(_os2_fp.get('interpretation', ''))}</div>",
                        unsafe_allow_html=True)
                    _fd1, _fd2 = st.columns(2)
                    with _fd1:
                        for _dk in ("recency", "breadth", "consistency"):
                            _dv = _fp_dims.get(_dk, 0)
                            _dc = _os2_color(_dv)
                            st.markdown(
                                f"<div style='display:flex;align-items:center;"
                                f"gap:8px;margin-bottom:7px;'>"
                                f"<span style='font-family:var(--font-mono);font-size:9px;"
                                f"color:var(--text-muted);flex:1;'>{_dk.upper()}</span>"
                                f"<div style='width:70px;'>"
                                + _os2_bar(_dv, _dc) +
                                f"</div><span style='font-family:var(--font-mono);font-size:10px;"
                                f"font-weight:700;color:{_dc};width:32px;text-align:right;'>"
                                f"{_dv}</span></div>",
                                unsafe_allow_html=True)
                    with _fd2:
                        for _dk in ("depth", "authenticity"):
                            _dv = _fp_dims.get(_dk, 0)
                            _dc = _os2_color(_dv)
                            st.markdown(
                                f"<div style='display:flex;align-items:center;"
                                f"gap:8px;margin-bottom:7px;'>"
                                f"<span style='font-family:var(--font-mono);font-size:9px;"
                                f"color:var(--text-muted);flex:1;'>{_dk.upper()}</span>"
                                f"<div style='width:70px;'>"
                                + _os2_bar(_dv, _dc) +
                                f"</div><span style='font-family:var(--font-mono);font-size:10px;"
                                f"font-weight:700;color:{_dc};width:32px;text-align:right;'>"
                                f"{_dv}</span></div>",
                                unsafe_allow_html=True)

            # Confidence breakdown
            if _os2_cbk:
                with st.expander("🔬  CONFIDENCE BREAKDOWN"):
                    _cb1, _cb2, _cb3, _cb4 = st.columns(4)
                    _cb1.metric("Name Match",      f"{_os2_cbk.get('name_match_pct', 0)}%")
                    _cb2.metric("Location",        f"{_os2_cbk.get('location_match_pct', 0)}%")
                    _cb3.metric("Role",            f"{_os2_cbk.get('role_match_pct', 0)}%")
                    _cb4.metric("Src Reliability", f"{_os2_cbk.get('source_reliability_avg', 0)}%")

            # Real-world presence
            if _os2_pres.get("signals"):
                with st.expander("🌍  REAL-WORLD PRESENCE"):
                    for _sig in _os2_pres["signals"]:
                        _sig_i = "✅" if _sig.get("found") else "❌"
                        _sig_url  = _sig.get("url", "")
                        _sig_ttl  = _html_os2.escape(_sig.get("title", "")[:70])
                        _sig_link = (
                            f" — <a href='{_sig_url}' target='_blank'"
                            f" style='color:var(--accent);'>{_sig_ttl}</a>"
                            if _sig.get("found") and _sig_url else ""
                        )
                        st.markdown(
                            f"<div style='font-family:var(--font-mono);font-size:10px;"
                            f"color:var(--text-secondary);margin-bottom:5px;'>"
                            f"<strong style='color:var(--text-primary);'>"
                            f"{_sig_i} {_sig.get('type', '?').upper()}</strong>"
                            f"{_sig_link}</div>",
                            unsafe_allow_html=True)

            # Last known activity
            if _os2_last.get("found"):
                _age2 = _os2_last.get("age_years", 0)
                _lc2  = "var(--green)" if _age2 <= 2 else "var(--amber)"
                _age_label = "✅ Recent" if _age2 <= 2 else f"⚠️ {_age2} years ago"
                st.markdown(
                    f"<div class='os2-panel'>"
                    f"<div style='font-family:var(--font-mono);font-size:8px;letter-spacing:2px;"
                    f"color:var(--text-muted);margin-bottom:6px;'>⏱ LAST KNOWN ACTIVITY</div>"
                    f"<div style='font-family:var(--font-mono);font-size:13px;"
                    f"font-weight:700;color:{_lc2};'>"
                    f"Year: {_os2_last.get('year', '?')} {_age_label}</div>"
                    f"<div style='font-family:var(--font-mono);font-size:9px;"
                    f"color:var(--text-secondary);margin-top:4px;'>"
                    f"{_html_os2.escape(_os2_last.get('snippet', '')[:120])}</div></div>",
                    unsafe_allow_html=True)

            # Candidate profiles
            if _os2_cands:
                st.markdown(
                    "<div style='font-family:var(--font-mono);font-size:9px;letter-spacing:2px;"
                    "color:var(--text-muted);margin:18px 0 8px 0;'>IDENTITY CANDIDATES</div>",
                    unsafe_allow_html=True)
                for _ci, _cand in enumerate(_os2_cands[:5]):
                    _cscore = _cand.get("similarity_score", 0)
                    _cpct   = int(_cscore * 100)
                    _cc2    = _os2_color(_cpct)
                    _crown  = "🥇" if _ci == 0 else f"#{_ci + 1}"
                    with st.expander(
                            f"{_crown} {_cand.get('name', '?')} — F-S: {_cscore:.3f}",
                            expanded=(_ci == 0)):
                        _prof_link = (
                            f"<a href='{_cand['profile_url']}' target='_blank'"
                            f" style='font-family:var(--font-mono);font-size:9px;"
                            f"color:var(--accent);display:block;margin-top:5px;'>"
                            f"&#8599; Profile link</a>"
                            if _cand.get("profile_url") else ""
                        )
                        st.markdown(
                            f"<div class='os2-cand'>"
                            f"<div style='display:flex;justify-content:space-between;"
                            f"align-items:center;margin-bottom:8px;'>"
                            f"<span style='font-family:var(--font-mono);font-size:9px;"
                            f"color:var(--text-muted);'>{_cand.get('platform', '')}</span>"
                            f"<span style='font-family:var(--font-mono);font-size:16px;"
                            f"font-weight:700;color:{_cc2};'>{_cpct}%</span></div>"
                            + _os2_bar(_cpct, _cc2) +
                            f"<div style='font-family:var(--font-mono);font-size:10px;"
                            f"color:var(--text-secondary);margin-top:8px;'>"
                            f"{_html_os2.escape(_cand.get('extracted_info', '')[:120])}</div>"
                            + _prof_link +
                            f"<div style='font-family:var(--font-mono);font-size:8px;"
                            f"color:var(--text-muted);margin-top:4px;'>"
                            f"Match: {_cand.get('name_match_quality', '')} · "
                            f"Sources: {_cand.get('source_count', 1)}</div></div>",
                            unsafe_allow_html=True)

            # Identity risk profile
            if _os2_risk:
                _ovr = _os2_risk.get("overall_risk", "")
                _rc3 = {
                    "HIGH RISK": "var(--red)",
                    "MEDIUM RISK": "var(--amber)",
                    "LOW RISK": "var(--green)"
                }.get(_ovr, "var(--text-muted)")
                with st.expander(f"⚠️  IDENTITY RISK PROFILE — {_ovr}"):
                    st.markdown(
                        f"<div style='font-family:var(--font-mono);font-size:11px;"
                        f"font-weight:700;color:{_rc3};margin-bottom:8px;'>● {_ovr}</div>",
                        unsafe_allow_html=True)
                    st.info(_os2_risk.get("recommended_action", ""))
                    for _rf in _os2_risk.get("risk_flags", []):
                        _lv   = _rf.get("level", "")
                        _css  = ("os2-r-hi" if _lv == "high"
                                 else "os2-r-med" if _lv == "medium" else "os2-r-pos")
                        _lc3  = {
                            "high": "var(--red)", "medium": "var(--amber)", "low": "var(--green)"
                        }.get(_lv, "var(--text-muted)")
                        _icon = "🔴" if _lv == "high" else "🟡"
                        st.markdown(
                            f"<div class='{_css}'>"
                            f"<span style='font-family:var(--font-mono);font-size:10px;"
                            f"color:{_lc3};'>{_icon} "
                            f"{_html_os2.escape(_rf.get('detail', ''))}</span></div>",
                            unsafe_allow_html=True)
                    for _ps in _os2_risk.get("positive_signals", []):
                        st.markdown(
                            f"<div class='os2-r-pos'>"
                            f"<span style='font-family:var(--font-mono);font-size:10px;"
                            f"color:var(--green);'>✅ {_html_os2.escape(_ps)}</span></div>",
                            unsafe_allow_html=True)
        else:
            st.markdown(
                "<div style='margin-top:40px;text-align:center;"
                "font-family:var(--font-mono);font-size:11px;"
                "color:var(--text-muted);letter-spacing:2px;'>"
                "ENTER A NAME AND PRESS RESOLVE IDENTITY</div>",
                unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════
# TAB — FINAL VERDICT (Cross-Engine Intelligence)
# ══════════════════════════════════════════════════════════════════════════
with tab_verdict:
    import html as _html_vd

    st.markdown("""
<style>
.vd-trust-pos  { border-left:3px solid var(--green);background:rgba(74,222,128,0.05); border-radius:4px;padding:8px 12px;margin:4px 0; }
.vd-trust-neg  { border-left:3px solid var(--red);  background:rgba(248,113,113,0.05);border-radius:4px;padding:8px 12px;margin:4px 0; }
.vd-trust-miss { border-left:3px solid var(--amber); background:rgba(251,191,36,0.05); border-radius:4px;padding:8px 12px;margin:4px 0; }
.vd-row  { display:flex;gap:12px;margin-bottom:10px;align-items:flex-start; }
.vd-lbl  { font-family:var(--font-mono);font-size:9px;color:var(--text-muted);letter-spacing:1px;width:110px;flex-shrink:0;margin-top:2px; }
.vd-val  { font-family:var(--font-mono);font-size:10px;color:var(--text-secondary);flex:1; }
</style>
""", unsafe_allow_html=True)

    st.markdown(
        label("CROSS-ENGINE INTELLIGENCE — TRUST EXPLANATION & CONFLICT MAP"),
        unsafe_allow_html=True)

    _cvd_vd  = st.session_state.get("cv_result", {}) or {}
    _os2d_vd = st.session_state.get("osint_result", {}) or {}

    if not _cvd_vd and not _os2d_vd:
        st.markdown(
            "<div style='background:var(--bg-card);border:1px solid var(--border-lit);"
            "border-radius:8px;padding:32px;text-align:center;'>"
            "<div style='font-family:var(--font-mono);font-size:11px;color:var(--text-muted);"
            "letter-spacing:2px;margin-bottom:8px;'>NO ANALYSIS DATA YET</div>"
            "<div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);'>"
            "Run <strong>CV Analysis</strong> and/or <strong>OSINT — Identity</strong> first,<br>"
            "then return here for the combined verdict.</div></div>",
            unsafe_allow_html=True)
    else:
        # Summary row
        _vs1, _vs2 = st.columns(2)
        with _vs1:
            _vc2 = _cvd_vd.get("verdict", "")
            _vcc = ("var(--green)" if "Authentic" in _vc2
                    else "var(--red)" if ("Fake" in _vc2 or "Inconsistent" in _vc2)
                    else ("var(--amber)" if _vc2 else "var(--text-muted)"))
            st.markdown(
                f"<div class='cv-panel'>"
                f"<div style='font-family:var(--font-mono);font-size:8px;letter-spacing:2px;"
                f"color:var(--text-muted);margin-bottom:5px;'>CV ENGINE</div>"
                f"<div style='font-family:var(--font-mono);font-size:16px;"
                f"font-weight:700;color:{_vcc};'>{_vc2 or 'No data'}</div>"
                f"<div style='font-family:var(--font-mono);font-size:9px;"
                f"color:var(--text-muted);margin-top:3px;'>"
                f"Confidence: {_cvd_vd.get('confidence', 0)}% · "
                f"Claims: {_cvd_vd.get('total_claims', 0)}</div></div>",
                unsafe_allow_html=True)
        with _vs2:
            _os_s = _os2d_vd.get("status", "")
            _os_c = {
                "LIKELY_MATCH": "var(--green)", "LOW_AMBIGUITY": "var(--amber)",
                "MULTIPLE_CANDIDATES": "var(--amber)", "AMBIGUOUS": "var(--red)",
                "INSUFFICIENT_DATA": "var(--red)"
            }.get(_os_s, "var(--text-muted)")
            _fp_s = _os2d_vd.get("digital_footprint", {}).get("total_score", 0)
            st.markdown(
                f"<div class='cv-panel'>"
                f"<div style='font-family:var(--font-mono);font-size:8px;letter-spacing:2px;"
                f"color:var(--text-muted);margin-bottom:5px;'>OSINT ENGINE</div>"
                f"<div style='font-family:var(--font-mono);font-size:16px;"
                f"font-weight:700;color:{_os_c};'>{_os_s or 'No data'}</div>"
                f"<div style='font-family:var(--font-mono);font-size:9px;"
                f"color:var(--text-muted);margin-top:3px;'>"
                f"Candidates: {len(_os2d_vd.get('candidates', []))} · "
                f"Footprint: {_fp_s}/100</div></div>",
                unsafe_allow_html=True)

        # Generate button
        if st.button("⚡  GENERATE FINAL VERDICT", type="primary", key="vd_run_btn"):
            with st.spinner(""):
                st.markdown(
                    "<div style='font-family:var(--font-mono);font-size:11px;"
                    "color:var(--accent);letter-spacing:1px;margin:8px 0;'>FUSING SIGNALS…</div>",
                    unsafe_allow_html=True)
                try:
                    _te_r = requests.post(
                        f"{API_URL}/identity-analysis/explain-trust",
                        json={"cv_result": _cvd_vd, "osint_result": _os2d_vd,
                              "final_decision": None},
                        timeout=60)
                    st.session_state["trust_expl"] = (
                        _te_r.json() if _te_r.status_code == 200 else None)
                    _cm_r = requests.post(
                        f"{API_URL}/identity-analysis/conflict-map",
                        json={"cv_result": _cvd_vd, "osint_result": _os2d_vd},
                        timeout=60)
                    st.session_state["conflict_map"] = (
                        _cm_r.json() if _cm_r.status_code == 200 else None)
                except Exception as _vde:
                    st.markdown(
                        f"<div style='color:var(--red);font-family:var(--font-mono);'>"
                        f"ERROR: {_vde}</div>", unsafe_allow_html=True)

        _trust_e = st.session_state.get("trust_expl")
        _conf_m  = st.session_state.get("conflict_map")

        if _trust_e:
            _sig_c = _trust_e.get("signal_count", {})
            st.markdown(
                f"<div style='font-family:var(--font-mono);font-size:9px;letter-spacing:2px;"
                f"color:var(--text-muted);margin:20px 0 6px 0;'>"
                f"ANALYSIS COMPLETE · {_sig_c.get('positive', 0)} POSITIVE · "
                f"{_sig_c.get('negative', 0)} NEGATIVE · {_sig_c.get('missing', 0)} GAPS</div>",
                unsafe_allow_html=True)

            _te1, _te2, _te3 = st.columns(3)
            with _te1:
                st.markdown(label("✅ WHY TRUSTED"), unsafe_allow_html=True)
                _items = _trust_e.get("why_trusted", []) or ["No positive signals found."]
                for _s in _items:
                    st.markdown(
                        f"<div class='vd-trust-pos'>"
                        f"<span style='font-family:var(--font-mono);font-size:10px;"
                        f"color:var(--green);'>{_html_vd.escape(str(_s))}</span></div>",
                        unsafe_allow_html=True)
            with _te2:
                st.markdown(label("🔴 WHY NOT TRUSTED"), unsafe_allow_html=True)
                _items = _trust_e.get("why_not_trusted", []) or ["No negative signals found."]
                for _s in _items:
                    st.markdown(
                        f"<div class='vd-trust-neg'>"
                        f"<span style='font-family:var(--font-mono);font-size:10px;"
                        f"color:var(--red);'>{_html_vd.escape(str(_s))}</span></div>",
                        unsafe_allow_html=True)
            with _te3:
                st.markdown(label("❓ WHAT IS MISSING"), unsafe_allow_html=True)
                _items = _trust_e.get("what_is_missing", []) or ["No gaps identified."]
                for _s in _items:
                    st.markdown(
                        f"<div class='vd-trust-miss'>"
                        f"<span style='font-family:var(--font-mono);font-size:10px;"
                        f"color:var(--amber);'>{_html_vd.escape(str(_s))}</span></div>",
                        unsafe_allow_html=True)

            _rec = _trust_e.get("overall_recommendation", "")
            if _rec:
                st.markdown(
                    f"<div class='reasoning-box' style='margin-top:16px;'>"
                    f"<div style='font-family:var(--font-mono);font-size:8px;letter-spacing:2px;"
                    f"color:var(--text-muted);margin-bottom:6px;'>📋 RECOMMENDATION</div>"
                    f"{_html_vd.escape(_rec)}</div>",
                    unsafe_allow_html=True)

        if _conf_m and _conf_m.get("fields"):
            _cm_align = _conf_m.get("overall_alignment", "")
            _cm_sum   = _conf_m.get("summary", {})
            _A_ICON   = {
                "aligned": "✅ ALIGNED", "partial_conflict": "⚠️ PARTIAL CONFLICT",
                "high_conflict": "🔴 HIGH CONFLICT", "insufficient_data": "❓ INSUFFICIENT DATA"
            }
            _A_COL = {
                "aligned": "var(--green)", "partial_conflict": "var(--amber)",
                "high_conflict": "var(--red)", "insufficient_data": "var(--text-muted)"
            }
            _alc = _A_COL.get(_cm_align, "var(--text-muted)")

            st.markdown(
                f"<div style='font-family:var(--font-mono);font-size:9px;letter-spacing:2px;"
                f"color:var(--text-muted);margin:20px 0 6px 0;'>"
                f"CROSS-ENGINE CONFLICT MAP · "
                f"<span style='color:{_alc};'>"
                f"{_A_ICON.get(_cm_align, _cm_align)}</span></div>",
                unsafe_allow_html=True)

            # Summary tiles — same style as fact-check tab
            st.markdown(
                f"<div class='summary-tiles'>"
                f"<div class='summary-tile'>"
                f"<div class='summary-tile-num' style='color:var(--green);'>"
                f"{_cm_sum.get('matches', 0)}</div>"
                f"<div class='summary-tile-lbl'>MATCHES</div></div>"
                f"<div class='summary-tile'>"
                f"<div class='summary-tile-num' style='color:var(--amber);'>"
                f"{_cm_sum.get('partials', 0)}</div>"
                f"<div class='summary-tile-lbl'>PARTIALS</div></div>"
                f"<div class='summary-tile'>"
                f"<div class='summary-tile-num' style='color:var(--red);'>"
                f"{_cm_sum.get('conflicts', 0)}</div>"
                f"<div class='summary-tile-lbl'>CONFLICTS</div></div>"
                f"<div class='summary-tile'>"
                f"<div class='summary-tile-num' style='color:var(--text-secondary);'>"
                f"{_cm_sum.get('unverified', 0)}</div>"
                f"<div class='summary-tile-lbl'>UNVERIFIED</div></div>"
                f"</div>",
                unsafe_allow_html=True)

            st.markdown(label("DETAILED ANALYSIS"), unsafe_allow_html=True)
            for _field in _conf_m.get("fields", []):
                _fv   = _field.get("verdict", "")
                _fi   = {"match": "✅", "partial": "🟡", "conflict": "🔴", "unverified": "❓"}.get(_fv, "⬜")
                _fvcc = {
                    "match": "var(--green)", "partial": "var(--amber)",
                    "conflict": "var(--red)", "unverified": "var(--text-muted)"
                }.get(_fv, "var(--text-muted)")
                # Claim-card style matching fact-check tab
                st.markdown(
                    f"<div class='claim-card' style='border-color:var(--border);'>"
                    f"<div class='claim-card-header'>"
                    f"<div class='claim-card-text'>{_field.get('field', '')}</div>"
                    f"<div class='claim-verdict-badge'"
                    f" style='background:{_fvcc}18;border:1px solid {_fvcc}66;color:{_fvcc};'>"
                    f"{_fi} {_fv.upper()}</div></div>"
                    f"<div class='vd-row'>"
                    f"<div class='vd-lbl'>CV SAYS</div>"
                    f"<div class='vd-val'>"
                    f"{_html_vd.escape(str(_field.get('cv_value', 'N/A')))}</div></div>"
                    f"<div class='vd-row'>"
                    f"<div class='vd-lbl'>OSINT SAYS</div>"
                    f"<div class='vd-val'>"
                    f"{_html_vd.escape(str(_field.get('osint_value', 'N/A')))}</div></div>"
                    f"<div class='reasoning-box'>"
                    f"{_html_vd.escape(_field.get('detail', ''))}</div>"
                    f"</div>",
                    unsafe_allow_html=True)

        with st.expander("METHODOLOGY"):
            st.json({
                "cv_engine":       "Bayesian evidence updating (Fellegi-Sunter 1969). Prior P=0.5 (Aitken & Taroni 2004). Source reliability: NIST FRVT.",
                "osint_engine":    "Fellegi-Sunter probabilistic record linkage. Merge threshold: posterior ≥0.70 (Winkler 2006). Status: ENFSI 2015.",
                "fusion":          "Weighted Bayesian fusion: identity(0.35) + cv_claims(0.30) + consistency(0.35). Kittler et al. 1998.",
                "footprint":       "5-dimension scoring: recency / breadth / consistency / depth / authenticity.",
                "disambiguation":  "Deductive exclusion via geographic and role contradictions.",
            })

# ── Footer ────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='margin-top:48px;padding-top:16px;border-top:1px solid var(--border);"
    "display:flex;justify-content:space-between;'>"
    "<span style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>ZERO-TRUST ARCHITECTURE</span>"
    "<span style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>MULTI-AGENT SYSTEM</span>"
    "<span style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>RAG-POWERED VERIFICATION</span>"
    "</div>",
    unsafe_allow_html=True)
