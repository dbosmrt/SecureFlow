# Dashboard Directory

This directory contains the React single-page application built with Vite. It serves as the user interface for security engineers to interact with SecureFlow.

## Core Features

1. **Active Findings Table (`FindingsTable.jsx`)**: Displays the vulnerabilities detected by the agent, sortable by severity (Critical, High, Medium, Low), along with CVE links and metadata.
2. **HITL Approval Queue (`ApprovalCard.jsx`)**: When the remediation agent proposes a fix (like creating a patch MR), a card appears here. An engineer can inspect the LLM's proposed action payload and click "Approve" or "Reject". This communicates with the FastAPI backend, which unblocks the agent's callback.
3. **Security Posture Chart (`RepoPosture.jsx`)**: Visualizes the repository's security health score over time.
4. **Compliance Report (`ComplianceReport.jsx`)**: Displays the current SLSA level and SBOM generation status.

## Development

- `npm install`
- `npm run dev` (Connects to the FastAPI backend via Axios in `api/client.js`)
- `npm run build` (Outputs to `dist/`, which is then served statically by `api/main.py` in production).
