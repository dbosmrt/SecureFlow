"""
SecureFlow — BigQuery / In-Memory Persistence Store
Provides async functions for storing and querying:
  - Security findings
  - Audit log entries
  - HITL approval queue

In development mode (no BigQuery client available), falls back
to thread-safe in-memory dictionaries. In production, writes
to BigQuery tables via the google-cloud-bigquery SDK.

Used by: all agents (via API endpoints), HITL callback, subscriber
"""
import json
import logging
import threading
from datetime import datetime
from typing import Any, Optional

from secureflow.config import settings

logger = logging.getLogger(__name__)

# BigQuery client initialization (graceful fallback)
_bq_client = None
_USE_BQ = False

try:
    from google.cloud import bigquery
    _bq_client = bigquery.Client(project=settings.gcp_project)
    _USE_BQ = True
    logger.info("BigQuery client initialized successfully")
except Exception as e:
    logger.info(f"BigQuery unavailable, using in-memory store: {e}")


# Thread-safe in-memory stores (development fallback)

_lock = threading.Lock()
_FINDINGS: dict[str, dict] = {}          # id -> finding dict
_AUDIT_LOG: list[dict] = []              # list of audit entries
_APPROVAL_QUEUE: dict[str, dict] = {}    # id -> approval dict

_DATASET = f"{settings.gcp_project}.{settings.bq_dataset}"



# Findings

async def write_finding(finding_dict: dict) -> None:
    """
    Persist a security finding.

    Args:
        finding_dict: Serialized Finding (from Finding.to_dict()).
    """
    if _USE_BQ and _bq_client:
        table_id = f"{_DATASET}.findings"
        errors = _bq_client.insert_rows_json(table_id, [finding_dict])
        if errors:
            logger.error(f"BigQuery write_finding failed: {errors}")
            raise RuntimeError(f"BigQuery insert error: {errors}")
        logger.info(f"Finding {finding_dict.get('id', '?')[:8]} written to BigQuery")
    else:
        with _lock:
            fid = finding_dict.get("id", str(len(_FINDINGS)))
            _FINDINGS[fid] = {
                **finding_dict,
                "created_at": finding_dict.get("created_at", datetime.utcnow().isoformat()),
            }
        logger.debug(f"Finding {fid[:8]} written to in-memory store")


async def query_findings(
    severity: Optional[str] = None,
    scanner: Optional[str] = None,
    status: Optional[str] = None,
    mr_iid: Optional[int] = None,
    limit: int = 50,
    offset: int = 0,
) -> list[dict]:
    """
    Query findings with optional filters.

    Args:
        severity: Filter by severity (CRITICAL/HIGH/MEDIUM/LOW).
        scanner: Filter by scanner agent name.
        status: Filter by status (OPEN/APPROVED/FIXED/DISMISSED).
        mr_iid: Filter by merge request IID.
        limit: Max results to return.
        offset: Pagination offset.

    Returns:
        List of finding dicts matching the filters.
    """
    if _USE_BQ and _bq_client:
        clauses = []
        params = []

        if severity:
            clauses.append("severity = @severity")
            params.append(bigquery.ScalarQueryParameter("severity", "STRING", severity))
        if scanner:
            clauses.append("scanner = @scanner")
            params.append(bigquery.ScalarQueryParameter("scanner", "STRING", scanner))
        if status:
            clauses.append("status = @status")
            params.append(bigquery.ScalarQueryParameter("status", "STRING", status))
        if mr_iid is not None:
            clauses.append("mr_iid = @mr_iid")
            params.append(bigquery.ScalarQueryParameter("mr_iid", "INTEGER", mr_iid))

        where = " AND ".join(clauses) if clauses else "TRUE"
        query = f"SELECT * FROM `{_DATASET}.findings` WHERE {where} ORDER BY created_at DESC LIMIT @limit OFFSET @offset"
        params.extend([
            bigquery.ScalarQueryParameter("limit", "INTEGER", limit),
            bigquery.ScalarQueryParameter("offset", "INTEGER", offset),
        ])

        try:
            job = _bq_client.query(query, job_config=bigquery.QueryJobConfig(query_parameters=params))
            return [dict(row) for row in job.result()]
        except Exception as e:
            logger.error(f"BigQuery query_findings failed: {e}")
            return []
    else:
        with _lock:
            results = list(_FINDINGS.values())

        # Apply filters
        if severity:
            results = [f for f in results if f.get("severity") == severity]
        if scanner:
            results = [f for f in results if f.get("scanner") == scanner]
        if status:
            results = [f for f in results if f.get("status") == status]
        if mr_iid is not None:
            results = [f for f in results if f.get("mr_iid") == mr_iid]

        # Sort by created_at descending
        results.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return results[offset:offset + limit]


async def get_findings_count() -> dict[str, int]:
    """Return count of findings grouped by severity."""
    if _USE_BQ and _bq_client:
        query = f"SELECT severity, COUNT(*) as count FROM `{_DATASET}.findings` GROUP BY severity"
        try:
            job = _bq_client.query(query)
            return {row["severity"]: row["count"] for row in job.result()}
        except Exception as e:
            logger.error(f"BigQuery get_findings_count failed: {e}")
            return {}
    else:
        with _lock:
            counts: dict[str, int] = {}
            for f in _FINDINGS.values():
                sev = f.get("severity", "UNKNOWN")
                counts[sev] = counts.get(sev, 0) + 1
            return counts



# Audit Log

async def write_audit_log(audit_dict: dict) -> None:
    """Persist an audit log entry."""
    if _USE_BQ and _bq_client:
        table_id = f"{_DATASET}.audit_log"
        errors = _bq_client.insert_rows_json(table_id, [audit_dict])
        if errors:
            logger.error(f"BigQuery write_audit_log failed: {errors}")
    else:
        with _lock:
            _AUDIT_LOG.append(audit_dict)
        logger.debug(f"Audit log entry written to in-memory store")



# Approval Queue (HITL)

async def write_approval_queue(
    action_id: str,
    finding_id: str,
    action_type: str,
    action_payload: dict,
    status: str,
    requested_at: datetime,
) -> None:
    """
    Write an action to the HITL approval queue.

    Args:
        action_id: Unique ID for this approval action.
        finding_id: Related finding ID.
        action_type: Type of GitLab action (e.g., create_merge_request).
        action_payload: Full tool call arguments.
        status: Initial status (PENDING).
        requested_at: When the action was requested.
    """
    row = {
        "id": action_id,
        "finding_id": finding_id,
        "action_type": action_type,
        "action_payload": json.dumps(action_payload) if isinstance(action_payload, dict) else action_payload,
        "status": status,
        "requested_at": requested_at.isoformat() if isinstance(requested_at, datetime) else requested_at,
        "decided_at": None,
        "decided_by": None,
    }

    if _USE_BQ and _bq_client:
        table_id = f"{_DATASET}.approval_queue"
        errors = _bq_client.insert_rows_json(table_id, [row])
        if errors:
            logger.error(f"BigQuery write_approval_queue failed: {errors}")
    else:
        with _lock:
            _APPROVAL_QUEUE[action_id] = row
        logger.debug(f"Approval {action_id[:8]} written to in-memory store")


async def get_pending_approvals() -> list[dict]:
    """Return all actions with status=PENDING."""
    if _USE_BQ and _bq_client:
        query = f"SELECT * FROM `{_DATASET}.approval_queue` WHERE status = 'PENDING' ORDER BY requested_at DESC"
        try:
            job = _bq_client.query(query)
            return [dict(row) for row in job.result()]
        except Exception as e:
            logger.error(f"BigQuery get_pending_approvals failed: {e}")
            return []
    else:
        with _lock:
            return [
                item for item in _APPROVAL_QUEUE.values()
                if item["status"] == "PENDING"
            ]


async def get_approval_status(action_id: str) -> str:
    """Get the current status of an approval action."""
    if _USE_BQ and _bq_client:
        query = f"SELECT status FROM `{_DATASET}.approval_queue` WHERE id = @action_id"
        config = bigquery.QueryJobConfig(
            query_parameters=[bigquery.ScalarQueryParameter("action_id", "STRING", action_id)]
        )
        try:
            results = list(_bq_client.query(query, job_config=config).result())
            if results:
                return results[0].status
        except Exception as e:
            logger.error(f"BigQuery get_approval_status failed: {e}")
    else:
        with _lock:
            if action_id in _APPROVAL_QUEUE:
                return _APPROVAL_QUEUE[action_id]["status"]
    return "UNKNOWN"


async def update_approval_status(
    action_id: str,
    status: str,
    decided_by: str,
    decided_at: datetime,
) -> bool:
    """
    Update the status of an approval action (APPROVED/REJECTED).

    Returns:
        True if the action was found and updated, False otherwise.
    """
    if _USE_BQ and _bq_client:
        query = f"""
            UPDATE `{_DATASET}.approval_queue`
            SET status = @status, decided_by = @decided_by, decided_at = @decided_at
            WHERE id = @action_id
        """
        config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("status", "STRING", status),
                bigquery.ScalarQueryParameter("decided_by", "STRING", decided_by),
                bigquery.ScalarQueryParameter("decided_at", "TIMESTAMP", decided_at),
                bigquery.ScalarQueryParameter("action_id", "STRING", action_id),
            ]
        )
        try:
            _bq_client.query(query, job_config=config).result()
            return True
        except Exception as e:
            logger.error(f"BigQuery update_approval_status failed: {e}")
            return False
    else:
        with _lock:
            if action_id in _APPROVAL_QUEUE:
                _APPROVAL_QUEUE[action_id]["status"] = status
                _APPROVAL_QUEUE[action_id]["decided_by"] = decided_by
                _APPROVAL_QUEUE[action_id]["decided_at"] = (
                    decided_at.isoformat() if isinstance(decided_at, datetime) else decided_at
                )
                return True
        return False



# Development helpers

def reset_mock_store() -> None:
    """Clear all in-memory stores. Used for testing only."""
    with _lock:
        _FINDINGS.clear()
        _AUDIT_LOG.clear()
        _APPROVAL_QUEUE.clear()
    logger.debug("In-memory stores cleared")
