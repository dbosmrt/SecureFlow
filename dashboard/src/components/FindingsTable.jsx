import React, { useState } from 'react';

/**
 * FindingsTable — Sortable security findings display
 * Shows severity badges, scanner type, CVE details, and status.
 */
const FindingsTable = ({ findings, loading }) => {
  const [sortField, setSortField] = useState('severity');
  const [sortAsc, setSortAsc] = useState(false);

  const severityOrder = { CRITICAL: 0, HIGH: 1, MEDIUM: 2, LOW: 3, INFO: 4 };

  const sorted = [...findings].sort((a, b) => {
    if (sortField === 'severity') {
      const diff = (severityOrder[a.severity] ?? 5) - (severityOrder[b.severity] ?? 5);
      return sortAsc ? diff : -diff;
    }
    const aVal = a[sortField] || '';
    const bVal = b[sortField] || '';
    return sortAsc ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
  });

  const handleSort = (field) => {
    if (sortField === field) {
      setSortAsc(!sortAsc);
    } else {
      setSortField(field);
      setSortAsc(false);
    }
  };

  const SortIcon = ({ field }) => (
    <span style={{ opacity: sortField === field ? 1 : 0.3, marginLeft: '4px' }}>
      {sortField === field ? (sortAsc ? '↑' : '↓') : '↕'}
    </span>
  );

  if (loading) {
    return (
      <div className="table-wrapper">
        <div className="empty-state">
          <div className="icon">⏳</div>
          <p>Loading findings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="table-wrapper">
      <table>
        <thead>
          <tr>
            <th onClick={() => handleSort('severity')} style={{ cursor: 'pointer' }}>
              Severity <SortIcon field="severity" />
            </th>
            <th onClick={() => handleSort('title')} style={{ cursor: 'pointer' }}>
              Finding <SortIcon field="title" />
            </th>
            <th onClick={() => handleSort('scanner')} style={{ cursor: 'pointer' }}>
              Scanner <SortIcon field="scanner" />
            </th>
            <th>CVE / Details</th>
            <th>File</th>
            <th onClick={() => handleSort('status')} style={{ cursor: 'pointer' }}>
              Status <SortIcon field="status" />
            </th>
          </tr>
        </thead>
        <tbody>
          {sorted.map((finding) => (
            <tr key={finding.id}>
              <td>
                <span className={`badge ${finding.severity?.toLowerCase()}`}>
                  {finding.severity}
                </span>
              </td>
              <td>
                <div style={{ fontWeight: 600, marginBottom: '2px' }}>{finding.title}</div>
                {finding.description && (
                  <div style={{ fontSize: '0.78rem', color: 'var(--text-muted)', maxWidth: '350px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {finding.description}
                  </div>
                )}
              </td>
              <td>
                <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                  {finding.scanner}
                </span>
              </td>
              <td>
                {finding.cve_ids && finding.cve_ids.length > 0 ? (
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                    {finding.cve_ids.map(cve => (
                      <span key={cve} className="badge info">{cve}</span>
                    ))}
                  </div>
                ) : (
                  <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>—</span>
                )}
                {finding.cvss_score && (
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginTop: '2px' }}>
                    CVSS: {finding.cvss_score}
                  </div>
                )}
              </td>
              <td>
                {finding.file_path ? (
                  <code style={{ fontSize: '0.8rem', color: 'var(--primary-light)' }}>
                    {finding.file_path}
                    {finding.line_number ? `:${finding.line_number}` : ''}
                  </code>
                ) : (
                  <span style={{ color: 'var(--text-muted)' }}>—</span>
                )}
              </td>
              <td>
                <span className={`badge status-${finding.status?.toLowerCase()}`}>
                  {finding.status}
                </span>
              </td>
            </tr>
          ))}
          {findings.length === 0 && (
            <tr>
              <td colSpan="6">
                <div className="empty-state">
                  <div className="icon">🛡️</div>
                  <p>No security findings detected. Your code is secure!</p>
                </div>
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
};

export default FindingsTable;
