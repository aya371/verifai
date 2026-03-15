from neo4j import GraphDatabase
from typing import Dict, Any
from config import config
from backend.utils.logger import logger

class Neo4jClient:
    """
    Neo4j Client
    Manages knowledge graph for multi-hop reasoning
    """
    
    def __init__(self):
        try:
            self.driver = GraphDatabase.driver(
                config.NEO4J_URI,
                auth=(config.NEO4J_USER, config.NEO4J_PASSWORD)
            )
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            logger.info("✅ Neo4j connected")
        except Exception as e:
            logger.warning(f"⚠️ Neo4j connection failed: {e}")
            self.driver = None
    
    def create_schema(self):
        """Create graph schema"""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            # Create constraints
            session.run("""
                CREATE CONSTRAINT claim_text IF NOT EXISTS
                FOR (c:Claim) REQUIRE c.text IS UNIQUE
            """)
            logger.info("✅ Neo4j schema created")
    
    def store_fact_check(self, task_id: str, text: str, result: Dict[str, Any]):
        """Store fact-check results in graph"""
        if not self.driver:
            return
        
        with self.driver.session() as session:
            session.run("""
                MERGE (t:Task {id: $task_id})
                SET t.text = $text,
                    t.verdict = $verdict,
                    t.confidence = $confidence,
                    t.timestamp = datetime()
            """, 
                task_id=task_id,
                text=text[:500],  # Limit length
                verdict=result.get('overall_verdict'),
                confidence=result.get('confidence')
            )
    
    def close(self):
        """Close driver connection"""
        if self.driver:
            self.driver.close()
            logger.info("✅ Neo4j disconnected")