import streamlit as st
import requests as http_requests
import base64
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import requests
from datetime import datetime

st.set_page_config(
    page_title="VerifAI - Digital Trust Verification",
    page_icon="V",
    layout="wide"
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;600&display=swap');
    html, body, [class*="css"] { font-family: 'IBM Plex Sans', sans-serif; }
</style>
""", unsafe_allow_html=True)

API_URL = "http://localhost:8000/api"


def render_source_timeline(sources: list, source_dates: list, verdict: str):
    """One timeline row per source showing domain + publication date"""

    if verdict == "REFUTED":
        dot_color = "#e17055"
    elif verdict == "SUPPORTED":
        dot_color = "#00b894"
    else:
        dot_color = "#74b9ff"

    if not source_dates:
        source_dates = ["Unknown"] * len(sources)

    while len(source_dates) < len(sources):
        source_dates.append("Unknown")

    rows = ""
    for i, (source, date) in enumerate(zip(sources[:5], source_dates[:5])):
        domain = source.replace("https://", "").replace("http://", "").split("/")[0]
        if len(domain) > 42:
            domain = domain[:42] + "..."
        date_label = date if (date and date not in ["Unknown", ""]) else "Date unknown"
        pct = 10 + (i * 16)

        rows += (
            "<div style='margin-bottom:16px;'>"
            "<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px;'>"
            "<span style='width:9px;height:9px;border-radius:50%;background:" + dot_color + ";flex-shrink:0;display:inline-block;box-shadow:0 0 5px " + dot_color + "88;'></span>"
            "<span style='font-size:12px;font-family:monospace;color:#c0c0d0;flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;'>" + domain + "</span>"
            "<span style='font-size:11px;font-family:monospace;color:#fff;background:#1a1a2e;border:1px solid " + dot_color + "55;padding:2px 10px;border-radius:4px;flex-shrink:0;'>" + date_label + "</span>"
            "</div>"
            "<div style='position:relative;height:5px;background:#12122a;border-radius:3px;'>"
            "<div style='position:absolute;left:0;top:0;height:100%;width:" + str(pct) + "%;background:linear-gradient(90deg,#1e1e3e," + dot_color + "44);border-radius:3px;'></div>"
            "<div style='position:absolute;top:50%;left:" + str(pct) + "%;transform:translate(-50%,-50%);width:13px;height:13px;border-radius:50%;background:" + dot_color + ";border:2px solid #0a0a1a;box-shadow:0 0 8px " + dot_color + ";'></div>"
            "</div>"
            "</div>"
        )

    html = (
        "<div style='background:#0a0a18;border:1px solid #1e1e3e;border-radius:10px;padding:18px 20px;margin-top:16px;'>"
        "<div style='font-size:10px;font-family:monospace;color:#444;letter-spacing:2px;margin-bottom:16px;'>SOURCE PUBLICATION DATES</div>"
        + rows +
        "<div style='display:flex;justify-content:space-between;font-size:10px;font-family:monospace;color:#2a2a4e;margin-top:8px;padding-top:8px;border-top:1px solid #1a1a2e;'>"
        "<span>OLDER</span><span>RECENT</span>"
        "</div>"
        "</div>"
    )

    st.markdown(html, unsafe_allow_html=True)



def ai_badge(detection: dict) -> str:
    """Render an AI detection badge"""
    if not detection:
        return ""
    label = detection.get("label", "Unknown")
    conf  = detection.get("confidence", 0)
    is_ai = detection.get("is_ai_generated", False)

    if "AI-Generated" in label or (is_ai and conf >= 80):
        color, icon = "#e17055", "🤖"
    elif "Likely AI" in label or (is_ai and conf >= 60):
        color, icon = "#fdcb6e", "⚠️"
    elif "Likely Human" in label or "Human" in label:
        color, icon = "#00b894", "✍️"
    else:
        color, icon = "#636e72", "❓"

    return (
        f"<span style='background:{color}22;border:1px solid {color}55;"
        f"color:{color};padding:2px 8px;border-radius:4px;"
        f"font-size:11px;font-family:monospace;'>"
        f"{icon} {label} ({conf:.0f}%)</span>"
    )

def render_ai_section(input_detection: dict, source_detections: list, sources: list):
    """Render the AI detection summary section"""
    if not input_detection and not source_detections:
        return

    rows = ""

    # Input detection
    if input_detection:
        label  = input_detection.get("label", "Unknown")
        conf   = input_detection.get("confidence", 0)
        is_ai  = input_detection.get("is_ai_generated", False)
        reason = input_detection.get("reasoning", "")
        signals = input_detection.get("signals", [])

        if is_ai and conf >= 60:
            dot, dc = "#e17055", "#e17055"
        elif "Human" in label:
            dot, dc = "#00b894", "#00b894"
        else:
            dot, dc = "#6c757d", "#6c757d"

        rows += (
            "<div style='margin-bottom:14px;padding-bottom:14px;border-bottom:1px solid #1a1a2e;'>"
            "<div style='display:flex;align-items:center;gap:8px;margin-bottom:6px;'>"
            f"<span style='font-size:11px;font-family:monospace;color:#888;'>YOUR INPUT</span>"
            f"<span style='background:{dc}22;border:1px solid {dc}55;color:{dc};"
            f"padding:2px 10px;border-radius:4px;font-size:11px;font-family:monospace;'>"
            f"{'🤖' if is_ai else '✍️'} {label} ({conf:.0f}%)</span>"
            "</div>"
            f"<div style='font-size:11px;color:#adb5bd;font-family:monospace;'>{reason}</div>"
        )
        if signals:
            rows += "<div style='margin-top:4px;'>" + "".join(
                f"<span style='background:#1e1e2e;border:1px solid #333;color:#636e72;"
                f"padding:1px 6px;border-radius:3px;font-size:10px;font-family:monospace;margin:2px;display:inline-block;'>{s}</span>"
                for s in signals[:4]
            ) + "</div>"
        rows += "</div>"

    # Source detections
    for i, (det, source) in enumerate(zip(source_detections[:3], sources[:3])):
        if not det:
            continue
        label  = det.get("label", "Unknown")
        conf   = det.get("confidence", 0)
        is_ai  = det.get("is_ai_generated", False)
        domain = source.replace("https://","").replace("http://","").split("/")[0]

        if is_ai and conf >= 60:
            dc = "#e17055"
        elif "Human" in label:
            dc = "#00b894"
        else:
            dc = "#6c757d"

        rows += (
            "<div style='display:flex;align-items:center;gap:10px;margin-bottom:8px;'>"
            f"<span style='font-size:11px;font-family:monospace;color:#c0c0d0;flex:1;'>{domain}</span>"
            f"<span style='background:{dc}22;border:1px solid {dc}55;color:{dc};"
            f"padding:2px 8px;border-radius:4px;font-size:11px;font-family:monospace;flex-shrink:0;'>"
            f"{'🤖' if is_ai else '✍️'} {label} ({conf:.0f}%)</span>"
            "</div>"
        )

    html = (
        "<div style='background:#0a0a18;border:1px solid #1e1e3e;border-radius:10px;"
        "padding:18px 20px;margin-top:16px;'>"
        "<div style='font-size:10px;font-family:monospace;color:#444;"
        "letter-spacing:2px;margin-bottom:14px;'>AI CONTENT DETECTION</div>"
        + rows +
        "</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


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


# Title
st.title("VerifAI: Digital Trust Verification Platform")
st.markdown("### Multi-Agent AI System for Fact-Checking & Identity Verification")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.header("System Status")
    try:
        r = requests.get(f"{API_URL}/health", timeout=2)
        if r.status_code == 200:
            st.success("Backend: Online")
            health = r.json()
            st.info(f"ChromaDB: {health.get('chroma', 'unknown')}")
            st.info(f"Neo4j: {health.get('neo4j', 'optional')}")
        else:
            st.error("Backend: Offline")
    except:
        st.error("Backend: Not Running")
        st.warning("Run: python run_demo.py")

    st.markdown("---")
    try:
        r = requests.get(f"{API_URL}/usage", timeout=2)
        if r.status_code == 200:
            usage = r.json()
            st.metric("Total Requests", usage['total_requests'])
            st.metric("Total Cost", f"${usage['total_cost']:.4f}")
            st.metric("Remaining Credit", f"${usage['remaining_credit']:.2f}")
    except:
        pass

    st.markdown("---")
    st.markdown("**Demo Mode:** Fact-Checking")
    st.markdown("*Identity verification coming soon*")

# Tabs
tab1, tab2 = st.tabs(["Fact-Check Article", "Verify Identity (Phase 2)"])

with tab1:
    st.header("Fact-Check Claims & Articles")
    st.markdown("Enter a claim, question, or paste an article. Supports typos and informal language.")

    with st.expander("Example Claims (click to load)"):
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Fake Hurricane Claim"):
                st.session_state.fact_check_input = "Hurricane Layla struck Dubai on September 15, 2024, causing $2 billion in damages."
            if st.button("Climate Fact"):
                st.session_state.fact_check_input = "Global temperatures have increased by approximately 1.1C since pre-industrial times."
        with col2:
            if st.button("Sports Claim"):
                st.session_state.fact_check_input = "Messi won the 2022 World Cup with Argentina"
            if st.button("Space Fact"):
                st.session_state.fact_check_input = "James Webb Space Telescope launched in December 2021"

    claim_text = st.text_area(
        "Enter claim, question, or article to verify:",
        value=st.session_state.get('fact_check_input', ''),
        height=150,
        placeholder="Example: 'did elon musk found tesla?' or paste a full article..."
    )

    col_a, col_b = st.columns([2, 1])
    with col_a:
        extract_claims = st.checkbox(
            "Auto-extract claims (recommended for articles)",
            value=True,
            help="Uses Claude to intelligently extract factual claims from your text"
        )
    with col_b:
        language = st.selectbox(
            "Search language",
            ["English", "Arabic", "French", "Spanish", "German",
             "Italian", "Portuguese", "Russian", "Chinese", "Japanese", "Turkish"],
            index=0,
            help="Search for evidence in this language. Results are translated back to English."
        )

    if st.button("Verify Claim", type="primary", use_container_width=True):
        if not claim_text or len(claim_text.strip()) < 3:
            st.error("Please enter a claim")
        else:
            with st.spinner("Searching web and analyzing with AI..."):
                try:
                    response = requests.post(
                        f"{API_URL}/fact-check",
                        json={"text": claim_text, "extract_claims": extract_claims, "language": language},
                        timeout=120
                    )

                    if response.status_code == 200:
                        result = response.json()
                        st.success("Analysis Complete!")

                        st.markdown("### Overall Verdict")
                        verdict = result['overall_verdict']
                        confidence = result['confidence']

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Verdict", verdict)
                        with col2:
                            st.metric("Confidence", f"{confidence:.1f}%")
                        with col3:
                            st.metric("Processing Time", f"{result['processing_time_ms']:.0f}ms")

                        st.markdown("---")

                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Claims Analyzed", result['claims_analyzed'])
                        with col2:
                            st.metric("Claims Refuted", result['claims_refuted'])
                        with col3:
                            st.metric("Claims Supported", result['claims_supported'])

                        st.markdown("---")
                        st.markdown("### Detailed Claim Analysis")

                        for i, claim_result in enumerate(result['detailed_results'], 1):
                            with st.expander(f"Claim {i}: {claim_result['claim_text'][:80]}...", expanded=(i == 1)):

                                v = claim_result['verdict']
                                if v == 'REFUTED':
                                    st.error(f"**Verdict:** {v}")
                                elif v == 'SUPPORTED':
                                    st.success(f"**Verdict:** {v}")
                                else:
                                    st.warning(f"**Verdict:** {v}")

                                st.progress(claim_result['confidence'] / 100)
                                st.caption(f"Confidence: {claim_result['confidence']:.1f}%")

                                st.markdown("**Reasoning:**")
                                st.info(claim_result['reasoning'])

                                if claim_result.get('sources'):
                                    st.markdown("**Sources:**")
                                    src_detections = claim_result.get('source_ai_detection', [])
                                    for si, source in enumerate(claim_result['sources']):
                                        det = src_detections[si] if si < len(src_detections) else {}
                                        badge = ai_badge(det)
                                        st.markdown(f"- [{source}]({source}) &nbsp;{badge}", unsafe_allow_html=True)

                                    render_source_timeline(
                                        sources=claim_result.get('sources', []),
                                        source_dates=claim_result.get('source_dates', []),
                                        verdict=claim_result['verdict']
                                    )
                                    render_ai_section(
                                        input_detection=claim_result.get('input_ai_detection', {}),
                                        source_detections=claim_result.get('source_ai_detection', []),
                                        sources=claim_result.get('sources', [])
                                    )

                                if claim_result.get('flags'):
                                    st.caption(f"Flags: {', '.join(claim_result['flags'])}")

                        with st.expander("Task Metadata"):
                            st.json({
                                "task_id": result['task_id'],
                                "timestamp": result['timestamp'],
                                "processing_time_ms": result['processing_time_ms']
                            })
                    else:
                        st.error(f"API Error: {response.status_code}")
                        st.code(response.text)

                except requests.exceptions.Timeout:
                    st.error("Request timed out. Try a shorter claim.")
                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend. Is it running?")
                except Exception as e:
                    st.error(f"Unexpected error: {str(e)}")

with tab2:
    st.header("Identity Verification")
    st.info("Coming in Phase 2")
    st.markdown("**Planned Features:**")
    st.markdown("- LinkedIn/social media profile verification")
    st.markdown("- Reverse image search & deepfake detection")
    st.markdown("- Data breach checking")
    st.markdown("- Credential validation")

    col1, col2 = st.columns(2)
    with col1:
        st.text_input("Full Name", disabled=True, placeholder="John Doe")
        st.text_input("Email", disabled=True, placeholder="john@example.com")
    with col2:
        st.file_uploader("Upload Resume (PDF)", disabled=True)
        st.file_uploader("Upload Profile Photo", disabled=True)
    st.button("Verify Identity", disabled=True)

st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("Zero-Trust Architecture")
with col2:
    st.caption("Multi-Agent System")
with col3:
    st.caption("RAG-Powered Verification")
