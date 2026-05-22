"""
Trust Explainer — Cross-Engine Intelligence Layer
==================================================
Implements:
  1. Cross-Engine Conflict Map  — CV claims vs OSINT findings (match/partial/conflict)
  2. Trust Explanation Engine   — why trusted, why not, what is missing

Save to: backend/agents/trust_explainer.py
"""
import re
from typing import Dict, List, Optional
from backend.utils.logger import logger


class CrossEngineConflictMap:
    """
    Compares CV Engine output vs OSINT Engine output field-by-field.
    Each field returns: match | partial | conflict | unverified
    """

    GEO_MARKERS = [
        "london","paris","berlin","dubai","beirut","new york","los angeles","cairo",
        "riyadh","toronto","sydney","usa","uk","lebanon","uae","france","germany",
        "india","china","japan","brazil","australia","canada","italy","spain","mexico",
        "turkey","egypt","jordan","singapore","amsterdam",
    ]
    JOB_KEYWORDS = [
        "engineer","developer","manager","director","analyst","architect","designer",
        "consultant","researcher","professor","doctor","scientist","ceo","cto","cfo","founder",
        "intern","officer","specialist","coordinator","lead","head",
    ]

    def compare(self, cv_result: Dict, osint_result: Dict) -> Dict:
        """
        Run field-by-field comparison.
        Returns a structured conflict map with per-field verdicts.
        """
        if not cv_result or not osint_result:
            return {
                "fields":        [],
                "summary":       {"matches": 0, "partials": 0, "conflicts": 0, "unverified": 0},
                "overall_alignment": "insufficient_data",
                "note": "Both CV and OSINT results required for conflict mapping.",
            }

        claims    = cv_result.get("claims", [])
        candidates = osint_result.get("candidates", [])
        top        = candidates[0] if candidates else {}

        cv_text_combined = " ".join(c.get("claim","") for c in claims).lower()
        osint_text       = (
            top.get("extracted_info","") + " " +
            top.get("match_explanation","") + " " +
            " ".join(top.get("sources",[]))
        ).lower()

        fields = []

        # Role / Job Title
        cv_role   = self._extract_role(cv_text_combined)
        osint_role = self._extract_role(osint_text)
        fields.append(self._compare_field(
            "Role / Job Title", cv_role, osint_role,
            source_cv="CV claims", source_osint="LinkedIn / public profile"
        ))

        # Location
        cv_locs    = {g for g in self.GEO_MARKERS if g in cv_text_combined}
        osint_locs = {g for g in self.GEO_MARKERS if g in osint_text}
        fields.append(self._compare_location(cv_locs, osint_locs))

        # Employer / Organisation
        cv_orgs    = self._extract_orgs(claims)
        osint_orgs = self._extract_orgs_from_text(osint_text)
        fields.append(self._compare_orgs(cv_orgs, osint_orgs))

        # Education
        cv_edu    = [c.get("claim","") for c in claims if c.get("type") == "education"]
        osint_edu = self._find_education_signals(osint_text)
        fields.append(self._compare_education(cv_edu, osint_edu, osint_text))

        # Consistency analyzer conflicts
        consistency = cv_result.get("consistency",{})  # may be in orchestrator result
        if consistency:
            for item in consistency.get("inconsistent",[])[:3]:
                fields.append({
                    "field":       "CV Claim vs Profile",
                    "cv_value":    item.get("claim","")[:80],
                    "osint_value": item.get("conflict","Contradicted by profile data")[:80],
                    "verdict":     "conflict",
                    "detail":      item.get("reason","")[:150],
                    "severity":    "high",
                })

        # Summarise
        matches    = sum(1 for f in fields if f["verdict"] == "match")
        partials   = sum(1 for f in fields if f["verdict"] == "partial")
        conflicts  = sum(1 for f in fields if f["verdict"] == "conflict")
        unverified = sum(1 for f in fields if f["verdict"] == "unverified")

        if conflicts >= 2:
            overall = "high_conflict"
        elif conflicts == 1 or partials >= 2:
            overall = "partial_conflict"
        elif matches >= 2:
            overall = "aligned"
        else:
            overall = "insufficient_data"

        return {
            "fields":   fields,
            "summary":  {
                "matches":    matches,
                "partials":   partials,
                "conflicts":  conflicts,
                "unverified": unverified,
            },
            "overall_alignment": overall,
            "note": self._alignment_note(overall, matches, conflicts),
        }

    def _compare_field(self, name: str, cv_val: str, osint_val: str,
                        source_cv="CV", source_osint="OSINT") -> Dict:
        if not cv_val and not osint_val:
            return {"field": name, "cv_value": "not found", "osint_value": "not found",
                    "verdict": "unverified", "detail": "Neither source contains this field.", "severity": "low"}
        if not cv_val:
            return {"field": name, "cv_value": "not specified", "osint_value": osint_val,
                    "verdict": "unverified", "detail": f"CV does not mention this field. {source_osint} says: {osint_val}.", "severity": "low"}
        if not osint_val:
            return {"field": name, "cv_value": cv_val, "osint_value": "not found in OSINT",
                    "verdict": "unverified", "detail": f"CV claims: {cv_val}. No OSINT confirmation.", "severity": "low"}

        overlap = self._token_overlap(cv_val, osint_val)
        if overlap >= 0.40:
            verdict = "match"
            detail  = f"Both sources agree: '{cv_val}'."
            severity= "none"
        elif overlap >= 0.15:
            verdict = "partial"
            detail  = f"CV: '{cv_val}' / OSINT: '{osint_val}' — partial alignment."
            severity= "medium"
        else:
            verdict = "conflict"
            detail  = f"CV states '{cv_val}' but OSINT shows '{osint_val}'."
            severity= "high"

        return {"field": name, "cv_value": cv_val, "osint_value": osint_val,
                "verdict": verdict, "detail": detail, "severity": severity}

    def _compare_location(self, cv_locs: set, osint_locs: set) -> Dict:
        if not cv_locs and not osint_locs:
            return {"field": "Location", "cv_value": "not specified", "osint_value": "not found",
                    "verdict": "unverified", "detail": "No location data in either source.", "severity": "low"}
        if not cv_locs:
            return {"field": "Location", "cv_value": "not specified", "osint_value": ", ".join(osint_locs),
                    "verdict": "unverified", "detail": "CV has no location. OSINT indicates: " + ", ".join(osint_locs), "severity": "low"}
        if not osint_locs:
            return {"field": "Location", "cv_value": ", ".join(cv_locs), "osint_value": "not found in OSINT",
                    "verdict": "unverified", "detail": f"CV indicates: {', '.join(cv_locs)}. Not confirmed by OSINT.", "severity": "low"}
        shared = cv_locs & osint_locs
        if shared:
            return {"field": "Location", "cv_value": ", ".join(cv_locs), "osint_value": ", ".join(osint_locs),
                    "verdict": "match", "detail": f"Consistent location: {', '.join(shared)}.", "severity": "none"}
        return {"field": "Location", "cv_value": ", ".join(cv_locs), "osint_value": ", ".join(osint_locs),
                "verdict": "conflict", "detail": f"CV: {', '.join(cv_locs)} vs OSINT: {', '.join(osint_locs)} — geographic mismatch.", "severity": "high"}

    def _compare_orgs(self, cv_orgs: List[str], osint_orgs: str) -> Dict:
        if not cv_orgs:
            return {"field": "Employer / Organisation", "cv_value": "not extracted", "osint_value": osint_orgs or "not found",
                    "verdict": "unverified", "detail": "No employer found in CV claims.", "severity": "low"}
        primary_org = cv_orgs[0]
        if osint_orgs and self._token_overlap(primary_org, osint_orgs) >= 0.30:
            return {"field": "Employer / Organisation", "cv_value": primary_org, "osint_value": osint_orgs,
                    "verdict": "match", "detail": f"Employer '{primary_org}' confirmed in OSINT.", "severity": "none"}
        if osint_orgs:
            return {"field": "Employer / Organisation", "cv_value": primary_org, "osint_value": osint_orgs,
                    "verdict": "conflict", "detail": f"CV claims '{primary_org}' but OSINT mentions '{osint_orgs}'.", "severity": "high"}
        return {"field": "Employer / Organisation", "cv_value": primary_org, "osint_value": "not found in OSINT",
                "verdict": "unverified", "detail": f"Employer '{primary_org}' not confirmed in OSINT.", "severity": "medium"}

    def _compare_education(self, cv_edu: List[str], osint_edu: str, osint_text: str) -> Dict:
        if not cv_edu:
            return {"field": "Education", "cv_value": "not specified", "osint_value": osint_edu or "not found",
                    "verdict": "unverified", "detail": "No education claims in CV.", "severity": "low"}
        primary = cv_edu[0]
        edu_words = [w.lower() for w in primary.split() if len(w) > 4]
        matches   = sum(1 for w in edu_words if w in osint_text)
        if matches >= len(edu_words) * 0.5:
            return {"field": "Education", "cv_value": primary[:80], "osint_value": osint_edu or "partial match in OSINT",
                    "verdict": "match", "detail": f"Education '{primary[:60]}' partially confirmed in OSINT.", "severity": "none"}
        return {"field": "Education", "cv_value": primary[:80], "osint_value": "not confirmed",
                "verdict": "unverified", "detail": f"Education '{primary[:60]}' not confirmed in OSINT.", "severity": "medium"}

    def _extract_role(self, text: str) -> str:
        for kw in self.JOB_KEYWORDS:
            idx = text.find(kw)
            if idx != -1:
                start = max(0, idx - 10)
                return text[start:min(len(text), idx + 50)].strip()[:80]
        return ""

    def _extract_orgs(self, claims: List[Dict]) -> List[str]:
        ORG_TYPES = ["university","college","institute","corp","company","ltd","inc","foundation","research","lab","bank","tech"]
        orgs = []
        for c in claims:
            info = c.get("claim","").lower()
            if any(ot in info for ot in ORG_TYPES):
                orgs.append(c.get("claim","")[:60])
        return list(dict.fromkeys(orgs))[:3]

    def _extract_orgs_from_text(self, text: str) -> str:
        ORG_TYPES = ["university","college","institute","corp","company","ltd","inc","foundation","research","lab","bank","tech"]
        for ot in ORG_TYPES:
            idx = text.find(ot)
            if idx != -1:
                return text[max(0, idx-15):min(len(text), idx+50)].strip()[:60]
        return ""

    def _find_education_signals(self, text: str) -> str:
        EDU_KW = ["university","college","degree","bachelor","master","phd","bsc","msc","mba"]
        for kw in EDU_KW:
            if kw in text:
                idx = text.find(kw)
                return text[max(0,idx-10):min(len(text),idx+60)].strip()[:80]
        return ""

    def _token_overlap(self, a: str, b: str) -> float:
        STOP = {"a","an","the","and","or","of","in","at","for","to","is","was","are"}
        def tok(s): return {w.lower() for w in s.split() if len(w) > 2 and w.lower() not in STOP}
        ta, tb = tok(a), tok(b)
        if not ta or not tb: return 0.0
        return len(ta & tb) / len(ta | tb)

    def _alignment_note(self, overall: str, matches: int, conflicts: int) -> str:
        return {
            "aligned":            f"{matches} field(s) align between CV and OSINT — high cross-engine consistency.",
            "partial_conflict":   f"{conflicts} conflict(s) detected. Review flagged fields before making a decision.",
            "high_conflict":      f"{conflicts} serious conflicts between CV claims and OSINT findings. Human investigation required.",
            "insufficient_data":  "Not enough data from both engines to generate a meaningful comparison.",
        }.get(overall, "Cross-engine comparison inconclusive.")


class TrustExplainer:
    """
    Generates a human-readable explanation of:
      - Why the subject IS trusted (positive signals)
      - Why the subject is NOT trusted (negative signals)
      - What is missing (gaps that prevent a conclusion)
    """

    def explain(
        self,
        cv_result:    Optional[Dict],
        osint_result: Optional[Dict],
        conflict_map: Optional[Dict],
        final_decision: Optional[Dict],
    ) -> Dict:
        positive  = []
        negative  = []
        missing   = []

        # ── CV Engine signals ─────────────────────────────────────────────
        if cv_result:
            verdict   = cv_result.get("verdict","")
            confidence = cv_result.get("confidence",0)
            n_claims  = cv_result.get("total_claims",0)
            n_with_ev = cv_result.get("claims_with_evidence",0)

            if verdict in ("Likely Authentic",):
                positive.append(f"CV Engine: {n_with_ev}/{n_claims} claims supported by external evidence (verdict: Likely Authentic, {confidence}% confidence).")
            elif verdict in ("Likely Inconsistent","Likely Fake"):
                negative.append(f"CV Engine: Document verification returned '{verdict}' at {confidence}% confidence.")
            else:
                missing.append(f"CV Engine: Inconclusive result ('{verdict}'). Insufficient public records to confirm claims.")

            # Red flags
            dashboard = cv_result.get("red_flag_dashboard",{})
            if dashboard.get("high_flags"):
                for f in dashboard["high_flags"][:2]:
                    negative.append(f"Red Flag [HIGH]: {f.get('detail','')[:120]}")
            if dashboard.get("verified"):
                positive.append(f"{len(dashboard['verified'])} CV claim(s) externally verified (evidence gallery).")

            # Proof of work
            pow_results = cv_result.get("proof_of_work",[])
            found_pow   = [p for p in pow_results if p.get("found")]
            missing_pow = [p for p in pow_results if not p.get("found") and p.get("platform","N/A") != "N/A"]
            if found_pow:
                positive.append(f"Proof-of-Work: Digital artefacts found on {', '.join(p['platform'] for p in found_pow)}.")
            if missing_pow:
                missing.append(f"Proof-of-Work: No artefacts on {', '.join(p['platform'] for p in missing_pow)} for claimed technical profile.")

            # Timeline
            timeline = cv_result.get("timeline_audit",{})
            if timeline.get("flags"):
                high_t = [f for f in timeline["flags"] if f.get("severity") == "high"]
                if high_t:
                    for f in high_t[:2]:
                        negative.append(f"Timeline: {f.get('detail','')[:120]}")

        else:
            missing.append("CV Engine: No CV text provided — document verification not performed.")

        # ── OSINT Engine signals ──────────────────────────────────────────
        if osint_result:
            status    = osint_result.get("status","")
            footprint = osint_result.get("digital_footprint",{})
            presence  = osint_result.get("real_world_presence",{})
            last_act  = osint_result.get("last_known_activity",{})
            disamb    = osint_result.get("disambiguation",{})

            if status == "LIKELY_MATCH":
                positive.append(f"OSINT Engine: Strong identity match found (F-S posterior ≥0.85).")
            elif status in ("AMBIGUOUS","INSUFFICIENT_DATA"):
                negative.append(f"OSINT Engine: Identity status '{status}' — public records insufficient or ambiguous.")

            fp_score = footprint.get("total_score",0)
            fp_tier  = footprint.get("tier","")
            if fp_score >= 60:
                positive.append(f"Digital Footprint: {fp_tier} ({fp_score}/100) — consistent public presence across platforms.")
            elif fp_score < 30:
                negative.append(f"Digital Footprint: {fp_tier} ({fp_score}/100) — unusually low for claimed experience level.")

            found_count = presence.get("found_count",0)
            if found_count >= 2:
                found_types = [s["type"] for s in presence.get("signals",[]) if s.get("found")]
                positive.append(f"Real-World Presence: {found_count} signal(s) confirmed ({', '.join(found_types)}).")
            elif found_count == 0:
                missing.append("Real-World Presence: No conference, media, or community signals found.")

            if last_act.get("found"):
                age = last_act.get("age_years",0)
                if age <= 2:
                    positive.append(f"Recent Activity: Last known mention found in {last_act.get('year','?')}.")
                else:
                    missing.append(f"Recent Activity: Last known mention was {age} years ago ({last_act.get('year','?')}).")
            else:
                missing.append("Last Known Activity: No dated mentions found — activity timeline unknown.")

            if disamb.get("resolved") and disamb.get("ambiguity_level") == "low":
                positive.append(f"Disambiguation: Identity resolved to '{disamb.get('resolved_to','')}' with high confidence.")
            elif disamb.get("ambiguity_level") == "high":
                negative.append("Disambiguation: Multiple candidates could not be resolved — identity ambiguous.")

        else:
            missing.append("OSINT Engine: No name provided — identity intelligence not performed.")

        # ── Cross-engine signals ──────────────────────────────────────────
        if conflict_map:
            alignment = conflict_map.get("overall_alignment","")
            summary   = conflict_map.get("summary",{})
            if alignment == "aligned":
                positive.append(f"Cross-Engine: CV and OSINT align on {summary.get('matches',0)} field(s) — high cross-engine consistency.")
            elif alignment == "high_conflict":
                negative.append(f"Cross-Engine: {summary.get('conflicts',0)} serious field conflict(s) between CV and OSINT. Investigate before deciding.")
            elif alignment == "partial_conflict":
                negative.append(f"Cross-Engine: Partial conflicts detected ({summary.get('conflicts',0)} conflict(s), {summary.get('partials',0)} partial match(es)).")

        # ── Final decision context ────────────────────────────────────────
        overall_recommendation = self._recommend(positive, negative, missing, final_decision)

        return {
            "why_trusted":         positive,
            "why_not_trusted":     negative,
            "what_is_missing":     missing,
            "overall_recommendation": overall_recommendation,
            "signal_count": {
                "positive": len(positive),
                "negative": len(negative),
                "missing":  len(missing),
            },
        }

    def _recommend(self, positive, negative, missing, decision) -> str:
        n_pos = len(positive)
        n_neg = len(negative)
        n_mis = len(missing)

        if decision:
            dec = decision.get("decision","")
            if dec == "Likely Authentic" and n_neg == 0:
                return "All signals align. Standard due diligence is sufficient. Human review recommended before any binding decision."
            if dec == "Likely Synthetic" or n_neg >= 3:
                return "Multiple negative signals detected. Mandatory human investigation required before any decision."
        if n_neg >= 2:
            return "Significant concerns detected. Human investigation and document verification required."
        if n_mis >= 3:
            return "Insufficient data for a confident assessment. Collect more information: CV text, name, context."
        if n_pos >= 3 and n_neg == 0:
            return "Positive signals dominate. Identity appears credible. Human review recommended before any binding decision."
        return "Mixed signals. Human review required. Focus investigation on flagged fields."
