import React, { useState, useEffect } from 'react';
import { ArrowLeft, Server, Code, GitMerge, FileWarning, Shield, Check, Activity, ShieldCheck, Cpu } from 'lucide-react';
import './Documentation.css';

/* ============================================================
   Custom Cursor (shared with Dashboard)
   ============================================================ */
const DocCursor = () => {
  const [pos, setPos] = useState({ x: -100, y: -100 });
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    const moveCursor = (e) => setPos({ x: e.clientX, y: e.clientY });
    const handleMouseOver = (e) => {
      if (e.target.closest('button, a, input, [role="button"]')) setIsHovering(true);
      else setIsHovering(false);
    };
    window.addEventListener('mousemove', moveCursor);
    window.addEventListener('mouseover', handleMouseOver);
    return () => {
      window.removeEventListener('mousemove', moveCursor);
      window.removeEventListener('mouseover', handleMouseOver);
    };
  }, []);

  return (
    <>
      <div
        className="dash-cursor-dot"
        style={{ transform: `translate(${pos.x - 4}px, ${pos.y - 4}px) scale(${isHovering ? 0 : 1})` }}
      />
      <div
        className="dash-cursor-ring"
        style={{ transform: `translate(${pos.x - 16}px, ${pos.y - 16}px) scale(${isHovering ? 1.5 : 1})` }}
      />
    </>
  );
};

/* ============================================================
   Logo SVG
   ============================================================ */
const LogoSVG = () => (
  <svg viewBox="0 0 100 100" className="dash-nav-logo-svg">
    <defs>
      <linearGradient id="logoGradDoc" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#fb923c" />
        <stop offset="100%" stopColor="#ea580c" />
      </linearGradient>
    </defs>
    <path
      d="M50 15 Q 85 30 85 65 Q 85 90 50 85 Q 15 90 15 65 Q 15 30 50 15 M50 15 Q 15 30 15 65 Q 15 80 50 75 Q 85 80 85 65 Q 85 30 50 15 Z"
      fill="none" stroke="url(#logoGradDoc)" strokeWidth="6"
    />
    <circle cx="50" cy="50" r="8" fill="#f97316" />
  </svg>
);

/* ============================================================
   Top Navigation
   ============================================================ */
const TopNav = ({ onNavigate }) => (
  <nav className="dash-nav glass-panel">
    <div className="dash-nav-left">
      <button className="dash-back-link" onClick={() => onNavigate && onNavigate('landing')}>
        <ArrowLeft style={{ width: 16, height: 16 }} />
      </button>
      <LogoSVG />
      <span className="dash-nav-brand">
        Secure<span className="dash-nav-brand-accent">Flow</span>
      </span>
      <div className="dash-nav-divider" />
      <span className="dash-nav-repo">
        <Server style={{ width: 16, height: 16 }} /> Architecture Documentation
      </span>
    </div>

    <div className="dash-nav-right">
      <div className="dash-nav-status">
        <div className="dash-nav-status-dot">
          <span className="ping animate-radar-ping" />
          <span className="solid" />
        </div>
        <span className="dash-nav-status-label">Agent Active</span>
      </div>
      <div className="dash-nav-avatar">DB</div>
    </div>
  </nav>
);

/* ============================================================
   Documentation Page
   ============================================================ */
const Documentation = ({ onNavigate }) => {
  return (
    <div className="doc-root">
      <DocCursor />
      <TopNav onNavigate={onNavigate} />

      <main className="doc-main">
        <div className="doc-hero">
          <div className="doc-hero-icon">
            <Server />
          </div>
          <h1>System Architecture & Data Flow</h1>
          <p>
            An in-depth guide on how SecureFlow works, its core components, 
            and the autonomous agent pipeline.
          </p>
        </div>

        <div className="doc-content-wrapper">
          <div className="doc-sidebar">
            <div className="doc-sidebar-inner glass-panel">
              <h4 className="doc-sidebar-title">Contents</h4>
              <ul className="doc-sidebar-list">
                <li><a href="#what-is-secureflow">What is SecureFlow?</a></li>
                <li><a href="#high-level-architecture">High-Level Architecture</a></li>
                <li><a href="#component-breakdown">Component Breakdown</a></li>
                <li><a href="#data-flow">Data Flow Walkthrough</a></li>
                <li><a href="#design-decisions">Key Design Decisions</a></li>
              </ul>
            </div>
          </div>

          <div className="doc-content glass-panel">
            <section id="what-is-secureflow" className="doc-section">
              <h2><Shield /> 1. What is SecureFlow?</h2>
              <p>
                SecureFlow is an <strong>autonomous software supply chain security agent</strong>. 
                When a developer opens a Merge Request (MR) on GitLab, SecureFlow:
              </p>
              <ul className="doc-list">
                <li><Check className="doc-list-icon" /> <strong>Scans dependencies</strong> for known vulnerabilities (OSV database)</li>
                <li><Check className="doc-list-icon" /> <strong>Hunts for secrets</strong> (API keys, tokens, credentials)</li>
                <li><Check className="doc-list-icon" /> <strong>Audits CI/CD pipelines</strong> for security anti-patterns and SLSA compliance</li>
                <li><Check className="doc-list-icon" /> <strong>Enriches findings</strong> with CVE details, CVSS scores, and risk assessments from NVD</li>
                <li><Check className="doc-list-icon" /> <strong>Generates fix patches</strong> and proposes remediation via GitLab</li>
                <li><Check className="doc-list-icon" /> <strong>Gates all write actions</strong> behind a human-in-the-loop (HITL) approval dashboard</li>
              </ul>
              <div className="doc-alert info">
                All 4 scanners run <strong>in parallel</strong>, and the remediation agent only acts after <strong>human approval</strong>.
              </div>
            </section>

            <div className="doc-divider" />

            <section id="high-level-architecture" className="doc-section">
              <h2><Cpu /> 2. High-Level Architecture</h2>
              <div className="doc-code-block">
                <pre>
{`        ┌────────────────────────────────────────┐
        │              GitLab                   │
        │  + Webhook (MR opened/push/pipeline)  │
        └──────────────┬─────────────────────────┘
                       │
        ┌──────────────▼─────────────────────────┐
        │      FastAPI Webhook Receiver           │
        │              (api/webhook.py)           │
        │           POST /webhook/gitlab          │
        └──────────────┬─────────────────────────┘
                       │
        ┌──────────────▼─────────────────────────┐
        │    Google Cloud Pub/Sub (async bus)     │
        │    ── OR local background task         │
        └──────────────┬─────────────────────────┘
                       │
        ┌──────────────▼─────────────────────────┐
        │        ADK Agent Pipeline               │
        │  ┌───────────────────────────┐          │
        │  │     Orchestrator           │          │
        │  │  (root LlmAgent)           │          │
        │  └───────────┬───────────────┘          │
        │              │                            │
        │  ┌───────────▼──────────────┐            │
        │  │  Sequential Agent         │            │
        │  │  (scan → remediate)       │            │
        │  └─────┬────────────────────┘            │
        │        │                                 │
        │  ┌─────▼──────────────────────┐           │
        │  │     Parallel Agent          │           │
        │  │   (4 scanners run together) │           │
        │  ├────────────┰────────────────┤           │
        │  │            │                │           │
        │  dependency  secret   pipeline threat_intel│
        │  scanner    hunter    auditor   agent      │
        │       │            │             │           │
        │       └────────────┴─────────────┘           │
        │                    │                           │
        │            ┌───────▼────────┐                   │
        │            │ Remediation   │                   │
        │            │ Agent (HITL)  │                   │
        │            └───────┬──────┘                   │
        └────────────────────│────────────────────────────┘`}
                </pre>
              </div>
            </section>

            <div className="doc-divider" />

            <section id="component-breakdown" className="doc-section">
              <h2><Code /> 3. Component Breakdown</h2>
              
              <h3>Trigger Layer: GitLab → Webhook</h3>
              <p>
                When a Merge Request is opened in GitLab, it sends a webhook POST to <code>/webhook/gitlab</code>.
                The endpoint verifies the token, parses the payload, and queues the event (via Pub/Sub in prod or background task locally).
              </p>
              <div className="doc-alert warning">
                <strong>Key design decision:</strong> The webhook endpoint returns <code>202 Accepted</code> immediately after queueing, so GitLab doesn't timeout.
              </div>

              <h3>Agent Layer: ADK Multi-Pipeline Orchestrator</h3>
              <p>
                SecureFlow uses <strong>Google ADK (Agent Development Kit)</strong> to define a multi-agent pipeline. Think of it as a directed acyclic graph where each node is an <code>LlmAgent</code>.
              </p>
              
              <div className="doc-grid">
                <div className="doc-card">
                  <h4>Dependency Scanner</h4>
                  <p>Find vulnerable/phantom packages in dependency files using OSV API.</p>
                </div>
                <div className="doc-card">
                  <h4>Secret Hunter</h4>
                  <p>Detect hardcoded secrets (API keys, tokens) using regex.</p>
                </div>
                <div className="doc-card">
                  <h4>Pipeline Auditor</h4>
                  <p>Audit <code>.gitlab-ci.yml</code> for security anti-patterns & SLSA.</p>
                </div>
                <div className="doc-card">
                  <h4>Threat Intel Agent</h4>
                  <p>Enrich findings with CVE/CVSS from NVD.</p>
                </div>
              </div>

              <h3>Remediation Agent & HITL Layer</h3>
              <p>
                The Remediation Agent is the <strong>only agent with write permissions</strong>. 
                ADK's <code>before_tool_callback</code> fires before a tool call. SecureFlow uses it to gate all GitLab write operations behind human approval.
              </p>
            </section>
            
            <div className="doc-divider" />

            <section id="data-flow" className="doc-section">
              <h2><Activity /> 4. Data Flow Walkthrough</h2>
              
              <div className="doc-step">
                <div className="doc-step-number">1</div>
                <div className="doc-step-content">
                  <h4>GitLab Webhook Fires</h4>
                  <p>GitLab MR Opened → POST /webhook/gitlab → X-Gitlab-Token validated → Event queued → Returns 202 Accepted</p>
                </div>
              </div>
              
              <div className="doc-step">
                <div className="doc-step-number">2</div>
                <div className="doc-step-content">
                  <h4>ADK Runner Processes Event</h4>
                  <p>Subscriber pulls message → Creates ADK Session → Activates Runner with orchestrator root agent</p>
                </div>
              </div>
              
              <div className="doc-step">
                <div className="doc-step-number">3</div>
                <div className="doc-step-content">
                  <h4>Agent Pipeline Executes</h4>
                  <p>Orchestrator delegates to full pipeline. Parallel scan runs 4 scanners. Then Remediation agent generates patches and proposes actions.</p>
                </div>
              </div>

              <div className="doc-step">
                <div className="doc-step-number">4</div>
                <div className="doc-step-content">
                  <h4>Human Approval (HITL)</h4>
                  <p>HITL callback intercepts write tools → Adds to approval queue → Dashboard shows pending action → Human approves → Tool executes</p>
                </div>
              </div>
            </section>

            <div className="doc-divider" />

            <section id="design-decisions" className="doc-section">
              <h2><ShieldCheck /> 5. Key Design Decisions</h2>
              
              <div className="doc-qa">
                <h4>Why ADK multi-agent instead of a single prompt?</h4>
                <p>Each scanner can be tested, improved, and reasoned about independently. Parallel execution saves time. HITL only gates the remediation agent, not the whole pipeline.</p>
              </div>
              
              <div className="doc-qa">
                <h4>Why HITL only on remediation?</h4>
                <p>Scanning agents are read-only (no side effects). Remediation is write (creates MRs/issues). We only gate the write operations to avoid accidentally spamming the GitLab project.</p>
              </div>

              <div className="doc-qa">
                <h4>Why BigQuery for persistence?</h4>
                <p>Serverless, no operational overhead, cheap for write-heavy workloads. Can easily query structured data. An in-memory fallback is used for rapid local development.</p>
              </div>
            </section>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Documentation;
