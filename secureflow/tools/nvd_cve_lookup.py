"""
SecureFlow -- NVD CVE Lookup Tool
Fetches CVE details from the NIST National Vulnerability Database (NVD).
Provides CVSS v3.1 scores, descriptions, and exploit availability.

API: https://services.nvd.nist.gov/rest/json/cves/2.0 (free, no auth required)
Rate limit: 5 requests per 30 seconds (without API key)

Used by: threat_intel_agent
"""
import httpx
import logging
from typing import Any

logger = logging.getLogger(__name__)

NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
REQUEST_TIMEOUT = 30  # seconds


async def nvd_lookup(cve_id: str) -> dict[str, Any]:
    """
    Fetch detailed vulnerability information from the NVD for a specific CVE.

    Args:
        cve_id: CVE identifier (e.g., 'CVE-2021-44228', 'CVE-2018-18074').

    Returns:
        A dict with:
        - cve_id (str): The CVE ID that was queried.
        - found (bool): Whether the CVE exists in NVD.
        - description (str): Human-readable vulnerability description.
        - cvss_score (float | None): CVSS v3.1 base score (0.0-10.0).
        - cvss_vector (str | None): Full CVSS v3.1 vector string.
        - severity (str): CRITICAL/HIGH/MEDIUM/LOW based on CVSS score.
        - published (str | None): Publication date (ISO format).
        - last_modified (str | None): Last modification date.
        - references (list[str]): Related reference URLs (max 5).
        - weaknesses (list[str]): CWE identifiers (e.g., 'CWE-502').
        - error (str | None): Error message if lookup failed.
    """
    params = {"cveId": cve_id}

    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            resp = await client.get(NVD_API_URL, params=params)
            resp.raise_for_status()
            data = resp.json()

        vulns = data.get("vulnerabilities", [])
        if not vulns:
            return {
                "cve_id": cve_id,
                "found": False,
                "description": "CVE not found in NVD",
                "cvss_score": None,
                "cvss_vector": None,
                "severity": "UNKNOWN",
                "published": None,
                "last_modified": None,
                "references": [],
                "weaknesses": [],
                "error": None,
            }

        cve_data = vulns[0].get("cve", {})

        # Extract description (prefer English)
        description = _extract_description(cve_data)

        # Extract CVSS v3.1 metrics
        cvss_score, cvss_vector, severity = _extract_cvss(cve_data)

        # Extract references (cap at 5)
        references = [
            ref.get("url", "")
            for ref in cve_data.get("references", [])[:5]
        ]

        # Extract CWE weaknesses
        weaknesses = _extract_weaknesses(cve_data)

        return {
            "cve_id": cve_id,
            "found": True,
            "description": description,
            "cvss_score": cvss_score,
            "cvss_vector": cvss_vector,
            "severity": severity,
            "published": cve_data.get("published"),
            "last_modified": cve_data.get("lastModified"),
            "references": references,
            "weaknesses": weaknesses,
            "error": None,
        }

    except httpx.TimeoutException:
        logger.error(f"NVD API timeout for {cve_id}")
        return _error_result(cve_id, f"NVD API timed out after {REQUEST_TIMEOUT}s")
    except httpx.HTTPStatusError as e:
        logger.error(f"NVD API HTTP error for {cve_id}: {e.response.status_code}")
        return _error_result(cve_id, f"NVD API returned HTTP {e.response.status_code}")
    except Exception as e:
        logger.error(f"NVD API unexpected error for {cve_id}: {e}")
        return _error_result(cve_id, str(e))


def _extract_description(cve_data: dict) -> str:
    """Extract English description from CVE data."""
    for desc in cve_data.get("descriptions", []):
        if desc.get("lang") == "en":
            return desc.get("value", "No description available")
    # Fallback: return first description
    descriptions = cve_data.get("descriptions", [])
    if descriptions:
        return descriptions[0].get("value", "No description available")
    return "No description available"


def _extract_cvss(cve_data: dict) -> tuple:
    """Extract CVSS v3.1 score, vector, and severity from CVE metrics."""
    metrics = cve_data.get("metrics", {})

    # Try CVSS v3.1 first, then v3.0
    for key in ("cvssMetricV31", "cvssMetricV30"):
        metric_list = metrics.get(key, [])
        if metric_list:
            cvss_data = metric_list[0].get("cvssData", {})
            score = cvss_data.get("baseScore")
            vector = cvss_data.get("vectorString")
            severity = cvss_data.get("baseSeverity", "UNKNOWN")
            return score, vector, severity.upper()

    # Fallback to v2
    v2_list = metrics.get("cvssMetricV2", [])
    if v2_list:
        cvss_data = v2_list[0].get("cvssData", {})
        score = cvss_data.get("baseScore")
        vector = cvss_data.get("vectorString")
        if score is not None:
            if score >= 9.0:
                severity = "CRITICAL"
            elif score >= 7.0:
                severity = "HIGH"
            elif score >= 4.0:
                severity = "MEDIUM"
            else:
                severity = "LOW"
        else:
            severity = "UNKNOWN"
        return score, vector, severity

    return None, None, "UNKNOWN"


def _extract_weaknesses(cve_data: dict) -> list[str]:
    """Extract CWE IDs from the weaknesses field."""
    cwes = []
    for weakness in cve_data.get("weaknesses", []):
        for desc in weakness.get("description", []):
            value = desc.get("value", "")
            if value.startswith("CWE-"):
                cwes.append(value)
    return cwes


def _error_result(cve_id: str, error: str) -> dict[str, Any]:
    """Return a standardized error result dict."""
    return {
        "cve_id": cve_id,
        "found": False,
        "description": "Lookup failed",
        "cvss_score": None,
        "cvss_vector": None,
        "severity": "UNKNOWN",
        "published": None,
        "last_modified": None,
        "references": [],
        "weaknesses": [],
        "error": error,
    }
