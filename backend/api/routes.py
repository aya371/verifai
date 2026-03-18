from fastapi import Request, APIRouter, HTTPException, Request, Depends
import time
from datetime import datetime
from backend.api.models import (
    FactCheckRequest, FactCheckResponse,
    HealthResponse, UsageStats
)
from backend.agents.orchestrator import Orchestrator
from backend.security.input_validator import validate_input
from backend.security.rate_limiter import check_rate_limit
from backend.utils.logger import logger

router = APIRouter()

def get_orchestrator(request: Request) -> Orchestrator:
    return Orchestrator(
        chroma_client=request.app.state.chroma,
        neo4j_client=request.app.state.neo4j,
        usage_tracker=request.app.state.usage_tracker
    )

@router.post("/fact-check", response_model=FactCheckResponse)
async def fact_check(
    request_data: FactCheckRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    start_time = time.time()
    try:
        user_id = "demo_user"
        check_rate_limit(user_id)
        validate_input(request_data.text)
        logger.info(f"Fact-check request: {len(request_data.text)} chars")

        result = await orchestrator.process_fact_check(
            text=request_data.text,
            extract_claims=request_data.extract_claims,
            language=getattr(request_data, "language", "English")
        )

        processing_time = (time.time() - start_time) * 1000
        response = FactCheckResponse(
            task_id=result['task_id'],
            overall_verdict=result['overall_verdict'],
            confidence=result['confidence'],
            claims_analyzed=result['claims_analyzed'],
            claims_refuted=result['claims_refuted'],
            claims_supported=result['claims_supported'],
            detailed_results=result['detailed_results'],
            processing_time_ms=processing_time,
            timestamp=datetime.now()
        )
        logger.info(f"Verdict: {result['overall_verdict']} ({processing_time:.0f}ms)")
        return response
    except Exception as e:
        logger.error(f"Fact-check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health", response_model=HealthResponse)
async def health_check(request: Request):
    return HealthResponse(
        status="healthy",
        chroma="connected" if hasattr(request.app.state, 'chroma') else "disconnected",
        neo4j="connected" if hasattr(request.app.state, 'neo4j') else "optional",
        timestamp=datetime.now()
    )

@router.get("/usage", response_model=UsageStats)
async def get_usage_stats(request: Request):
    tracker = request.app.state.usage_tracker
    summary = tracker.get_summary()
    return UsageStats(
        total_requests=summary['total_requests'],
        total_cost=summary['total_cost'],
        remaining_credit=summary['remaining_credit'],
        requests_today=summary.get('requests_today', 0)
    )


@router.post("/identity-verify")
async def identity_verify(request: Request):
    """Verify identity of a person, email, URL, or organization"""
    from backend.agents.identity_verifier import IdentityVerifier
    data = await request.json()
    verifier = IdentityVerifier()
    result = verifier.verify(data)
    return result


@router.post("/identity-verify-name")
async def identity_verify_name(request: Request):
    from backend.agents.identity_verifier import IdentityVerifier
    data = await request.json()
    name = data.get("name", "")
    verifier = IdentityVerifier()
    context = data.get("context", "")
    return verifier.verify_by_name(name, extra_context=context)

@router.post("/identity-verify-photo")
async def identity_verify_photo(request: Request):
    from backend.agents.identity_verifier import IdentityVerifier
    from fastapi import UploadFile
    form = await request.form()
    photo = form.get("photo")
    if not photo:
        return {"error": "No photo provided"}
    image_bytes = await photo.read()
    image_type  = photo.content_type or "image/jpeg"
    verifier = IdentityVerifier()
    return verifier.verify_by_photo(image_bytes, image_type)



@router.post("/identity-search-candidates")
async def identity_search_candidates(request: Request):
    from backend.agents.identity_verifier import IdentityVerifier
    data = await request.json()
    name = data.get("name", "")
    verifier = IdentityVerifier()
    candidates = verifier.search_candidates(name)
    return {"candidates": candidates}


@router.post("/identity-search-platforms")
async def identity_search_platforms(request: Request):
    from backend.agents.identity_verifier import IdentityVerifier
    data = await request.json()
    name = data.get("name", "")
    verifier = IdentityVerifier()
    profiles = verifier.search_across_platforms(name)
    return {"profiles": profiles, "name": name}
