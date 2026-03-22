"""
Health Check Endpoints

GET /health  - Liveness probe: "Is the process alive?"
GET /ready   - Readiness probe: "Can we handle requests?" (expanded in Phase 6)
"""

from fastapi import APIRouter

router = APIRouter()

@router.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "healthy"}
