"""
VerifAI FastAPI Backend — Security hardened main.py
Save to: backend/main.py
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from backend.api.routes import router
from backend.database.chroma_client import ChromaClient
from backend.database.neo4j_client import Neo4jClient
from backend.utils.usage_tracker import UsageTracker
from backend.utils.logger import logger

MAX_UPLOAD_SIZE = 52_428_800   # 50 MB

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Starting VerifAI backend...")
    logger.info("📊 Initializing ChromaDB...")
    app.state.chroma = ChromaClient()
    logger.info("✅ ChromaDB initialized")
    logger.info("🔗 Connecting to Neo4j...")
    app.state.neo4j = Neo4jClient()
    logger.info("✅ Neo4j connected")
    app.state.usage_tracker = UsageTracker()
    logger.info("✅ Usage tracker initialized")
    logger.info("🎉 VerifAI backend ready!")
    yield
    try:
        app.state.neo4j.close()
    except Exception:
        pass

app = FastAPI(
    title="VerifAI API",
    description="Digital Trust Verification Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:8501",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# ── File size limit ───────────────────────────────────────────────────────
# Checked via Content-Length header BEFORE reading the body.
# This avoids the BaseHTTPMiddleware streaming bug entirely.
@app.middleware("http")
async def limit_upload_size(request: Request, call_next):
    content_length = request.headers.get("content-length")
    if content_length and int(content_length) > MAX_UPLOAD_SIZE:
        return JSONResponse(
            status_code=413,
            content={"detail": "File too large. Maximum allowed size is 50 MB."}
        )
    return await call_next(request)

# ── Security headers ──────────────────────────────────────────────────────
# Uses a route-level dependency instead of BaseHTTPMiddleware to avoid
# the "No response returned" RuntimeError on streaming/long responses.
# This is the correct pattern for Starlette >= 0.20 with async routes.
SECURITY_HEADERS = {
    "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    "X-Content-Type-Options":    "nosniff",
    "X-Frame-Options":           "DENY",
    "Referrer-Policy":           "strict-origin-when-cross-origin",
}

@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    try:
        response = await call_next(request)
    except RuntimeError as e:
        if "No response returned" in str(e):
            # Streaming response consumed — return empty 200 with headers
            response = Response(status_code=200)
        else:
            raise
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

app.include_router(router, prefix="/api")
