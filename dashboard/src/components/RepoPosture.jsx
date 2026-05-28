import React, { useMemo } from 'react';

/**
 * RepoPosture — Security score visualization
 * Shows a bar chart of security posture over the last 7 days,
 * calculated from findings data.
 */
const RepoPosture = ({ findings = [] }) => {
  // Calculate a simple security score: 100 - (weighted findings penalty)
  const currentScore = useMemo(() => {
    if (findings.length === 0) return 100;
    const penalties = { CRITICAL: 15, HIGH: 8, MEDIUM: 4, LOW: 1, INFO: 0 };
    const totalPenalty = findings.reduce((sum, f) => sum + (penalties[f.severity] || 0), 0);
    return Math.max(0, Math.min(100, 100 - totalPenalty));
  }, [findings]);

  // Simulated historical data (in production, this comes from the API)
  const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Today'];
  const scores = [82, 85, 78, 88, 91, 94, currentScore];

  const getBarColor = (score) => {
    if (score >= 90) return 'var(--success)';
    if (score >= 70) return 'var(--primary)';
    if (score >= 50) return 'var(--warning)';
    return 'var(--danger)';
  };

  const getScoreLabel = (score) => {
    if (score >= 90) return { text: 'Excellent', color: 'var(--success)' };
    if (score >= 70) return { text: 'Good', color: 'var(--primary)' };
    if (score >= 50) return { text: 'Fair', color: 'var(--warning)' };
    return { text: 'Critical', color: 'var(--danger)' };
  };

  const label = getScoreLabel(currentScore);

  return (
    <div className="card">
      <h3 className="card-title">
        <span className="accent-bar" style={{ background: 'var(--success)' }}></span>
        Security Posture
      </h3>

      {/* Current Score */}
      <div style={{ display: 'flex', alignItems: 'baseline', gap: '0.75rem', marginBottom: '1.25rem' }}>
        <span style={{ fontSize: '3rem', fontWeight: 800, color: label.color, lineHeight: 1 }}>
          {currentScore}
        </span>
        <span style={{ fontSize: '1rem', color: 'var(--text-muted)' }}>/100</span>
        <span className="badge" style={{ background: `${label.color}22`, color: label.color, border: `1px solid ${label.color}44` }}>
          {label.text}
        </span>
      </div>

      {/* Bar Chart */}
      <div className="chart-container">
        {scores.map((score, idx) => (
          <div key={idx} className="chart-bar-wrapper">
            <div
              className="chart-bar"
              data-value={score}
              style={{
                height: `${score * 1.6}px`,
                background: `linear-gradient(180deg, ${getBarColor(score)}, ${getBarColor(score)}44)`,
                animationDelay: `${idx * 80}ms`,
              }}
            ></div>
            <span className="chart-label">{days[idx]}</span>
          </div>
        ))}
      </div>
    </div>
  );
};

export default RepoPosture;
