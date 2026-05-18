"""
SecureFlow -- SLSA Compliance Checker Tool
Analyzes a .gitlab-ci.yml pipeline configuration to determine
the SLSA (Supply-chain Levels for Software Artifacts) compliance level.

Pure Python analysis, no external API calls. Zero cost.

SLSA Levels:
  Level 1: Build process is documented (has CI config)
  Level 2: Hosted build + version control (uses runners, has source)
  Level 3: Hardened builds (isolated, parameterless, hermetic)
  Level 4: Two-party review + hermetic + reproducible

Used by: pipeline_auditor agent
"""
import re
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def check_slsa_compliance(ci_config_content: str) -> dict[str, Any]:
    """
    Analyze a .gitlab-ci.yml configuration for SLSA compliance.

    Args:
        ci_config_content: Raw YAML content of .gitlab-ci.yml file.

    Returns:
        A dict with:
        - slsa_level (int): Achieved SLSA level (0-4).
        - checks (dict): Individual check results (bool per check).
        - recommendations (list[str]): Suggestions to improve compliance.
        - risk_factors (list[str]): Identified security risks in the pipeline.
        - error (str | None): Error message if analysis failed.
    """
    try:
        checks = {
            "has_ci_config": True,  # We received content, so this is true
            "has_build_stage": False,
            "has_test_stage": False,
            "uses_pinned_images": False,
            "no_allow_failure_on_security": True,
            "has_artifact_signing": False,
            "has_sast_scanning": False,
            "has_dependency_scanning": False,
            "no_privileged_mode": True,
            "has_protected_branches": False,
            "has_review_requirement": False,
            "has_provenance_generation": False,
        }

        recommendations = []
        risk_factors = []
        content_lower = ci_config_content.lower()

        # --- Level 1 checks: documented build ---
        if re.search(r"\bbuild\b", content_lower):
            checks["has_build_stage"] = True
        else:
            recommendations.append("Add a 'build' stage to your pipeline")

        if re.search(r"\btest\b", content_lower):
            checks["has_test_stage"] = True
        else:
            recommendations.append("Add a 'test' stage to your pipeline")

        # --- Level 2 checks: version-controlled build ---
        # Check for pinned Docker images (sha256 digest)
        if re.search(r"image:\s*\S+@sha256:", ci_config_content):
            checks["uses_pinned_images"] = True
        else:
            recommendations.append("Pin Docker images using sha256 digests (e.g., image: python@sha256:abc123)")

        # Check for security scanning
        if re.search(r"\bsast\b|semgrep|bandit|sonarqube", content_lower):
            checks["has_sast_scanning"] = True
        else:
            recommendations.append("Add SAST scanning (e.g., GitLab SAST, Semgrep, or Bandit)")

        if re.search(r"dependency.scanning|safety\s+check|pip.audit|npm\s+audit|osv-scanner", content_lower):
            checks["has_dependency_scanning"] = True
        else:
            recommendations.append("Add dependency scanning (e.g., pip-audit, npm audit, osv-scanner)")

        # --- Level 3 checks: hardened builds ---
        # Check for privileged mode (security risk)
        if re.search(r"privileged:\s*true", content_lower):
            checks["no_privileged_mode"] = False
            risk_factors.append("Pipeline uses privileged mode - containers can escape isolation")

        # Check for allow_failure on security jobs
        if re.search(r"allow_failure:\s*true", content_lower):
            # Check if it's on a security-related job
            if re.search(r"(sast|security|scan).*allow_failure:\s*true", content_lower, re.DOTALL):
                checks["no_allow_failure_on_security"] = False
                risk_factors.append("Security jobs have allow_failure:true - failures will be silently ignored")

        # Check for artifact signing
        if re.search(r"cosign|sigstore|gpg\s+sign|artifact.*sign", content_lower):
            checks["has_artifact_signing"] = True
        else:
            recommendations.append("Add artifact signing (e.g., cosign, sigstore)")

        # --- Level 4 checks: two-party review + provenance ---
        if re.search(r"protected|approval|review|merge.request.approval", content_lower):
            checks["has_review_requirement"] = True
        else:
            recommendations.append("Enforce merge request approvals on protected branches")

        if re.search(r"provenance|slsa.provenance|in-toto|attestation", content_lower):
            checks["has_provenance_generation"] = True
        else:
            recommendations.append("Add SLSA provenance generation to your build pipeline")

        # --- Additional risk factors ---
        if re.search(r"curl\s.*\|\s*sh|wget\s.*\|\s*bash|curl\s.*\|\s*bash", content_lower):
            risk_factors.append("Pipeline uses curl|bash pattern - risk of code injection")

        if re.search(r"\$\{?\w*TOKEN\w*\}?|\$\{?\w*SECRET\w*\}?|\$\{?\w*PASSWORD\w*\}?", ci_config_content):
            if not re.search(r"variables:.*\n.*protected:\s*true", ci_config_content, re.DOTALL):
                risk_factors.append("Secrets used in pipeline may not be protected variables")

        # Calculate SLSA level
        slsa_level = _calculate_level(checks)

        return {
            "slsa_level": slsa_level,
            "checks": checks,
            "recommendations": recommendations,
            "risk_factors": risk_factors,
            "error": None,
        }

    except Exception as e:
        logger.error(f"SLSA compliance check failed: {e}")
        return {
            "slsa_level": 0,
            "checks": {},
            "recommendations": [],
            "risk_factors": [],
            "error": str(e),
        }


def _calculate_level(checks: dict) -> int:
    """Calculate SLSA level from individual check results."""
    # Level 1: has build process
    if not checks.get("has_ci_config") or not checks.get("has_build_stage"):
        return 0

    level = 1

    # Level 2: version-controlled + some automation
    if (checks.get("has_test_stage") and
            (checks.get("has_sast_scanning") or checks.get("has_dependency_scanning"))):
        level = 2

    # Level 3: hardened builds
    if (level >= 2 and
            checks.get("uses_pinned_images") and
            checks.get("no_privileged_mode") and
            checks.get("no_allow_failure_on_security")):
        level = 3

    # Level 4: two-party review + provenance
    if (level >= 3 and
            checks.get("has_artifact_signing") and
            checks.get("has_review_requirement") and
            checks.get("has_provenance_generation")):
        level = 4

    return level
