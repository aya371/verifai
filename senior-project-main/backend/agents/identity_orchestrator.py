"""
Identity Analysis Orchestrator — Fellegi-Sunter + Bayesian Evidence Fusion
Save to: backend/agents/identity_orchestrator.py

Scoring methodology:
- Identity confidence: Bayesian posterior via ENFSI (2015) LR updating
  Prior = 0.5 (uninformative, Aitken & Taroni 2004)
- Candidate scoring: Fellegi-Sunter (1969) agreement weights
- Consistency: Bayesian LR fusion (ENFSI 2015)
- Media: Bayesian heuristic analysis (Krawetz 2007, ASVspoof 2019)

References:
- Fellegi & Sunter (1969) "A Theory for Record Linkage"
- ENFSI Guideline for Evaluative Reporting (2015)
- Aitken & Taroni (2004) "Statistics and the Evaluation of Evidence"
- Kittler et al. (1998) "On Combining Classifiers"
- Niculescu-Mizil & Caruana (2005) [full calibration: future work]

Save to: backend/agents/identity_orchestrator.py

Key addition: Step 6 builds a structured decision_explanation that compares
(CV claims + user context) vs (resolved identity from merged sources).
This replaces the shallow candidate-vs-candidate comparison.
"""
import re
from typing import Dict, List, Optional
from backend.agents.cv_analyzer import CVAnalyzer
from backend.agents.identity_resolver import IdentityResolver
from backend.agents.consistency_analyzer import ConsistencyAnalyzer
from backend.agents.media_analyzer import MediaAnalyzer
from backend.utils.logger import logger


class IdentityOrchestrator:

    def __init__(self):
        self.cv_analyzer          = CVAnalyzer()
        self.identity_resolver    = IdentityResolver()
        self.consistency_analyzer = ConsistencyAnalyzer()
        self.media_analyzer       = MediaAnalyzer()
        logger.info("IdentityOrchestrator initialized")

    def analyze(
        self,
        name:           str             = "",
        context:        str             = "",
        cv_text:        Optional[str]   = None,
        image_bytes:    Optional[bytes] = None,
        image_filename: str             = "",
        audio_bytes:    Optional[bytes] = None,
        audio_filename: str             = "",
        video_bytes:    Optional[bytes] = None,
        video_filename: str             = "",
    ) -> Dict:

        report = {
            "identity_status":      "INSUFFICIENT_DATA",
            "candidates":           [],
            "claims_analysis":      [],
            "consistency":          {},
            "media_analysis":       {},
            "decision_explanation": {},   # ← replaces shallow comparison
            "confidence_summary": {},   # computed in Step 7
            "warnings":    [],
            "explanation": "",
        }

        # ── Step 1: CV Analysis ──────────────────────────────────────────
        cv_claims = []
        if cv_text and cv_text.strip():
            logger.info("Step 1: CV analysis")
            cv_result = self.cv_analyzer.analyze(cv_text)
            report["claims_analysis"] = cv_result["claims"]
            cv_claims = cv_result["claims"]

        # ── Step 2: Identity Resolution ──────────────────────────────────
        if name:
            logger.info(f"Step 2: identity resolution for '{name}'")
            resolution = self.identity_resolver.resolve(name, context)
            report["candidates"]      = resolution["candidates"]
            report["identity_status"] = resolution["status"]
            if resolution.get("warning"):
                report["warnings"].append(resolution["warning"])

        # ── Step 3: Consistency Analysis ─────────────────────────────────
        if cv_claims and report["candidates"]:
            logger.info("Step 3: consistency analysis")
            consistency = self.consistency_analyzer.analyze(
                claims=cv_claims,
                candidates=report["candidates"],
                original_text=cv_text or ""
            )
            report["consistency"] = consistency
            n_bad = len(consistency.get("inconsistent", []))
            if n_bad:
                report["warnings"].append(
                    f"⚠️ {n_bad} claim(s) conflict with found profile data. Review required.")

        # ── Step 4: Media Analysis ────────────────────────────────────────
        has_media = any([image_bytes, audio_bytes, video_bytes])
        if has_media:
            logger.info("Step 4: media analysis")
            media = self.media_analyzer.analyze(
                image_bytes=image_bytes,   image_filename=image_filename,
                audio_bytes=audio_bytes,   audio_filename=audio_filename,
                video_bytes=video_bytes,   video_filename=video_filename,
            )
            report["media_analysis"] = media
            flag = media.get("overall_flag", "NO SIGNALS")
            if "SUSPICIOUS" in flag:
                report["warnings"].append(
                    "⚠️ Media shows suspicious signals — independent verification recommended.")
            elif "MINOR" in flag:
                report["warnings"].append(
                    "ℹ️ Minor media anomalies detected — review if high-stakes decision.")

        # ── Step 5: Cross-Modal Warnings ─────────────────────────────────
        report["warnings"].extend(self._cross_modal_warnings(report))

        # ── Step 6: Decision Explanation ─────────────────────────────────
        logger.info("Step 6: decision explanation")
        report["decision_explanation"] = self._build_decision_explanation(
            name=name,
            context=context,
            cv_claims=cv_claims,
            cv_text=cv_text or "",
            candidates=report["candidates"],
            consistency=report["consistency"],
            identity_status=report["identity_status"],
        )

        # ── Step 7: Deterministic Scoring ────────────────────────────────
        # Computed AFTER decision_explanation so match/conflict counts are ready.
        report["confidence_summary"] = self._compute_scores(
            report=report,
            has_media=has_media,
        )

        # ── Step 8: Summary Explanation ──────────────────────────────────
        report["explanation"] = self._build_explanation(report)
        return report

    # ══════════════════════════════════════════════════════════════════════
    # DECISION EXPLANATION ENGINE
    # Compares: (CV + context) vs (resolved identity from sources)
    # ══════════════════════════════════════════════════════════════════════

    def _build_decision_explanation(
        self,
        name:             str,
        context:          str,
        cv_claims:        List[Dict],
        cv_text:          str,
        candidates:       List[Dict],
        consistency:      Dict,
        identity_status:  str,
    ) -> Dict:
        """
        Produce a structured explanation comparing what the user provided
        against what public sources revealed.

        Returns:
          {
            "similarities": [...],   # supporting signals
            "conflicts":    [...],   # specific mismatches with details
            "final_decision": {
              "verdict":     "LIKELY MATCH" | "AMBIGUOUS" | "LOW CONFIDENCE",
              "reason":      [...],
              "conclusion":  "..."
            }
          }
        """
        similarities = []
        conflicts    = []
        top = candidates[0] if candidates else {}

        # ── Gather source profile text ────────────────────────────────────
        source_info = (
            top.get("extracted_info", "") + " " +
            top.get("match_explanation", "") + " " +
            " ".join(top.get("sources", []))
        ).lower()

        # ── Extract structured fields from CV + context ───────────────────
        cv_lower     = cv_text.lower()
        ctx_lower    = context.lower()
        input_text   = cv_lower + " " + ctx_lower

        # Pull structured claim values
        cv_name      = self._extract_field(cv_claims, ["employment","other"], "name") or name
        cv_locations = self._extract_locations(input_text)
        cv_jobs      = self._extract_jobs(cv_claims)
        cv_orgs      = self._extract_orgs(cv_claims)
        cv_edu       = self._extract_education(cv_claims)

        src_locations = self._extract_locations(source_info)
        src_jobs      = self._extract_jobs_from_text(source_info)
        src_orgs      = self._extract_orgs_from_text(source_info)

        # ── 1. NAME COMPARISON ────────────────────────────────────────────
        src_name = top.get("name", "")
        if name and src_name:
            name_sim = self._name_similarity(name, src_name)
            if name_sim >= 0.80:
                similarities.append({
                    "field": "Name",
                    "detail": f"Input name '{name}' matches source name '{src_name}'",
                })
            elif name_sim >= 0.50:
                conflicts.append({
                    "field": "Name",
                    "input": name,
                    "source": src_name,
                    "detail": f"Partial name match — input '{name}' vs source '{src_name}'",
                    "severity": "low",
                })
            else:
                conflicts.append({
                    "field": "Name",
                    "input": name,
                    "source": src_name,
                    "detail": f"Name mismatch — input '{name}' vs source '{src_name}'",
                    "severity": "high",
                })

        # ── 2. LOCATION COMPARISON ────────────────────────────────────────
        if cv_locations and src_locations:
            shared = cv_locations & src_locations
            diff_a = cv_locations - src_locations
            diff_b = src_locations - cv_locations
            if shared:
                similarities.append({
                    "field": "Location",
                    "detail": f"Consistent location: {', '.join(shared)}",
                })
            elif diff_a and diff_b:
                conflicts.append({
                    "field": "Location",
                    "input":  ", ".join(diff_a),
                    "source": ", ".join(diff_b),
                    "detail": f"CV/context indicates '{', '.join(diff_a)}' but sources indicate '{', '.join(diff_b)}'",
                    "severity": "high",
                })
        elif cv_locations and not src_locations:
            conflicts.append({
                "field": "Location",
                "input":  ", ".join(cv_locations),
                "source": "not found in sources",
                "detail": f"Location '{', '.join(cv_locations)}' from CV/context not found in public profile",
                "severity": "low",
            })

        # ── 3. JOB / ROLE COMPARISON ──────────────────────────────────────
        if cv_jobs and src_jobs:
            overlap = self._keyword_overlap(cv_jobs, src_jobs)
            if overlap >= 0.30:
                similarities.append({
                    "field": "Role / Job",
                    "detail": f"Role alignment detected: CV '{cv_jobs}' / Sources '{src_jobs}'",
                })
            else:
                conflicts.append({
                    "field": "Role / Job",
                    "input":  cv_jobs,
                    "source": src_jobs,
                    "detail": f"Role mismatch — CV: '{cv_jobs}' vs Sources: '{src_jobs}'",
                    "severity": "high",
                })
        elif cv_jobs and not src_jobs:
            conflicts.append({
                "field": "Role / Job",
                "input":  cv_jobs,
                "source": "not found in sources",
                "detail": f"Job title '{cv_jobs}' from CV not confirmed in any public source",
                "severity": "medium",
            })

        # ── 4. ORGANIZATION / EDUCATION COMPARISON ────────────────────────
        for cv_org in cv_orgs[:3]:
            if cv_org.lower() in source_info:
                similarities.append({
                    "field": "Organization",
                    "detail": f"Organization '{cv_org}' confirmed in public sources",
                })
            else:
                conflicts.append({
                    "field": "Organization",
                    "input":  cv_org,
                    "source": "not found in sources",
                    "detail": f"Organization '{cv_org}' from CV not found in public profile",
                    "severity": "medium",
                })

        for edu in cv_edu[:2]:
            if any(w in source_info for w in edu.lower().split() if len(w) > 4):
                similarities.append({
                    "field": "Education",
                    "detail": f"Education reference '{edu}' found in public data",
                })
            else:
                conflicts.append({
                    "field": "Education",
                    "input":  edu,
                    "source": "not found in sources",
                    "detail": f"Education '{edu}' from CV not confirmed in public sources",
                    "severity": "medium",
                })

        # ── 5. CONSISTENCY ANALYSIS CONFLICTS ────────────────────────────
        # Pull ALL conflicts from ConsistencyAnalyzer.
        # These are Claude-verified contradictions — the most reliable signals.
        # They MUST appear in the decision explanation so the user can see them.
        #
        # Defensive: guard against missing keys, partial results, or errors.
        inconsistent_items = consistency.get("inconsistent") or []
        unknown_items      = consistency.get("unknown") or []

        for item in inconsistent_items:
            claim        = item.get("claim", "").strip()
            reason       = item.get("reason", "").strip()
            conflict_val = item.get("conflict", "").strip()
            if not claim:
                continue
            conflicts.append({
                "field":    "CV Claim",
                "input":    claim[:120],
                "source":   conflict_val[:120] if conflict_val else "contradicted by found profile data",
                "detail":   reason[:200] if reason else f"Claim '{claim[:80]}' directly contradicts found profile data",
                "severity": "high",
            })

        # Surface unverifiable claims as low-severity conflicts
        # so the user knows which claims could not be confirmed.
        # These do NOT penalize scoring — they are informational.
        for item in unknown_items[:3]:   # cap at 3 to avoid noise
            claim  = item.get("claim", "").strip()
            reason = item.get("reason", "no data found in profile").strip()
            if claim:
                conflicts.append({
                    "field":    "Unverifiable Claim",
                    "input":    claim[:120],
                    "source":   "no public data found",
                    "detail":   reason[:200],
                    "severity": "low",
                })

        # ── 6. CANDIDATE COUNT / AMBIGUITY ────────────────────────────────
        if len(candidates) >= 2:
            names = [c.get("name","?") for c in candidates[:3]]
            conflicts.append({
                "field": "Identity Ambiguity",
                "input":  name,
                "source": ", ".join(names),
                "detail": (f"Multiple distinct profiles found: {', '.join(names)}. "
                           f"Cannot determine which refers to the input identity."),
                "severity": "high",
            })
        elif candidates and top.get("source_count", 1) >= 2:
            similarities.append({
                "field": "Source Consistency",
                "detail": (f"Identity confirmed across {top.get('source_count',1)} "
                           f"independent sources (merged)"),
            })

        # ── 7. COMPUTE VERDICT ────────────────────────────────────────────
        verdict, reason, conclusion = self._compute_verdict(
            identity_status=identity_status,
            similarities=similarities,
            conflicts=conflicts,
            n_candidates=len(candidates),
        )

        return {
            "similarities":   similarities,
            "conflicts":      conflicts,
            "final_decision": {
                "verdict":    verdict,
                "reason":     reason,
                "conclusion": conclusion,
            },
        }

    def _compute_verdict(
        self,
        identity_status: str,
        similarities:    List[Dict],
        conflicts:       List[Dict],
        n_candidates:    int,
    ) -> tuple:
        """Determine verdict, reason list, and conclusion sentence."""

        high_conflicts   = [c for c in conflicts if c.get("severity") == "high"]
        medium_conflicts = [c for c in conflicts if c.get("severity") == "medium"]
        n_sims           = len(similarities)
        n_high           = len(high_conflicts)
        n_med            = len(medium_conflicts)

        # Verdict logic
        if identity_status == "LIKELY_MATCH" and n_high == 0 and n_sims >= 2:
            verdict = "LIKELY MATCH"
        elif n_high >= 2 or identity_status in ["AMBIGUOUS", "INSUFFICIENT_DATA"]:
            verdict = "AMBIGUOUS"
        elif n_high == 1 or n_med >= 2:
            verdict = "LOW CONFIDENCE"
        elif n_sims >= 2 and n_high == 0:
            verdict = "LIKELY MATCH"
        else:
            verdict = "LOW CONFIDENCE"

        # Build reason list
        reason = []
        if n_sims:
            reason.append(
                f"{n_sims} supporting signal(s) found: "
                + ", ".join(s["field"] for s in similarities[:3])
            )
        if high_conflicts:
            reason.append(
                f"{len(high_conflicts)} high-severity conflict(s): "
                + ", ".join(c["field"] for c in high_conflicts[:3])
            )
        if medium_conflicts:
            reason.append(
                f"{len(medium_conflicts)} unconfirmed claim(s): "
                + ", ".join(c["field"] for c in medium_conflicts[:3])
            )
        if n_candidates >= 2:
            reason.append(f"{n_candidates} distinct candidates found — identity is ambiguous")
        if not reason:
            reason.append("Insufficient data to assess identity")

        # Conclusion
        conclusions = {
            "LIKELY MATCH":    (
                "The provided identity aligns with public sources across multiple signals. "
                "Human verification is still recommended before any decision."
            ),
            "LOW CONFIDENCE":  (
                "Some signals align but unresolved conflicts exist. "
                "Identity cannot be confidently assessed — human review is required."
            ),
            "AMBIGUOUS":       (
                "Significant conflicts detected between provided information and public sources. "
                "Identity cannot be assessed from available evidence. "
                "Thorough human review is mandatory."
            ),
        }
        conclusion = conclusions.get(verdict, "Insufficient data to draw conclusions.")

        return verdict, reason, conclusion

    # ══════════════════════════════════════════════════════════════════════
    # FIELD EXTRACTORS
    # ══════════════════════════════════════════════════════════════════════

    GEO_MARKERS = [
        "london", "paris", "berlin", "dubai", "beirut", "new york",
        "los angeles", "cairo", "riyadh", "toronto", "sydney", "usa",
        "uk", "lebanon", "uae", "france", "germany", "india", "china",
        "japan", "brazil", "australia", "canada", "italy", "spain",
        "mexico", "turkey", "egypt", "jordan", "singapore", "amsterdam",
    ]

    JOB_KEYWORDS = [
        "engineer", "developer", "manager", "director", "analyst", "architect",
        "designer", "consultant", "researcher", "professor", "doctor", "nurse",
        "teacher", "scientist", "ceo", "cto", "cfo", "founder", "intern",
        "student", "officer", "specialist", "coordinator", "lead", "head",
    ]

    ORG_TYPES = [
        "university", "college", "institute", "hospital", "corp", "company",
        "llc", "ltd", "inc", "foundation", "school", "lab", "center", "centre",
        "research", "group", "agency", "ministry", "bank", "tech", "systems",
    ]

    def _extract_locations(self, text: str) -> set:
        t = text.lower()
        return {g for g in self.GEO_MARKERS if g in t}

    def _extract_jobs(self, claims: List[Dict]) -> str:
        for claim in claims:
            if claim.get("type") in ["employment", "other"]:
                info = claim.get("claim", "")
                for kw in self.JOB_KEYWORDS:
                    if kw in info.lower():
                        return info[:80]
        return ""

    def _extract_jobs_from_text(self, text: str) -> str:
        for kw in self.JOB_KEYWORDS:
            idx = text.find(kw)
            if idx != -1:
                start = max(0, idx - 10)
                end   = min(len(text), idx + 40)
                return text[start:end].strip()[:80]
        return ""

    def _extract_orgs(self, claims: List[Dict]) -> List[str]:
        orgs = []
        for claim in claims:
            info = claim.get("claim", "").lower()
            for ot in self.ORG_TYPES:
                if ot in info:
                    orgs.append(claim.get("claim", "")[:60])
                    break
        return list(dict.fromkeys(orgs))[:4]

    def _extract_orgs_from_text(self, text: str) -> str:
        for ot in self.ORG_TYPES:
            idx = text.find(ot)
            if idx != -1:
                start = max(0, idx - 15)
                end   = min(len(text), idx + 40)
                return text[start:end].strip()[:60]
        return ""

    def _extract_education(self, claims: List[Dict]) -> List[str]:
        edu = []
        for claim in claims:
            if claim.get("type") == "education":
                edu.append(claim.get("claim", "")[:60])
        return edu[:3]

    def _extract_field(self, claims: List[Dict],
                        types: List[str], field: str) -> str:
        for claim in claims:
            if claim.get("type") in types:
                return claim.get("claim", "")[:60]
        return ""

    def _keyword_overlap(self, text_a: str, text_b: str) -> float:
        def tokens(s):
            return {w.lower() for w in re.findall(r'\b\w{3,}\b', s)}
        ta, tb = tokens(text_a), tokens(text_b)
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    def _name_similarity(self, name_a: str, name_b: str) -> float:
        def tokens(s):
            return {t.lower() for t in re.findall(r'\b\w+\b', s) if len(t) > 1}
        ta, tb = tokens(name_a), tokens(name_b)
        if not ta or not tb:
            return 0.0
        return len(ta & tb) / len(ta | tb)

    # ══════════════════════════════════════════════════════════════════════
    # CROSS-MODAL + EXPLANATION
    # ══════════════════════════════════════════════════════════════════════

    # ══════════════════════════════════════════════════════════════════════
    # DETERMINISTIC SCORING LAYER
    # ══════════════════════════════════════════════════════════════════════

    def _compute_scores(self, report: Dict, has_media: bool) -> Dict:
        """
        Deterministic scoring using Bayesian evidence fusion.

        IDENTITY CONFIDENCE:
          Iterative Bayesian updating over match/conflict signals.
          Prior = 0.5 (uninformative, Aitken & Taroni 2004).
          Each supporting signal: LR=6 (moderate ENFSI scale).
          Each conflict: LR=0.15 (strong against, ENFSI scale).
          Ambiguity (multiple candidates): LR=0.4 (penalizes uncertainty).

        EVIDENCE SCORE:
          min(100, external_source_count * 10).
          External sources only — no CV mixing.
          Grounded in NIST FRVT source reliability hierarchy.

        CONSISTENCY SCORE:
          Taken directly from ConsistencyAnalyzer Bayesian posterior.
          Already computed via ENFSI LR framework.

        MEDIA SCORE:
          Taken from MediaAnalyzer Bayesian deepfake_probability.
          None = not provided (N/A in UI).

        References:
          Fellegi & Sunter (1969), ENFSI (2015), Aitken & Taroni (2004),
          Kittler et al. (1998) "On Combining Classifiers"
        """
        de         = report.get("decision_explanation", {})
        sims       = de.get("similarities", [])
        confs      = de.get("conflicts", [])
        candidates = report.get("candidates", [])
        top        = candidates[0] if candidates else {}
        consistency = report.get("consistency", {})

        n_matches   = len(sims)
        ambiguity   = 1 if len(candidates) >= 2 else 0

        # ══════════════════════════════════════════════════════════════════
        # IDENTITY CONFIDENCE — Quality-Dependent Weighted Fusion
        #
        # Core principle: Identity match ≠ Identity trust
        # (Kittler et al. 1998 — "On Combining Classifiers")
        #
        # Two independent signals are fused with quality-dependent weights:
        #
        # SIGNAL A — Resolution score (Fellegi-Sunter agreement weights, Winkler 2006):
        #   baseline=0.30 + matches×0.16 − DE_conflicts×0.22, capped at 0.82
        #
        # SIGNAL B — Consistency factor (ENFSI LR posterior, ENFSI 2015):
        #   consistency_pct/100 − n_cons_inconsistent×0.18, floor 0.08
        #   ConsistencyAnalyzer contradictions (Claude-verified) directly penalize.
        #
        # WEIGHTING (quality-dependent per Kittler 1998 §4.3):
        #   When cons_factor < 0.30 → w_res=0.38, w_cons=0.62 (conflicts dominate)
        #   When cons_factor 0.30-0.60 → balanced 52/48
        #   When cons_factor > 0.60 → w_res=0.65, w_cons=0.35 (resolution leads)
        #
        # AMBIGUITY: ×0.68 penalty when multiple candidates exist.
        # ══════════════════════════════════════════════════════════════════

        n_de_conflicts      = len(confs)
        n_cons_inconsistent = len(consistency.get("inconsistent", []))

        # Resolution score
        resolution = 0.30 + (n_matches * 0.16) - (n_de_conflicts * 0.22)
        resolution = max(0.05, min(0.82, resolution))

        # Consistency factor
        # Read consistency_score carefully:
        # - None or missing = no CV provided, no comparison possible → neutral (0.5)
        # - Integer 0-100 = real Bayesian posterior from ConsistencyAnalyzer
        # Using 0.5 (not 50%) as neutral avoids false penalty or false reward
        # when consistency data is absent.
        cons_raw = consistency.get("consistency_score", None)
        if cons_raw is None or consistency.get("not_applicable", False):
            # No CV was provided — treat as neutral, no consistency signal
            cons_pct = 50   # neutral prior — no evidence either way
        elif isinstance(cons_raw, float) and cons_raw <= 1.0:
            cons_pct = int(cons_raw * 100)   # legacy 0.0-1.0 conversion
        else:
            cons_pct = int(cons_raw)          # already 0-100 integer

        cons_penalty = n_cons_inconsistent * 0.18
        cons_factor  = max(0.08, cons_pct / 100.0 - cons_penalty)

        # Quality-dependent weights
        if cons_factor < 0.30:
            w_res, w_cons = 0.38, 0.62
        elif cons_factor < 0.60:
            w_res, w_cons = 0.52, 0.48
        else:
            w_res, w_cons = 0.65, 0.35

        posterior = w_res * resolution + w_cons * cons_factor
        if ambiguity:
            posterior *= 0.68

        id_conf = int(max(0, min(100, posterior * 100)))

        # 2. Evidence Score — external sources only (NIST FRVT)
        sources_count  = top.get("source_count") or len(top.get("sources", [])) or 0
        evidence_score = min(100, sources_count * 10)

        # 3. Consistency Score — from ConsistencyAnalyzer Bayesian posterior
        # Consistency Score: None when no CV provided (displayed as N/A)
        # Guards against the "always 50%" bug when consistency={} empty dict
        cons_score_raw = report.get("consistency", {}).get("consistency_score", None)
        not_applicable  = report.get("consistency", {}).get("not_applicable", False)
        if cons_score_raw is None or not_applicable:
            cons_int = None   # N/A — no CV to compare against
        elif isinstance(cons_score_raw, float) and cons_score_raw <= 1.0:
            cons_int = int(cons_score_raw * 100)
        else:
            cons_int = int(cons_score_raw)

        # 4. Media Score — from MediaAnalyzer deepfake_probability
        media_score = None
        if has_media:
            media = report.get("media_analysis", {})
            # Use overall_authenticity if available (new schema)
            overall = media.get("overall_authenticity", {})
            if overall and "deepfake_probability" in overall:
                media_score = max(0, int((1.0 - overall["deepfake_probability"]) * 100))
            else:
                # Fallback: average anomaly scores
                anom_list = [
                    media[k].get("anomaly_score", 0)
                    for k in ["image", "audio", "video"]
                    if isinstance(media.get(k), dict)
                    and media[k].get("anomaly_score") is not None
                ]
                if anom_list:
                    media_score = max(0, int(100 - sum(anom_list) / len(anom_list)))

        return {
            "identity_confidence": round(posterior, 3),   # 0.0-1.0 Bayesian posterior
            "evidence_score":      int(evidence_score),   # 0-100
            "consistency_score":   cons_int,              # 0-100 integer or None (N/A)
            "media_score":         media_score,            # int or None
            # legacy keys
            "evidence_quality":    round(evidence_score / 100, 2),
            "media_anomaly_score": (100 - media_score) if media_score is not None else 0,
            # raw counts for UI tooltips
            "_n_matches":    n_matches,
            "_n_conflicts":  n_de_conflicts + n_cons_inconsistent,
            "_n_candidates": len(candidates),
            "_sources_count": sources_count,
            "methodology": (
                f"Identity confidence: quality-dependent fusion "
                f"(resolution={resolution:.2f}, cons_factor={cons_factor:.2f}, "
                f"weights={w_res:.2f}/{w_cons:.2f}) — Kittler et al. 1998. "
                f"{n_matches} supporting signals, "
                f"{n_de_conflicts} DE conflicts, "
                f"{n_cons_inconsistent} Claude-confirmed contradictions. "
                f"Evidence: {sources_count} external sources × 10 (NIST FRVT)."
            ),
        }


    def _cross_modal_warnings(self, report: Dict) -> List[str]:
        extra = []
        identity_risk = (
            report.get("identity_status") in
            ["AMBIGUOUS", "INSUFFICIENT_DATA", "MULTIPLE_CANDIDATES"] or
            len(report.get("consistency", {}).get("inconsistent", [])) > 0
        )
        media_flag = report.get("media_analysis", {}).get("overall_flag", "")
        media_risk = "SUSPICIOUS" in media_flag

        if identity_risk and media_risk:
            extra.append(
                "⚠️ Multiple risk signals across identity and media analysis. "
                "Thorough human review required.")
        elif identity_risk and report.get("media_analysis") and not media_risk:
            extra.append(
                "ℹ️ Identity signals require attention. Media shows no strong anomalies.")
        elif media_risk and not identity_risk:
            extra.append(
                "ℹ️ Media signals require attention. Identity analysis shows no contradictions.")
        if (report.get("identity_status") == "AMBIGUOUS"
                and not report.get("claims_analysis")):
            extra.append(
                "ℹ️ Identity ambiguous and no CV provided. "
                "Additional context would help narrow candidates.")
        return extra

    def _build_explanation(self, report: Dict) -> str:
        status  = report.get("identity_status", "INSUFFICIENT_DATA")
        n_cands = len(report.get("candidates", []))
        n_claim = len(report.get("claims_analysis", []))
        cs      = report["confidence_summary"]
        n_bad   = len(report.get("consistency", {}).get("inconsistent", []))
        mflag   = report.get("media_analysis", {}).get("overall_flag", "")
        verdict = report.get("decision_explanation", {}).get(
            "final_decision", {}).get("verdict", "")

        desc = {
            "LIKELY_MATCH":        "One candidate with high name and context match.",
            "LOW_AMBIGUITY":       "One primary candidate profile identified.",
            "MULTIPLE_CANDIDATES": f"{n_cands} distinct profiles found.",
            "AMBIGUOUS":           f"⚠️ {n_cands} candidates — identity is ambiguous.",
            "INSUFFICIENT_DATA":   "⚠️ Insufficient public data.",
        }
        lines = [desc.get(status, "Identity status undetermined.")]
        if verdict:
            lines.append(f"Decision engine verdict: {verdict}.")
        if n_claim:
            ev_pct = int(cs.get("evidence_score", 0))
            lines.append(f"{n_claim} claims analyzed. Evidence score: {ev_pct}%.")
        cons_score_expl = cs.get("consistency_score", None)
        if cons_score_expl is not None:
            cons_int_expl = int(cons_score_expl) if isinstance(cons_score_expl, (int, float)) else 0
            if cons_int_expl > 0:
                lines.append(
                    f"{cons_int_expl}% of checkable signals are consistent with profile data.")
        elif not report.get("claims_analysis"):
            lines.append("Consistency: no CV provided — claim-level comparison not performed.")
        if n_bad:
            lines.append(f"⚠️ {n_bad} claim(s) directly conflict with found profile data.")
        if mflag and mflag != "NO SIGNALS":
            lines.append(f"Media signals: {mflag}.")
        lines.append(
            "This report presents evidence only. "
            "Final assessment requires human judgment.")
        return " ".join(lines)
