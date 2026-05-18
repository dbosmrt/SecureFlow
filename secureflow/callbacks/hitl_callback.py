"""
SecureFlow — HITL Confirmation Callback
ADK before_tool_callback that gates all GitLab write operations
behind human approval via the dashboard.

CRITICAL FIX from v1:
  - Parameter names MUST be exactly (tool, args, tool_context)
  - ADK passes callback arguments by keyword, so renaming
    params like 'tool_input' will cause TypeError at runtime.

How it works:
  1. Agent decides to call a GitLab write tool (e.g., create_merge_request)
  2. This callback fires BEFORE the tool executes
  3. Callback writes the action to the approval queue (BigQuery / in-memory)
  4. Callback polls the queue until a human approves or rejects
  5. If approved → return None (proceed with tool execution)
  6. If rejected → return a dict result (skip tool, return rejection message)

Used by: remediation_agent (attached as before_tool_callback=)
"""
import asyncio
import uuid
import logging
from datetime import datetime
from typing import Any, Optional

from secureflow.memory.bigquery_store import (
    write_approval_queue,
    get_approval_status,
)
from secureflow.config import settings

logger = logging.getLogger(__name__)

# GitLab MCP tools that REQUIRE human approval before execution
WRITE_TOOLS = {
    "create_merge_request",
    "create_issue",
    "create_workitem_note",
    "manage_pipeline",
}

# Read-only tools that can execute without approval
READ_TOOLS = {
    "get_issue",
    "get_merge_request",
    "get_merge_request_commits",
    "get_merge_request_diffs",
    "get_merge_request_pipelines",
    "get_pipeline_jobs",
    "search",
    "search_labels",
    "semantic_code_search",
}


async def hitl_confirmation_callback(
    tool: Any,
    args: dict,
    tool_context: Any,
) -> Optional[dict]:
    """
    ADK before_tool_callback for HITL gating on GitLab write operations.

    IMPORTANT: Parameter names (tool, args, tool_context) MUST match
    exactly — ADK passes them as keyword arguments.

    Args:
        tool: The BaseTool instance being invoked.
        args: The arguments dict being passed to the tool.
        tool_context: The ToolContext with session/state info.

    Returns:
        None: Proceed with normal tool execution (approved or read-only).
        dict: Skip tool execution and return this as the result (rejected).
    """
    tool_name = getattr(tool, "name", str(tool))

    # Read-only tools pass through without approval
    if tool_name not in WRITE_TOOLS:
        logger.debug(f"HITL: tool '{tool_name}' is read-only, proceeding")
        return None

    # --- Write tool detected: require human approval ---
    action_id = str(uuid.uuid4())
    finding_id = args.get("finding_id", "unknown")

    logger.info(
        f"HITL GATE: tool='{tool_name}' action_id={action_id[:8]} "
        f"requires human approval"
    )

    # Write to approval queue
    await write_approval_queue(
        action_id=action_id,
        finding_id=finding_id,
        action_type=tool_name,
        action_payload=args,
        status="PENDING",
        requested_at=datetime.utcnow(),
    )

    # Poll for human decision
    max_wait = settings.hitl_timeout_minutes * 60
    poll_interval = 5
    elapsed = 0

    while elapsed < max_wait:
        status = await get_approval_status(action_id)

        if status == "APPROVED":
            logger.info(f"HITL: action {action_id[:8]} APPROVED")
            return None  # Proceed with tool execution

        elif status == "REJECTED":
            logger.info(f"HITL: action {action_id[:8]} REJECTED")
            # Return a result dict to skip tool execution
            return {
                "status": "rejected",
                "message": f"Human operator rejected action: {tool_name}",
                "action_id": action_id,
            }

        await asyncio.sleep(poll_interval)
        elapsed += poll_interval

    # Timeout: auto-reject
    logger.warning(
        f"HITL: action {action_id[:8]} TIMED OUT after "
        f"{settings.hitl_timeout_minutes} minutes"
    )

    # Update status to timeout
    from secureflow.memory.bigquery_store import update_approval_status
    await update_approval_status(
        action_id=action_id,
        status="TIMEOUT_REJECTED",
        decided_by="system_timeout",
        decided_at=datetime.utcnow(),
    )

    return {
        "status": "timeout_rejected",
        "message": f"Action '{tool_name}' timed out waiting for approval "
                   f"({settings.hitl_timeout_minutes} min)",
        "action_id": action_id,
    }
