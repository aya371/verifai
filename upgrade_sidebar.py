"""
Upgrades the sidebar to a professional intelligence platform look.
Run from: C:\\Users\\aya\\Desktop\\verifai
"""
import base64, os

# Load logo
logo_path = "frontend/assets/logo.png"
if os.path.exists(logo_path):
    with open(logo_path, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
else:
    logo_b64 = ""

logo_img = f"<img src='data:image/png;base64,{logo_b64}' style='width:72px;height:72px;object-fit:contain;display:block;margin:0 auto 8px auto;filter:drop-shadow(0 0 8px #38bdf844);'>" if logo_b64 else ""

content = open("frontend/dashboard.py", encoding="utf-8").read()

old_sidebar = """with st.sidebar:
    st.markdown(
        "<div style='font-family:var(--font-mono);font-size:18px;font-weight:700;"
        "color:var(--accent);letter-spacing:2px;margin-bottom:2px;'>VERIFAI</div>"
        "<div style='font-family:var(--font-mono);font-size:9px;color:var(--text-muted);"
        "letter-spacing:3px;margin-bottom:24px;'>DIGITAL TRUST PLATFORM</div>",
        unsafe_allow_html=True)

    # User info + logout
    user = st.session_state.get("current_user")
    if user:
        st.markdown(
            f"<div style='background:var(--bg-card);border:1px solid var(--border-lit);"
            f"border-radius:6px;padding:12px;margin-bottom:16px;'>"
            f"<div style='font-family:var(--font-mono);font-size:9px;color:var(--text-muted);"
            f"letter-spacing:2px;margin-bottom:4px;'>SIGNED IN AS</div>"
            f"<div style='font-family:var(--font-mono);font-size:13px;color:var(--accent);"
            f"font-weight:600;'>{user['name']}</div>"
            f"<div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);'>"
            f"{user['email']}</div>"
            f"</div>",
            unsafe_allow_html=True)
        if st.button("SIGN OUT", key="logout_btn", use_container_width=True):
            from backend.auth.auth_manager import logout_session
            logout_session(st.session_state.get("auth_token"))
            st.session_state["auth_token"]   = None
            st.session_state["current_user"] = None
            st.rerun()

    st.markdown(f"<div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:2px;margin-bottom:10px;'>SYSTEM STATUS</div>", unsafe_allow_html=True)

    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        if r.status_code == 200:
            h = r.json()
            for svc, status in [("BACKEND", "ONLINE"), ("CHROMADB", h.get('chroma','\u2014').upper()), ("NEO4J", h.get('neo4j','\u2014').upper())]:
                c = "var(--green)" if "online" in status.lower() or "connect" in status.lower() else "var(--amber)"
                st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center;padding:6px 10px;background:var(--bg-card);border:1px solid var(--border);border-radius:4px;margin-bottom:4px;'><span style='font-family:var(--font-mono);font-size:10px;color:var(--text-secondary);'>{svc}</span><span style='font-family:var(--font-mono);font-size:9px;color:{c};letter-spacing:1px;'>{status}</span></div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='padding:8px 10px;background:var(--bg-card);border:1px solid var(--red-dim);border-radius:4px;font-family:var(--font-mono);font-size:10px;color:var(--red);'>BACKEND OFFLINE</div>", unsafe_allow_html=True)
    except:
        st.markdown(f"<div style='padding:8px 10px;background:var(--bg-card);border:1px solid var(--red-dim);border-radius:4px;font-family:var(--font-mono);font-size:10px;color:var(--red);'>BACKEND OFFLINE</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin:20px 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)

    try:
        r = requests.get(f"{API_URL}/usage", timeout=2)
        if r.status_code == 200:
            u = r.json()
            for lbl_text, val in [("REQUESTS", str(u.get('total_requests',0))), ("COST", f"${u.get('total_cost',0):.4f}"), ("CREDIT", f"${u.get('remaining_credit',0):.2f}")]:
                st.markdown(f"<div style='margin-bottom:12px;'><div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;margin-bottom:3px;'>{lbl_text}</div><div style='font-family:var(--font-mono);font-size:18px;font-weight:700;color:var(--text-primary);'>{val}</div></div>", unsafe_allow_html=True)
    except:
        pass

    st.markdown("<div style='margin:20px 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;'>MULTI-AGENT RAG SYSTEM</div>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:var(--font-mono);font-size:9px;color:var(--text-muted);margin-top:4px;'>CLAUDE AI \xb7 DUCKDUCKGO \xb7 CHROMADB</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin:20px 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);letter-spacing:1.5px;margin-bottom:10px;'>DISPLAY THEME</div>", unsafe_allow_html=True)

    col_d, col_l = st.columns(2)
    with col_d:
        if st.button("DARK", key="theme_dark", use_container_width=True):
            st.session_state["theme"] = "dark"
            st.rerun()
    with col_l:
        if st.button("LIGHT", key="theme_light", use_container_width=True):
            st.session_state["theme"] = "light"
            st.rerun()

    # Show current theme
    _cur = st.session_state.get("theme", "dark")
    st.markdown(
        f"<div style='font-family:var(--font-mono);font-size:9px;color:var(--accent);"
        f"text-align:center;margin-top:6px;letter-spacing:1px;'>"
        f"ACTIVE: {_cur.upper()}</div>",
        unsafe_allow_html=True)"""

new_sidebar = f"""with st.sidebar:
    # ── Logo + Branding ───────────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;padding:8px 0 4px 0;'>"
        "{logo_img}"
        "<div style='font-family:var(--font-mono);font-size:20px;font-weight:700;"
        "color:var(--accent);letter-spacing:4px;margin-bottom:2px;"
        "text-shadow:0 0 20px var(--accent)44;'>VERIFAI</div>"
        "<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);"
        "letter-spacing:3px;'>DIGITAL TRUST PLATFORM</div>"
        "<div style='margin:12px auto;width:40px;height:1px;background:linear-gradient(90deg,transparent,var(--accent),transparent);'></div>"
        "</div>",
        unsafe_allow_html=True)

    # ── User Card ─────────────────────────────────────────────────────
    user = st.session_state.get("current_user")
    if user:
        st.markdown(
            f"<div style='background:linear-gradient(135deg,var(--bg-card),var(--bg-deep));"
            f"border:1px solid var(--border-lit);border-radius:8px;padding:12px 14px;"
            f"margin-bottom:12px;position:relative;overflow:hidden;'>"
            f"<div style='position:absolute;top:0;left:0;width:3px;height:100%;"
            f"background:linear-gradient(180deg,var(--accent),transparent);border-radius:8px 0 0 8px;'></div>"
            f"<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);"
            f"letter-spacing:2px;margin-bottom:6px;'>AUTHENTICATED USER</div>"
            f"<div style='display:flex;align-items:center;gap:8px;margin-bottom:4px;'>"
            f"<div style='width:8px;height:8px;border-radius:50%;background:var(--green);"
            f"box-shadow:0 0 6px var(--green);flex-shrink:0;'></div>"
            f"<div style='font-family:var(--font-mono);font-size:13px;color:var(--accent);"
            f"font-weight:700;letter-spacing:0.5px;'>{user['name']}</div>"
            f"</div>"
            f"<div style='font-family:var(--font-mono);font-size:10px;color:var(--text-muted);"
            f"padding-left:16px;'>{user['email']}</div>"
            f"</div>",
            unsafe_allow_html=True)
        if st.button("SIGN OUT", key="logout_btn", use_container_width=True):
            from backend.auth.auth_manager import logout_session
            logout_session(st.session_state.get("auth_token"))
            st.session_state["auth_token"]   = None
            st.session_state["current_user"] = None
            st.rerun()

    st.markdown("<div style='margin:14px 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)

    # ── System Status ─────────────────────────────────────────────────
    st.markdown("<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:8px;'>SYSTEM STATUS</div>", unsafe_allow_html=True)

    try:
        r = requests.get(f"{{API_URL}}/health", timeout=2)
        if r.status_code == 200:
            h = r.json()
            for svc, status in [("BACKEND", "ONLINE"), ("CHROMADB", h.get('chroma','ERR').upper()), ("NEO4J", h.get('neo4j','ERR').upper())]:
                is_ok = "online" in status.lower() or "connect" in status.lower()
                dot_color = "var(--green)" if is_ok else "var(--amber)"
                txt_color = "var(--green)" if is_ok else "var(--amber)"
                st.markdown(
                    f"<div style='display:flex;justify-content:space-between;align-items:center;"
                    f"padding:7px 12px;background:var(--bg-card);border:1px solid var(--border);"
                    f"border-radius:4px;margin-bottom:3px;'>"
                    f"<div style='display:flex;align-items:center;gap:8px;'>"
                    f"<div style='width:6px;height:6px;border-radius:50%;background:{dot_color};"
                    f"box-shadow:0 0 6px {dot_color};'></div>"
                    f"<span style='font-family:var(--font-mono);font-size:10px;color:var(--text-secondary);'>{svc}</span>"
                    f"</div>"
                    f"<span style='font-family:var(--font-mono);font-size:9px;color:{txt_color};letter-spacing:1px;'>{status}</span>"
                    f"</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div style='padding:8px;background:var(--bg-card);border:1px solid var(--red-dim);border-radius:4px;font-family:var(--font-mono);font-size:10px;color:var(--red);display:flex;gap:8px;align-items:center;'><div style='width:6px;height:6px;border-radius:50%;background:var(--red);box-shadow:0 0 6px var(--red);'></div>BACKEND OFFLINE</div>", unsafe_allow_html=True)
    except:
        st.markdown(f"<div style='padding:8px;background:var(--bg-card);border:1px solid var(--red-dim);border-radius:4px;font-family:var(--font-mono);font-size:10px;color:var(--red);display:flex;gap:8px;align-items:center;'><div style='width:6px;height:6px;border-radius:50%;background:var(--red);'></div>BACKEND OFFLINE</div>", unsafe_allow_html=True)

    st.markdown("<div style='margin:14px 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)

    # ── Usage Stats ───────────────────────────────────────────────────
    st.markdown("<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:10px;'>USAGE METRICS</div>", unsafe_allow_html=True)

    try:
        r = requests.get(f"{{API_URL}}/usage", timeout=2)
        if r.status_code == 200:
            u = r.json()
            total_req  = u.get('total_requests', 0)
            total_cost = u.get('total_cost', 0)
            remaining  = u.get('remaining_credit', 0)
            initial_credit = 5.0
            used_pct = min(100, int((initial_credit - remaining) / initial_credit * 100))
            remaining_pct = 100 - used_pct

            # Requests + Cost side by side
            st.markdown(
                f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:10px;'>"
                f"<div style='background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;'>"
                f"<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:1px;margin-bottom:4px;'>REQUESTS</div>"
                f"<div style='font-family:var(--font-mono);font-size:20px;font-weight:700;color:var(--accent);'>{total_req}</div>"
                f"</div>"
                f"<div style='background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;'>"
                f"<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:1px;margin-bottom:4px;'>SPENT</div>"
                f"<div style='font-family:var(--font-mono);font-size:20px;font-weight:700;color:var(--amber);'>${total_cost:.3f}</div>"
                f"</div>"
                f"</div>",
                unsafe_allow_html=True)

            # Credit bar
            bar_color = "var(--green)" if remaining_pct > 50 else ("var(--amber)" if remaining_pct > 20 else "var(--red)")
            st.markdown(
                f"<div style='background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;margin-bottom:4px;'>"
                f"<div style='display:flex;justify-content:space-between;margin-bottom:6px;'>"
                f"<span style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:1px;'>CREDIT REMAINING</span>"
                f"<span style='font-family:var(--font-mono);font-size:10px;color:{bar_color};font-weight:700;'>${remaining:.2f}</span>"
                f"</div>"
                f"<div style='background:var(--border);border-radius:3px;height:4px;overflow:hidden;'>"
                f"<div style='background:linear-gradient(90deg,{bar_color},{bar_color}88);height:100%;width:{remaining_pct}%;border-radius:3px;transition:width 0.3s;'></div>"
                f"</div>"
                f"<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);margin-top:4px;text-align:right;'>{remaining_pct}% remaining</div>"
                f"</div>",
                unsafe_allow_html=True)
    except:
        pass

    st.markdown("<div style='margin:14px 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)

    # ── Stack Info ────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px 12px;'>"
        "<div style='font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:8px;'>TECH STACK</div>"
        "<div style='display:flex;flex-wrap:wrap;gap:4px;'>"
        "<span style='font-family:var(--font-mono);font-size:9px;color:var(--accent);background:var(--accent)12;border:1px solid var(--accent)33;padding:2px 7px;border-radius:3px;'>CLAUDE AI</span>"
        "<span style='font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;'>DUCKDUCKGO</span>"
        "<span style='font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;'>CHROMADB</span>"
        "<span style='font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;'>FASTAPI</span>"
        "<span style='font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;'>SQLITE</span>"
        "</div>"
        "</div>",
        unsafe_allow_html=True)

    st.markdown("<div style='margin:14px 0;border-top:1px solid var(--border);'></div>", unsafe_allow_html=True)

    # ── Theme Toggle ──────────────────────────────────────────────────
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
        f"text-align:center;margin-top:5px;letter-spacing:1px;'>ACTIVE: {{_cur.upper()}}</div>",
        unsafe_allow_html=True)"""

if old_sidebar in content:
    content = content.replace(old_sidebar, new_sidebar)
    open("frontend/dashboard.py", "w", encoding="utf-8").write(content)
    print("OK - sidebar upgraded!")
else:
    print("ERROR - could not find old sidebar block")
    # Try finding by first unique line
    idx = content.find("with st.sidebar:")
    if idx != -1:
        print(f"Found sidebar at char {idx}")
        print("First 100 chars after:", repr(content[idx:idx+100]))
