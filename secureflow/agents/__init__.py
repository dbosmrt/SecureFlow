"""
SecureFlow — Agents Package
Contains all ADK LlmAgent definitions:
- orchestrator: Root agent coordinating the pipeline
- dependency_scanner: Scans for vulnerable packages
- secret_hunter: Detects hardcoded credentials
- pipeline_auditor: Audits CI/CD configurations
- threat_intel_agent: Enriches findings with CVE data
- remediation_agent: Generates and applies fixes (HITL gated)

The root_agent export is used by `adk web` for interactive testing.
"""

from .orchestrator import orchestrator as root_agent

__all__ = ["root_agent"]
