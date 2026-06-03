"""
Phase 7 -- React Dashboard Tests
===================================
Validates dashboard structure, build output, and component integrity.
Cost: $0 (all local validation).

  Test 1: Package.json structure (no unnecessary deps)
  Test 2: All components exist
  Test 3: Build output exists and is valid
  Test 4: CSS design system tokens
  Test 5: API client completeness
  Test 6: Vite config has API proxy
"""
import os
import json
import time
import sys

DASHBOARD_ROOT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "dashboard"
)


def test_package_json():
    """Test 1: Validate package.json is lean and correct."""
    print("=== Test 1: package.json Validation ===")

    path = os.path.join(DASHBOARD_ROOT, "package.json")
    assert os.path.exists(path), "package.json not found"

    with open(path, "r") as f:
        pkg = json.load(f)

    print(f"  Name: {pkg.get('name')}")
    print(f"  Version: {pkg.get('version')}")

    deps = pkg.get("dependencies", {})
    dev_deps = pkg.get("devDependencies", {})
    print(f"  Dependencies: {len(deps)} ({', '.join(deps.keys())})")
    print(f"  Dev deps: {len(dev_deps)} ({', '.join(dev_deps.keys())})")

    assert "react" in deps, "Missing react"
    assert "react-dom" in deps, "Missing react-dom"
    assert "axios" not in deps, "axios should be removed (using native fetch)"
    assert "vite" in dev_deps, "Missing vite"

    scripts = pkg.get("scripts", {})
    assert "dev" in scripts, "Missing dev script"
    assert "build" in scripts, "Missing build script"

    print("PASSED: package.json is lean and correct\n")


def test_components_exist():
    """Test 2: All required components exist."""
    print("=== Test 2: Component Files ===")

    required = [
        "src/App.jsx",
        "src/main.jsx",
        "src/index.css",
        "src/api/client.js",
        "src/components/FindingsTable.jsx",
        "src/components/ApprovalCard.jsx",
        "src/components/RepoPosture.jsx",
        "src/components/ComplianceReport.jsx",
    ]

    for component in required:
        path = os.path.join(DASHBOARD_ROOT, component)
        exists = os.path.exists(path)
        size = os.path.getsize(path) if exists else 0
        status = f"OK ({size} bytes)" if exists else "MISSING"
        print(f"  {component}: {status}")
        assert exists, f"Missing component: {component}"

    # Check no dead files
    dead_files = ["src/App.css", "src/assets/react.svg", "src/assets/vite.svg"]
    for dead in dead_files:
        path = os.path.join(DASHBOARD_ROOT, dead)
        if os.path.exists(path):
            print(f"  WARNING: Dead file still exists: {dead}")

    print("PASSED: All components present\n")


def test_build_output():
    """Test 3: Verify build output exists."""
    print("=== Test 3: Build Output ===")

    dist_dir = os.path.join(DASHBOARD_ROOT, "dist")
    assert os.path.exists(dist_dir), "dist/ not found — run 'npm run build' first"

    index_html = os.path.join(dist_dir, "index.html")
    assert os.path.exists(index_html), "dist/index.html not found"

    assets_dir = os.path.join(dist_dir, "assets")
    assert os.path.exists(assets_dir), "dist/assets/ not found"

    # Check for JS and CSS bundles
    assets = os.listdir(assets_dir)
    js_files = [f for f in assets if f.endswith('.js')]
    css_files = [f for f in assets if f.endswith('.css')]

    print(f"  index.html: {os.path.getsize(index_html)} bytes")
    print(f"  JS bundles: {len(js_files)}")
    for f in js_files:
        size_kb = os.path.getsize(os.path.join(assets_dir, f)) / 1024
        print(f"    {f}: {size_kb:.1f} KB")
    print(f"  CSS bundles: {len(css_files)}")
    for f in css_files:
        size_kb = os.path.getsize(os.path.join(assets_dir, f)) / 1024
        print(f"    {f}: {size_kb:.1f} KB")

    assert len(js_files) >= 1, "No JS bundle found"
    assert len(css_files) >= 1, "No CSS bundle found"

    print("PASSED: Build output is valid\n")


def test_css_design_system():
    """Test 4: Verify CSS has proper design tokens."""
    print("=== Test 4: CSS Design System ===")

    path = os.path.join(DASHBOARD_ROOT, "src", "index.css")
    with open(path, "r") as f:
        css = f.read()

    tokens = {
        "inter_font": "'Inter'" in css,
        "dark_background": "--bg-body" in css,
        "glassmorphism": "backdrop-filter" in css,
        "gradient_brand": "linear-gradient" in css,
        "animations": "@keyframes" in css,
        "severity_badges": ".badge.critical" in css,
        "responsive": "@media" in css,
        "css_variables": ":root" in css,
        "hover_effects": ":hover" in css,
        "transitions": "transition" in css,
    }

    for token, present in tokens.items():
        status = "OK" if present else "MISSING"
        print(f"  {token}: {status}")

    missing = [k for k, v in tokens.items() if not v]
    assert not missing, f"Missing design tokens: {missing}"
    print("PASSED: Design system is complete\n")


def test_api_client():
    """Test 5: Verify API client has all required functions."""
    print("=== Test 5: API Client Completeness ===")

    path = os.path.join(DASHBOARD_ROOT, "src", "api", "client.js")
    with open(path, "r") as f:
        content = f.read()

    required_exports = [
        "getFindings",
        "getFindingsSummary",
        "getPendingApprovals",
        "processApproval",
        "getHealth",
    ]

    for fn in required_exports:
        found = f"export async function {fn}" in content or f"export function {fn}" in content
        status = "OK" if found else "MISSING"
        print(f"  {fn}: {status}")
        assert found, f"Missing API function: {fn}"

    # Verify no axios import
    assert "axios" not in content, "API client should use native fetch, not axios"
    assert "fetch" in content, "API client should use native fetch"
    print(f"  Uses native fetch: OK")

    print("PASSED: API client is complete\n")


def test_vite_config():
    """Test 6: Verify Vite config has API proxy."""
    print("=== Test 6: Vite Configuration ===")

    path = os.path.join(DASHBOARD_ROOT, "vite.config.js")
    with open(path, "r") as f:
        content = f.read()

    checks = {
        "react_plugin": "react()" in content,
        "api_proxy": "'/api'" in content,
        "proxy_target": "localhost:8000" in content,
        "build_outdir": "outDir" in content,
    }

    for check, passed in checks.items():
        status = "OK" if passed else "MISSING"
        print(f"  {check}: {status}")

    missing = [k for k, v in checks.items() if not v]
    assert not missing, f"Missing Vite config: {missing}"
    print("PASSED: Vite configuration is correct\n")


if __name__ == "__main__":
    print("=" * 60)
    print("  SecureFlow Phase 7 -- React Dashboard Tests")
    print("  Cost: $0 (all local validation)")
    print("=" * 60 + "\n")

    start = time.time()
    passed = 0
    total = 6

    tests = [
        test_package_json,
        test_components_exist,
        test_build_output,
        test_css_design_system,
        test_api_client,
        test_vite_config,
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
        print(f"  ALL PHASE 7 TESTS PASSED ({passed}/{total})  ({elapsed:.1f}s)")
    else:
        print(f"  PHASE 7: {passed}/{total} PASSED  ({elapsed:.1f}s)")
    print("=" * 60)

    sys.exit(0 if passed == total else 1)
