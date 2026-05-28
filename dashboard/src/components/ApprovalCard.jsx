import React, { useState } from 'react';
import { processApproval } from '../api/client';

/**
 * ApprovalCard — HITL approval/rejection UI
 * Shows the pending action with payload preview and action buttons.
 */
const ApprovalCard = ({ approval, onProcessed }) => {
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);

  const handleAction = async (action) => {
    setProcessing(true);
    setError(null);
    try {
      await processApproval(approval.id, action);
      onProcessed();
    } catch (err) {
      setError(err.message || 'Failed to process');
    } finally {
      setProcessing(false);
    }
  };

  const payloadStr = typeof approval.action_payload === 'string'
    ? approval.action_payload
    : JSON.stringify(approval.action_payload, null, 2);

  return (
    <div className="approval-card">
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
          <span className="badge" style={{ background: 'rgba(139, 92, 246, 0.2)', color: 'var(--purple-light)', border: '1px solid rgba(139, 92, 246, 0.3)' }}>
            {approval.action_type}
          </span>
          <span style={{ fontSize: '1rem', fontWeight: 600 }}>Requires Approval</span>
        </div>

        <div style={{ display: 'flex', gap: '1.5rem', fontSize: '0.8rem', color: 'var(--text-muted)', marginBottom: '0.75rem' }}>
          <span>Finding: <code style={{ color: 'var(--text-secondary)' }}>{approval.finding_id?.slice(0, 8)}...</code></span>
          {approval.requested_at && (
            <span>Requested: {new Date(approval.requested_at).toLocaleString()}</span>
          )}
        </div>

        <div className="code-block">
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{payloadStr}</pre>
        </div>

        {error && (
          <div style={{ marginTop: '0.5rem', fontSize: '0.8rem', color: 'var(--danger)' }}>
            ⚠ {error}
          </div>
        )}
      </div>

      <div style={{ display: 'flex', gap: '0.75rem', flexShrink: 0 }}>
        <button
          className="btn btn-reject"
          onClick={() => handleAction('REJECT')}
          disabled={processing}
        >
          {processing ? '...' : 'Reject'}
        </button>
        <button
          className="btn btn-approve"
          onClick={() => handleAction('APPROVE')}
          disabled={processing}
        >
          {processing ? '...' : '✓ Approve'}
        </button>
      </div>
    </div>
  );
};

export default ApprovalCard;
