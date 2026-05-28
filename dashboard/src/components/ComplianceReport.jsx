import React from 'react';

/**
 * ComplianceReport — SLSA & SBOM compliance status display
 * Shows compliance levels, SBOM status, and action buttons.
 */
const ComplianceReport = () => {
  const items = [
    {
      label: 'SLSA Level',
      value: 'Level 3',
      color: 'var(--success)',
      borderColor: 'rgba(16, 185, 129, 0.25)',
    },
    {
      label: 'SBOM Format',
      value: 'CycloneDX v1.5',
      color: 'var(--primary)',
      borderColor: 'rgba(59, 130, 246, 0.25)',
    },
    {
      label: 'Last Scan',
      value: new Date().toLocaleDateString(),
      color: 'var(--text-primary)',
      borderColor: 'var(--border)',
    },
    {
      label: 'Audit Trail',
      value: 'Active',
      color: 'var(--success)',
      borderColor: 'rgba(16, 185, 129, 0.25)',
    },
  ];

  return (
    <div className="card">
      <h3 className="card-title">
        <span className="accent-bar" style={{ background: 'var(--primary)' }}></span>
        Compliance Status
      </h3>

      <div className="compliance-grid">
        {items.map((item, idx) => (
          <div key={idx} className="compliance-item" style={{ borderColor: item.borderColor }}>
            <div className="compliance-label">{item.label}</div>
            <div className="compliance-value" style={{ color: item.color }}>
              {item.value}
            </div>
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', marginTop: '1.25rem' }}>
        <button className="btn btn-secondary">
          📄 Download SBOM
        </button>
        <button className="btn btn-secondary">
          📋 View Audit Trail
        </button>
      </div>
    </div>
  );
};

export default ComplianceReport;
