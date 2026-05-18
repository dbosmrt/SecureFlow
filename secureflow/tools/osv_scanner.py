"""
SecureFlow — OSV Vulnerability Scanner Tool
Queries the OSV (Open Source Vulnerabilities) database to check
if a specific package version has known vulnerabilities.

API: https://api.osv.dev/v1/query (POST, free, no auth required)

Used by: dependency_scanner agent
"""
import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)

# API endpoint and timeout
OSV_API_URL = "https://api.osv.dev/v1/query"
REQUEST_TIMEOUT = 30  # seconds


async def osv_check(package_name: str, version: str, ecosystem: str) -> dict[str, Any]:
    """
    Query the OSV database for known vulnerabilities in a package.

    Args:
        package_name: Name of the package (e.g., 'requests', 'lodash').
        version: Version string (e.g., '2.6.0', '4.17.15').
        ecosystem: Package ecosystem. One of: PyPI, npm, Go, Maven,
                   NuGet, crates.io, RubyGems, Packagist.

    Returns:
        A dict with:
        - vulnerable (bool): Whether any vulnerabilities were found.
        - count (int): Number of vulnerabilities.
        - vulns (list[dict]): List of vulnerability summaries, each with:
            - id: OSV vulnerability ID (e.g., 'GHSA-xxxx').
            - summary: Brief description.
            - severity: CRITICAL/HIGH/MEDIUM/LOW based on CVSS.
            - aliases: Related CVE IDs.
            - fixed_version: First patched version (if available).
        - error (str | None): Error message if the query failed.
    """
    payload = {
        "version": version,
        "package": {
            "name": package_name,
            "ecosystem": ecosystem,
        },
    }

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.post(OSV_API_URL, json=payload)
            resp.raise_for_status()
            data = resp.json()

        raw_vulns = data.get("vulns", [])
        vulns = []
        for v in raw_vulns:
            # Extract severity from CVSS score in database_specific or severity field
            severity = _extract_severity(v)
            fixed = _extract_fixed_version(v, ecosystem)
            vulns.append({
                "id": v.get("id", "UNKNOWN"),
                "summary": v.get("summary", "No summary available"),
                "severity": severity,
                "aliases": v.get("aliases", []),
                "fixed_version": fixed,
            })

        return {
            "vulnerable": len(vulns) > 0,
            "count": len(vulns),
            "vulns": vulns,
            "error": None,
        }

    except httpx.TimeoutException:
        logger.error(f"OSV API timeout for {package_name}@{version}")
        return {
            "vulnerable": False,
            "count": 0,
            "vulns": [],
            "error": f"OSV API request timed out after {REQUEST_TIMEOUT}s",
        }
    except httpx.HTTPStatusError as e:
        logger.error(f"OSV API HTTP error for {package_name}@{version}: {e.response.status_code}")
        return {
            "vulnerable": False,
            "count": 0,
            "vulns": [],
            "error": f"OSV API returned HTTP {e.response.status_code}",
        }
    except Exception as e:
        logger.error(f"OSV API unexpected error for {package_name}@{version}: {e}")
        return {
            "vulnerable": False,
            "count": 0,
            "vulns": [],
            "error": str(e),
        }


def _extract_severity(vuln: dict) -> str:
    """Extract severity level from OSV vulnerability data."""
    # Try severity array first (newer OSV format)
    for sev in vuln.get("severity", []):
        score_str = sev.get("score", "")
        if "CVSS" in sev.get("type", ""):
            # Parse CVSS vector to get base score
            try:
                # Look for the base score in the vector
                parts = score_str.split("/")
                for part in parts:
                    if part.startswith("CVSS:"):
                        continue
                    # The score is typically available in database_specific
                    break
            except Exception:
                pass

    # Try database_specific for CVSS score
    db_specific = vuln.get("database_specific", {})
    cvss_score = db_specific.get("cvss_score") or db_specific.get("severity")
    if isinstance(cvss_score, (int, float)):
        if cvss_score >= 9.0:
            return "CRITICAL"
        elif cvss_score >= 7.0:
            return "HIGH"
        elif cvss_score >= 4.0:
            return "MEDIUM"
        else:
            return "LOW"

    if isinstance(cvss_score, str):
        return cvss_score.upper()

    # Fallback: check ecosystem_specific
    eco = vuln.get("ecosystem_specific", {})
    if eco.get("severity"):
        return str(eco["severity"]).upper()

    return "UNKNOWN"


def _extract_fixed_version(vuln: dict, ecosystem: str) -> str | None:
    """Extract the first fixed version from the affected ranges."""
    for affected in vuln.get("affected", []):
        pkg = affected.get("package", {})
        if pkg.get("ecosystem", "").lower() == ecosystem.lower():
            for rng in affected.get("ranges", []):
                for event in rng.get("events", []):
                    if "fixed" in event:
                        return event["fixed"]
    return None
