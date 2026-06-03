"""
SecureFlow — Findings API Endpoint
Query, filter, and retrieve security findings.
"""
import logging
from typing import Optional

from fastapi import APIRouter, Query

from secureflow.memory.bigquery_store import query_findings, get_findings_count

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/findings", tags=["Findings"])


@router.get("")
async def list_findings(
    severity: Optional[str] = Query(None, description="Filter: CRITICAL|HIGH|MEDIUM|LOW"),
    scanner: Optional[str] = Query(None, description="Filter: dependency|secret|pipeline|threat_intel"),
    status: Optional[str] = Query(None, description="Filter: OPEN|APPROVED|FIXED|DISMISSED"),
    mr_iid: Optional[int] = Query(None, description="Filter by merge request IID"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
):
    """
    Query security findings with optional filters.

    Returns a paginated list of findings with total count.
    """
    findings = await query_findings(
        severity=severity,
        scanner=scanner,
        status=status,
        mr_iid=mr_iid,
        limit=limit,
        offset=offset,
    )

    return {
        "findings": findings,
        "count": len(findings),
        "limit": limit,
        "offset": offset,
    }


@router.get("/summary")
async def findings_summary():
    """
    Get a summary of findings grouped by severity.
    Used by the dashboard for the security posture chart.
    """
    counts = await get_findings_count()
    total = sum(counts.values())

    return {
        "total": total,
        "by_severity": counts,
    }
