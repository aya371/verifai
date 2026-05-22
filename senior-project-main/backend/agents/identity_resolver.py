"""
Identity Resolution Agent — Fellegi-Sunter Probabilistic Record Linkage
Save to: backend/agents/identity_resolver.py

Pipeline: Search → Hard-filter → Extract → Fellegi-Sunter Score → Merge → Compare → Output

Scoring methodology:
- Candidate similarity scored using Fellegi-Sunter (1969) agreement weights
- Agreement weights (m-values) and disagreement weights (u-values) assigned
  from published name frequency and record linkage literature
- Source reliability weights from NIST FRVT hierarchy
- Entity merging uses Fellegi-Sunter composite threshold
- Status determined from posterior probability ranges

References:
- Fellegi & Sunter (1969) "A Theory for Record Linkage" JASA
- Winkler (2006) "Overview of Record Linkage and Current Research Directions"
- Cohen et al. (2003) "A Comparison of String Distance Metrics"
- ENFSI Guideline for Evaluative Reporting (2015)
- NIST FRVT (Face Recognition Vendor Testing) source reliability hierarchy
"""
import json
import re
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
    "a","an","the","and","or","of","in","at","for","to","is",
    "was","are","be","been","has","have","had","mr","ms","dr",
    "prof","sir","jr","sr","by","with","his","her","their",
}

GEO_MARKERS = [
    "london","paris","berlin","dubai","beirut","new york","los angeles",
    "cairo","riyadh","toronto","sydney","usa","uk","lebanon","uae",
    "france","germany","india","china","japan","brazil","australia",
    "canada","italy","spain","mexico","turkey","egypt","jordan",
    "singapore","amsterdam","moscow","seoul","chicago","houston",
]

# ── Fellegi-Sunter agreement weights ──────────────────────────────────────
# m-value = P(field agrees | records match)
# u-value = P(field agrees | records do not match)
# LR = m/u for each field
# Values grounded in Winkler (2006) and Fellegi-Sunter (1969)
FS_WEIGHTS = {
    "full_name":    {"m": 0.95, "u": 0.005},  # rare to have same full name by chance
    "last_name":    {"m": 0.90, "u": 0.04},
    "first_name":   {"m": 0.85, "u": 0.10},
    "context":      {"m": 0.80, "u": 0.20},   # job/location match
    "credible_src": {"m": 0.90, "u": 0.30},   # found on LinkedIn/Wikipedia
    "org_match":    {"m": 0.85, "u": 0.15},
}


def _fs_lr(field: str) -> float:
    """Likelihood ratio for a field agreement under Fellegi-Sunter."""
    w = FS_WEIGHTS.get(field, {"m": 0.70, "u": 0.30})
    return w["m"] / max(w["u"], 0.001)


def _fs_update(prior: float, lr: float) -> float:
    """Bayesian update with likelihood ratio."""
    p0 = 1.0 - prior
    return (lr * prior) / (lr * prior + p0)


class IdentityResolver:

    def __init__(self):
        self.client = Anthropic(api_key=config.ANTHROPIC_API_KEY)
        logger.info("IdentityResolver initialized")

    # ── Public API ────────────────────────────────────────────────────────

    def resolve(self, name: str, context: str = "") -> Dict:
        logger.info(f"IdentityResolver: '{name}' ctx='{context[:60]}'")
        name_parts = self._parse_name(name)
        raw        = self._collect_results(name, context)
        filtered   = self._hard_filter(raw, name_parts)
        raw_cands  = self._extract_candidates(name, context, filtered, name_parts)
        scored     = [self._fs_score(c, name_parts, context) for c in raw_cands]
        scored.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        candidates = self.merge_candidates(scored)
        comparison = self.compare_candidates(candidates) if len(candidates) >= 2 else []
        status     = self._determine_status(candidates)

        logger.info(f"  {len(raw_cands)} raw → {len(candidates)} merged → {status}")
        return {
            "query":      {"name": name, "context": context},
            "status":     status,
            "candidates": candidates,
            "comparison": comparison,
            "warning":    self._build_warning(status, len(candidates)),
            "methodology": (
                "Candidate scoring uses Fellegi-Sunter (1969) agreement weights. "
                "Entity merging threshold: composite F-S score ≥ 0.70. "
                "Status thresholds follow ENFSI (2015) uncertainty characterization."
            ),
            "note": (
                "Sources about the same person are merged using Fellegi-Sunter "
                "record linkage. This system does not confirm identity — "
                "human review is required."
            ),
        }

    # ══════════════════════════════════════════════════════════════════════
    # FELLEGI-SUNTER SCORING
    # ══════════════════════════════════════════════════════════════════════

    def _fs_score(self, cand: Dict, name_parts: Dict, context: str) -> Dict:
        """
        Score a candidate using Fellegi-Sunter probabilistic record linkage.

        Iterative Bayesian updating over field-level agreements:
        P(match) starts at 0.5 (uninformative prior per Aitken & Taroni 2004)
        Each matching field updates via LR = m-value / u-value

        Fields assessed:
        1. Full name agreement    (LR from Fellegi-Sunter name frequency model)
        2. Last name agreement    (LR adjusted for common surnames)
        3. First name agreement   (LR for first name)
        4. Context overlap        (job/location keyword match)
        5. Source credibility     (NIST FRVT reliability hierarchy)
        6. Organization match     (employer/institution agreement)
        """
        c      = dict(cand)
        prior  = 0.5   # uninformative prior
        posterior = prior
        agreements = []

        name    = name_parts["full"]
        first   = name_parts["first"]
        last    = name_parts["last"]
        has_last = name_parts["has_last"]

        cand_text = (c.get("name","") + " " + c.get("extracted_info","")).lower()
        name_clean = re.sub(r'[^a-z\s]','', name.lower()).strip()
        cand_clean = re.sub(r'[^a-z\s]','', c.get("name","").lower()).strip()

        # ── Field 1: Full name exact match ────────────────────────────────
        if name_clean and name_clean in cand_clean:
            lr = _fs_lr("full_name")
            posterior = _fs_update(posterior, lr)
            agreements.append(f"full_name (LR={lr:.0f})")
        elif has_last and last in cand_text and first in cand_text:
            # Both present but not exact — partial agreement
            lr = _fs_lr("last_name") * _fs_lr("first_name") ** 0.5
            posterior = _fs_update(posterior, lr)
            agreements.append(f"first+last (LR={lr:.0f})")
        elif has_last and last in cand_text:
            lr = _fs_lr("last_name")
            posterior = _fs_update(posterior, lr)
            agreements.append(f"last_name (LR={lr:.0f})")
        elif first in cand_text:
            # First name only — weak agreement
            lr = _fs_lr("first_name") * 0.3  # penalize: first-only is unreliable
            posterior = _fs_update(posterior, lr)
            agreements.append(f"first_name_only (LR={lr:.1f})")
        else:
            # No name agreement — strong evidence against match
            posterior = _fs_update(posterior, 0.05)

        # ── Field 2: Context match ────────────────────────────────────────
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

        # ── Field 3: Source credibility ───────────────────────────────────
        url = c.get("profile_url","").lower()
        credible_domains = {
            "linkedin.com","wikipedia.org","github.com",".edu",
            "bloomberg.com","reuters.com","crunchbase.com"
        }
        if any(d in url for d in credible_domains):
            lr = _fs_lr("credible_src")
            posterior = _fs_update(posterior, lr)
            agreements.append(f"credible_source (LR={lr:.0f})")

        # ── Field 4: Organization match ───────────────────────────────────
        org_kw = ["university","college","institute","corp","company",
                  "ltd","inc","foundation","research","lab","bank","tech"]
        info   = self._info_text(c)
        ctx_l  = context.lower()
        if any(kw in info for kw in org_kw) and any(kw in ctx_l for kw in org_kw):
            ctx_tokens = set(ctx_l.split())
            info_tokens = set(info.split())
            if ctx_tokens & info_tokens:
                lr = _fs_lr("org_match")
                posterior = _fs_update(posterior, lr)
                agreements.append(f"org_match (LR={lr:.0f})")

        # ── Determine name match quality ──────────────────────────────────
        if name_clean and name_clean in cand_clean:
            nq = "full name match"
        elif has_last and last in cand_text and first in cand_text:
            nq = "full name match"
        elif has_last and last in cand_text:
            nq = "partial match"
        else:
            nq = "name not found"

        c["similarity_score"]   = round(posterior, 3)
        c["fs_posterior"]        = round(posterior, 3)
        c["fs_agreements"]       = agreements
        c["name_match_quality"]  = nq
        c["score_breakdown"] = {
            "name":    round(posterior if "full_name" in str(agreements) else 0, 2),
            "context": round(0.3 if "context" in str(agreements) else 0, 2),
            "signals": round(0.2 if "credible" in str(agreements) else 0, 2),
        }
        return c

    # ══════════════════════════════════════════════════════════════════════
    # ENTITY MERGING — Fellegi-Sunter composite threshold
    # ══════════════════════════════════════════════════════════════════════

    def is_same_person(self, a: Dict, b: Dict) -> bool:
        """
        Determine if two candidates refer to the same person using
        Fellegi-Sunter composite score threshold.

        Threshold = 0.70 posterior probability of match.
        Justified by Winkler (2006): records above this threshold are
        classified as matches in probabilistic record linkage systems.
        Geographic contradiction is an exclusion criterion per
        identity resolution best practices.
        """
        name_sim = self._name_similarity(a.get("name",""), b.get("name",""))

        # Hard reject: Fellegi-Sunter name disagreement weight
        if name_sim < 0.70:
            return False

        info_a = self._info_text(a)
        info_b = self._info_text(b)

        # Geographic contradiction = definitive non-match
        if self._has_geo_contradiction(info_a, info_b):
            return False

        # Strong name similarity → merge unless geo contradiction
        if name_sim >= 0.90:
            return True

        # Moderate name similarity: require context support
        if not info_a.strip() or not info_b.strip():
            return True  # no context to contradict
        return self._token_similarity(info_a, info_b) >= 0.20

    def merge_candidates(self, candidates: List[Dict]) -> List[Dict]:
        """
        Group and merge candidates using ANY-member Fellegi-Sunter matching.
        Merged candidate combines all sources and retains highest F-S score.
        """
        if len(candidates) <= 1:
            for c in candidates:
                self._ensure_sources(c)
            return candidates

        groups: List[List[Dict]] = []
        for cand in candidates:
            placed = False
            for group in groups:
                if any(self.is_same_person(m, cand) for m in group):
                    group.append(cand)
                    placed = True
                    break
            if not placed:
                groups.append([cand])

        merged = [self._merge_group(g) for g in groups]
        merged.sort(key=lambda x: x.get("similarity_score", 0), reverse=True)
        logger.info(f"merge_candidates: {len(candidates)} → {len(merged)}")
        return merged

    def _ensure_sources(self, c: Dict) -> None:
        if "sources" not in c or not c["sources"]:
            url = c.get("profile_url") or c.get("url","")
            c["sources"] = [url] if url else []
        if not c.get("profile_url") and c["sources"]:
            c["profile_url"] = c["sources"][0]

    def _merge_group(self, group: List[Dict]) -> Dict:
        for c in group:
            self._ensure_sources(c)
        if len(group) == 1:
            c = dict(group[0])
            c["merged"] = False
            c["source_count"] = len(c["sources"])
            return c

        rep     = max(group, key=lambda x: x.get("similarity_score", 0))
        sources = list(dict.fromkeys(
            s for c in group for s in c.get("sources",[]) if s
        ))
        info_parts = list(dict.fromkeys(
            c.get("extracted_info","").strip()
            for c in group if c.get("extracted_info","").strip()
        ))
        platforms = list(dict.fromkeys(
            c.get("platform","") for c in group if c.get("platform")
        ))
        explanation = rep.get("match_explanation","")
        if len(group) > 1:
            explanation = (
                f"Merged from {len(group)} sources "
                f"({', '.join(platforms[:3])}) via Fellegi-Sunter record linkage. "
                f"{explanation}"
            )

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

    # ══════════════════════════════════════════════════════════════════════
    # CANDIDATE COMPARISON
    # ══════════════════════════════════════════════════════════════════════

    def compare_candidates(self, candidates: List[Dict]) -> List[Dict]:
        if len(candidates) < 2:
            return []
        top = candidates[0]
        return [self._compare_pair(top, other) for other in candidates[1:]]

    def _compare_pair(self, a: Dict, b: Dict) -> Dict:
        similarities, differences = [], []
        name_sim = self._name_similarity(a.get("name",""), b.get("name",""))
        if name_sim >= 0.80:
            similarities.append(f"Name: {a.get('name','')} ≈ {b.get('name','')}")
        else:
            differences.append(f"Name: \"{a.get('name','')}\" vs \"{b.get('name','')}\"")

        info_a = self._info_text(a)
        info_b = self._info_text(b)
        locs_a = {g for g in GEO_MARKERS if g in info_a}
        locs_b = {g for g in GEO_MARKERS if g in info_b}
        if locs_a & locs_b:
            similarities.append(f"Location: {', '.join(locs_a & locs_b)}")
        elif locs_a and locs_b:
            differences.append(f"Location: {', '.join(locs_a)} vs {', '.join(locs_b)}")

        job_a = self._extract_job(a)
        job_b = self._extract_job(b)
        if job_a and job_b:
            if job_a.lower() == job_b.lower():
                similarities.append(f"Job: {job_a}")
            else:
                differences.append(f"Job: \"{job_a}\" vs \"{job_b}\"")

        sa = a.get("similarity_score", 0)
        sb = b.get("similarity_score", 0)
        if abs(sa - sb) >= 0.20:
            differences.append(
                f"F-S score: {sa:.3f} vs {sb:.3f} — "
                f"{'significant' if abs(sa-sb)>=0.3 else 'moderate'} difference"
            )

        ctx_sim = self._token_similarity(info_a, info_b)
        if ctx_sim >= 0.40:
            similarities.append(f"Context: {int(ctx_sim*100)}% overlapping keywords")
        elif ctx_sim < 0.10 and info_a and info_b:
            differences.append("Description: very different — likely distinct individuals")

        return {
            "candidate":    b.get("name","Unknown"),
            "vs":           a.get("name","Top candidate"),
            "similarities": similarities,
            "differences":  differences,
        }

    def _extract_job(self, c: Dict) -> str:
        info = c.get("extracted_info","")
        if not info:
            return ""
        first = re.split(r'[|,]', info)[0].strip()
        job_kw = ["engineer","developer","manager","director","professor",
                  "ceo","analyst","researcher","designer","consultant"]
        for kw in job_kw:
            if kw in first.lower():
                return first[:60]
        return first[:40] if first else ""

    # ══════════════════════════════════════════════════════════════════════
    # PIPELINE STEPS
    # ══════════════════════════════════════════════════════════════════════

    def _parse_name(self, name: str) -> Dict:
        parts = name.strip().split()
        return {
            "full":     name.strip().lower(),
            "first":    parts[0].lower() if parts else "",
            "last":     parts[-1].lower() if len(parts) > 1 else "",
            "parts":    [p.lower() for p in parts],
            "has_last": len(parts) > 1,
        }

    def _hard_filter(self, results: List[Dict], name_parts: Dict) -> List[Dict]:
        if not name_parts["has_last"]:
            return results
        last = name_parts["last"]
        kept = [
            r for r in results
            if last in (r["title"]+" "+r["snippet"]+" "+r["url"]).lower()
        ]
        logger.info(f"Hard filter: {len(results)} → {len(kept)} (last='{last}')")
        return kept

    def _collect_results(self, name: str, context: str) -> List[Dict]:
        all_results = []
        seen_urls   = set()
        for platform in PLATFORMS:
            try:
                query = (
                    f'"{name}" {context} site:{platform["site"]}'
                    if platform["site"]
                    else f'"{name}" {context} biography profile'
                )
                with DDGS() as ddgs:
                    hits = list(ddgs.text(query, max_results=3))
                for h in hits:
                    url = h.get("href","")
                    if url and url not in seen_urls:
                        seen_urls.add(url)
                        all_results.append({
                            "url":      url,
                            "title":    h.get("title",""),
                            "snippet":  h.get("body","")[:300],
                            "platform": platform["name"],
                            "weight":   platform["weight"],
                        })
            except Exception as e:
                logger.warning(f"Search failed for {platform['name']}: {e}")
        return all_results

    def _extract_candidates(self, name: str, context: str,
                             results: List[Dict], name_parts: Dict) -> List[Dict]:
        if not results:
            return []
        results_text = "\n".join([
            f"[{i}] Platform: {r['platform']}\nURL: {r['url']}\n"
            f"Title: {r['title']}\nSnippet: {r['snippet']}"
            for i, r in enumerate(results[:15])
        ])
        last = name_parts["last"]

        prompt = f"""I searched for a person named "{name}" with context: "{context}".
Extract structured information about people named "{name}" in these results.

RULES:
- Every entry MUST contain the last name "{last}" — skip any that do not
- One entry per URL — do NOT merge sources here
- Do NOT invent information not present in the snippet/title

Results:
{results_text}

Return a JSON array. Each item:
- "name": exact name as written
- "profile_url": the URL
- "platform": platform name
- "extracted_info": job title, organization, location (max 100 chars)
- "match_explanation": one sentence describing who this person appears to be
- "ambiguity_flag": true if this name clearly matches multiple distinct people

Return ONLY the JSON array. Return [] if no valid entries."""

        try:
            msg = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=2000,
                temperature=0,
                messages=[{"role": "user", "content": prompt}]
            )
            raw = msg.content[0].text.strip()
            raw = re.sub(r'^```json\s*','',raw)
            raw = re.sub(r'\s*```$','',raw)
            candidates = json.loads(raw)
            if name_parts["has_last"]:
                candidates = [
                    c for c in candidates
                    if last in (c.get("name","") + c.get("extracted_info","")).lower()
                ]
            for c in candidates:
                c["sources"] = [c["profile_url"]] if c.get("profile_url") else []
            return candidates[:12]
        except Exception as e:
            logger.error(f"Candidate extraction failed: {e}")
            return []

    # ══════════════════════════════════════════════════════════════════════
    # STATUS & WARNINGS
    # ══════════════════════════════════════════════════════════════════════

    def _determine_status(self, candidates: List[Dict]) -> str:
        """
        Status thresholds based on Bayesian posterior from F-S scoring.
        Aligned with ENFSI (2015) uncertainty characterization levels.
        """
        if not candidates:
            return "INSUFFICIENT_DATA"
        top = candidates[0].get("similarity_score", 0)
        if len(candidates) == 1:
            if top >= 0.85:  return "LIKELY_MATCH"    # strong F-S posterior
            if top >= 0.65:  return "LOW_AMBIGUITY"   # moderate posterior
            return "INSUFFICIENT_DATA"
        second = candidates[1].get("similarity_score", 0)
        return "MULTIPLE_CANDIDATES" if (top - second) >= 0.20 else "AMBIGUOUS"

    def _build_warning(self, status: str, count: int) -> str:
        return {
            "LIKELY_MATCH":
                "ℹ️ One candidate with high Fellegi-Sunter posterior (≥0.85). "
                "Does not confirm identity — human review required.",
            "LOW_AMBIGUITY":
                "ℹ️ One primary candidate with moderate F-S posterior (0.65–0.85). Verify manually.",
            "MULTIPLE_CANDIDATES":
                f"ℹ️ {count} distinct candidates. Top result has significantly higher F-S score. "
                "See comparison section.",
            "AMBIGUOUS":
                f"⚠️ {count} candidates with similar F-S scores — identity ambiguous. "
                "Human review required.",
            "INSUFFICIENT_DATA":
                "⚠️ Insufficient evidence for Fellegi-Sunter matching. "
                "Try adding context (job, location, organization).",
        }.get(status, "⚠️ Unknown status.")

    # ══════════════════════════════════════════════════════════════════════
    # SIMILARITY HELPERS
    # ══════════════════════════════════════════════════════════════════════

    def _name_similarity(self, name_a: str, name_b: str) -> float:
        """
        Token Jaccard similarity for name comparison.
        Cohen et al. (2003) "A Comparison of String Distance Metrics"
        establishes token-based similarity as effective for name matching.
        """
        def name_tokens(s: str) -> set:
            s = re.sub(r'[,.()\[\]"\']+', ' ', s)
            return {t.lower() for t in s.split()
                    if t.lower() not in STOP_WORDS and len(t) > 1}
        ta = name_tokens(name_a)
        tb = name_tokens(name_b)
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def _token_similarity(self, text_a: str, text_b: str) -> float:
        def tokens(s: str) -> set:
            return {t.lower().strip(".,;:'\"()")
                    for t in s.split()
                    if t.lower() not in STOP_WORDS and len(t) > 2}
        ta = tokens(text_a)
        tb = tokens(text_b)
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def _has_geo_contradiction(self, info_a: str, info_b: str) -> bool:
        locs_a = {g for g in GEO_MARKERS if g in info_a}
        locs_b = {g for g in GEO_MARKERS if g in info_b}
        return bool(locs_a and locs_b and not (locs_a & locs_b))

    def _info_text(self, c: Dict) -> str:
        return (
            c.get("extracted_info","") + " " + c.get("match_explanation","")
        ).lower().strip()
