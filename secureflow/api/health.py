"""
SecureFlow — Health Check Endpoint
Cloud Run readiness/liveness probe.
"""
from fastapi import APIRouter

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check():
    """
    Returns service health status.
    Used by Cloud Run for readiness probes and by load balancers.
    """
    return {
        "status": "healthy",
        "service": "secureflow",
        "version": "2.0.0",
    }
