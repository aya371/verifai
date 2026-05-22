"""
Identity Consistency Analyzer — Bayesian claim-profile comparison
Save to: backend/agents/consistency_analyzer.py

Methodology:
- Each claim classified as consistent/inconsistent/unknown
  by Claude based on found profile evidence
- Consistency score computed as Bayesian posterior:
  P(identity_consistent | evidence) using ENFSI LR framework
- Never labels claims as "lies" or "true" — only as consistent or not

References:
- ENFSI Guideline for Evaluative Reporting (2015)
- Fellegi & Sunter (1969) "A Theory for Record Linkage"
- Aitken & Taroni (2004) "Statistics and the Evaluation of Evidence"
"""
import json
import re
from typing import Dict, List, Tuple
from anthropic import Anthropic
from config import config
from backend.utils.logger import logger

# Bayesian prior: P(claims_consistent) = 0.5 (uninformative)
PRIOR_CONSISTENT = 0.5

# ENFSI LR values for consistency evidence
LR_CONSISTENT   = 9.0    # finding consistent evidence: LR=9 (moderate per ENFSI)
LR_INCONSISTENT = 0.10   # finding contradiction: LR=0.1 (strong against)
LR_UNKNOWN      = 1.0    # no information: LR=1 (neutral, no update)


def _bayesian_update(prior: float, lr: float) -> float:
    p0 = 1.0 - prior
    return (lr * prior) / (lr * prior + p0)


class ConsistencyAnalyzer:
    """
    Compares CV claims against candidate profile data.
    Returns consistent/inconsistent/unknown lists with
    Bayesian posterior consistency score.
    """

    def __init__(self):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        logger.info("ConsistencyAnalyzer initialized")

    def analyze(self, claims: List[Dict], candidates: List[Dict],
                 original_text: str = "") -> Dict:
        if not claims:
            return self._empty_result("No claims to analyze.")
        if not candidates:
            return self._empty_result("No candidate profiles to compare against.")

        top_candidate = candidates[0]
        profile_text  = self._candidate_to_text(top_candidate)
        result        = self._compare(claims, profile_text, original_text)

        # Bayesian posterior consistency score
        posterior = self._bayesian_consistency_score(result)

        return {
            "compared_against": {
                "name":     top_candidate.get("name","Unknown"),
                "url":      top_candidate.get("profile_url",""),
                "score":    top_candidate.get("similarity_score", 0),
                "fs_posterior": top_candidate.get("fs_posterior", 0),
            },
            "consistent":         result["consistent"],
            "inconsistent":       result["inconsistent"],
            "unknown":            result["unknown"],
            "consistency_score":  int(posterior * 100),   # 0-100 integer
            "consistency_posterior": round(posterior, 3), # 0.0-1.0
            "consistency_lr":     round(self._combined_lr(result), 2),
            "methodology":        (
                "Consistency score computed via Bayesian updating "
                "(ENFSI 2015). Each consistent claim applies LR=9 "
                "(moderate support), each inconsistency applies LR=0.1 "
                "(strong against), unknown claims are neutral (LR=1). "
                "Prior P(consistent)=0.5 per Aitken & Taroni (2004)."
            ),
            "note": (
                "Inconsistency means the claim conflicts with found profile data. "
                "It does not mean the claim is false — profile data may be incomplete."
            ),
        }

    def _compare(self, claims: List[Dict], profile_text: str,
                  original_text: str) -> Dict:
        claims_text = "\n".join([
            f"- [{c.get('type','?')}] {c.get('claim','')}"
            for c in claims
        ])

        prompt = f"""You are a forensic identity analyst. Compare these CV claims against found profile data.
Be strict and precise. Your job is to detect contradictions, not to give the benefit of the doubt.

CLAIMS FROM CV/INPUT:
{claims_text}

FOUND PROFILE DATA (from web sources):
{profile_text[:2000]}

CLASSIFICATION RULES — apply strictly:

"consistent" — use ONLY when profile data clearly supports the claim:
  ✓ Profile says "Software Engineer at Google" — claim says "Engineer at Google" → consistent
  ✓ Profile mentions the same university — claim mentions that university → consistent

"inconsistent" — use when profile data contradicts OR significantly differs from the claim:
  ✗ Profile says "CEO at Tesla" — claim says "Junior Developer" → inconsistent (role mismatch)
  ✗ Profile says "University of Pennsylvania" — claim says "AUST Lebanon" → inconsistent (education mismatch)
  ✗ Profile says "Based in USA" — claim says "Based in Beirut" → inconsistent (location mismatch)
  ✗ Profile clearly shows a different employer — claim shows another employer → inconsistent
  ✗ Profile shows a well-known public figure with a different background — claim doesn't match → inconsistent
  IMPORTANT: Do NOT mark as "unknown" when the profile clearly shows something DIFFERENT.
  A clear mismatch is "inconsistent", not "unknown".

"unknown" — use ONLY when the profile has NO information about that specific claim:
  ? Profile has no mention of certifications — claim mentions a certification → unknown
  ? Profile has no dates — claim has specific employment dates → unknown

CRITICAL: If the profile belongs to a well-known person (public figure, executive, professor)
and the CV claim contradicts their known role, organization, or location — mark as INCONSISTENT.

Return ONLY a JSON object:
{{
  "consistent": [{{"claim": "...", "reason": "what in the profile supports this"}}],
  "inconsistent": [{{"claim": "...", "reason": "specific contradiction found", "conflict": "what the profile actually shows"}}],
  "unknown": [{{"claim": "...", "reason": "profile has no data on this"}}]
}}"""

        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=1500,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = msg.content[0].text.strip()
            raw = re.sub(r'^```json\s*','',raw)
            raw = re.sub(r'\s*```$','',raw)
            return json.loads(raw)
        except Exception as e:
            logger.error(f"Consistency comparison failed: {e}")
            return {
                "consistent":   [],
                "inconsistent": [],
                "unknown":      [{"claim": c.get("claim",""), "reason": "Analysis error"}
                                  for c in claims]
            }

    def _bayesian_consistency_score(self, result: Dict) -> float:
        """
        Compute posterior P(identity_consistent | evidence) via
        iterative Bayesian updating per ENFSI (2015) LR framework.
        """
        posterior = PRIOR_CONSISTENT
        for _ in result.get("consistent", []):
            posterior = _bayesian_update(posterior, LR_CONSISTENT)
        for _ in result.get("inconsistent", []):
            posterior = _bayesian_update(posterior, LR_INCONSISTENT)
        # Unknown claims: LR=1, no update needed
        return round(max(0.0, min(1.0, posterior)), 3)

    def _combined_lr(self, result: Dict) -> float:
        lr = 1.0
        for _ in result.get("consistent", []):
            lr *= LR_CONSISTENT
        for _ in result.get("inconsistent", []):
            lr *= LR_INCONSISTENT
        return lr

    def _candidate_to_text(self, candidate: Dict) -> str:
        parts = []
        if candidate.get("name"):
            parts.append(f"Name: {candidate['name']}")
        if candidate.get("extracted_info"):
            parts.append(f"Info: {candidate['extracted_info']}")
        if candidate.get("match_explanation"):
            parts.append(f"Context: {candidate['match_explanation']}")
        if candidate.get("profile_url"):
            parts.append(f"Source: {candidate['profile_url']}")
        return "\n".join(parts)

    def _empty_result(self, reason: str) -> Dict:
        # consistency_score=None signals "not applicable" to the orchestrator.
        # This prevents the default 50 from silently appearing in scoring
        # when no CV was provided or no candidates were found.
        return {
            "compared_against":       {},
            "consistent":             [],
            "inconsistent":           [],
            "unknown":                [],
            "consistency_score":      None,   # None = not applicable, not 50%
            "consistency_posterior":  None,
            "consistency_lr":         1.0,
            "not_applicable":         True,
            "note":                   reason,
        }
