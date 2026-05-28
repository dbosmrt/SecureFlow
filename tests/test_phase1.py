"""Phase 1 — Test Script: Validates config, models, and imports."""

def test_config():
    print("=== Test 1: Config ===")
    from secureflow.config import settings
    d = settings.model_dump()
    for k, v in d.items():
        print(f"  {k}: {v}")
    print(f"  is_production: {settings.is_production}")
    print(f"  bq_full_dataset: {settings.bq_full_dataset}")
    assert settings.environment == "development"
    assert settings.is_production is False
    assert settings.hitl_timeout_minutes == 15
    print("PASSED: Config loads with all defaults\n")


def test_models():
    print("=== Test 2: Models ===")
    from secureflow.models import Finding, AuditLogEntry, ApprovalAction, GitLabWebhookPayload

    # Test Finding
    f = Finding(
        mr_iid=42,
        project_id="123",
        scanner="dependency",
        severity="CRITICAL",
        title="Vulnerable dependency: requests",
        description="CVE-2018-18074 in requests 2.6.0",
        remediation="Upgrade requests to >=2.20.0",
        recommended_fix="requests>=2.20.0",
        cve_ids=["CVE-2018-18074"],
        cvss_score=9.8,
        risk_score=9,
    )
    d = f.to_dict()
    print(f"  Finding.id:       {d['id'][:8]}...")
    print(f"  Finding.scanner:  {d['scanner']}")
    print(f"  Finding.severity: {d['severity']}")
    print(f"  Finding.cve_ids:  {d['cve_ids']}")
    print(f"  Finding.cvss:     {d['cvss_score']}")
    print(f"  Finding.status:   {d['status']}")
    assert d["scanner"] == "dependency"
    assert d["severity"] == "CRITICAL"
    assert d["cvss_score"] == 9.8
    assert d["status"] == "OPEN"
    assert len(d["id"]) == 36  # UUID format
    print(f"  Finding fields ({len(d)} total): {list(d.keys())}")

    # Test AuditLogEntry
    a = AuditLogEntry(
        agent="dependency_scanner",
        action="scan_dependencies",
        tool_name="osv_check",
        tool_input={"package": "requests", "version": "2.6.0"},
        result="found 1 vulnerability",
    )
    ad = a.to_dict()
    print(f"  AuditLog.agent:   {ad['agent']}")
    print(f"  AuditLog.action:  {ad['action']}")
    assert ad["agent"] == "dependency_scanner"

    # Test ApprovalAction
    ap = ApprovalAction(
        finding_id=f.id,
        action_type="create_merge_request",
        action_payload={"branch": "fix/vuln-requests"},
    )
    apd = ap.to_dict()
    print(f"  Approval.status:  {apd['status']}")
    print(f"  Approval.type:    {apd['action_type']}")
    assert apd["status"] == "PENDING"

    # Test GitLabWebhookPayload (Pydantic model)
    w = GitLabWebhookPayload(
        object_kind="merge_request",
        project={"id": 123, "name": "test-project"},
        object_attributes={"iid": 1, "state": "opened", "source_branch": "feature"},
        user={"name": "developer", "username": "dev123"},
    )
    print(f"  Webhook.kind:     {w.object_kind}")
    print(f"  Webhook.project:  {w.project['name']}")
    assert w.object_kind == "merge_request"
    assert w.changes is None  # optional field

    print("PASSED: All 4 models instantiate, serialize, and validate\n")


def test_imports():
    print("=== Test 3: Package Imports ===")
    import secureflow
    print(f"  secureflow v{secureflow.__version__}")

    import secureflow.agents
    print("  secureflow.agents      OK")

    import secureflow.tools
    print("  secureflow.tools       OK")

    import secureflow.api
    print("  secureflow.api         OK")

    import secureflow.memory
    print("  secureflow.memory      OK")

    import secureflow.callbacks
    print("  secureflow.callbacks   OK")

    import secureflow.pubsub
    print("  secureflow.pubsub      OK")

    from secureflow.config import settings
    print("  secureflow.config      OK")

    from secureflow.models import Finding
    print("  secureflow.models      OK")

    print("PASSED: All 8 packages import cleanly\n")


def test_config_validation():
    print("=== Test 4: Config Validation ===")
    from secureflow.config import Settings

    # Test valid environment
    s = Settings(environment="production")
    assert s.is_production is True
    print("  environment='production' -> is_production=True  OK")

    s = Settings(environment="testing")
    assert s.is_production is False
    print("  environment='testing' -> is_production=False    OK")

    # Test invalid environment raises error
    try:
        Settings(environment="staging")
        print("  FAILED: should have raised ValueError for 'staging'")
    except Exception as e:
        print(f"  environment='staging' -> ValidationError       OK")

    # Test log level normalization
    s = Settings(log_level="debug")
    assert s.log_level == "DEBUG"
    print("  log_level='debug' -> 'DEBUG' (normalized)       OK")

    print("PASSED: Validators work correctly\n")


if __name__ == "__main__":
    print("=" * 60)
    print("  SecureFlow Phase 1 — Foundation Tests")
    print("=" * 60 + "\n")
    test_config()
    test_models()
    test_imports()
    test_config_validation()
    print("=" * 60)
    print("  ALL PHASE 1 TESTS PASSED")
    print("=" * 60)
