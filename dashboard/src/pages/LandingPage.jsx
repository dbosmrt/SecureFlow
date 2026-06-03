import React, { useState, useEffect, useRef } from 'react';
import {
  Shield, Check, ArrowRight, Play, Server, Bot,
  Lock, Eye, AlertTriangle,
  Code, GitMerge, FileWarning, Plug
} from 'lucide-react';
import './LandingPage.css';

/* ============================================================
   Reveal — Intersection Observer entrance animation
   ============================================================ */
const Reveal = ({ children, delay = 0, direction = 'up' }) => {
  const [isVisible, setIsVisible] = useState(false);
  const ref = useRef(null);

  useEffect(() => {
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) {
          setIsVisible(true);
          observer.unobserve(entry.target);
        }
      },
      { threshold: 0.1, rootMargin: '0px 0px -50px 0px' }
    );
    if (ref.current) observer.observe(ref.current);
    return () => observer.disconnect();
  }, []);

  const hiddenClass = isVisible ? 'visible' : `hidden-${direction}`;

  return (
    <div
      ref={ref}
      style={{ transitionDelay: `${delay}ms`, transitionDuration: '1000ms' }}
      className={`reveal ${hiddenClass}`}
    >
      {children}
    </div>
  );
};

/* ============================================================
   Custom Cursor — Glassmorphic dual-ring cursor
   ============================================================ */
const CustomCursor = () => {
  const [pos, setPos] = useState({ x: -100, y: -100 });
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    const moveCursor = (e) => setPos({ x: e.clientX, y: e.clientY });
    const handleMouseOver = (e) => {
      if (e.target.closest('button, a, input, [role="button"]')) {
        setIsHovering(true);
      } else {
        setIsHovering(false);
      }
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
        className="cursor-dot"
        style={{
          transform: `translate(${pos.x - 4}px, ${pos.y - 4}px) scale(${isHovering ? 0 : 1})`,
        }}
      />
      <div
        className="cursor-ring"
        style={{
          transform: `translate(${pos.x - 20}px, ${pos.y - 20}px) scale(${isHovering ? 1.5 : 1})`,
        }}
      />
    </>
  );
};

/* ============================================================
   Navbar
   ============================================================ */
const Navbar = ({ onNavigate }) => (
  <nav className="landing-nav">
    <div className="landing-nav-inner">
      <div className="nav-logo">
        <div className="nav-logo-icon">
          <Shield style={{ width: 24, height: 24, color: 'white' }} />
        </div>
        <span className="nav-logo-text">SecureFlow</span>
      </div>
      <div className="nav-actions">
        <button className="nav-doc-link" onClick={() => onNavigate && onNavigate('connect')}>
          <Plug style={{ width: 14, height: 14, marginRight: 6 }} />Connect Repo
        </button>
        <button className="nav-cta" onClick={() => onNavigate && onNavigate('dashboard')}>
          <span style={{ position: 'relative', zIndex: 10, display: 'flex', alignItems: 'center' }}>
            Open Dashboard <ArrowRight style={{ width: 16, height: 16, marginLeft: 8 }} />
          </span>
        </button>
      </div>
    </div>
  </nav>
);

/* ============================================================
   Hero
   ============================================================ */
const Hero = ({ onNavigate }) => {
  const botRef = useRef(null);
  const [eyeOffset, setEyeOffset] = useState({ x: 0, y: 0 });
  const [headRotation, setHeadRotation] = useState({ x: 0, y: 0 });

  useEffect(() => {
    const handleMouseMove = (e) => {
      if (!botRef.current) return;
      const rect = botRef.current.getBoundingClientRect();
      const botX = rect.left + rect.width / 2;
      const botY = rect.top + rect.height / 2;

      const deltaX = e.clientX - botX;
      const deltaY = e.clientY - botY;

      const angle = Math.atan2(deltaY, deltaX);
      const distance = Math.min(Math.hypot(deltaX, deltaY) / 12, 16);

      setEyeOffset({
        x: Math.cos(angle) * distance,
        y: Math.sin(angle) * distance,
      });

      setHeadRotation({
        x: (deltaY / window.innerHeight) * 20,
        y: (deltaX / window.innerWidth) * 35,
      });
    };
    window.addEventListener('mousemove', handleMouseMove);
    return () => window.removeEventListener('mousemove', handleMouseMove);
  }, []);

  return (
    <section className="hero" id="hero">
      {/* Background Animated Blobs */}
      <div className="hero-blob hero-blob-1 animate-blob" />
      <div className="hero-blob hero-blob-2 animate-blob animation-delay-2000" />
      <div className="hero-blob hero-blob-3 animate-blob animation-delay-4000" />

      {/* Interactive Wall-E Style Bot */}
      <div className="hero-bot-container">
        <div
          ref={botRef}
          className="hero-bot"
          style={{
            transform: `perspective(1000px) rotateX(${-headRotation.x}deg) rotateY(${headRotation.y}deg)`,
          }}
        >
          <div className="hero-bot-visor">
            {/* Left Eye */}
            <div className="hero-bot-eye">
              <div
                className="hero-bot-pupil"
                style={{
                  transform: `translate(calc(-50% + ${eyeOffset.x}px), calc(-50% + ${eyeOffset.y}px))`,
                }}
              >
                <div className="hero-bot-pupil-inner" />
                <div className="hero-bot-pupil-highlight" />
              </div>
              <div className="hero-bot-eyelid" />
            </div>
            {/* Right Eye */}
            <div className="hero-bot-eye">
              <div
                className="hero-bot-pupil"
                style={{
                  transform: `translate(calc(-50% + ${eyeOffset.x}px), calc(-50% + ${eyeOffset.y}px))`,
                }}
              >
                <div className="hero-bot-pupil-inner" />
                <div className="hero-bot-pupil-highlight" />
              </div>
              <div className="hero-bot-eyelid" />
            </div>
          </div>
          <div className="hero-bot-neck">
            <div className="hero-bot-neck-line" style={{ marginTop: '1rem' }} />
            <div className="hero-bot-neck-line" style={{ marginTop: '0.5rem' }} />
          </div>
        </div>
      </div>

      <div className="hero-content">
        {/* Left Column: Text */}
        <div className="hero-text">
          <Reveal delay={100} direction="up">
            <div className="hero-badge">
              <span className="hero-badge-dot" />
              Powered by Gemini 2.5 Flash & Google ADK
            </div>
          </Reveal>

          <Reveal delay={200} direction="up">
            <h1 className="hero-title">
              Autonomous Security, <br />
              <span className="warm-gradient-text">Human in Control.</span>
            </h1>
          </Reveal>

          <Reveal delay={300} direction="up">
            <p className="hero-desc">
              The invisible, highly scalable team of security engineers that lives inside your GitLab.
              SecureFlow scans, hunts, and writes the code to fix vulnerabilities—pausing only for your final approval.
            </p>
          </Reveal>

          <Reveal delay={400} direction="up">
            <div className="hero-actions">
              <button className="hero-btn-primary" onClick={() => onNavigate && onNavigate('connect')}>
                Connect Repo <Plug style={{ width: 20, height: 20 }} />
              </button>
              <button className="hero-btn-secondary" onClick={() => onNavigate && onNavigate('documentation')}>
                Read Architecture <Server style={{ width: 20, height: 20, color: '#a8a29e' }} />
              </button>
            </div>
          </Reveal>
        </div>

        {/* Right Column: Floating Dashboard Mockup */}
        <div className="hero-mockup-wrapper">
          <Reveal delay={500} direction="left">
            <div className="glass-card hero-mockup">
              <div className="hero-mockup-topbar">
                <div className="hero-mockup-dots">
                  <span /><span /><span />
                </div>
                <div className="hero-mockup-label">secureflow-agent</div>
              </div>

              <div className="hero-mockup-body">
                <div className="mockup-line">
                  <span className="mockup-prompt">❯</span> Analyzing Merge Request !42...
                </div>
                <div className="mockup-line">
                  <span className="mockup-prompt">❯</span> Running parallel scanners...
                </div>
                <div className="mockup-indent">
                  <div className="mockup-success"><Check style={{ width: 16, height: 16, marginRight: 8 }} /> Pipeline: SLSA L3 OK</div>
                  <div className="mockup-success"><Check style={{ width: 16, height: 16, marginRight: 8 }} /> Secrets: Clear</div>
                  <div className="mockup-danger"><AlertTriangle style={{ width: 16, height: 16, marginRight: 8 }} /> Dependencies: 1 Vulnerability (CVE-2024-3422)</div>
                </div>
                <div className="mockup-action">
                  <Lock style={{ width: 16, height: 16, marginRight: 8 }} /> ACTION REQUIRED: Review Patch
                </div>
              </div>

              <div className="hero-agent-badge">
                <div className="hero-agent-badge-inner">
                  <div className="hero-agent-icon">
                    <Bot />
                  </div>
                  <div>
                    <p className="hero-agent-status-label">Agent Status</p>
                    <p className="hero-agent-status-value">Remediation Ready</p>
                  </div>
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
};

/* ============================================================
   Problem / Solution Section
   ============================================================ */
const ProblemSolution = () => {
  const cards = [
    {
      icon: <AlertTriangle style={{ width: 24, height: 24, color: '#f43f5e' }} />,
      title: "Alert Fatigue",
      desc: "Traditional tools spam developers with noisy false positives. SecureFlow only alerts when it has context-aware, verified findings.",
    },
    {
      icon: <Code style={{ width: 24, height: 24, color: '#f59e0b' }} />,
      title: "The Shift-Left Paradox",
      desc: "Expecting developers to be security experts slows them down. SecureFlow brings the expertise directly into the code review.",
    },
    {
      icon: <FileWarning style={{ width: 24, height: 24, color: '#ea580c' }} />,
      title: "Phantom Packages",
      desc: "Hackers publish malicious packages with similar names. Our agents detect typosquatting before the code is ever run.",
    },
    {
      icon: <GitMerge style={{ width: 24, height: 24, color: '#10b981' }} />,
      title: "Manual Remediation",
      desc: "Finding bugs is easy; fixing them takes time. SecureFlow autonomously writes the patch and waits for your final approval.",
    },
  ];

  return (
    <section className="problem-section" id="problems">
      <div className="problem-section-inner">
        <Reveal direction="up" delay={100}>
          <div className="problem-header">
            <h2 className="problem-label">The Problem Solved</h2>
            <h3 className="problem-title">Development velocity is outpacing security capacity.</h3>
            <p className="problem-desc">
              Traditional SAST and SCA tools are noisy and require manual fixes. SecureFlow transitions
              your pipeline from <em>Static Detection</em> to <em>Autonomous Remediation</em>.
            </p>
          </div>
        </Reveal>

        <div className="problem-grid">
          {cards.map((card, idx) => (
            <Reveal key={idx} direction="up" delay={idx * 150 + 200}>
              <div className="problem-card">
                <div className="problem-card-icon">{card.icon}</div>
                <h4 className="problem-card-title">{card.title}</h4>
                <p className="problem-card-desc">{card.desc}</p>
              </div>
            </Reveal>
          ))}
        </div>
      </div>
    </section>
  );
};

/* ============================================================
   Custom Animated SVG Icons
   ============================================================ */
const OrchestratorIcon = () => (
  <svg viewBox="0 0 100 100" className="arch-svg-icon-lg" style={{ transition: 'transform 700ms cubic-bezier(0.34, 1.56, 0.64, 1)' }}>
    <defs>
      <linearGradient id="coreGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#fb923c" />
        <stop offset="100%" stopColor="#ea580c" />
      </linearGradient>
    </defs>
    <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(251,146,60,0.2)" strokeWidth="1" />
    <circle cx="50" cy="50" r="40" fill="none" stroke="#fb923c" strokeWidth="2" strokeDasharray="30 10 10 10" className="animate-spin-slow" />
    <circle cx="50" cy="50" r="28" fill="none" stroke="rgba(244,63,94,0.2)" strokeWidth="1" />
    <circle cx="50" cy="50" r="28" fill="none" stroke="#f43f5e" strokeWidth="3" strokeDasharray="15 20 40 10" className="animate-spin-reverse-slow" />
    <circle cx="50" cy="50" r="14" fill="url(#coreGrad)" className="animate-pulse" style={{ filter: 'drop-shadow(0 0 10px rgba(234,88,12,0.8))' }} />
    <circle cx="50" cy="50" r="4" fill="#fff" />
  </svg>
);

const DependencyIcon = () => (
  <svg viewBox="0 0 100 100" className="arch-svg-icon" style={{ position: 'relative', zIndex: 10 }}>
    <path d="M50 15 L80 30 L80 65 L50 80 L20 65 L20 30 Z" fill="none" stroke="#3b82f6" strokeWidth="2" className="animate-draw-path" />
    <path d="M50 15 L50 50 M20 30 L50 50 M80 30 L50 50 M20 65 L50 50 M80 65 L50 50 M50 80 L50 50" fill="none" stroke="rgba(59,130,246,0.3)" strokeWidth="1" />
    <circle cx="50" cy="50" className="animate-node-pulse" style={{ animationDelay: '0s' }} />
    <circle cx="20" cy="30" r="3" fill="#60a5fa" />
    <circle cx="80" cy="30" r="3" fill="#60a5fa" />
    <circle cx="20" cy="65" r="3" fill="#60a5fa" />
    <circle cx="80" cy="65" r="3" fill="#60a5fa" />
  </svg>
);

const SecretIcon = () => (
  <svg viewBox="0 0 100 100" className="arch-svg-icon" style={{ position: 'relative', zIndex: 10 }}>
    <path d="M50 10 L85 30 L85 70 L50 90 L15 70 L15 30 Z" fill="rgba(244,63,94,0.1)" stroke="#f43f5e" strokeWidth="1" strokeDasharray="5 5" className="animate-spin-slow" />
    <path d="M25 50 Q50 20 75 50 Q50 80 25 50 Z" fill="none" stroke="#fb7185" strokeWidth="2" className="animate-draw-path stagger-1" />
    <circle cx="50" cy="50" r="10" fill="none" stroke="#fda4af" strokeWidth="2" />
    <circle cx="50" cy="50" r="4" fill="#e11d48" className="animate-pulse" style={{ filter: 'drop-shadow(0 0 5px #e11d48)' }} />
    <line x1="15" y1="50" x2="85" y2="50" stroke="#fff" strokeWidth="1" opacity="0.5" />
  </svg>
);

const PipelineIcon = () => (
  <svg viewBox="0 0 100 100" className="arch-svg-icon" style={{ position: 'relative', zIndex: 10, transition: 'transform 500ms cubic-bezier(0.34, 1.56, 0.64, 1)' }}>
    <path d="M10 75 L50 95 L90 75 L50 55 Z" fill="rgba(16,185,129,0.1)" stroke="#10b981" strokeWidth="2" className="animate-draw-path stagger-2" />
    <path d="M10 50 L50 70 L90 50 L50 30 Z" fill="rgba(52,211,153,0.1)" stroke="#34d399" strokeWidth="2" className="animate-draw-path stagger-1" />
    <path d="M10 25 L50 45 L90 25 L50 5 Z" fill="rgba(110,231,183,0.2)" stroke="#6ee7b7" strokeWidth="2" className="animate-draw-path" />
    <circle cx="50" cy="25" r="2" fill="#fff" className="animate-pulse-ring" />
    <line x1="50" y1="45" x2="50" y2="70" stroke="#10b981" strokeWidth="2" strokeDasharray="4 4" className="animate-data-flow" />
  </svg>
);

const ThreatIcon = () => (
  <svg viewBox="0 0 100 100" className="arch-svg-icon" style={{ position: 'relative', zIndex: 10 }}>
    <circle cx="50" cy="50" r="40" fill="none" stroke="rgba(251,191,36,0.3)" strokeWidth="1" />
    <circle cx="50" cy="50" r="25" fill="none" stroke="rgba(251,191,36,0.5)" strokeWidth="1" />
    <circle cx="50" cy="50" r="10" fill="none" stroke="#fbbf24" strokeWidth="2" />
    <path d="M50 50 L50 10 A40 40 0 0 1 90 50 Z" fill="url(#radarSweep)" className="animate-spin-slow" />
    <defs>
      <linearGradient id="radarSweep" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="rgba(251,191,36,0.8)" />
        <stop offset="100%" stopColor="rgba(251,191,36,0)" />
      </linearGradient>
    </defs>
    <circle cx="70" cy="30" className="animate-node-pulse" style={{ animationDelay: '1s' }} />
    <circle cx="30" cy="60" className="animate-node-pulse" style={{ animationDelay: '2.5s' }} />
  </svg>
);

const RemediationIcon = () => (
  <svg viewBox="0 0 100 100" className="arch-svg-icon-lg" style={{ transition: 'transform 1000ms cubic-bezier(0.34, 1.56, 0.64, 1)' }}>
    <defs>
      <linearGradient id="remGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#f97316" />
        <stop offset="100%" stopColor="#f43f5e" />
      </linearGradient>
    </defs>
    <path d="M50 10 L60 30 L50 40 L40 30 Z" fill="url(#remGrad)" className="animate-draw-path" />
    <path d="M50 90 L60 70 L50 60 L40 70 Z" fill="url(#remGrad)" className="animate-draw-path stagger-1" />
    <path d="M10 50 L30 40 L40 50 L30 60 Z" fill="url(#remGrad)" className="animate-draw-path stagger-2" />
    <path d="M90 50 L70 40 L60 50 L70 60 Z" fill="url(#remGrad)" className="animate-draw-path stagger-3" />
    <circle cx="50" cy="50" r="12" fill="none" stroke="#fff" strokeWidth="2" strokeDasharray="10 5" className="animate-spin-reverse-slow" />
    <circle cx="50" cy="50" r="6" fill="#fcd34d" style={{ filter: 'drop-shadow(0 0 15px #fcd34d)' }} className="animate-pulse" />
  </svg>
);

/* ============================================================
   Architecture Section
   ============================================================ */
const Architecture = () => {
  return (
    <section id="agents" className="arch-section animate-pan-bg">
      <div className="arch-radial-bg" />

      <div className="arch-inner">
        <Reveal direction="up" delay={100}>
          <div className="arch-header">
            <h2 className="arch-label">Multi-Agent Graph</h2>
            <h3 className="arch-title">
              A team of <span className="arch-title-gradient">specialized AI agents.</span>
            </h3>
            <p className="arch-desc">
              Powered by Google ADK and Gemini 2.5 Flash, SecureFlow orchestrates four specialized scanner agents running in parallel, governed by a master orchestrator.
            </p>
          </div>
        </Reveal>

        <div className="arch-flow">
          {/* Orchestrator */}
          <Reveal direction="down" delay={200}>
            <div className="arch-orchestrator spring-hover">
              <OrchestratorIcon />
              <h4 className="arch-orch-title">Orchestrator Agent</h4>
              <p className="arch-orch-desc">Receives GitLab Webhook. Analyzes intent and delegates tasks to parallel scanners.</p>
            </div>
          </Reveal>

          {/* Data Bus Top */}
          <div className="arch-data-bus">
            <svg preserveAspectRatio="none">
              <line x1="50%" y1="0" x2="50%" y2="50%" stroke="rgba(249,115,22,0.3)" strokeWidth="2" />
              <line x1="50%" y1="0" x2="50%" y2="50%" stroke="#fb923c" strokeWidth="2" className="animate-data-flow" />
              <line x1="12.5%" y1="50%" x2="87.5%" y2="50%" stroke="rgba(249,115,22,0.3)" strokeWidth="2" />
              <line x1="12.5%" y1="50%" x2="87.5%" y2="50%" stroke="#fb923c" strokeWidth="2" className="animate-data-flow" />
              <line x1="12.5%" y1="50%" x2="12.5%" y2="100%" stroke="rgba(59,130,246,0.3)" strokeWidth="2" />
              <line x1="12.5%" y1="50%" x2="12.5%" y2="100%" stroke="#3b82f6" strokeWidth="2" className="animate-data-flow" />
              <line x1="37.5%" y1="50%" x2="37.5%" y2="100%" stroke="rgba(244,63,94,0.3)" strokeWidth="2" />
              <line x1="37.5%" y1="50%" x2="37.5%" y2="100%" stroke="#f43f5e" strokeWidth="2" className="animate-data-flow" />
              <line x1="62.5%" y1="50%" x2="62.5%" y2="100%" stroke="rgba(16,185,129,0.3)" strokeWidth="2" />
              <line x1="62.5%" y1="50%" x2="62.5%" y2="100%" stroke="#10b981" strokeWidth="2" className="animate-data-flow" />
              <line x1="87.5%" y1="50%" x2="87.5%" y2="100%" stroke="rgba(245,158,11,0.3)" strokeWidth="2" />
              <line x1="87.5%" y1="50%" x2="87.5%" y2="100%" stroke="#f59e0b" strokeWidth="2" className="animate-data-flow" />
            </svg>
          </div>

          {/* Parallel Scanners */}
          <div className="arch-scanners">
            <Reveal direction="up" delay={300}>
              <div className="arch-scanner-card blue spring-hover">
                <div className="arch-scanner-overlay blue" />
                <DependencyIcon />
                <h4 className="arch-scanner-title">Dependency Scanner</h4>
                <p className="arch-scanner-desc">OSV API & Phantom Package Detection.</p>
              </div>
            </Reveal>

            <Reveal direction="up" delay={400}>
              <div className="arch-scanner-card rose spring-hover">
                <div className="arch-scanner-overlay rose" />
                <SecretIcon />
                <h4 className="arch-scanner-title">Secret Hunter</h4>
                <p className="arch-scanner-desc">Context-aware credential and token detection.</p>
              </div>
            </Reveal>

            <Reveal direction="up" delay={500}>
              <div className="arch-scanner-card emerald spring-hover">
                <div className="arch-scanner-overlay emerald" />
                <PipelineIcon />
                <h4 className="arch-scanner-title">Pipeline Auditor</h4>
                <p className="arch-scanner-desc">SLSA Compliance & CI/CD anti-patterns.</p>
              </div>
            </Reveal>

            <Reveal direction="up" delay={600}>
              <div className="arch-scanner-card amber spring-hover">
                <div className="arch-scanner-overlay amber" />
                <ThreatIcon />
                <h4 className="arch-scanner-title">Threat Intel Agent</h4>
                <p className="arch-scanner-desc">NVD API enrichment (CVSS scores).</p>
              </div>
            </Reveal>
          </div>

          {/* Data Bus Bottom */}
          <div className="arch-data-bus">
            <svg preserveAspectRatio="none">
              <line x1="12.5%" y1="0" x2="12.5%" y2="50%" stroke="rgba(59,130,246,0.3)" strokeWidth="2" />
              <line x1="12.5%" y1="0" x2="12.5%" y2="50%" stroke="#3b82f6" strokeWidth="2" className="animate-data-flow" />
              <line x1="37.5%" y1="0" x2="37.5%" y2="50%" stroke="rgba(244,63,94,0.3)" strokeWidth="2" />
              <line x1="37.5%" y1="0" x2="37.5%" y2="50%" stroke="#f43f5e" strokeWidth="2" className="animate-data-flow" />
              <line x1="62.5%" y1="0" x2="62.5%" y2="50%" stroke="rgba(16,185,129,0.3)" strokeWidth="2" />
              <line x1="62.5%" y1="0" x2="62.5%" y2="50%" stroke="#10b981" strokeWidth="2" className="animate-data-flow" />
              <line x1="87.5%" y1="0" x2="87.5%" y2="50%" stroke="rgba(245,158,11,0.3)" strokeWidth="2" />
              <line x1="87.5%" y1="0" x2="87.5%" y2="50%" stroke="#f59e0b" strokeWidth="2" className="animate-data-flow" />

              <line x1="12.5%" y1="50%" x2="87.5%" y2="50%" stroke="rgba(249,115,22,0.3)" strokeWidth="2" />
              <line x1="12.5%" y1="50%" x2="50%" y2="50%" stroke="#fb923c" strokeWidth="2" className="animate-data-flow" />
              <line x1="87.5%" y1="50%" x2="50%" y2="50%" stroke="#fb923c" strokeWidth="2" className="animate-data-flow" />

              <line x1="50%" y1="50%" x2="50%" y2="100%" stroke="rgba(249,115,22,0.3)" strokeWidth="2" />
              <line x1="50%" y1="50%" x2="50%" y2="100%" stroke="#fb923c" strokeWidth="2" className="animate-data-flow" />
            </svg>
          </div>

          {/* Remediation Agent */}
          <Reveal direction="up" delay={800}>
            <div className="arch-remediation spring-hover">
              <div className="arch-remediation-overlay" />
              <div className="arch-remediation-bar" />
              <div className="arch-remediation-content">
                <RemediationIcon />
                <h4 className="arch-rem-title">Remediation Agent</h4>
                <p className="arch-rem-desc">Gathers all findings, generates the correct patch, and autonomously proposes GitLab actions.</p>
                <div className="arch-rem-badge">
                  <Lock /> Blocked by HITL Callback until approved
                </div>
              </div>
            </div>
          </Reveal>
        </div>
      </div>
    </section>
  );
};

/* ============================================================
   HITL Section
   ============================================================ */
const HITLSection = () => {
  return (
    <section id="hitl" className="hitl-section">
      <div className="hitl-inner">
        <div className="hitl-grid">
          <div className="hitl-text">
            <Reveal direction="right" delay={100}>
              <div className="hitl-icon-wrap">
                <Eye />
              </div>
              <h2 className="hitl-title">
                Never blindly modify production. <br />
                <span className="hitl-title-accent">The HITL Safety Net.</span>
              </h2>
              <p className="hitl-desc">
                We know you can't hand over write-access to an AI without oversight.
                That's why SecureFlow relies on a strict <strong>Human-In-The-Loop (HITL)</strong> policy.
              </p>
              <ul className="hitl-list">
                {[
                  "ADK before_tool_callback intercepts all write actions.",
                  "Actions are queued in BigQuery with PENDING status.",
                  "Review the AI's reasoning on the React Dashboard.",
                  "One click to Approve and trigger the GitLab MCP commit.",
                ].map((item, i) => (
                  <li key={i}>
                    <Check />
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
              <button className="hitl-explore-btn">
                Explore the Dashboard Architecture <ArrowRight />
              </button>
            </Reveal>
          </div>

          <div className="hitl-card-wrapper">
            <Reveal direction="left" delay={300}>
              <div className="hitl-card">
                <div className="hitl-pulse-ring animate-pulse-ring" />
                <div className="hitl-shield-icon">
                  <Shield />
                </div>
                <h3 className="hitl-card-title">Pending Approval</h3>
                <div className="hitl-code-preview">
                  <div className="hitl-code-header">
                    <div>
                      <p className="hitl-code-title">Bump requests to 2.31.0</p>
                      <p className="hitl-code-file">requirements.txt</p>
                    </div>
                    <span className="hitl-severity-badge">Critical</span>
                  </div>
                  <div className="hitl-diff">
                    <div className="hitl-diff-remove">- requests==2.28.1</div>
                    <div className="hitl-diff-add">+ requests==2.31.0</div>
                  </div>
                </div>
                <div className="hitl-card-actions">
                  <button className="hitl-btn-reject">Reject</button>
                  <button className="hitl-btn-approve">Approve Fix</button>
                </div>
              </div>
            </Reveal>
          </div>
        </div>
      </div>
    </section>
  );
};

/* ============================================================
   Footer
   ============================================================ */
const Footer = () => (
  <footer className="landing-footer">
    <div className="landing-footer-inner">
      <p>Built for the Google Cloud + GitLab Hackathon 2026. Powered by Gemini 2.5 Flash.</p>
    </div>
  </footer>
);

/* ============================================================
   Landing Page — Main Export
   ============================================================ */
const LandingPage = ({ onNavigate }) => {
  return (
    <div className="landing-root">
      <CustomCursor />
      <Navbar onNavigate={onNavigate} />
      <Hero onNavigate={onNavigate} />
      <ProblemSolution />
      <Architecture />
      <HITLSection />
      <Footer />
    </div>
  );
};

export default LandingPage;
