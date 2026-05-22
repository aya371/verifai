"""
Patches dashboard.py to add the Identity & Media Verification tab.
Run from: C:\\Users\\User\\Documents\\verifai
"""

content = open("frontend/dashboard.py", encoding="utf-8").read()

if "MEDIA VERIFICATION" in content or "cross-verify" in content:
    print("Already patched.")
    exit()

# Find where tabs are defined
if 'tab1, tab2 = st.tabs(["FACT CHECK", "IDENTITY"])' in content:
    content = content.replace(
        'tab1, tab2 = st.tabs(["FACT CHECK", "IDENTITY"])',
        'tab1, tab2, tab3 = st.tabs(["FACT CHECK", "IDENTITY", "MEDIA VERIFY"])'
    )
    print("OK tabs line updated")
elif "st.tabs" in content:
    import re
    content = re.sub(
        r'(tab\w+(?:,\s*tab\w+)*)\s*=\s*st\.tabs\((\[.*?\])\)',
        lambda m: m.group(0).replace(
            m.group(2),
            m.group(2).replace("]", ', "MEDIA VERIFY"]')
        ).replace(m.group(1), m.group(1) + ", tab3"),
        content
    )
    print("OK tabs updated via regex")

# Find footer to insert tab3 block before it
footer_marker = "# ── Footer"
if footer_marker not in content:
    footer_marker = 'st.markdown(\n    f"<div style=\'margin-top:48px'

tab3_code = '''
# ══════════════════════════════════════════════════════════════════════════
# TAB 3 — IDENTITY & MEDIA VERIFICATION
# ══════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(lbl("Subject Name (optional)"), unsafe_allow_html=True)
    media_name = st.text_input("", placeholder="e.g. Elon Musk, John Smith...",
                                label_visibility="collapsed", key="media_name")

    col_img_up, col_aud_up, col_vid_up = st.columns(3)
    with col_img_up:
        st.markdown(lbl("Image"), unsafe_allow_html=True)
        media_image = st.file_uploader("", type=["jpg","jpeg","png","webp"],
                                        label_visibility="collapsed", key="media_img")
    with col_aud_up:
        st.markdown(lbl("Audio"), unsafe_allow_html=True)
        media_audio = st.file_uploader("", type=["wav","mp3","ogg","flac","m4a"],
                                        label_visibility="collapsed", key="media_aud")
    with col_vid_up:
        st.markdown(lbl("Video"), unsafe_allow_html=True)
        media_video = st.file_uploader("", type=["mp4","avi","mov","mkv","webm"],
                                        label_visibility="collapsed", key="media_vid")

    st.markdown(
        f"<div style=\'font-family:JetBrains Mono,monospace;font-size:10px;color:{_muted};"
        f"margin-bottom:12px;\'>"
        f"Provide a name and/or upload media files. At least one input is required.</div>",
        unsafe_allow_html=True)

    if st.button("ANALYZE TRUST", key="media_analyze_btn", type="primary", use_container_width=True):
        if not media_name and not media_image and not media_audio and not media_video:
            st.warning("Please provide at least a name or one media file.")
        else:
            with st.spinner("Running multi-agent media verification..."):
                try:
                    import io
                    files  = {}
                    data   = {}
                    if media_name and media_name.strip():
                        data["name"] = media_name.strip()
                    if media_image:
                        files["image"] = (media_image.name, media_image.getvalue(), media_image.type)
                    if media_audio:
                        files["audio"] = (media_audio.name, media_audio.getvalue(), media_audio.type)
                    if media_video:
                        files["video"] = (media_video.name, media_video.getvalue(), media_video.type)

                    resp = requests.post(
                        "http://localhost:8000/api/media/cross-verify",
                        data=data, files=files, timeout=120
                    )

                    if resp.status_code == 200:
                        result       = resp.json()
                        trust_score  = result.get("trust_score", 0)
                        verdict      = result.get("verdict", "UNCERTAIN")
                        explanation  = result.get("explanation", "")
                        signals      = result.get("signals", [])
                        warnings_list = result.get("warnings", [])
                        breakdown    = result.get("score_breakdown", {})

                        vc = _green if verdict == "TRUSTED" else (_amber if verdict == "UNCERTAIN" else _red)
                        dash_score = int(trust_score * 2.199)

                        # Trust score ring
                        st.markdown(
                            f"<div style=\'display:flex;align-items:center;gap:24px;"
                            f"background:{_bg_deep};border:1px solid {vc}33;"
                            f"border-radius:8px;padding:20px 24px;margin:16px 0;\'>"
                            f"<svg width=\'90\' height=\'90\' viewBox=\'0 0 90 90\' style=\'flex-shrink:0;\'>"
                            f"<circle cx=\'45\' cy=\'45\' r=\'35\' fill=\'none\' stroke=\'{_border}\' stroke-width=\'6\'/>"
                            f"<circle cx=\'45\' cy=\'45\' r=\'35\' fill=\'none\' stroke=\'{vc}\' stroke-width=\'6\'"
                            f" stroke-dasharray=\'{dash_score} 219.9\' stroke-linecap=\'round\' transform=\'rotate(-90 45 45)\'/>"
                            f"<text x=\'45\' y=\'49\' text-anchor=\'middle\' font-size=\'18\' font-weight=\'700\'"
                            f" fill=\'{vc}\' font-family=\'JetBrains Mono,monospace\'>{trust_score}</text>"
                            f"</svg>"
                            f"<div>"
                            f"<div style=\'font-family:JetBrains Mono,monospace;font-size:20px;"
                            f"font-weight:700;color:{vc};letter-spacing:2px;margin-bottom:8px;\'>{verdict}</div>"
                            f"<div style=\'font-family:Space Grotesk,sans-serif;font-size:13px;"
                            f"color:{_text2};line-height:1.6;\'>{explanation}</div>"
                            f"</div></div>",
                            unsafe_allow_html=True)

                        # Score breakdown
                        if breakdown:
                            st.markdown(lbl("Score Breakdown"), unsafe_allow_html=True)
                            cols_bd = st.columns(len(breakdown))
                            for idx, (key, val) in enumerate(breakdown.items()):
                                bc = trust_color(int(val))
                                with cols_bd[idx]:
                                    st.markdown(
                                        f"<div style=\'background:{_bg_card};border:1px solid {_border};"
                                        f"border-radius:6px;padding:12px;text-align:center;\'>"
                                        f"<div style=\'font-family:JetBrains Mono,monospace;font-size:8px;"
                                        f"color:{_muted};letter-spacing:2px;margin-bottom:4px;\'>{key.upper()}</div>"
                                        f"<div style=\'font-family:JetBrains Mono,monospace;font-size:22px;"
                                        f"font-weight:700;color:{bc};\'>{int(val)}</div>"
                                        f"</div>",
                                        unsafe_allow_html=True)

                        # Signals
                        if signals:
                            st.markdown(lbl("Verification Signals"), unsafe_allow_html=True)
                            for sig in signals:
                                st.markdown(
                                    f"<div style=\'font-family:Space Grotesk,sans-serif;font-size:13px;"
                                    f"color:{_green};padding:4px 0;border-bottom:1px solid {_border};\'>"
                                    f"+ {sig}</div>",
                                    unsafe_allow_html=True)

                        # Warnings
                        if warnings_list:
                            st.markdown(lbl("Warnings"), unsafe_allow_html=True)
                            for w in warnings_list:
                                st.markdown(
                                    f"<div style=\'font-family:Space Grotesk,sans-serif;font-size:13px;"
                                    f"color:{_red};padding:4px 0;border-bottom:1px solid {_border};\'>"
                                    f"- {w}</div>",
                                    unsafe_allow_html=True)

                    else:
                        st.error(f"API Error {resp.status_code}: {resp.text}")

                except requests.exceptions.ConnectionError:
                    st.error("Cannot connect to backend.")
                except Exception as e:
                    st.error(f"Error: {e}")

'''

if footer_marker in content:
    content = content.replace(footer_marker, tab3_code + "\n" + footer_marker)
    print("OK tab3 inserted before footer")
else:
    content = content + "\n" + tab3_code
    print("OK tab3 appended at end")

open("frontend/dashboard.py", "w", encoding="utf-8").write(content)
print("Done! Run: python run_demo.py")
