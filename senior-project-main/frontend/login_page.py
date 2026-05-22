"""
Login page for VerifAI.
Save to: frontend/login_page.py
"""
import streamlit as st
import sys, os, base64
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_logo_b64():
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(logo_path):
        with open(logo_path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    return ""

def render_login_css():
    theme = st.session_state.get("theme", "dark")
    if theme == "light":
        bg       = "#f0f6ff"
        card     = "#ffffff"
        text     = "#0f172a"
        muted    = "#64748b"
        border   = "#cbd5e1"
        accent   = "#0284c7"
        input_bg = "#f8fafc"
        ph_color = "#94a3b8"
        cursor_c = "#0284c7"
    else:
        bg       = "#080f17"
        card     = "#111f2e"
        text     = "#f1f8ff"
        muted    = "#4a7090"
        border   = "#1e3448"
        accent   = "#38bdf8"
        input_bg = "#0a1628"
        ph_color = "#2a5070"
        cursor_c = "#38bdf8"

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
    background-color: {bg} !important;
}}
.stApp, [data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"] {{
    background-color: {bg} !important;
}}
#MainMenu, footer, header {{ visibility: hidden !important; }}
[data-testid="stDecoration"] {{ display: none !important; }}
[data-testid="stTextInput"] input {{
    background-color: {input_bg} !important;
    border: 1px solid {border} !important;
    border-radius: 6px !important;
    color: {text} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 14px !important;
    padding: 12px 16px !important;
    caret-color: {cursor_c} !important;
}}
[data-testid="stTextInput"] input::placeholder {{
    color: {ph_color} !important;
    opacity: 1 !important;
}}
[data-testid="stTextInput"] input::-webkit-input-placeholder {{
    color: {ph_color} !important;
    opacity: 1 !important;
}}
[data-testid="stTextInput"] input::-moz-placeholder {{
    color: {ph_color} !important;
    opacity: 1 !important;
}}
[data-testid="stTextInput"] input:-ms-input-placeholder {{
    color: {ph_color} !important;
    opacity: 1 !important;
}}
[data-testid="stTextInput"] input:focus {{
    border-color: {accent} !important;
    box-shadow: 0 0 0 3px {accent}20 !important;
    outline: none !important;
}}
[data-testid="stTextInput"] button {{
    color: {muted} !important;
    background: transparent !important;
    border: none !important;
}}
[data-testid="stButton"] button {{
    background: transparent !important;
    border: 1px solid {accent} !important;
    color: {accent} !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    letter-spacing: 2px !important;
    border-radius: 4px !important;
    padding: 10px 0 !important;
    transition: all 0.2s !important;
}}
[data-testid="stButton"] button:hover {{
    background: {accent}15 !important;
    box-shadow: 0 0 16px {accent}25 !important;
}}
</style>
""", unsafe_allow_html=True)


def render_cybersec_bg():
    theme = st.session_state.get("theme", "dark")
    if theme == "light":
        return
    st.markdown("""
<style>
#cyberbg {
    position: fixed; top: 0; left: 0;
    width: 100vw; height: 100vh;
    pointer-events: none; z-index: 0; overflow: hidden;
}
#matrix-canvas { position: absolute; top: 0; left: 0; opacity: 0.13; }
#particle-canvas { position: absolute; top: 0; left: 0; }
.scan-line {
    position: absolute; left: 0; top: 0; width: 100%; height: 2px;
    background: rgba(56,189,248,0.06);
    animation: scandown 5s linear infinite;
}
@keyframes scandown { 0% { top: 0; } 100% { top: 100vh; } }
.corner-tl {
    position: fixed; top: 18px; left: 18px;
    width: 22px; height: 22px;
    border-top: 1px solid rgba(56,189,248,0.3);
    border-left: 1px solid rgba(56,189,248,0.3);
    pointer-events: none; z-index: 1;
}
.corner-br {
    position: fixed; bottom: 18px; right: 18px;
    width: 22px; height: 22px;
    border-bottom: 1px solid rgba(56,189,248,0.3);
    border-right: 1px solid rgba(56,189,248,0.3);
    pointer-events: none; z-index: 1;
}
</style>
<div id="cyberbg">
    <canvas id="matrix-canvas"></canvas>
    <canvas id="particle-canvas"></canvas>
    <div class="scan-line"></div>
</div>
<div class="corner-tl"></div>
<div class="corner-br"></div>
<script>
(function() {
    function init() {
        const W = window.innerWidth, H = window.innerHeight;
        const mc = document.getElementById('matrix-canvas');
        mc.width = W; mc.height = H;
        const mx = mc.getContext('2d');
        const cols = Math.floor(W / 16);
        const drops = Array(cols).fill(1);
        const chars = '01アイウエABCDEF><{}[]#$@!';
        function drawMatrix() {
            mx.fillStyle = 'rgba(8,15,23,0.06)';
            mx.fillRect(0, 0, W, H);
            mx.font = '13px JetBrains Mono, monospace';
            drops.forEach((y, i) => {
                const c = chars[Math.floor(Math.random() * chars.length)];
                mx.globalAlpha = Math.random() * 0.5 + 0.1;
                mx.fillStyle = '#38bdf8';
                mx.fillText(c, i * 16, y * 16);
                if (y * 16 > H && Math.random() > 0.975) drops[i] = 0;
                drops[i]++;
            });
            mx.globalAlpha = 1;
        }
        const pc = document.getElementById('particle-canvas');
        pc.width = W; pc.height = H;
        const pctx = pc.getContext('2d');
        const pts = Array.from({ length: 28 }, () => ({
            x: Math.random() * W, y: Math.random() * H,
            vx: (Math.random() - 0.5) * 0.45,
            vy: (Math.random() - 0.5) * 0.45,
            r: Math.random() * 1.8 + 0.8
        }));
        function drawParticles() {
            pctx.clearRect(0, 0, W, H);
            pts.forEach(p => {
                p.x += p.vx; p.y += p.vy;
                if (p.x < 0 || p.x > W) p.vx *= -1;
                if (p.y < 0 || p.y > H) p.vy *= -1;
                pctx.beginPath();
                pctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                pctx.fillStyle = 'rgba(56,189,248,0.35)';
                pctx.fill();
            });
            pts.forEach((p, i) => {
                pts.slice(i + 1).forEach(q => {
                    const dx = p.x - q.x, dy = p.y - q.y;
                    const dist = Math.sqrt(dx * dx + dy * dy);
                    if (dist < 125) {
                        pctx.beginPath();
                        pctx.moveTo(p.x, p.y); pctx.lineTo(q.x, q.y);
                        pctx.strokeStyle = 'rgba(56,189,248,' + (0.15 * (1 - dist / 125)) + ')';
                        pctx.lineWidth = 0.5; pctx.stroke();
                    }
                });
            });
        }
        function loop() { drawMatrix(); drawParticles(); requestAnimationFrame(loop); }
        loop();
    }
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else { init(); }
})();
</script>
""", unsafe_allow_html=True)


def render_login_page() -> bool:
    from backend.auth.auth_manager import login_user, register_user, validate_session

    token = st.session_state.get("auth_token")
    if token:
        user = validate_session(token)
        if user:
            st.session_state["current_user"] = user
            return True

    render_login_css()
    render_cybersec_bg()

    theme = st.session_state.get("theme", "dark")
    if theme == "light":
        bg, card, text, muted, border, accent = "#f0f6ff", "#ffffff", "#0f172a", "#64748b", "#cbd5e1", "#0284c7"
    else:
        bg, card, text, muted, border, accent = "#080f17", "#111f2e", "#f1f8ff", "#4a7090", "#1e3448", "#38bdf8"

    logo_b64 = get_logo_b64()

    _, center, _ = st.columns([1, 1.2, 1])
    with center:
        st.markdown("<div style='height:48px;'></div>", unsafe_allow_html=True)

        logo_html = (
            f"<img src='data:image/png;base64,{logo_b64}' "
            f"style='width:90px;height:90px;object-fit:contain;"
            f"display:block;margin:0 auto 12px auto;' />"
        ) if logo_b64 else ""

        st.markdown(
            f"<div style='text-align:center;margin-bottom:28px;position:relative;z-index:2;'>"
            f"{logo_html}"
            f"<div style='font-family:JetBrains Mono,monospace;font-size:30px;font-weight:700;"
            f"color:{accent};letter-spacing:6px;'>VERIFAI</div>"
            f"<div style='font-family:JetBrains Mono,monospace;font-size:9px;"
            f"color:{muted};letter-spacing:4px;margin-top:6px;'>DIGITAL TRUST PLATFORM</div>"
            f"</div>",
            unsafe_allow_html=True)

        if "auth_tab" not in st.session_state:
            st.session_state["auth_tab"] = "login"

        col_login, col_register = st.columns(2)
        with col_login:
            if st.button("SIGN IN", key="tab_login", use_container_width=True):
                st.session_state["auth_tab"] = "login"
                st.rerun()
        with col_register:
            if st.button("CREATE ACCOUNT", key="tab_register", use_container_width=True):
                st.session_state["auth_tab"] = "register"
                st.rerun()

        is_login = st.session_state["auth_tab"] == "login"
        st.markdown(
            f"<div style='display:flex;margin-bottom:20px;'>"
            f"<div style='flex:1;height:2px;background:{accent if is_login else border};'></div>"
            f"<div style='flex:1;height:2px;background:{accent if not is_login else border};'></div>"
            f"</div>",
            unsafe_allow_html=True)

        st.markdown(
            f"<div style='background:{card};border:1px solid {border};"
            f"border-radius:10px;padding:28px 28px 24px;margin-bottom:14px;"
            f"position:relative;z-index:2;'>",
            unsafe_allow_html=True)

        if is_login:
            st.markdown(
                f"<div style='font-family:JetBrains Mono,monospace;font-size:9px;"
                f"color:{muted};letter-spacing:2px;margin-bottom:18px;'>SIGN IN TO YOUR ACCOUNT</div>",
                unsafe_allow_html=True)
            email    = st.text_input("", placeholder="Email address", key="login_email",    label_visibility="collapsed")
            password = st.text_input("", placeholder="Password",      key="login_password", label_visibility="collapsed", type="password")
            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            if st.button("SIGN IN →", key="login_btn", use_container_width=True):
                if not email or not password:
                    st.markdown(f"<div style='color:#f87171;font-family:JetBrains Mono,monospace;font-size:11px;margin-top:8px;'>Please fill in all fields.</div>", unsafe_allow_html=True)
                else:
                    with st.spinner(""):
                        result = login_user(email, password)
                    if result["success"]:
                        st.session_state["auth_token"]   = result["token"]
                        st.session_state["current_user"] = result["user"]
                        st.rerun()
                    else:
                        st.markdown(f"<div style='color:#f87171;font-family:JetBrains Mono,monospace;font-size:11px;margin-top:8px;'>{result['error']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(
                f"<div style='font-family:JetBrains Mono,monospace;font-size:9px;"
                f"color:{muted};letter-spacing:2px;margin-bottom:18px;'>CREATE A NEW ACCOUNT</div>",
                unsafe_allow_html=True)
            name     = st.text_input("", placeholder="Full name",              key="reg_name",     label_visibility="collapsed")
            email    = st.text_input("", placeholder="Email address",           key="reg_email",    label_visibility="collapsed")
            password = st.text_input("", placeholder="Password (min 8 chars)",  key="reg_password", label_visibility="collapsed", type="password")
            confirm  = st.text_input("", placeholder="Confirm password",        key="reg_confirm",  label_visibility="collapsed", type="password")
            st.markdown("<div style='height:6px;'></div>", unsafe_allow_html=True)
            if st.button("CREATE ACCOUNT →", key="register_btn", use_container_width=True):
                if not all([name, email, password, confirm]):
                    st.markdown(f"<div style='color:#f87171;font-family:JetBrains Mono,monospace;font-size:11px;margin-top:8px;'>Please fill in all fields.</div>", unsafe_allow_html=True)
                elif password != confirm:
                    st.markdown(f"<div style='color:#f87171;font-family:JetBrains Mono,monospace;font-size:11px;margin-top:8px;'>Passwords do not match.</div>", unsafe_allow_html=True)
                elif len(password) < 8:
                    st.markdown(f"<div style='color:#f87171;font-family:JetBrains Mono,monospace;font-size:11px;margin-top:8px;'>Password must be at least 8 characters.</div>", unsafe_allow_html=True)
                else:
                    with st.spinner(""):
                        result = register_user(name, email, password)
                    if result["success"]:
                        st.markdown(f"<div style='color:#4ade80;font-family:JetBrains Mono,monospace;font-size:11px;margin-top:8px;'>Account created! Please sign in.</div>", unsafe_allow_html=True)
                        st.session_state["auth_tab"] = "login"
                        import time; time.sleep(1.2)
                        st.rerun()
                    else:
                        st.markdown(f"<div style='color:#f87171;font-family:JetBrains Mono,monospace;font-size:11px;margin-top:8px;'>{result['error']}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown(
            f"<div style='font-family:JetBrains Mono,monospace;font-size:9px;"
            f"color:{muted};text-align:center;line-height:1.8;margin-bottom:16px;"
            f"position:relative;z-index:2;'>"
            f"Passwords encrypted with bcrypt &nbsp;·&nbsp; Sessions last 30 days</div>",
            unsafe_allow_html=True)

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
