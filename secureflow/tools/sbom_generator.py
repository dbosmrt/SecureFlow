"""
SecureFlow -- SBOM Generator Tool
Generates a CycloneDX-format Software Bill of Materials (SBOM)
by parsing dependency manifest files (requirements.txt, package.json).

Pure Python, no external API calls. Zero cost.

Used by: remediation_agent (to produce compliance artifacts)
"""
import json
import uuid
import re
import logging
from datetime import datetime
from typing import Any

logger = logging.getLogger(__name__)


async def generate_sbom(manifest_content: str, manifest_type: str, project_name: str = "unknown") -> dict[str, Any]:
    """
    Generate a CycloneDX v1.5 SBOM from a dependency manifest file.

    Args:
        manifest_content: Raw text content of the manifest file
                          (e.g., contents of requirements.txt or package.json).
        manifest_type: Type of manifest. One of:
                       'requirements.txt', 'package.json', 'Pipfile', 'pyproject.toml'.
        project_name: Name of the project for the SBOM metadata.

    Returns:
        A dict with:
        - success (bool): Whether SBOM was generated successfully.
        - sbom (dict): The CycloneDX JSON SBOM document.
        - component_count (int): Number of components in the SBOM.
        - format (str): Always 'CycloneDX'.
        - spec_version (str): Always '1.5'.
        - error (str | None): Error message if generation failed.
    """
    try:
        # Parse dependencies based on manifest type
        if manifest_type in ("requirements.txt", "requirements"):
            components = _parse_requirements_txt(manifest_content)
        elif manifest_type in ("package.json", "npm"):
            components = _parse_package_json(manifest_content)
        else:
            return {
                "success": False,
                "sbom": {},
                "component_count": 0,
                "format": "CycloneDX",
                "spec_version": "1.5",
                "error": f"Unsupported manifest type: {manifest_type}",
            }

        # Build CycloneDX SBOM
        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "tools": [
                    {
                        "vendor": "SecureFlow",
                        "name": "sbom_generator",
                        "version": "2.0.0",
                    }
                ],
                "component": {
                    "type": "application",
                    "name": project_name,
                },
            },
            "components": components,
        }

        return {
            "success": True,
            "sbom": sbom,
            "component_count": len(components),
            "format": "CycloneDX",
            "spec_version": "1.5",
            "error": None,
        }

    except Exception as e:
        logger.error(f"SBOM generation failed: {e}")
        return {
            "success": False,
            "sbom": {},
            "component_count": 0,
            "format": "CycloneDX",
            "spec_version": "1.5",
            "error": str(e),
        }


def _parse_requirements_txt(content: str) -> list[dict]:
    """Parse requirements.txt format into CycloneDX components."""
    components = []
    for line in content.strip().splitlines():
        line = line.strip()
        # Skip comments, empty lines, flags
        if not line or line.startswith("#") or line.startswith("-"):
            continue

        # Parse name and version specifier
        # Handles: requests==2.28.0, flask>=2.0, django~=4.2
        match = re.match(r"^([a-zA-Z0-9_\-\.]+)\s*([><=!~]+)?\s*([\d\.\*]+)?", line)
        if match:
            name = match.group(1)
            version = match.group(3) or "unspecified"
            components.append({
                "type": "library",
                "name": name,
                "version": version,
                "purl": f"pkg:pypi/{name}@{version}",
            })

    return components


def _parse_package_json(content: str) -> list[dict]:
    """Parse package.json format into CycloneDX components."""
    components = []
    try:
        pkg = json.loads(content)
    except json.JSONDecodeError:
        return components

    # Merge dependencies and devDependencies
    all_deps = {}
    all_deps.update(pkg.get("dependencies", {}))
    all_deps.update(pkg.get("devDependencies", {}))

    for name, version_spec in all_deps.items():
        # Strip version prefixes (^, ~, >=)
        version = re.sub(r"^[\^~>=<]+", "", version_spec)
        components.append({
            "type": "library",
            "name": name,
            "version": version,
            "purl": f"pkg:npm/{name}@{version}",
        })

    return components
