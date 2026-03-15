from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

class FactCheckRequest(BaseModel):
    text: str = Field(..., min_length=10, max_length=10000)
    extract_claims: bool = Field(default=True)
    language: str = Field(default="English")

class AIDetectionResult(BaseModel):
    is_ai_generated: bool = False
    confidence: float = 0
    label: str = "Unknown"
    signals: List[str] = Field(default_factory=list)
    reasoning: str = ""

class FactCheckVerdict(BaseModel):
    claim_text: str
    verdict: str
    confidence: float = Field(ge=0, le=100)
    reasoning: str
    sources: List[str] = Field(default_factory=list)
    source_dates: List[str] = Field(default_factory=list)
    language: str = Field(default="English")
    flags: List[str] = Field(default_factory=list)
    input_ai_detection: Optional[AIDetectionResult] = None
    source_ai_detection: List[AIDetectionResult] = Field(default_factory=list)

class FactCheckResponse(BaseModel):
    task_id: str
    overall_verdict: str
    confidence: float
    claims_analyzed: int
    claims_refuted: int
    claims_supported: int
    detailed_results: List[FactCheckVerdict]
    processing_time_ms: float
    timestamp: datetime

class HealthResponse(BaseModel):
    status: str
    chroma: str
    neo4j: str
    timestamp: datetime

class UsageStats(BaseModel):
    total_requests: int
    total_cost: float
    remaining_credit: float
    requests_today: int
