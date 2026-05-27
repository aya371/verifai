"""
VerifAI Login Page — All 4 fixes applied:
  FIX 1: After register → auto sign-in (no redirect needed)
  FIX 2: Forgot password flow with reset form
  FIX 3: Password strength: 8 chars + 1 uppercase + 1 special
  FIX 4: Login notification email sent on successful sign-in
Save to: frontend/login_page.py
"""
import streamlit as st
import streamlit.components.v1 as components
import sys, os, base64, re, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ── Email config — set these in your .env ─────────────────────────────
SMTP_HOST     = os.getenv("SMTP_HOST",     "smtp.gmail.com")
SMTP_PORT     = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER     = os.getenv("SMTP_USER",     "")   # your Gmail address
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")   # Gmail app password
FROM_NAME     = "VerifAI Security"


def _send_login_email(to_email: str, user_name: str):
    """Send a login notification email. Silent fail if SMTP not configured."""
    if not SMTP_USER or not SMTP_PASSWORD:
        return
    try:
        now = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "VerifAI — New Login Detected"
        msg["From"]    = f"{FROM_NAME} <{SMTP_USER}>"
        msg["To"]      = to_email

        html = f"""
        <div style="font-family:Arial,sans-serif;max-width:480px;margin:0 auto;
                    background:#07101d;color:#e2e8f0;padding:32px;border-radius:12px;">
          <h2 style="color:#60a5fa;margin-bottom:4px;">VerifAI</h2>
          <p style="color:#94a3b8;font-size:13px;margin-bottom:24px;">
              Digital Trust Verification Platform</p>
          <p>Hi <strong>{user_name}</strong>,</p>
          <p>A new login to your VerifAI account was detected:</p>
          <div style="background:#0f1f38;border-radius:8px;padding:16px;margin:16px 0;">
            <p style="margin:0;font-size:13px;">
              🕐 <strong>Time:</strong> {now}<br>
              📧 <strong>Account:</strong> {to_email}
            </p>
          </div>
          <p style="font-size:13px;color:#94a3b8;">
            If this wasn't you, please reset your password immediately.</p>
          <hr style="border-color:#1e3a5f;margin:24px 0;">
          <p style="font-size:11px;color:#475569;">
              This is an automated security notification from VerifAI.</p>
        </div>"""

        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, to_email, msg.as_string())
    except Exception:
        pass  # Silent fail — login still succeeds even if email fails


def _password_hint():
    st.markdown(
        "<div style='font-size:11px;color:rgba(148,163,184,0.55);"
        "margin-top:4px;font-family:Inter,sans-serif;'>"
        "Min. 8 characters · 1 uppercase letter · 1 special character"
        "</div>",
        unsafe_allow_html=True)


def _validate_password_ui(password: str) -> Optional[str]:
    """Client-side password check matching auth_manager rules."""
    if len(password) < 8:
        return "Password must be at least 8 characters."
    if not re.search(r"[A-Z]", password):
        return "Password must contain at least one uppercase letter."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-\+=/\\]", password):
        return "Password must contain at least one special character."
    return None


def _logo_b64() -> str:
    for p in [
        os.path.join(os.path.dirname(__file__), "assets", "logo.png"),
        r"C:\Users\aya\Pictures\logo.png",
        r"C:\Users\User\Pictures\logo.png",
    ]:
        if os.path.exists(p):
            with open(p, "rb") as f:
                return base64.b64encode(f.read()).decode()
    return ""


def render_login_page() -> bool:
    from backend.auth.auth_manager import (
        login_user, register_user, validate_session, reset_password
    )

    # ── Already logged in? ─────────────────────────────────────────────
    if st.session_state.get("auth_token"):
        user = validate_session(st.session_state["auth_token"])
        if user:
            st.session_state["current_user"] = user
            return True

    # ── Session state init ─────────────────────────────────────────────
    for k, v in [
        ("login_tab",   "signin"),
        ("login_error", ""),
        ("login_ok",    ""),
        ("forgot_mode", False),
        ("reset_sent",  False),
    ]:
        if k not in st.session_state:
            st.session_state[k] = v

    mode  = st.session_state["login_tab"]
    logo  = _logo_b64()
    logo_src = f"data:image/png;base64,{logo}" if logo else ""
    logo_img = (
        f'<img src="{logo_src}" style="width:150px;height:auto;" alt="VerifAI">'
        if logo_src else
        '<div style="width:140px;height:140px;border-radius:50%;'
        'background:linear-gradient(135deg,#1d4ed8,#4f46e5);'
        'display:flex;align-items:center;justify-content:center;'
        'font-size:56px;">🛡️</div>'
    )

    # ── Global CSS (unchanged from original) ──────────────────────────
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
[data-testid="stDecoration"],[data-testid="stToolbar"],[data-testid="stStatusWidget"],
[data-testid="stSidebarCollapsedControl"],[data-testid="stBottom"],
#MainMenu,footer,header{display:none!important;}
html,body,.stApp,[data-testid="stAppViewContainer"],[data-testid="stAppViewBlockContainer"]{
    background:#07101d!important;overflow:hidden!important;height:100vh!important;}
.main,section.main{background:#07101d!important;overflow:hidden!important;
    height:100vh!important;padding:0!important;}
.main .block-container{padding:0!important;max-width:100%!important;
    height:100vh!important;overflow:hidden!important;}
[data-testid="stTextInput"] label{font-size:11px!important;font-weight:700!important;
    color:rgba(148,163,184,0.82)!important;letter-spacing:1px!important;
    text-transform:uppercase!important;font-family:'Inter',sans-serif!important;}
[data-testid="stTextInput"]>div>div{background:rgba(10,20,45,0.88)!important;
    border:1.5px solid rgba(255,255,255,0.10)!important;border-radius:11px!important;
    box-shadow:none!important;transition:all 0.2s!important;}
[data-testid="stTextInput"]>div>div:focus-within{
    border-color:rgba(59,130,246,0.60)!important;
    background:rgba(10,20,55,0.95)!important;
    box-shadow:0 0 0 3px rgba(59,130,246,0.13)!important;}
[data-testid="stTextInput"] input{background:transparent!important;color:#ffffff!important;
    font-size:14px!important;font-family:'Inter',sans-serif!important;
    -webkit-text-fill-color:#ffffff!important;caret-color:#3b82f6!important;}
[data-testid="stTextInput"] input::placeholder{color:rgba(148,163,184,0.42)!important;
    -webkit-text-fill-color:rgba(148,163,184,0.42)!important;}
[data-testid="column"] [data-testid="stButton"]>button{
    background:rgba(255,255,255,0.04)!important;
    border:1.5px solid rgba(255,255,255,0.09)!important;color:#64748b!important;
    font-size:13px!important;font-weight:600!important;padding:9px 0!important;
    border-radius:10px!important;font-family:'Inter',sans-serif!important;
    box-shadow:none!important;transform:none!important;transition:all 0.18s!important;}
[data-testid="column"] [data-testid="stButton"]>button:hover{
    background:rgba(255,255,255,0.08)!important;color:#94a3b8!important;}
.vf-active [data-testid="stButton"]>button{
    background:rgba(59,130,246,0.15)!important;
    border-color:rgba(59,130,246,0.38)!important;color:#93c5fd!important;}
.vf-go [data-testid="stButton"]>button{
    background:linear-gradient(135deg,#2563eb,#4f46e5)!important;
    border:none!important;color:#ffffff!important;font-size:15px!important;
    font-weight:700!important;padding:13px 0!important;border-radius:11px!important;
    font-family:'Inter',sans-serif!important;
    box-shadow:0 4px 18px rgba(37,99,235,0.40)!important;transition:all 0.2s ease!important;}
.vf-go [data-testid="stButton"]>button:hover{
    filter:brightness(1.10)!important;
    box-shadow:0 6px 26px rgba(37,99,235,0.58)!important;
    transform:translateY(-1px)!important;}
.vf-link [data-testid="stButton"]>button{
    background:transparent!important;border:none!important;
    color:#3b82f6!important;font-size:12px!important;font-weight:600!important;
    padding:2px 0!important;box-shadow:none!important;transform:none!important;}
.vf-link [data-testid="stButton"]>button:hover{color:#60a5fa!important;}
[data-testid="column"]:last-child{background:#07101d!important;}
</style>
""", unsafe_allow_html=True)

    left, right = st.columns([1.1, 0.9], gap="small")

    # ── LEFT animated panel (unchanged) ───────────────────────────────
    with left:
        components.html(f"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{width:100%;height:100vh;overflow:hidden;background:#07101d;font-family:'Inter',sans-serif;}}
#c{{position:fixed;inset:0;z-index:0;}}
.scene{{position:relative;z-index:2;height:100vh;display:flex;flex-direction:column;justify-content:center;align-items:center;padding:32px 40px;text-align:center;}}
.logo-stage{{position:relative;display:inline-block;margin-bottom:28px;transform-style:preserve-3d;animation:logo3d 9s ease-in-out infinite;}}
.halo{{position:absolute;width:340px;height:340px;border-radius:50%;background:radial-gradient(circle,rgba(124,58,237,0.15) 0%,transparent 65%);top:50%;left:50%;transform:translate(-50%,-50%);filter:blur(36px);animation:breathe 7s ease-in-out infinite reverse;}}
.glow{{position:absolute;width:250px;height:250px;border-radius:50%;background:radial-gradient(circle,rgba(59,130,246,0.44) 0%,rgba(99,102,241,0.16) 45%,transparent 70%);top:50%;left:50%;transform:translate(-50%,-50%);filter:blur(24px);animation:breathe 4.5s ease-in-out infinite;}}
.ring{{position:absolute;border-radius:50%;top:50%;left:50%;border-style:solid;}}
.r1{{width:185px;height:185px;border-width:1.5px;border-color:rgba(59,130,246,0.38);transform:translate(-50%,-50%) rotateX(68deg);animation:orbit1 14s linear infinite;}}
.r2{{width:230px;height:230px;border-width:1px;border-color:rgba(124,58,237,0.24);transform:translate(-50%,-50%) rotateX(68deg) rotateZ(55deg);animation:orbit2 22s linear infinite;}}
.r3{{width:276px;height:276px;border-width:1px;border-style:dashed;border-color:rgba(59,130,246,0.10);transform:translate(-50%,-50%) rotateX(68deg) rotateZ(110deg);animation:orbit3 34s linear infinite;}}
.orb-dot{{position:absolute;width:9px;height:9px;border-radius:50%;background:#60a5fa;box-shadow:0 0 16px 5px rgba(96,165,250,0.85);top:calc(50% - 4.5px);left:-4.5px;}}
.logo-img{{position:relative;z-index:4;animation:wobble 9s ease-in-out infinite;filter:drop-shadow(0 0 28px rgba(59,130,246,0.68)) drop-shadow(0 0 64px rgba(99,102,241,0.34));padding:8px;}}
.logo-img img{{width:150px;height:auto;display:block;}}
.brand-title{{font-family:'Space Grotesk',sans-serif;font-size:52px;font-weight:800;line-height:1;letter-spacing:-2px;background:linear-gradient(120deg,#ffffff 0%,#bfdbfe 25%,#a78bfa 55%,#93c5fd 80%,#ffffff 100%);background-size:300% auto;-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;animation:shine 8s linear infinite;margin-bottom:7px;}}
.brand-sub{{font-size:10px;font-weight:700;letter-spacing:6px;text-transform:uppercase;color:rgba(148,163,184,0.34);margin-bottom:13px;}}
.divline{{height:1.5px;width:0;margin:0 auto 18px;background:linear-gradient(90deg,transparent,#3b82f6,#7c3aed,transparent);border-radius:2px;animation:drawline 1.6s cubic-bezier(0.22,1,0.36,1) 0.3s forwards;}}
.brand-desc{{font-size:13px;color:rgba(148,163,184,0.48);line-height:1.8;animation:fadeup 0.9s ease 0.7s both;}}
.status{{display:flex;align-items:center;justify-content:center;gap:7px;margin-top:20px;font-size:10px;color:rgba(100,116,139,0.36);animation:fadeup 0.6s ease 1.0s both;}}
.sdot{{width:6px;height:6px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px #22c55e;animation:blink 2.5s ease infinite;}}
@keyframes logo3d{{0%{{transform:translateY(0) rotateY(-5deg) rotateX(3deg) scale(1);}}25%{{transform:translateY(-10px) rotateY(2deg) rotateX(-2deg) scale(1.02);}}50%{{transform:translateY(-15px) rotateY(6deg) rotateX(3deg) scale(1.03);}}75%{{transform:translateY(-7px) rotateY(-2deg) rotateX(0) scale(1.01);}}100%{{transform:translateY(0) rotateY(-5deg) rotateX(3deg) scale(1);}}}}
@keyframes wobble{{0%,100%{{transform:rotate(-1.5deg) scale(1);}}50%{{transform:rotate(1.5deg) scale(1.05);}}}}
@keyframes breathe{{0%,100%{{opacity:.7;transform:translate(-50%,-50%) scale(1);}}50%{{opacity:1;transform:translate(-50%,-50%) scale(1.15);}}}}
@keyframes orbit1{{from{{transform:translate(-50%,-50%) rotateX(68deg) rotateZ(0deg);}}to{{transform:translate(-50%,-50%) rotateX(68deg) rotateZ(360deg);}}}}
@keyframes orbit2{{from{{transform:translate(-50%,-50%) rotateX(68deg) rotateZ(55deg);}}to{{transform:translate(-50%,-50%) rotateX(68deg) rotateZ(415deg);}}}}
@keyframes orbit3{{from{{transform:translate(-50%,-50%) rotateX(68deg) rotateZ(110deg);}}to{{transform:translate(-50%,-50%) rotateX(68deg) rotateZ(-250deg);}}}}
@keyframes shine{{0%{{background-position:-200% center;}}100%{{background-position:200% center;}}}}
@keyframes drawline{{from{{width:0;}}to{{width:70%;}}}}
@keyframes fadeup{{from{{opacity:0;transform:translateY(10px);}}to{{opacity:1;transform:translateY(0);}}}}
@keyframes blink{{0%,100%{{opacity:1;}}50%{{opacity:.2;}}}}
</style></head><body>
<canvas id="c"></canvas>
<div class="scene">
  <div class="logo-stage">
    <div class="halo"></div><div class="glow"></div>
    <div class="ring r1"><div class="orb-dot"></div></div>
    <div class="ring r2"></div><div class="ring r3"></div>
    <div class="logo-img">{logo_img}</div>
  </div>
  <div class="brand-title">VERIFAI</div>
  <div class="brand-sub">Digital Trust Verification</div>
  <div class="divline"></div>
  <div class="brand-desc">AI-powered platform for identity verification,<br>fact-checking &amp; content analysis.</div>
  <div class="status"><div class="sdot"></div>All systems operational</div>
</div>
<script>
var cv=document.getElementById('c'),ctx=cv.getContext('2d');
function resize(){{cv.width=window.innerWidth;cv.height=window.innerHeight;}}
resize();window.addEventListener('resize',resize);
var stars=Array.from({{length:120}},function(){{return{{x:Math.random()*2000,y:Math.random()*1200,r:Math.random()*1.3+0.3,a:Math.random(),da:(Math.random()-0.5)*0.004,dx:(Math.random()-0.5)*0.08,dy:-Math.random()*0.18-0.03}};}});
var orbs=[{{x:0.18,y:0.25,r:0.28,c:'rgba(37,99,235,0.11)',s:0.00014}},{{x:0.80,y:0.70,r:0.22,c:'rgba(124,58,237,0.08)',s:0.00017}},{{x:0.50,y:0.05,r:0.18,c:'rgba(16,185,129,0.06)',s:0.00011}}];
var t=0;
function draw(){{
    ctx.clearRect(0,0,cv.width,cv.height);
    ctx.fillStyle='#07101d';ctx.fillRect(0,0,cv.width,cv.height);
    orbs.forEach(function(o){{var cx=(o.x+Math.sin(t*o.s*1000)*0.055)*cv.width,cy=(o.y+Math.cos(t*o.s*800)*0.045)*cv.height,rad=o.r*Math.min(cv.width,cv.height),g=ctx.createRadialGradient(cx,cy,0,cx,cy,rad);g.addColorStop(0,o.c);g.addColorStop(1,'transparent');ctx.fillStyle=g;ctx.beginPath();ctx.arc(cx,cy,rad,0,Math.PI*2);ctx.fill();}});
    stars.forEach(function(s){{s.x+=s.dx;s.y+=s.dy;s.a+=s.da;if(s.a<0)s.da=Math.abs(s.da);if(s.a>1)s.da=-Math.abs(s.da);if(s.y<-5)s.y=cv.height+5;if(s.x<-5)s.x=cv.width+5;if(s.x>cv.width+5)s.x=-5;if(s.r>1.2&&s.a>0.7){{ctx.strokeStyle='rgba(148,163,184,'+(s.a*0.35).toFixed(2)+')';ctx.lineWidth=0.5;ctx.beginPath();ctx.moveTo(s.x-s.r*2.5,s.y);ctx.lineTo(s.x+s.r*2.5,s.y);ctx.stroke();ctx.beginPath();ctx.moveTo(s.x,s.y-s.r*2.5);ctx.lineTo(s.x,s.y+s.r*2.5);ctx.stroke();}}ctx.beginPath();ctx.arc(s.x,s.y,s.r,0,Math.PI*2);ctx.fillStyle='rgba(148,163,184,'+(s.a*0.48).toFixed(2)+')';ctx.fill();}});
    t++;requestAnimationFrame(draw);
}}
draw();
</script>
</body></html>
""", height=750, scrolling=False)

    # ── RIGHT: Form ────────────────────────────────────────────────────
    with right:
        st.markdown("<div style='height:8vh'></div>", unsafe_allow_html=True)
        st.markdown("""
<div style="background:rgba(12,22,40,0.0);max-width:380px;margin:0 auto;
  font-family:'Inter',sans-serif;">
""", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════
        # FIX 2 — FORGOT PASSWORD FLOW
        # ══════════════════════════════════════════════════════════════
        if st.session_state.get("forgot_mode"):
            st.markdown("""
<div style="margin-bottom:20px;">
  <div style="font-size:24px;font-weight:700;color:#f1f5f9;letter-spacing:-0.4px;margin-bottom:3px;">
    Reset Password 🔑</div>
  <div style="font-size:13px;color:rgba(148,163,184,0.58);line-height:1.5;">
    Enter your email and choose a new password.</div>
</div>""", unsafe_allow_html=True)

            fp_email    = st.text_input("Email Address",
                                         placeholder="you@example.com", key="fp_email")
            fp_pass     = st.text_input("New Password",
                                         placeholder="Min 8 chars · 1 uppercase · 1 special",
                                         type="password", key="fp_pass")
            fp_confirm  = st.text_input("Confirm New Password",
                                         placeholder="Repeat new password",
                                         type="password", key="fp_confirm")
            _password_hint()
            st.write("")

            col_back, col_reset = st.columns(2, gap="small")
            with col_back:
                if st.button("← Back", key="fp_back", use_container_width=True):
                    st.session_state["forgot_mode"]  = False
                    st.session_state["login_error"]  = ""
                    st.session_state["reset_sent"]   = False
                    st.rerun()
            with col_reset:
                st.markdown('<div class="vf-go">', unsafe_allow_html=True)
                if st.button("Reset Password", key="fp_go", use_container_width=True):
                    if not fp_email.strip() or not fp_pass or not fp_confirm:
                        st.session_state["login_error"] = "All fields are required."
                        st.rerun()
                    elif fp_pass != fp_confirm:
                        st.session_state["login_error"] = "Passwords do not match."
                        st.rerun()
                    else:
                        pw_err = _validate_password_ui(fp_pass)
                        if pw_err:
                            st.session_state["login_error"] = pw_err
                            st.rerun()
                        else:
                            r = reset_password(fp_email.strip(), fp_pass)
                            if r.get("success"):
                                st.session_state["forgot_mode"]  = False
                                st.session_state["login_tab"]    = "signin"
                                st.session_state["login_ok"]     = "Password reset — please sign in."
                                st.session_state["login_error"]  = ""
                                st.rerun()
                            else:
                                st.session_state["login_error"] = r.get("error", "Reset failed.")
                                st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            if st.session_state.get("login_error"):
                st.markdown(
                    f"<div style='background:rgba(239,68,68,0.10);border:1px solid rgba(239,68,68,0.28);"
                    f"border-radius:10px;padding:10px 14px;color:#fca5a5;font-size:13px;"
                    f"font-weight:500;margin-top:8px;font-family:Inter,sans-serif;'>"
                    f"⚠️&nbsp; {st.session_state['login_error']}</div>",
                    unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════
        # NORMAL SIGN IN / REGISTER
        # ══════════════════════════════════════════════════════════════
        else:
            # Heading
            if mode == "signin":
                st.markdown("""
<div style="margin-bottom:20px;">
  <div style="font-size:24px;font-weight:700;color:#f1f5f9;letter-spacing:-0.4px;margin-bottom:3px;">
    Welcome back 👋</div>
  <div style="font-size:13px;color:rgba(148,163,184,0.58);line-height:1.5;">
    Sign in to your VerifAI account to continue.</div>
</div>""", unsafe_allow_html=True)
            else:
                st.markdown("""
<div style="margin-bottom:20px;">
  <div style="font-size:24px;font-weight:700;color:#f1f5f9;letter-spacing:-0.4px;margin-bottom:3px;">
    Create account ✨</div>
  <div style="font-size:13px;color:rgba(148,163,184,0.58);line-height:1.5;">
    Join VerifAI — start verifying today.</div>
</div>""", unsafe_allow_html=True)

            # Tabs
            c1, c2 = st.columns(2, gap="small")
            with c1:
                st.markdown('<div class="vf-active">' if mode=="signin" else "<div>",
                            unsafe_allow_html=True)
                if st.button("Sign In", key="t_si", use_container_width=True):
                    st.session_state["login_tab"]   = "signin"
                    st.session_state["login_error"] = ""
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
            with c2:
                st.markdown('<div class="vf-active">' if mode=="register" else "<div>",
                            unsafe_allow_html=True)
                if st.button("Register", key="t_re", use_container_width=True):
                    st.session_state["login_tab"]   = "register"
                    st.session_state["login_error"] = ""
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

            st.write("")

            # ── SIGN IN ───────────────────────────────────────────────
            if mode == "signin":
                email_si = st.text_input("Email Address",
                                          placeholder="you@example.com", key="si_u")
                password_si = st.text_input("Password",
                                             placeholder="Your password",
                                             type="password", key="si_p")
                st.write("")
                st.markdown('<div class="vf-go">', unsafe_allow_html=True)
                go = st.button("Sign in to VerifAI →", key="btn_si",
                               use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

                # FIX 2 — Forgot password link
                st.markdown('<div class="vf-link" style="text-align:right;margin-top:6px;">',
                            unsafe_allow_html=True)
                if st.button("Forgot password?", key="btn_forgot"):
                    st.session_state["forgot_mode"]  = True
                    st.session_state["login_error"]  = ""
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)

                if go:
                    if not email_si.strip() or not password_si:
                        st.session_state["login_error"] = "Please enter your email and password."
                        st.rerun()
                    else:
                        with st.spinner("Verifying credentials…"):
                            r = login_user(email_si.strip(), password_si)
                        if r.get("success"):
                            st.session_state["auth_token"]   = r["token"]
                            st.session_state["current_user"] = r["user"]
                            st.session_state["login_error"]  = ""
                            # FIX 4 — Send login notification email
                            _send_login_email(r["user"]["email"], r["user"]["name"])
                            st.rerun()
                        else:
                            st.session_state["login_error"] = r.get("error", "Incorrect credentials.")
                            st.rerun()

                if st.session_state.get("login_error"):
                    st.markdown(
                        f"<div style='background:rgba(239,68,68,0.10);border:1px solid rgba(239,68,68,0.28);"
                        f"border-radius:10px;padding:10px 14px;color:#fca5a5;font-size:13px;"
                        f"font-weight:500;margin-top:8px;font-family:Inter,sans-serif;'>"
                        f"⚠️&nbsp; {st.session_state['login_error']}</div>",
                        unsafe_allow_html=True)
                if st.session_state.get("login_ok"):
                    st.markdown(
                        f"<div style='background:rgba(34,197,94,0.10);border:1px solid rgba(34,197,94,0.28);"
                        f"border-radius:10px;padding:10px 14px;color:#86efac;font-size:13px;"
                        f"font-weight:500;margin-top:8px;font-family:Inter,sans-serif;'>"
                        f"✅&nbsp; {st.session_state['login_ok']}</div>",
                        unsafe_allow_html=True)
                    st.session_state["login_ok"] = ""

                st.markdown(
                    "<div style='text-align:center;margin-top:18px;font-size:13px;"
                    "color:rgba(100,116,139,0.60);font-family:Inter,sans-serif;'>"
                    "No account?&nbsp;<span style='color:#3b82f6;font-weight:600;'>"
                    "Click Register above</span></div>",
                    unsafe_allow_html=True)

            # ── REGISTER ─────────────────────────────────────────────
            else:
                st.text_input("Full Name",
                              placeholder="Your full name",      key="re_u")
                st.text_input("Email Address",
                              placeholder="you@example.com",     key="re_e")
                st.text_input("Password",
                              placeholder="Min 8 chars · 1 uppercase · 1 special",
                              type="password",                   key="re_p")
                _password_hint()
                st.text_input("Confirm Password",
                              placeholder="Repeat your password",
                              type="password",                   key="re_c")
                st.write("")
                st.markdown('<div class="vf-go">', unsafe_allow_html=True)
                go = st.button("Create Account →", key="btn_re",
                               use_container_width=True)
                st.markdown("</div>", unsafe_allow_html=True)

                if go:
                    u = st.session_state.get("re_u", "").strip()
                    e = st.session_state.get("re_e", "").strip()
                    p = st.session_state.get("re_p", "")
                    c = st.session_state.get("re_c", "")

                    if not all([u, e, p, c]):
                        msg = "All fields are required."
                    elif p != c:
                        msg = "Passwords do not match."
                    else:
                        # FIX 3 — full password validation
                        msg = _validate_password_ui(p)

                    if msg:
                        st.session_state["login_error"] = msg
                        st.rerun()
                    else:
                        with st.spinner("Creating your account…"):
                            r = register_user(u, e, p)
                        if r.get("success"):
                            # FIX 1 — auto sign-in after registration
                            login_result = login_user(e, p)
                            if login_result.get("success"):
                                st.session_state["auth_token"]   = login_result["token"]
                                st.session_state["current_user"] = login_result["user"]
                                st.session_state["login_error"]  = ""
                                _send_login_email(login_result["user"]["email"],
                                                  login_result["user"]["name"])
                                st.rerun()
                            else:
                                # Fallback — go to sign-in with success message
                                st.session_state["login_ok"]    = "Account created — please sign in."
                                st.session_state["login_tab"]   = "signin"
                                st.session_state["login_error"] = ""
                                st.rerun()
                        else:
                            st.session_state["login_error"] = r.get("error", "Registration failed.")
                            st.rerun()

                if st.session_state.get("login_error"):
                    st.markdown(
                        f"<div style='background:rgba(239,68,68,0.10);border:1px solid rgba(239,68,68,0.28);"
                        f"border-radius:10px;padding:10px 14px;color:#fca5a5;font-size:13px;"
                        f"font-weight:500;margin-top:8px;font-family:Inter,sans-serif;'>"
                        f"⚠️&nbsp; {st.session_state['login_error']}</div>",
                        unsafe_allow_html=True)

                st.markdown(
                    "<div style='text-align:center;margin-top:18px;font-size:13px;"
                    "color:rgba(100,116,139,0.60);font-family:Inter,sans-serif;'>"
                    "Already registered?&nbsp;<span style='color:#3b82f6;font-weight:600;'>"
                    "Click Sign In above</span></div>",
                    unsafe_allow_html=True)

        # Security badges
        st.markdown("""
<div style="display:flex;justify-content:center;gap:6px;margin-top:16px;flex-wrap:wrap;">
  <span style="display:flex;align-items:center;gap:4px;padding:3px 10px;
    background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
    border-radius:20px;font-size:9px;font-weight:600;
    color:rgba(100,116,139,0.45);font-family:Inter,sans-serif;letter-spacing:0.5px;text-transform:uppercase;">
    <span style="width:4px;height:4px;border-radius:50%;background:#22c55e;
      box-shadow:0 0 4px #22c55e;display:inline-block;"></span>bcrypt-256
  </span>
  <span style="display:flex;align-items:center;gap:4px;padding:3px 10px;
    background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
    border-radius:20px;font-size:9px;font-weight:600;
    color:rgba(100,116,139,0.45);font-family:Inter,sans-serif;letter-spacing:0.5px;text-transform:uppercase;">
    <span style="width:4px;height:4px;border-radius:50%;background:#22c55e;
      box-shadow:0 0 4px #22c55e;display:inline-block;"></span>Zero-Trust
  </span>
  <span style="display:flex;align-items:center;gap:4px;padding:3px 10px;
    background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);
    border-radius:20px;font-size:9px;font-weight:600;
    color:rgba(100,116,139,0.45);font-family:Inter,sans-serif;letter-spacing:0.5px;text-transform:uppercase;">
    <span style="width:4px;height:4px;border-radius:50%;background:#22c55e;
      box-shadow:0 0 4px #22c55e;display:inline-block;"></span>AES Sessions
  </span>
</div>
""", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    return False
