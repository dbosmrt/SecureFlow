"""
SecureFlow — GitLab Service Layer
====================================
Handles all direct GitLab API interactions for the
Connect Repository feature:

  - Validate PAT (GET /user)
  - Resolve project from URL
  - Create/list/delete webhooks
  - Detect duplicate webhooks

Uses httpx for async HTTP. PATs are never logged or persisted.
"""
import logging
import re
from urllib.parse import quote_plus
from typing import Optional

import httpx

from secureflow.config import settings

logger = logging.getLogger(__name__)

GITLAB_API_BASE = "https://gitlab.com/api/v4"


# ============================================================
# Token Validation
# ============================================================
async def validate_token(gitlab_token: str) -> dict:
    """
    Validate a GitLab Personal Access Token by calling GET /user.

    Args:
        gitlab_token: The PAT to validate.

    Returns:
        User info dict (name, username, id, etc.).

    Raises:
        ValueError: If the token is invalid or expired.
        httpx.HTTPError: On network failures.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{GITLAB_API_BASE}/user",
            headers={"PRIVATE-TOKEN": gitlab_token},
        )

    if resp.status_code == 401:
        raise ValueError("Invalid or expired GitLab token")
    if resp.status_code != 200:
        raise ValueError(f"GitLab API error: {resp.status_code} {resp.text[:200]}")

    user = resp.json()
    logger.info(f"GitLab token validated for user: {user.get('username', 'unknown')}")
    return user


# ============================================================
# Project Resolution
# ============================================================
def parse_repository_url(repository_url: str) -> str:
    """
    Extract the namespace/project path from a GitLab repository URL.

    Supports:
        https://gitlab.com/user/project
        https://gitlab.com/group/subgroup/project
        https://gitlab.com/user/project.git
        https://gitlab.com/user/project/

    Returns:
        URL-encoded project path (e.g., "user%2Fproject").

    Raises:
        ValueError: If the URL is not a valid GitLab URL.
    """
    # Strip trailing slashes and .git
    url = repository_url.strip().rstrip("/")
    if url.endswith(".git"):
        url = url[:-4]

    # Extract path from URL
    match = re.match(
        r"https?://(?:www\.)?gitlab\.com/(.+)",
        url,
        re.IGNORECASE,
    )
    if not match:
        raise ValueError(
            "Invalid GitLab URL. Expected format: https://gitlab.com/namespace/project"
        )

    project_path = match.group(1).strip("/")
    if not project_path or "/" not in project_path:
        raise ValueError(
            "Invalid GitLab URL. Must include namespace and project name "
            "(e.g., https://gitlab.com/user/project)"
        )

    return project_path


async def resolve_project(gitlab_token: str, repository_url: str) -> dict:
    """
    Resolve a GitLab project from a repository URL.

    Args:
        gitlab_token: Valid GitLab PAT.
        repository_url: Full GitLab repository URL.

    Returns:
        Project metadata dict from GitLab API.

    Raises:
        ValueError: If the URL is invalid or project not found.
    """
    project_path = parse_repository_url(repository_url)
    encoded_path = quote_plus(project_path)

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{GITLAB_API_BASE}/projects/{encoded_path}",
            headers={"PRIVATE-TOKEN": gitlab_token},
        )

    if resp.status_code == 404:
        raise ValueError(
            f"Project not found: {project_path}. "
            "Check the URL and ensure your token has access to this project."
        )
    if resp.status_code != 200:
        raise ValueError(f"GitLab API error: {resp.status_code} {resp.text[:200]}")

    project = resp.json()
    logger.info(
        f"Resolved project: {project.get('name_with_namespace', 'unknown')} "
        f"(id={project.get('id')})"
    )
    return project


# ============================================================
# Webhook Management
# ============================================================
async def list_webhooks(gitlab_token: str, project_id: int) -> list[dict]:
    """
    List all webhooks for a GitLab project.

    Args:
        gitlab_token: Valid GitLab PAT.
        project_id: GitLab project ID (numeric).

    Returns:
        List of webhook dicts.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(
            f"{GITLAB_API_BASE}/projects/{project_id}/hooks",
            headers={"PRIVATE-TOKEN": gitlab_token},
        )

    if resp.status_code != 200:
        logger.warning(f"Failed to list webhooks for project {project_id}: {resp.status_code}")
        return []

    return resp.json()


async def find_existing_webhook(
    gitlab_token: str, project_id: int, webhook_url: str
) -> Optional[dict]:
    """
    Check if a SecureFlow webhook already exists on the project.

    Args:
        gitlab_token: Valid GitLab PAT.
        project_id: GitLab project ID.
        webhook_url: The webhook URL to look for.

    Returns:
        Existing webhook dict if found, None otherwise.
    """
    hooks = await list_webhooks(gitlab_token, project_id)
    for hook in hooks:
        if hook.get("url", "").rstrip("/") == webhook_url.rstrip("/"):
            logger.info(f"Found existing SecureFlow webhook (id={hook.get('id')}) on project {project_id}")
            return hook
    return None


async def create_webhook(
    gitlab_token: str,
    project_id: int,
    webhook_url: Optional[str] = None,
    webhook_secret: Optional[str] = None,
) -> dict:
    """
    Create a SecureFlow webhook on a GitLab project.
    Avoids duplicates by checking existing webhooks first.

    Args:
        gitlab_token: Valid GitLab PAT.
        project_id: GitLab project ID (numeric).
        webhook_url: Override URL (defaults to settings.secureflow_base_url + /webhook/gitlab).
        webhook_secret: Override secret (defaults to settings.gitlab_webhook_secret).

    Returns:
        Webhook dict (newly created or existing).
    """
    url = webhook_url or f"{settings.secureflow_base_url}/webhook/gitlab"
    secret = webhook_secret or settings.gitlab_webhook_secret

    # Check for existing webhook to avoid duplicates
    existing = await find_existing_webhook(gitlab_token, project_id, url)
    if existing:
        logger.info(f"Webhook already exists on project {project_id}, skipping creation")
        return existing

    payload = {
        "url": url,
        "token": secret,
        "merge_requests_events": True,
        "push_events": True,
        "pipeline_events": True,
        "enable_ssl_verification": True,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{GITLAB_API_BASE}/projects/{project_id}/hooks",
            headers={"PRIVATE-TOKEN": gitlab_token},
            json=payload,
        )

    if resp.status_code not in (200, 201):
        raise ValueError(
            f"Failed to create webhook: {resp.status_code} {resp.text[:200]}"
        )

    hook = resp.json()
    logger.info(f"Webhook created on project {project_id} (hook_id={hook.get('id')})")
    return hook


async def delete_webhook(
    gitlab_token: str, project_id: int, hook_id: int
) -> bool:
    """
    Delete a webhook from a GitLab project.

    Args:
        gitlab_token: Valid GitLab PAT.
        project_id: GitLab project ID.
        hook_id: Webhook ID to delete.

    Returns:
        True if deleted successfully.
    """
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.delete(
            f"{GITLAB_API_BASE}/projects/{project_id}/hooks/{hook_id}",
            headers={"PRIVATE-TOKEN": gitlab_token},
        )

    if resp.status_code == 204:
        logger.info(f"Webhook {hook_id} deleted from project {project_id}")
        return True

    logger.warning(f"Failed to delete webhook {hook_id}: {resp.status_code}")
    return False
