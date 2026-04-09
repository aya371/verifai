"""
Upgrades the sidebar. Run from: C:\\Users\\aya\\Desktop\\verifai
"""
import base64, os, re

# Load logo
logo_b64 = ""
if os.path.exists("frontend/assets/logo.png"):
    with open("frontend/assets/logo.png", "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()

logo_img = (f'<img src="data:image/png;base64,{logo_b64}" '
            f'style="width:72px;height:72px;object-fit:contain;'
            f'display:block;margin:0 auto 8px auto;'
            f'filter:drop-shadow(0 0 8px #38bdf844);">') if logo_b64 else ""

content = open("frontend/dashboard.py", encoding="utf-8").read()

# Find sidebar start and end
start = content.find("with st.sidebar:")
# Find the header section after sidebar
end = content.find("\n# ", start + 100)
# Find more precisely - look for the header markdown
end2 = content.find('st.markdown(\n    "<div style=\'margin-bottom:24px', start)
if end2 == -1:
    end2 = content.find("tab1, tab2 = st.tabs", start)
if end2 == -1:
    end2 = content.find("\nst.markdown(", start + 200)

print(f"Sidebar from {start} to {end2}")

new_sidebar = '''with st.sidebar:
    # Logo + Brand
    st.markdown(
        "<div style=\'text-align:center;padding:8px 0 4px 0;\'>"
        f"<div>{logo_img}</div>"
        "<div style=\'font-family:var(--font-mono);font-size:20px;font-weight:700;"
        "color:var(--accent);letter-spacing:4px;margin-bottom:2px;"
        "text-shadow:0 0 20px #38bdf844;\'>VERIFAI</div>"
        "<div style=\'font-family:var(--font-mono);font-size:8px;color:var(--text-muted);"
        "letter-spacing:3px;\'>DIGITAL TRUST PLATFORM</div>"
        "<div style=\'margin:10px auto;width:40px;height:1px;"
        "background:linear-gradient(90deg,transparent,var(--accent),transparent);\'></div>"
        "</div>",
        unsafe_allow_html=True)

    # User card
    user = st.session_state.get("current_user")
    if user:
        uname  = user.get("name", "")
        uemail = user.get("email", "")
        st.markdown(
            "<div style=\'background:linear-gradient(135deg,var(--bg-card),var(--bg-deep));"
            "border:1px solid var(--border-lit);border-radius:8px;padding:12px 14px;"
            "margin-bottom:12px;position:relative;overflow:hidden;\'>"
            "<div style=\'position:absolute;top:0;left:0;width:3px;height:100%;"
            "background:linear-gradient(180deg,var(--accent),transparent);"
            "border-radius:8px 0 0 8px;\'></div>"
            "<div style=\'font-family:var(--font-mono);font-size:8px;color:var(--text-muted);"
            "letter-spacing:2px;margin-bottom:6px;\'>AUTHENTICATED USER</div>"
            "<div style=\'display:flex;align-items:center;gap:8px;margin-bottom:4px;\'>"
            "<div style=\'width:7px;height:7px;border-radius:50%;background:var(--green);"
            "box-shadow:0 0 6px var(--green);flex-shrink:0;\'></div>"
            f"<div style=\'font-family:var(--font-mono);font-size:13px;color:var(--accent);"
            f"font-weight:700;\'>{uname}</div>"
            "</div>"
            f"<div style=\'font-family:var(--font-mono);font-size:10px;color:var(--text-muted);"
            f"padding-left:15px;\'>{uemail}</div>"
            "</div>",
            unsafe_allow_html=True)
        if st.button("SIGN OUT", key="logout_btn", use_container_width=True):
            from backend.auth.auth_manager import logout_session
            logout_session(st.session_state.get("auth_token"))
            st.session_state["auth_token"]   = None
            st.session_state["current_user"] = None
            st.rerun()

    st.markdown("<div style=\'margin:12px 0;border-top:1px solid var(--border);\'></div>", unsafe_allow_html=True)

    # System status
    st.markdown("<div style=\'font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:8px;\'>SYSTEM STATUS</div>", unsafe_allow_html=True)
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        if r.status_code == 200:
            h = r.json()
            for svc, status in [("BACKEND","ONLINE"),("CHROMADB",h.get("chroma","ERR").upper()),("NEO4J",h.get("neo4j","ERR").upper())]:
                is_ok = "online" in status.lower() or "connect" in status.lower()
                dc = "var(--green)" if is_ok else "var(--amber)"
                st.markdown(
                    f"<div style=\'display:flex;justify-content:space-between;align-items:center;"
                    f"padding:7px 12px;background:var(--bg-card);border:1px solid var(--border);"
                    f"border-radius:4px;margin-bottom:3px;\'>"
                    f"<div style=\'display:flex;align-items:center;gap:8px;\'>"
                    f"<div style=\'width:6px;height:6px;border-radius:50%;background:{dc};"
                    f"box-shadow:0 0 5px {dc};\'></div>"
                    f"<span style=\'font-family:var(--font-mono);font-size:10px;color:var(--text-secondary);\'>{svc}</span>"
                    f"</div>"
                    f"<span style=\'font-family:var(--font-mono);font-size:9px;color:{dc};letter-spacing:1px;\'>{status}</span>"
                    f"</div>", unsafe_allow_html=True)
        else:
            st.markdown("<div style=\'padding:8px;background:var(--bg-card);border:1px solid var(--red-dim);border-radius:4px;font-family:var(--font-mono);font-size:10px;color:var(--red);\'>BACKEND OFFLINE</div>", unsafe_allow_html=True)
    except:
        st.markdown("<div style=\'padding:8px;background:var(--bg-card);border:1px solid var(--red-dim);border-radius:4px;font-family:var(--font-mono);font-size:10px;color:var(--red);\'>BACKEND OFFLINE</div>", unsafe_allow_html=True)

    st.markdown("<div style=\'margin:12px 0;border-top:1px solid var(--border);\'></div>", unsafe_allow_html=True)

    # Usage metrics
    st.markdown("<div style=\'font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:8px;\'>USAGE METRICS</div>", unsafe_allow_html=True)
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
                f"<div style=\'display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px;\'>"
                f"<div style=\'background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;\'>"
                f"<div style=\'font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:1px;margin-bottom:3px;\'>REQUESTS</div>"
                f"<div style=\'font-family:var(--font-mono);font-size:20px;font-weight:700;color:var(--accent);\'>{total_req}</div>"
                f"</div>"
                f"<div style=\'background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;\'>"
                f"<div style=\'font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:1px;margin-bottom:3px;\'>SPENT</div>"
                f"<div style=\'font-family:var(--font-mono);font-size:20px;font-weight:700;color:var(--amber);\'>${total_cost:.3f}</div>"
                f"</div></div>"
                f"<div style=\'background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px;\'>"
                f"<div style=\'display:flex;justify-content:space-between;margin-bottom:5px;\'>"
                f"<span style=\'font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:1px;\'>CREDIT REMAINING</span>"
                f"<span style=\'font-family:var(--font-mono);font-size:10px;color:{bar_color};font-weight:700;\'>${remaining:.2f}</span>"
                f"</div>"
                f"<div style=\'background:var(--border);border-radius:3px;height:4px;\'>"
                f"<div style=\'background:linear-gradient(90deg,{bar_color},{bar_color}88);height:100%;width:{rem_pct}%;border-radius:3px;\'></div>"
                f"</div>"
                f"<div style=\'font-family:var(--font-mono);font-size:8px;color:var(--text-muted);margin-top:3px;text-align:right;\'>{rem_pct}% remaining</div>"
                f"</div>",
                unsafe_allow_html=True)
    except:
        pass

    st.markdown("<div style=\'margin:12px 0;border-top:1px solid var(--border);\'></div>", unsafe_allow_html=True)

    # Tech stack
    st.markdown(
        "<div style=\'background:var(--bg-card);border:1px solid var(--border);border-radius:6px;padding:10px 12px;\'>"
        "<div style=\'font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:7px;\'>TECH STACK</div>"
        "<div style=\'display:flex;flex-wrap:wrap;gap:4px;\'>"
        "<span style=\'font-family:var(--font-mono);font-size:9px;color:var(--accent);background:var(--accent)12;border:1px solid var(--accent)33;padding:2px 7px;border-radius:3px;\'>CLAUDE AI</span>"
        "<span style=\'font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;\'>DUCKDUCKGO</span>"
        "<span style=\'font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;\'>CHROMADB</span>"
        "<span style=\'font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;\'>FASTAPI</span>"
        "<span style=\'font-family:var(--font-mono);font-size:9px;color:var(--text-secondary);background:var(--bg-deep);border:1px solid var(--border);padding:2px 7px;border-radius:3px;\'>SQLITE</span>"
        "</div></div>",
        unsafe_allow_html=True)

    st.markdown("<div style=\'margin:12px 0;border-top:1px solid var(--border);\'></div>", unsafe_allow_html=True)

    # Theme toggle
    st.markdown("<div style=\'font-family:var(--font-mono);font-size:8px;color:var(--text-muted);letter-spacing:2px;margin-bottom:8px;\'>DISPLAY THEME</div>", unsafe_allow_html=True)
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
        f"<div style=\'font-family:var(--font-mono);font-size:8px;color:var(--accent);"
        f"text-align:center;margin-top:5px;letter-spacing:1px;\'>ACTIVE: {_cur.upper()}</div>",
        unsafe_allow_html=True)

'''

# Replace logo_img placeholder
new_sidebar = new_sidebar.replace(
    'f"<div>{logo_img}</div>"',
    f'"<div>{logo_img}</div>"'
)

new_content = content[:start] + new_sidebar + content[end2:]
open("frontend/dashboard.py", "w", encoding="utf-8").write(new_content)
print("Done! Run: python run_demo.py")
