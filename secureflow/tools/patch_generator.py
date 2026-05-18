"""
SecureFlow -- Patch Generator Tool
Generates template-based code patches for common vulnerability fixes.
In Phase 5, this will be enhanced with Gemini for AI-powered patch generation.

Pure Python, no external API calls. Zero cost.

Used by: remediation_agent
"""
import logging
from typing import Any

logger = logging.getLogger(__name__)


async def generate_patch(
    finding_type: str,
    file_path: str,
    package_name: str,
    current_version: str,
    fixed_version: str,
    ecosystem: str,
) -> dict[str, Any]:
    """
    Generate a code patch to fix a security finding.

    Currently uses template-based generation for common patterns.
    Will be enhanced with Gemini LLM in Phase 5 for complex fixes.

    Args:
        finding_type: Type of finding. One of:
                      'vulnerable_dependency', 'phantom_package', 'hardcoded_secret',
                      'insecure_pipeline', 'outdated_dependency'.
        file_path: Path to the file that needs patching.
        package_name: Name of the affected package.
        current_version: Current (vulnerable) version.
        fixed_version: Version to upgrade to (or 'REMOVE' for phantom packages).
        ecosystem: Package ecosystem ('pypi', 'npm', etc.).

    Returns:
        A dict with:
        - success (bool): Whether a patch was generated.
        - patch (str): The unified diff patch content.
        - description (str): Human-readable description of the fix.
        - branch_name (str): Suggested git branch name.
        - commit_message (str): Suggested commit message.
        - error (str | None): Error message if generation failed.
    """
    try:
        if finding_type == "vulnerable_dependency":
            return _patch_vulnerable_dep(
                file_path, package_name, current_version, fixed_version, ecosystem
            )
        elif finding_type == "phantom_package":
            return _patch_phantom_package(
                file_path, package_name, ecosystem
            )
        elif finding_type == "hardcoded_secret":
            return _patch_hardcoded_secret(file_path, package_name)
        else:
            return {
                "success": False,
                "patch": "",
                "description": f"No template available for finding type: {finding_type}",
                "branch_name": "",
                "commit_message": "",
                "error": f"Unsupported finding type: {finding_type}. "
                         "AI-powered patch generation available in Phase 5.",
            }

    except Exception as e:
        logger.error(f"Patch generation failed: {e}")
        return {
            "success": False,
            "patch": "",
            "description": "Patch generation failed",
            "branch_name": "",
            "commit_message": "",
            "error": str(e),
        }


def _patch_vulnerable_dep(
    file_path: str,
    package_name: str,
    current_version: str,
    fixed_version: str,
    ecosystem: str,
) -> dict[str, Any]:
    """Generate patch for upgrading a vulnerable dependency."""
    if ecosystem.lower() in ("pypi", "pip", "python"):
        old_line = f"{package_name}=={current_version}"
        new_line = f"{package_name}>={fixed_version}"
    elif ecosystem.lower() in ("npm", "node"):
        old_line = f'"{package_name}": "{current_version}"'
        new_line = f'"{package_name}": "^{fixed_version}"'
    else:
        old_line = f"{package_name} {current_version}"
        new_line = f"{package_name} {fixed_version}"

    patch = (
        f"--- a/{file_path}\n"
        f"+++ b/{file_path}\n"
        f"@@ -1,1 +1,1 @@\n"
        f"-{old_line}\n"
        f"+{new_line}\n"
    )

    safe_name = package_name.replace("@", "").replace("/", "-")

    return {
        "success": True,
        "patch": patch,
        "description": f"Upgrade {package_name} from {current_version} to {fixed_version} to fix known vulnerabilities",
        "branch_name": f"secureflow/fix-{safe_name}-{fixed_version}",
        "commit_message": f"fix(security): upgrade {package_name} to {fixed_version}\n\n"
                          f"Fixes known vulnerabilities in {package_name} {current_version}.\n"
                          f"Automated fix by SecureFlow security agent.",
        "error": None,
    }


def _patch_phantom_package(
    file_path: str,
    package_name: str,
    ecosystem: str,
) -> dict[str, Any]:
    """Generate patch for removing a phantom (non-existent) package."""
    patch = (
        f"--- a/{file_path}\n"
        f"+++ b/{file_path}\n"
        f"@@ -1,1 +0,0 @@\n"
        f"-{package_name}\n"
    )

    safe_name = package_name.replace("@", "").replace("/", "-")

    return {
        "success": True,
        "patch": patch,
        "description": f"CRITICAL: Remove phantom package '{package_name}' - "
                       f"this package does not exist on {ecosystem} and may be a "
                       f"typosquatting or dependency confusion attack",
        "branch_name": f"secureflow/remove-phantom-{safe_name}",
        "commit_message": f"fix(security): remove phantom package {package_name}\n\n"
                          f"CRITICAL: '{package_name}' does not exist on {ecosystem}.\n"
                          f"This is a potential dependency confusion / typosquatting attack.\n"
                          f"Automated fix by SecureFlow security agent.",
        "error": None,
    }


def _patch_hardcoded_secret(file_path: str, secret_identifier: str) -> dict[str, Any]:
    """Generate patch suggesting env var replacement for hardcoded secrets."""
    env_var_name = secret_identifier.upper().replace("-", "_").replace(".", "_")

    patch = (
        f"--- a/{file_path}\n"
        f"+++ b/{file_path}\n"
        f'@@ -1,1 +1,1 @@\n'
        f'-{secret_identifier} = "REDACTED_SECRET_VALUE"\n'
        f'+{secret_identifier} = os.environ.get("{env_var_name}")\n'
    )

    return {
        "success": True,
        "patch": patch,
        "description": f"Replace hardcoded secret '{secret_identifier}' with environment variable lookup",
        "branch_name": f"secureflow/fix-secret-{env_var_name.lower()[:30]}",
        "commit_message": f"fix(security): remove hardcoded secret {secret_identifier}\n\n"
                          f"Replaced with os.environ.get('{env_var_name}').\n"
                          f"Automated fix by SecureFlow security agent.",
        "error": None,
    }
