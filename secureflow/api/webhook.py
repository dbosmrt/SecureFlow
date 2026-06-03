"""
SecureFlow — Webhook Endpoint
Receives GitLab webhook events, validates the token,
and enqueues them for processing.

In development (no Pub/Sub), events are stored directly
in the in-memory store for testing.
"""
import hmac
import hashlib
import uuid
import json
import logging
from datetime import datetime

from fastapi import APIRouter, Request, HTTPException, Header
from typing import Optional

from secureflow.config import settings
from secureflow.memory.bigquery_store import write_finding

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["Webhook"])

# In-memory event log for development (tracks received webhooks)
_received_events: list[dict] = []


def verify_gitlab_token(token: Optional[str]) -> bool:
    """
    Verify the X-Gitlab-Token header against our configured secret.

    GitLab webhooks use a simple shared-secret token in the
    X-Gitlab-Token header (not HMAC-based like GitHub).
    """
    if not settings.gitlab_webhook_secret or settings.gitlab_webhook_secret == "mock-secret":
        # Skip validation in development
        return True

    if not token:
        return False

    return hmac.compare_digest(token, settings.gitlab_webhook_secret)


@router.post("/gitlab")
async def gitlab_webhook(
    request: Request,
    x_gitlab_token: Optional[str] = Header(None),
):
    """
    Receives GitLab webhook events, validates authentication,
    and queues for agent processing.

    Supports event types: merge_request, push, pipeline.
    """
    # --- Authenticate ---
    if not verify_gitlab_token(x_gitlab_token):
        raise HTTPException(status_code=401, detail="Invalid or missing X-Gitlab-Token")

    # --- Parse payload ---
    try:
        data = await request.json()
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # --- Extract event metadata ---
    object_kind = data.get("object_kind", "unknown")
    project_name = data.get("project", {}).get("name", "unknown")
    project_id = data.get("project", {}).get("id", "unknown")
    event_id = str(uuid.uuid4())

    logger.info(
        f"Webhook received: type={object_kind} project={project_name} "
        f"project_id={project_id} event_id={event_id}"
    )

    # --- Filter: only process supported event types ---
    supported_events = {"merge_request", "push", "pipeline"}
    if object_kind not in supported_events:
        logger.info(f"Skipping unsupported event type: {object_kind}")
        return {
            "status": "skipped",
            "event_id": event_id,
            "reason": f"Event type '{object_kind}' not supported",
        }

    # --- Enqueue for processing ---
    event_record = {
        "event_id": event_id,
        "object_kind": object_kind,
        "project_id": str(project_id),
        "project_name": project_name,
        "received_at": datetime.utcnow().isoformat(),
        "payload": data,
    }

    # Try Pub/Sub first (Phase 6), fall back to local storage
    try:
        from secureflow.pubsub.publisher import publish_event
        await publish_event(data)
        logger.info(f"Event {event_id[:8]} published to Pub/Sub")
    except Exception as e:
        logger.info(f"Pub/Sub unavailable, storing locally: {e}")
        _received_events.append(event_record)

    return {
        "status": "accepted",
        "event_id": event_id,
        "object_kind": object_kind,
    }


def get_received_events() -> list[dict]:
    """Return all locally-stored events (development helper)."""
    return _received_events
