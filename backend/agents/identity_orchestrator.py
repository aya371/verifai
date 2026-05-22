"""
Identity Analysis Orchestrator — Two-Engine Architecture (Media-Free)
======================================================================
Coordinates ENGINE 1 (CV Verification) and ENGINE 2 (OSINT Intelligence).
No media inputs. No image/audio/video.

Save to: backend/agents/identity_orchestrator.py
"""
import re
from typing import Dict, List, Optional
from backend.agents.cv_analyzer import CVAnalyzer
from backend.agents.identity_resolver import IdentityResolver
from backend.agents.consistency_analyzer import ConsistencyAnalyzer
from backend.agents.trust_explainer import CrossEngineConflictMap, TrustExplainer
from backend.utils.logger import logger
from backend.agents.signal_normalizer import normalize_identity, normalize_cv_claims, normalize_consistency


class IdentityOrchestrator:

    def __init__(self):
        self.cv_analyzer          = CVAnalyzer()
        self.identity_resolver    = IdentityResolver()
        self.consistency_analyzer = ConsistencyAnalyzer()
        self.conflict_mapper      = CrossEngineConflictMap()
        self.trust_explainer      = TrustExplainer()
        logger.info("IdentityOrchestrator initialized (two-engine, media-free)")

    def analyze(self, name: str = "", context: str = "", cv_text: Optional[str] = None) -> Dict:
        report = {
            "cv_verdict": "", "cv_confidence": 0, "cv_evidence_summary": "",
            "cv_final_explanation": "", "cv_sources": [], "claims_analysis": [],
            "identity_status": "INSUFFICIENT_DATA", "candidates": [],
            "consistency": {}, "decision_explanation": {}, "confidence_summary": {},
            "cross_engine_conflict_map": {}, "trust_explanation": {},
            "warnings": [], "explanation": "",
        }
        cv_claims  = []
        cv_result  = {}
        osint_result = {}

        # ── ENGINE 1: CV Verification ─────────────────────────────────────
        if cv_text and cv_text.strip():
            logger.info("ENGINE 1: CV document verification")
            cv_result = self.cv_analyzer.analyze(cv_text, context=context)
            report["claims_analysis"]      = cv_result["claims"]
            report["cv_verdict"]           = cv_result.get("verdict","Unverified")
            report["cv_confidence"]        = cv_result.get("confidence",30)
            report["cv_evidence_summary"]  = cv_result.get("evidence_summary","")
            report["cv_final_explanation"] = cv_result.get("final_explanation","")
            report["cv_sources"]           = cv_result.get("sources",[])
            # Advanced features passthrough
            report["timeline_audit"]          = cv_result.get("timeline_audit",{})
            report["proof_of_work"]           = cv_result.get("proof_of_work",[])
            report["inflation_analysis"]      = cv_result.get("inflation_analysis",[])
            report["credential_verification"] = cv_result.get("credential_verification",[])
            report["red_flag_dashboard"]      = cv_result.get("red_flag_dashboard",{})
            cv_claims = cv_result["claims"]

        # ── ENGINE 2: OSINT Intelligence ─────────────────────────────────
        if name:
            logger.info(f"ENGINE 2: OSINT identity resolution for '{name}'")
            osint_result = self.identity_resolver.resolve(name, context)
            report["candidates"]          = osint_result["candidates"]
            report["identity_status"]     = osint_result["status"]
            report["digital_footprint"]   = osint_result.get("digital_footprint",{})
            report["real_world_presence"] = osint_result.get("real_world_presence",{})
            report["last_known_activity"] = osint_result.get("last_known_activity",{})
            report["confidence_breakdown"]= osint_result.get("confidence_breakdown",{})
            report["disambiguation"]      = osint_result.get("disambiguation",{})
            report["identity_risk_profile"] = osint_result.get("identity_risk_profile",{})
            if osint_result.get("warning"):
                report["warnings"].append(osint_result["warning"])

        # ── Cross-Engine: Consistency ─────────────────────────────────────
        if cv_claims and report["candidates"]:
            logger.info("Cross-engine: consistency analysis")
            consistency = self.consistency_analyzer.analyze(
                claims=cv_claims, candidates=report["candidates"], original_text=cv_text or "")
            report["consistency"] = consistency
            n_bad = len(consistency.get("inconsistent",[]))
            if n_bad:
                report["warnings"].append(f"⚠️ {n_bad} claim(s) conflict with found profile data.")

        # ── Cross-Engine: Conflict Map ────────────────────────────────────
        if cv_result or osint_result:
            logger.info("Cross-engine: conflict map")
            # Merge consistency into cv_result for the mapper
            merged_cv = dict(cv_result) if cv_result else {}
            merged_cv["consistency"] = report.get("consistency",{})
            report["cross_engine_conflict_map"] = self.conflict_mapper.compare(merged_cv, osint_result)

        # ── Decision Explanation ──────────────────────────────────────────
        report["decision_explanation"] = self._build_decision_explanation(
            name=name, context=context, cv_claims=cv_claims, cv_text=cv_text or "",
            candidates=report["candidates"], consistency=report.get("consistency",{}),
            identity_status=report["identity_status"])

        # ── Scoring ───────────────────────────────────────────────────────
        report["confidence_summary"] = self._compute_scores(report)

        # ── Trust Explanation ─────────────────────────────────────────────
        from backend.agents.decision_fusion import fuse_signals
        signals = {}
        cs = report["confidence_summary"]
        if cs.get("identity_confidence"): signals["identity"] = normalize_identity(cs)
        if cv_claims:                     signals["cv_claims"] = normalize_cv_claims(cv_claims)
        if report.get("consistency"):     signals["consistency"] = normalize_consistency(report["consistency"])
        final_decision = fuse_signals(signals) if len(signals) >= 2 else None
        report["final_decision"] = final_decision or {"decision":"Insufficient Data","confidence_level":"low","explanation":"Not enough data.","warnings":[]}

        report["trust_explanation"] = self.trust_explainer.explain(
            cv_result    = cv_result if cv_result else None,
            osint_result = osint_result if osint_result else None,
            conflict_map = report.get("cross_engine_conflict_map"),
            final_decision = report["final_decision"],
        )

        # ── Summary ───────────────────────────────────────────────────────
        report["explanation"] = self._build_explanation(report)
        return report

    def analyze_for_fusion(self, name="", context="", cv_text=None, **_ignored) -> Dict:
        """Entry point for routes.py. Media kwargs silently discarded."""
        report = self.analyze(name=name, context=context, cv_text=cv_text)
        return {"detailed_report": report, "decision": report.get("final_decision",{})}

    # ── Decision Explanation ──────────────────────────────────────────────

    def _build_decision_explanation(self, name, context, cv_claims, cv_text, candidates, consistency, identity_status):
        similarities, conflicts = [], []
        top = candidates[0] if candidates else {}
        source_info = (top.get("extracted_info","") + " " + top.get("match_explanation","") + " " + " ".join(top.get("sources",[]))).lower()
        input_text = cv_text.lower() + " " + context.lower()

        cv_locs   = self._extract_locations(input_text)
        cv_jobs   = self._extract_jobs(cv_claims)
        cv_orgs   = self._extract_orgs(cv_claims)
        cv_edu    = self._extract_education(cv_claims)
        src_locs  = self._extract_locations(source_info)
        src_jobs  = self._extract_jobs_from_text(source_info)

        src_name = top.get("name","")
        if name and src_name:
            sim = self._name_sim(name, src_name)
            if sim >= 0.80:   similarities.append({"field":"Name","detail":f"'{name}' matches '{src_name}'"})
            elif sim >= 0.50: conflicts.append({"field":"Name","input":name,"source":src_name,"detail":f"Partial match","severity":"low"})
            else:             conflicts.append({"field":"Name","input":name,"source":src_name,"detail":f"Name mismatch","severity":"high"})

        if cv_locs and src_locs:
            shared = cv_locs & src_locs
            if shared:       similarities.append({"field":"Location","detail":f"Consistent: {', '.join(shared)}"})
            elif cv_locs and src_locs: conflicts.append({"field":"Location","input":", ".join(cv_locs),"source":", ".join(src_locs),"detail":"Location mismatch","severity":"high"})

        if cv_jobs and src_jobs:
            overlap = self._kw_overlap(cv_jobs, src_jobs)
            if overlap >= 0.30: similarities.append({"field":"Role","detail":f"Role aligned: CV '{cv_jobs}' / OSINT '{src_jobs}'"})
            else:               conflicts.append({"field":"Role","input":cv_jobs,"source":src_jobs,"detail":"Role mismatch","severity":"high"})
        elif cv_jobs:
            conflicts.append({"field":"Role","input":cv_jobs,"source":"not found","detail":"Job title not confirmed in OSINT","severity":"medium"})

        for org in cv_orgs[:3]:
            if org.lower() in source_info: similarities.append({"field":"Organisation","detail":f"'{org}' confirmed"})
            else:                          conflicts.append({"field":"Organisation","input":org,"source":"not found","detail":f"'{org}' not in OSINT","severity":"medium"})

        for item in (consistency.get("inconsistent") or []):
            claim = item.get("claim","").strip()
            if claim:
                conflicts.append({"field":"CV Claim","input":claim[:120],"source":item.get("conflict","contradicted by profile")[:120],"detail":item.get("reason","")[:200],"severity":"high"})

        for item in (consistency.get("unknown") or [])[:3]:
            claim = item.get("claim","").strip()
            if claim:
                conflicts.append({"field":"Unverifiable","input":claim[:120],"source":"no public data","detail":item.get("reason","")[:200],"severity":"low"})

        if len(candidates) >= 2:
            names = [c.get("name","?") for c in candidates[:3]]
            conflicts.append({"field":"Identity Ambiguity","input":name,"source":", ".join(names),"detail":f"Multiple profiles: {', '.join(names)}","severity":"high"})
        elif candidates and top.get("source_count",1) >= 2:
            similarities.append({"field":"Source Consistency","detail":f"Confirmed across {top.get('source_count',1)} sources"})

        verdict, reason, conclusion = self._compute_verdict(identity_status, similarities, conflicts, len(candidates))
        return {"similarities":similarities,"conflicts":conflicts,"final_decision":{"verdict":verdict,"reason":reason,"conclusion":conclusion}}

    def _compute_verdict(self, identity_status, similarities, conflicts, n_candidates):
        high = [c for c in conflicts if c.get("severity")=="high"]
        med  = [c for c in conflicts if c.get("severity")=="medium"]
        n_s, n_h, n_m = len(similarities), len(high), len(med)
        if identity_status == "LIKELY_MATCH" and n_h == 0 and n_s >= 2:    verdict = "Likely Authentic"
        elif n_h >= 2 or identity_status in ("AMBIGUOUS","INSUFFICIENT_DATA"): verdict = "Likely Inconsistent"
        elif n_h == 1 or n_m >= 2:                                          verdict = "Authenticity Unverified (Leaning Positive)"
        elif n_s >= 2 and n_h == 0:                                         verdict = "Likely Authentic"
        elif n_s >= 1 and n_h == 0:                                         verdict = "Authenticity Unverified (Leaning Positive)"
        else:                                                                verdict = "Unverified"
        reason = []
        if n_s:  reason.append(f"{n_s} supporting signal(s): " + ", ".join(s["field"] for s in similarities[:3]))
        if high: reason.append(f"{n_h} high-severity conflict(s): " + ", ".join(c["field"] for c in high[:3]))
        if med:  reason.append(f"{n_m} unconfirmed claim(s): " + ", ".join(c["field"] for c in med[:3]))
        if n_candidates >= 2: reason.append(f"{n_candidates} distinct candidates — ambiguous")
        if not reason: reason.append("Insufficient data")
        conclusions = {
            "Likely Authentic": "The provided identity aligns with public sources. Human verification recommended.",
            "Authenticity Unverified (Leaning Positive)": "Some signals align but not all claims verified.",
            "Unverified": "No public records found — neutral, inconclusive result.",
            "Likely Inconsistent": "Significant conflicts detected. Mandatory human review.",
        }
        return verdict, reason, conclusions.get(verdict,"Insufficient data.")

    def _compute_scores(self, report) -> Dict:
        de         = report.get("decision_explanation",{})
        sims       = de.get("similarities",[])
        confs      = de.get("conflicts",[])
        candidates = report.get("candidates",[])
        top        = candidates[0] if candidates else {}
        consistency = report.get("consistency",{})
        n_matches  = len(sims)
        ambiguity  = 1 if len(candidates) >= 2 else 0
        n_de_conf  = len(confs)
        n_cons     = len(consistency.get("inconsistent",[]))
        resolution = max(0.05, min(0.82, 0.30 + n_matches * 0.16 - n_de_conf * 0.22))
        cons_raw   = consistency.get("consistency_score",None)
        cons_pct   = 50 if (cons_raw is None or consistency.get("not_applicable",False)) else (int(cons_raw*100) if isinstance(cons_raw,float) and cons_raw<=1.0 else int(cons_raw))
        cons_factor = max(0.08, cons_pct/100.0 - n_cons*0.18)
        if cons_factor < 0.30:     w_res, w_cons = 0.38, 0.62
        elif cons_factor < 0.60:   w_res, w_cons = 0.52, 0.48
        else:                      w_res, w_cons = 0.65, 0.35
        posterior = w_res * resolution + w_cons * cons_factor
        if ambiguity: posterior *= 0.68
        sources_count  = top.get("source_count") or len(top.get("sources",[])) or 0
        evidence_score = min(100, sources_count * 10)
        cons_int = None if (cons_raw is None or consistency.get("not_applicable",False)) else (int(cons_raw*100) if isinstance(cons_raw,float) and cons_raw<=1.0 else int(cons_raw))
        return {
            "identity_confidence": round(posterior,3),
            "evidence_score":      int(evidence_score),
            "consistency_score":   cons_int,
            "media_score":         None,
            "evidence_quality":    round(evidence_score/100,2),
            "media_anomaly_score": 0,
            "_n_matches":    n_matches,
            "_n_conflicts":  n_de_conf + n_cons,
            "_n_candidates": len(candidates),
            "_sources_count":sources_count,
            "methodology":   f"Identity confidence: quality-dependent fusion (resolution={resolution:.2f}, cons_factor={cons_factor:.2f}).",
        }

    def _build_explanation(self, report) -> str:
        status = report.get("identity_status","INSUFFICIENT_DATA")
        n_c    = len(report.get("candidates",[]))
        cs     = report["confidence_summary"]
        n_bad  = len(report.get("consistency",{}).get("inconsistent",[]))
        cv_v   = report.get("cv_verdict","")
        cv_pct = report.get("cv_confidence",0)
        cv_src = report.get("cv_sources",[])
        lines  = []
        status_desc = {"LIKELY_MATCH":"One candidate with strong name and context match found.","LOW_AMBIGUITY":"One primary candidate profile identified.","MULTIPLE_CANDIDATES":f"{n_c} distinct public profiles found.","AMBIGUOUS":f"⚠️ {n_c} candidates — identity ambiguous.","INSUFFICIENT_DATA":"⚠️ Insufficient public data."}
        lines.append(status_desc.get(status,"Status undetermined."))
        if cv_v:
            label = {"Likely Authentic":f"CV Engine: Likely Authentic ({cv_pct}%).","Authenticity Unverified (Leaning Positive)":f"CV Engine: Unverified — leaning positive ({cv_pct}%).","Unverified":f"CV Engine: Unverified ({cv_pct}%) — neutral.","Likely Inconsistent":f"⚠️ CV Engine: Likely Inconsistent ({cv_pct}%).","Likely Fake":f"⚠️ CV Engine: Likely Fake ({cv_pct}%)."}
            lines.append(label.get(cv_v,f"CV verdict: {cv_v} ({cv_pct}%)."))
        if cv_src:
            lines.append("Sources: " + "; ".join(f"{s['title'][:40]} [{s['type']}]" for s in cv_src[:4]) + ".")
        cons_score = cs.get("consistency_score",None)
        if cons_score is not None: lines.append(f"Consistency: {int(cons_score)}% of checkable claims align with found profile.")
        if n_bad: lines.append(f"⚠️ {n_bad} claim(s) conflict with found profile data — review required.")
        lines.append("This report is probabilistic. Final assessment requires human judgment.")
        return " ".join(lines)

    # ── Helpers ───────────────────────────────────────────────────────────
    GEO_MARKERS = ["london","paris","berlin","dubai","beirut","new york","los angeles","cairo","riyadh","toronto","sydney","usa","uk","lebanon","uae","france","germany","india","china","japan","brazil","australia","canada","italy","spain","mexico","turkey","egypt","jordan","singapore","amsterdam"]
    JOB_KEYWORDS = ["engineer","developer","manager","director","analyst","architect","designer","consultant","researcher","professor","doctor","scientist","ceo","cto","cfo","founder","intern","officer","specialist","coordinator","lead","head"]
    ORG_TYPES = ["university","college","institute","hospital","corp","company","llc","ltd","inc","foundation","school","lab","center","centre","research","group","agency","ministry","bank","tech","systems"]

    def _extract_locations(self, t): return {g for g in self.GEO_MARKERS if g in t}
    def _extract_jobs(self, claims):
        for c in claims:
            if c.get("type") in ("employment","other"):
                info = c.get("claim","")
                if any(kw in info.lower() for kw in self.JOB_KEYWORDS): return info[:80]
        return ""
    def _extract_jobs_from_text(self, t):
        for kw in self.JOB_KEYWORDS:
            idx = t.find(kw)
            if idx != -1: return t[max(0,idx-10):min(len(t),idx+40)].strip()[:80]
        return ""
    def _extract_orgs(self, claims):
        orgs = []
        for c in claims:
            if any(ot in c.get("claim","").lower() for ot in self.ORG_TYPES): orgs.append(c.get("claim","")[:60])
        return list(dict.fromkeys(orgs))[:4]
    def _extract_education(self, claims): return [c.get("claim","")[:60] for c in claims if c.get("type")=="education"][:3]
    def _kw_overlap(self, a, b):
        def t(s): return {w.lower() for w in re.findall(r'\b\w{3,}\b',s)}
        ta,tb = t(a),t(b)
        return len(ta&tb)/len(ta|tb) if ta and tb else 0.0
    def _name_sim(self, a, b):
        def t(s): return {x.lower() for x in re.findall(r'\b\w+\b',s) if len(x)>1}
        ta,tb = t(a),t(b)
        return len(ta&tb)/len(ta|tb) if ta and tb else 0.0
