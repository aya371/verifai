from typing import List, Dict, Any
from backend.utils.logger import logger

class Retriever:
    """
    Retrieval Agent
    Queries ChromaDB for relevant evidence chunks
    """
    
    def __init__(self, chroma_client):
        self.chroma = chroma_client
        logger.info("📊 Retriever initialized")
    
    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve top-k most relevant chunks for query
        
        Returns list of:
        {
            'text': chunk text,
            'source': source URL,
            'date': publication date,
            'credibility': source credibility score,
            'similarity_score': cosine similarity
        }
        """
        logger.info(f"🔍 Retrieving top-{top_k} chunks for: {query[:50]}...")
        
        try:
            # Query ChromaDB
            results = self.chroma.query(
                query_texts=[query],
                n_results=top_k
            )
            
            if not results or not results['documents'][0]:
                logger.warning("⚠️ No results from ChromaDB")
                return []
            
            # Format results
            chunks = []
            for i, doc in enumerate(results['documents'][0]):
                metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                distance = results['distances'][0][i] if results['distances'] else 0
                
                chunks.append({
                    'text': doc,
                    'source': metadata.get('source', 'Unknown'),
                    'date': metadata.get('date', 'Unknown'),
                    'credibility': metadata.get('credibility', 0.5),
                    'similarity_score': 1 - distance  # Convert distance to similarity
                })
            
            logger.info(f"✅ Retrieved {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            logger.error(f"❌ Retrieval error: {e}")
            return []