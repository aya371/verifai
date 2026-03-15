from typing import List, Dict, Any
from backend.utils.logger import logger

class Reasoner:
    """
    Reasoner Agent
    Aggregates results from multiple claims and calculates overall verdict
    """
    
    def __init__(self):
        logger.info("🧮 Reasoner initialized")
    
    def aggregate(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate individual claim verdicts into overall verdict
        """
        if not results:
            return {
                'overall_verdict': 'NO_CLAIMS',
                'confidence': 0,
                'claims_analyzed': 0,
                'claims_refuted': 0,
                'claims_supported': 0,
                'detailed_results': []
            }
        
        # Count verdicts
        refuted = sum(1 for r in results if r['verdict'] == 'REFUTED')
        supported = sum(1 for r in results if r['verdict'] == 'SUPPORTED')
        inconclusive = sum(1 for r in results if r['verdict'] == 'INCONCLUSIVE')
        
        total = len(results)
        
        # Calculate overall verdict
        if refuted == total:
            overall_verdict = "COMPLETELY FALSE"
        elif refuted > total / 2:
            overall_verdict = "MOSTLY FALSE"
        elif supported == total:
            overall_verdict = "COMPLETELY TRUE"
        elif supported > total / 2:
            overall_verdict = "MOSTLY TRUE"
        else:
            overall_verdict = "MIXED CLAIMS"
        
        # Average confidence
        avg_confidence = sum(r['confidence'] for r in results) / total
        
        logger.info(f"🧮 Aggregated: {overall_verdict} ({avg_confidence:.1f}%)")
        
        return {
            'overall_verdict': overall_verdict,
            'confidence': avg_confidence,
            'claims_analyzed': total,
            'claims_refuted': refuted,
            'claims_supported': supported,
            'detailed_results': results
        }