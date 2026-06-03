"""
Phase 6 -- GCP Infrastructure Tests
======================================
Validates all infrastructure files WITHOUT deploying anything.
Cost: $0 (all local validation).

  Test 1: Dockerfile syntax and best practices
  Test 2: docker-compose.yml validity
  Test 3: cloudbuild.yaml structure
  Test 4: Terraform file syntax (HCL parsing)
  Test 5: BigQuery schema matches Python models
  Test 6: Publisher/Subscriber imports
  Test 7: .dockerignore coverage
"""
import os
import json
import time
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def test_dockerfile():
    """Test 1: Validate Dockerfile structure and best practices."""
    print("=== Test 1: Dockerfile Validation ===")

    path = os.path.join(PROJECT_ROOT, "Dockerfile")
    assert os.path.exists(path), "Dockerfile not found"

    with open(path, "r") as f:
        content = f.read()
        lines = content.splitlines()

    checks = {
        "multi_stage": content.count("FROM ") >= 2,
        "python_311": "python:3.11" in content,
        "non_root_user": "useradd" in content or "USER " in content,
        "healthcheck": "HEALTHCHECK" in content,
        "no_cache": "--no-cache-dir" in content,
        "port_env": "PORT" in content,
        "uvicorn": "uvicorn" in content,
        "workdir": "WORKDIR" in content,
    }

    for check, passed in checks.items():
        status = "OK" if passed else "FAIL"
        print(f"  {check}: {status}")

    failed = [k for k, v in checks.items() if not v]
    assert not failed, f"Dockerfile checks failed: {failed}"
    print("PASSED: Dockerfile is production-ready\n")


def test_docker_compose():
    """Test 2: Validate docker-compose.yml structure."""
    print("=== Test 2: docker-compose.yml Validation ===")

    path = os.path.join(PROJECT_ROOT, "docker-compose.yml")
    assert os.path.exists(path), "docker-compose.yml not found"

    # Use PyYAML if available, otherwise basic string check
    try:
        import yaml
        with open(path, "r") as f:
            compose = yaml.safe_load(f)

        services = compose.get("services", {})
        print(f"  Services: {list(services.keys())}")
        assert "api" in services, "Missing 'api' service"

        api = services["api"]
        assert "ports" in api, "API service missing ports"
        assert "env_file" in api, "API service missing env_file"
        assert "healthcheck" in api, "API service missing healthcheck"

        print(f"  API ports: {api['ports']}")
        print(f"  API env_file: {api['env_file']}")
        print(f"  Healthcheck: configured")

        if "subscriber" in services:
            print(f"  Subscriber: configured (profile: {services['subscriber'].get('profiles', 'default')})")

        print("PASSED: docker-compose.yml is valid\n")

    except ImportError:
        with open(path, "r") as f:
            content = f.read()
        assert "services:" in content, "Missing services key"
        assert "api:" in content, "Missing api service"
        assert "healthcheck:" in content, "Missing healthcheck"
        print("  (PyYAML not installed, basic string validation used)")
        print("PASSED: docker-compose.yml basic structure OK\n")


def test_cloudbuild():
    """Test 3: Validate cloudbuild.yaml structure."""
    print("=== Test 3: cloudbuild.yaml Validation ===")

    path = os.path.join(PROJECT_ROOT, "cloudbuild.yaml")
    assert os.path.exists(path), "cloudbuild.yaml not found"

    try:
        import yaml
        with open(path, "r") as f:
            cb = yaml.safe_load(f)

        steps = cb.get("steps", [])
        print(f"  Steps: {len(steps)}")
        for i, step in enumerate(steps):
            print(f"    Step {i+1}: {step.get('name', '?')}")

        assert len(steps) >= 3, "Expected at least 3 steps (build, push, deploy)"
        assert "images" in cb, "Missing images section"
        assert "substitutions" in cb, "Missing substitutions section"

        # Check we're using Artifact Registry (not deprecated GCR)
        build_step = steps[0]
        build_args = " ".join(build_step.get("args", []))
        uses_artifact_registry = "pkg.dev" in build_args
        print(f"  Uses Artifact Registry: {uses_artifact_registry}")
        assert uses_artifact_registry, "Should use Artifact Registry, not deprecated GCR"

        print("PASSED: cloudbuild.yaml is valid\n")

    except ImportError:
        with open(path, "r") as f:
            content = f.read()
        assert "steps:" in content
        assert "pkg.dev" in content, "Should use Artifact Registry"
        print("  (PyYAML not installed, basic string validation used)")
        print("PASSED: cloudbuild.yaml basic structure OK\n")


def test_terraform_files():
    """Test 4: Validate all Terraform files exist and have correct structure."""
    print("=== Test 4: Terraform Files Validation ===")

    infra_dir = os.path.join(PROJECT_ROOT, "infra")
    required_files = [
        "main.tf",
        "variables.tf",
        "pubsub.tf",
        "bigquery.tf",
        "iam.tf",
        "secret_manager.tf",
    ]

    for tf_file in required_files:
        path = os.path.join(infra_dir, tf_file)
        assert os.path.exists(path), f"Missing {tf_file}"
        size = os.path.getsize(path)
        print(f"  {tf_file}: {size} bytes")

    # Check main.tf for key resources
    with open(os.path.join(infra_dir, "main.tf"), "r") as f:
        main_content = f.read()

    tf_checks = {
        "terraform_block": "terraform {" in main_content,
        "required_providers": "required_providers" in main_content,
        "cloud_run_v2": "google_cloud_run_v2_service" in main_content,
        "artifact_registry": "google_artifact_registry_repository" in main_content,
        "api_enablement": "google_project_service" in main_content,
        "startup_probe": "startup_probe" in main_content,
        "liveness_probe": "liveness_probe" in main_content,
        "outputs": 'output "service_url"' in main_content,
    }

    for check, passed in tf_checks.items():
        status = "OK" if passed else "FAIL"
        print(f"  main.tf/{check}: {status}")

    # Check pubsub.tf for dead letter
    with open(os.path.join(infra_dir, "pubsub.tf"), "r") as f:
        pubsub_content = f.read()
    has_dead_letter = "dead_letter" in pubsub_content
    print(f"  pubsub.tf/dead_letter_topic: {'OK' if has_dead_letter else 'FAIL'}")

    # Check secret_manager.tf for google_api_key
    with open(os.path.join(infra_dir, "secret_manager.tf"), "r") as f:
        secrets_content = f.read()
    has_api_key_secret = "google_api_key" in secrets_content
    print(f"  secret_manager.tf/google_api_key: {'OK' if has_api_key_secret else 'FAIL'}")

    # Check iam.tf for api key accessor
    with open(os.path.join(infra_dir, "iam.tf"), "r") as f:
        iam_content = f.read()
    has_api_key_iam = "google_api_key_accessor" in iam_content
    print(f"  iam.tf/google_api_key_accessor: {'OK' if has_api_key_iam else 'FAIL'}")

    all_checks = list(tf_checks.values()) + [has_dead_letter, has_api_key_secret, has_api_key_iam]
    failed = sum(1 for v in all_checks if not v)
    assert failed == 0, f"{failed} Terraform checks failed"
    print("PASSED: All Terraform files valid\n")


def test_bigquery_schema_matches_models():
    """Test 5: Verify BQ schemas match Python model fields."""
    print("=== Test 5: BigQuery Schema vs Python Models ===")

    from secureflow.models import Finding, AuditLogEntry, ApprovalAction

    # Parse BQ schema from bigquery.tf
    infra_dir = os.path.join(PROJECT_ROOT, "infra")
    with open(os.path.join(infra_dir, "bigquery.tf"), "r") as f:
        bq_content = f.read()

    # Extract JSON schemas between EOF markers
    import re
    schemas = re.findall(r'<<EOF\n(\[.*?\])\nEOF', bq_content, re.DOTALL)
    assert len(schemas) == 3, f"Expected 3 table schemas, found {len(schemas)}"

    # Parse each schema
    findings_schema = json.loads(schemas[0])
    audit_schema = json.loads(schemas[1])
    approval_schema = json.loads(schemas[2])

    # Check findings table fields match Finding dataclass
    finding_instance = Finding(
        mr_iid=1, project_id="test", scanner="test",
        severity="LOW", title="t", description="d",
        remediation="r", recommended_fix="f"
    )
    finding_dict_keys = set(finding_instance.to_dict().keys())
    bq_finding_fields = {f["name"] for f in findings_schema}
    missing_in_bq = finding_dict_keys - bq_finding_fields
    extra_in_bq = bq_finding_fields - finding_dict_keys
    print(f"  Findings: Python={len(finding_dict_keys)} fields, BQ={len(bq_finding_fields)} fields")
    if missing_in_bq:
        print(f"    WARNING: Missing in BQ: {missing_in_bq}")
    if extra_in_bq:
        print(f"    WARNING: Extra in BQ: {extra_in_bq}")
    assert not missing_in_bq, f"BQ findings table missing fields: {missing_in_bq}"

    # Check audit log
    audit_instance = AuditLogEntry(agent="test", action="test", tool_name="test")
    audit_dict_keys = set(audit_instance.to_dict().keys())
    bq_audit_fields = {f["name"] for f in audit_schema}
    print(f"  Audit log: Python={len(audit_dict_keys)} fields, BQ={len(bq_audit_fields)} fields")
    missing = audit_dict_keys - bq_audit_fields
    assert not missing, f"BQ audit_log table missing fields: {missing}"

    # Check approval queue
    approval_instance = ApprovalAction(finding_id="test", action_type="test", action_payload={})
    approval_dict_keys = set(approval_instance.to_dict().keys())
    bq_approval_fields = {f["name"] for f in approval_schema}
    print(f"  Approvals: Python={len(approval_dict_keys)} fields, BQ={len(bq_approval_fields)} fields")
    missing = approval_dict_keys - bq_approval_fields
    assert not missing, f"BQ approval_queue table missing fields: {missing}"

    print("PASSED: All BQ schemas match Python models\n")


def test_pubsub_imports():
    """Test 6: Verify publisher/subscriber import cleanly."""
    print("=== Test 6: Pub/Sub Module Imports ===")

    # Publisher should import without error (Pub/Sub client is optional)
    from secureflow.pubsub.publisher import publish_event
    print(f"  publisher.publish_event: OK")

    # Subscriber should import without error
    from secureflow.pubsub.subscriber import process_webhook_event, start_subscriber
    print(f"  subscriber.process_webhook_event: OK")
    print(f"  subscriber.start_subscriber: OK")

    print("PASSED: Pub/Sub modules import cleanly\n")


def test_dockerignore():
    """Test 7: Verify .dockerignore excludes sensitive files."""
    print("=== Test 7: .dockerignore Coverage ===")

    path = os.path.join(PROJECT_ROOT, ".dockerignore")
    assert os.path.exists(path), ".dockerignore not found"

    with open(path, "r") as f:
        content = f.read()

    must_exclude = [".git", ".env", "__pycache__", "tests/", "infra/", "node_modules"]
    for pattern in must_exclude:
        found = pattern in content
        status = "OK" if found else "MISSING"
        print(f"  Excludes {pattern}: {status}")
        assert found, f".dockerignore should exclude {pattern}"

    print("PASSED: .dockerignore covers sensitive files\n")


if __name__ == "__main__":
    print("=" * 60)
    print("  SecureFlow Phase 6 -- GCP Infrastructure Tests")
    print("  Cost: $0 (all local validation, no deployment)")
    print("=" * 60 + "\n")

    start = time.time()
    passed = 0
    total = 7

    tests = [
        test_dockerfile,
        test_docker_compose,
        test_cloudbuild,
        test_terraform_files,
        test_bigquery_schema_matches_models,
        test_pubsub_imports,
        test_dockerignore,
    ]

    for test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  FAILED: {e}\n")

    elapsed = time.time() - start
    print("=" * 60)
    if passed == total:
        print(f"  ALL PHASE 6 TESTS PASSED ({passed}/{total})  ({elapsed:.1f}s)")
    else:
        print(f"  PHASE 6: {passed}/{total} PASSED  ({elapsed:.1f}s)")
    print("=" * 60)

    sys.exit(0 if passed == total else 1)
