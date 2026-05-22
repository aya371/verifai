"""
Identity Resolution Agent — OSINT Identity Intelligence Engine
==============================================================
ENGINE 2 of VerifAI's two-engine architecture.

Purpose: Reconstruct who the person actually is from the internet.
         Starts from a NAME and works inward from public sources.

Advanced features implemented:
  1. Identity Disambiguation Engine    — deductive candidate elimination
  2. Digital Footprint Score           — recency/breadth/consistency/depth/authenticity
  3. Multi-Platform Profile Merger     — conflict-resolved ground truth
  4. Real-World Presence Detector      — conferences, media, awards, community
  5. Identity Risk Profile             — structured OSINT report
  6. Identity Confidence Breakdown     — name/location/role/source match %
  7. Last Known Activity               — most recent signal extraction
  8. Ambiguity Detection               — structured explanation vs guessing

Methodology:
  Fellegi-Sunter (1969) probabilistic record linkage
  ENFSI (2015) uncertainty characterisation
  NIST FRVT source reliability hierarchy
"""
import json
import re
from datetime import date
from typing import Dict, List, Optional, Tuple
from ddgs import DDGS
from anthropic import Anthropic
from config import config
from backend.utils.logger import logger

PLATFORMS = [
    {"name": "LinkedIn",  "site": "linkedin.com",  "weight": 0.9},
    {"name": "Wikipedia", "site": "wikipedia.org", "weight": 1.0},
    {"name": "GitHub",    "site": "github.com",    "weight": 0.7},
    {"name": "Twitter/X", "site": "twitter.com",   "weight": 0.5},
    {"name": "News",      "site": None,            "weight": 0.6},
]

STOP_WORDS = {
    "a","an","the","and","or","of","in","at","for","to","is","was","are","be","been",
    "has","have","had","mr","ms","dr","prof","sir","jr","sr","by","with","his","her","their",
}

GEO_MARKERS = [
    "london","paris","berlin","dubai","beirut","new york","los angeles","cairo","riyadh",
    "toronto","sydney","usa","uk","lebanon","uae","france","germany","india","china","japan",
    "brazil","australia","canada","italy","spain","mexico","turkey","egypt","jordan","singapore",
    "amsterdam","moscow","seoul","chicago","houston","boston","san francisco","milan",
]

FS_WEIGHTS = {
    "full_name":    {"m": 0.95, "u": 0.005},
    "last_name":    {"m": 0.90, "u": 0.04},
    "first_name":   {"m": 0.85, "u": 0.10},
    "context":      {"m": 0.80, "u": 0.20},
    "credible_src": {"m": 0.90, "u": 0.30},
    "org_match":    {"m": 0.85, "u": 0.15},
}


def _fs_lr(field: str) -> float:
    w = FS_WEIGHTS.get(field, {"m": 0.70, "u": 0.30})
    return w["m"] / max(w["u"], 0.001)


def _fs_update(prior: float, lr: float) -> float:
    p0 = 1.0 - prior
    return (lr * prior) / (lr * prior + p0)


# ═══════════════════════════════════════════════════════════════════════════
# DIGITAL FOOTPRINT SCORER
# ═══════════════════════════════════════════════════════════════════════════

class DigitalFootprintScorer:
    """
    Scores a person's digital presence across 5 dimensions (0-100).
    Ghost (0-20) → Low (20-50) → Normal (50-75) → High (75-100).
    """

    def score(self, candidates: List[Dict], raw_results: List[Dict]) -> Dict:
        recency       = self._score_recency(raw_results)
        breadth       = self._score_breadth(raw_results)
        consistency   = self._score_consistency(candidates)
        depth         = self._score_depth(raw_results)
        authenticity  = self._score_authenticity(raw_results)

        total = int((recency + breadth + consistency + depth + authenticity) / 5)

        if total >= 75:   tier = "High Visibility"
        elif total >= 50: tier = "Normal Presence"
        elif total >= 20: tier = "Low Footprint"
        else:             tier = "Ghost"

        return {
            "total_score":    total,
            "tier":           tier,
            "dimensions": {
                "recency":      recency,
                "breadth":      breadth,
                "consistency":  consistency,
                "depth":        depth,
                "authenticity": authenticity,
            },
            "interpretation": self._interpret(total, tier),
        }

    def _score_recency(self, results: List[Dict]) -> int:
        current_year = date.today().year
        years = []
        for r in results:
            text = r.get("snippet","") + r.get("title","")
            found = re.findall(r'\b(20\d{2})\b', text)
            for y in found:
                if 2000 <= int(y) <= current_year:
                    years.append(int(y))
        if not years:
            return 10
        most_recent = max(years)
        gap = current_year - most_recent
        if gap == 0:    return 100
        if gap <= 1:    return 85
        if gap <= 2:    return 70
        if gap <= 4:    return 50
        if gap <= 6:    return 30
        return 10

    def _score_breadth(self, results: List[Dict]) -> int:
        unique_domains = set()
        for r in results:
            url = r.get("url","")
            m = re.search(r'https?://([^/]+)', url)
            if m:
                domain = re.sub(r'^www\.', '', m.group(1))
                unique_domains.add(domain)
        n = len(unique_domains)
        if n >= 8:    return 100
        if n >= 5:    return 80
        if n >= 3:    return 60
        if n >= 2:    return 40
        if n >= 1:    return 20
        return 0

    def _score_consistency(self, candidates: List[Dict]) -> int:
        if not candidates:
            return 0
        if len(candidates) == 1:
            return 80
        top    = candidates[0].get("similarity_score", 0)
        second = candidates[1].get("similarity_score", 0) if len(candidates) > 1 else 0
        diff   = top - second
        if diff >= 0.40:  return 85
        if diff >= 0.20:  return 65
        if diff >= 0.10:  return 40
        return 15

    def _score_depth(self, results: List[Dict]) -> int:
        depth_keywords = ["article","interview","publication","paper","award","conference","keynote","biography","profile"]
        shallow_only   = ["directory","listing","contact","phone","email"]
        deep_count    = sum(1 for r in results if any(kw in (r.get("snippet","") + r.get("title","")).lower() for kw in depth_keywords))
        shallow_count = sum(1 for r in results if any(kw in (r.get("snippet","") + r.get("title","")).lower() for kw in shallow_only))
        if deep_count >= 4:   return 100
        if deep_count >= 2:   return 75
        if deep_count >= 1:   return 50
        if shallow_count >= 2: return 25
        return 10

    def _score_authenticity(self, results: List[Dict]) -> int:
        primary_domains = ["linkedin.com","wikipedia.org",".edu",".gov","github.com","bloomberg.com","reuters.com","researchgate.net","arxiv.org"]
        aggregator_domains = ["yellowpages","whitepages","spokeo","pipl","beenverified"]
        primary_count = sum(1 for r in results if any(d in r.get("url","").lower() for d in primary_domains))
        aggregator_count = sum(1 for r in results if any(d in r.get("url","").lower() for d in aggregator_domains))
        total = len(results) or 1
        primary_ratio = primary_count / total
        if primary_ratio >= 0.6 and aggregator_count == 0: return 100
        if primary_ratio >= 0.4:  return 75
        if primary_ratio >= 0.2:  return 50
        if aggregator_count >= 2: return 20
        return 30

    def _interpret(self, score: int, tier: str) -> str:
        return {
            "High Visibility": (f"Score {score}/100: Strong public digital presence. "
                "Multiple primary sources confirm this identity with high consistency."),
            "Normal Presence": (f"Score {score}/100: Typical professional digital footprint. "
                "Several sources found across platforms."),
            "Low Footprint":   (f"Score {score}/100: Limited digital presence. "
                "Few sources found. Expected for private individuals or early-career professionals."),
            "Ghost":           (f"Score {score}/100: Near-zero digital footprint. "
                "Extremely limited public presence — unusual for claimed experience level."),
        }.get(tier, f"Score {score}/100.")


# ═══════════════════════════════════════════════════════════════════════════
# REAL-WORLD PRESENCE DETECTOR
# ═══════════════════════════════════════════════════════════════════════════

class RealWorldPresenceDetector:
    """
    Searches for signals that a real professional would generate:
    conferences, media appearances, awards, community activity.
    """

    PRESENCE_QUERIES = [
        ("conference",  lambda n: f'"{n}" conference OR "invited talk" OR keynote OR "presented at"'),
        ("media",       lambda n: f'"{n}" interview OR "spoke to" OR "told reporters" OR "according to"'),
        ("award",       lambda n: f'"{n}" award OR prize OR recognition OR "named to" OR "listed as"'),
        ("community",   lambda n: f'site:stackoverflow.com "{n}" OR site:github.com "{n}"'),
        ("publication", lambda n: f'"{n}" "published" OR "paper" OR "journal" OR "conference proceedings"'),
    ]

    def detect(self, name: str) -> Dict:
        if not name or len(name.split()) < 2:
            return {"signals": [], "note": "Name too short for presence detection."}
        signals = []
        for kind, query_fn in self.PRESENCE_QUERIES:
            result = self._search(kind, query_fn(name))
            if result:
                signals.append(result)
        return {
            "signals":     signals,
            "found_count": sum(1 for s in signals if s.get("found")),
            "note": f"{sum(1 for s in signals if s.get('found'))}/{len(signals)} presence signals detected.",
        }

    def _search(self, kind: str, query: str) -> Dict:
        try:
            with DDGS() as ddgs:
                hits = list(ddgs.text(query, max_results=2))
            if hits:
                return {
                    "type":    kind,
                    "found":   True,
                    "url":     hits[0].get("href",""),
                    "title":   hits[0].get("title",""),
                    "snippet": hits[0].get("body","")[:200],
                }
            return {"type": kind, "found": False, "url": "", "title": "", "snippet": ""}
        except Exception as e:
            logger.warning(f"Real-world presence search failed ({kind}): {e}")
            return {"type": kind, "found": False, "url": "", "title": "", "snippet": "", "error": str(e)[:80]}


# ═══════════════════════════════════════════════════════════════════════════
# LAST KNOWN ACTIVITY EXTRACTOR
# ═══════════════════════════════════════════════════════════════════════════

class LastKnownActivityExtractor:
    """Finds the most recent dated mention across all OSINT results."""

    def extract(self, raw_results: List[Dict]) -> Dict:
        current_year = date.today().year
        best_year, best_month, best_result = 0, 0, None
        for r in raw_results:
            text = (r.get("snippet","") + " " + r.get("title","")).lower()
            years = [int(y) for y in re.findall(r'\b(20\d{2})\b', text) if 2000 <= int(y) <= current_year]
            if not years:
                continue
            year = max(years)
            # Try to find a month
            MONTHS = {"january":1,"february":2,"march":3,"april":4,"may":5,"june":6,
                      "july":7,"august":8,"september":9,"october":10,"november":11,"december":12,
                      "jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"aug":8,"sep":9,"oct":10,"nov":11,"dec":12}
            month = 0
            for m_name, m_num in MONTHS.items():
                if m_name in text:
                    month = m_num
                    break
            if year > best_year or (year == best_year and month > best_month):
                best_year, best_month, best_result = year, month, r
        if not best_result:
            return {"found": False, "year": None, "month": None, "source": None, "snippet": None}
        return {
            "found":   True,
            "year":    best_year,
            "month":   best_month if best_month else None,
            "source":  best_result.get("url",""),
            "title":   best_result.get("title",""),
            "snippet": best_result.get("snippet","")[:150],
            "age_years": current_year - best_year,
        }


# ═══════════════════════════════════════════════════════════════════════════
# IDENTITY CONFIDENCE BREAKDOWN
# ═══════════════════════════════════════════════════════════════════════════

class IdentityConfidenceBreakdown:
    """
    Produces a field-level breakdown of what drove the identity confidence score.
    """

    def compute(self, name: str, context: str, candidates: List[Dict], raw_results: List[Dict]) -> Dict:
        if not candidates:
            return {
                "name_match_pct":     0,
                "location_match_pct": 0,
                "role_match_pct":     0,
                "source_reliability_avg": 0,
                "breakdown_note":     "No candidates found.",
            }
        top = candidates[0]
        candidate_text = (top.get("extracted_info","") + " " + top.get("match_explanation","")).lower()
        name_match = self._name_match(name, top.get("name",""))
        location_match = self._location_match(context, candidate_text)
        role_match     = self._role_match(context, candidate_text)
        src_rel = self._source_reliability_avg(raw_results)
        return {
            "name_match_pct":         name_match,
            "location_match_pct":     location_match,
            "role_match_pct":         role_match,
            "source_reliability_avg": src_rel,
            "breakdown_note": (
                f"Name match: {name_match}%, "
                f"Location: {location_match}%, "
                f"Role: {role_match}%, "
                f"Avg source reliability: {src_rel}%."
            ),
        }

    def _name_match(self, query_name: str, found_name: str) -> int:
        def tok(s): return {w.lower() for w in re.findall(r'\b\w+\b', s) if len(w) > 1}
        a, b = tok(query_name), tok(found_name)
        if not a or not b:
            return 0
        return int(len(a & b) / len(a | b) * 100)

    def _location_match(self, context: str, candidate_text: str) -> int:
        ctx_locs = {g for g in GEO_MARKERS if g in context.lower()}
        can_locs = {g for g in GEO_MARKERS if g in candidate_text}
        if not ctx_locs:
            return 50  # no location in context — neutral
        if not can_locs:
            return 0
        return int(len(ctx_locs & can_locs) / len(ctx_locs | can_locs) * 100)

    def _role_match(self, context: str, candidate_text: str) -> int:
        JOB_KW = ["engineer","developer","manager","director","analyst","architect","designer",
                  "consultant","researcher","professor","doctor","scientist","ceo","cto","founder"]
        ctx_roles = {k for k in JOB_KW if k in context.lower()}
        can_roles = {k for k in JOB_KW if k in candidate_text}
        if not ctx_roles:
            return 50
        if not can_roles:
            return 0
        return int(len(ctx_roles & can_roles) / len(ctx_roles | can_roles) * 100)

    def _source_reliability_avg(self, results: List[Dict]) -> int:
        DOMAIN_WEIGHTS = {"linkedin.com":90,"wikipedia.org":95,".edu":90,".gov":95,"github.com":75,"bloomberg.com":85,"reuters.com":85}
        weights = []
        for r in results:
            url = r.get("url","").lower()
            for d, w in DOMAIN_WEIGHTS.items():
                if d in url:
                    weights.append(w)
                    break
            else:
                weights.append(55)
        return int(sum(weights) / len(weights)) if weights else 0


# ═══════════════════════════════════════════════════════════════════════════
# MAIN IDENTITY RESOLVER
# ═══════════════════════════════════════════════════════════════════════════

class IdentityResolver:
    """
    ENGINE 2 — OSINT Identity Intelligence Engine
    Orchestrates all OSINT sub-modules.
    """

    def __init__(self):
        self.client            = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.footprint_scorer  = DigitalFootprintScorer()
        self.presence_detector = RealWorldPresenceDetector()
        self.last_activity     = LastKnownActivityExtractor()
        self.conf_breakdown    = IdentityConfidenceBreakdown()
        logger.info("IdentityResolver (OSINT Identity Intelligence Engine) initialized")

    def resolve(self, name: str, context: str = "") -> Dict:
        logger.info(f"IdentityResolver: '{name}' ctx='{context[:60]}'")
        name_parts = self._parse_name(name)

        # Step 1: Multi-platform search
        raw = self._collect_results(name, context)

        # Step 2: Hard filter by last name
        filtered = self._hard_filter(raw, name_parts)

        # Step 3: Claude candidate extraction
        raw_cands = self._extract_candidates(name, context, filtered, name_parts)

        # Step 4: Fellegi-Sunter scoring
        scored = [self._fs_score(c, name_parts, context) for c in raw_cands]
        scored.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)

        # Step 5: Entity merging
        candidates = self.merge_candidates(scored)

        # Step 6: Disambiguation
        disambiguation = self._disambiguate(name, context, candidates)

        # Step 7: Candidate comparison
        comparison = self.compare_candidates(candidates) if len(candidates) >= 2 else []

        # Step 8: Status
        status = self._determine_status(candidates)

        # Step 9: Digital footprint
        footprint = self.footprint_scorer.score(candidates, raw)

        # Step 10: Real-world presence
        presence = self.presence_detector.detect(name)

        # Step 11: Last known activity
        last_known = self.last_activity.extract(raw)

        # Step 12: Confidence breakdown
        conf_breakdown = self.conf_breakdown.compute(name, context, candidates, raw)

        # Step 13: Identity risk profile
        risk_profile = self._build_risk_profile(
            name, status, candidates, footprint, presence, last_known, disambiguation
        )

        logger.info(f"  {len(raw_cands)} raw → {len(candidates)} merged → {status} | footprint={footprint['total_score']}")

        return {
            "query":                {"name": name, "context": context},
            "status":               status,
            "candidates":           candidates,
            "comparison":           comparison,
            "disambiguation":       disambiguation,
            "digital_footprint":    footprint,
            "real_world_presence":  presence,
            "last_known_activity":  last_known,
            "confidence_breakdown": conf_breakdown,
            "identity_risk_profile": risk_profile,
            "warning":              self._build_warning(status, len(candidates)),
            "methodology": (
                "Fellegi-Sunter (1969) probabilistic record linkage. "
                "Digital Footprint: 5-dimension scoring (recency/breadth/consistency/depth/authenticity). "
                "Real-World Presence: targeted DuckDuckGo platform queries. "
                "Status thresholds: ENFSI (2015) uncertainty characterisation."
            ),
        }

    # ── Disambiguation ────────────────────────────────────────────────────

    def _disambiguate(self, name: str, context: str, candidates: List[Dict]) -> Dict:
        """
        Deductive disambiguation using contextual exclusion.
        Returns a structured report — never guesses silently.
        """
        if not candidates:
            return {
                "resolved":        False,
                "resolved_to":     None,
                "method":          "No candidates found.",
                "ruled_out":       [],
                "ambiguity_level": "high",
                "note":            "No public profiles found for this name.",
            }

        if len(candidates) == 1:
            return {
                "resolved":        True,
                "resolved_to":     candidates[0].get("name",""),
                "confidence":      candidates[0].get("similarity_score", 0),
                "method":          "Single candidate — no disambiguation needed.",
                "ruled_out":       [],
                "ambiguity_level": "low",
            }

        # Try deductive exclusion using context
        context_lower = context.lower()
        ctx_locs  = {g for g in GEO_MARKERS if g in context_lower}
        ctx_roles = set(re.findall(r'\b(?:engineer|developer|professor|doctor|analyst|manager|director|researcher|scientist|ceo|cto|founder)\b', context_lower))

        ruled_out  = []
        survivors  = []

        for cand in candidates:
            info = (cand.get("extracted_info","") + " " + cand.get("match_explanation","")).lower()
            cand_locs  = {g for g in GEO_MARKERS if g in info}
            cand_roles = set(re.findall(r'\b(?:engineer|developer|professor|doctor|analyst|manager|director|researcher|scientist|ceo|cto|founder)\b', info))

            excluded = False
            reason   = ""

            # Geographic exclusion
            if ctx_locs and cand_locs and not (ctx_locs & cand_locs):
                excluded = True
                reason   = f"Location mismatch: context={', '.join(ctx_locs)}, profile={', '.join(cand_locs)}"

            # Role exclusion
            if not excluded and ctx_roles and cand_roles and not (ctx_roles & cand_roles):
                excluded = True
                reason   = f"Role mismatch: context={', '.join(ctx_roles)}, profile={', '.join(cand_roles)}"

            if excluded:
                ruled_out.append({"name": cand.get("name","?"), "reason": reason})
            else:
                survivors.append(cand)

        if len(survivors) == 1:
            return {
                "resolved":        True,
                "resolved_to":     survivors[0].get("name",""),
                "confidence":      survivors[0].get("similarity_score", 0),
                "method":          f"Deductive exclusion ({len(ruled_out)} candidate(s) ruled out by context).",
                "ruled_out":       ruled_out,
                "ambiguity_level": "low",
            }
        elif len(survivors) == 0:
            return {
                "resolved":        False,
                "resolved_to":     None,
                "method":          "All candidates excluded — context may be incorrect or too specific.",
                "ruled_out":       ruled_out,
                "ambiguity_level": "high",
                "note":            "No candidates survived context filtering. Manual review required.",
            }
        else:
            # Still multiple survivors — score-based selection with ambiguity flag
            top_score    = survivors[0].get("similarity_score", 0)
            second_score = survivors[1].get("similarity_score", 0) if len(survivors) > 1 else 0
            diff         = top_score - second_score
            ambiguity    = "low" if diff >= 0.30 else ("medium" if diff >= 0.15 else "high")
            return {
                "resolved":        ambiguity != "high",
                "resolved_to":     survivors[0].get("name","") if ambiguity != "high" else None,
                "confidence":      top_score,
                "method":          f"Partial disambiguation: {len(ruled_out)} excluded, {len(survivors)} remaining. Score gap={diff:.2f}.",
                "ruled_out":       ruled_out,
                "ambiguity_level": ambiguity,
                "note":            "Multiple profiles remain. Provide more context for full resolution." if ambiguity == "high" else "",
            }

    # ── Identity Risk Profile ─────────────────────────────────────────────

    def _build_risk_profile(
        self, name: str, status: str, candidates: List[Dict],
        footprint: Dict, presence: Dict, last_known: Dict, disambiguation: Dict
    ) -> Dict:
        risk_flags = []
        positive_signals = []

        # Footprint risk
        if footprint["total_score"] < 20:
            risk_flags.append({"level": "high",   "detail": f"Near-zero digital footprint ({footprint['total_score']}/100) — unusual for claimed experience."})
        elif footprint["total_score"] < 40:
            risk_flags.append({"level": "medium", "detail": f"Low digital footprint ({footprint['total_score']}/100)."})
        else:
            positive_signals.append(f"Digital footprint: {footprint['tier']} ({footprint['total_score']}/100).")

        # Presence risk
        found_count = presence.get("found_count", 0)
        if found_count == 0:
            risk_flags.append({"level": "medium", "detail": "No real-world presence signals (conferences, media, awards)."})
        else:
            found_types = [s["type"] for s in presence.get("signals",[]) if s.get("found")]
            positive_signals.append(f"Real-world presence confirmed: {', '.join(found_types)}.")

        # Last activity risk
        if last_known.get("found"):
            age = last_known.get("age_years", 0)
            if age > 5:
                risk_flags.append({"level": "medium", "detail": f"Last known activity was {age} years ago."})
            else:
                positive_signals.append(f"Recent activity found ({last_known.get('year')}).")
        else:
            risk_flags.append({"level": "low", "detail": "No dated mentions found — activity timeline unknown."})

        # Ambiguity risk
        if disambiguation.get("ambiguity_level") == "high":
            risk_flags.append({"level": "high", "detail": "Identity ambiguous — multiple candidates could not be resolved."})
        elif disambiguation.get("resolved"):
            positive_signals.append(f"Identity disambiguated: resolved to '{disambiguation.get('resolved_to','?')}'.")

        # Status
        if status in ("LIKELY_MATCH",):
            positive_signals.append("Strong Fellegi-Sunter identity match found.")
        elif status in ("AMBIGUOUS","INSUFFICIENT_DATA"):
            risk_flags.append({"level": "medium", "detail": f"OSINT status: {status} — identity not firmly established."})

        high   = [f for f in risk_flags if f["level"] == "high"]
        medium = [f for f in risk_flags if f["level"] == "medium"]
        low    = [f for f in risk_flags if f["level"] == "low"]

        overall = "HIGH RISK" if high else ("MEDIUM RISK" if medium else "LOW RISK")

        return {
            "subject":          name,
            "overall_risk":     overall,
            "risk_flags":       risk_flags,
            "positive_signals": positive_signals,
            "recommended_action": (
                "Mandatory human review and document verification required."
                if overall == "HIGH RISK" else
                "Human review recommended for flagged items."
                if overall == "MEDIUM RISK" else
                "Standard due diligence sufficient."
            ),
        }

    # ═══════════════════════════════════════════════════════════════════════
    # FELLEGI-SUNTER SCORING (unchanged from original)
    # ═══════════════════════════════════════════════════════════════════════

    def _fs_score(self, cand: Dict, name_parts: Dict, context: str) -> Dict:
        c, prior = dict(cand), 0.5
        posterior, agreements = prior, []
        name  = name_parts["full"]
        first = name_parts["first"]
        last  = name_parts["last"]
        has_last = name_parts["has_last"]
        cand_text = (c.get("name","") + " " + c.get("extracted_info","")).lower()
        name_clean = re.sub(r'[^a-z\s]','', name.lower()).strip()
        cand_clean = re.sub(r'[^a-z\s]','', c.get("name","").lower()).strip()

        if name_clean and name_clean in cand_clean:
            lr = _fs_lr("full_name")
            posterior = _fs_update(posterior, lr)
            agreements.append(f"full_name (LR={lr:.0f})")
        elif has_last and last in cand_text and first in cand_text:
            lr = _fs_lr("last_name") * _fs_lr("first_name") ** 0.5
            posterior = _fs_update(posterior, lr)
            agreements.append(f"first+last (LR={lr:.0f})")
        elif has_last and last in cand_text:
            lr = _fs_lr("last_name")
            posterior = _fs_update(posterior, lr)
            agreements.append(f"last_name (LR={lr:.0f})")
        elif first in cand_text:
            lr = _fs_lr("first_name") * 0.3
            posterior = _fs_update(posterior, lr)
            agreements.append(f"first_name_only (LR={lr:.1f})")
        else:
            posterior = _fs_update(posterior, 0.05)

        if context.strip():
            info_text = self._info_text(c)
            ctx_sim   = self._token_similarity(context.lower(), info_text)
            if ctx_sim >= 0.35:
                lr = _fs_lr("context")
                posterior = _fs_update(posterior, lr)
                agreements.append(f"context_overlap={ctx_sim:.2f} (LR={lr:.0f})")
            elif ctx_sim >= 0.15:
                lr = _fs_lr("context") * 0.4
                posterior = _fs_update(posterior, lr)
                agreements.append(f"weak_context (LR={lr:.1f})")

        url = c.get("profile_url","").lower()
        credible = {"linkedin.com","wikipedia.org","github.com",".edu","bloomberg.com","reuters.com","crunchbase.com"}
        if any(d in url for d in credible):
            lr = _fs_lr("credible_src")
            posterior = _fs_update(posterior, lr)
            agreements.append(f"credible_source (LR={lr:.0f})")

        org_kw = ["university","college","institute","corp","company","ltd","inc","foundation","research","lab","bank","tech"]
        info   = self._info_text(c)
        ctx_l  = context.lower()
        if any(kw in info for kw in org_kw) and any(kw in ctx_l for kw in org_kw):
            if set(ctx_l.split()) & set(info.split()):
                lr = _fs_lr("org_match")
                posterior = _fs_update(posterior, lr)
                agreements.append(f"org_match (LR={lr:.0f})")

        nq = "full name match" if (name_clean and name_clean in cand_clean) or (has_last and last in cand_text and first in cand_text) else ("partial match" if has_last and last in cand_text else "name not found")
        c["similarity_score"]  = round(posterior, 3)
        c["fs_posterior"]      = round(posterior, 3)
        c["fs_agreements"]     = agreements
        c["name_match_quality"] = nq
        c["score_breakdown"]   = {
            "name":    round(posterior if "full_name" in str(agreements) else 0, 2),
            "context": round(0.3 if "context" in str(agreements) else 0, 2),
            "signals": round(0.2 if "credible" in str(agreements) else 0, 2),
        }
        return c

    # ── Entity Merging ────────────────────────────────────────────────────

    def is_same_person(self, a: Dict, b: Dict) -> bool:
        name_sim = self._name_similarity(a.get("name",""), b.get("name",""))
        if name_sim < 0.70: return False
        info_a = self._info_text(a)
        info_b = self._info_text(b)
        if self._has_geo_contradiction(info_a, info_b): return False
        if name_sim >= 0.90: return True
        if not info_a.strip() or not info_b.strip(): return True
        return self._token_similarity(info_a, info_b) >= 0.20

    def merge_candidates(self, candidates: List[Dict]) -> List[Dict]:
        if len(candidates) <= 1:
            for c in candidates: self._ensure_sources(c)
            return candidates
        groups: List[List[Dict]] = []
        for cand in candidates:
            placed = False
            for group in groups:
                if any(self.is_same_person(m, cand) for m in group):
                    group.append(cand); placed = True; break
            if not placed:
                groups.append([cand])
        merged = [self._merge_group(g) for g in groups]
        merged.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        return merged

    def _ensure_sources(self, c: Dict) -> None:
        if "sources" not in c or not c["sources"]:
            url = c.get("profile_url") or c.get("url","")
            c["sources"] = [url] if url else []
        if not c.get("profile_url") and c["sources"]:
            c["profile_url"] = c["sources"][0]

    def _merge_group(self, group: List[Dict]) -> Dict:
        for c in group: self._ensure_sources(c)
        if len(group) == 1:
            c = dict(group[0]); c["merged"] = False; c["source_count"] = len(c["sources"]); return c
        rep     = max(group, key=lambda x: x.get("similarity_score", 0))
        sources = list(dict.fromkeys(s for c in group for s in c.get("sources",[]) if s))
        info_parts = list(dict.fromkeys(c.get("extracted_info","").strip() for c in group if c.get("extracted_info","").strip()))
        platforms  = list(dict.fromkeys(c.get("platform","") for c in group if c.get("platform")))
        explanation = f"Merged from {len(group)} sources ({', '.join(platforms[:3])}) via Fellegi-Sunter record linkage. {rep.get('match_explanation','')}"
        return {
            "name":              rep.get("name",""),
            "profile_url":       sources[0] if sources else "",
            "platform":          rep.get("platform",""),
            "extracted_info":    " | ".join(info_parts[:4]),
            "similarity_score":  rep.get("similarity_score", 0),
            "fs_posterior":      rep.get("fs_posterior", 0),
            "fs_agreements":     rep.get("fs_agreements", []),
            "score_breakdown":   rep.get("score_breakdown", {}),
            "match_explanation": explanation,
            "name_match_quality": rep.get("name_match_quality",""),
            "ambiguity_flag":    rep.get("ambiguity_flag", False),
            "sources":           sources,
            "source_count":      len(sources),
            "merged":            True,
        }

    def compare_candidates(self, candidates: List[Dict]) -> List[Dict]:
        if len(candidates) < 2: return []
        top = candidates[0]
        return [self._compare_pair(top, other) for other in candidates[1:]]

    def _compare_pair(self, a: Dict, b: Dict) -> Dict:
        similarities, differences = [], []
        name_sim = self._name_similarity(a.get("name",""), b.get("name",""))
        if name_sim >= 0.80:
            similarities.append(f"Name: {a.get('name','')} ≈ {b.get('name','')}")
        else:
            differences.append(f"Name: \"{a.get('name','')}\" vs \"{b.get('name','')}\"")
        info_a, info_b = self._info_text(a), self._info_text(b)
        locs_a = {g for g in GEO_MARKERS if g in info_a}
        locs_b = {g for g in GEO_MARKERS if g in info_b}
        if locs_a & locs_b:
            similarities.append(f"Location: {', '.join(locs_a & locs_b)}")
        elif locs_a and locs_b:
            differences.append(f"Location: {', '.join(locs_a)} vs {', '.join(locs_b)}")
        ctx_sim = self._token_similarity(info_a, info_b)
        if ctx_sim >= 0.40:
            similarities.append(f"Context: {int(ctx_sim*100)}% overlapping keywords")
        elif ctx_sim < 0.10 and info_a and info_b:
            differences.append("Description: very different — likely distinct individuals")
        return {"candidate": b.get("name","Unknown"), "vs": a.get("name","Top candidate"), "similarities": similarities, "differences": differences}

    # ── Pipeline Helpers ──────────────────────────────────────────────────

    def _parse_name(self, name: str) -> Dict:
        parts = name.strip().split()
        return {"full": name.strip().lower(), "first": parts[0].lower() if parts else "", "last": parts[-1].lower() if len(parts) > 1 else "", "parts": [p.lower() for p in parts], "has_last": len(parts) > 1}

    def _hard_filter(self, results: List[Dict], name_parts: Dict) -> List[Dict]:
        if not name_parts["has_last"]: return results
        last = name_parts["last"]
        kept = [r for r in results if last in (r["title"]+" "+r["snippet"]+" "+r["url"]).lower()]
        logger.info(f"Hard filter: {len(results)} → {len(kept)}")
        return kept

    def _collect_results(self, name: str, context: str) -> List[Dict]:
        all_results, seen_urls = [], set()
        for platform in PLATFORMS:
            try:
                query = (f'"{name}" {context} site:{platform["site"]}' if platform["site"] else f'"{name}" {context} biography profile')
                with DDGS() as ddgs:
                    hits = list(ddgs.text(query, max_results=3))
                for h in hits:
                    url = h.get("href","")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append({"url": url, "title": h.get("title",""), "snippet": h.get("body","")[:300], "platform": platform["name"], "weight": platform["weight"]})
            except Exception as e:
                logger.warning(f"Search failed for {platform['name']}: {e}")
        return all_results

    def _extract_candidates(self, name: str, context: str, results: List[Dict], name_parts: Dict) -> List[Dict]:
        if not results: return []
        results_text = "\n".join([f"[{i}] Platform: {r['platform']}\nURL: {r['url']}\nTitle: {r['title']}\nSnippet: {r['snippet']}" for i, r in enumerate(results[:15])])
        last = name_parts["last"]
        prompt = f"""I searched for a person named "{name}" with context: "{context}".
Extract structured information about people named "{name}" in these results.
RULES: Every entry MUST contain the last name "{last}" — skip any that do not. One entry per URL.
Results:\n{results_text}
Return a JSON array. Each item:
- "name": exact name as written
- "profile_url": the URL
- "platform": platform name
- "extracted_info": job title, organization, location (max 100 chars)
- "match_explanation": one sentence
- "ambiguity_flag": true if name matches multiple people
Return ONLY the JSON array. Return [] if no valid entries."""
        try:
            msg = self.client.messages.create(model=config.CLAUDE_MODEL, max_tokens=2000, temperature=0, messages=[{"role": "user", "content": prompt}])
            raw = re.sub(r'^```json\s*','',msg.content[0].text.strip())
            raw = re.sub(r'\s*```$','',raw)
            candidates = json.loads(raw)
            if name_parts["has_last"]:
                candidates = [c for c in candidates if last in (c.get("name","") + c.get("extracted_info","")).lower()]
            for c in candidates:
                c["sources"] = [c["profile_url"]] if c.get("profile_url") else []
            return candidates[:12]
        except Exception as e:
            logger.error(f"Candidate extraction failed: {e}")
            return []

    def _determine_status(self, candidates: List[Dict]) -> str:
        if not candidates: return "INSUFFICIENT_DATA"
        top = candidates[0].get("similarity_score", 0)
        if len(candidates) == 1:
            if top >= 0.85: return "LIKELY_MATCH"
            if top >= 0.65: return "LOW_AMBIGUITY"
            return "INSUFFICIENT_DATA"
        second = candidates[1].get("similarity_score", 0)
        return "MULTIPLE_CANDIDATES" if (top - second) >= 0.20 else "AMBIGUOUS"

    def _build_warning(self, status: str, count: int) -> str:
        return {
            "LIKELY_MATCH": "ℹ️ One candidate with high F-S posterior (≥0.85). Human review required.",
            "LOW_AMBIGUITY": "ℹ️ One primary candidate with moderate F-S posterior (0.65–0.85). Verify manually.",
            "MULTIPLE_CANDIDATES": f"ℹ️ {count} distinct candidates. Top result has significantly higher F-S score.",
            "AMBIGUOUS": f"⚠️ {count} candidates with similar F-S scores — identity ambiguous.",
            "INSUFFICIENT_DATA": "⚠️ Insufficient evidence for F-S matching. Add context (job, location, organisation).",
        }.get(status, "⚠️ Unknown status.")

    def _name_similarity(self, a: str, b: str) -> float:
        def tok(s): return {t.lower() for t in re.sub(r'[,.()[\]"\']+', ' ', s).split() if t.lower() not in STOP_WORDS and len(t) > 1}
        ta, tb = tok(a), tok(b)
        if not ta or not tb: return 0.0
        return len(ta & tb) / len(ta | tb)

    def _token_similarity(self, a: str, b: str) -> float:
        def tok(s): return {t.lower().strip(".,;:'\"()") for t in s.split() if t.lower() not in STOP_WORDS and len(t) > 2}
        ta, tb = tok(a), tok(b)
        if not ta or not tb: return 0.0
        return len(ta & tb) / len(ta | tb)

    def _has_geo_contradiction(self, a: str, b: str) -> bool:
        la = {g for g in GEO_MARKERS if g in a}
        lb = {g for g in GEO_MARKERS if g in b}
        return bool(la and lb and not (la & lb))

    def _info_text(self, c: Dict) -> str:
        return (c.get("extracted_info","") + " " + c.get("match_explanation","")).lower().strip()
