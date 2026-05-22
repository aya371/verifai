"""
routes.py — VerifAI API Routes (media-free, two-engine + investigation)
"""
from fastapi import Request, APIRouter, HTTPException, Depends, Form
from backend.agents.identity_orchestrator import IdentityOrchestrator
from backend.agents.investigation_builder import InvestigationBuilder
from backend.agents.trust_explainer import CrossEngineConflictMap, TrustExplainer
import time
from datetime import datetime
from backend.api.models import FactCheckRequest, FactCheckResponse, HealthResponse, UsageStats
from backend.agents.orchestrator import Orchestrator
from backend.security.input_validator import validate_input
from backend.security.rate_limiter import check_rate_limit
from backend.utils.logger import logger
from backend.utils.dependencies import get_identity_orchestrator

router = APIRouter()


def get_orchestrator(request: Request) -> Orchestrator:
    return Orchestrator(chroma_client=request.app.state.chroma, neo4j_client=request.app.state.neo4j, usage_tracker=request.app.state.usage_tracker)


# ── Fact-Check (unchanged) ────────────────────────────────────────────────

@router.post("/fact-check", response_model=FactCheckResponse)
async def fact_check(request_data: FactCheckRequest, orchestrator: Orchestrator = Depends(get_orchestrator)):
    start_time = time.time()
    try:
        check_rate_limit("demo_user")
        validate_input(request_data.text)
        result = await orchestrator.process_fact_check(text=request_data.text, extract_claims=request_data.extract_claims, language=getattr(request_data,"language","English"))
        ms = (time.time() - start_time) * 1000
        return FactCheckResponse(task_id=result['task_id'], overall_verdict=result['overall_verdict'], confidence=result['confidence'], claims_analyzed=result['claims_analyzed'], claims_refuted=result['claims_refuted'], claims_supported=result['claims_supported'], detailed_results=result['detailed_results'], processing_time_ms=ms, timestamp=datetime.now())
    except Exception as e:
        logger.error(f"Fact-check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    return HealthResponse(status="healthy", chroma="connected" if hasattr(request.app.state,'chroma') else "disconnected", neo4j="connected" if hasattr(request.app.state,'neo4j') else "optional", timestamp=datetime.now())


@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(request: Request):
    s = request.app.state.usage_tracker.get_summary()
    return UsageStats(total_requests=s['total_requests'], total_cost=s['total_cost'], remaining_credit=s['remaining_credit'], requests_today=s.get('requests_today',0))


# ── ENGINE 1 — Document Verification Engine ──────────────────────────────

@router.post("/identity-analysis/cv")
async def analyze_cv(request: Request):
    """
    ENGINE 1 — Document Verification Engine
    Accepts: cv_text (str), context (str)
    Returns: claims, evidence gallery, timeline audit, proof-of-work,
             inflation analysis, credential verification, red flag dashboard.
    """
    from backend.agents.cv_analyzer import CVAnalyzer
    data    = await request.json()
    cv_text = data.get("cv_text","")
    context = data.get("context","")
    if not cv_text or len(cv_text.strip()) < 50:
        raise HTTPException(status_code=422, detail="CV text too short (minimum 50 characters).")
    return CVAnalyzer().analyze(cv_text, context=context)


# ── ENGINE 2 — OSINT Identity Intelligence Engine ────────────────────────

@router.post("/identity-analysis/resolve")
async def resolve_identity(request: Request):
    """
    ENGINE 2 — OSINT Identity Intelligence Engine
    Accepts: name (str), context (str)
    Returns: candidates, disambiguation, digital_footprint, real_world_presence,
             last_known_activity, confidence_breakdown, identity_risk_profile.
    """
    from backend.agents.identity_resolver import IdentityResolver
    data    = await request.json()
    name    = data.get("name","").strip()
    context = data.get("context","").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Name is required.")
    return IdentityResolver().resolve(name, context)


# ── COMBINED — Both Engines ───────────────────────────────────────────────

@router.post("/identity-analysis/full")
async def identity_analysis_full(
    name:    str = Form(""),
    context: str = Form(""),
    cv_text: str = Form(""),
    orchestrator: IdentityOrchestrator = Depends(get_identity_orchestrator),
):
    """
    Full two-engine analysis. No media inputs.
    Returns: decision, evidence (full report including cross-engine conflict map and trust explanation).
    """
    result = orchestrator.analyze_for_fusion(name=name, context=context, cv_text=cv_text or None)
    return {"decision": result["decision"], "evidence": result["detailed_report"]}


# ── INVESTIGATION MODE ────────────────────────────────────────────────────

@router.post("/identity-analysis/investigate")
async def investigate(request: Request):
    """
    Full 6-step investigation pipeline with reasoning trace.
    Accepts: name (str), context (str), cv_text (str)
    Returns: step-by-step logs, reasoning trace, final decision.
    """
    data = await request.json()
    builder = InvestigationBuilder()
    return builder.run(
        name    = data.get("name",""),
        context = data.get("context",""),
        cv_text = data.get("cv_text",""),
    )


# ── CROSS-ENGINE CONFLICT MAP ─────────────────────────────────────────────

@router.post("/identity-analysis/conflict-map")
async def conflict_map(request: Request):
    """
    Compare CV Engine output vs OSINT Engine output.
    Accepts: cv_result (dict), osint_result (dict)
    Returns: field-by-field match/partial/conflict map.
    """
    data        = await request.json()
    cv_result   = data.get("cv_result",{})
    osint_result = data.get("osint_result",{})
    mapper = CrossEngineConflictMap()
    return mapper.compare(cv_result, osint_result)


# ── TRUST EXPLAINER ───────────────────────────────────────────────────────

@router.post("/identity-analysis/explain-trust")
async def explain_trust(request: Request):
    """
    Generate trust explanation from engine results.
    Returns: why_trusted, why_not_trusted, what_is_missing, recommendation.
    """
    data         = await request.json()
    explainer    = TrustExplainer()
    conflict_map = CrossEngineConflictMap().compare(data.get("cv_result",{}), data.get("osint_result",{}))
    return explainer.explain(
        cv_result    = data.get("cv_result"),
        osint_result = data.get("osint_result"),
        conflict_map = conflict_map,
        final_decision = data.get("final_decision"),
    )


# ── NEO4J GRAPH ───────────────────────────────────────────────────────────

@router.post("/identity-analysis/store-graph")
async def store_identity_graph(request: Request):
    """Store identity analysis in Neo4j knowledge graph."""
    from backend.graph.neo4j_graph_manager import Neo4jGraphManager
    data   = await request.json()
    name   = data.get("name","")
    osint  = data.get("osint_result",{})
    cv     = data.get("cv_result",{})
    graph  = Neo4jGraphManager()
    stored = graph.store_identity(name, osint, cv)
    return {"stored": stored, "graph_enabled": graph.enabled}


@router.get("/identity-analysis/graph/{name}")
async def get_identity_graph(name: str):
    """Retrieve identity graph for visualisation."""
    from backend.graph.neo4j_graph_manager import Neo4jGraphManager
    graph = Neo4jGraphManager()
    return graph.get_identity_graph(name)


@router.get("/identity-analysis/graph/{name}/conflicts")
async def get_graph_conflicts(name: str):
    """Detect cross-platform conflicts for a person in the graph."""
    from backend.graph.neo4j_graph_manager import Neo4jGraphManager
    graph = Neo4jGraphManager()
    return {"conflicts": graph.detect_conflicts(name)}
