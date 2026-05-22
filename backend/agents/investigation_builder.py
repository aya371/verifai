"""
Investigation Builder — Step-by-Step Investigation Pipeline
============================================================
Implements the 6-step investigation mode with:
  - Reasoning trace per step
  - Step-by-step logs
  - Full pipeline coordination

Steps:
  1. Claim Extraction
  2. Evidence Search
  3. Identity Resolution
  4. Profile Merging
  5. Consistency Check
  6. Final Decision

Save to: backend/agents/investigation_builder.py
"""
import time
from datetime import datetime
from typing import Dict, List, Optional
from backend.agents.cv_analyzer import CVAnalyzer
from backend.agents.identity_resolver import IdentityResolver
from backend.agents.consistency_analyzer import ConsistencyAnalyzer
from backend.agents.signal_normalizer import normalize_identity, normalize_cv_claims, normalize_consistency
from backend.utils.logger import logger


class InvestigationBuilder:
    """
    Runs the complete 6-step investigation pipeline and returns
    a structured trace of reasoning at each step.
    """

    STEP_NAMES = [
        "Claim Extraction",
        "Evidence Search",
        "Identity Resolution",
        "Profile Merging",
        "Consistency Check",
        "Final Decision",
    ]

    def __init__(self):
        self.cv_analyzer          = CVAnalyzer()
        self.identity_resolver    = IdentityResolver()
        self.consistency_analyzer = ConsistencyAnalyzer()
        logger.info("InvestigationBuilder initialized")

    def run(
        self,
        name:    str = "",
        context: str = "",
        cv_text: str = "",
    ) -> Dict:
        """
        Execute the full investigation pipeline.
        Returns step-by-step logs, reasoning trace, and final decision.
        """
        investigation_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        steps    = []
        start_ts = time.time()

        # ── STEP 1: Claim Extraction ─────────────────────────────────────
        step1 = self._step("Claim Extraction", step_num=1)
        claims_raw = []
        cv_result  = {}
        if cv_text and cv_text.strip():
            step1["input"] = {"cv_length": len(cv_text), "has_context": bool(context)}
            step1["reasoning"] = (
                "Claude NLP extracts structured factual claims from the CV text. "
                "Each claim is classified by type (employment, education, certification) "
                "and assigned a targeted web search query. "
                "This transforms unstructured text into verifiable propositions."
            )
            cv_result  = self.cv_analyzer.analyze(cv_text, context)
            claims_raw = cv_result.get("claims", [])
            step1["output"] = {
                "claims_extracted": len(claims_raw),
                "claim_types": list({c.get("type","?") for c in claims_raw}),
                "sample_claims": [c.get("claim","")[:80] for c in claims_raw[:3]],
            }
            step1["status"] = "complete"
            step1["note"]   = f"Extracted {len(claims_raw)} verifiable claims."
        else:
            step1["status"]   = "skipped"
            step1["note"]     = "No CV text provided — claim extraction skipped."
            step1["output"]   = {"claims_extracted": 0}
            step1["reasoning"]= "Step skipped: no CV input."
        step1["duration_ms"] = int((time.time() - start_ts) * 1000)
        steps.append(step1)

        # ── STEP 2: Evidence Search ──────────────────────────────────────
        step2 = self._step("Evidence Search", step_num=2)
        t2 = time.time()
        if claims_raw:
            high_ev   = sum(1 for c in claims_raw if c.get("confidence") == "high")
            medium_ev = sum(1 for c in claims_raw if c.get("confidence") == "medium")
            none_ev   = sum(1 for c in claims_raw if c.get("confidence") == "not_found")
            step2["input"]    = {"claims_to_search": len(claims_raw)}
            step2["reasoning"] = (
                f"DuckDuckGo web search executed for each claim's targeted query. "
                f"Source reliability weighted by domain (NIST FRVT hierarchy): "
                f"LinkedIn=0.90, Wikipedia=0.95, .edu=0.90, GitHub=0.75. "
                f"Bayesian posterior computed per claim using P(claim_true|evidence). "
                f"Relevance scored by token Jaccard similarity between claim and snippet. "
                f"Contradicting results (negation within 3-token window of claim keywords) "
                f"apply 0.30× posterior penalty per contradiction."
            )
            step2["output"] = {
                "high_confidence_claims":   high_ev,
                "medium_confidence_claims": medium_ev,
                "unverified_claims":        none_ev,
                "sources_found":            len(cv_result.get("sources", [])),
                "evidence_gallery_entries": sum(len(c.get("evidence_gallery",[])) for c in claims_raw),
            }
            step2["status"] = "complete"
            step2["note"]   = f"{high_ev} strong, {medium_ev} moderate, {none_ev} unverified claims."
        else:
            step2["status"]    = "skipped"
            step2["note"]      = "No claims to search."
            step2["reasoning"] = "Step skipped: no claims from Step 1."
            step2["output"]    = {}
        step2["duration_ms"] = int((time.time() - t2) * 1000)
        steps.append(step2)

        # ── STEP 3: Identity Resolution ──────────────────────────────────
        step3 = self._step("Identity Resolution", step_num=3)
        t3 = time.time()
        osint_result = {}
        candidates   = []
        if name:
            step3["input"]    = {"name": name, "context": context[:100] if context else ""}
            step3["reasoning"] = (
                "Multi-platform DuckDuckGo search across LinkedIn, Wikipedia, GitHub, Twitter, News. "
                "Hard filter: results must contain last name token. "
                "Claude extracts structured candidate profiles from snippets. "
                "Fellegi-Sunter scoring assigns probabilistic identity posterior: "
                "full_name LR=190, last_name LR=22, context LR=4, credible_source LR=3. "
                "Disambiguation uses deductive exclusion: candidates ruled out by geographic "
                "or role contradictions with provided context."
            )
            osint_result = self.identity_resolver.resolve(name, context)
            candidates   = osint_result.get("candidates", [])
            step3["output"] = {
                "status":           osint_result.get("status",""),
                "candidates_found": len(candidates),
                "top_candidate":    candidates[0].get("name","") if candidates else None,
                "top_score":        candidates[0].get("similarity_score", 0) if candidates else 0,
                "disambiguation":   osint_result.get("disambiguation", {}).get("ambiguity_level",""),
                "footprint_score":  osint_result.get("digital_footprint",{}).get("total_score", 0),
                "presence_signals": osint_result.get("real_world_presence",{}).get("found_count",0),
            }
            step3["status"] = "complete"
            step3["note"]   = osint_result.get("warning","")
        else:
            step3["status"]    = "skipped"
            step3["note"]      = "No name provided — identity resolution skipped."
            step3["reasoning"] = "Step skipped: no name input."
            step3["output"]    = {}
        step3["duration_ms"] = int((time.time() - t3) * 1000)
        steps.append(step3)

        # ── STEP 4: Profile Merging ──────────────────────────────────────
        step4 = self._step("Profile Merging", step_num=4)
        t4 = time.time()
        if candidates:
            merged_count = sum(1 for c in candidates if c.get("merged"))
            step4["input"]    = {"candidates_before_merge": len(candidates)}
            step4["reasoning"] = (
                "Fellegi-Sunter ANY-member matching groups candidates referring to the same person. "
                "Merge threshold: composite posterior ≥ 0.70 (Winkler 2006). "
                "Geographic contradiction = hard exclusion. "
                "Merged candidate inherits all source URLs, highest F-S score, "
                "and a combined extracted_info string from all group members."
            )
            step4["output"] = {
                "merged_groups": merged_count,
                "final_candidates": len(candidates),
                "platforms_merged": list({c.get("platform","") for c in candidates if c.get("merged")}),
            }
            step4["status"] = "complete"
            step4["note"]   = f"{merged_count} candidate(s) merged from multiple sources."
        else:
            step4["status"]    = "skipped"
            step4["note"]      = "No candidates to merge."
            step4["reasoning"] = "Step skipped: no OSINT candidates."
            step4["output"]    = {}
        step4["duration_ms"] = int((time.time() - t4) * 1000)
        steps.append(step4)

        # ── STEP 5: Consistency Check ────────────────────────────────────
        step5 = self._step("Consistency Check", step_num=5)
        t5 = time.time()
        consistency = {}
        if claims_raw and candidates:
            step5["input"] = {
                "claims_to_check": len(claims_raw),
                "top_candidate":   candidates[0].get("name",""),
            }
            step5["reasoning"] = (
                "Claude compares each CV claim against the top candidate's profile data. "
                "Classification rules: 'consistent' = profile explicitly supports the claim, "
                "'inconsistent' = profile clearly contradicts the claim (role/location/employer mismatch), "
                "'unknown' = profile has no data on this specific claim. "
                "Bayesian posterior computed via ENFSI (2015) LR framework: "
                "consistent LR=9 (moderate support), inconsistent LR=0.1 (strong against), "
                "unknown LR=1 (neutral). Prior P(consistent)=0.5 (Aitken & Taroni 2004)."
            )
            consistency = self.consistency_analyzer.analyze(
                claims=claims_raw,
                candidates=candidates,
                original_text=cv_text or ""
            )
            step5["output"] = {
                "consistent_claims":   len(consistency.get("consistent",[])),
                "inconsistent_claims": len(consistency.get("inconsistent",[])),
                "unknown_claims":      len(consistency.get("unknown",[])),
                "consistency_score":   consistency.get("consistency_score","N/A"),
                "consistency_lr":      consistency.get("consistency_lr","N/A"),
            }
            step5["status"] = "complete"
            n_bad = len(consistency.get("inconsistent",[]))
            step5["note"]   = f"{n_bad} conflict(s) detected." if n_bad else "No conflicts detected."
        else:
            step5["status"]    = "skipped"
            step5["note"]      = "Consistency check requires both CV claims and OSINT candidates."
            step5["reasoning"] = "Step skipped: missing CV or OSINT data."
            step5["output"]    = {}
        step5["duration_ms"] = int((time.time() - t5) * 1000)
        steps.append(step5)

        # ── STEP 6: Final Decision ────────────────────────────────────────
        step6 = self._step("Final Decision", step_num=6)
        t6 = time.time()
        signals = {}

        cs_summary = {}
        if osint_result.get("candidates"):
            top_cand = osint_result["candidates"][0]
            cs_summary = {
                "identity_confidence": top_cand.get("similarity_score", 0.5),
                "evidence_score":      min(100, top_cand.get("source_count", 0) * 10),
                "consistency_score":   consistency.get("consistency_score"),
            }
            signals["identity"] = normalize_identity(cs_summary)

        if claims_raw:
            signals["cv_claims"] = normalize_cv_claims(claims_raw)

        if consistency:
            signals["consistency"] = normalize_consistency(consistency)

        from backend.agents.decision_fusion import fuse_signals
        final_decision = fuse_signals(signals) if len(signals) >= 2 else {
            "decision": "Insufficient Data",
            "confidence_level": "low",
            "confidence_reason": "Not enough modules contributed.",
            "explanation": "Provide both CV and name for a full assessment.",
            "warnings": [],
        }

        step6["input"] = {
            "signals_contributing": list(signals.keys()),
            "cv_verdict":           cv_result.get("verdict","") if cv_result else "",
            "osint_status":         osint_result.get("status","") if osint_result else "",
        }
        step6["reasoning"] = (
            "Weighted multi-modal evidence fusion (Kittler et al. 1998). "
            "Contributing signals: " + ", ".join(signals.keys()) + ". "
            "Base weights: identity=0.35, cv_claims=0.30, consistency=0.35. "
            "Dynamic weight normalization: only contributing modules included. "
            "Conflict detection: authentic + synthetic signals trigger confidence penalty. "
            "Strong synthetic consistency (strength>0.5) applies dominance override."
        )
        step6["output"] = {
            "final_decision":    final_decision.get("decision",""),
            "confidence_level":  final_decision.get("confidence_level",""),
            "confidence_reason": final_decision.get("confidence_reason",""),
            "warnings":          final_decision.get("warnings",[]),
        }
        step6["status"]     = "complete"
        step6["note"]       = f"Decision: {final_decision.get('decision','')} ({final_decision.get('confidence_level','')} confidence)"
        step6["duration_ms"]= int((time.time() - t6) * 1000)
        steps.append(step6)

        total_ms = int((time.time() - start_ts) * 1000)

        return {
            "investigation_id":  investigation_id,
            "total_duration_ms": total_ms,
            "steps":             steps,
            "final_decision":    final_decision,
            "cv_analysis":       cv_result,
            "osint_analysis":    osint_result,
            "consistency":       consistency,
            "summary": {
                "steps_completed": sum(1 for s in steps if s["status"] == "complete"),
                "steps_skipped":   sum(1 for s in steps if s["status"] == "skipped"),
                "cv_verdict":      cv_result.get("verdict","N/A") if cv_result else "N/A",
                "osint_status":    osint_result.get("status","N/A") if osint_result else "N/A",
                "decision":        final_decision.get("decision",""),
            },
        }

    def _step(self, name: str, step_num: int) -> Dict:
        return {
            "step_number": step_num,
            "step_name":   name,
            "status":      "pending",
            "input":       {},
            "output":      {},
            "reasoning":   "",
            "note":        "",
            "duration_ms": 0,
        }
