from sentence_transformers import SentenceTransformer
from typing import List
import numpy as np
from config import config
from backend.utils.logger import logger

class EmbeddingGenerator:
    """
    Generates vector embeddings using Sentence Transformers
    Runs locally - no API calls, no RAM overhead
    """
    
    def __init__(self):
        logger.info(f"🔢 Loading embedding model: {config.EMBEDDING_MODEL}")
        self.model = SentenceTransformer(config.EMBEDDING_MODEL)
        logger.info("✅ Embedding model loaded")
    
    def generate(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """Generate embeddings for list of texts"""
        logger.info(f"🔢 Generating embeddings for {len(texts)} texts...")
        
        embeddings = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            convert_to_numpy=True
        )
        
        logger.info(f"✅ Generated {len(embeddings)} embeddings")
        return embeddings
    
    def generate_single(self, text: str) -> np.ndarray:
        """Generate embedding for single text"""
        return self.model.encode(text, convert_to_numpy=True)