from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from config import config
from backend.api.routes import router
from backend.database.chroma_client import ChromaClient
from backend.database.neo4j_client import Neo4jClient
from backend.utils.logger import logger
from backend.utils.usage_tracker import UsageTracker

# Global instances
chroma_client = None
neo4j_client = None
usage_tracker = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events"""
    # Startup
    logger.info("🚀 Starting VerifAI backend...")
    
    global chroma_client, neo4j_client, usage_tracker
    
    try:
        # Initialize ChromaDB
        logger.info("📊 Initializing ChromaDB...")
        chroma_client = ChromaClient()
        app.state.chroma = chroma_client
        logger.info("✅ ChromaDB initialized")
        
        # Initialize Neo4j (optional for demo if not installed)
        try:
            logger.info("🔗 Connecting to Neo4j...")
            neo4j_client = Neo4jClient()
            neo4j_client.create_schema()
            app.state.neo4j = neo4j_client
            logger.info("✅ Neo4j connected")
        except Exception as e:
            logger.warning(f"⚠️ Neo4j not available: {e}")
            app.state.neo4j = None
        
        # Initialize usage tracker
        usage_tracker = UsageTracker()
        app.state.usage_tracker = usage_tracker
        logger.info("✅ Usage tracker initialized")
        
        logger.info("🎉 VerifAI backend ready!")
        
    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down VerifAI backend...")
    if neo4j_client:
        neo4j_client.close()
    logger.info("✅ Cleanup complete")

# Create FastAPI app
app = FastAPI(
    title="VerifAI API",
    description="Multi-Agent Platform for Digital Trust Verification",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(router, prefix="/api")

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "VerifAI API - Digital Trust Verification",
        "version": "1.0.0",
        "status": "operational",
        "demo": "fact-checking",
        "endpoints": {
            "fact_check": "/api/fact-check",
            "health": "/api/health",
            "usage": "/api/usage"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "chroma": "connected" if chroma_client else "disconnected",
        "neo4j": "connected" if neo4j_client else "not required for demo"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True
    )