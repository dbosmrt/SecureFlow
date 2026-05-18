"""
SecureFlow — Secret Hunter Agent
Scans merge request diffs for hardcoded secrets, API keys, tokens,
and credentials using regex patterns.

Tools:
  - GitLab MCP: get_merge_request_diffs (to read changed files)
  - FunctionTool: scan_for_secrets (regex-based secret detection)

Output: JSON list of Finding objects for any detected secrets.
"""
import re
import logging
from typing import Any

from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from secureflow.config import settings

logger = logging.getLogger(__name__)

# High-confidence regex patterns for common secret types
SECRET_PATTERNS = {
    "AWS Access Key": r"AKIA[0-9A-Z]{16}",
    "AWS Secret Key": r"(?i)aws_secret_access_key\s*[=:]\s*['\"]?([A-Za-z0-9/+=]{40})",
    "GitHub Token": r"gh[ps]_[A-Za-z0-9_]{36,}",
    "GitLab Token": r"glpat-[A-Za-z0-9\-_]{20,}",
    "Google API Key": r"AIza[0-9A-Za-z\-_]{35}",
    "Slack Token": r"xox[bpors]-[0-9]{10,13}-[0-9]{10,13}-[a-zA-Z0-9]{24,}",
    "Generic API Key": r"(?i)(api[_-]?key|apikey)\s*[=:]\s*['\"]?([A-Za-z0-9_\-]{20,})",
    "Generic Secret": r"(?i)(secret|password|passwd|pwd)\s*[=:]\s*['\"]?([^\s'\"]{8,})",
    "Private Key": r"-----BEGIN (?:RSA |EC |DSA )?PRIVATE KEY-----",
    "JWT Token": r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}",
    "Hex Token (32+)": r"(?i)(token|key|secret)\s*[=:]\s*['\"]?([0-9a-f]{32,})",
}


async def scan_for_secrets(diff_content: str, file_path: str) -> dict[str, Any]:
    """
    Scan a code diff for hardcoded secrets using regex patterns.

    Args:
        diff_content: The raw diff text to scan (from MR diffs).
        file_path: Path of the file being scanned (for context).

    Returns:
        A dict with:
        - secrets_found (bool): Whether any secrets were detected.
        - count (int): Number of secrets found.
        - findings (list[dict]): List of detected secrets with:
            - type: Type of secret (e.g., 'AWS Access Key').
            - line: The line containing the secret (MASKED).
            - line_number: Approximate line number.
            - severity: Always 'CRITICAL' for secrets.
        - error (str | None): Error message if scan failed.
    """
    try:
        findings = []

        for line_num, line in enumerate(diff_content.splitlines(), 1):
            # Only scan added lines (lines starting with +)
            if not line.startswith("+"):
                continue

            clean_line = line.lstrip("+").strip()
            if not clean_line or clean_line.startswith("#") or clean_line.startswith("//"):
                continue

            for secret_type, pattern in SECRET_PATTERNS.items():
                if re.search(pattern, clean_line):
                    # MASK the secret in output for safety
                    masked = re.sub(
                        r"([A-Za-z0-9_\-/+=]{4})[A-Za-z0-9_\-/+=]{4,}",
                        r"\1****REDACTED****",
                        clean_line,
                    )
                    findings.append({
                        "type": secret_type,
                        "line": masked,
                        "line_number": line_num,
                        "file_path": file_path,
                        "severity": "CRITICAL",
                    })
                    break  # One match per line is enough

        return {
            "secrets_found": len(findings) > 0,
            "count": len(findings),
            "findings": findings,
            "error": None,
        }

    except Exception as e:
        logger.error(f"Secret scan failed for {file_path}: {e}")
        return {
            "secrets_found": False,
            "count": 0,
            "findings": [],
            "error": str(e),
        }


INSTRUCTION = """You are the SecureFlow Secret Hunter. Your job is to detect
hardcoded secrets, API keys, tokens, and credentials in merge request diffs.

WORKFLOW:
1. Use get_merge_request_diffs to get the changed files.
2. For EACH changed file, call scan_for_secrets(diff_content, file_path).
3. Report all detected secrets as CRITICAL findings.

OUTPUT FORMAT (JSON list):
[
  {
    "scanner": "secret",
    "severity": "CRITICAL",
    "title": "Hardcoded AWS Access Key detected",
    "description": "Found AWS Access Key in config.py line 42",
    "file_path": "config.py",
    "line_number": 42,
    "remediation": "Remove the secret and rotate the credential immediately. Use environment variables or a secret manager.",
    "recommended_fix": "aws_key = os.environ.get('AWS_ACCESS_KEY_ID')"
  }
]

CRITICAL RULES:
- NEVER output the actual secret value. Always use REDACTED placeholders.
- Every hardcoded secret is severity=CRITICAL, no exceptions.
- Check ALL file types, not just .py — also .env, .yml, .json, .js, .ts, etc.
- If no secrets are found, return an empty list [].
"""

secret_hunter = LlmAgent(
    name="secret_hunter",
    model=settings.gemini_model,
    description="Detects hardcoded secrets, API keys, and credentials in code",
    instruction=INSTRUCTION,
    tools=[
        FunctionTool(scan_for_secrets),
    ],
)
