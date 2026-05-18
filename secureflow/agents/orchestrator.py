"""
SecureFlow — Orchestrator (Root Agent)
========================================
The root agent that coordinates the entire security pipeline.

Architecture:
  orchestrator (LlmAgent)
    -> secureflow_pipeline (SequentialAgent)
       -> parallel_security_scan (ParallelAgent)
          -> dependency_scanner
          -> secret_hunter
          -> pipeline_auditor
          -> threat_intel_agent
       -> remediation_agent (with HITL callback)

The orchestrator receives webhook events and delegates to the
sequential pipeline, which first runs all scanners in parallel,
then passes consolidated findings to the remediation agent.

NOTE: memory_service is NOT a valid LlmAgent param in current ADK.
      Memory is configured at the Runner level (Phase 6).
"""
from google.adk.agents import LlmAgent, ParallelAgent, SequentialAgent

from secureflow.config import settings
from secureflow.agents.dependency_scanner import dependency_scanner
from secureflow.agents.secret_hunter import secret_hunter
from secureflow.agents.pipeline_auditor import pipeline_auditor
from secureflow.agents.threat_intel_agent import threat_intel_agent
from secureflow.agents.remediation_agent import remediation_agent

# ============================================================
# Stage 1: Parallel Security Scan
# All 4 scanners run simultaneously on the same MR data
# ============================================================
parallel_scan = ParallelAgent(
    name="parallel_security_scan",
    sub_agents=[
        dependency_scanner,
        secret_hunter,
        pipeline_auditor,
        threat_intel_agent,
    ],
)

# ============================================================
# Full Pipeline: Scan -> Remediate (sequential)
# ============================================================
full_pipeline = SequentialAgent(
    name="secureflow_pipeline",
    sub_agents=[parallel_scan, remediation_agent],
)

# ============================================================
# Root Orchestrator
# ============================================================
INSTRUCTION = """You are the SecureFlow orchestrator. You receive GitLab webhook
events and coordinate a team of security agents to protect the software supply chain.

When you receive a webhook event:
1. Extract: project_id, merge_request_iid, author, branch names, and diff URL.
2. Pass this context to the secureflow_pipeline which will:
   a. Run 4 scanners in parallel (dependency, secret, pipeline, threat intel).
   b. Pass consolidated findings to the remediation agent.
3. Collect the final results.
4. Format the response as a consolidated security report.

RESPONSE FORMAT:
{
  "scan_id": "<uuid>",
  "project_id": "<id>",
  "mr_iid": <iid>,
  "timestamp": "<iso>",
  "findings_count": <n>,
  "findings": [...],
  "remediation_summary": {...}
}

RULES:
- Never take GitLab write actions yourself — delegate to remediation_agent.
- Always respond in structured JSON.
- Log every significant action for the audit trail.
"""

orchestrator = LlmAgent(
    name="orchestrator",
    model=settings.gemini_model,
    description="Root orchestrator coordinating the SecureFlow security pipeline",
    instruction=INSTRUCTION,
    sub_agents=[full_pipeline],
)
