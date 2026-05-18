"""
SecureFlow — Dependency Scanner Agent
Scans merge request diffs for vulnerable or phantom dependencies.

Tools:
  - GitLab MCP: get_merge_request_diffs (to read changed files)
  - FunctionTool: osv_check (query OSV vulnerability database)
  - FunctionTool: check_package_exists (detect phantom packages)

Output: JSON list of Finding objects for any vulnerable/phantom deps found.
"""
from google.adk.agents import LlmAgent
from google.adk.tools import FunctionTool

from secureflow.config import settings
from secureflow.tools.osv_scanner import osv_check
from secureflow.tools.phantom_package_detector import check_package_exists

INSTRUCTION = """You are the SecureFlow Dependency Scanner. Your job is to find
vulnerable and phantom (non-existent) packages in merge request diffs.

WORKFLOW:
1. Use get_merge_request_diffs to get the changed files in the MR.
2. Look for dependency files: requirements.txt, package.json, Pipfile,
   pyproject.toml, go.mod, pom.xml, Gemfile, etc.
3. For each NEW or CHANGED dependency line, extract: package_name, version, ecosystem.
4. Call osv_check(package_name, version, ecosystem) for each dependency.
5. Call check_package_exists(package_name, ecosystem) for each dependency.
6. If osv_check returns vulnerable=true, create a finding with severity based on CVSS.
7. If check_package_exists returns is_phantom=true, create a CRITICAL finding.

OUTPUT FORMAT (JSON list):
[
  {
    "scanner": "dependency",
    "severity": "CRITICAL|HIGH|MEDIUM|LOW",
    "title": "Short description",
    "description": "Detailed explanation",
    "file_path": "requirements.txt",
    "package_name": "requests",
    "current_version": "2.6.0",
    "fixed_version": "2.32.0",
    "cve_ids": ["CVE-2018-18074"],
    "cvss_score": 9.8,
    "remediation": "Upgrade requests to >=2.32.0",
    "recommended_fix": "requests>=2.32.0"
  }
]

RULES:
- Always mask any credentials found in dependency files.
- If no dependency files are changed, return an empty list [].
- Be precise with ecosystem names: PyPI, npm, Go, Maven, NuGet.
"""

dependency_scanner = LlmAgent(
    name="dependency_scanner",
    model=settings.gemini_model,
    description="Scans dependencies for known vulnerabilities and phantom packages",
    instruction=INSTRUCTION,
    tools=[
        FunctionTool(osv_check),
        FunctionTool(check_package_exists),
    ],
)
