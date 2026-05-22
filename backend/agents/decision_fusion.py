"""
Decision Fusion Engine — Media-Free Build
==========================================
Fuses: identity (0.35), cv_claims (0.30), consistency (0.35), text_ai (0.15).
Media module fully removed.
"""
import random
from typing import Dict, List
from backend.agents.signal_normalizer import SignalObject
from backend.utils.logger import logger

_BASE_WEIGHTS = {
    "identity":    0.35,
    "cv_claims":   0.30,
    "text_ai":     0.15,
    "consistency": 0.35,
}

def _lean_to_numeric(lean): return {"authentic": 1.0, "synthetic": 0.0, "unknown": 0.5}.get(lean, 0.5)
def _jitter(lst): return random.choice(lst)

_CONF_PHRASES = {
    "high":   ["several independent signals align strongly", "multiple reliable indicators point in the same direction"],
    "medium": ["some signals are present but not conclusive", "evidence exists but is moderate or partially contradictory"],
    "low":    ["the evidence is weak or inconsistent", "the system could not gather enough information for a firm assessment"],
}


def fuse_signals(signals: Dict[str, SignalObject]) -> Dict:
    contributing = {n: s for n, s in signals.items() if s.contributing and s.strength > 0.15}
    if len(contributing) < 2:
        return _insufficient_data("Not enough independent modules provided useful information.")

    avg_strength = sum(s.strength for s in contributing.values()) / len(contributing)
    if avg_strength < 0.25:
        return _insufficient_data("Available signals are too faint for a meaningful assessment.")

    total_weight = sum(_BASE_WEIGHTS.get(n, 0.0) for n in contributing)
    if total_weight == 0:
        return _insufficient_data("Weight configuration error.")

    weighted_sum, lean_values, detailed = 0.0, {}, {}
    for name, sig in contributing.items():
        w = _BASE_WEIGHTS[name] / total_weight
        weighted_sum += w * _lean_to_numeric(sig.lean) * sig.strength
        lean_values[name]  = sig.lean
        detailed[name]     = sig.to_dict()

    posterior = weighted_sum
    leans     = list(lean_values.values())
    conflict  = "authentic" in leans and "synthetic" in leans

    if "synthetic" in leans:
        strong = max((s.strength for s in contributing.values() if s.lean == "synthetic"), default=0)
        if strong > 0.5:
            posterior = min(posterior, 0.35)

    category, conf_level = _categorize(posterior, leans, conflict, len(contributing))
    conf_reason = _build_confidence_reason(conf_level, len(contributing), avg_strength, conflict)
    explanation, warnings = _build_explanation(category, conf_level, detailed, conflict)

    return {
        "decision":          category,
        "confidence_level":  conf_level,
        "confidence_reason": conf_reason,
        "explanation":       explanation,
        "warnings":          warnings,
        "methodology":       "Weighted Bayesian fusion: identity(0.35) + cv_claims(0.30) + consistency(0.35). Media module not present.",
    }


def _categorize(posterior, leans, conflict, n):
    if posterior >= 0.70:
        cat = "Likely Authentic"
        cl  = "high" if posterior >= 0.80 and n >= 2 else "medium"
    elif posterior <= 0.35:
        cat = "Likely Synthetic"
        cl  = "high" if posterior <= 0.20 and n >= 2 else "medium"
    else:
        cat = "Uncertain"
        cl  = "medium" if abs(posterior - 0.5) >= 0.10 else "low"
    if conflict:
        cl = "medium" if cl == "high" else ("low" if cl == "medium" else "low")
    if n < 2 and cl != "low":
        cl = "low"
    return cat, cl


def _build_confidence_reason(cl, n, avg, conflict):
    desc = "strong" if avg > 0.6 else ("moderate" if avg > 0.3 else "weak")
    base = _jitter(_CONF_PHRASES[cl])
    parts = [f"{n} module(s) contributed", f"average signal strength is {desc}"]
    if conflict: parts.append("modules disagree, lowering confidence")
    return base + " (" + ", ".join(parts) + ")."


def _build_explanation(category, confidence, signals, conflict):
    warnings, paragraphs = [], []

    identity = signals.get("identity")
    if identity and identity.get("contributing"):
        lean = identity["lean"]
        if lean == "authentic":
            paragraphs.append("Identity verification supports the provided information.")
        elif lean == "synthetic":
            paragraphs.append("Identity analysis suggests possible fabrication of personal details.")
            key = identity.get("key_signals",[])
            if key: paragraphs.append(f"Signals: {', '.join(key[:3])}.")
        else:
            paragraphs.append("Identity evidence is insufficient to draw conclusions.")

    cv = signals.get("cv_claims")
    if cv and cv.get("contributing"):
        er = cv.get("strength", 0)
        if er > 0.6:   paragraphs.append("Most CV claims have supporting web evidence.")
        elif er > 0.3: paragraphs.append("Some CV claims verified, but others lack evidence.")
        else:          paragraphs.append("Few CV claims could be corroborated by external sources.")

    consistency = signals.get("consistency")
    if consistency and consistency.get("contributing"):
        if "conflicting claims detected" in consistency.get("key_signals",[]):
            paragraphs.append("Consistency analysis found contradictions between the CV and public profiles.")
            warnings.append("CV claims conflict with found profile data – human review advised.")
        else:
            paragraphs.append("No major inconsistencies found in the CV claims.")

    text = signals.get("text_ai")
    if text and text.get("contributing"):
        if text["lean"] == "synthetic":
            paragraphs.append("Text analysis found AI writing patterns.")
            key = text.get("key_signals",[])
            if key: paragraphs.append(f"Indicators: {', '.join(key[:2])}.")

    if conflict:
        warnings.insert(0, "Conflicting signals across modules – confidence reduced.")

    paragraphs.append("This assessment is probabilistic and should be used as decision support, not a final verdict.")
    return " ".join(paragraphs), warnings


def _insufficient_data(reason):
    return {
        "decision": "Insufficient Data", "confidence_level": "low",
        "confidence_reason": "Not enough reliable evidence.",
        "explanation": reason, "warnings": ["System could not perform full analysis."],
        "methodology": "Multi-modal fusion — insufficient signals. Media not present in this build.",
    }
