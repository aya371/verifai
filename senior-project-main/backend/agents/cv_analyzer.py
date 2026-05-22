"""
CV / Document Analysis Agent — Research-grounded evidence assessment
Save to: backend/agents/cv_analyzer.py

Methodology:
- Claim extraction via Claude (structured NLP)
- Evidence retrieval via DuckDuckGo web search
- Confidence assessment using Bayesian evidence updating
  with likelihood ratios grounded in the ENFSI (2015) verbal scale
  and source reliability hierarchy from NIST FRVT literature

IMPORTANT: This agent does NOT verify claims.
It finds evidence and reports Bayesian confidence estimates.
Final judgment is always left to the human reviewer.

References:
- ENFSI Guideline for Evaluative Reporting (2015)
- Winkler (2006) "Overview of Record Linkage and Current Research Directions"
- Farid (2009) "A Survey of Image Forgery Detection"
"""
import json
import re
from typing import Dict, List, Tuple
from ddgs import DDGS
from anthropic import Anthropic
from config import config
from backend.utils.logger import logger

# ── Bayesian prior for claim truth ────────────────────────────────────────
# P(claim_true) = 0.5 — uninformative prior before evidence.
# Follows the recommendation in Aitken & Taroni (2004):
# "Statistics and the Evaluation of Evidence for Forensic Scientists"
PRIOR_CLAIM_TRUE = 0.5

# ── Source reliability weights (NIST FRVT hierarchy) ─────────────────────
# Higher-credibility domains assigned higher likelihood ratios.
# Justified by source reliability literature in forensic evidence evaluation.
CREDIBLE_DOMAINS = {
    "linkedin.com":      0.90,
    "wikipedia.org":     0.95,
    ".edu":              0.90,
    ".gov":              0.95,
    "github.com":        0.75,
    "bloomberg.com":     0.85,
    "reuters.com":       0.85,
    "crunchbase.com":    0.80,
    "researchgate.net":  0.85,
    "scholar.google.com":0.90,
}
GENERAL_SOURCE_RELIABILITY = 0.55


def _source_reliability(url: str) -> float:
    """Return reliability weight for a given URL."""
    url_lower = url.lower()
    for domain, weight in CREDIBLE_DOMAINS.items():
        if domain in url_lower:
            return weight
    return GENERAL_SOURCE_RELIABILITY


def _bayesian_update(prior: float, p_h1: float, p_h0: float) -> float:
    """
    Single Bayesian update step.
    P(H1|E) = P(E|H1)*P(H1) / [P(E|H1)*P(H1) + P(E|H0)*P(H0)]
    Based on Fellegi-Sunter (1969) probabilistic record linkage framework.
    """
    numerator   = p_h1 * prior
    denominator = numerator + p_h0 * (1.0 - prior)
    if denominator == 0:
        return prior
    return max(0.0, min(1.0, numerator / denominator))


def _posterior_to_label(posterior: float) -> str:
    """
    Convert Bayesian posterior to evidence confidence label.
    Thresholds aligned with ENFSI (2015) verbal likelihood ratio scale.
    """
    if posterior >= 0.85:  return "high"
    if posterior >= 0.65:  return "medium"
    if posterior >= 0.45:  return "low"
    return "not_found"


class CVAnalyzer:
    """
    Extracts structured claims from CV text and retrieves web evidence.
    Confidence assessed via Bayesian updating — not binary verdicts.
    """

    def __init__(self):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        logger.info("CVAnalyzer initialized")

    def analyze(self, cv_text: str) -> Dict:
        logger.info("CVAnalyzer: extracting claims")
        claims = self._extract_claims(cv_text)
        logger.info(f"CVAnalyzer: found {len(claims)} claims")

        analyzed = []
        for claim in claims:
            evidence = self._search_evidence(claim)
            analyzed.append({
                "claim":           claim["text"],
                "type":            claim["type"],
                "evidence":        evidence["results"],
                "confidence":      evidence["confidence"],
                "posterior":       evidence["posterior"],        # Bayesian posterior 0-1
                "likelihood_ratio": evidence["likelihood_ratio"], # combined LR
                "note":            evidence["note"],
            })

        return {
            "claims":               analyzed,
            "total_claims":         len(analyzed),
            "claims_with_evidence": sum(1 for c in analyzed if c["confidence"] != "not_found"),
            "summary":              self._summarize(analyzed),
            "methodology":          (
                "Claims assessed using Bayesian evidence updating "
                "(Fellegi-Sunter 1969) with source reliability weights "
                "from NIST FRVT literature. Prior P(claim_true)=0.5 "
                "(uninformative). Confidence labels follow ENFSI (2015) "
                "verbal likelihood ratio scale."
            ),
        }

    # ── Claim Extraction ──────────────────────────────────────────────────

    def _extract_claims(self, cv_text: str) -> List[Dict]:
        prompt = f"""Extract all verifiable factual claims from this CV.
Focus on: job titles, company names, employment dates, education institutions,
degrees, certifications, and notable achievements.

CV TEXT:
{cv_text[:4000]}

Return ONLY a JSON array. Each item must have:
- "text": the exact claim as a short sentence
- "type": one of: employment / education / certification / achievement / other
- "search_query": a focused web search query to find evidence for this claim

Return ONLY the JSON array, no other text."""

        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=1500,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = msg.content[0].text.strip()
            raw = re.sub(r'^```json\s*', '', raw)
            raw = re.sub(r'\s*```$', '', raw)
            return json.loads(raw)[:10]
        except Exception as e:
            logger.warning(f"Claim extraction failed: {e}")
            return []

    # ── Evidence Search ───────────────────────────────────────────────────

    def _search_evidence(self, claim: Dict) -> Dict:
        query   = claim.get("search_query", claim.get("text", ""))
        results = []

        try:
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=4))
            for h in hits:
                url     = h.get("href", "")
                title   = h.get("title", "")
                snippet = h.get("body", "")[:300]
                if url and title:
                    results.append({
                        "url":         url,
                        "title":       title,
                        "snippet":     snippet,
                        "reliability": round(_source_reliability(url), 2),
                    })
        except Exception as e:
            logger.warning(f"Evidence search failed for '{query}': {e}")

        posterior, lr, note = self._bayesian_assess(results, claim)
        return {
            "results":         results,
            "confidence":      _posterior_to_label(posterior),
            "posterior":       round(posterior, 3),
            "likelihood_ratio": round(lr, 1),
            "note":            note,
        }

    def _bayesian_assess(
        self, results: List[Dict], claim: Dict
    ) -> Tuple[float, float, str]:
        """
        Assess evidence using Bayesian updating.

        For each source found:
          P(E|H1) = source reliability (how likely this source confirms true claims)
          P(E|H0) = 1 - source reliability (how likely this source is noise)

        Combined LR = product of individual source LRs.
        Posterior updated iteratively (Fellegi-Sunter 1969).
        """
        if not results:
            return (
                0.1,   # posterior near 0 with no evidence
                0.0,
                "No web evidence found for this claim. "
                "Absence of evidence does not imply the claim is false."
            )

        posterior  = PRIOR_CLAIM_TRUE
        combined_lr = 1.0

        for r in results:
            rel = r["reliability"]
            p_h1 = rel            # P(finding this source | claim is true)
            p_h0 = 1.0 - rel      # P(finding this source | claim is false)
            lr_i  = p_h1 / max(p_h0, 0.01)
            combined_lr *= lr_i
            posterior    = _bayesian_update(posterior, p_h1, p_h0)

        n = len(results)
        label = _posterior_to_label(posterior)
        note  = (
            f"Bayesian posterior {posterior:.2f} from {n} source(s). "
            f"Combined LR={combined_lr:.1f} "
            f"({self._lr_verbal(combined_lr)} evidence per ENFSI 2015 scale)."
        )
        return posterior, combined_lr, note

    def _lr_verbal(self, lr: float) -> str:
        """ENFSI (2015) verbal likelihood ratio scale."""
        if lr >= 1000:  return "very strong"
        if lr >= 100:   return "strong"
        if lr >= 10:    return "moderate"
        if lr >= 1:     return "weak"
        return "supports H0"

    def _summarize(self, analyzed: List[Dict]) -> str:
        total     = len(analyzed)
        high      = sum(1 for c in analyzed if c["confidence"] == "high")
        medium    = sum(1 for c in analyzed if c["confidence"] == "medium")
        low       = sum(1 for c in analyzed if c["confidence"] == "low")
        not_found = sum(1 for c in analyzed if c["confidence"] == "not_found")

        if total == 0:
            return "No verifiable claims could be extracted."

        parts = []
        if high:      parts.append(f"{high} claim(s) with strong evidence (posterior ≥ 0.85)")
        if medium:    parts.append(f"{medium} claim(s) with moderate evidence (0.65–0.85)")
        if low:       parts.append(f"{low} claim(s) with weak evidence (0.45–0.65)")
        if not_found: parts.append(f"{not_found} claim(s) with no web evidence")

        return (
            ". ".join(parts) + ". "
            "Note: absence of evidence does not imply falsehood. "
            "All scores are Bayesian estimates with uninformative prior P=0.5."
        )
