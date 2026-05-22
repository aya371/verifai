import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any
from config import config
from backend.utils.logger import logger

class ChromaClient:
    """
    ChromaDB Client
    Manages vector database for RAG retrieval
    """
    
    def __init__(self):
        logger.info(f"📊 Initializing ChromaDB at {config.CHROMA_PERSIST_DIR}")
        
        # Initialize ChromaDB with persistent storage
        self.client = chromadb.PersistentClient(
            path=config.CHROMA_PERSIST_DIR
        )
        
        # Get or create collection
        try:
            self.collection = self.client.get_collection(
                name=config.CHROMA_COLLECTION_NAME
            )
            count = self.collection.count()
            logger.info(f"✅ Loaded existing collection: {count} chunks")
        except:
            self.collection = self.client.create_collection(
                name=config.CHROMA_COLLECTION_NAME,
                metadata={"description": "VerifAI knowledge base"}
            )
            logger.info("✅ Created new collection")
    
    def add_documents(self, texts: List[str], metadatas: List[Dict], ids: List[str]):
        """Add documents to collection"""
        self.collection.add(
            documents=texts,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"✅ Added {len(texts)} documents")
    
    def query(self, query_texts: List[str], n_results: int = 5) -> Dict[str, Any]:
        """Query for similar documents"""
        results = self.collection.query(
            query_texts=query_texts,
            n_results=n_results
        )
        return results
    
    def count(self) -> int:
        """Get total document count"""
        return self.collection.count()