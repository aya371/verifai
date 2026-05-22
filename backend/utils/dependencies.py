"""
FastAPI Dependencies
Save to: backend/utils/dependencies.py

Provides reusable FastAPI Depends() callables.
"""
from backend.agents.identity_orchestrator import IdentityOrchestrator

# Singleton — created once, reused across all requests
_identity_orchestrator = None

def get_identity_orchestrator() -> IdentityOrchestrator:
    """
    FastAPI dependency that returns a shared IdentityOrchestrator instance.
    Use with: orchestrator: IdentityOrchestrator = Depends(get_identity_orchestrator)
    """
    global _identity_orchestrator
    if _identity_orchestrator is None:
        _identity_orchestrator = IdentityOrchestrator()
    return _identity_orchestrator
