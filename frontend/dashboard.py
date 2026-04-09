import streamlit as st
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

tab1, tab2 = st.tabs(["FACT CHECK", "IDENTITY"])

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
with tab2:
    id_tab1, id_tab2 = st.tabs(["SEARCH BY NAME", "PHOTO IDENTIFICATION"])

    # ── Name Search ───────────────────────────────────────────────────────
    with id_tab1:
        st.markdown(label("SUBJECT NAME"), unsafe_allow_html=True)
        id_name = st.text_input("", placeholder="e.g. Elon Musk, Marco Rubio, Reuters…",
                                 label_visibility="collapsed", key="id_name_v4")

        if st.button("▶  SEARCH ACROSS PLATFORMS", key="search_platforms_btn", use_container_width=True):
            if not id_name.strip():
                st.warning("Enter a name.")
            else:
                with st.spinner(""):
                    st.markdown(
                        f"<div style='font-family:var(--font-mono);font-size:11px;color:var(--accent);letter-spacing:1px;margin:8px 0;'>SCANNING PLATFORMS…</div>",
                        unsafe_allow_html=True)
                    try:
                        resp = requests.post(f"{API_URL}/identity-search-platforms",
                            json={"name": id_name}, timeout=60)
                        if resp.status_code == 200:
                            st.session_state["platform_profiles"] = resp.json().get("profiles",[])
                            st.session_state["identity_result"]   = None
                        else:
                            st.error(resp.text)
                    except Exception as e:
                        st.error(str(e))

        if st.session_state.get("platform_profiles") is not None:
            profiles = st.session_state["platform_profiles"]
            if not profiles:
                st.markdown(
                    "<div style='background:var(--bg-card);border:1px solid var(--border);"
                    "border-radius:6px;padding:16px;font-family:var(--font-mono);font-size:12px;"
                    "color:var(--text-muted);'>NO VERIFIED PROFILES FOUND — Try a different spelling or add more context.</div>",
                    unsafe_allow_html=True)
            else:
                st.markdown(
                    f"<div style='font-family:var(--font-mono);font-size:10px;color:var(--accent);"
                    f"letter-spacing:2px;margin-bottom:12px;'>{len(profiles)} VERIFIED PROFILE(S) FOUND</div>",
                    unsafe_allow_html=True)
                cols = st.columns(min(len(profiles), 3))
                for i, p in enumerate(profiles):
                    with cols[i % min(len(profiles), 3)]:
                        color   = p.get("color","#7a9bb5")
                        plat    = p.get("platform","")
                        icon    = p.get("icon","")
                        url     = p.get("url","")
                        title   = p.get("title","")
                        snippet = p.get("snippet","")
                        st.markdown(
                            f"<div style='background:var(--bg-card);border:1px solid {color}33;"
                            f"border-top:2px solid {color};border-radius:6px;padding:14px;"
                            f"margin-bottom:8px;'>"
                            f"<div style='font-family:var(--font-mono);font-size:10px;color:{color};"
                            f"letter-spacing:1px;font-weight:700;margin-bottom:8px;'>{icon} {plat.upper()}</div>"
                            f"<div style='font-size:12px;color:var(--text-primary);font-weight:500;"
                            f"margin-bottom:6px;line-height:1.4;'>{title[:55]}</div>"
                            f"<div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);"
                            f"margin-bottom:10px;line-height:1.5;'>{snippet[:90]}…</div>"
                            f"<a href='{url}' target='_blank' style='font-family:var(--font-mono);"
                            f"font-size:10px;color:{color};text-decoration:none;letter-spacing:1px;'>"
                            f"↗ VIEW PROFILE</a></div>",
                            unsafe_allow_html=True)
                        if st.button("LOAD FULL PROFILE", key=f"load_{i}"):
                            with st.spinner(""):
                                try:
                                    r2 = requests.post(f"{API_URL}/identity-verify-name",
                                        json={"name": id_name, "context": f"{plat} {snippet[:100]}"},
                                        timeout=60)
                                    if r2.status_code == 200:
                                        st.session_state["identity_result"]   = r2.json()
                                        st.session_state["platform_profiles"] = None
                                        st.rerun()
                                    else:
                                        st.error(r2.text)
                                except Exception as e:
                                    st.error(str(e))

    # ── Photo ID ──────────────────────────────────────────────────────────
    with id_tab2:
        st.markdown(
            f"<div style='background:var(--bg-card);border:1px solid var(--amber-dim);"
            f"border-left:3px solid var(--amber);border-radius:0 6px 6px 0;"
            f"padding:10px 16px;margin-bottom:16px;font-family:var(--font-mono);"
            f"font-size:11px;color:var(--amber);'>"
            f"⚠  PHOTO IDENTIFICATION WORKS FOR PUBLIC FIGURES ONLY (politicians, celebrities, athletes, etc.)</div>",
            unsafe_allow_html=True)

        uploaded = st.file_uploader("", type=["jpg","jpeg","png","webp"], label_visibility="collapsed", key="id_photo")
        if st.button("▶  IDENTIFY & VERIFY", key="id_photo_btn"):
            if not uploaded:
                st.warning("Upload a photo first.")
            else:
                with st.spinner(""):
                    try:
                        files = {"photo": (uploaded.name, uploaded.getvalue(), uploaded.type)}
                        r2 = requests.post(f"{API_URL}/identity-verify-photo", files=files, timeout=60)
                        if r2.status_code == 200:
                            st.session_state["identity_result"]         = r2.json()
                            st.session_state["identity_uploaded_photo"] = uploaded.getvalue()
                        else:
                            st.error(r2.text)
                    except Exception as e:
                        st.error(str(e))

    # ── Identity Result Card ──────────────────────────────────────────────
    if st.session_state.get("identity_result"):
        result   = st.session_state["identity_result"]
        score    = result.get("trust_score", 0)
        badge_t  = result.get("badge","UNKNOWN")
        summary  = result.get("summary","")
        bio      = result.get("bio","")
        photo_url = result.get("photo_url","")
        pd2      = result.get("checks",{}).get("profile",{})
        persona  = result.get("persona_type", pd2.get("persona_type","Unknown"))
        risk     = result.get("risk_level",   pd2.get("risk_level","Unknown"))
        interesting = result.get("interesting_fact", pd2.get("interesting_fact",""))
        red_flags   = result.get("red_flags",[])
        pos_signals = result.get("positive_signals",[])
        affiliations = result.get("affiliations",[])
        social_links = result.get("social_links",[])
        controversies = result.get("controversies",[])
        recs          = result.get("recommendations",[])
        input_type  = result.get("input_type","name")
        input_value = result.get("input_value", result.get("input",{}).get("name",""))
        identification = result.get("identification",{})

        st.markdown("<div style='margin-top:24px;border-top:1px solid var(--border);padding-top:20px;'></div>", unsafe_allow_html=True)

        # Photo banner for photo identification
        if input_type == "photo" and identification:
            id_conf = identification.get("confidence",0)
            id_name_f = identification.get("name","Unknown")
            id_role = identification.get("likely_role","")
            bc = "var(--green)" if id_conf >= 70 else "var(--amber)"
            st.markdown(
                f"<div style='background:var(--bg-deep);border:1px solid {bc}33;"
                f"border-left:3px solid {bc};border-radius:0 4px 4px 0;"
                f"padding:10px 16px;margin-bottom:14px;font-family:var(--font-mono);"
                f"font-size:11px;color:{bc};'>"
                f"IDENTIFIED: {id_name_f.upper()} · {id_role.upper()} · CONFIDENCE {id_conf}%</div>",
                unsafe_allow_html=True)

        # Photo + trust ring
        col_img, col_score = st.columns([1, 4], gap="large")
        with col_img:
            upl = st.session_state.get("identity_uploaded_photo")
            if input_type == "photo" and upl:
                st.image(upl, width=120)
            elif photo_url:
                try: st.image(photo_url, width=120)
                except: st.markdown("👤")
            else:
                st.markdown("<div style='font-size:56px;text-align:center;padding:10px;'>👤</div>", unsafe_allow_html=True)

        with col_score:
            render_trust_ring(score, input_value, badge_t, risk, persona)

        if summary:
            st.markdown(
                f"<div style='font-family:var(--font-mono);font-size:12px;color:var(--text-secondary);"
                f"line-height:1.7;border-left:2px solid var(--border-lit);padding-left:14px;"
                f"margin-bottom:14px;'>{summary}</div>",
                unsafe_allow_html=True)

        if bio:
            with st.expander("FULL BIOGRAPHY"):
                st.markdown(f"<div style='font-family:var(--font-mono);font-size:12px;color:var(--text-secondary);line-height:1.7;'>{bio}</div>", unsafe_allow_html=True)

        if interesting:
            st.markdown(
                f"<div style='background:var(--bg-deep);border:1px solid var(--accent-dim)33;"
                f"border-left:2px solid var(--accent-dim);border-radius:0 4px 4px 0;"
                f"padding:10px 16px;margin-bottom:14px;font-family:var(--font-mono);"
                f"font-size:11px;color:var(--accent-dim);'>💡 {interesting}</div>",
                unsafe_allow_html=True)

        if affiliations:
            st.markdown(label("AFFILIATIONS"), unsafe_allow_html=True)
            aff = " ".join([f"<span style='background:var(--bg-card);border:1px solid var(--border-lit);color:var(--text-secondary);padding:3px 10px;border-radius:3px;font-family:var(--font-mono);font-size:10px;letter-spacing:0.5px;'>{a}</span>" for a in affiliations[:6]])
            st.markdown(f"<div style='display:flex;flex-wrap:wrap;gap:6px;margin-bottom:14px;'>{aff}</div>", unsafe_allow_html=True)

        if social_links:
            st.markdown(label("ONLINE PRESENCE"), unsafe_allow_html=True)
            for link in social_links[:5]:
                st.markdown(f"<div style='font-family:var(--font-mono);font-size:11px;margin-bottom:4px;'><a href='{link}' target='_blank' style='color:var(--accent-dim);text-decoration:none;'>↗ {link[:70]}</a></div>", unsafe_allow_html=True)

        col1, col2 = st.columns(2, gap="large")
        with col1:
            if red_flags:
                st.markdown(label("RED FLAGS"), unsafe_allow_html=True)
                for f in red_flags[:5]:
                    st.markdown(f"<div style='font-family:var(--font-mono);font-size:11px;color:var(--red);padding:4px 0;border-bottom:1px solid var(--border);'>⚑ {f}</div>", unsafe_allow_html=True)
        with col2:
            if pos_signals:
                st.markdown(label("POSITIVE SIGNALS"), unsafe_allow_html=True)
                for s in pos_signals[:5]:
                    st.markdown(f"<div style='font-family:var(--font-mono);font-size:11px;color:var(--green);padding:4px 0;border-bottom:1px solid var(--border);'>✓ {s}</div>", unsafe_allow_html=True)

        if controversies:
            st.markdown(label("CONTROVERSIES"), unsafe_allow_html=True)
            for c in controversies[:4]:
                st.markdown(f"<div style='font-family:var(--font-mono);font-size:11px;color:var(--amber);padding:4px 0;border-bottom:1px solid var(--border);'>◈ {c}</div>", unsafe_allow_html=True)

        if recs:
            st.markdown(label("RECOMMENDATIONS"), unsafe_allow_html=True)
            for r in recs[:3]:
                st.markdown(f"<div style='font-family:var(--font-mono);font-size:11px;color:var(--text-secondary);padding:4px 0;'>→ {r}</div>", unsafe_allow_html=True)

        render_pdf_download([], result)


# ── Footer ────────────────────────────────────────────────────────────────
st.markdown(
    "<div style='margin-top:48px;padding-top:16px;border-top:1px solid var(--border);"
    "display:flex;justify-content:space-between;'>"
    "<span style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>ZERO-TRUST ARCHITECTURE</span>"
    "<span style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>MULTI-AGENT SYSTEM</span>"
    "<span style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>RAG-POWERED VERIFICATION</span>"
    "</div>",
    unsafe_allow_html=True)
