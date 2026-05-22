import streamlit as st
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

st.markdown(
    "<div style='margin-bottom:24px;padding-bottom:20px;border-bottom:1px solid var(--border);'>"
    "<div style='font-family:var(--font-mono);font-size:26px;font-weight:700;color:var(--accent);"
    "letter-spacing:3px;'>VERIFAI</div>"
    "<div style='font-family:var(--font-mono);font-size:11px;color:var(--text-muted);letter-spacing:2px;margin-top:4px;'>"
    "DIGITAL TRUST VERIFICATION PLATFORM · MULTI-AGENT AI SYSTEM</div>"
    "</div>",
    unsafe_allow_html=True)

tab1, tab3 = st.tabs(["FACT CHECK", "IDENTITY ANALYSIS"])

# ══════════════════════════════════════════════════════════════════════════
# TAB 1 — FACT CHECKER
# ══════════════════════════════════════════════════════════════════════════
with tab1:
    col_input, col_config = st.columns([3, 1], gap="large")

    with col_input:
        st.markdown(label("INPUT — CLAIM OR ARTICLE"), unsafe_allow_html=True)
        examples = {
            "Select example...": "",
            "Climate Science": "Scientists say global temperatures have risen 1.1°C since pre-industrial times",
            "COVID-19 Origin": "The COVID-19 pandemic spread in 2019 from Wuhan, China",
            "Tech": "Apple became the first company to reach $3 trillion market cap",
        }
        selected = st.selectbox("", list(examples.keys()), label_visibility="collapsed")
        default = examples.get(selected, "")
        user_input = st.text_area("", value=default, height=130,
            placeholder="Enter claim, question, or paste a full article…",
            label_visibility="collapsed")

    with col_config:
        st.markdown(label("CONFIGURATION"), unsafe_allow_html=True)
        language = st.selectbox("", ["English","Arabic","French","Spanish","German",
            "Italian","Portuguese","Russian","Chinese","Japanese","Turkish"],
            label_visibility="collapsed")
        extract = st.checkbox("Auto-extract claims", value=True)
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
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
                        overall = data.get("overall_verdict","UNKNOWN")
                        conf    = data.get("confidence", 0)
                        ms      = data.get("processing_time_ms", 0)
                        vc      = verdict_color(overall)

                        # ── Overall verdict bar ──
                        st.markdown(
                            f"<div style='background:var(--bg-deep);border:1px solid {vc}33;"
                            f"border-left:3px solid {vc};border-radius:0 6px 6px 0;"
                            f"padding:14px 20px;margin:16px 0;display:flex;align-items:center;gap:20px;'>"
                            f"<div style='font-family:var(--font-mono);font-size:18px;font-weight:700;color:{vc};letter-spacing:2px;'>{overall}</div>"
                            f"<div style='width:1px;height:30px;background:var(--border);'></div>"
                            f"<div><div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>CONFIDENCE</div>"
                            f"<div style='font-family:var(--font-mono);font-size:16px;color:var(--text-primary);'>{conf:.1f}%</div></div>"
                            f"<div style='width:1px;height:30px;background:var(--border);'></div>"
                            f"<div><div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>PROCESSING</div>"
                            f"<div style='font-family:var(--font-mono);font-size:16px;color:var(--text-primary);'>{ms:.0f}ms</div></div>"
                            f"<div style='width:1px;height:30px;background:var(--border);'></div>"
                            f"<div><div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>CLAIMS</div>"
                            f"<div style='font-family:var(--font-mono);font-size:16px;color:var(--text-primary);'>{data.get('claims_analyzed',0)}</div></div>"
                            f"</div>",
                            unsafe_allow_html=True)

                        # ── Per-claim results ──
                        st.markdown(label("DETAILED ANALYSIS"), unsafe_allow_html=True)

                        for idx, cr in enumerate(data.get("detailed_results",[]), 1):
                            cv   = cr.get("verdict","UNKNOWN")
                            cc   = verdict_color(cv)
                            conf2 = cr.get("confidence",0)
                            claim_text = cr.get("claim_text","")
                            reasoning  = cr.get("reasoning","")
                            sources    = cr.get("sources",[])
                            src_dates  = cr.get("source_dates",[])

                            with st.expander(f"[ {idx:02d} ]  {claim_text[:90]}…", expanded=True):
                                st.markdown(
                                    f"<div style='background:{cc}0d;border:1px solid {cc}33;"
                                    f"border-left:3px solid {cc};border-radius:0 4px 4px 0;"
                                    f"padding:8px 14px;margin-bottom:12px;display:flex;"
                                    f"align-items:center;gap:12px;'>"
                                    f"<span style='font-family:var(--font-mono);font-size:12px;"
                                    f"font-weight:700;color:{cc};letter-spacing:1px;'>{cv}</span>"
                                    f"<span style='font-family:var(--font-mono);font-size:11px;"
                                    f"color:var(--text-muted);'>{conf2:.1f}% confidence</span>"
                                    f"</div>",
                                    unsafe_allow_html=True)

                                st.progress(conf2 / 100)

                                if reasoning:
                                    st.markdown(
                                        f"<div style='background:var(--bg-deep);border:1px solid var(--border);"
                                        f"border-radius:4px;padding:14px;margin:12px 0;"
                                        f"font-family:var(--font-mono);font-size:12px;"
                                        f"color:var(--text-secondary);line-height:1.7;'>{reasoning}</div>",
                                        unsafe_allow_html=True)

                                if sources:
                                    st.markdown(label("SOURCES"), unsafe_allow_html=True)
                                    for si, src in enumerate(sources):
                                        st.markdown(
                                            f"<div style='font-family:var(--font-mono);font-size:12px;"
                                            f"color:var(--accent);margin-bottom:6px;'>"
                                            f"<a href='{src}' target='_blank' style='color:var(--accent);"
                                            f"text-decoration:none;'>↗ {src[:80]}</a></div>",
                                            unsafe_allow_html=True)

                                render_source_timeline(sources, src_dates, cv)
                                render_ai_detection(cr.get("input_ai_detection",{}))

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
# TAB 2 — IDENTITY
# ══════════════════════════════════════════════════════════════════════════

# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — IDENTITY ANALYSIS  (Evidence-Based, Multi-Modal)
# ══════════════════════════════════════════════════════════════════════════
with tab3:

    # ── Disclaimer ────────────────────────────────────────────────────────
    st.markdown(
        "<div style='font-family:var(--font-mono);font-size:9px;color:var(--text-muted);"
        "letter-spacing:1.5px;padding:10px 14px;background:var(--bg-card);"
        "border:1px solid var(--border);border-radius:4px;margin-bottom:16px;'>"
        "EVIDENCE-BASED ANALYSIS — This module does not verify identity, confirm claims, "
        "or detect deepfakes. All outputs are preliminary signals for human review only.</div>",
        unsafe_allow_html=True)

    # ── Inputs ────────────────────────────────────────────────────────────
    ia_c1, ia_c2 = st.columns([1, 1], gap="large")
    with ia_c1:
        st.markdown(label("SUBJECT NAME"), unsafe_allow_html=True)
        ia_name = st.text_input("", placeholder="e.g. Nour Massalkhi",
                                 label_visibility="collapsed", key="ia_name")
        st.markdown(label("CONTEXT (optional)"), unsafe_allow_html=True)
        ia_ctx  = st.text_input("", placeholder="e.g. Software Engineer, UAE",
                                 label_visibility="collapsed", key="ia_ctx")
        st.markdown(label("CV / DOCUMENT (optional)"), unsafe_allow_html=True)
        ia_cv_file = st.file_uploader("", type=["pdf", "docx", "txt"],
                                       label_visibility="collapsed", key="ia_cv_file")
        ia_cv = ""
        if ia_cv_file is not None:
            _ftype = ia_cv_file.name.lower()
            try:
                if _ftype.endswith(".txt"):
                    ia_cv = ia_cv_file.read().decode("utf-8", errors="ignore")
                elif _ftype.endswith(".pdf"):
                    import io as _io
                    try:
                        import pypdf as _pypdf
                        _reader = _pypdf.PdfReader(_io.BytesIO(ia_cv_file.read()))
                        ia_cv = " ".join(p.extract_text() or "" for p in _reader.pages)
                    except ImportError:
                        try:
                            import PyPDF2 as _PyPDF2
                            _reader = _PyPDF2.PdfReader(_io.BytesIO(ia_cv_file.read()))
                            ia_cv = " ".join(
                                (p.extract_text() or "") for p in _reader.pages)
                        except ImportError:
                            st.warning("PDF support requires pypdf. Run: pip install pypdf")
                elif _ftype.endswith(".docx"):
                    import io as _io
                    try:
                        import docx as _docx
                        _doc = _docx.Document(_io.BytesIO(ia_cv_file.read()))
                        ia_cv = " ".join(p.text for p in _doc.paragraphs if p.text.strip())
                    except ImportError:
                        st.warning("DOCX support requires python-docx. Run: pip install python-docx")
            except Exception as _e:
                st.error(f"Could not read file: {_e}")
            if ia_cv:
                word_count = len(ia_cv.split())
                st.markdown(
                    f"<div style='font-family:var(--font-mono);font-size:9px;"
                    f"color:var(--green);padding:4px 8px;background:var(--bg-card);"
                    f"border:1px solid var(--green)33;border-radius:4px;margin-top:4px;'>"
                    f"✓ {ia_cv_file.name} extracted — {word_count} words</div>",
                    unsafe_allow_html=True)
    with ia_c2:
        st.markdown(label("IMAGE (optional)"), unsafe_allow_html=True)
        ia_img  = st.file_uploader("", type=["jpg","jpeg","png","webp"],
                                    label_visibility="collapsed", key="ia_img")
        st.markdown(label("AUDIO (optional)"), unsafe_allow_html=True)
        ia_aud  = st.file_uploader("", type=["wav","mp3","ogg","flac","m4a"],
                                    label_visibility="collapsed", key="ia_aud")
        st.markdown(label("VIDEO (optional)"), unsafe_allow_html=True)
        ia_vid  = st.file_uploader("", type=["mp4","avi","mov","mkv","webm"],
                                    label_visibility="collapsed", key="ia_vid")

    ia_run = st.button("RUN IDENTITY ANALYSIS", key="ia_run",
                        type="primary", use_container_width=True)

    if ia_run:
        if not ia_name and not ia_cv and not ia_cv_file:
            st.warning("Please provide at least a name or CV text.")
        else:
            with st.spinner("Collecting evidence across sources..."):
                try:
                    form_data = {}
                    files     = {}
                    if ia_name: form_data["name"]    = ia_name
                    if ia_ctx:  form_data["context"] = ia_ctx
                    if ia_cv:   form_data["cv_text"] = ia_cv
                    if ia_img:  files["image"] = (ia_img.name, ia_img.getvalue(), ia_img.type)
                    if ia_aud:  files["audio"] = (ia_aud.name, ia_aud.getvalue(), ia_aud.type)
                    if ia_vid:  files["video"] = (ia_vid.name, ia_vid.getvalue(), ia_vid.type)

                    resp = requests.post(
                        f"{API_URL}/identity-analysis/full",
                        data=form_data, files=files, timeout=180
                    )

                    if resp.status_code == 200:
                        r        = resp.json()
                        status   = r.get("identity_status", "INSUFFICIENT_DATA")
                        cs       = r.get("confidence_summary", {})
                        warnings = r.get("warnings", [])
                        media    = r.get("media_analysis", {})

                        # Read merged candidates
                        candidates_merged = r.get("candidates", [])
                        n_merged          = len(candidates_merged)

                        # All scores come from the deterministic _compute_scores()
                        # which uses match/conflict counts — never multipliers alone
                        id_conf    = int(cs.get("identity_confidence", 0) * 100)
                        ev_qual    = cs.get("evidence_score", 0)          # already 0-100
                        # consistency_score is None when no CV provided (N/A)
                        _cons_raw = cs.get("consistency_score", None)
                        cons_sc   = int(_cons_raw) if _cons_raw is not None else None
                        media_sc   = cs.get("media_score", None)          # None = N/A

                        def ring_color(pct, invert=False):
                            v = (100 - pct) if invert else pct
                            if v >= 70: return "var(--green)"
                            if v >= 40: return "var(--amber)"
                            return "var(--red)"

                        def score_ring(score, label_text, invert=False):
                            c   = ring_color(score, invert)
                            d   = int(score * 2.199)
                            return (
                                f"<div style='text-align:center;'>"
                                f"<svg width='80' height='80' viewBox='0 0 80 80'>"
                                f"<circle cx='40' cy='40' r='32' fill='none' stroke='var(--border)' stroke-width='5'/>"
                                f"<circle cx='40' cy='40' r='32' fill='none' stroke='{c}' stroke-width='5'"
                                f" stroke-dasharray='{d} 201' stroke-linecap='round' transform='rotate(-90 40 40)'/>"
                                f"<text x='40' y='44' text-anchor='middle' font-size='15' font-weight='700'"
                                f" fill='{c}' font-family='var(--font-mono)'>{score}%</text>"
                                f"</svg>"
                                f"<div style='font-family:var(--font-mono);font-size:8px;"
                                f"color:var(--text-muted);letter-spacing:1.5px;margin-top:4px;'>"
                                f"{label_text}</div></div>"
                            )

                        # ── Summary Panel ─────────────────────────────────
                        status_colors = {
                            "LIKELY_MATCH":        "var(--green)",
                            "LOW_AMBIGUITY":       "var(--green)",
                            "MULTIPLE_CANDIDATES": "var(--amber)",
                            "AMBIGUOUS":           "var(--red)",
                            "INSUFFICIENT_DATA":   "var(--text-muted)",
                        }
                        sc = status_colors.get(status, "var(--text-muted)")

                        has_media   = bool(media and any(k in media for k in ["image","audio","video"]))
                        media_flag  = media.get("overall_flag", "NO SIGNALS") if has_media else "—"
                        cons_label  = "N/A" if cons_sc is None else ("Partial match" if 30 < cons_sc < 80 else ("Strong match" if cons_sc >= 80 else ("No data" if cons_sc == 0 else "Weak match")))
                        ev_label    = "Strong" if ev_qual >= 70 else ("Medium" if ev_qual >= 40 else "Limited")
                        overall_label = "Moderate uncertainty" if status in ["AMBIGUOUS","MULTIPLE_CANDIDATES"] else ("Low uncertainty" if status in ["LOW_AMBIGUITY","LIKELY_MATCH"] else "Insufficient data")
                        overall_color = "var(--amber)" if status in ["AMBIGUOUS","MULTIPLE_CANDIDATES"] else ("var(--green)" if status in ["LOW_AMBIGUITY","LIKELY_MATCH"] else "var(--red)")

                        st.markdown(
                            f"<div style='background:var(--bg-card);border:1px solid var(--border-lit);"
                            f"border-radius:8px;padding:20px 24px;margin:16px 0;'>"
                            f"<div style='font-family:var(--font-mono);font-size:10px;color:var(--accent);"
                            f"letter-spacing:2px;margin-bottom:14px;'>FINAL ANALYSIS SUMMARY</div>"
                            f"<div style='display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:8px;"
                            f"margin-bottom:14px;font-family:var(--font-mono);font-size:11px;'>"
                            f"<div><span style='color:var(--text-muted);'>Identity</span><br>"
                            f"<span style='color:{sc};font-weight:700;'>{status.replace('_',' ')}</span></div>"
                            f"<div><span style='color:var(--text-muted);'>Evidence</span><br>"
                            f"<span style='color:var(--text-primary);font-weight:700;'>{ev_label}</span></div>"
                            f"<div><span style='color:var(--text-muted);'>Consistency</span><br>"
                            f"<span style='color:var(--text-primary);font-weight:700;'>{cons_label}</span></div>"
                            f"<div><span style='color:var(--text-muted);'>Media</span><br>"
                            f"<span style='color:var(--text-primary);font-weight:700;'>{media_flag[:25] if media_flag else '—'}</span></div>"
                            f"</div>"
                            f"<div style='border-top:1px solid var(--border);padding-top:10px;"
                            f"font-family:var(--font-ui);font-size:13px;color:var(--text-secondary);'>"
                            f"<span style='color:{overall_color};font-weight:600;'>Overall: {overall_label}</span>"
                            f" — {r.get('explanation','')}</div>"
                            f"</div>",
                            unsafe_allow_html=True)

                        # ── Warning Banners ────────────────────────────────
                        for w in warnings:
                            wc = "var(--red)" if "⚠️" in w else "var(--amber)"
                            st.markdown(
                                f"<div style='font-family:var(--font-mono);font-size:11px;"
                                f"color:{wc};padding:8px 14px;background:var(--bg-card);"
                                f"border:1px solid {wc}33;border-radius:4px;"
                                f"margin-bottom:6px;'>{w}</div>",
                                unsafe_allow_html=True)

                        # ── Score Rings ────────────────────────────────────
                        st.markdown(label("CONFIDENCE INDICATORS"), unsafe_allow_html=True)
                        _n_m  = cs.get("_n_matches", 0)
                        _n_c  = cs.get("_n_conflicts", 0)
                        ring_cols = st.columns(4)

                        def score_ring_na(label_text):
                            """Ring showing N/A when media not provided."""
                            return (
                                f"<div style='text-align:center;'>"
                                f"<svg width='80' height='80' viewBox='0 0 80 80'>"
                                f"<circle cx='40' cy='40' r='32' fill='none' stroke='var(--border)' stroke-width='5'/>"
                                f"<text x='40' y='44' text-anchor='middle' font-size='13' font-weight='700'"
                                f" fill='var(--text-muted)' font-family='var(--font-mono)'>N/A</text>"
                                f"</svg>"
                                f"<div style='font-family:var(--font-mono);font-size:8px;"
                                f"color:var(--text-muted);letter-spacing:1.5px;margin-top:4px;'>"
                                f"{label_text}</div></div>"
                            )

                        ring_metrics = [
                            (id_conf, "IDENTITY CONF",
                             f"40 + {_n_m}×12 − {_n_c}×18 − ambiguity×20"),
                            (ev_qual,  "EVIDENCE",
                             f"ext. sources × 10 = {ev_qual}%"),
                            (cons_sc if cons_sc is not None else 0, "CONSISTENCY",
                             f"Bayesian LR posterior = {cons_sc}%" if cons_sc is not None else "no CV provided"),
                        ]
                        for col_i, (score, lbl_t, tip) in enumerate(ring_metrics):
                            with ring_cols[col_i]:
                                if lbl_t == "CONSISTENCY" and cons_sc is None:
                                    st.markdown(score_ring_na("CONSISTENCY"),
                                                unsafe_allow_html=True)
                                else:
                                    st.markdown(score_ring(score, lbl_t), unsafe_allow_html=True)
                                st.markdown(
                                    f"<div style='font-family:var(--font-mono);font-size:8px;"
                                    f"color:var(--text-muted);text-align:center;margin-top:2px;'>"
                                    f"{tip}</div>",
                                    unsafe_allow_html=True)
                        with ring_cols[3]:
                            if media_sc is not None:
                                st.markdown(score_ring(media_sc, "MEDIA CLEAN"),
                                            unsafe_allow_html=True)
                                st.markdown(
                                    f"<div style='font-family:var(--font-mono);font-size:8px;"
                                    f"color:var(--text-muted);text-align:center;margin-top:2px;'>"
                                    f"100 − anomaly = {media_sc}%</div>",
                                    unsafe_allow_html=True)
                            else:
                                st.markdown(score_ring_na("MEDIA CLEAN"),
                                            unsafe_allow_html=True)
                                st.markdown(
                                    f"<div style='font-family:var(--font-mono);font-size:8px;"
                                    f"color:var(--text-muted);text-align:center;margin-top:2px;'>"
                                    f"no media provided</div>",
                                    unsafe_allow_html=True)

                        # ── Identity Candidates ────────────────────────────
                        candidates = r.get("candidates", [])
                        if candidates:
                            st.markdown(
                                label(f"IDENTITY CANDIDATES — {len(candidates)} after entity merging"),
                                unsafe_allow_html=True)
                            for i, cand in enumerate(candidates):
                                score  = cand.get("similarity_score", 0)
                                cc     = ring_color(int(score * 100))
                                amb    = "⚠️ " if cand.get("ambiguity_flag") else ""
                                nqual  = cand.get("name_match_quality", "")
                                nqc    = "var(--green)" if nqual == "full name match" else (
                                         "var(--amber)" if nqual == "partial match" else "var(--text-muted)")
                                with st.expander(
                                    f"{amb}#{i+1}  {cand.get('name','Unknown')}  "
                                    f"[{cand.get('platform','')}]  score: {score:.2f}",
                                    expanded=(i == 0)
                                ):
                                    left, right = st.columns([1, 3])
                                    with left:
                                        st.markdown(score_ring(int(score*100), "SIMILARITY"),
                                                    unsafe_allow_html=True)
                                    with right:
                                        if nqual:
                                            st.markdown(
                                                f"<span style='background:{nqc}18;border:1px solid {nqc}44;"
                                                f"color:{nqc};padding:2px 10px;border-radius:3px;"
                                                f"font-family:var(--font-mono);font-size:10px;'>"
                                                f"{nqual.upper()}</span>",
                                                unsafe_allow_html=True)
                                        # Score breakdown bar
                                        breakdown = cand.get("score_breakdown", {})
                                        if breakdown:
                                            st.markdown(
                                                f"<div style='margin-top:8px;font-family:var(--font-mono);"
                                                f"font-size:9px;color:var(--text-muted);letter-spacing:1.5px;"
                                                f"margin-bottom:4px;'>SCORE BREAKDOWN</div>",
                                                unsafe_allow_html=True)
                                            for bk_key, bk_val in breakdown.items():
                                                bk_pct = int(float(bk_val) * 100)
                                                bk_max = {"name": 50, "context": 30, "signals": 20}.get(bk_key, 100)
                                                bk_fill = int((float(bk_val) / bk_max) * 100) if bk_max else 0
                                                bk_c = "var(--green)" if bk_fill >= 60 else ("var(--amber)" if bk_fill >= 30 else "var(--text-muted)")
                                                st.markdown(
                                                    f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>"
                                                    f"<div style='font-family:var(--font-mono);font-size:9px;"
                                                    f"color:var(--text-muted);width:60px;'>{bk_key.upper()}</div>"
                                                    f"<div style='flex:1;height:4px;background:var(--border);border-radius:2px;'>"
                                                    f"<div style='width:{min(100,bk_fill)}%;height:100%;"
                                                    f"background:{bk_c};border-radius:2px;'></div></div>"
                                                    f"<div style='font-family:var(--font-mono);font-size:9px;"
                                                    f"color:{bk_c};width:30px;text-align:right;'>{bk_pct}</div>"
                                                    f"</div>",
                                                    unsafe_allow_html=True)
                                        if cand.get("extracted_info"):
                                            st.markdown(
                                                f"<div style='font-family:var(--font-ui);font-size:13px;"
                                                f"color:var(--text-secondary);margin:8px 0;'>"
                                                f"{cand['extracted_info']}</div>",
                                                unsafe_allow_html=True)
                                        if cand.get("match_explanation"):
                                            st.markdown(
                                                f"<div style='font-family:var(--font-ui);font-size:11px;"
                                                f"color:var(--text-muted);font-style:italic;margin-bottom:8px;'>"
                                                f"{cand['match_explanation']}</div>",
                                                unsafe_allow_html=True)
                                        # Sources list — always use sources[], fall back to profile_url
                                        src_list = cand.get("sources") or (
                                            [cand["profile_url"]] if cand.get("profile_url") else []
                                        )
                                        src_list = [s for s in src_list if s]
                                        if src_list:
                                            merged_badge = ""
                                            if cand.get("merged") and len(src_list) > 1:
                                                merged_badge = (
                                                    f"<span style='background:var(--green)18;"
                                                    f"border:1px solid var(--green)44;color:var(--green);"
                                                    f"padding:1px 8px;border-radius:3px;"
                                                    f"font-family:var(--font-mono);font-size:9px;"
                                                    f"margin-left:8px;'>✓ {len(src_list)} merged</span>"
                                                )
                                            st.markdown(
                                                f"<div style='font-family:var(--font-mono);font-size:9px;"
                                                f"color:var(--text-muted);letter-spacing:1.5px;"
                                                f"margin-top:10px;margin-bottom:6px;'>"
                                                f"SOURCES{merged_badge}</div>",
                                                unsafe_allow_html=True)
                                            for idx_s, src in enumerate(src_list[:4]):
                                                # Derive a readable label from the URL
                                                src_domain = re.sub(r'https?://', '', src).split('/')[0].replace('www.','')
                                                st.markdown(
                                                    f"<a href='{src}' target='_blank' "
                                                    f"style='display:flex;align-items:center;gap:6px;"
                                                    f"font-family:var(--font-mono);font-size:11px;"
                                                    f"color:var(--accent);text-decoration:none;"
                                                    f"padding:5px 8px;margin-bottom:4px;"
                                                    f"background:var(--bg-deep);"
                                                    f"border:1px solid var(--border);"
                                                    f"border-radius:4px;'>"
                                                    f"<span style='color:var(--text-muted);'>{idx_s+1}.</span> "
                                                    f"View Profile — {src_domain}</a>",
                                                    unsafe_allow_html=True)
                        else:
                            st.markdown(
                                f"<div style='background:var(--bg-card);border:1px solid var(--border);"
                                f"border-radius:6px;padding:14px;font-family:var(--font-mono);"
                                f"font-size:11px;color:var(--text-muted);'>"
                                f"No matching candidates found. Try providing more context "
                                f"(job title, location, company).</div>",
                                unsafe_allow_html=True)

                        # ── Claims & Evidence ──────────────────────────────
                        claims = r.get("claims_analysis", [])
                        if claims:
                            st.markdown(
                                label(f"CLAIMS & EVIDENCE — {len(claims)} extracted"),
                                unsafe_allow_html=True)
                            conf_meta = {
                                "high":      ("STRONG EVIDENCE",  "var(--green)"),
                                "medium":    ("PARTIAL EVIDENCE", "var(--amber)"),
                                "low":       ("WEAK EVIDENCE",    "var(--red)"),
                                "not_found": ("NO EVIDENCE",      "var(--text-muted)"),
                            }
                            for cl in claims:
                                conf     = cl.get("confidence", "not_found")
                                clbl, cc = conf_meta.get(conf, (conf.upper(), "var(--text-muted)"))
                                with st.expander(
                                    f"[{cl.get('type','?').upper()}]  {cl.get('claim','')[:80]}"
                                ):
                                    st.markdown(
                                        f"<span style='background:{cc}18;border:1px solid {cc}44;"
                                        f"color:{cc};padding:2px 10px;border-radius:3px;"
                                        f"font-family:var(--font-mono);font-size:10px;'>{clbl}</span>",
                                        unsafe_allow_html=True)
                                    if cl.get("note"):
                                        st.markdown(
                                            f"<div style='font-family:var(--font-ui);font-size:12px;"
                                            f"color:var(--text-muted);margin:8px 0;font-style:italic;'>"
                                            f"{cl['note']}</div>",
                                            unsafe_allow_html=True)
                                    for ev in cl.get("evidence", [])[:3]:
                                        st.markdown(
                                            f"<div style='margin-bottom:8px;padding:8px 10px;"
                                            f"background:var(--bg-card);border:1px solid var(--border);"
                                            f"border-radius:4px;'>"
                                            f"<a href='{ev.get('url','')}' target='_blank' "
                                            f"style='font-family:var(--font-mono);font-size:11px;"
                                            f"color:var(--accent);text-decoration:none;'>"
                                            f"{ev.get('title','')[:70]}</a>"
                                            f"<div style='font-family:var(--font-ui);font-size:11px;"
                                            f"color:var(--text-muted);margin-top:4px;'>"
                                            f"{ev.get('snippet','')[:150]}</div></div>",
                                            unsafe_allow_html=True)

                        # ── Consistency Analysis ───────────────────────────
                        cons = r.get("consistency", {})
                        if cons and any([cons.get("consistent"), cons.get("inconsistent"), cons.get("unknown")]):
                            st.markdown(label("CONSISTENCY ANALYSIS"), unsafe_allow_html=True)
                            cs_score  = cons.get("consistency_score", 0)
                            cs_color  = ring_color(int(cs_score * 100))
                            compared  = cons.get("compared_against", {})
                            col_ring, col_detail = st.columns([1, 3])
                            with col_ring:
                                st.markdown(score_ring(int(cs_score*100), "CONSISTENCY"),
                                            unsafe_allow_html=True)
                            with col_detail:
                                st.markdown(
                                    f"<div style='font-family:var(--font-mono);font-size:9px;"
                                    f"color:var(--text-muted);letter-spacing:2px;margin-bottom:4px;'>"
                                    f"COMPARED AGAINST: {compared.get('name','?')}</div>"
                                    f"<div style='font-family:var(--font-mono);font-size:9px;"
                                    f"color:var(--text-muted);'>Measures claim-profile alignment. "
                                    f"Not a trust verdict.</div>",
                                    unsafe_allow_html=True)
                                if compared.get("url"):
                                    st.markdown(
                                        f"<a href='{compared['url']}' target='_blank' "
                                        f"style='font-family:var(--font-mono);font-size:11px;"
                                        f"color:var(--accent);text-decoration:none;'>"
                                        f"VIEW SOURCE →</a>",
                                        unsafe_allow_html=True)

                            col_ok, col_bad, col_unk = st.columns(3)
                            for col, key, clr, prefix in [
                                (col_ok,  "consistent",   "var(--green)",      "+"),
                                (col_bad, "inconsistent", "var(--red)",        "⚠"),
                                (col_unk, "unknown",      "var(--text-muted)", "?"),
                            ]:
                                items = cons.get(key, [])
                                with col:
                                    st.markdown(
                                        f"<div style='font-family:var(--font-mono);font-size:9px;"
                                        f"color:{clr};letter-spacing:2px;margin-bottom:8px;'>"
                                        f"{key.upper()} ({len(items)})</div>",
                                        unsafe_allow_html=True)
                                    for c in items:
                                        st.markdown(
                                            f"<div style='font-size:12px;color:var(--text-secondary);"
                                            f"padding:4px 0;border-bottom:1px solid var(--border);'>"
                                            f"{prefix} {c.get('claim','')[:55]}</div>",
                                            unsafe_allow_html=True)


                        # ── Decision Explanation Engine ────────────────────
                        de = r.get("decision_explanation", {})
                        if de:
                            st.markdown(label("IDENTITY DECISION EXPLANATION"),
                                        unsafe_allow_html=True)

                            de_sims   = de.get("similarities", [])
                            de_confs  = de.get("conflicts", [])
                            de_fd     = de.get("final_decision", {})
                            de_verdict = de_fd.get("verdict", "")
                            de_reason  = de_fd.get("reason", [])
                            de_concl   = de_fd.get("conclusion", "")

                            col_de_l, col_de_r = st.columns(2)

                            # Similarities column
                            with col_de_l:
                                st.markdown(
                                    f"<div style='font-family:var(--font-mono);font-size:9px;"
                                    f"color:var(--green);letter-spacing:2px;margin-bottom:8px;'>"
                                    f"SUPPORTING SIGNALS ({len(de_sims)})</div>",
                                    unsafe_allow_html=True)
                                if de_sims:
                                    for sim in de_sims:
                                        st.markdown(
                                            f"<div style='padding:6px 10px;margin-bottom:5px;"
                                            f"background:var(--bg-deep);"
                                            f"border-left:2px solid var(--green);"
                                            f"border-radius:0 4px 4px 0;'>"
                                            f"<div style='font-family:var(--font-mono);font-size:9px;"
                                            f"color:var(--green);letter-spacing:1px;margin-bottom:2px;'>"
                                            f"✔ {sim.get('field','').upper()}</div>"
                                            f"<div style='font-family:var(--font-ui);font-size:12px;"
                                            f"color:var(--text-secondary);'>{sim.get('detail','')}</div>"
                                            f"</div>",
                                            unsafe_allow_html=True)
                                else:
                                    st.markdown(
                                        f"<div style='font-family:var(--font-ui);font-size:12px;"
                                        f"color:var(--text-muted);padding:8px;'>"
                                        f"No supporting signals found.</div>",
                                        unsafe_allow_html=True)

                            # Conflicts column
                            with col_de_r:
                                st.markdown(
                                    f"<div style='font-family:var(--font-mono);font-size:9px;"
                                    f"color:var(--red);letter-spacing:2px;margin-bottom:8px;'>"
                                    f"CONFLICTS ({len(de_confs)})</div>",
                                    unsafe_allow_html=True)
                                if de_confs:
                                    for conf in de_confs:
                                        sev   = conf.get("severity", "medium")
                                        sev_c = "var(--red)" if sev == "high" else "var(--amber)"
                                        sev_l = "HIGH" if sev == "high" else ("MED" if sev == "medium" else "LOW")
                                        st.markdown(
                                            f"<div style='padding:6px 10px;margin-bottom:5px;"
                                            f"background:var(--bg-deep);"
                                            f"border-left:2px solid {sev_c};"
                                            f"border-radius:0 4px 4px 0;'>"
                                            f"<div style='display:flex;align-items:center;gap:6px;"
                                            f"margin-bottom:3px;'>"
                                            f"<span style='font-family:var(--font-mono);font-size:9px;"
                                            f"color:{sev_c};letter-spacing:1px;'>⚠ {conf.get('field','').upper()}</span>"
                                            f"<span style='background:{sev_c}18;border:1px solid {sev_c}44;"
                                            f"color:{sev_c};padding:1px 6px;border-radius:2px;"
                                            f"font-family:var(--font-mono);font-size:8px;'>{sev_l}</span>"
                                            f"</div>"
                                            f"<div style='font-family:var(--font-ui);font-size:12px;"
                                            f"color:var(--text-secondary);'>{conf.get('detail','')}</div>"
                                            + (
                                                f"<div style='display:flex;gap:12px;margin-top:4px;'>"
                                                f"<span style='font-family:var(--font-mono);font-size:10px;"
                                                f"color:var(--text-muted);'>CV/Input: "
                                                f"<span style='color:var(--amber);'>{conf.get('input','')[:40]}</span></span>"
                                                f"<span style='font-family:var(--font-mono);font-size:10px;"
                                                f"color:var(--text-muted);'>Sources: "
                                                f"<span style='color:var(--text-primary);'>{conf.get('source','')[:40]}</span></span>"
                                                f"</div>"
                                                if conf.get("input") and conf.get("source") else ""
                                            )
                                            + f"</div>",
                                            unsafe_allow_html=True)
                                else:
                                    st.markdown(
                                        f"<div style='font-family:var(--font-ui);font-size:12px;"
                                        f"color:var(--text-muted);padding:8px;'>"
                                        f"No conflicts detected.</div>",
                                        unsafe_allow_html=True)

                            # Final Decision block
                            if de_verdict:
                                vdict_colors = {
                                    "LIKELY MATCH":   "var(--green)",
                                    "LOW CONFIDENCE": "var(--amber)",
                                    "AMBIGUOUS":      "var(--red)",
                                }
                                vc2 = vdict_colors.get(de_verdict, "var(--text-muted)")
                                reason_html = "".join(
                                    f"<div style='font-family:var(--font-ui);font-size:12px;"
                                    f"color:var(--text-secondary);padding:3px 0;"
                                    f"border-bottom:1px solid var(--border);'>— {rr}</div>"
                                    for rr in de_reason
                                )
                                st.markdown(
                                    f"<div style='background:var(--bg-card);"
                                    f"border:1px solid {vc2}44;"
                                    f"border-top:3px solid {vc2};"
                                    f"border-radius:0 0 6px 6px;"
                                    f"padding:16px 20px;margin-top:12px;'>"
                                    f"<div style='display:flex;align-items:center;gap:12px;"
                                    f"margin-bottom:12px;'>"
                                    f"<div style='font-family:var(--font-mono);font-size:10px;"
                                    f"color:var(--text-muted);letter-spacing:2px;'>FINAL DECISION</div>"
                                    f"<div style='background:{vc2}18;border:1px solid {vc2}44;"
                                    f"color:{vc2};padding:3px 14px;border-radius:3px;"
                                    f"font-family:var(--font-mono);font-size:12px;"
                                    f"font-weight:700;letter-spacing:1px;'>{de_verdict}</div>"
                                    f"</div>"
                                    f"<div style='margin-bottom:10px;'>{reason_html}</div>"
                                    f"<div style='font-family:var(--font-ui);font-size:13px;"
                                    f"color:var(--text-secondary);line-height:1.6;"
                                    f"padding-top:8px;border-top:1px solid var(--border);'>"
                                    f"{de_concl}</div>"
                                    f"</div>",
                                    unsafe_allow_html=True)

                        # ── Media Analysis ─────────────────────────────────
                        if has_media:
                            st.markdown(label("MEDIA SIGNALS"), unsafe_allow_html=True)
                            # Use overall_authenticity from new schema, fallback to overall_flag
                            overall_auth  = media.get("overall_authenticity", {})
                            overall_label = overall_auth.get("authenticity_label", "")
                            overall       = media.get("overall_flag", "NO SIGNALS")
                            if overall_label:
                                overall = overall_label.upper()
                            oc = "var(--red)" if any(x in overall.upper() for x in ["MANIPULATED","SUSPICIOUS"]) else (
                                 "var(--amber)" if any(x in overall.upper() for x in ["LIKELY","MINOR","UNCERTAIN"]) else "var(--green)")

                            for mtype, icon in [("image","IMG"), ("audio","AUD"), ("video","VID")]:
                                mdata = media.get(mtype)
                                if not mdata:
                                    continue
                                # New schema: authenticity_label + deepfake_probability
                                auth_label = mdata.get("authenticity_label", "")
                                dfprob     = mdata.get("deepfake_probability", None)
                                ev_str     = mdata.get("evidence_strength", "")
                                mflag      = auth_label or mdata.get("flag", "no obvious anomalies")
                                mscore     = mdata.get("anomaly_score", int((dfprob or 0) * 100))
                                mclean     = max(0, 100 - mscore)
                                mc = (
                                    "var(--red)"   if any(x in mflag.lower() for x in ["manipulated","suspicious"]) else
                                    "var(--amber)" if any(x in mflag.lower() for x in ["likely","uncertain","variance","inconsistencies"]) else
                                    "var(--green)"
                                )

                                col_r, col_info = st.columns([1, 4])
                                with col_r:
                                    st.markdown(score_ring(mclean, f"{icon} CLEAN"),
                                                unsafe_allow_html=True)
                                with col_info:
                                    # Header: authenticity label + deepfake probability
                                    dfprob_str = f" · deepfake prob: {dfprob:.2f}" if dfprob is not None else ""
                                    ev_str_disp = f" · evidence: {ev_str}" if ev_str else ""
                                    st.markdown(
                                        f"<div style='padding-top:8px;'>"
                                        f"<div style='font-family:var(--font-mono);font-size:10px;"
                                        f"font-weight:700;color:{mc};margin-bottom:4px;'>"
                                        f"{mtype.upper()} — {mflag.upper()}"
                                        f"</div>"
                                        f"<div style='font-family:var(--font-mono);font-size:9px;"
                                        f"color:var(--text-muted);margin-bottom:6px;'>"
                                        f"{dfprob_str}{ev_str_disp}"
                                        f"</div>",
                                        unsafe_allow_html=True)
                                    signals = mdata.get("signals", [])
                                    if signals:
                                        for s in signals:
                                            st.markdown(
                                                f"<div style='font-family:var(--font-ui);font-size:12px;"
                                                f"color:var(--text-secondary);padding:2px 0;"
                                                f"border-bottom:1px solid var(--border);'>· {s}</div>",
                                                unsafe_allow_html=True)
                                    else:
                                        st.markdown(
                                            f"<div style='font-family:var(--font-ui);font-size:12px;"
                                            f"color:var(--text-muted);'>No signals detected.</div>",
                                            unsafe_allow_html=True)
                                    # Method note
                                    method = mdata.get("method","")
                                    if method:
                                        st.markdown(
                                            f"<div style='font-family:var(--font-ui);font-size:10px;"
                                            f"color:var(--text-muted);font-style:italic;margin-top:4px;'>"
                                            f"{method}</div>",
                                            unsafe_allow_html=True)
                                    st.markdown("</div>", unsafe_allow_html=True)

                            st.markdown(
                                f"<div style='font-family:var(--font-ui);font-size:11px;"
                                f"color:var(--text-muted);font-style:italic;margin-top:8px;"
                                f"padding:8px 12px;background:var(--bg-card);"
                                f"border:1px solid var(--border);border-radius:4px;'>"
                                f"{media.get('disclaimer','')}</div>",
                                unsafe_allow_html=True)

                    else:
                        st.error(f"API Error {resp.status_code}: {resp.text}")

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend.")
                except Exception as e:
                    st.error(f"Error: {e}")


# ── Footer ────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='margin-top:48px;padding-top:16px;border-top:1px solid var(--border);"
    "display:flex;justify-content:space-between;'>"
    "<span style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>ZERO-TRUST ARCHITECTURE</span>"
    "<span style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>MULTI-AGENT SYSTEM</span>"
    "<span style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>RAG-POWERED VERIFICATION</span>"
    "</div>",
    unsafe_allow_html=True)
