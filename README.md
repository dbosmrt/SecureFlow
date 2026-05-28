# SecureFlow

> Autonomous software supply chain security agent powered by Google ADK, Gemini, and GitLab MCP.

Developed for the **Google Cloud + GitLab Hackathon 2026** (Track: GitLab).

---

## What It Does

SecureFlow monitors GitLab repositories in real time. When a merge request is opened, it automatically:

1. **Scans dependencies** for known vulnerabilities (OSV database) and phantom/typosquatted packages
2. **Hunts for secrets** — hardcoded API keys, tokens, and credentials using regex pattern matching
3. **Audits CI/CD pipelines** for security anti-patterns and SLSA compliance
4. **Enriches findings** with CVE details, CVSS scores, and risk assessments from NVD
5. **Generates fix patches** and proposes remediation via GitLab merge requests
6. **Gates all write actions** behind a human-in-the-loop (HITL) approval dashboard

All 4 scanners run **in parallel**, and the remediation agent only acts after **human approval**.

---

## Architecture

```
                         ┌─────────────┐
                         │ Orchestrator │  (root LlmAgent)
                         └──────┬──────┘
                                │
                    ┌───────────┴───────────┐
                    │  SequentialAgent       │
                    │  (secureflow_pipeline) │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┼─────────────────┐
              │          ParallelAgent             │
              │     (parallel_security_scan)       │
              ├──────────┬──────────┬──────────────┤
              │          │          │              │
         dependency   secret   pipeline     threat_intel
          scanner     hunter    auditor       agent
              │          │          │              │
              └──────────┴──────────┴──────────────┘
                                │
                    ┌───────────┴───────────┐
                    │  Remediation Agent    │
                    │  (HITL gated)         │
                    └──────────────────────┘
```

---

## Project Structure

```
secureflow/
├── secureflow/                 # Core Python package
│   ├── __init__.py             # Package root (version)
│   ├── config.py               # Pydantic-settings configuration
│   ├── models.py               # Data contracts (Finding, AuditLog, etc.)
│   ├── agents/                 # ADK LlmAgent definitions
│   │   ├── __init__.py         # Exports root_agent for `adk web`
│   │   ├── orchestrator.py     # Root agent + pipeline composition
│   │   ├── dependency_scanner.py
│   │   ├── secret_hunter.py
│   │   ├── pipeline_auditor.py
│   │   ├── threat_intel_agent.py
│   │   └── remediation_agent.py
│   ├── tools/                  # Standalone async tool functions
│   │   ├── osv_scanner.py      # OSV vulnerability database (FREE API)
│   │   ├── phantom_package_detector.py  # PyPI + npm existence check
│   │   ├── nvd_cve_lookup.py   # NVD CVE details (FREE API)
│   │   ├── sbom_generator.py   # CycloneDX SBOM generation
│   │   ├── slsa_checker.py     # SLSA compliance analysis
│   │   ├── patch_generator.py  # Template-based fix patches
│   │   └── gitlab_mcp_client.py # GitLab MCP toolset factory
│   ├── api/                    # FastAPI server
│   │   ├── main.py             # App factory + CORS + routers
│   │   ├── health.py           # GET /health
│   │   ├── webhook.py          # POST /webhook/gitlab
│   │   ├── findings.py         # GET /api/findings
│   │   └── approvals.py        # GET/POST /api/approvals
│   ├── memory/                 # Persistence layer
│   │   └── bigquery_store.py   # In-memory (dev) / BigQuery (prod)
│   ├── callbacks/              # ADK callbacks
│   │   └── hitl_callback.py    # Human-in-the-loop gate
│   └── pubsub/                 # Event bus
│       ├── publisher.py        # Pub/Sub event publisher
│       └── subscriber.py       # Background worker
├── tests/                      # Phase-based test suites
│   ├── test_phase1.py          # Foundation (config, models, imports)
│   ├── test_phase2.py          # Free API tools (OSV, NVD, PyPI, npm)
│   ├── test_phase3.py          # FastAPI + mock store + HITL
│   ├── test_phase4.py          # GitLab MCP client + live validation
│   └── test_phase5.py          # ADK agents + Gemini simulation
├── demo/                       # Live demo scripts
│   └── scenarios/              # GitLab MR simulation scenarios
├── evals/                      # ADK evaluation framework
│   └── scenarios/              # Mock payloads for offline testing
├── infra/                      # Terraform (Phase 6)
├── dashboard/                  # React + Vite frontend (Phase 7)
├── requirements.txt            # Pinned Python dependencies
├── pyproject.toml              # Editable install config
├── Dockerfile                  # Multi-stage container build
├── docker-compose.yml          # Local development stack
├── cloudbuild.yaml             # Cloud Build CI/CD pipeline
├── .env.example                # Environment variable template
└── LICENSE
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- A [Google AI Studio API key](https://aistudio.google.com/apikey) (free tier available)
- A [GitLab Personal Access Token](https://gitlab.com/-/user_settings/personal_access_tokens) with `api` scope (free)

### Setup

```bash
# 1. Clone and enter the project
cd secureflow

# 2. Install dependencies
pip install -r requirements.txt
pip install -e .

# 3. Configure environment
cp .env.example .env
# Edit .env with your GOOGLE_API_KEY and GITLAB_TOKEN

# 4. Verify installation (runs all free tests)
python tests/test_phase1.py
python tests/test_phase2.py
python tests/test_phase3.py
```

### Run the Agent (Interactive)

```bash
# Start the ADK web UI (costs Gemini tokens)
adk web secureflow/agents/
# Open http://localhost:8000 and interact with the orchestrator
```

### Run the API Server

```bash
# Start FastAPI server (free, local)
uvicorn secureflow.api.main:app --reload --port 8000
# Docs at http://localhost:8000/docs
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Readiness probe |
| `GET` | `/` | Service info |
| `POST` | `/webhook/gitlab` | Receives GitLab webhook events |
| `GET` | `/api/findings` | Query findings (filter by severity, scanner, status) |
| `GET` | `/api/findings/summary` | Findings count by severity |
| `GET` | `/api/approvals` | List pending HITL actions |
| `GET` | `/api/approvals/{id}` | Get approval status |
| `POST` | `/api/approvals/{id}` | Approve or reject an action |

---

## Testing

Tests are organized by phase and cost:

```bash
# Phase 1: Foundation ($0)
python tests/test_phase1.py

# Phase 2: Free API tools ($0) — hits OSV, NVD, PyPI, npm
python tests/test_phase2.py

# Phase 3: FastAPI + mock store ($0) — 17 endpoint assertions
python tests/test_phase3.py

# Phase 4: GitLab MCP ($0) — requires GITLAB_TOKEN in .env
python tests/test_phase4.py

# Phase 5: Gemini agents (~$0.04) — requires GOOGLE_API_KEY in .env
python tests/test_phase5.py
```

---

## Cost Model

| Component | Cost | Notes |
|-----------|------|-------|
| OSV, PyPI, npm, NVD APIs | **Free** | No auth required |
| GitLab PAT | **Free** | `api` scope on gitlab.com |
| Gemini 2.5 Flash | **~$0.01/scan** | AI Studio free tier: 1M tokens/day |
| BigQuery | **Pay-per-query** | First 1TB/month free |
| Cloud Run | **Pay-per-request** | 2M requests/month free |
| Pub/Sub | **Pay-per-message** | First 10GB/month free |

---

## License

MIT License. See [LICENSE](LICENSE).
