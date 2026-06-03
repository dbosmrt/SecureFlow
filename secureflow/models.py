"""
SecureFlow — Data Models

Core data structures used across the entire system.
Defined per Section 7 of the master prompt specification.

These models are used by:
- Agents: to structure findings output
- BigQuery store: as row schemas
- API endpoints: as response models
- Dashboard: as data contracts
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


# 7.1 — Finding (core security finding)

@dataclass
class Finding:
    """
    A single security finding produced by one of the scanner agents.

    Fields:
        id: Unique identifier (UUID4).
        mr_iid: GitLab Merge Request internal ID.
        project_id: GitLab project ID (string for flexibility).
        scanner: Which agent produced this finding.
        severity: CRITICAL | HIGH | MEDIUM | LOW | INFO.
        title: Short human-readable title.
        description: Detailed explanation of the vulnerability.
        file_path: File where the issue was found (if applicable).
        line_number: Line number in the file (if applicable).
        cve_ids: List of associated CVE identifiers.
        cvss_score: CVSS v3.1 base score (0.0 - 10.0).
        risk_score: Composite risk score (1-10).
        remediation: Description of how to fix the issue.
        recommended_fix: Exact code or version change to apply.
        status: Current state of the finding.
        created_at: When the finding was created.
        resolved_at: When the finding was resolved (if ever).
    """

    mr_iid: int
    project_id: str
    scanner: str  # dependency | secret | pipeline | threat_intel
    severity: str  # CRITICAL | HIGH | MEDIUM | LOW | INFO
    title: str
    description: str
    remediation: str
    recommended_fix: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    cve_ids: list[str] = field(default_factory=list)
    cvss_score: Optional[float] = None
    risk_score: int = 5
    status: str = "OPEN"  # OPEN | APPROVED | FIXED | DISMISSED
    created_at: datetime = field(default_factory=datetime.utcnow)
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        """Serialize to a dict suitable for BigQuery insertion."""
        return {
            "id": self.id,
            "mr_iid": self.mr_iid,
            "project_id": self.project_id,
            "scanner": self.scanner,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "file_path": self.file_path,
            "line_number": self.line_number,
            "cve_ids": self.cve_ids,
            "cvss_score": self.cvss_score,
            "risk_score": self.risk_score,
            "remediation": self.remediation,
            "recommended_fix": self.recommended_fix,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }



# 7.2 — Audit Log Entry
@dataclass
class AuditLogEntry:
    """
    An entry in the audit trail recording every agent action.

    Fields:
        id: Unique identifier (UUID4).
        timestamp: When the action occurred.
        agent: Which agent performed the action.
        action: What was done (e.g., "scan_dependencies").
        tool_name: MCP or custom tool that was called.
        tool_input: Arguments passed to the tool (as dict).
        result: Outcome of the tool call (summary string).
        approved_by: Who approved the action (for HITL gated ops).
    """

    agent: str
    action: str
    tool_name: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    tool_input: Optional[dict] = None
    result: Optional[str] = None
    approved_by: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to a dict suitable for BigQuery insertion."""
        import json

        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "agent": self.agent,
            "action": self.action,
            "tool_name": self.tool_name,
            "tool_input": json.dumps(self.tool_input) if self.tool_input else None,
            "result": self.result,
            "approved_by": self.approved_by,
        }



# 7.3 — Approval Action (HITL queue)

@dataclass
class ApprovalAction:
    """
    A pending action in the HITL approval queue.

    Fields:
        id: Unique identifier (UUID4).
        finding_id: Related finding ID.
        action_type: Type of GitLab action (e.g., create_merge_request).
        action_payload: Full arguments for the tool call.
        status: PENDING | APPROVED | REJECTED | TIMEOUT_REJECTED.
        requested_at: When approval was requested.
        decided_at: When a decision was made.
        decided_by: Username of the approver/rejector.
    """

    finding_id: str
    action_type: str
    action_payload: dict
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "PENDING"  # PENDING | APPROVED | REJECTED | TIMEOUT_REJECTED
    requested_at: datetime = field(default_factory=datetime.utcnow)
    decided_at: Optional[datetime] = None
    decided_by: Optional[str] = None

    def to_dict(self) -> dict:
        """Serialize to a dict suitable for BigQuery insertion."""
        import json

        return {
            "id": self.id,
            "finding_id": self.finding_id,
            "action_type": self.action_type,
            "action_payload": json.dumps(self.action_payload),
            "status": self.status,
            "requested_at": self.requested_at.isoformat(),
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "decided_by": self.decided_by,
        }



# 7.4 — GitLab Webhook Payload (Pydantic for FastAPI validation)

class GitLabWebhookPayload(BaseModel):
    """
    Pydantic model for validating incoming GitLab webhook payloads.
    Used by the FastAPI webhook endpoint for automatic validation.
    """

    object_kind: str  # "merge_request", "push", "pipeline"
    project: dict  # {id, name, web_url, ...}
    object_attributes: dict  # {iid, state, source_branch, target_branch, url, ...}
    user: dict  # {name, username, ...}
    changes: Optional[dict] = None
