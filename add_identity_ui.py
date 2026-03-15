"""
Adds identity verification UI + PDF export to VerifAI dashboard.
Run from: C:\\Users\\aya\\Desktop\\verifai
"""
import re

# ── 1. Add identity route to routes.py ────────────────────────────────────
routes = open("backend/api/routes.py", encoding="utf-8").read()

identity_route = '''

@router.post("/identity-verify")
async def identity_verify(request: Request):
    """Verify identity of a person, email, URL, or organization"""
    from backend.agents.identity_verifier import IdentityVerifier
    data = await request.json()
    verifier = IdentityVerifier()
    result = verifier.verify(data)
    return result
'''

if "identity-verify" not in routes:
    # Add import for Request if not present
    if "from starlette.requests import Request" not in routes and "from fastapi import" in routes:
        routes = routes.replace("from fastapi import", "from fastapi import Request,", 1)
        if "Request, Request" in routes:
            routes = routes.replace("Request, Request", "Request", 1)
    routes += identity_route
    open("backend/api/routes.py", "w", encoding="utf-8").write(routes)
    print("OK  backend/api/routes.py — identity route added")
else:
    print("OK  backend/api/routes.py — already has identity route")


# ── 2. Patch dashboard.py ──────────────────────────────────────────────────
dashboard = open("frontend/dashboard.py", encoding="utf-8").read()

# Add imports at the top
old_import_block = "import streamlit as st"
new_import_block = """import streamlit as st
import requests as http_requests
import base64
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))"""

if "import base64" not in dashboard:
    dashboard = dashboard.replace(old_import_block, new_import_block, 1)
    print("OK  dashboard.py — imports added")

# Add identity section + PDF export rendering function
identity_ui_code = '''
def render_identity_section(api_base: str):
    """Identity Verification Section"""
    st.markdown("""
    <div style='background:#0a0a18;border:1px solid #1e1e3e;border-radius:12px;padding:20px 24px;margin-top:24px;'>
        <div style='font-size:10px;font-family:monospace;color:#444;letter-spacing:2px;margin-bottom:4px;'>IDENTITY VERIFICATION</div>
        <div style='font-size:13px;color:#c0c0d0;margin-bottom:2px;'>Verify a person, organization, email, or website</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("🔍 Run Identity Verification", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            id_name  = st.text_input("Name or Organization", placeholder="e.g. Elon Musk / Reuters")
            id_email = st.text_input("Email Address", placeholder="e.g. contact@example.com")
        with col2:
            id_url   = st.text_input("Website or Profile URL", placeholder="e.g. https://reuters.com")
            id_desc  = st.text_area("Additional Context", placeholder="Any extra info about this identity...", height=68)

        if st.button("🛡 Verify Identity", use_container_width=True):
            if not any([id_name, id_email, id_url, id_desc]):
                st.warning("Please provide at least one field to verify.")
            else:
                with st.spinner("Analyzing identity..."):
                    try:
                        resp = http_requests.post(
                            f"{api_base}/api/identity-verify",
                            json={"name": id_name, "email": id_email,
                                  "url": id_url, "description": id_desc},
                            timeout=30
                        )
                        if resp.status_code == 200:
                            st.session_state["identity_result"] = resp.json()
                        else:
                            st.error(f"Verification failed: {resp.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")


def render_trust_score(result: dict):
    """Render the identity trust score card"""
    score  = result.get("trust_score", 0)
    badge  = result.get("badge", "UNKNOWN")
    summary = result.get("summary", "")
    checks = result.get("checks", {})
    profile = checks.get("profile", {})
    persona = profile.get("persona_type", "")
    risk    = profile.get("risk_level", "")
    interesting = profile.get("interesting_fact", "")
    red_flags   = result.get("red_flags", [])
    pos_signals = result.get("positive_signals", [])
    recs        = result.get("recommendations", [])

    if score >= 75:
        score_color, badge_bg = "#00b894", "#00b89422"
    elif score >= 50:
        score_color, badge_bg = "#fdcb6e", "#fdcb6e22"
    else:
        score_color, badge_bg = "#e17055", "#e1705522"

    # Score ring + badge
    ring_pct = score
    ring_html = (
        "<div style='display:flex;align-items:center;gap:24px;background:#0a0a18;"
        "border:1px solid #1e1e3e;border-radius:12px;padding:20px 24px;margin-bottom:12px;'>"
        "<div style='position:relative;width:90px;height:90px;flex-shrink:0;'>"
        f"<svg width='90' height='90' viewBox='0 0 90 90'>"
        "<circle cx='45' cy='45' r='38' fill='none' stroke='#1e1e3e' stroke-width='8'/>"
        f"<circle cx='45' cy='45' r='38' fill='none' stroke='{score_color}' stroke-width='8'"
        f" stroke-dasharray='{ring_pct * 2.387} 238.7'"
        " stroke-linecap='round' transform='rotate(-90 45 45)'/>"
        f"<text x='45' y='50' text-anchor='middle' font-size='20' font-weight='bold'"
        f" fill='{score_color}' font-family='monospace'>{score}</text>"
        "</svg></div>"
        "<div style='flex:1;'>"
        f"<div style='background:{badge_bg};border:1px solid {score_color}44;"
        f"color:{score_color};padding:4px 14px;border-radius:6px;"
        f"font-size:13px;font-family:monospace;font-weight:bold;display:inline-block;"
        f"margin-bottom:8px;'>{badge}</div>"
        f"<div style='font-size:11px;color:#888;font-family:monospace;margin-bottom:4px;'>"
        f"Persona: {persona} &nbsp;|&nbsp; Risk: {risk}</div>"
        f"<div style='font-size:12px;color:#c0c0d0;'>{summary}</div>"
        "</div></div>"
    )
    st.markdown(ring_html, unsafe_allow_html=True)

    if interesting:
        st.markdown(
            f"<div style='background:#12122a;border-left:3px solid #6c63ff;"
            f"padding:10px 16px;border-radius:0 8px 8px 0;font-size:12px;"
            f"color:#a29bfe;margin-bottom:12px;'>💡 {interesting}</div>",
            unsafe_allow_html=True)

    # Red flags & positive signals
    col1, col2 = st.columns(2)
    with col1:
        if red_flags:
            flags_html = "<div style='background:#0a0a18;border:1px solid #e1705533;border-radius:8px;padding:14px;'>"
            flags_html += "<div style='font-size:10px;font-family:monospace;color:#e17055;letter-spacing:1px;margin-bottom:8px;'>⚠ RED FLAGS</div>"
            for f in red_flags:
                flags_html += f"<div style='font-size:11px;color:#e17055;margin-bottom:4px;font-family:monospace;'>• {f}</div>"
            flags_html += "</div>"
            st.markdown(flags_html, unsafe_allow_html=True)
    with col2:
        if pos_signals:
            sig_html = "<div style='background:#0a0a18;border:1px solid #00b89433;border-radius:8px;padding:14px;'>"
            sig_html += "<div style='font-size:10px;font-family:monospace;color:#00b894;letter-spacing:1px;margin-bottom:8px;'>✓ POSITIVE SIGNALS</div>"
            for s in pos_signals:
                sig_html += f"<div style='font-size:11px;color:#00b894;margin-bottom:4px;font-family:monospace;'>• {s}</div>"
            sig_html += "</div>"
            st.markdown(sig_html, unsafe_allow_html=True)

    # Per-check breakdown
    for check_name, check in checks.items():
        if check_name == "profile":
            continue
        cscore = check.get("score", 0)
        clabel = check.get("label", "")
        cvalue = check.get("value", "")
        cc = "#00b894" if cscore >= 70 else ("#fdcb6e" if cscore >= 40 else "#e17055")
        check_html = (
            f"<div style='background:#0a0a18;border:1px solid #1e1e3e;border-radius:8px;"
            f"padding:12px 16px;margin-top:10px;display:flex;align-items:center;gap:12px;'>"
            f"<div style='font-size:10px;font-family:monospace;color:#888;min-width:80px;'>{check_name.upper()}</div>"
            f"<div style='font-size:11px;color:#c0c0d0;flex:1;font-family:monospace;'>{cvalue}</div>"
            f"<div style='background:{cc}22;border:1px solid {cc}55;color:{cc};"
            f"padding:2px 10px;border-radius:4px;font-size:11px;font-family:monospace;'>{clabel} ({cscore})</div>"
            f"</div>"
        )
        st.markdown(check_html, unsafe_allow_html=True)

    # Recommendations
    if recs:
        st.markdown("<div style='margin-top:14px;font-size:10px;font-family:monospace;color:#444;letter-spacing:1px;'>RECOMMENDATIONS</div>", unsafe_allow_html=True)
        for r in recs:
            st.markdown(f"<div style='font-size:11px;color:#a29bfe;padding:4px 0;font-family:monospace;'>→ {r}</div>", unsafe_allow_html=True)


def render_pdf_download(fact_results: list, identity_result: dict = None):
    """Render PDF download button"""
    try:
        import sys, os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from backend.utils.pdf_exporter import build_report_pdf
        pdf_bytes = build_report_pdf(fact_results, identity_result)
        b64 = base64.b64encode(pdf_bytes).decode()
        from datetime import datetime
        filename = f"verifai_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        href = (
            f'<a href="data:application/pdf;base64,{b64}" download="{filename}" '
            f'style="display:block;text-align:center;background:linear-gradient(135deg,#6c63ff,#a29bfe);'
            f'color:white;padding:12px 24px;border-radius:8px;text-decoration:none;'
            f'font-family:monospace;font-size:13px;font-weight:bold;margin-top:16px;">'
            f'📄 Download Full Report as PDF</a>'
        )
        st.markdown(href, unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"PDF export unavailable: {e}")
        st.caption("Run: pip install reportlab")

'''

if "render_identity_section" not in dashboard:
    # Insert before "# Title" or st.title
    insert_point = dashboard.find("# Title\nst.title")
    if insert_point == -1:
        insert_point = dashboard.find("st.title(")
    if insert_point != -1:
        dashboard = dashboard[:insert_point] + identity_ui_code + "\n" + dashboard[insert_point:]
        print("OK  dashboard.py — identity UI functions added")
    else:
        dashboard += "\n" + identity_ui_code
        print("OK  dashboard.py — identity UI functions appended")

# Now find where results are shown and add identity + PDF section after them
# Look for Task Metadata expander or end of results rendering
old_task_meta = 'st.expander("📊 Task Metadata"'
new_task_meta = 'st.expander("📊 Task Metadata"'

# Add identity + PDF after all results — find the results block end
results_end_marker = "st.markdown('---')" 

# Instead, add after the detailed results section
pdf_call = '''
                # ── Identity Verification ─────────────────────────────────
                render_identity_section(API_BASE)

                # Show identity result if available
                if st.session_state.get("identity_result"):
                    st.markdown("<div style='margin-top:8px;font-size:10px;font-family:monospace;color:#444;letter-spacing:2px;'>IDENTITY ANALYSIS RESULT</div>", unsafe_allow_html=True)
                    render_trust_score(st.session_state["identity_result"])

                # ── PDF Download ───────────────────────────────────────────
                st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)
                render_pdf_download(
                    fact_results=response_data.get("detailed_results", []),
                    identity_result=st.session_state.get("identity_result")
                )
'''

# Find a good injection point — after the detailed results loop
if "render_identity_section" not in dashboard or "render_pdf_download" not in dashboard:
    # Find after "Task Metadata" expander
    task_meta_pos = dashboard.find('st.expander("📊 Task Metadata"')
    if task_meta_pos == -1:
        task_meta_pos = dashboard.find("Task Metadata")
    if task_meta_pos != -1:
        # Find start of that line
        line_start = dashboard.rfind("\n", 0, task_meta_pos) + 1
        dashboard = dashboard[:line_start] + pdf_call + "\n" + dashboard[line_start:]
        print("OK  dashboard.py — PDF + identity calls added before Task Metadata")
    else:
        print("WARN could not find Task Metadata section to inject PDF/identity")

with open("frontend/dashboard.py", "w", encoding="utf-8") as f:
    f.write(dashboard)
print("OK  frontend/dashboard.py saved")


print("""
Done! Now:
  1. pip install reportlab
  2. Copy pdf_exporter.py to backend/utils/pdf_exporter.py
  3. Copy identity_verifier.py to backend/agents/identity_verifier.py
  4. python run_demo.py

Features added:
  - Identity verification panel (below results)
  - Trust score ring (0-100) with VERIFIED / UNCERTAIN / SUSPICIOUS badge
  - Red flags + positive signals
  - Per-check breakdown (email, domain, AI profile analysis)
  - 💡 Interesting insight about the identity
  - Recommendations
  - 📄 Download Full Report as PDF button
""")
