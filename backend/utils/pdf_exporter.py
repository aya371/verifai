from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Table, TableStyle, HRFlowable)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from typing import Dict, List
import io, re
from datetime import datetime

# ── Colours (same palette as original) ───────────────────────────────
ACCENT     = colors.HexColor("#6c63ff")
GREEN      = colors.HexColor("#00b894")
RED        = colors.HexColor("#e17055")
YELLOW     = colors.HexColor("#fdcb6e")
WHITE      = colors.white
LIGHT_GRAY = colors.HexColor("#c0c0d0")
MID_GRAY   = colors.HexColor("#888888")
CARD_BG    = colors.HexColor("#12122a")
DARK_BG    = colors.HexColor("#0d0d1a")
DIVIDER    = colors.HexColor("#1e1e3e")

# Subtle tinted backgrounds for verdict cards
GREEN_TINT  = colors.HexColor("#0a1f18")
RED_TINT    = colors.HexColor("#1f0e0a")
YELLOW_TINT = colors.HexColor("#1f1a0a")


def verdict_color(verdict: str):
    v = verdict.upper()
    if "SUPPORTED" in v:    return GREEN
    if "REFUTED"   in v:    return RED
    if "INCONCLUSIVE" in v: return YELLOW
    return LIGHT_GRAY


def verdict_bg(verdict: str):
    v = verdict.upper()
    if "SUPPORTED" in v:    return GREEN_TINT
    if "REFUTED"   in v:    return RED_TINT
    if "INCONCLUSIVE" in v: return YELLOW_TINT
    return CARD_BG


def conf_color(score: float):
    if score >= 75: return GREEN
    if score >= 45: return YELLOW
    return RED


def safe_text(text: str) -> str:
    if not text:
        return ""
    t = re.sub(r'<[^>]+>', '', str(text))
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _conf_bar(score: float, width_mm: float = 110) -> Table:
    """Filled progress bar matching the dark theme."""
    filled  = max(0.0, min(100.0, score)) / 100
    bar_w   = width_mm * mm
    fill_w  = bar_w * filled
    empty_w = bar_w - fill_w
    cc      = conf_color(score)

    bar = Table([["", ""]], colWidths=[fill_w, max(empty_w, 0.5)])
    bar.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (0, 0), cc),
        ("BACKGROUND",    (1, 0), (1, 0), DIVIDER),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    label = Paragraph(
        f"{score:.0f}%",
        ParagraphStyle("pct", fontSize=9, textColor=cc,
                       fontName="Helvetica-Bold")
    )
    outer = Table([[bar, label]], colWidths=[bar_w + 2, 16 * mm])
    outer.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return outer


def build_report_pdf(
    fact_results: List[Dict],
    identity_result: Dict = None,   # kept for signature compatibility — ignored
    title: str = "VerifAI Fact-Check Report"
) -> bytes:

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=20 * mm, rightMargin=20 * mm,
        topMargin=20 * mm, bottomMargin=20 * mm
    )

    # ── Styles (same names as original) ──────────────────────────────
    s_title    = ParagraphStyle("T",  fontSize=24, textColor=ACCENT,
                                alignment=TA_CENTER, spaceAfter=4,
                                fontName="Helvetica-Bold")
    s_subtitle = ParagraphStyle("S",  fontSize=10, textColor=MID_GRAY,
                                alignment=TA_CENTER, spaceAfter=2)
    s_section  = ParagraphStyle("H",  fontSize=13, textColor=WHITE,
                                spaceBefore=14, spaceAfter=6,
                                fontName="Helvetica-Bold")
    s_body     = ParagraphStyle("B",  fontSize=9,  textColor=LIGHT_GRAY,
                                spaceAfter=4, leading=14)
    s_label    = ParagraphStyle("L",  fontSize=8,  textColor=MID_GRAY,
                                spaceAfter=2, fontName="Helvetica-Bold")
    s_mono     = ParagraphStyle("M",  fontSize=8,  textColor=LIGHT_GRAY,
                                fontName="Courier", spaceAfter=4, leading=12)

    story = []

    # ── Header ────────────────────────────────────────────────────────
    story.append(Spacer(1, 6 * mm))
    story.append(Paragraph("VerifAI", s_title))
    story.append(Spacer(1, 4 * mm))
    story.append(Paragraph("Fact-Check Report",
                            ParagraphStyle("S2", fontSize=13, textColor=MID_GRAY,
                                           alignment=TA_CENTER, spaceAfter=3)))
    story.append(Spacer(1, 3 * mm))
    story.append(Paragraph(
        datetime.now().strftime("Generated: %B %d, %Y at %H:%M"),
        ParagraphStyle("DT", fontSize=9, textColor=MID_GRAY,
                       alignment=TA_CENTER, spaceAfter=4)))
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 6 * mm))

    # ── Summary tiles ─────────────────────────────────────────────────
    if fact_results:
        total     = len(fact_results)
        supported = sum(1 for r in fact_results
                        if "SUPPORTED"   in r.get("verdict", "").upper())
        refuted   = sum(1 for r in fact_results
                        if "REFUTED"     in r.get("verdict", "").upper())
        inconc    = total - supported - refuted
        avg_conf  = (sum(float(r.get("confidence", 0))
                         for r in fact_results) / total) if total else 0

        def tile(val, lbl, col):
            inner = Table(
                [[Paragraph(str(val),
                             ParagraphStyle("tv", fontSize=20, textColor=col,
                                            fontName="Helvetica-Bold",
                                            alignment=TA_CENTER))],
                 [Paragraph(lbl,
                             ParagraphStyle("tl", fontSize=7, textColor=MID_GRAY,
                                            alignment=TA_CENTER,
                                            fontName="Helvetica-Bold"))]],
                colWidths=["100%"]
            )
            inner.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), CARD_BG),
                ("TOPPADDING",    (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LINEABOVE",     (0, 0), (0, 0), 2, col),
            ]))
            return inner

        tile_w = (170 * mm) / 5
        tiles = Table(
            [[tile(total,             "CLAIMS",       ACCENT),
              tile(supported,         "SUPPORTED",    GREEN),
              tile(refuted,           "REFUTED",      RED),
              tile(inconc,            "INCONCLUSIVE", YELLOW),
              tile(f"{avg_conf:.0f}%","AVG CONF",     conf_color(avg_conf))]],
            colWidths=[tile_w] * 5
        )
        tiles.setStyle(TableStyle([
            ("LEFTPADDING",  (0, 0), (-1, -1), 3),
            ("RIGHTPADDING", (0, 0), (-1, -1), 3),
            ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ]))
        story.append(tiles)
        story.append(Spacer(1, 6 * mm))

    # ── Claims ────────────────────────────────────────────────────────
    if fact_results:
        story.append(Paragraph("FACT-CHECK RESULTS", s_section))
        story.append(Spacer(1, 2 * mm))

        for i, result in enumerate(fact_results, 1):
            verdict   = result.get("verdict",    "UNKNOWN")
            conf      = float(result.get("confidence", 0))
            claim     = result.get("claim_text", "")
            reasoning = result.get("reasoning",  "")
            sources   = result.get("sources",    [])
            src_dates = result.get("source_dates", [])
            input_ai  = result.get("input_ai_detection", {})
            vc        = verdict_color(verdict)
            vbg       = verdict_bg(verdict)

            # Claim header card — verdict tinted background
            header = Table([[
                Paragraph(
                    f"Claim {i}",
                    ParagraphStyle("cn", fontSize=8, textColor=MID_GRAY,
                                   fontName="Helvetica-Bold")),
                Paragraph(
                    verdict,
                    ParagraphStyle("vd", fontSize=11, textColor=vc,
                                   fontName="Helvetica-Bold",
                                   alignment=TA_CENTER)),
            ]], colWidths=["18%", "82%"])
            header.setStyle(TableStyle([
                ("BACKGROUND",    (0, 0), (-1, -1), vbg),
                ("TOPPADDING",    (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("LEFTPADDING",   (0, 0), (-1, -1), 10),
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("LINEBELOW",     (0, 0), (-1, -1), 1, vc),
            ]))
            story.append(header)
            story.append(Spacer(1, 2 * mm))

            # Confidence bar
            conf_row = Table([[
                Paragraph("Confidence",
                           ParagraphStyle("cfl", fontSize=8, textColor=MID_GRAY,
                                          fontName="Helvetica-Bold")),
                _conf_bar(conf),
            ]], colWidths=["18%", "82%"])
            conf_row.setStyle(TableStyle([
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]))
            story.append(conf_row)

            # Claim text
            if claim:
                story.append(Paragraph(
                    f"<b>Claim:</b> {safe_text(claim)}", s_body))

            # Reasoning
            if reasoning:
                story.append(Paragraph("Reasoning:", s_label))
                story.append(Paragraph(safe_text(reasoning), s_mono))

            # Sources
            if sources:
                story.append(Paragraph("Sources:", s_label))
                rows = [
                    [
                        Paragraph(f"{j + 1}.",
                                   ParagraphStyle("sn", fontSize=8,
                                                  textColor=MID_GRAY)),
                        Paragraph(safe_text(src),
                                   ParagraphStyle("su", fontSize=8,
                                                  textColor=ACCENT,
                                                  leading=11)),
                        Paragraph(src_dates[j] if j < len(src_dates) else "—",
                                   ParagraphStyle("sd", fontSize=7,
                                                  textColor=MID_GRAY,
                                                  alignment=TA_RIGHT)),
                    ]
                    for j, src in enumerate(sources[:4])
                ]
                src_tbl = Table(rows, colWidths=["5%", "75%", "20%"])
                src_tbl.setStyle(TableStyle([
                    ("TOPPADDING",    (0, 0), (-1, -1), 3),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                    ("LEFTPADDING",   (0, 0), (-1, -1), 4),
                    ("LINEBELOW",     (0, 0), (-1, -1), 0.3, DIVIDER),
                    ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ]))
                story.append(src_tbl)

            # AI detection
            if input_ai:
                label  = input_ai.get("label", "Unknown")
                conf2  = float(input_ai.get("confidence", 0))
                is_ai  = input_ai.get("is_ai_generated", False)
                hex_c  = "e17055" if is_ai else "00b894"
                prefix = "AI-Generated" if is_ai else "Human-Written"
                story.append(Paragraph(
                    f"Input AI Detection: "
                    f"<font color='#{hex_c}'>{prefix} — {label} "
                    f"({conf2:.0f}%)</font>",
                    s_body))

            story.append(Spacer(1, 4 * mm))
            story.append(HRFlowable(width="100%", thickness=0.5,
                                    color=DIVIDER))
            story.append(Spacer(1, 4 * mm))

    # ── Footer ────────────────────────────────────────────────────────
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 2 * mm))
    story.append(Paragraph(
        "VerifAI — Digital Trust Verification Platform |  "
        "All findings are probabilistic and require human review.",
        ParagraphStyle("footer", fontSize=8, textColor=MID_GRAY,
                       alignment=TA_CENTER)))

    doc.build(story)
    buffer.seek(0)
    return buffer.read()
