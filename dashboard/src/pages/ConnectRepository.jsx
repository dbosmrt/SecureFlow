import React, { useState, useEffect } from 'react';
import {
  Shield, ArrowLeft, GitBranch, Link2, Key, Eye, EyeOff,
  Check, AlertTriangle, Trash2, Loader, Clock, CheckCircle2,
  XCircle, Plug, GitMerge, ArrowRight
} from 'lucide-react';
import { connectRepository, getConnectedProjects, disconnectProject } from '../api/client';
import './ConnectRepository.css';

/* ============================================================
   Custom Cursor (shared with Dashboard)
   ============================================================ */
const ConnectCursor = () => {
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
      <linearGradient id="logoGradConnect" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stopColor="#fb923c" />
        <stop offset="100%" stopColor="#ea580c" />
      </linearGradient>
    </defs>
    <path
      d="M50 15 Q 85 30 85 65 Q 85 90 50 85 Q 15 90 15 65 Q 15 30 50 15 M50 15 Q 15 30 15 65 Q 15 80 50 75 Q 85 80 85 65 Q 85 30 50 15 Z"
      fill="none" stroke="url(#logoGradConnect)" strokeWidth="6"
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
      <button className="dash-back-link" onClick={() => onNavigate && onNavigate('dashboard')}>
        <ArrowLeft style={{ width: 16, height: 16 }} />
      </button>
      <LogoSVG />
      <span className="dash-nav-brand">
        Secure<span className="dash-nav-brand-accent">Flow</span>
      </span>
      <div className="dash-nav-divider" />
      <span className="dash-nav-repo">
        <Plug style={{ width: 16, height: 16 }} /> Connect Repository
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
   Connect Repository Page
   ============================================================ */
const ConnectRepository = ({ onNavigate }) => {
  // Form state
  const [token, setToken] = useState('');
  const [repoUrl, setRepoUrl] = useState('');
  const [showToken, setShowToken] = useState(false);
  const [errors, setErrors] = useState({});

  // Submission state
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null); // { type: 'success'|'error', message }
  const [step, setStep] = useState(0); // 0=form, 1=validating, 2=resolving, 3=webhook, 4=done

  // Connected projects state
  const [projects, setProjects] = useState([]);
  const [projectsLoading, setProjectsLoading] = useState(true);
  const [disconnecting, setDisconnecting] = useState({});

  // Load connected projects
  const loadProjects = async () => {
    try {
      const res = await getConnectedProjects();
      setProjects(res.projects || []);
    } catch (err) {
      console.error('Failed to load projects:', err);
    } finally {
      setProjectsLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
  }, []);

  // Validation
  const validate = () => {
    const errs = {};
    if (!token.trim()) errs.token = 'GitLab PAT is required';
    else if (!token.trim().startsWith('glpat-')) errs.token = 'PAT should start with "glpat-"';

    if (!repoUrl.trim()) errs.url = 'Repository URL is required';
    else if (!/^https?:\/\/(www\.)?gitlab\.com\/.+\/.+/i.test(repoUrl.trim())) {
      errs.url = 'Invalid GitLab URL (e.g., https://gitlab.com/user/project)';
    }

    setErrors(errs);
    return Object.keys(errs).length === 0;
  };

  // Submit handler
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validate()) return;

    setLoading(true);
    setResult(null);

    // Animated step progression
    setStep(1);
    await new Promise(r => setTimeout(r, 400));
    setStep(2);
    await new Promise(r => setTimeout(r, 300));
    setStep(3);

    try {
      const res = await connectRepository({
        gitlab_token: token.trim(),
        repository_url: repoUrl.trim(),
      });

      setStep(4);

      if (res.success) {
        setResult({ type: 'success', message: res.message || 'Repository connected successfully!' });
        setToken('');
        setRepoUrl('');
        await loadProjects();
      } else {
        setResult({ type: 'error', message: res.message || 'Failed to connect repository.' });
      }
    } catch (err) {
      setResult({ type: 'error', message: err.message || 'Connection failed. Please try again.' });
    } finally {
      setLoading(false);
      setTimeout(() => setStep(0), 3000);
    }
  };

  // Disconnect handler
  const handleDisconnect = async (projectId) => {
    setDisconnecting(prev => ({ ...prev, [projectId]: true }));
    try {
      await disconnectProject(projectId);
      await loadProjects();
    } catch (err) {
      console.error('Disconnect failed:', err);
    } finally {
      setDisconnecting(prev => ({ ...prev, [projectId]: false }));
    }
  };

  const stepLabels = [
    { icon: Key, label: 'Validate Token' },
    { icon: GitBranch, label: 'Resolve Project' },
    { icon: Plug, label: 'Register Webhook' },
    { icon: Check, label: 'Connected' },
  ];

  return (
    <div className="connect-root">
      <ConnectCursor />
      <TopNav onNavigate={onNavigate} />

      <main className="connect-main">
        {/* Hero */}
        <div className="connect-hero">
          <div className="connect-hero-icon">
            <Plug />
          </div>
          <h1>Connect Repository</h1>
          <p>
            Paste your GitLab PAT and repository URL. SecureFlow handles everything —
            webhook setup, project validation, and security scanning.
          </p>
        </div>

        {/* Step indicator */}
        {step > 0 && (
          <div className="connect-steps">
            {stepLabels.map((s, i) => {
              const StepIcon = s.icon;
              const isActive = step === i + 1;
              const isDone = step > i + 1;
              return (
                <React.Fragment key={i}>
                  {i > 0 && <div className="connect-step-divider" />}
                  <div className={`connect-step ${isActive ? 'active' : ''} ${isDone ? 'done' : ''}`}>
                    {isDone ? <Check /> : <StepIcon />}
                    {s.label}
                  </div>
                </React.Fragment>
              );
            })}
          </div>
        )}

        {/* Connect Form */}
        <form className="connect-form-card" onSubmit={handleSubmit} id="connect-form">
          {/* PAT Input */}
          <div className="connect-form-group">
            <label className="connect-form-label" htmlFor="gitlab-pat">
              GitLab Personal Access Token
              <span className="connect-form-hint">Requires api scope</span>
            </label>
            <div className="connect-input-wrap">
              <Key />
              <input
                id="gitlab-pat"
                className={`connect-input ${errors.token ? 'error' : ''}`}
                type={showToken ? 'text' : 'password'}
                placeholder="glpat-xxxxxxxxxxxxxxxxxxxxxxxx"
                value={token}
                onChange={(e) => { setToken(e.target.value); setErrors(prev => ({ ...prev, token: null })); }}
                disabled={loading}
                autoComplete="off"
              />
              <button
                type="button"
                className="connect-eye-toggle"
                onClick={() => setShowToken(!showToken)}
                tabIndex={-1}
              >
                {showToken ? <EyeOff /> : <Eye />}
              </button>
            </div>
            {errors.token && (
              <div className="connect-field-error">
                <AlertTriangle style={{ width: 12, height: 12 }} /> {errors.token}
              </div>
            )}
          </div>

          {/* Repository URL Input */}
          <div className="connect-form-group">
            <label className="connect-form-label" htmlFor="repo-url">
              GitLab Repository URL
            </label>
            <div className="connect-input-wrap">
              <Link2 />
              <input
                id="repo-url"
                className={`connect-input ${errors.url ? 'error' : ''}`}
                type="url"
                placeholder="https://gitlab.com/username/project-name"
                value={repoUrl}
                onChange={(e) => { setRepoUrl(e.target.value); setErrors(prev => ({ ...prev, url: null })); }}
                disabled={loading}
              />
            </div>
            {errors.url && (
              <div className="connect-field-error">
                <AlertTriangle style={{ width: 12, height: 12 }} /> {errors.url}
              </div>
            )}
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            className="connect-submit-btn"
            disabled={loading}
            id="connect-submit"
          >
            {loading ? (
              <>
                <div className="connect-spinner" />
                Connecting...
              </>
            ) : (
              <>
                <Plug />
                Connect Repository
              </>
            )}
          </button>

          {/* Result Message */}
          {result && (
            <div className={`connect-status ${result.type}`}>
              {result.type === 'success' ? <CheckCircle2 /> : <XCircle />}
              {result.message}
            </div>
          )}
        </form>

        {/* Connected Projects Table */}
        <div className="connect-projects-section">
          <div className="connect-projects-header">
            <h3 className="connect-projects-title">
              <Shield /> Connected Projects
            </h3>
            <span className="connect-projects-count">{projects.length} project{projects.length !== 1 ? 's' : ''}</span>
          </div>

          <div className="connect-projects-card">
            <table className="connect-projects-table">
              <thead>
                <tr>
                  <th>Repository</th>
                  <th>Status</th>
                  <th>Last Scan</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {projectsLoading && (
                  <tr>
                    <td colSpan="4" style={{ textAlign: 'center', padding: '3rem', color: '#78716c' }}>
                      ⏳ Loading connected projects...
                    </td>
                  </tr>
                )}
                {!projectsLoading && projects.length === 0 && (
                  <tr>
                    <td colSpan="4">
                      <div className="connect-empty">
                        <div className="connect-empty-icon">🔗</div>
                        <p>No repositories connected yet. Paste your PAT and URL above to get started.</p>
                      </div>
                    </td>
                  </tr>
                )}
                {projects.map((project) => (
                  <tr key={project.project_id}>
                    <td>
                      <div className="connect-project-name">{project.project_name}</div>
                      <div className="connect-project-namespace">{project.namespace}</div>
                    </td>
                    <td>
                      <span className={`connect-status-badge ${project.status || 'connected'}`}>
                        {project.status === 'connected' ? <CheckCircle2 /> : <AlertTriangle />}
                        {project.status === 'connected' ? '✓ Connected' : '⚠ Needs Attention'}
                      </span>
                    </td>
                    <td>
                      <span className="connect-scan-time">
                        {project.last_scan_at
                          ? new Date(project.last_scan_at).toLocaleString()
                          : 'Not yet scanned'}
                      </span>
                    </td>
                    <td>
                      <button
                        className="connect-disconnect-btn"
                        onClick={() => handleDisconnect(project.project_id)}
                        disabled={disconnecting[project.project_id]}
                      >
                        {disconnecting[project.project_id] ? (
                          <><Loader style={{ width: 14, height: 14, animation: 'spin 0.6s linear infinite' }} /> ...</>
                        ) : (
                          <><Trash2 /> Disconnect</>
                        )}
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </main>
    </div>
  );
};

export default ConnectRepository;
