"""
SecureFlow — Approvals API Endpoint (HITL Queue)
Manage the Human-in-the-Loop approval queue.
Allows operators to approve or reject agent-proposed actions
before they execute on GitLab.
"""
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from secureflow.memory.bigquery_store import (
    get_pending_approvals,
    update_approval_status,
    get_approval_status,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/approvals", tags=["Approvals"])


class ApprovalDecision(BaseModel):
    """Request body for approving or rejecting an action."""
    status: str  # "APPROVED" or "REJECTED"
    decided_by: str  # username of the approver


@router.get("")
async def list_pending_approvals():
    """
    Get all pending HITL approval actions.
    The dashboard polls this endpoint to show pending items.
    """
    pending = await get_pending_approvals()
    return {
        "pending": pending,
        "count": len(pending),
    }


@router.get("/{action_id}")
async def get_approval(action_id: str):
    """Get the status of a specific approval action."""
    status = await get_approval_status(action_id)
    if status == "UNKNOWN":
        raise HTTPException(status_code=404, detail=f"Approval action {action_id} not found")
    return {
        "action_id": action_id,
        "status": status,
    }


@router.post("/{action_id}")
async def decide_approval(action_id: str, decision: ApprovalDecision):
    """
    Approve or reject a pending action.

    Body:
        status: "APPROVED" or "REJECTED"
        decided_by: username of the person making the decision
    """
    # Validate status
    if decision.status not in ("APPROVED", "REJECTED"):
        raise HTTPException(
            status_code=400,
            detail="status must be 'APPROVED' or 'REJECTED'",
        )

    # Check the action exists and is still pending
    current = await get_approval_status(action_id)
    if current == "UNKNOWN":
        raise HTTPException(status_code=404, detail=f"Approval action {action_id} not found")
    if current != "PENDING":
        raise HTTPException(
            status_code=409,
            detail=f"Action already decided: {current}",
        )

    # Update
    success = await update_approval_status(
        action_id=action_id,
        status=decision.status,
        decided_by=decision.decided_by,
        decided_at=datetime.utcnow(),
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to update approval status")

    logger.info(
        f"Approval {action_id[:8]} -> {decision.status} by {decision.decided_by}"
    )

    return {
        "action_id": action_id,
        "status": decision.status,
        "decided_by": decision.decided_by,
    }
