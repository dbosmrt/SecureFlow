"""
SecureFlow -- Pub/Sub Subscriber
Background worker that pulls webhook events from Pub/Sub
and runs them through the ADK agent pipeline.

CRITICAL FIX from v1:
  - Replaced `google.ai.generativelanguage` with `google.genai.types`
  - Fixed `asyncio.run()` inside callback (Pub/Sub callbacks are sync)

Usage (production):
    python -m secureflow.pubsub.subscriber

Dependencies: google-cloud-pubsub, google-adk (only in production)
"""
import json
import asyncio
import logging
from typing import Optional

from secureflow.config import settings

logger = logging.getLogger(__name__)


# Lazy ADK Runner initialization

_runner = None
_session_service = None


def _init_runner():
    """Initialize the ADK Runner and SessionService (once, on first use)."""
    global _runner, _session_service

    if _runner is not None:
        return True

    try:
        from google.adk.runners import Runner
        from google.adk.sessions import InMemorySessionService
        from secureflow.agents import root_agent

        _session_service = InMemorySessionService()
        _runner = Runner(
            agent=root_agent,
            app_name="secureflow",
            session_service=_session_service,
        )
        logger.info("ADK Runner initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize ADK Runner: {e}")
        return False



# Event processing

async def process_webhook_event(event: dict) -> None:
    """
    Process a webhook event through the ADK agent pipeline.

    Creates a session, sends the event as a user message,
    and collects the agent's findings.
    """
    if not _init_runner():
        logger.error("Cannot process event: ADK Runner unavailable")
        return

    from google.genai import types as genai_types

    project_id = event.get("project", {}).get("id", "unknown")

    # Create a session for this event
    session = await _session_service.create_session(
        app_name="secureflow",
        user_id=f"gitlab-{project_id}",
    )

    try:
        async for response in _runner.run_async(
            user_id=session.user_id,
            session_id=session.id,
            new_message=genai_types.Content(
                role="user",
                parts=[genai_types.Part(text=json.dumps(event))],
            ),
        ):
            if response.is_final_response():
                logger.info(f"Pipeline complete for project {project_id}")
                # In production, findings would be persisted to BigQuery
                # via the remediation agent. Here we just log completion.

    except Exception as e:
        logger.error(f"Pipeline execution failed for project {project_id}: {e}")



# Pub/Sub subscriber loop

def _sync_callback(message) -> None:
    """
    Pub/Sub message callback (synchronous).

    Pub/Sub client calls this synchronously, so we use
    asyncio.run() to bridge into our async pipeline.
    """
    logger.info(f"Received Pub/Sub message: {message.message_id}")
    try:
        event = json.loads(message.data.decode("utf-8"))
        asyncio.run(process_webhook_event(event))
        message.ack()
        logger.info(f"Message {message.message_id} processed and acknowledged")
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in message {message.message_id}")
        message.nack()
    except Exception as e:
        logger.error(f"Error processing message {message.message_id}: {e}")
        message.nack()


def start_subscriber() -> None:
    """
    Start the Pub/Sub subscriber loop.

    Blocks until interrupted or an error occurs.
    Only works in production with google-cloud-pubsub installed.
    """
    try:
        from google.cloud import pubsub_v1
    except ImportError:
        logger.error("google-cloud-pubsub not installed. Cannot start subscriber.")
        return

    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(
        settings.gcp_project,
        settings.pubsub_subscription,
    )

    logger.info(f"Starting subscriber on {subscription_path}...")
    streaming_pull = subscriber.subscribe(subscription_path, callback=_sync_callback)

    with subscriber:
        try:
            streaming_pull.result()
        except KeyboardInterrupt:
            logger.info("Subscriber stopped by user")
            streaming_pull.cancel()
        except Exception as e:
            logger.error(f"Subscriber error: {e}")
            streaming_pull.cancel()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    start_subscriber()
