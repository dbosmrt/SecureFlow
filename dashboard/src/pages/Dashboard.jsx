import React, { useState, useEffect, useMemo } from 'react';
import {
  Shield, Check, ArrowRight, Activity, Zap, Lock, Eye, AlertTriangle,
  Code, FileWarning, Search, GitMerge, FileCheck, Download, Clock,
  Terminal, ShieldCheck, ChevronRight, Bot, ArrowLeft, Plug
} from 'lucide-react';
import {
  AreaChart, Area, Tooltip, ResponsiveContainer
} from 'recharts';
import { getFindings, getPendingApprovals, getFindingsSummary, processApproval } from '../api/client';
import './Dashboard.css';

/* ============================================================
   Custom Cursor
   ============================================================ */
const DashCursor = () => {
  const [pos, setPos] = useState({ x: -100, y: -100 });
  const [isHovering, setIsHovering] = useState(false);

  useEffect(() => {
    const moveCursor = (e) => setPos({ x: e.clientX, y: e.clientY });
    const handleMouseOver = (e) => {
      if (e.target.closest('button, a, input, tr, [role="button"]')) setIsHovering(true);
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
      <linearGradient id="logoGradDash" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#fb923c" />
        <stop offset="100%" stopColor="#ea580c" />
      </linearGradient>
    </defs>
    <path
      d="M50 15 Q 85 30 85 65 Q 85 90 50 85 Q 15 90 15 65 Q 15 30 50 15 M50 15 Q 15 30 15 65 Q 15 80 50 75 Q 85 80 85 65 Q 85 30 50 15 Z"
      fill="none" stroke="url(#logoGradDash)" strokeWidth="6"
    />
    <circle cx="50" cy="50" r="8" fill="#f97316" />
  </svg>
);

/* ============================================================
   Top Navigation
   ============================================================ */
const TopNav = ({ onNavigate, lastUpdated }) => (
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
        <GitMerge /> gitlab.com/acme-corp/core-api
      </span>
    </div>

    <div className="dash-nav-right">
      <button
        className="dash-compliance-btn"
        style={{ padding: '0.375rem 0.875rem', borderRadius: '9999px', fontWeight: 700, fontSize: '0.8rem' }}
        onClick={() => onNavigate && onNavigate('connect')}
      >
        <Plug style={{ width: 14, height: 14 }} /> Connect Repo
      </button>

      <div className="dash-nav-updated">
        <Clock />
        {lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : 'Updated just now'}
      </div>

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
   Severity Badge
   ============================================================ */
const SeverityBadge = ({ level }) => {
  const cls = {
    CRITICAL: 'critical',
    HIGH: 'high',
    MEDIUM: 'medium',
    LOW: 'low',
  }[level] || 'low';

  return <span className={`severity-badge ${cls}`}>{level}</span>;
};

/* ============================================================
   Stat Card
   ============================================================ */
const StatCard = ({ icon: Icon, label, value, trend, trendUp, colorClass }) => (
  <div className="glass-panel dash-stat-card spring-hover">
    <div className="dash-stat-top">
      <div className={`dash-stat-icon ${colorClass}`}>
        <Icon />
      </div>
      {trend && (
        <span className={`dash-stat-trend ${trendUp ? 'up' : 'down'}`}>
          {trendUp ? '↑' : '↓'} {trend}
        </span>
      )}
    </div>
    <div>
      <h4 className="dash-stat-label">{label}</h4>
      <h2 className="dash-stat-value">{value}</h2>
    </div>
  </div>
);

/* ============================================================
   HITL Approval Queue
   ============================================================ */
const HITLApprovalQueue = ({ approvals, onProcessed }) => {
  const [processing, setProcessing] = useState({});

  const handleAction = async (id, action) => {
    setProcessing(prev => ({ ...prev, [id]: true }));
    try {
      await processApproval(id, action);
      onProcessed();
    } catch (err) {
      console.error('Approval action failed:', err);
    } finally {
      setProcessing(prev => ({ ...prev, [id]: false }));
    }
  };

  if (!approvals || approvals.length === 0) return null;

  return (
    <div style={{ marginBottom: '2rem' }}>
      <div className="dash-hitl-header">
        <h3 className="dash-hitl-title">
          <Lock /> Action Required: HITL Queue
        </h3>
        <span className="dash-hitl-badge">{approvals.length} Pending</span>
      </div>

      <div className="dash-hitl-grid">
        {approvals.map((approval) => {
          const payloadStr = typeof approval.action_payload === 'string'
            ? approval.action_payload
            : JSON.stringify(approval.action_payload, null, 2);

          // Try to parse diff lines from payload
          let diffLines = [];
          try {
            const payload = typeof approval.action_payload === 'string'
              ? JSON.parse(approval.action_payload)
              : approval.action_payload;
            if (payload && typeof payload === 'object') {
              // Try to extract meaningful diff info
              Object.entries(payload).forEach(([key, value]) => {
                if (typeof value === 'string' && value.includes('==')) {
                  diffLines.push({ type: 'remove', line: `- ${key}: ${value}` });
                  diffLines.push({ type: 'add', line: `+ ${key}: (patched version)` });
                }
              });
            }
          } catch {
            // Fallback: show raw payload as single block
          }

          return (
            <div key={approval.id} className="glass-panel dash-hitl-card">
              <div className="dash-hitl-card-body">
                <div className="dash-hitl-card-top">
                  <div>
                    <div className="dash-hitl-card-meta">
                      <SeverityBadge level="CRITICAL" />
                      <span className="dash-hitl-card-id">{approval.id?.slice(0, 12)}</span>
                    </div>
                    <h4 className="dash-hitl-card-title">
                      {approval.action_type || 'Pending Action'}
                    </h4>
                    <p className="dash-hitl-card-file">
                      <FileWarning /> {approval.finding_id?.slice(0, 8) || 'unknown'}
                    </p>
                  </div>
                </div>

                {/* AI Reasoning Block */}
                <div className="dash-reasoning">
                  <div className="dash-reasoning-header">
                    <Bot />
                    <span className="dash-reasoning-label">Agent Reasoning</span>
                  </div>
                  <p className="dash-reasoning-text">
                    "The agent has analyzed this finding and proposes the following remediation action. Please review carefully before approving."
                  </p>
                </div>

                {/* Code Diff Block */}
                <div className="dash-diff code-scroll">
                  <div className="dash-diff-header">
                    <span>Proposed Patch</span>
                    <Code />
                  </div>
                  <div className="dash-diff-body">
                    {diffLines.length > 0 ? (
                      diffLines.map((line, idx) => (
                        <div key={idx} className={`dash-diff-line ${line.type === 'remove' ? 'diff-remove' : 'diff-add'}`}>
                          {line.line}
                        </div>
                      ))
                    ) : (
                      <div style={{ color: '#a8a29e' }}>
                        <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{payloadStr}</pre>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              <div className="dash-hitl-actions">
                <button
                  className="dash-btn-reject"
                  onClick={() => handleAction(approval.id, 'REJECT')}
                  disabled={processing[approval.id]}
                >
                  {processing[approval.id] ? '...' : 'Reject Patch'}
                </button>
                <button
                  className="dash-btn-approve"
                  onClick={() => handleAction(approval.id, 'APPROVE')}
                  disabled={processing[approval.id]}
                >
                  <Check /> {processing[approval.id] ? '...' : 'Approve & Commit'}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

/* ============================================================
   Findings Table
   ============================================================ */
const DashFindingsTable = ({ findings, loading }) => {
  const statusIcon = (status) => {
    const s = status?.toLowerCase();
    if (s === 'fixed' || s === 'remediated') return <Check />;
    if (s === 'pending' || s === 'pending approval') return <Lock />;
    return <Eye />;
  };

  const statusClass = (status) => {
    const s = status?.toLowerCase();
    if (s === 'fixed' || s === 'remediated') return 'remediated';
    if (s === 'pending' || s === 'pending approval') return 'pending';
    return 'open';
  };

  return (
    <div className="glass-panel dash-findings">
      <div className="dash-findings-header">
        <h3 className="dash-findings-title">
          <Search /> Active Security Findings
        </h3>
        <button className="dash-findings-viewall">
          View All <ChevronRight />
        </button>
      </div>
      <div style={{ overflowX: 'auto' }}>
        <table className="dash-findings-table">
          <thead>
            <tr>
              <th>Severity</th>
              <th>Finding / Details</th>
              <th>Origin File</th>
              <th>Agent Status</th>
            </tr>
          </thead>
          <tbody>
            {loading && (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '3rem', color: '#78716c' }}>
                  ⏳ Loading findings...
                </td>
              </tr>
            )}
            {!loading && findings.length === 0 && (
              <tr>
                <td colSpan="4" style={{ textAlign: 'center', padding: '3rem', color: '#78716c' }}>
                  🛡️ No security findings detected. Your code is secure!
                </td>
              </tr>
            )}
            {findings.map((finding) => (
              <tr key={finding.id}>
                <td><SeverityBadge level={finding.severity} /></td>
                <td>
                  <div className="dash-finding-name">{finding.title || finding.finding}</div>
                  <div className="dash-finding-detail">{finding.description || finding.details}</div>
                </td>
                <td className="dash-finding-file">
                  {finding.file_path || finding.file || '—'}
                  {finding.line_number ? `:${finding.line_number}` : ''}
                </td>
                <td>
                  <span className={`finding-status ${statusClass(finding.status)}`}>
                    {statusIcon(finding.status)}
                    {finding.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

/* ============================================================
   Security Posture (Area Chart)
   ============================================================ */
const SecurityPosture = ({ findings }) => {
  const currentScore = useMemo(() => {
    if (!findings || findings.length === 0) return 100;
    const penalties = { CRITICAL: 15, HIGH: 8, MEDIUM: 4, LOW: 1, INFO: 0 };
    const totalPenalty = findings.reduce((sum, f) => sum + (penalties[f.severity] || 0), 0);
    return Math.max(0, Math.min(100, 100 - totalPenalty));
  }, [findings]);

  const postureData = [
    { day: 'Mon', score: 82 }, { day: 'Tue', score: 85 }, { day: 'Wed', score: 78 },
    { day: 'Thu', score: 88 }, { day: 'Fri', score: 91 }, { day: 'Sat', score: 94 },
    { day: 'Today', score: currentScore }
  ];

  const getLabel = (score) => {
    if (score >= 90) return 'Excellent';
    if (score >= 70) return 'Good';
    if (score >= 50) return 'Fair';
    return 'Critical';
  };

  return (
    <div className="glass-panel dash-posture">
      <div className="dash-posture-header">
        <div>
          <h3 className="dash-posture-title"><Activity /> Security Posture</h3>
          <p className="dash-posture-subtitle">Repository health score over 7 days</p>
        </div>
        <div className="dash-posture-score">
          <span className="dash-posture-score-value">{currentScore}</span>
          <span className="dash-posture-score-max">/100</span>
          <div className="dash-posture-score-label">{getLabel(currentScore)}</div>
        </div>
      </div>

      <div className="dash-posture-chart">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart data={postureData} margin={{ top: 5, right: 0, left: 0, bottom: 0 }}>
            <defs>
              <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
              </linearGradient>
            </defs>
            <Tooltip
              contentStyle={{ backgroundColor: 'rgba(255,255,255,0.9)', borderRadius: '8px', border: 'none', boxShadow: '0 4px 6px -1px rgba(0,0,0,0.1)' }}
              itemStyle={{ color: '#10b981', fontWeight: 'bold' }}
            />
            <Area type="monotone" dataKey="score" stroke="#10b981" strokeWidth={3} fillOpacity={1} fill="url(#colorScore)" />
          </AreaChart>
        </ResponsiveContainer>
      </div>

      <div className="dash-posture-days">
        {postureData.map(d => <span key={d.day}>{d.day}</span>)}
      </div>
    </div>
  );
};

/* ============================================================
   Compliance Status
   ============================================================ */
const ComplianceStatus = () => (
  <div className="glass-panel dash-compliance">
    <div>
      <h3 className="dash-compliance-title">
        <ShieldCheck /> Compliance Status
      </h3>

      <div className="dash-compliance-grid">
        <div className="dash-compliance-item">
          <p className="dash-compliance-label">SLSA Level</p>
          <p className="dash-compliance-value indigo">Level 3</p>
        </div>
        <div className="dash-compliance-item">
          <p className="dash-compliance-label">SBOM Format</p>
          <p className="dash-compliance-value dark">CycloneDX 1.5</p>
        </div>
      </div>
    </div>

    <div className="dash-compliance-actions">
      <button className="dash-compliance-btn">
        <Download /> Get SBOM
      </button>
      <button className="dash-compliance-btn">
        <Terminal /> Audit Log
      </button>
    </div>
  </div>
);

/* ============================================================
   Dashboard Page — Main Export
   ============================================================ */
const DashboardPage = ({ onNavigate }) => {
  const [findings, setFindings] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [summary, setSummary] = useState({ critical: 0, high: 0, medium: 0, low: 0, total: 0 });
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadData = async () => {
    try {
      const [findingsRes, approvalsRes, summaryRes] = await Promise.allSettled([
        getFindings(),
        getPendingApprovals(),
        getFindingsSummary(),
      ]);

      if (findingsRes.status === 'fulfilled') {
        setFindings(findingsRes.value.findings || []);
      }
      if (approvalsRes.status === 'fulfilled') {
        setApprovals(approvalsRes.value.pending || []);
      }
      if (summaryRes.status === 'fulfilled') {
        setSummary(summaryRes.value);
      }

      setLastUpdated(new Date());
    } catch (e) {
      console.error('Failed to load data:', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    const interval = setInterval(loadData, 8000);
    return () => clearInterval(interval);
  }, []);

  const totalFindings = summary.total || findings.length;
  const criticalCount = summary.critical || findings.filter(f => f.severity === 'CRITICAL').length;
  const remediatedCount = findings.filter(f => f.status?.toLowerCase() === 'fixed' || f.status?.toLowerCase() === 'remediated').length;

  return (
    <div className="dashboard-root">
      <DashCursor />
      <TopNav onNavigate={onNavigate} lastUpdated={lastUpdated} />

      <main className="dash-main">
        {/* KPI Row */}
        <div className="dash-stats-grid">
          <StatCard
            icon={AlertTriangle}
            label="Total Findings"
            value={totalFindings}
            trend={criticalCount > 0 ? `${criticalCount}` : null}
            trendUp={false}
            colorClass="rose"
          />
          <StatCard
            icon={Shield}
            label="Remediated"
            value={remediatedCount}
            trend={remediatedCount > 0 ? '✓' : null}
            trendUp={true}
            colorClass="emerald"
          />
          <StatCard
            icon={Zap}
            label="Parallel Scans"
            value="1,024"
            colorClass="blue"
          />
          <StatCard
            icon={FileCheck}
            label="SLSA Score"
            value="L3"
            colorClass="indigo"
          />
        </div>

        {/* HITL Queue */}
        <HITLApprovalQueue approvals={approvals} onProcessed={loadData} />

        {/* Bottom Grid: Findings + Posture/Compliance */}
        <div className="dash-bottom-grid">
          <DashFindingsTable findings={findings} loading={loading} />
          <div className="dash-bottom-sidebar">
            <SecurityPosture findings={findings} />
            <ComplianceStatus />
          </div>
        </div>
      </main>
    </div>
  );
};

export default DashboardPage;
