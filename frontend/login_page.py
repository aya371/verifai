"""
Login page for VerifAI.
Save to: frontend/login_page.py
"""
import streamlit as st
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def render_login_css():
    theme = st.session_state.get("theme", "dark")
    if theme == "light":
        bg, card, text, muted, border = "#f8fafc", "#ffffff", "#0f172a", "#64748b", "#cbd5e1"
    else:
        bg, card, text, muted, border = "#080f17", "#111f2e", "#f1f8ff", "#4a7090", "#1e3448"

    st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap');

html, body, [class*="css"] {{
    font-family: 'Space Grotesk', sans-serif !important;
    background-color: {bg} !important;
    color: {text} !important;
}}
.main .block-container {{
    padding: 0 !important;
    max-width: 100% !important;
}}
#MainMenu, footer, header {{ visibility: hidden !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}

[data-testid="stTextInput"] input {{
    background: {card} !important;
    border: 1px solid {border} !important;
    border-radius: 6px !important;
    color: {text} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
}}
[data-testid="stTextInput"] input:focus {{
    border-color: #38bdf8 !important;
    box-shadow: 0 0 0 3px #38bdf815 !important;
}}
[data-testid="stButton"] button {{
    background: linear-gradient(135deg, #38bdf820, #38bdf808) !important;
    border: 1px solid #38bdf8 !important;
    color: #38bdf8 !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 2px !important;
    border-radius: 4px !important;
    padding: 10px 0 !important;
    width: 100% !important;
    transition: all 0.2s !important;
}}
[data-testid="stButton"] button:hover {{
    background: linear-gradient(135deg, #38bdf835, #38bdf815) !important;
    box-shadow: 0 0 20px #38bdf825 !important;
}}
</style>
""", unsafe_allow_html=True)


def render_login_page() -> bool:
    """
    Renders the login/register page.
    Returns True if user is authenticated, False otherwise.
    """
    from backend.auth.auth_manager import login_user, register_user, validate_session

    # Check existing session
    token = st.session_state.get("auth_token")
    if token:
        user = validate_session(token)
        if user:
            st.session_state["current_user"] = user
            return True

    render_login_css()

    theme = st.session_state.get("theme", "dark")
    if theme == "light":
        bg, card, text, muted, border, accent = "#f8fafc", "#ffffff", "#0f172a", "#64748b", "#cbd5e1", "#0284c7"
    else:
        bg, card, text, muted, border, accent = "#080f17", "#111f2e", "#f1f8ff", "#4a7090", "#1e3448", "#38bdf8"

    # Centered layout
    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<div style='height:60px;'></div>", unsafe_allow_html=True)

        # Logo
        st.markdown(
            f"<div style='text-align:center;margin-bottom:40px;'>"
            f"<div style='font-family:JetBrains Mono,monospace;font-size:36px;"
            f"font-weight:700;color:{accent};letter-spacing:6px;'>VERIFAI</div>"
            f"<div style='font-family:JetBrains Mono,monospace;font-size:10px;"
            f"color:{muted};letter-spacing:4px;margin-top:6px;'>DIGITAL TRUST PLATFORM</div>"
            f"</div>",
            unsafe_allow_html=True)

        # Tab toggle
        if "auth_tab" not in st.session_state:
            st.session_state["auth_tab"] = "login"

        col_login, col_register = st.columns(2)
        with col_login:
            active = st.session_state["auth_tab"] == "login"
            if st.button("SIGN IN", key="tab_login", use_container_width=True):
                st.session_state["auth_tab"] = "login"
                st.rerun()
        with col_register:
            if st.button("CREATE ACCOUNT", key="tab_register", use_container_width=True):
                st.session_state["auth_tab"] = "register"
                st.rerun()

        # Active indicator
        is_login = st.session_state["auth_tab"] == "login"
        st.markdown(
            f"<div style='display:flex;margin-bottom:24px;'>"
            f"<div style='flex:1;height:2px;background:{''+accent if is_login else border};transition:all 0.3s;'></div>"
            f"<div style='flex:1;height:2px;background:{''+accent if not is_login else border};transition:all 0.3s;'></div>"
            f"</div>",
            unsafe_allow_html=True)

        # Card
        st.markdown(
            f"<div style='background:{card};border:1px solid {border};"
            f"border-radius:12px;padding:32px;margin-bottom:16px;'>",
            unsafe_allow_html=True)

        if is_login:
            # ── Sign In ──────────────────────────────────────────────────
            st.markdown(
                f"<div style='font-family:JetBrains Mono,monospace;font-size:10px;"
                f"color:{muted};letter-spacing:2px;margin-bottom:20px;'>SIGN IN TO YOUR ACCOUNT</div>",
                unsafe_allow_html=True)

            email    = st.text_input("", placeholder="Email address", key="login_email", label_visibility="collapsed")
            password = st.text_input("", placeholder="Password", type="password", key="login_password", label_visibility="collapsed")

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            if st.button("SIGN IN →", key="login_btn", use_container_width=True):
                if not email or not password:
                    st.markdown(f"<div style='color:#f87171;font-family:JetBrains Mono,monospace;font-size:12px;margin-top:8px;'>⚠ Please fill in all fields.</div>", unsafe_allow_html=True)
                else:
                    with st.spinner(""):
                        result = login_user(email, password)
                    if result["success"]:
                        st.session_state["auth_token"]   = result["token"]
                        st.session_state["current_user"] = result["user"]
                        st.rerun()
                    else:
                        st.markdown(f"<div style='color:#f87171;font-family:JetBrains Mono,monospace;font-size:12px;margin-top:8px;'>⚠ {result['error']}</div>", unsafe_allow_html=True)

        else:
            # ── Create Account ────────────────────────────────────────────
            st.markdown(
                f"<div style='font-family:JetBrains Mono,monospace;font-size:10px;"
                f"color:{muted};letter-spacing:2px;margin-bottom:20px;'>CREATE A NEW ACCOUNT</div>",
                unsafe_allow_html=True)

            name     = st.text_input("", placeholder="Full name", key="reg_name", label_visibility="collapsed")
            email    = st.text_input("", placeholder="Email address", key="reg_email", label_visibility="collapsed")
            password = st.text_input("", placeholder="Password (min. 8 characters)", type="password", key="reg_password", label_visibility="collapsed")
            confirm  = st.text_input("", placeholder="Confirm password", type="password", key="reg_confirm", label_visibility="collapsed")

            st.markdown("<div style='height:8px;'></div>", unsafe_allow_html=True)

            if st.button("CREATE ACCOUNT →", key="register_btn", use_container_width=True):
                if not all([name, email, password, confirm]):
                    st.markdown(f"<div style='color:#f87171;font-family:JetBrains Mono,monospace;font-size:12px;margin-top:8px;'>⚠ Please fill in all fields.</div>", unsafe_allow_html=True)
                elif password != confirm:
                    st.markdown(f"<div style='color:#f87171;font-family:JetBrains Mono,monospace;font-size:12px;margin-top:8px;'>⚠ Passwords do not match.</div>", unsafe_allow_html=True)
                else:
                    with st.spinner(""):
                        result = register_user(name, email, password)
                    if result["success"]:
                        st.markdown(f"<div style='color:#4ade80;font-family:JetBrains Mono,monospace;font-size:12px;margin-top:8px;'>✓ {result['message']} Please sign in.</div>", unsafe_allow_html=True)
                        st.session_state["auth_tab"] = "login"
                        import time; time.sleep(1.5)
                        st.rerun()
                    else:
                        st.markdown(f"<div style='color:#f87171;font-family:JetBrains Mono,monospace;font-size:12px;margin-top:8px;'>⚠ {result['error']}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        # Password hint
        if not is_login:
            st.markdown(
                f"<div style='font-family:JetBrains Mono,monospace;font-size:10px;"
                f"color:{muted};text-align:center;line-height:1.6;'>"
                f"Passwords are encrypted with bcrypt.<br>"
                f"We never store plain-text credentials.</div>",
                unsafe_allow_html=True)

        # Theme toggle
        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)
        col_d, col_l = st.columns(2)
        with col_d:
            if st.button("DARK", key="login_dark", use_container_width=True):
                st.session_state["theme"] = "dark"
                st.rerun()
        with col_l:
            if st.button("LIGHT", key="login_light", use_container_width=True):
                st.session_state["theme"] = "light"
                st.rerun()

    return False
