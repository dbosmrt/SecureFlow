"""
SecureFlow -- Pub/Sub Publisher
Publishes webhook events to Google Cloud Pub/Sub for async processing.

In production (Cloud Run), the subscriber picks up messages and runs
the ADK agent pipeline. In development, this gracefully degrades —
if Pub/Sub client isn't available, publish_event() logs and returns.

Dependencies: google-cloud-pubsub (only in production)
"""
import json
import logging
from typing import Optional

from secureflow.config import settings

logger = logging.getLogger(__name__)

_publisher = None
_topic_path: Optional[str] = None

try:
    from google.cloud import pubsub_v1

    _publisher = pubsub_v1.PublisherClient()
    _topic_path = _publisher.topic_path(settings.gcp_project, settings.pubsub_topic)
    logger.info(f"Pub/Sub publisher initialized: topic={_topic_path}")
except Exception as e:
    logger.info(f"Pub/Sub unavailable (expected in local dev): {e}")


async def publish_event(event_data: dict) -> Optional[str]:
    """
    Publish a webhook event to the Pub/Sub topic.

    Args:
        event_data: The webhook payload dict to publish.

    Returns:
        The Pub/Sub message ID if published, None if unavailable.
    """
    if not _publisher or not _topic_path:
        logger.debug("Pub/Sub not available, skipping publish")
        return None

    data = json.dumps(event_data).encode("utf-8")
    try:
        future = _publisher.publish(_topic_path, data)
        message_id = future.result(timeout=10)
        logger.info(f"Published message {message_id} to {_topic_path}")
        return message_id
    except Exception as e:
        logger.error(f"Pub/Sub publish failed: {e}")
        return None
