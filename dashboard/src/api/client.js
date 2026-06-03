/**
 * SecureFlow Dashboard — API Client
 * Lightweight fetch wrapper for the FastAPI backend.
 * No external dependencies required — uses native fetch.
 *
 * In development, Vite proxies /api → localhost:8000/api.
 * In production, the dashboard is served by the same FastAPI origin.
 */

const BASE_URL = import.meta.env.VITE_API_URL || '';

async function request(path, options = {}) {
  const url = `${BASE_URL}${path}`;
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  });

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(error.detail || `HTTP ${res.status}`);
  }

  return res.json();
}

// ---- Findings ----
export async function getFindings(params = {}) {
  const query = new URLSearchParams(params).toString();
  return request(`/api/findings${query ? '?' + query : ''}`);
}

export async function getFindingsSummary() {
  return request('/api/findings/summary');
}

// ---- Approvals ----
export async function getPendingApprovals() {
  return request('/api/approvals');
}

export async function processApproval(actionId, action) {
  return request(`/api/approvals/${actionId}`, {
    method: 'POST',
    body: JSON.stringify({ action }),
  });
}

// ---- Health ----
export async function getHealth() {
  return request('/health');
}
