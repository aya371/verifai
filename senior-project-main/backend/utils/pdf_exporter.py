"""
PDF export utility for VerifAI reports.
Uses reportlab to generate styled PDF reports.
Install: pip install reportlab
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from typing import Dict, List
import io
from datetime import datetime


# ── Color palette ──────────────────────────────────────────────────────────
DARK_BG    = colors.HexColor("#0d0d1a")
ACCENT     = colors.HexColor("#6c63ff")
GREEN      = colors.HexColor("#00b894")
RED        = colors.HexColor("#e17055")
YELLOW     = colors.HexColor("#fdcb6e")
WHITE      = colors.white
LIGHT_GRAY = colors.HexColor("#c0c0d0")
MID_GRAY   = colors.HexColor("#888888")
CARD_BG    = colors.HexColor("#12122a")


def verdict_color(verdict: str):
    v = verdict.upper()
    if "SUPPORTED" in v:   return GREEN
    if "REFUTED" in v:     return RED
    if "INCONCLUSIVE" in v: return YELLOW
    return LIGHT_GRAY


def trust_color(score: int):
    if score >= 75: return GREEN
    if score >= 50: return YELLOW
    return RED


def build_report_pdf(
    fact_results: List[Dict],
    identity_result: Dict = None,
    title: str = "VerifAI Analysis Report"
) -> bytes:
    """Generate a styled PDF report and return as bytes"""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm
    )

    styles = getSampleStyleSheet()

    # Custom styles
    s_title = ParagraphStyle("ReportTitle",
        fontSize=24, textColor=ACCENT, alignment=TA_CENTER,
        spaceAfter=4, fontName="Helvetica-Bold")
    s_subtitle = ParagraphStyle("Subtitle",
        fontSize=10, textColor=MID_GRAY, alignment=TA_CENTER, spaceAfter=2)
    s_section = ParagraphStyle("Section",
        fontSize=13, textColor=WHITE, spaceBefore=14, spaceAfter=6,
        fontName="Helvetica-Bold")
    s_body = ParagraphStyle("Body",
        fontSize=9, textColor=LIGHT_GRAY, spaceAfter=4, leading=14)
    s_label = ParagraphStyle("Label",
        fontSize=8, textColor=MID_GRAY, spaceAfter=2, fontName="Helvetica-Bold")
    s_value = ParagraphStyle("Value",
        fontSize=10, textColor=WHITE, spaceAfter=6, fontName="Helvetica-Bold")
    s_flag = ParagraphStyle("Flag",
        fontSize=8, textColor=RED, spaceAfter=2)
    s_signal = ParagraphStyle("Signal",
        fontSize=8, textColor=GREEN, spaceAfter=2)
    s_mono = ParagraphStyle("Mono",
        fontSize=8, textColor=LIGHT_GRAY, fontName="Courier", spaceAfter=4, leading=12)

    story = []

    # ── Header ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 4*mm))
    story.append(Paragraph("🛡 VerifAI", s_title))
    story.append(Paragraph("Digital Trust Verification Platform", s_subtitle))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %H:%M')}", s_subtitle))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 6*mm))

    # ── Fact-Check Results ─────────────────────────────────────────────────
    if fact_results:
        story.append(Paragraph("FACT-CHECK RESULTS", s_section))
        story.append(Spacer(1, 2*mm))

        for i, result in enumerate(fact_results, 1):
            verdict  = result.get("verdict", "UNKNOWN")
            conf     = result.get("confidence", 0)
            claim    = result.get("claim_text", "")
            reasoning = result.get("reasoning", "")
            sources  = result.get("sources", [])
            src_dates = result.get("source_dates", [])
            vc       = verdict_color(verdict)

            # Claim header table
            claim_data = [[
                Paragraph(f"Claim {i}", ParagraphStyle("cn", fontSize=8,
                    textColor=MID_GRAY, fontName="Helvetica-Bold")),
                Paragraph(verdict, ParagraphStyle("vd", fontSize=11,
                    textColor=vc, fontName="Helvetica-Bold", alignment=TA_CENTER)),
                Paragraph(f"{conf:.0f}% confidence", ParagraphStyle("cf", fontSize=9,
                    textColor=LIGHT_GRAY, alignment=TA_CENTER)),
            ]]
            claim_table = Table(claim_data, colWidths=["15%", "25%", "60%"])
            claim_table.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,-1), CARD_BG),
                ("ROUNDEDCORNERS", [4]),
                ("TOPPADDING",    (0,0), (-1,-1), 8),
                ("BOTTOMPADDING", (0,0), (-1,-1), 8),
                ("LEFTPADDING",   (0,0), (-1,-1), 10),
                ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
            ]))
            story.append(claim_table)
            story.append(Spacer(1, 2*mm))

            # Claim text
            story.append(Paragraph(f"<b>Claim:</b> {claim}", s_body))

            # Reasoning
            if reasoning:
                story.append(Paragraph("Reasoning:", s_label))
                story.append(Paragraph(reasoning, s_mono))

            # Sources
            if sources:
                story.append(Paragraph("Sources:", s_label))
                for j, src in enumerate(sources[:3]):
                    date = src_dates[j] if j < len(src_dates) else "Unknown"
                    story.append(Paragraph(f"• {src}  [{date}]", s_mono))

            # AI detection on input
            input_ai = result.get("input_ai_detection", {})
            if input_ai:
                label = input_ai.get("label", "")
                conf2 = input_ai.get("confidence", 0)
                is_ai = input_ai.get("is_ai_generated", False)
                color = RED if is_ai else GREEN
                story.append(Paragraph(
                    f"Input AI Detection: <font color='#{color.hexval()[1:] if hasattr(color,'hexval') else '888888'}'>"
                    f"{'🤖' if is_ai else '✍️'} {label} ({conf2:.0f}%)</font>",
                    s_body))

            # Source AI detections
            src_ai = result.get("source_ai_detection", [])
            if src_ai:
                story.append(Paragraph("Source AI Detection:", s_label))
                for j, det in enumerate(src_ai[:3]):
                    if det:
                        domain = sources[j].replace("https://","").replace("http://","").split("/")[0] if j < len(sources) else f"Source {j+1}"
                        story.append(Paragraph(
                            f"• {domain}: {det.get('label','?')} ({det.get('confidence',0):.0f}%)",
                            s_mono))

            story.append(Spacer(1, 4*mm))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#1e1e3e")))
            story.append(Spacer(1, 4*mm))

    # ── Identity Verification ──────────────────────────────────────────────
    if identity_result:
        story.append(Paragraph("IDENTITY VERIFICATION", s_section))
        story.append(Spacer(1, 2*mm))

        trust_score = identity_result.get("trust_score", 0)
        badge       = identity_result.get("badge", "UNKNOWN")
        summary     = identity_result.get("summary", "")
        red_flags   = identity_result.get("red_flags", [])
        pos_signals = identity_result.get("positive_signals", [])
        recs        = identity_result.get("recommendations", [])
        interesting = identity_result.get("checks", {}).get("profile", {}).get("interesting_fact", "")
        persona     = identity_result.get("checks", {}).get("profile", {}).get("persona_type", "")
        risk        = identity_result.get("checks", {}).get("profile", {}).get("risk_level", "")
        tc          = trust_color(trust_score)

        # Trust score card
        score_data = [[
            Paragraph("TRUST SCORE", ParagraphStyle("ts_label", fontSize=8,
                textColor=MID_GRAY, fontName="Helvetica-Bold", alignment=TA_CENTER)),
            Paragraph(badge, ParagraphStyle("badge", fontSize=11,
                textColor=tc, fontName="Helvetica-Bold", alignment=TA_CENTER)),
            Paragraph(f"Persona: {persona}", ParagraphStyle("persona", fontSize=9,
                textColor=LIGHT_GRAY, alignment=TA_CENTER)),
            Paragraph(f"Risk: {risk}", ParagraphStyle("risk", fontSize=9,
                textColor=(RED if risk=="High" else YELLOW if risk=="Medium" else GREEN),
                alignment=TA_CENTER)),
        ]]
        score_table = Table([[
            Paragraph(str(trust_score), ParagraphStyle("score_num", fontSize=36,
                textColor=tc, fontName="Helvetica-Bold", alignment=TA_CENTER)),
            Table(score_data, colWidths=["33%","33%","33%"])
        ]], colWidths=["20%", "80%"])
        score_table.setStyle(TableStyle([
            ("BACKGROUND",    (0,0), (-1,-1), CARD_BG),
            ("TOPPADDING",    (0,0), (-1,-1), 10),
            ("BOTTOMPADDING", (0,0), (-1,-1), 10),
            ("LEFTPADDING",   (0,0), (-1,-1), 12),
            ("VALIGN",        (0,0), (-1,-1), "MIDDLE"),
        ]))
        story.append(score_table)
        story.append(Spacer(1, 3*mm))

        if summary:
            story.append(Paragraph(summary, s_body))

        if interesting:
            story.append(Paragraph(f"💡 {interesting}", ParagraphStyle("insight",
                fontSize=9, textColor=ACCENT, spaceAfter=6, leading=14)))

        # Red flags & positive signals side by side
        col1, col2 = [], []
        if red_flags:
            col1.append(Paragraph("⚠ Red Flags", ParagraphStyle("rf_head", fontSize=9,
                textColor=RED, fontName="Helvetica-Bold", spaceAfter=4)))
            for f in red_flags:
                col1.append(Paragraph(f"• {f}", s_flag))
        if pos_signals:
            col2.append(Paragraph("✓ Positive Signals", ParagraphStyle("ps_head", fontSize=9,
                textColor=GREEN, fontName="Helvetica-Bold", spaceAfter=4)))
            for s in pos_signals:
                col2.append(Paragraph(f"• {s}", s_signal))

        if col1 or col2:
            two_col = Table([[col1, col2]], colWidths=["50%", "50%"])
            two_col.setStyle(TableStyle([
                ("VALIGN",       (0,0), (-1,-1), "TOP"),
                ("LEFTPADDING",  (0,0), (-1,-1), 0),
                ("RIGHTPADDING", (0,0), (-1,-1), 8),
            ]))
            story.append(two_col)
            story.append(Spacer(1, 3*mm))

        # Recommendations
        if recs:
            story.append(Paragraph("Recommendations:", s_label))
            for r in recs:
                story.append(Paragraph(f"→ {r}", s_body))

        # Per-check details
        checks = identity_result.get("checks", {})
        for check_name, check in checks.items():
            if check_name == "profile":
                continue
            story.append(Spacer(1, 2*mm))
            story.append(Paragraph(f"{check_name.upper()} CHECK", s_label))
            story.append(Paragraph(
                f"{check.get('value','')}  —  {check.get('label','')}  (Score: {check.get('score',0)})",
                s_body))
            for fl in check.get("flags", []):
                story.append(Paragraph(f"⚠ {fl}", s_flag))
            for sg in check.get("signals", []):
                story.append(Paragraph(f"✓ {sg}", s_signal))

    # ── Footer ─────────────────────────────────────────────────────────────
    story.append(Spacer(1, 8*mm))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 2*mm))
    story.append(Paragraph(
        "VerifAI — Digital Trust Verification Platform | Powered by Claude AI",
        ParagraphStyle("footer", fontSize=8, textColor=MID_GRAY, alignment=TA_CENTER)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
