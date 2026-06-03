"""
Phase 3 -- FastAPI Server + Mock Store + HITL Tests
=====================================================
Tests the full API server with in-memory storage.
Starts uvicorn, hits all endpoints with httpx, validates responses.
"""
import asyncio
import time
import json


def test_store():
    """Test 1: BigQuery mock store — write, query, filter."""
    print("=== Test 1: Mock Store ===")
    from secureflow.memory.bigquery_store import (
        write_finding, query_findings, get_findings_count,
        write_approval_queue, get_pending_approvals,
        get_approval_status, update_approval_status,
        reset_mock_store,
    )
    from datetime import datetime

    # Clean slate
    reset_mock_store()

    # Write findings
    asyncio.run(write_finding({
        "id": "f-001", "mr_iid": 42, "project_id": "123",
        "scanner": "dependency", "severity": "CRITICAL",
        "title": "Vuln in requests", "status": "OPEN",
        "created_at": "2026-01-01T00:00:00",
    }))
    asyncio.run(write_finding({
        "id": "f-002", "mr_iid": 42, "project_id": "123",
        "scanner": "secret", "severity": "HIGH",
        "title": "Hardcoded API key", "status": "OPEN",
        "created_at": "2026-01-02T00:00:00",
    }))
    asyncio.run(write_finding({
        "id": "f-003", "mr_iid": 99, "project_id": "456",
        "scanner": "dependency", "severity": "MEDIUM",
        "title": "Outdated lodash", "status": "FIXED",
        "created_at": "2026-01-03T00:00:00",
    }))
    print("  Wrote 3 findings")

    # Query all
    all_findings = asyncio.run(query_findings())
    assert len(all_findings) == 3, f"Expected 3, got {len(all_findings)}"
    print(f"  query_findings() -> {len(all_findings)} results")

    # Filter by severity
    critical = asyncio.run(query_findings(severity="CRITICAL"))
    assert len(critical) == 1
    print(f"  filter severity=CRITICAL -> {len(critical)} result")

    # Filter by scanner
    dep = asyncio.run(query_findings(scanner="dependency"))
    assert len(dep) == 2
    print(f"  filter scanner=dependency -> {len(dep)} results")

    # Filter by status
    fixed = asyncio.run(query_findings(status="FIXED"))
    assert len(fixed) == 1
    print(f"  filter status=FIXED -> {len(fixed)} result")

    # Filter by mr_iid
    mr42 = asyncio.run(query_findings(mr_iid=42))
    assert len(mr42) == 2
    print(f"  filter mr_iid=42 -> {len(mr42)} results")

    # Severity counts
    counts = asyncio.run(get_findings_count())
    assert counts["CRITICAL"] == 1
    assert counts["HIGH"] == 1
    assert counts["MEDIUM"] == 1
    print(f"  severity counts: {counts}")

    # Approval queue
    asyncio.run(write_approval_queue(
        action_id="a-001",
        finding_id="f-001",
        action_type="create_merge_request",
        action_payload={"branch": "fix/vuln"},
        status="PENDING",
        requested_at=datetime.utcnow(),
    ))
    print("  Wrote 1 approval action")

    pending = asyncio.run(get_pending_approvals())
    assert len(pending) == 1
    print(f"  pending approvals: {len(pending)}")

    status = asyncio.run(get_approval_status("a-001"))
    assert status == "PENDING"
    print(f"  approval status: {status}")

    # Approve it
    asyncio.run(update_approval_status("a-001", "APPROVED", "admin", datetime.utcnow()))
    status = asyncio.run(get_approval_status("a-001"))
    assert status == "APPROVED"
    print(f"  after approve: {status}")

    pending = asyncio.run(get_pending_approvals())
    assert len(pending) == 0
    print(f"  pending after approve: {len(pending)}")

    print("PASSED: Mock store works\n")


def test_hitl_callback():
    """Test 2: HITL callback — correct signature and import."""
    print("=== Test 2: HITL Callback ===")
    from secureflow.callbacks.hitl_callback import (
        hitl_confirmation_callback,
        WRITE_TOOLS,
        READ_TOOLS,
    )
    import inspect

    # Check it's async
    assert asyncio.iscoroutinefunction(hitl_confirmation_callback)
    print("  Is async: True")

    # Check parameter names match ADK requirement
    sig = inspect.signature(hitl_confirmation_callback)
    param_names = list(sig.parameters.keys())
    assert param_names == ["tool", "args", "tool_context"], \
        f"Wrong params: {param_names}. ADK requires (tool, args, tool_context)"
    print(f"  Params: {param_names} (matches ADK spec)")

    # Check write tools
    assert "create_merge_request" in WRITE_TOOLS
    assert "create_issue" in WRITE_TOOLS
    print(f"  Write tools: {len(WRITE_TOOLS)} gated")
    print(f"  Read tools:  {len(READ_TOOLS)} pass-through")

    print("PASSED: HITL callback signature correct\n")


def test_api_server():
    """Test 3: Full API server — start, hit endpoints, validate responses."""
    print("=== Test 3: API Server (httpx) ===")
    import httpx
    from secureflow.memory.bigquery_store import reset_mock_store
    reset_mock_store()

    # Use TestClient for synchronous testing (no need to start uvicorn)
    from fastapi.testclient import TestClient
    from secureflow.api.main import app

    client = TestClient(app)

    # --- Health check ---
    r = client.get("/health")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "healthy"
    print(f"  GET /health -> {data}")

    # --- Root ---
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["service"] == "SecureFlow"
    print(f"  GET / -> service={data['service']}, version={data['version']}")

    # --- Webhook: valid event ---
    webhook_payload = {
        "object_kind": "merge_request",
        "project": {"id": 123, "name": "test-project"},
        "object_attributes": {
            "iid": 1, "state": "opened",
            "source_branch": "feature/auth",
            "target_branch": "main",
            "url": "https://gitlab.com/test/merge_requests/1",
        },
        "user": {"name": "Developer", "username": "dev123"},
    }
    r = client.post(
        "/webhook/gitlab",
        json=webhook_payload,
        headers={"X-Gitlab-Token": "mock-secret"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "accepted"
    assert data["object_kind"] == "merge_request"
    print(f"  POST /webhook/gitlab -> status={data['status']}, event_id={data['event_id'][:8]}...")

    # --- Webhook: unsupported event type ---
    r = client.post(
        "/webhook/gitlab",
        json={"object_kind": "note", "project": {}, "object_attributes": {}, "user": {}},
        headers={"X-Gitlab-Token": "mock-secret"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "skipped"
    print(f"  POST /webhook/gitlab (note) -> status={data['status']}")

    # --- Webhook: bad JSON ---
    r = client.post(
        "/webhook/gitlab",
        content=b"not json",
        headers={"Content-Type": "application/json", "X-Gitlab-Token": "mock-secret"},
    )
    assert r.status_code == 400
    print(f"  POST /webhook/gitlab (bad json) -> 400")

    # --- Findings: empty ---
    r = client.get("/api/findings")
    assert r.status_code == 200
    data = r.json()
    assert data["count"] == 0
    print(f"  GET /api/findings -> {data['count']} findings (empty)")

    # --- Seed some findings via store ---
    import asyncio
    from secureflow.memory.bigquery_store import write_finding, write_approval_queue
    from datetime import datetime

    asyncio.run(write_finding({
        "id": "f-100", "mr_iid": 1, "project_id": "123",
        "scanner": "dependency", "severity": "CRITICAL",
        "title": "CVE-2021-44228 in log4j", "status": "OPEN",
        "created_at": datetime.utcnow().isoformat(),
    }))
    asyncio.run(write_finding({
        "id": "f-101", "mr_iid": 1, "project_id": "123",
        "scanner": "secret", "severity": "HIGH",
        "title": "AWS key in config.py", "status": "OPEN",
        "created_at": datetime.utcnow().isoformat(),
    }))

    # --- Findings: with data ---
    r = client.get("/api/findings")
    data = r.json()
    assert data["count"] == 2
    print(f"  GET /api/findings -> {data['count']} findings")

    # --- Findings: filter ---
    r = client.get("/api/findings?severity=CRITICAL")
    data = r.json()
    assert data["count"] == 1
    print(f"  GET /api/findings?severity=CRITICAL -> {data['count']} finding")

    # --- Findings: summary ---
    r = client.get("/api/findings/summary")
    data = r.json()
    assert data["total"] == 2
    print(f"  GET /api/findings/summary -> total={data['total']}, by_severity={data['by_severity']}")

    # --- Approvals: empty ---
    r = client.get("/api/approvals")
    data = r.json()
    assert data["count"] == 0
    print(f"  GET /api/approvals -> {data['count']} pending")

    # --- Seed an approval ---
    asyncio.run(write_approval_queue(
        action_id="a-100",
        finding_id="f-100",
        action_type="create_merge_request",
        action_payload={"branch": "secureflow/fix-log4j"},
        status="PENDING",
        requested_at=datetime.utcnow(),
    ))

    # --- Approvals: with data ---
    r = client.get("/api/approvals")
    data = r.json()
    assert data["count"] == 1
    print(f"  GET /api/approvals -> {data['count']} pending")

    # --- Approval: get status ---
    r = client.get("/api/approvals/a-100")
    data = r.json()
    assert data["status"] == "PENDING"
    print(f"  GET /api/approvals/a-100 -> status={data['status']}")

    # --- Approval: approve ---
    r = client.post(
        "/api/approvals/a-100",
        json={"status": "APPROVED", "decided_by": "admin"},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "APPROVED"
    print(f"  POST /api/approvals/a-100 (approve) -> status={data['status']}")

    # --- Approval: check it's no longer pending ---
    r = client.get("/api/approvals")
    data = r.json()
    assert data["count"] == 0
    print(f"  GET /api/approvals -> {data['count']} pending (approved)")

    # --- Approval: double-approve should fail ---
    r = client.post(
        "/api/approvals/a-100",
        json={"status": "REJECTED", "decided_by": "admin"},
    )
    assert r.status_code == 409
    print(f"  POST /api/approvals/a-100 (double-decide) -> 409 Conflict")

    # --- Approval: not found ---
    r = client.get("/api/approvals/nonexistent")
    assert r.status_code == 404
    print(f"  GET /api/approvals/nonexistent -> 404")

    print("PASSED: API server works\n")


if __name__ == "__main__":
    print("=" * 60)
    print("  SecureFlow Phase 3 -- FastAPI + Store + HITL Tests")
    print("=" * 60 + "\n")

    start = time.time()

    test_store()
    test_hitl_callback()
    test_api_server()

    elapsed = time.time() - start
    print("=" * 60)
    print(f"  ALL PHASE 3 TESTS PASSED  ({elapsed:.1f}s)")
    print("=" * 60)
