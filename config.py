# config.py
"""
VerifAI Configuration
Centralized configuration management with environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Config:
    """Application configuration"""
    
    # Project paths
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR / "data"
    KNOWLEDGE_BASE_DIR = DATA_DIR / "knowledge_base"
    VECTOR_DB_DIR = DATA_DIR / "vectordb"
    CACHE_DIR = DATA_DIR / "cache"
    
    # Ensure directories exist
    DATA_DIR.mkdir(exist_ok=True)
    KNOWLEDGE_BASE_DIR.mkdir(exist_ok=True)
    VECTOR_DB_DIR.mkdir(exist_ok=True)
    CACHE_DIR.mkdir(exist_ok=True)
    
    # API Keys
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY not found in environment variables. "
            "Please create a .env file with your API key."
        )
    
    # Claude Settings
    CLAUDE_MODEL = "claude-haiku-4-5-20251001"
    CLAUDE_MAX_TOKENS = int(os.getenv("CLAUDE_MAX_TOKENS", "1000"))
    CLAUDE_TEMPERATURE = float(os.getenv("CLAUDE_TEMPERATURE", "0.1"))
    
    # Neo4j Settings
    NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    
    # ChromaDB Settings
    CHROMA_PERSIST_DIR = str(VECTOR_DB_DIR)
    CHROMA_COLLECTION_NAME = os.getenv("CHROMA_COLLECTION_NAME", "verifai_kb")
    
    # Embedding Settings
    EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    EMBEDDING_DIMENSION = 384  # for all-MiniLM-L6-v2
    
    # Server Settings
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8501"))
    
    # Security Settings
    MAX_INPUT_LENGTH = int(os.getenv("MAX_INPUT_LENGTH", "10000"))
    RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
    RATE_LIMIT_WINDOW_MINUTES = int(os.getenv("RATE_LIMIT_WINDOW_MINUTES", "1"))
    
    # RAG Settings
    RAG_TOP_K = int(os.getenv("RAG_TOP_K", "5"))
    RAG_RERANK_TOP_K = int(os.getenv("RAG_RERANK_TOP_K", "3"))
    RAG_MIN_SIMILARITY = float(os.getenv("RAG_MIN_SIMILARITY", "0.5"))
    
    # Agent Settings
    ENABLE_RERANKING = os.getenv("ENABLE_RERANKING", "False").lower() == "true"
    ENABLE_AUDIT_LOG = os.getenv("ENABLE_AUDIT_LOG", "True").lower() == "true"
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = str(BASE_DIR / "verifai.log")
    
    # Demo Settings
    DEMO_MODE = os.getenv("DEMO_MODE", "False").lower() == "true"
    CACHE_RESPONSES = os.getenv("CACHE_RESPONSES", "True").lower() == "true"

# Singleton instance
config = Config()