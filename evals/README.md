# Evaluations Directory

This directory contains the test suite for the SecureFlow agents, utilizing the `adk eval` framework.

## Scenarios

We define mock webhook payloads (with malicious PR diffs) as JSON files in the `scenarios/` directory:
- `vulnerable_deps.json`: Tests the dependency scanner's ability to find CVEs using OSV.
- `hardcoded_secret.json`: Tests the secret hunter's regex and semantic search capabilities.
- `phantom_package.json`: Tests typosquatting detection using the PyPI/npm registry tools.
- `pipeline_secret_leak.json`: Tests the pipeline auditor's log analysis.

## Running Evals

Execute `./run_evals.sh` to trigger the `google-adk` evaluation engine against the `orchestrator` agent. It will run the agent locally against each scenario without hitting the real GitLab API, ensuring deterministic evaluation.
