"""
SecureFlow — Projects API Endpoint
=====================================
Connect, list, and disconnect GitLab repositories.

Endpoints:
  POST   /api/projects/connect     — Connect a new repository
  GET    /api/projects             — List all connected projects
  DELETE /api/projects/{project_id} — Disconnect a repository
"""
import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException

from secureflow.models import (
    ConnectedProject,
    ConnectRepositoryRequest,
    ConnectRepositoryResponse,
)
from secureflow.services.gitlab_service import (
    validate_token,
    resolve_project,
    create_webhook,
    delete_webhook,
)
from secureflow.memory.bigquery_store import (
    write_connected_project,
    query_connected_projects,
    get_connected_project,
    delete_connected_project,
)
from secureflow.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/connect", response_model=ConnectRepositoryResponse)
async def connect_repository(req: ConnectRepositoryRequest):
    """
    Connect a GitLab repository to SecureFlow.

    Flow:
      1. Validate the GitLab PAT
      2. Resolve the project from the repository URL
      3. Check if already connected
      4. Register the SecureFlow webhook
      5. Store the connected project
      6. Return success/failure

    Request Body:
        gitlab_token: GitLab Personal Access Token
        repository_url: Full GitLab repository URL
    """
    # --- Step 1: Validate token ---
    try:
        user_info = await validate_token(req.gitlab_token)
    except ValueError as e:
        return ConnectRepositoryResponse(
            success=False,
            webhook_created=False,
            message=str(e),
        )
    except Exception as e:
        logger.error(f"Token validation failed: {e}")
        return ConnectRepositoryResponse(
            success=False,
            webhook_created=False,
            message="Failed to validate GitLab token. Please check your network and try again.",
        )

    # --- Step 2: Resolve project ---
    try:
        project = await resolve_project(req.gitlab_token, req.repository_url)
    except ValueError as e:
        return ConnectRepositoryResponse(
            success=False,
            webhook_created=False,
            message=str(e),
        )
    except Exception as e:
        logger.error(f"Project resolution failed: {e}")
        return ConnectRepositoryResponse(
            success=False,
            webhook_created=False,
            message="Failed to resolve GitLab project. Please check the URL and try again.",
        )

    project_id = str(project["id"])
    project_name = project.get("name", "unknown")
    namespace = project.get("path_with_namespace", "unknown")

    # --- Step 3: Check if already connected ---
    existing = await get_connected_project(project_id)
    if existing and existing.get("status") == "connected":
        return ConnectRepositoryResponse(
            success=True,
            project_id=project_id,
            project_name=project_name,
            webhook_created=True,
            message=f"Project '{project_name}' is already connected.",
        )

    # --- Step 4: Create webhook ---
    webhook_created = False
    webhook_id = None
    try:
        hook = await create_webhook(
            gitlab_token=req.gitlab_token,
            project_id=int(project_id),
        )
        webhook_created = True
        webhook_id = str(hook.get("id", ""))
    except ValueError as e:
        logger.warning(f"Webhook creation failed (non-fatal): {e}")
        # Continue — project can still be tracked even if webhook fails
    except Exception as e:
        logger.warning(f"Webhook creation failed (non-fatal): {e}")

    # --- Step 5: Store connected project ---
    try:
        connected = ConnectedProject(
            project_id=project_id,
            project_name=project_name,
            namespace=namespace,
            repository_url=req.repository_url.strip(),
            webhook_id=webhook_id,
            connected_at=datetime.utcnow(),
            status="connected" if webhook_created else "error",
        )
        await write_connected_project(connected.to_dict())
    except Exception as e:
        logger.error(f"Failed to store connected project: {e}")
        return ConnectRepositoryResponse(
            success=False,
            webhook_created=webhook_created,
            message="Project resolved but failed to save. Please try again.",
        )

    # --- Step 6: Return success ---
    logger.info(
        f"Repository connected: {namespace} "
        f"(project_id={project_id}, webhook={'yes' if webhook_created else 'no'})"
    )

    return ConnectRepositoryResponse(
        success=True,
        project_id=project_id,
        project_name=project_name,
        webhook_created=webhook_created,
        message=f"Successfully connected '{project_name}'!"
        + (" Webhook registered." if webhook_created else " Webhook creation failed — manual setup may be needed."),
    )


@router.get("")
async def list_projects():
    """
    List all connected GitLab repositories.
    The dashboard polls this endpoint to show connected projects.
    """
    projects = await query_connected_projects()
    return {
        "projects": projects,
        "count": len(projects),
    }


@router.delete("/{project_id}")
async def disconnect_project(project_id: str):
    """
    Disconnect a GitLab repository from SecureFlow.
    Removes the project from the store. Webhook deletion
    is best-effort (requires the original PAT).
    """
    existing = await get_connected_project(project_id)
    if not existing:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    deleted = await delete_connected_project(project_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to disconnect project")

    logger.info(f"Project {project_id} disconnected")

    return {
        "success": True,
        "project_id": project_id,
        "message": f"Project '{existing.get('project_name', project_id)}' disconnected.",
    }
