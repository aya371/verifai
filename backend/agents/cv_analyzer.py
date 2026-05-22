"""
CV / Document Analysis Agent — Document Verification Engine
============================================================
ENGINE 1 of VerifAI's two-engine architecture.

Purpose: Verify whether claims inside a CV are truthful.
         Starts from the DOCUMENT and works outward to the web.

Advanced features implemented:
  1. Forensic Timeline Auditor   — date overlap & gap detection
  2. Proof-of-Work Validator     — GitHub / Scholar / arXiv artefact search
  3. Credential Inflation Detector — Claude rubric (0-10 risk score)
  4. Academic Credential Verifier — degree programme existence check
  5. Red Flag Dashboard Generator — structured risk aggregation
  6. Evidence Gallery             — source + snippet + matched text + credibility
  7. Claim Traceability           — claim → query → result → match logic

Methodology:
  Bayesian evidence updating (Fellegi-Sunter 1969, ENFSI 2015)
  Source reliability from NIST FRVT hierarchy
  Prior P(claim_true) = 0.5 (Aitken & Taroni 2004)
"""
import json
import re
from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from ddgs import DDGS
from anthropic import Anthropic
from config import config
from backend.utils.logger import logger

# ── Constants ─────────────────────────────────────────────────────────────
PRIOR_CLAIM_TRUE = 0.5

CREDIBLE_DOMAINS = {
    "linkedin.com":       0.90,
    "wikipedia.org":      0.95,
    ".edu":               0.90,
    ".gov":               0.95,
    "github.com":         0.75,
    "bloomberg.com":      0.85,
    "reuters.com":        0.85,
    "crunchbase.com":     0.80,
    "researchgate.net":   0.85,
    "scholar.google.com": 0.90,
    "arxiv.org":          0.88,
    "patents.google.com": 0.85,
    "stackoverflow.com":  0.70,
}
GENERAL_SOURCE_RELIABILITY = 0.55

DOMAIN_LABELS = {
    "linkedin.com":       ("LinkedIn",           "high"),
    "wikipedia.org":      ("Wikipedia",          "high"),
    ".edu":               ("Academic",           "high"),
    ".gov":               ("Government",         "high"),
    "github.com":         ("GitHub",             "medium-high"),
    "bloomberg.com":      ("Bloomberg",          "high"),
    "reuters.com":        ("Reuters",            "high"),
    "crunchbase.com":     ("Crunchbase",         "medium-high"),
    "researchgate.net":   ("ResearchGate",       "high"),
    "scholar.google.com": ("Google Scholar",     "high"),
    "arxiv.org":          ("arXiv",              "high"),
    "stackoverflow.com":  ("StackOverflow",      "medium"),
    "patents.google.com": ("Google Patents",     "high"),
}


def _source_reliability(url: str) -> float:
    for domain, weight in CREDIBLE_DOMAINS.items():
        if domain in url.lower():
            return weight
    return GENERAL_SOURCE_RELIABILITY


def _domain_label(url: str) -> Tuple[str, str]:
    """Return (source_name, credibility_tier) for a URL."""
    for domain, (name, tier) in DOMAIN_LABELS.items():
        if domain in url.lower():
            return name, tier
    return "Web Source", "low"


def _bayesian_update(prior: float, p_h1: float, p_h0: float) -> float:
    num = p_h1 * prior
    den = num + p_h0 * (1.0 - prior)
    return max(0.0, min(1.0, num / den)) if den else prior


def _posterior_to_label(p: float) -> str:
    if p >= 0.85: return "high"
    if p >= 0.65: return "medium"
    if p >= 0.45: return "low"
    return "not_found"


def _verdict_from_analysis(analyzed, context_signal, is_unrealistic, unrealistic_reason):
    total = len(analyzed)
    if total == 0:
        return "Unverified", 40, "No claims could be extracted for analysis."

    high   = sum(1 for c in analyzed if c["confidence"] == "high")
    medium = sum(1 for c in analyzed if c["confidence"] == "medium")
    low_ev = sum(1 for c in analyzed if c["confidence"] == "low")
    none   = sum(1 for c in analyzed if c["confidence"] == "not_found")
    source_contradictions = sum(
        1 for c in analyzed for e in c.get("evidence", [])
        if e.get("relevance", 1.0) <= 0.10
    )
    has_osint    = (high + medium) > 0
    evidence_pct = round(((high * 1.0 + medium * 0.5 + low_ev * 0.25) / total) * 100)
    strong_osint = high >= 2 or (high >= 1 and medium >= 1)

    if is_unrealistic:
        return "Likely Fake", 25, (
            f"{unrealistic_reason} The CV contains content that cannot reflect a real "
            "professional background. Result: Likely Fake — independent human review is mandatory."
        )
    if source_contradictions >= 2 and context_signal == "contradiction":
        return "Likely Fake", max(20, 35 - source_contradictions * 5), (
            f"Multiple contradictions detected ({source_contradictions}) and context misaligns. "
            "Result: Likely Fake — human review is mandatory."
        )
    if context_signal == "contradiction":
        return "Likely Inconsistent", max(35, 50 - source_contradictions * 5), (
            "The provided context does not align with the CV content. "
            "Result: Likely Inconsistent — human review is required."
        )
    if strong_osint and source_contradictions == 0:
        ctx_note = "Provided context aligns with CV data. " if context_signal == "match" else ""
        return "Likely Authentic", min(92, 60 + evidence_pct), (
            f"Strong external evidence found for {high + medium} claim(s). "
            f"{ctx_note}No contradictions detected. Result: Likely Authentic."
        )
    if context_signal == "match":
        internal = (total - none) / total if total else 0
        pct = min(65, 55 + int(internal * 10))
        return "Authenticity Unverified (Leaning Positive)", pct, (
            "No public records found but context aligns with CV claims. "
            "Result: Authenticity Unverified (Leaning Positive)."
        )
    if has_osint and context_signal == "neutral":
        return "Authenticity Unverified (Leaning Positive)", min(65, 50 + evidence_pct), (
            f"Partial evidence found ({high + medium} claim(s)). "
            "Result: Authenticity Unverified (Leaning Positive)."
        )
    internal = "appears internally coherent" if none < total // 2 else "has unverifiable claims"
    return "Unverified", max(40, min(50, evidence_pct + 40)), (
        f"No public records found. No context provided. CV {internal}. "
        "Result: Unverified — neutral finding."
    )


# ═══════════════════════════════════════════════════════════════════════════
# FORENSIC TIMELINE AUDITOR
# ═══════════════════════════════════════════════════════════════════════════

class ForensicTimelineAuditor:
    """
    Extracts all dated entries from a CV and detects temporal impossibilities.
    Pure Python datetime arithmetic — no external calls.
    """

    MONTH_MAP = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
        "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
        "january": 1, "february": 2, "march": 3, "april": 4,
        "june": 6, "july": 7, "august": 8, "september": 9,
        "october": 10, "november": 11, "december": 12,
    }

    def audit(self, cv_text: str, claude_client) -> Dict:
        """Extract timeline events via Claude, then run arithmetic checks."""
        events    = self._extract_events(cv_text, claude_client)
        flags     = self._detect_issues(events, cv_text)
        age_check = self._check_age_consistency(events, cv_text)
        gaps      = self._detect_gaps(events)
        return {
            "timeline":       events,
            "flags":          flags + age_check,
            "gaps":           gaps,
            "total_flags":    len(flags) + len(age_check),
            "methodology":    "Datetime arithmetic on Claude-extracted dates. No LLM inference used for flags.",
        }

    def _extract_events(self, cv_text: str, client) -> List[Dict]:
        prompt = f"""Extract all dated career/education events from this CV.
For each entry return:
- "event": short description (max 60 chars)
- "type": "education" | "employment" | "certification" | "other"
- "start_year": integer or null
- "start_month": integer 1-12 or null
- "end_year": integer or null  (use 9999 for "present"/"current")
- "end_month": integer 1-12 or null (use 12 for "present")
- "organization": institution or company name

CV:
{cv_text[:3000]}

Return ONLY a JSON array. Return [] if no dated entries found."""
        try:
            msg = client.messages.create(
                model=config.CLAUDE_MODEL, max_tokens=1500, temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = re.sub(r'^```json\s*', '', msg.content[0].text.strip())
            raw = re.sub(r'\s*```$', '', raw)
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Timeline extraction failed: {e}")
            return []

    def _to_date(self, year: Optional[int], month: Optional[int]) -> Optional[date]:
        if not year:
            return None
        y = min(year, date.today().year + 1)
        m = month or 1
        return date(y, m, 1)

    def _detect_issues(self, events: List[Dict], cv_text: str) -> List[Dict]:
        flags = []
        employments = [e for e in events if e.get("type") == "employment"]
        educations  = [e for e in events if e.get("type") == "education"]

        # Check employment overlaps
        for i in range(len(employments)):
            for j in range(i + 1, len(employments)):
                a, b = employments[i], employments[j]
                a_start = self._to_date(a.get("start_year"), a.get("start_month"))
                a_end   = self._to_date(a.get("end_year", 9999), a.get("end_month", 12))
                b_start = self._to_date(b.get("start_year"), b.get("start_month"))
                b_end   = self._to_date(b.get("end_year", 9999), b.get("end_month", 12))
                if not all([a_start, a_end, b_start, b_end]):
                    continue
                overlap_start = max(a_start, b_start)
                overlap_end   = min(a_end, b_end)
                if overlap_start < overlap_end:
                    months = (overlap_end.year - overlap_start.year) * 12 + (overlap_end.month - overlap_start.month)
                    if months >= 4:
                        flags.append({
                            "type":     "EMPLOYMENT_OVERLAP",
                            "severity": "medium" if months < 12 else "high",
                            "detail":   f"Employment overlap of {months} months: '{a.get('event','?')}' and '{b.get('event','?')}'",
                            "months":   months,
                        })

        # Check education vs employment overlaps
        for edu in educations:
            for emp in employments:
                e_start = self._to_date(edu.get("start_year"), edu.get("start_month"))
                e_end   = self._to_date(edu.get("end_year", 9999), edu.get("end_month", 12))
                w_start = self._to_date(emp.get("start_year"), emp.get("start_month"))
                w_end   = self._to_date(emp.get("end_year", 9999), emp.get("end_month", 12))
                if not all([e_start, e_end, w_start, w_end]):
                    continue
                overlap_start = max(e_start, w_start)
                overlap_end   = min(e_end, w_end)
                if overlap_start < overlap_end:
                    months = (overlap_end.year - overlap_start.year) * 12 + (overlap_end.month - overlap_start.month)
                    if months >= 12:
                        flags.append({
                            "type":     "EDU_EMPLOYMENT_OVERLAP",
                            "severity": "medium",
                            "detail":   f"{months}-month overlap between full-time study '{edu.get('event','?')}' and employment '{emp.get('event','?')}'",
                            "months":   months,
                        })

        # Check implausible experience claims
        exp_match = re.findall(r'(\d+)\+?\s*years?\s+(?:of\s+)?experience', cv_text.lower())
        for raw_years in exp_match:
            claimed = int(raw_years)
            if claimed > 40:
                flags.append({
                    "type":     "IMPLAUSIBLE_EXPERIENCE",
                    "severity": "high",
                    "detail":   f"Claims {claimed} years of experience — implausible for most careers.",
                })

        return flags

    def _detect_gaps(self, events: List[Dict]) -> List[Dict]:
        """Find unexplained gaps > 18 months in employment history."""
        employments = sorted(
            [e for e in events if e.get("type") == "employment" and e.get("start_year")],
            key=lambda x: (x.get("start_year", 0), x.get("start_month", 1))
        )
        gaps = []
        for i in range(1, len(employments)):
            prev_end   = self._to_date(employments[i-1].get("end_year"), employments[i-1].get("end_month"))
            curr_start = self._to_date(employments[i].get("start_year"), employments[i].get("start_month"))
            if prev_end and curr_start and curr_start > prev_end:
                months = (curr_start.year - prev_end.year) * 12 + (curr_start.month - prev_end.month)
                if months >= 18:
                    gaps.append({
                        "between": f"{employments[i-1].get('event','?')} → {employments[i].get('event','?')}",
                        "months":  months,
                        "note":    "Unexplained gap — not a flag, informational only.",
                    })
        return gaps

    def _check_age_consistency(self, events: List[Dict], cv_text: str) -> List[Dict]:
        """Check if education dates + claimed experience are age-consistent."""
        flags = []
        birth_match = re.search(r'born\s+(?:in\s+)?(\d{4})', cv_text.lower())
        if not birth_match:
            return flags
        birth_year = int(birth_match.group(1))
        educations = [e for e in events if e.get("type") == "education" and e.get("start_year")]
        for edu in educations:
            age_at_start = edu["start_year"] - birth_year
            if age_at_start < 14 or age_at_start > 60:
                flags.append({
                    "type":     "AGE_INCONSISTENCY",
                    "severity": "high",
                    "detail":   f"Age at start of '{edu.get('event','?')}': {age_at_start} — implausible.",
                })
        return flags


# ═══════════════════════════════════════════════════════════════════════════
# PROOF-OF-WORK VALIDATOR
# ═══════════════════════════════════════════════════════════════════════════

class ProofOfWorkValidator:
    """
    For technical/academic claims, searches for digital artefacts
    that a real professional would leave online.
    """

    ARTEFACT_QUERIES = {
        "github": lambda name, kw: f'site:github.com "{name}" {kw}',
        "scholar": lambda name, kw: f'site:scholar.google.com "{name}" {kw}',
        "arxiv":   lambda name, kw: f'site:arxiv.org "{name}" {kw}',
        "patent":  lambda name, kw: f'site:patents.google.com "{name}" {kw}',
        "stackoverflow": lambda name, kw: f'site:stackoverflow.com "{name}"',
    }

    TECHNICAL_KEYWORDS = [
        "open-source", "github", "contributor", "software engineer",
        "developer", "programmer", "machine learning", "data scientist",
    ]
    ACADEMIC_KEYWORDS = [
        "researcher", "phd", "professor", "publication", "paper",
        "journal", "conference", "dissertation", "thesis",
    ]

    def validate(self, name: str, claims: List[Dict]) -> List[Dict]:
        """Run proof-of-work searches for technical and academic claims."""
        results = []
        claim_text = " ".join(c.get("claim", "") for c in claims).lower()

        is_technical = any(kw in claim_text for kw in self.TECHNICAL_KEYWORDS)
        is_academic  = any(kw in claim_text for kw in self.ACADEMIC_KEYWORDS)

        targets = []
        if is_technical:
            kw = "software developer open source"
            targets += [
                ("github",       self.ARTEFACT_QUERIES["github"](name, kw)),
                ("stackoverflow",self.ARTEFACT_QUERIES["stackoverflow"](name, "")),
            ]
        if is_academic:
            kw = "research paper publication"
            targets += [
                ("scholar", self.ARTEFACT_QUERIES["scholar"](name, kw)),
                ("arxiv",   self.ARTEFACT_QUERIES["arxiv"](name, kw)),
                ("patent",  self.ARTEFACT_QUERIES["patent"](name, kw)),
            ]

        if not targets:
            return [{
                "platform": "N/A",
                "query":    "No technical/academic claims detected",
                "found":    False,
                "evidence": None,
                "url":      None,
                "note":     "Proof-of-work validation not applicable for this profile.",
            }]

        for platform, query in targets:
            result = self._search_artefact(platform, query)
            results.append(result)

        return results

    def _search_artefact(self, platform: str, query: str) -> Dict:
        try:
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=3))
            if hits:
                best = hits[0]
                return {
                    "platform": platform,
                    "query":    query,
                    "found":    True,
                    "evidence": best.get("body", "")[:200],
                    "url":      best.get("href", ""),
                    "title":    best.get("title", ""),
                    "note":     f"Artefact found on {platform}.",
                }
            return {
                "platform": platform,
                "query":    query,
                "found":    False,
                "evidence": None,
                "url":      None,
                "note":     f"No artefact found on {platform} — absence of evidence noted.",
            }
        except Exception as e:
            logger.warning(f"Proof-of-work search failed for {platform}: {e}")
            return {
                "platform": platform, "query": query, "found": False,
                "evidence": None, "url": None, "note": f"Search error: {str(e)[:80]}",
            }


# ═══════════════════════════════════════════════════════════════════════════
# CREDENTIAL INFLATION DETECTOR
# ═══════════════════════════════════════════════════════════════════════════

class CredentialInflationDetector:
    """
    Uses Claude with a structured rubric to score each claim
    on an Inflation Risk Index (0–10).
    """

    RUBRIC = """
Score each CV claim on an Inflation Risk Index (0-10):

0-2: MINIMAL — precise, verifiable, no superlatives
3-4: LOW — minor generality, mostly specific
5-6: MEDIUM — vague quantities, unverifiable scale ("Fortune 500", "$50M budget")
7-8: HIGH — superlatives, passive role language inflated ("led" vs "contributed to")
9-10: VERY HIGH — impossible/contradictory claims, fictional achievements

Flag these patterns:
- Unverifiable quantification ("increased revenue 400%", "managed 200 staff")
- Vague authority claims ("worked with top executives")
- Certification misrepresentation ("AWS exposure" listed as "AWS Certified")
- Passive inflation: "drove" / "spearheaded" / "transformed" without specifics
- Title inflation: "Senior Lead Principal Architect" type stacking
"""

    def detect(self, claims: List[Dict], client) -> List[Dict]:
        if not claims:
            return []
        claims_text = "\n".join([
            f"[{i+1}] ({c.get('type','?')}) {c.get('claim', '')}"
            for i, c in enumerate(claims[:10])
        ])
        prompt = f"""{self.RUBRIC}

CV CLAIMS:
{claims_text}

Return a JSON array. For each claim:
- "claim_index": integer (1-based)
- "claim": the claim text
- "inflation_risk": integer 0-10
- "risk_level": "minimal" | "low" | "medium" | "high" | "very_high"
- "flags": list of detected inflation patterns
- "recommended_question": one follow-up question a reviewer should ask

Return ONLY the JSON array."""
        try:
            msg = client.messages.create(
                model=config.CLAUDE_MODEL, max_tokens=2000, temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = re.sub(r'^```json\s*', '', msg.content[0].text.strip())
            raw = re.sub(r'\s*```$', '', raw)
            return json.loads(raw)
        except Exception as e:
            logger.warning(f"Inflation detection failed: {e}")
            return []


# ═══════════════════════════════════════════════════════════════════════════
# ACADEMIC CREDENTIAL VERIFIER
# ═══════════════════════════════════════════════════════════════════════════

class AcademicCredentialVerifier:
    """
    For each education claim, verifies:
    1. The institution exists (Wikipedia/official page)
    2. The claimed degree programme exists at that institution
    3. The graduation year is plausible
    """

    def verify(self, claims: List[Dict], client) -> List[Dict]:
        edu_claims = [c for c in claims if c.get("type") == "education"]
        if not edu_claims:
            return []
        results = []
        for claim in edu_claims[:4]:
            result = self._verify_claim(claim, client)
            results.append(result)
        return results

    def _verify_claim(self, claim: Dict, client) -> Dict:
        claim_text = claim.get("claim", "")
        institution = self._extract_institution(claim_text, client)
        if not institution:
            return {
                "claim":              claim_text,
                "institution":        None,
                "institution_found":  False,
                "programme_found":    None,
                "year_plausible":     None,
                "note":               "Could not extract institution name from claim.",
            }
        # Search for institution
        wiki_result = self._search_institution(institution)
        programme_check = self._check_programme(institution, claim_text, wiki_result, client)
        return {
            "claim":              claim_text,
            "institution":        institution,
            "institution_found":  wiki_result.get("found", False),
            "institution_url":    wiki_result.get("url", ""),
            "institution_snippet":wiki_result.get("snippet", ""),
            "programme_found":    programme_check["found"],
            "programme_note":     programme_check["note"],
            "year_plausible":     self._check_year(claim_text, wiki_result),
        }

    def _extract_institution(self, claim_text: str, client) -> Optional[str]:
        prompt = f"""Extract only the institution name from this education claim.
Return ONLY the institution name as plain text, nothing else.
If none found, return "NONE".

Claim: {claim_text}"""
        try:
            msg = client.messages.create(
                model=config.CLAUDE_MODEL, max_tokens=50, temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            result = msg.content[0].text.strip()
            return None if result == "NONE" else result
        except:
            return None

    def _search_institution(self, institution: str) -> Dict:
        try:
            query = f'"{institution}" university OR college OR institute site:wikipedia.org'
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=2))
            if hits:
                return {"found": True, "url": hits[0].get("href",""), "snippet": hits[0].get("body","")[:300]}
            # Try without Wikipedia
            with DDGS() as ddgs:
                hits = list(ddgs.text(f'"{institution}" official university', max_results=2))
            if hits:
                return {"found": True, "url": hits[0].get("href",""), "snippet": hits[0].get("body","")[:300]}
            return {"found": False, "url": "", "snippet": ""}
        except Exception as e:
            logger.warning(f"Institution search failed: {e}")
            return {"found": False, "url": "", "snippet": ""}

    def _check_programme(self, institution: str, claim_text: str, inst_result: Dict, client) -> Dict:
        if not inst_result.get("found"):
            return {"found": None, "note": "Institution not found — cannot verify programme."}
        degree = self._extract_degree(claim_text)
        if not degree:
            return {"found": None, "note": "Could not extract degree name."}
        snippet = inst_result.get("snippet", "")
        # Simple keyword check in snippet
        degree_words = [w.lower() for w in degree.split() if len(w) > 3]
        matches = sum(1 for w in degree_words if w in snippet.lower())
        if matches >= len(degree_words) * 0.5:
            return {"found": True, "note": f"Programme keywords for '{degree}' found in institution description."}
        return {"found": False, "note": f"Programme '{degree}' not confirmed in institution's public description."}

    def _extract_degree(self, claim_text: str) -> Optional[str]:
        patterns = [
            r'\b(BSc|BA|BEng|MSc|MA|MEng|MBA|PhD|DPhil|LLB|MD|BBA)\b[^,\n]*',
            r'\bBachelor[^,\n]*',
            r'\bMaster[^,\n]*',
            r'\bDoctorate[^,\n]*',
        ]
        for pat in patterns:
            m = re.search(pat, claim_text, re.IGNORECASE)
            if m:
                return m.group(0).strip()[:80]
        return None

    def _check_year(self, claim_text: str, inst_result: Dict) -> Optional[bool]:
        years = re.findall(r'\b(19|20)\d{2}\b', claim_text)
        if not years:
            return None
        year = int(years[0])
        current = date.today().year
        return 1950 <= year <= current + 1


# ═══════════════════════════════════════════════════════════════════════════
# MAIN CV ANALYZER
# ═══════════════════════════════════════════════════════════════════════════

class CVAnalyzer:
    """
    ENGINE 1 — Document Verification Engine
    Orchestrates all CV analysis sub-modules.
    """

    def __init__(self):
        self.client              = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.timeline_auditor    = ForensicTimelineAuditor()
        self.pow_validator       = ProofOfWorkValidator()
        self.inflation_detector  = CredentialInflationDetector()
        self.credential_verifier = AcademicCredentialVerifier()
        logger.info("CVAnalyzer (Document Verification Engine) initialized")

    def analyze(self, cv_text: str, context: str = "") -> Dict:
        logger.info("CVAnalyzer: starting full document verification pipeline")

        # Step 1 — Claim extraction + evidence search
        claims = self._extract_claims(cv_text)
        logger.info(f"CVAnalyzer: {len(claims)} claims extracted")

        if not claims:
            return self._empty_result()

        analyzed = []
        for claim in claims:
            evidence = self._search_evidence(claim)
            analyzed.append({
                "claim":            claim["text"],
                "type":             claim["type"],
                "evidence":         evidence["results"],
                "evidence_gallery": evidence["gallery"],
                "traceability":     evidence["traceability"],
                "confidence":       evidence["confidence"],
                "posterior":        evidence["posterior"],
                "likelihood_ratio": evidence["likelihood_ratio"],
                "note":             evidence["note"],
            })

        # Step 2 — Context classification
        context_signal = self._classify_context(cv_text, context) if context else "neutral"

        # Step 3 — Unrealistic content detection
        is_unrealistic, unrealistic_reason = self._detect_unrealistic_content(cv_text, analyzed)

        # Step 4 — Verdict
        verdict, confidence_pct, final_explanation = _verdict_from_analysis(
            analyzed, context_signal, is_unrealistic, unrealistic_reason
        )

        # Step 5 — Forensic timeline audit
        logger.info("CVAnalyzer: running timeline audit")
        timeline_audit = self.timeline_auditor.audit(cv_text, self.client)

        # Step 6 — Proof-of-work validation
        logger.info("CVAnalyzer: running proof-of-work validation")
        name = self._extract_name(cv_text)
        pow_results = self.pow_validator.validate(name, analyzed)

        # Step 7 — Credential inflation detection
        logger.info("CVAnalyzer: running inflation detection")
        inflation_results = self.inflation_detector.detect(analyzed, self.client)

        # Step 8 — Academic credential verification
        logger.info("CVAnalyzer: running academic credential verification")
        credential_results = self.credential_verifier.verify(analyzed, self.client)

        # Step 9 — Red flag dashboard
        red_flag_dashboard = self._build_red_flag_dashboard(
            analyzed, timeline_audit, pow_results,
            inflation_results, credential_results
        )

        # Step 10 — All sources
        all_sources = []
        for c in analyzed:
            for r in c.get("evidence", []):
                name_lbl, tier = _domain_label(r["url"])
                all_sources.append({
                    "url":              r["url"],
                    "title":            r.get("title", ""),
                    "type":             name_lbl,
                    "credibility_tier": tier,
                })

        return {
            # Core
            "claims":                analyzed,
            "total_claims":          len(analyzed),
            "claims_with_evidence":  sum(1 for c in analyzed if c["confidence"] != "not_found"),
            "verdict":               verdict,
            "confidence":            confidence_pct,
            "final_explanation":     final_explanation,
            "evidence_summary":      self._build_evidence_summary(analyzed, all_sources, bool(context), context_signal == "match"),
            "sources":               self._dedupe_sources(all_sources),
            # Advanced features
            "timeline_audit":        timeline_audit,
            "proof_of_work":         pow_results,
            "inflation_analysis":    inflation_results,
            "credential_verification": credential_results,
            "red_flag_dashboard":    red_flag_dashboard,
            "methodology": (
                "Bayesian evidence updating (Fellegi-Sunter 1969, ENFSI 2015). "
                "Forensic Timeline Audit uses Python datetime arithmetic. "
                "Proof-of-Work searches GitHub/Scholar/arXiv via DuckDuckGo. "
                "Inflation Detection uses Claude rubric scoring. "
                "Prior P(claim_true)=0.5 (Aitken & Taroni 2004)."
            ),
        }

    # ── Red Flag Dashboard ────────────────────────────────────────────────

    def _build_red_flag_dashboard(
        self, analyzed, timeline_audit, pow_results,
        inflation_results, credential_results
    ) -> Dict:
        high_flags   = []
        medium_flags = []
        low_flags    = []
        verified     = []

        # Timeline flags
        for f in timeline_audit.get("flags", []):
            entry = {"source": "Timeline", "detail": f["detail"]}
            if f["severity"] == "high":     high_flags.append(entry)
            elif f["severity"] == "medium": medium_flags.append(entry)
            else:                           low_flags.append(entry)

        # Proof-of-work
        for p in pow_results:
            if not p["found"] and p["platform"] != "N/A":
                medium_flags.append({"source": "Proof-of-Work",
                    "detail": f"No {p['platform']} artefact found for claimed technical profile."})

        # Inflation
        for inf in inflation_results:
            risk = inf.get("inflation_risk", 0)
            claim_text = inf.get("claim", "")[:80]
            entry = {"source": "Inflation", "detail": f"[Risk {risk}/10] {claim_text}"}
            if risk >= 8:        high_flags.append(entry)
            elif risk >= 5:      medium_flags.append(entry)
            elif risk >= 3:      low_flags.append(entry)

        # Credentials
        for cr in credential_results:
            if cr.get("institution_found") is False:
                high_flags.append({"source": "Credential", "detail": f"Institution not found: {cr.get('institution','?')}"})
            elif cr.get("programme_found") is False:
                medium_flags.append({"source": "Credential", "detail": f"Programme not confirmed: {cr.get('claim','?')[:80]}"})

        # Verified claims
        for c in analyzed:
            if c["confidence"] in ("high", "medium"):
                verified.append({"source": "OSINT", "detail": f"{c['claim'][:80]} — {c['confidence']} confidence"})

        total_risk = len(high_flags) * 3 + len(medium_flags) * 2 + len(low_flags)
        max_risk   = max(1, (len(analyzed) * 3))
        risk_score = min(100, int((total_risk / max_risk) * 100))

        if risk_score >= 60:    risk_level = "HIGH"
        elif risk_score >= 30:  risk_level = "MEDIUM"
        else:                   risk_level = "LOW"

        return {
            "risk_level":    risk_level,
            "risk_score":    risk_score,
            "high_flags":    high_flags,
            "medium_flags":  medium_flags,
            "low_flags":     low_flags,
            "verified":      verified,
            "summary": (
                f"{len(high_flags)} high-risk, {len(medium_flags)} medium-risk, "
                f"{len(low_flags)} low-risk flags detected. "
                f"{len(verified)} claim(s) supported by external evidence."
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
                model=config.CLAUDE_MODEL, max_tokens=1500, temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = re.sub(r'^```json\s*', '', msg.content[0].text.strip())
            raw = re.sub(r'\s*```$', '', raw)
            return json.loads(raw)[:10]
        except Exception as e:
            logger.warning(f"Claim extraction failed: {e}")
            return []

    def _extract_name(self, cv_text: str) -> str:
        """Heuristic: first line of CV is usually the name."""
        lines = [l.strip() for l in cv_text.strip().splitlines() if l.strip()]
        if lines:
            first = lines[0]
            if len(first.split()) <= 5 and len(first) < 60:
                return first
        return ""

    # ── Evidence Search + Gallery + Traceability ─────────────────────────

    def _search_evidence(self, claim: Dict) -> Dict:
        query   = claim.get("search_query", claim.get("text", ""))
        results = []
        gallery = []
        traceability = {
            "claim":        claim.get("text", ""),
            "query":        query,
            "results_found":0,
            "match_logic":  "",
        }

        try:
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=4))
            for h in hits:
                url     = h.get("href", "")
                title   = h.get("title", "")
                snippet = h.get("body", "")[:300]
                if not url or not title:
                    continue
                base_rel  = _source_reliability(url)
                relevance = self._claim_relevance(claim.get("text",""), title + " " + snippet)
                eff_rel   = round(base_rel * relevance, 3)
                src_name, credibility_tier = _domain_label(url)
                matched_text = self._extract_matched_text(claim.get("text",""), snippet)

                result = {
                    "url":              url,
                    "title":            title,
                    "snippet":          snippet,
                    "reliability":      eff_rel,
                    "base_reliability": round(base_rel, 2),
                    "relevance":        round(relevance, 2),
                }
                results.append(result)

                # Evidence Gallery entry
                gallery.append({
                    "url":              url,
                    "title":            title,
                    "snippet":          snippet,
                    "source_name":      src_name,
                    "credibility_tier": credibility_tier,
                    "matched_text":     matched_text,
                    "relevance_score":  round(relevance, 2),
                })
        except Exception as e:
            logger.warning(f"Evidence search failed: {e}")

        traceability["results_found"] = len(results)
        traceability["match_logic"]   = self._build_match_logic(claim.get("text",""), results)

        posterior, lr, note = self._bayesian_assess(results, claim)
        return {
            "results":      results,
            "gallery":      gallery,
            "traceability": traceability,
            "confidence":   _posterior_to_label(posterior),
            "posterior":    round(posterior, 3),
            "likelihood_ratio": round(lr, 1),
            "note":         note,
        }

    def _extract_matched_text(self, claim_text: str, snippet: str) -> str:
        """Find the sentence in snippet most similar to the claim."""
        claim_words = set(claim_text.lower().split())
        sentences   = re.split(r'[.!?]', snippet)
        best, best_score = "", 0
        for sent in sentences:
            words = set(sent.lower().split())
            score = len(claim_words & words) / max(len(claim_words), 1)
            if score > best_score:
                best, best_score = sent.strip(), score
        return best[:150] if best else ""

    def _build_match_logic(self, claim_text: str, results: List[Dict]) -> str:
        if not results:
            return "No results returned for this query."
        high_rel  = sum(1 for r in results if r.get("relevance", 0) >= 0.6)
        contradictions = sum(1 for r in results if r.get("relevance", 1) <= 0.10)
        parts = [f"{len(results)} result(s) retrieved."]
        if high_rel:
            parts.append(f"{high_rel} result(s) with high relevance (≥0.6) to the claim.")
        if contradictions:
            parts.append(f"{contradictions} result(s) appear to contradict the claim (relevance ≤0.10).")
        avg_rel = sum(r.get("relevance", 0) for r in results) / len(results)
        parts.append(f"Average relevance: {avg_rel:.2f}.")
        return " ".join(parts)

    def _claim_relevance(self, claim_text: str, result_text: str) -> float:
        STOP = {"a","an","the","and","or","of","in","at","for","to","is","was","are","be","been","has","have","had","with","by","as","on","from"}
        NEGATIONS = {"not","no","never","false","incorrect","wrong","denied","fake"}
        def tokens(s): return {w.lower().strip(".,;:'\"()[]") for w in s.split() if len(w) > 2 and w.lower() not in STOP}
        ct, rt = tokens(claim_text), tokens(result_text)
        if not ct or not rt:
            return 0.50
        intersection = ct & rt
        jaccard      = len(intersection) / len(ct | rt)
        result_words = result_text.lower().split()
        for i, w in enumerate(result_words):
            if w in NEGATIONS:
                if set(result_words[max(0,i-3):i+4]) & ct:
                    return 0.10
        return round(0.20 + min(0.80, jaccard * 1.60), 3)

    def _bayesian_assess(self, results, claim):
        if not results:
            return 0.30, 0.0, "No web evidence found. Result: UNVERIFIED — not refuted."
        posterior, combined_lr = PRIOR_CLAIM_TRUE, 1.0
        for r in results:
            rel  = r["reliability"]
            p_h1 = rel
            p_h0 = 1.0 - rel
            lr_i = p_h1 / max(p_h0, 0.01)
            combined_lr *= lr_i
            posterior    = _bayesian_update(posterior, p_h1, p_h0)
        contradictions = sum(1 for r in results if r.get("relevance", 1.0) <= 0.10)
        if contradictions:
            posterior = max(0.05, posterior * (0.3 ** contradictions))
        high_quality = sum(1 for r in results if r.get("base_reliability", r["reliability"]) >= 0.80 and r.get("relevance", 0.5) >= 0.60)
        if high_quality >= 2:
            posterior = min(1.0, posterior + 0.20)
        posterior = round(max(0.05, min(0.95, posterior)), 3)
        note = (f"Bayesian posterior {posterior:.2f} from {len(results)} source(s). "
                f"{contradictions} contradiction(s), {high_quality} high-quality match(es). "
                f"Combined LR={combined_lr:.1f}.")
        return posterior, combined_lr, note

    # ── Context + Unrealistic Checks ─────────────────────────────────────

    def _classify_context(self, cv_text: str, context: str) -> str:
        STOP = {"a","an","the","and","or","of","in","at","for","to","is","was","are","be","been","has","have","had","with","by","as","on","from","that","this","it","he","she","they","we","i","my","your","their","our","its"}
        if not context or not cv_text:
            return "neutral"
        ctx_words = [w.lower().strip(".,;:\"'()[]") for w in context.split() if len(w) > 3 and w.lower() not in STOP]
        if len(ctx_words) < 4:
            return "neutral"
        cv_lower = cv_text.lower()
        matched  = sum(1 for w in ctx_words if w in cv_lower)
        ratio    = matched / len(ctx_words)
        if ratio >= 0.40:    return "match"
        elif ratio < 0.15:   return "contradiction"
        return "neutral"

    def _detect_unrealistic_content(self, cv_text: str, claims: list) -> tuple:
        combined = cv_text.lower() + " " + " ".join(c.get("claim","") for c in claims).lower()
        FICTIONAL = ["martian","klingon","elvish","sindarin","dothraki","valyrian","na'vi","parseltongue"]
        for lang in FICTIONAL:
            if lang in combined:
                return True, f"CV references a fictional language ('{lang}')."
        concurrent_at = len(re.findall(r'\bat\s+[A-Z][a-zA-Z]+', cv_text))
        PRESTIGE_SIGNALS = ["simultaneously","concurrently","current role","currently working at"]
        if any(sig in combined for sig in PRESTIGE_SIGNALS) and concurrent_at >= 4:
            return True, f"CV claims {concurrent_at} concurrent roles at different organisations."
        SENIOR = ["chief executive","ceo","chief technology","cto","chief financial","cfo","chief operating","coo","vice president","managing director","board member","board director","full professor"]
        if sum(1 for t in SENIOR if t in combined) >= 4:
            return True, "CV lists 4+ simultaneous C-suite titles."
        return False, ""

    # ── Helpers ───────────────────────────────────────────────────────────

    def _label_source(self, url: str) -> str:
        name, _ = _domain_label(url)
        return name

    def _dedupe_sources(self, sources: list) -> list:
        seen, out = set(), []
        for s in sources:
            if s["url"] not in seen:
                seen.add(s["url"])
                out.append(s)
        return out[:10]

    def _build_evidence_summary(self, analyzed, all_sources, context_provided, context_consistent) -> str:
        total  = len(analyzed)
        high   = sum(1 for c in analyzed if c["confidence"] == "high")
        medium = sum(1 for c in analyzed if c["confidence"] == "medium")
        none   = sum(1 for c in analyzed if c["confidence"] == "not_found")
        deduped = self._dedupe_sources(all_sources)
        parts  = []
        if deduped:
            types = list({s["type"] for s in deduped})
            parts.append(f"External sources found: {len(deduped)} source(s) ({', '.join(types[:4])}).")
            if high + medium > 0:
                parts.append(f"{high + medium} claim(s) have supporting evidence ({high} strong, {medium} moderate).")
            if none:
                parts.append(f"{none} claim(s) had no matching public records.")
        else:
            parts.append("No public identity records found.")
        if context_provided:
            parts.append("Context consistent with CV." if context_consistent else "Context does not align with CV — inconsistency flagged.")
        return " ".join(parts)

    def _empty_result(self) -> Dict:
        return {
            "claims": [], "total_claims": 0, "claims_with_evidence": 0,
            "verdict": "Unverified", "confidence": 30,
            "evidence_summary": "No verifiable claims could be extracted.",
            "final_explanation": "No verifiable claims found — inconclusive result.",
            "sources": [], "timeline_audit": {}, "proof_of_work": [],
            "inflation_analysis": [], "credential_verification": [],
            "red_flag_dashboard": {"risk_level": "LOW", "risk_score": 0, "high_flags": [], "medium_flags": [], "low_flags": [], "verified": [], "summary": "No claims to analyse."},
            "methodology": "No claims extracted.",
        }
