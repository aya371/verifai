"""
signal_normalizer.py — Standardized signal objects for cross-module fusion.
Media module fully removed. Fuses: identity, cv_claims, consistency, text_ai, factcheck.
"""
from typing import Dict, Optional


class SignalObject:
    def __init__(self, lean: str, strength: float, contributing: bool,
                 key_signals: Optional[list] = None, details: Optional[Dict] = None, error: Optional[str] = None):
        self.lean         = lean
        self.strength     = min(1.0, max(0.0, strength))
        self.contributing = contributing
        self.key_signals  = key_signals or []
        self.details      = details or {}
        self.error        = error

    def to_dict(self) -> Dict:
        return {"lean": self.lean, "strength": self.strength, "contributing": self.contributing,
                "key_signals": self.key_signals, "details": self.details, "error": self.error}


def normalize_ai_detection(ai_result: Dict) -> SignalObject:
    if not ai_result or ai_result.get("label") == "Too short to analyze":
        return SignalObject("unknown", 0.0, False)
    is_ai = ai_result.get("is_ai_generated", False)
    conf  = ai_result.get("confidence", 0) / 100.0
    lean  = "synthetic" if is_ai and conf > 0.6 else ("authentic" if not is_ai and conf > 0.6 else "unknown")
    return SignalObject(lean, conf, True, key_signals=ai_result.get("signals", [])[:3])


def normalize_identity(confidence_summary: Dict) -> SignalObject:
    if not confidence_summary:
        return SignalObject("unknown", 0.0, False)
    id_conf = confidence_summary.get("identity_confidence", 0.5)
    lean    = "authentic" if id_conf > 0.7 else ("synthetic" if id_conf < 0.3 else "unknown")
    signals = ["high identity confidence"] if id_conf > 0.7 else (["low identity confidence"] if id_conf < 0.3 else [])
    return SignalObject(lean, id_conf, True, key_signals=signals, details=confidence_summary)


def normalize_consistency(consistency_data: Dict) -> SignalObject:
    if not consistency_data or consistency_data.get("not_applicable"):
        return SignalObject("unknown", 0.0, False)
    score = consistency_data.get("consistency_score", None)
    if score is None:
        return SignalObject("unknown", 0.0, False)
    norm    = score / 100.0
    lean    = "authentic" if norm > 0.6 else ("synthetic" if norm < 0.4 else "unknown")
    signals = []
    if consistency_data.get("consistent"):   signals.append("CV claims match profile data")
    if consistency_data.get("inconsistent"): signals.append("conflicting claims detected")
    return SignalObject(lean, norm, True, key_signals=signals)


def normalize_cv_claims(claims_analysis: list) -> SignalObject:
    if not claims_analysis:
        return SignalObject("unknown", 0.0, False)
    high   = sum(1 for c in claims_analysis if c.get("confidence") == "high")
    medium = sum(1 for c in claims_analysis if c.get("confidence") == "medium")
    total  = len(claims_analysis)
    ratio  = (high * 1.0 + medium * 0.5) / total if total else 0
    lean   = "authentic" if ratio > 0.5 else ("synthetic" if ratio < 0.3 else "unknown")
    return SignalObject(lean, ratio, True, key_signals=[f"{high} strong evidence claims"])


def normalize_factcheck(factcheck_aggregate: Dict) -> SignalObject:
    if not factcheck_aggregate:
        return SignalObject("unknown", 0.0, False)
    verdict    = factcheck_aggregate.get("overall_verdict", "INCONCLUSIVE")
    confidence = factcheck_aggregate.get("confidence", 0) / 100.0
    true_v  = ["COMPLETELY TRUE", "MOSTLY TRUE", "SUPPORTED"]
    false_v = ["COMPLETELY FALSE", "MOSTLY FALSE", "REFUTED"]
    lean = "authentic" if verdict in true_v else ("synthetic" if verdict in false_v else "unknown")
    key_signals = [f"Overall verdict: {verdict}", f"{factcheck_aggregate.get('claims_analyzed', 0)} claims checked"]
    if factcheck_aggregate.get("claims_refuted", 0) > 0:
        key_signals.append(f"{factcheck_aggregate['claims_refuted']} claim(s) refuted")
    return SignalObject(lean, min(1.0, max(0.0, confidence)), True, key_signals=key_signals)
