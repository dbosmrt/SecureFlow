"""
SecureFlow — GitLab MCP Client
Factory function that creates a McpToolset connected to the
official GitLab MCP server via SSE (Server-Sent Events).

CRITICAL FIX from v1:
  - Class is McpToolset (not MCPToolset)
  - Connection params use SseConnectionParams (not SseServerParams)
  - Imported from google.adk.tools.mcp_tool.mcp_session_manager
  - NOT instantiated at module level (MCP connections are async)

Available GitLab MCP tools (as of GitLab 18.8+):
  READ:
    - get_issue, get_merge_request, get_merge_request_commits
    - get_merge_request_diffs, get_merge_request_pipelines
    - get_pipeline_jobs, search, search_labels
    - semantic_code_search (Premium/Ultimate only)

  WRITE (gated by HITL callback):
    - create_issue, create_merge_request
    - create_workitem_note, manage_pipeline

Used by: all scanner agents + remediation_agent
"""
import logging
from typing import Optional

from secureflow.config import settings

logger = logging.getLogger(__name__)

# GitLab MCP Server endpoint
GITLAB_MCP_URL = "https://gitlab.com/-/mcp"


def get_gitlab_mcp_toolset(
    tool_filter: Optional[list[str]] = None,
):
    """
    Create a McpToolset instance connected to GitLab's MCP server.

    This returns a McpToolset that can be passed directly into
    an LlmAgent's tools=[] list. The ADK framework handles the
    async connection lifecycle automatically when used with adk web
    or a Runner.

    Args:
        tool_filter: Optional list of tool names to expose.
                     If None, all GitLab MCP tools are available.
                     Example: ['get_merge_request_diffs', 'create_issue']

    Returns:
        McpToolset instance ready for agent use.

    Example:
        ```python
        from secureflow.tools.gitlab_mcp_client import get_gitlab_mcp_toolset

        agent = LlmAgent(
            name="scanner",
            model="gemini-1.5-pro",
            tools=[get_gitlab_mcp_toolset(tool_filter=["get_merge_request_diffs"])],
        )
        ```
    """
    from google.adk.tools.mcp_tool import McpToolset
    from google.adk.tools.mcp_tool.mcp_session_manager import SseConnectionParams

    token = settings.gitlab_token
    if token == "mock-token":
        logger.warning(
            "GitLab token is 'mock-token'. Set GITLAB_TOKEN env var "
            "with a real Personal Access Token (api scope) for live use."
        )

    logger.info(f"Creating GitLab McpToolset (url={GITLAB_MCP_URL})")

    toolset_kwargs = {
        "connection_params": SseConnectionParams(
            url=GITLAB_MCP_URL,
            headers={
                "Authorization": f"Bearer {token}",
            },
        ),
    }

    if tool_filter:
        toolset_kwargs["tool_filter"] = tool_filter
        logger.info(f"Tool filter: {tool_filter}")

    return McpToolset(**toolset_kwargs)



# Convenience factories for specific agent roles


def get_scanner_toolset():
    """McpToolset with only read tools — for scanner agents."""
    return get_gitlab_mcp_toolset(tool_filter=[
        "get_merge_request",
        "get_merge_request_diffs",
        "get_merge_request_commits",
        "get_merge_request_pipelines",
        "get_pipeline_jobs",
        "search",
    ])


def get_remediation_toolset():
    """McpToolset with read + write tools — for remediation agent."""
    return get_gitlab_mcp_toolset(tool_filter=[
        "get_merge_request",
        "get_merge_request_diffs",
        "create_issue",
        "create_merge_request",
        "create_workitem_note",
        "manage_pipeline",
    ])
