import React, { useState, useEffect } from 'react';
import FindingsTable from './components/FindingsTable';
import ApprovalCard from './components/ApprovalCard';
import RepoPosture from './components/RepoPosture';
import ComplianceReport from './components/ComplianceReport';
import { getFindings, getPendingApprovals, getFindingsSummary } from './api/client';
import './index.css';

function App() {
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

  return (
    <div>
      {/* ---- Header ---- */}
      <header className="app-header flex-between">
        <div className="flex-center" style={{ gap: '0.75rem' }}>
          <div className="logo-icon">
            <svg viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path d="M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z"/>
            </svg>
          </div>
          <h1 className="logo-text">SecureFlow</h1>
        </div>

        <div className="flex-center" style={{ gap: '1rem' }}>
          {lastUpdated && (
            <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              Updated {lastUpdated.toLocaleTimeString()}
            </span>
          )}
          <div className="status-pill">
            <div className="status-dot"></div>
            Agent Active
          </div>
        </div>
      </header>

      {/* ---- Main Content ---- */}
      <main className="container">

        {/* Stats Bar */}
        <div className="stats-bar">
          <div className="stat-card">
            <div className="stat-label">Total Findings</div>
            <div className="stat-value info">{summary.total || findings.length}</div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Critical</div>
            <div className="stat-value critical">
              {summary.critical || findings.filter(f => f.severity === 'CRITICAL').length}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">High</div>
            <div className="stat-value warning">
              {summary.high || findings.filter(f => f.severity === 'HIGH').length}
            </div>
          </div>
          <div className="stat-card">
            <div className="stat-label">Pending Approvals</div>
            <div className="stat-value" style={{ color: approvals.length > 0 ? 'var(--purple)' : 'var(--success)' }}>
              {approvals.length}
            </div>
          </div>
        </div>

        {/* HITL Approvals */}
        {approvals.length > 0 && (
          <section style={{ marginBottom: '2rem' }}>
            <h2 className="section-title">
              <span className="accent-bar" style={{ background: 'var(--purple)' }}></span>
              Human-in-the-Loop Approvals
              <span className="badge" style={{ background: 'var(--purple)', color: 'white', marginLeft: 'auto' }}>
                {approvals.length} pending
              </span>
            </h2>
            {approvals.map(a => (
              <ApprovalCard key={a.id} approval={a} onProcessed={loadData} />
            ))}
          </section>
        )}

        {/* Findings Table */}
        <section style={{ marginBottom: '2rem' }}>
          <h2 className="section-title">
            <span className="accent-bar" style={{ background: 'var(--primary)' }}></span>
            Security Findings
            {findings.length > 0 && (
              <span className="badge info" style={{ marginLeft: 'auto' }}>{findings.length} total</span>
            )}
          </h2>
          <FindingsTable findings={findings} loading={loading} />
        </section>

        {/* Bottom Grid */}
        <div className="bottom-grid">
          <RepoPosture findings={findings} />
          <ComplianceReport />
        </div>
      </main>
    </div>
  );
}

export default App;
