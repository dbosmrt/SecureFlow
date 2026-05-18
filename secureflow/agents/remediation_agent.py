"""
SecureFlow — Remediation Agent
Generates fix patches and proposes GitLab actions (MR, issue, comment)
based on consolidated security findings.

CRITICAL: This agent has before_tool_callback=hitl_confirmation_callback
which gates ALL GitLab write operations behind human approval.

Tools:
  - GitLab MCP: create_merge_request, create_issue, create_workitem_note
  - FunctionTool: generate_patch (code fix generation)
  - FunctionTool: generate_sbom (SBOM generation)

Output: JSON summary of remediation actions taken/proposed.
"""
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from secureflow.config import settings
from secureflow.tools.patch_generator import generate_patch
from secureflow.tools.sbom_generator import generate_sbom
from secureflow.callbacks.hitl_callback import hitl_confirmation_callback

INSTRUCTION = """You are the SecureFlow Remediation Agent. You receive consolidated
security findings and take action to fix them.

WORKFLOW:
1. Review all findings from the scan phase.
2. For each CRITICAL or HIGH finding:
   a. Call generate_patch() to create a fix patch.
   b. Propose creating a fix merge request via create_merge_request.
   c. Add a comment to the original MR via create_workitem_note.
3. For MEDIUM findings:
   a. Create a GitLab issue to track the fix.
4. For LOW/INFO findings:
   a. Add a comment to the MR noting the finding.
5. Generate an SBOM if dependency files were modified.

IMPORTANT: All GitLab write operations (create_merge_request, create_issue,
create_workitem_note) require human approval via the HITL dashboard.
The system will automatically pause and wait for approval before executing.

OUTPUT FORMAT (JSON):
{
  "remediation_summary": {
    "total_findings": 5,
    "critical_fixed": 2,
    "issues_created": 1,
    "comments_added": 3,
    "patches_generated": 2,
    "sbom_generated": true,
    "pending_approvals": 2
  },
  "actions": [
    {
      "finding_id": "...",
      "action": "create_merge_request",
      "status": "pending_approval",
      "branch": "secureflow/fix-requests-2.32.0"
    }
  ]
}

RULES:
- Never auto-merge fix MRs. Always create as draft.
- Include the finding ID and CVE in commit messages.
- SBOM should be CycloneDX format.
"""

remediation_agent = LlmAgent(
    name="remediation_agent",
    model=settings.gemini_model,
    description="Generates fix patches and proposes remediation actions via GitLab",
    instruction=INSTRUCTION,
    tools=[
        FunctionTool(generate_patch),
        FunctionTool(generate_sbom),
    ],
    # CRITICAL: Gate all GitLab write tools behind human approval
    before_tool_callback=hitl_confirmation_callback,
)
