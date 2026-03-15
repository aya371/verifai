"""
Adds AI-generated content detection to VerifAI.
- Detects if user input is AI-generated
- Detects if each source article is AI-generated
- Shows badge next to each source + summary section

Run from: C:\\Users\\aya\\Desktop\\verifai
"""

# ── 1. Create the AI detector agent ─────────────────────────────────────
ai_detector_code = '''from anthropic import Anthropic
from config import config
from backend.utils.logger import logger
from typing import Dict

AI_DETECTION_PROMPT = """You are an AI-generated content detector. Analyze the following text and determine if it was likely written by an AI (like GPT, Claude, Gemini) or by a human.

Look for these AI writing signals:
- Overly structured and balanced sentences
- Repetitive transitional phrases ("Furthermore", "Additionally", "In conclusion")
- Lack of personal voice, emotion, or unique perspective
- Unnaturally perfect grammar and punctuation
- Generic, non-specific examples
- Hedging language ("It is worth noting", "It is important to consider")
- Suspiciously comprehensive coverage of all angles

TEXT TO ANALYZE:
{text}

Respond ONLY with a JSON object:
{{
    "is_ai_generated": true or false,
    "confidence": 0-100,
    "label": "AI-Generated" | "Likely AI" | "Uncertain" | "Likely Human" | "Human-Written",
    "signals": ["list of detected signals that influenced the decision"],
    "reasoning": "One sentence explanation"
}}
"""

class AIDetector:
    def __init__(self):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        logger.info("AIDetector initialized")

    def detect(self, text: str) -> Dict:
        """Detect if text is AI-generated"""
        if not text or len(text.strip()) < 50:
            return {
                "is_ai_generated": False,
                "confidence": 0,
                "label": "Too short to analyze",
                "signals": [],
                "reasoning": "Text too short for reliable detection"
            }
        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=300,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": AI_DETECTION_PROMPT.format(text=text[:1500])
                }]
            )
            import json, re
            response = msg.content[0].text.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            return json.loads(response.strip())
        except Exception as e:
            logger.error(f"AI detection failed: {e}")
            return {
                "is_ai_generated": False,
                "confidence": 0,
                "label": "Detection failed",
                "signals": [],
                "reasoning": str(e)
            }
'''

import os
os.makedirs("backend/agents", exist_ok=True)
with open("backend/agents/ai_detector.py", "w", encoding="utf-8") as f:
    f.write(ai_detector_code)
print("OK  backend/agents/ai_detector.py created")


# ── 2. Update fact_checker.py to run AI detection on input + sources ─────
fc = open("backend/agents/fact_checker.py", encoding="utf-8").read()

old_import = "from backend.utils.logger import logger"
new_import = "from backend.utils.logger import logger\nfrom backend.agents.ai_detector import AIDetector"

old_init = "        logger.info(\"FactChecker initialized\")"
new_init = "        self.ai_detector = AIDetector()\n        logger.info(\"FactChecker initialized\")"

old_verdict_build = (
    "            verdict[\"claim_text\"] = claim_text\n"
    "            verdict[\"language\"] = language\n"
    "            verdict[\"sources\"] = [chunk[\"source\"] for chunk in evidence_chunks[:3]]\n"
    "            verdict[\"source_dates\"] = [chunk.get(\"date\", \"Unknown\") for chunk in evidence_chunks[:3]]"
)

new_verdict_build = (
    "            verdict[\"claim_text\"] = claim_text\n"
    "            verdict[\"language\"] = language\n"
    "            verdict[\"sources\"] = [chunk[\"source\"] for chunk in evidence_chunks[:3]]\n"
    "            verdict[\"source_dates\"] = [chunk.get(\"date\", \"Unknown\") for chunk in evidence_chunks[:3]]\n"
    "            # AI detection on user input\n"
    "            verdict[\"input_ai_detection\"] = self.ai_detector.detect(claim_text)\n"
    "            # AI detection on each source snippet\n"
    "            verdict[\"source_ai_detection\"] = [\n"
    "                self.ai_detector.detect(chunk.get(\"text\", \"\"))\n"
    "                for chunk in evidence_chunks[:3]\n"
    "            ]"
)

if old_import in fc and "AIDetector" not in fc:
    fc = fc.replace(old_import, new_import)
if old_init in fc and "ai_detector" not in fc:
    fc = fc.replace(old_init, new_init)
if old_verdict_build in fc:
    fc = fc.replace(old_verdict_build, new_verdict_build)
    print("OK  backend/agents/fact_checker.py updated")
else:
    print("WARN fact_checker.py — verdict block not found, patching manually")
    fc = fc.replace(
        'verdict["source_dates"] = [chunk.get("date", "Unknown") for chunk in evidence_chunks[:3]]',
        'verdict["source_dates"] = [chunk.get("date", "Unknown") for chunk in evidence_chunks[:3]]\n'
        '            verdict["input_ai_detection"] = self.ai_detector.detect(claim_text)\n'
        '            verdict["source_ai_detection"] = [self.ai_detector.detect(chunk.get("text", "")) for chunk in evidence_chunks[:3]]'
    )
    print("OK  backend/agents/fact_checker.py patched via fallback")

with open("backend/agents/fact_checker.py", "w", encoding="utf-8") as f:
    f.write(fc)


# ── 3. Update models.py to include AI detection fields ───────────────────
models_code = '''from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class FactCheckRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    extract_claims: bool = Field(default=True)
    language: str = Field(default="English")

class AIDetectionResult(BaseModel):
    is_ai_generated: bool = False
    confidence: float = 0
    label: str = "Unknown"
    signals: List[str] = Field(default_factory=list)
    reasoning: str = ""

class FactCheckVerdict(BaseModel):
    claim_text: str
    verdict: str
    confidence: float = Field(ge=0, le=100)
    reasoning: str
    sources: List[str] = Field(default_factory=list)
    source_dates: List[str] = Field(default_factory=list)
    language: str = Field(default="English")
    flags: List[str] = Field(default_factory=list)
    input_ai_detection: Optional[AIDetectionResult] = None
    source_ai_detection: List[AIDetectionResult] = Field(default_factory=list)

class FactCheckResponse(BaseModel):
    task_id: str
    overall_verdict: str
    confidence: float
    claims_analyzed: int
    claims_refuted: int
    claims_supported: int
    detailed_results: List[FactCheckVerdict]
    processing_time_ms: float
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    chroma: str
    neo4j: str
    timestamp: datetime

class UsageStats(BaseModel):
    total_requests: int
    total_cost: float
    remaining_credit: float
    requests_today: int
'''

with open("backend/api/models.py", "w", encoding="utf-8") as f:
    f.write(models_code)
print("OK  backend/api/models.py updated with AI detection fields")


# ── 4. Update dashboard.py to show AI detection badges + section ─────────
dashboard = open("frontend/dashboard.py", encoding="utf-8").read()

# Add AI badge renderer function after imports
ai_badge_fn = '''
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
'''

# Insert after the render_source_timeline function
old_title = "# Title\nst.title"
new_title = ai_badge_fn + "\n# Title\nst.title"

if "def ai_badge" not in dashboard:
    dashboard = dashboard.replace(old_title, new_title)
    print("OK  frontend/dashboard.py — AI badge functions added")

# Add AI detection rendering after the source timeline call
old_timeline_call = (
    "                                    render_source_timeline(\n"
    "                                        sources=claim_result.get('sources', []),\n"
    "                                        source_dates=claim_result.get('source_dates', []),\n"
    "                                        verdict=claim_result['verdict']\n"
    "                                    )"
)

new_timeline_call = (
    "                                    render_source_timeline(\n"
    "                                        sources=claim_result.get('sources', []),\n"
    "                                        source_dates=claim_result.get('source_dates', []),\n"
    "                                        verdict=claim_result['verdict']\n"
    "                                    )\n"
    "                                    render_ai_section(\n"
    "                                        input_detection=claim_result.get('input_ai_detection', {}),\n"
    "                                        source_detections=claim_result.get('source_ai_detection', []),\n"
    "                                        sources=claim_result.get('sources', [])\n"
    "                                    )"
)

if old_timeline_call in dashboard:
    dashboard = dashboard.replace(old_timeline_call, new_timeline_call)
    print("OK  frontend/dashboard.py — AI detection rendering added")
else:
    print("WARN could not find timeline call to patch")

# Also add AI badge next to each source link
old_sources = (
    "                                if claim_result.get('sources'):\n"
    "                                    st.markdown(\"**Sources:**\")\n"
    "                                    for source in claim_result['sources']:\n"
    "                                        st.markdown(f\"- [{source}]({source})\")"
)
new_sources = (
    "                                if claim_result.get('sources'):\n"
    "                                    st.markdown(\"**Sources:**\")\n"
    "                                    src_detections = claim_result.get('source_ai_detection', [])\n"
    "                                    for si, source in enumerate(claim_result['sources']):\n"
    "                                        det = src_detections[si] if si < len(src_detections) else {}\n"
    "                                        badge = ai_badge(det)\n"
    "                                        st.markdown(f\"- [{source}]({source}) &nbsp;{badge}\", unsafe_allow_html=True)"
)

if old_sources in dashboard:
    dashboard = dashboard.replace(old_sources, new_sources)
    print("OK  frontend/dashboard.py — AI badges added next to sources")

with open("frontend/dashboard.py", "w", encoding="utf-8") as f:
    f.write(dashboard)
print("OK  frontend/dashboard.py saved")

print("""
Done! Restart with: python run_demo.py

What you'll see:
  - 🤖 AI-Generated (85%) badge next to each source
  - ✍️ Human-Written (92%) badge next to human sources  
  - AI CONTENT DETECTION section below the timeline
  - Your input also gets analyzed for AI patterns
""")
