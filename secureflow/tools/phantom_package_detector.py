"""
SecureFlow -- Phantom Package Detector Tool
Checks if a package actually exists on its registry (PyPI or npm).
Non-existent packages flagged as CRITICAL (typosquatting / dependency confusion).

APIs:
  - PyPI:  https://pypi.org/pypi/{name}/json  (free, no auth)
  - npm:   https://registry.npmjs.org/{name}   (free, no auth)

Used by: dependency_scanner agent
"""
import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 15  # seconds

# Registry URL templates
REGISTRY_URLS = {
    "pypi": "https://pypi.org/pypi/{name}/json",
    "npm": "https://registry.npmjs.org/{name}",
}


async def check_package_exists(package_name: str, ecosystem: str) -> dict[str, Any]:
    """
    Check if a package exists on its registry.

    A non-existent package in a dependency file is a strong indicator of
    typosquatting or dependency confusion attacks.

    Args:
        package_name: Name of the package to verify (e.g., 'requsets').
        ecosystem: Package ecosystem. Currently supports: 'pypi', 'npm'.
                   Case-insensitive.

    Returns:
        A dict with:
        - exists (bool): Whether the package was found on the registry.
        - registry (str): Which registry was queried ('pypi' or 'npm').
        - status_code (int): HTTP status code from the registry.
        - latest_version (str | None): Latest version if the package exists.
        - is_phantom (bool): True if the package does NOT exist (inverse of exists).
        - risk_level (str): 'CRITICAL' if phantom, 'NONE' if exists.
        - error (str | None): Error message if the check failed.
    """
    eco_lower = ecosystem.lower()

    # Map common ecosystem names to our supported registries
    eco_map = {
        "pypi": "pypi",
        "pip": "pypi",
        "python": "pypi",
        "npm": "npm",
        "node": "npm",
        "javascript": "npm",
    }

    registry = eco_map.get(eco_lower)
    if registry is None:
        return {
            "exists": True,  # Assume exists for unsupported ecosystems
            "registry": eco_lower,
            "status_code": 0,
            "latest_version": None,
            "is_phantom": False,
            "risk_level": "UNKNOWN",
            "error": f"Unsupported ecosystem: {ecosystem}. Only 'pypi' and 'npm' are supported.",
        }

    url = REGISTRY_URLS[registry].format(name=package_name)

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(url)

        if resp.status_code == 200:
            # Package exists
            latest_version = _extract_latest_version(resp.json(), registry)
            return {
                "exists": True,
                "registry": registry,
                "status_code": 200,
                "latest_version": latest_version,
                "is_phantom": False,
                "risk_level": "NONE",
                "error": None,
            }
        elif resp.status_code == 404:
            # Package does NOT exist -> PHANTOM
            logger.warning(
                f"PHANTOM PACKAGE DETECTED: '{package_name}' does not exist on {registry}"
            )
            return {
                "exists": False,
                "registry": registry,
                "status_code": 404,
                "latest_version": None,
                "is_phantom": True,
                "risk_level": "CRITICAL",
                "error": None,
            }
        else:
            return {
                "exists": True,  # Assume exists on unexpected codes (be safe)
                "registry": registry,
                "status_code": resp.status_code,
                "latest_version": None,
                "is_phantom": False,
                "risk_level": "UNKNOWN",
                "error": f"Unexpected HTTP status: {resp.status_code}",
            }

    except httpx.TimeoutException:
        logger.error(f"Registry check timeout for {package_name} on {registry}")
        return {
            "exists": True,
            "registry": registry,
            "status_code": 0,
            "latest_version": None,
            "is_phantom": False,
            "risk_level": "UNKNOWN",
            "error": f"Request timed out after {REQUEST_TIMEOUT}s",
        }
    except Exception as e:
        logger.error(f"Registry check error for {package_name}: {e}")
        return {
            "exists": True,
            "registry": registry,
            "status_code": 0,
            "latest_version": None,
            "is_phantom": False,
            "risk_level": "UNKNOWN",
            "error": str(e),
        }


def _extract_latest_version(data: dict, registry: str) -> str | None:
    """Extract the latest version string from registry response."""
    try:
        if registry == "pypi":
            return data.get("info", {}).get("version")
        elif registry == "npm":
            return data.get("dist-tags", {}).get("latest")
    except Exception:
        pass
    return None
