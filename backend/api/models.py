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


# ── Media Analysis Models ─────────────────────────────────────────────────

class AudioAnalysisResult(BaseModel):
    media_type: str = "audio"
    authenticity_label: str = "uncertain"
    authenticity_confidence: float = 0.5
    deepfake_probability: float = 0.5
    evidence_strength: str = "weak"
    signals: List[str] = Field(default_factory=list)
    anomaly_score: int = 0
    entropy: Optional[float] = None
    size_kb: Optional[float] = None
    format: str = "unknown"
    method: str = ""
    flag: str = "no obvious anomalies"

class VideoAnalysisResult(BaseModel):
    media_type: str = "video"
    authenticity_label: str = "uncertain"
    authenticity_confidence: float = 0.5
    deepfake_probability: float = 0.5
    evidence_strength: str = "weak"
    signals: List[str] = Field(default_factory=list)
    anomaly_score: int = 0
    entropy: Optional[float] = None
    size_mb: Optional[float] = None
    format: str = "unknown"
    method: str = ""
    flag: str = "no obvious anomalies"

class CrossVerifyResult(BaseModel):
    overall_status: str = "uncertain"
    confidence: float = 0.5
    identity_match: Optional[Dict[str, Any]] = None
    image_result: Optional[Dict[str, Any]] = None
    audio_result: Optional[Dict[str, Any]] = None
    video_result: Optional[Dict[str, Any]] = None
    cross_modal: Optional[Dict[str, Any]] = None
    signals: List[str] = Field(default_factory=list)
    note: str = ""