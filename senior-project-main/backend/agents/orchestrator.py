import uuid
from typing import Dict, Any
from backend.agents.claim_extractor import ClaimExtractor
from backend.agents.fact_checker import FactChecker
from backend.agents.reasoner import Reasoner
from backend.utils.logger import logger

class Orchestrator:
    """
    Central Orchestrator Agent
    Routes tasks to specialized agents and coordinates execution
    """
    def __init__(self, chroma_client, neo4j_client, usage_tracker):
        self.chroma = chroma_client
        self.neo4j = neo4j_client
        self.usage_tracker = usage_tracker
        self.claim_extractor = ClaimExtractor()
        self.fact_checker = FactChecker(chroma_client, usage_tracker)
        self.reasoner = Reasoner()
        logger.info("🧠 Orchestrator initialized")

    async def process_fact_check(self, text: str, extract_claims: bool = True, language: str = "English") -> Dict[str, Any]:
        """
        Process fact-checking request
        Flow:
        1. Extract claims (if requested)
        2. Fact-check each claim
        3. Aggregate results with Reasoner
        """
        task_id = str(uuid.uuid4())[:8]
        logger.info(f"🎯 Task {task_id}: Starting fact-check pipeline")

        # Step 1: Extract claims
        if extract_claims:
            logger.info(f"📋 Extracting claims...")
            claims = await self.claim_extractor.extract(text, language=language)
            logger.info(f"✅ Extracted {len(claims)} claims")
        else:
            claims = [{
                'claim_id': 'claim_1',
                'text': text,
                'language': language,
                'entities': [],
                'claim_type': 'general'
            }]

        # Step 2: Fact-check each claim
        logger.info(f"🔍 Fact-checking {len(claims)} claims...")
        results = []
        for claim in claims:
            verdict = await self.fact_checker.verify(claim)
            results.append(verdict)
        logger.info(f"✅ All claims verified")

        # Step 3: Aggregate with Reasoner
        logger.info(f"🧮 Aggregating results...")
        final_result = self.reasoner.aggregate(results)

        # Store in Neo4j (optional)
        if self.neo4j:
            try:
                self.neo4j.store_fact_check(task_id, text, final_result)
            except Exception as e:
                logger.warning(f"⚠️ Neo4j storage failed: {e}")

        final_result['task_id'] = task_id
        logger.info(f"🎉 Task {task_id} complete: {final_result['overall_verdict']}")
        return final_result
