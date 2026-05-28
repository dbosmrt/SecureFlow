# SecureFlow: Architecture & Project Deep Dive

## 1. Executive Summary

**SecureFlow** is an autonomous, multi-agent software supply chain security system. Built for the Google Cloud + GitLab Hackathon 2026, it acts as an invisible, highly scalable team of security engineers that live directly inside your GitLab repository. 

Whenever a developer pushes code or opens a Merge Request (MR), SecureFlow intercepts the event, analyzes the code changes using a graph of specialized AI agents, detects complex security threats across multiple dimensions, and **autonomously writes the code to fix them**. However, it enforces a strict **Human-In-The-Loop (HITL)** policy, meaning no code is ever merged without a human reviewing and clicking "Approve" on a secure dashboard.

---

## 2. The Problem Statement: Why is SecureFlow Needed?

Modern software development is experiencing a severe bottleneck: **Development velocity is outpacing security capacity.**

1. **Alert Fatigue:** Traditional Static Application Security Testing (SAST) and Software Composition Analysis (SCA) tools are notoriously noisy. They throw hundreds of alerts based on rigid rules (e.g., regex matching, exact version strings). Developers, overwhelmed by false positives, begin ignoring the alerts entirely.
2. **The "Shift-Left" Paradox:** We tell developers to "shift security left" (fix vulnerabilities during the coding phase rather than post-deployment). However, expecting developers to also be security experts slows down feature delivery.
3. **Supply Chain Attacks:** Hackers are increasingly targeting the supply chain. Instead of hacking an application, they publish malicious packages to public registries (like PyPI or npm) with names suspiciously similar to popular packages (Typosquatting/Phantom Packages). Traditional tools often miss these because the packages are functionally "new" and not yet in CVE databases.
4. **Remediation is Manual:** Even when a tool correctly identifies a vulnerability, the developer still has to stop working, research the CVE, figure out how to patch it, and write the fix.

**SecureFlow solves this** by transitioning from *Static Detection* to *Autonomous Remediation*. It doesn't just point out the fire; it brings the fire extinguisher and asks you for permission to use it.

---

## 3. High-Level Architecture Flow

SecureFlow operates on a real-time, event-driven architecture hosted entirely on Google Cloud Platform (GCP).

1. **The Trigger:** A developer pushes a commit or creates a Merge Request in GitLab.
2. **The Ingestion:** GitLab fires a webhook to the SecureFlow FastAPI application (running on **Cloud Run**).
3. **The Event Bus:** To ensure the system doesn't drop webhooks during traffic spikes, the API immediately publishes the event to **Google Cloud Pub/Sub** and returns a `200 OK` to GitLab.
4. **The Processing:** A background subscriber picks up the event and initializes the **Google Agent Development Kit (ADK) Runner**.
5. **The Agent Graph:** The ADK Runner spins up the **Orchestrator Agent**, which acts as the manager. It delegates the code analysis to four specialized **Scanner Agents** that run in *parallel*.
6. **The Remediation:** Once scanning is complete, the **Remediation Agent** aggregates the findings and generates a patch.
7. **The HITL Gate:** The system halts. It logs a "Pending Action" to the database.
8. **The Approval:** A human logs into the **React Dashboard**, reviews the AI's findings and proposed code changes, and clicks "Approve."
9. **The Execution:** The system resumes, using the **GitLab MCP** to commit the fix directly to the repository.

---

## 4. Component Deep Dive: The "What" and "Why"

### A. The Brains: Google ADK & Gemini 2.5 Flash
* **What it is:** We utilized Google's native Agent Development Kit (ADK) to build a graph of agents. The intelligence engine powering these agents is **Gemini 2.5 Flash**.
* **Why it is necessary:** 
    * **ADK:** Building multi-agent systems from scratch is incredibly complex (managing state, message passing, tool calling). ADK provides a robust, native framework specifically optimized for Google Cloud.
    * **Gemini 2.5 Flash:** We chose *Flash* over *Pro* specifically for autonomous agents. Agents make dozens of LLM calls per minute. Flash provides near-instant reasoning at a fraction of the cost (~$0.01 per full repository scan), making it the only financially viable option for high-volume CI/CD pipelines. Furthermore, its massive context window allows it to read entire codebases at once.

### B. The Hands: GitLab MCP (Model Context Protocol)
* **What it is:** MCP is a standardized protocol that dictates how AI models interact with external data sources. We built a custom GitLab MCP client that wraps the GitLab REST API.
* **Why it is necessary:** You cannot give an LLM raw API access and say "fix the code." It will hallucinate endpoints and cause catastrophic damage. By wrapping GitLab in MCP tools (e.g., `get_mr_diff`, `create_commit`, `comment_on_mr`), we strictly define *exactly* what the AI is physically capable of doing, creating a secure boundary.

### C. The Multi-Agent Graph (The Workers)
Instead of using one massive, confused AI prompt, SecureFlow uses a hierarchical graph of specialized agents. 
* **Why it is necessary:** Specialization prevents hallucination. An agent explicitly told to "only look for hardcoded AWS keys" will perform vastly better than an agent told to "find all security bugs."

1. **Orchestrator Agent (The Manager):** Receives the initial webhook and coordinates the downstream agents.
2. **Dependency Scanner:** Extracts `requirements.txt` or `package.json`. It uses the **OSV API Tool** to check for known vulnerabilities, and the **Phantom Package Detector Tool** to ensure the package actually exists on PyPI/npm (preventing typosquatting attacks).
3. **Secret Hunter:** Analyzes the `git diff` for leaked API keys, database passwords, and tokens. Because it uses Gemini, it understands *context* (e.g., it knows `API_KEY="test_key_123"` in a `test_api.py` file is safe, whereas `API_KEY="AKIA..."` in `main.py` is a critical breach).
4. **Pipeline Auditor:** Scans `.gitlab-ci.yml` files. It looks for CI/CD anti-patterns (like running containers in `--privileged` mode or `curl | bash` patterns) and checks against **SLSA** (Supply chain Levels for Software Artifacts) compliance frameworks.
5. **Threat Intel Agent:** Takes the CVEs found by the dependency scanner and queries the **NVD API** to enrich the data with CVSS scores and plain-English explanations of *how* the vulnerability could be exploited.
6. **Remediation Agent (The Closer):** Gathers all findings. If it finds a vulnerable package, it uses the **Patch Generator Tool** to figure out the safe upgrade version. If it finds a secret, it writes the code to redact it. 

### D. The Safety Net: React Dashboard & HITL Callback
* **What it is:** A premium, glassmorphism-styled React application running on Vite. It connects to the FastAPI backend.
* **Why it is necessary:** **Never trust AI to blindly modify production code.** The Remediation Agent is physically blocked from writing to GitLab by a `before_tool_callback` in the ADK. When the agent tries to call `create_commit`, the callback intercepts it, pauses the agent, and sends the payload to the React Dashboard. Only when a human reviews the AI's reasoning and clicks "Approve" does the callback release the lock and allow the agent to proceed.

### E. The Memory & Compliance: BigQuery
* **What it is:** All findings, audit logs, and HITL actions are streamed directly into Google BigQuery.
* **Why it is necessary:** Security is ultimately about compliance and auditing. If an auditor asks, "Why was this dependency updated on Tuesday?", your organization needs a cryptographic-like trail. BigQuery stores the exact time of the scan, the AI's reasoning, the specific CVEs involved, and the username of the human who approved the fix.

---

## 5. Execution Flow Example (Step-by-Step)

Let's look at what happens when a developer accidentally types `pip install reqeusts` (a typo of `requests`) and pushes the code.

1. Developer pushes code to GitLab.
2. GitLab sends a webhook payload to Cloud Run.
3. Pub/Sub queues the event.
4. The **Orchestrator** spins up the scanners.
5. The **Dependency Scanner** looks at the `requirements.txt`. It queries PyPI for `reqeusts` using the Phantom Package tool.
6. PyPI returns a 404 (or the tool flags it as a known malicious typosquat).
7. The Dependency Scanner flags this as a **CRITICAL** supply chain attack.
8. The **Remediation Agent** realizes the developer meant `requests`. It prepares a git commit to change `reqeusts` to `requests==2.31.0`.
9. The ADK Callback intercepts the commit and flags it as `PENDING_APPROVAL`.
10. The Lead Security Engineer gets an alert, opens the **React Dashboard**, sees the typosquatting attempt, reviews the proposed code change, and clicks "Approve Fix."
11. SecureFlow pushes the corrected `requirements.txt` to the developer's branch.

---

## 6. Business Value & Hackathon Alignment

SecureFlow directly addresses the core theme of the Google Cloud + GitLab Hackathon by seamlessly blending Google's cutting-edge AI (Gemini + ADK) with GitLab's robust DevSecOps ecosystem (MCP + Webhooks). 

* **Cost Reduction:** Automates thousands of hours of manual code review and CVE research.
* **Risk Mitigation:** Catches zero-day typosquatting and secret leaks *before* they are merged into the `main` branch.
* **Developer Experience (DX):** Developers no longer get yelled at by security tools; instead, they get a helpful bot that writes the fix for them.
* **Enterprise Readiness:** Built on scalable GCP infrastructure (Cloud Run, Pub/Sub, BigQuery) with strict, auditable Human-in-the-Loop controls.
