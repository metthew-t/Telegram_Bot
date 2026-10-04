import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';
import LoadingButton from '../components/LoadingButton.jsx';

export default function AdminDashboardPage() {
  const [cases, setCases] = useState([]);
  const [allCases, setAllCases] = useState([]);
  const [feedbacks, setFeedbacks] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const [requestingId, setRequestingId] = useState(null);
  const user = getUser();
  const navigate = useNavigate();

  useEffect(() => {
    fetchCases();
    fetchFeedbacks();
  }, []);

  useEffect(() => {
    applyFilters();
  }, [filter, search, allCases]);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/cases/', 'GET');
      setAllCases(data || []);
    } catch (err) {
      setError('Failed to load cases');
    } finally {
      setLoading(false);
    }
  };

  const fetchFeedbacks = async () => {
    try {
      const data = await apiCall('/api/feedbacks/', 'GET');
      setFeedbacks(data || []);
    } catch (err) {
      console.error('Failed to load feedbacks:', err);
    }
  };

  const applyFilters = () => {
    let filtered = [...allCases];

    // Status / assignment filter
    if (filter === 'mine') {
      filtered = filtered.filter(
        (c) =>
          c.assigned_admin?.id === user?.id ||
          c.assigned_admin?.label === user?.username
      );
    } else if (filter === 'open') {
      filtered = filtered.filter((c) => c.status === 'open');
    } else if (filter === 'assigned') {
      filtered = filtered.filter((c) => c.status === 'assigned');
    } else if (filter === 'resolved') {
      filtered = filtered.filter((c) => c.status === 'resolved');
    } else if (filter === 'closed') {
      filtered = filtered.filter((c) => c.status === 'closed');
    }

    // Text search
    if (search.trim()) {
      const q = search.toLowerCase();
      filtered = filtered.filter(
        (c) =>
          c.title?.toLowerCase().includes(q) ||
          c.description?.toLowerCase().includes(q) ||
          String(c.id).includes(q)
      );
    }

    setCases(filtered);
  };

  const handleRequestAssignment = async (caseId) => {
    setRequestingId(caseId);
    try {
      await apiCall('/api/assignment-requests/', 'POST', {
        case_id: caseId,
      });
      alert('Assignment request sent to owner for approval');
      fetchCases();
    } catch (err) {
      alert(err.message || 'Failed to request assignment');
    } finally {
      setRequestingId(null);
    }
  };

  const getTimeElapsed = (timestamp) => {
    if (!timestamp) return 'N/A';
    const now = new Date();
    const then = new Date(timestamp);
    const diffMs = now - then;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffDays > 0) return `${diffDays}d ago`;
    if (diffHours > 0) return `${diffHours}h ago`;
    if (diffMins > 0) return `${diffMins}m ago`;
    return 'Just now';
  };

  const stats = {
    total: allCases.length,
    open: allCases.filter((c) => c.status === 'open').length,
    assigned: allCases.filter((c) => c.status === 'assigned').length,
    resolved: allCases.filter((c) => c.status === 'resolved').length,
    closed: allCases.filter((c) => c.status === 'closed').length,
  };

  return (
    <div className="page-panel">
      <div className="panel-header">
        <h1>Admin Support Desk</h1>
        <p>Manage your assigned cases and assist new users</p>
      </div>

      {/* Stats Row */}
      <div className="stats-row">
        <div className="stat-card">
          <span className="stat-value">{allCases.filter(c => c.assigned_admin?.id === user?.id).length}</span>
          <span className="stat-label">My Active Cases</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.open}</span>
          <span className="stat-label">Available (Open)</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{feedbacks.length}</span>
          <span className="stat-label">Feedbacks</span>
        </div>
      </div>

      {/* Search Bar */}
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          placeholder="Search for a case ID or title..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          style={{ width: '100%' }}
        />
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs">
        <button
          className={`tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All Available ({allCases.length})
        </button>
        <button
          className={`tab ${filter === 'mine' ? 'active' : ''}`}
          onClick={() => setFilter('mine')}
        >
          Assigned to Me
        </button>
        <button
          className={`tab ${filter === 'open' ? 'active' : ''}`}
          onClick={() => setFilter('open')}
        >
          Take New (Open)
        </button>
        <button
          className={`tab ${filter === 'closed' ? 'active' : ''}`}
          onClick={() => setFilter('closed')}
        >
          Closed Cases
        </button>
      </div>

      {/* Cases List */}
      <div style={{ marginTop: '20px' }}>
        {loading ? (
          <div className="loading-spinner" />
        ) : cases.length === 0 ? (
          <p className="empty-state">No matching cases found</p>
        ) : (
          <div className="cases-grid">
            {cases.map((caseItem) => {
              const isAssignedToMe = caseItem.assigned_admin?.id === user?.id || 
                                     caseItem.assigned_admin?.label === user?.username;
              const caseFeedback = feedbacks.find(f => f.case === caseItem.id);
              const isClickable = user?.role === 'owner' || isAssignedToMe || caseItem.status === 'open';
              
              return (
                <div
                  key={caseItem.id}
                  className="case-card"
                  onClick={() => isClickable && navigate(`/cases/${caseItem.id}`)}
                  style={{
                    opacity: isClickable ? 1 : 0.6,
                    cursor: isClickable ? 'pointer' : 'not-allowed',
                    background: isClickable 
                      ? undefined 
                      : 'linear-gradient(135deg, rgba(0,0,0,0.02) 0%, rgba(0,0,0,0.05) 100%)',
                  }}
                >
                  <div className="case-header">
                    <h3>
                      <span className="case-id-badge">Case #{caseItem.user_case_number || caseItem.id}</span>
                      {caseItem.assigned_admin && (
                        <span style={{ fontSize: '0.9rem', color: '#64748b', marginLeft: '8px' }}>
                          → {caseItem.assigned_admin.label || caseItem.assigned_admin.username}
                        </span>
                      )}
                    </h3>
                    <span className={`status-badge status-${caseItem.status}`}>
                      {caseItem.status}
                    </span>
                  </div>
                  <h4>{caseItem.title}</h4>
                  <p>{caseItem.description?.substring(0, 80)}...</p>

                  <div className="case-meta">
                    <span>Created: {getTimeElapsed(caseItem.created_at)}</span>
                    {caseItem.assigned_at && (
                      <span> • Assigned: {getTimeElapsed(caseItem.assigned_at)}</span>
                    )}
                    {caseItem.resolved_at && (
                      <span> • Resolved: {getTimeElapsed(caseItem.resolved_at)}</span>
                    )}
                    {caseItem.closed_at && (
                      <span> • Closed: {getTimeElapsed(caseItem.closed_at)}</span>
                    )}
                  </div>

                  {caseFeedback && (
                    <div style={{ 
                      marginTop: '8px', 
                      padding: '8px', 
                      background: '#f0fdf4', 
                      borderRadius: '6px',
                      fontSize: '0.85rem'
                    }}>
                      <strong>📝 Feedback:</strong> {caseFeedback.content.substring(0, 60)}...
                      {caseFeedback.rating && <span> ⭐ {caseFeedback.rating}/5</span>}
                    </div>
                  )}

                  {caseItem.status === 'open' && !caseItem.assigned_admin && (
                    <LoadingButton
                      className="button button-primary button-sm"
                      style={{ marginTop: '0.75rem' }}
                      loading={requestingId === caseItem.id}
                      loadingText="Requesting..."
                      onClick={(e) => {
                        e.stopPropagation();
                        handleRequestAssignment(caseItem.id);
                      }}
                    >
                      Request Assignment
                    </LoadingButton>
                  )}
                  
                  {!isAssignedToMe && !isClickable && (
                    <div style={{ 
                      marginTop: '8px', 
                      padding: '6px 10px', 
                      background: '#e5e7eb', 
                      borderRadius: '4px',
                      fontSize: '0.85rem',
                      color: '#6b7280'
                    }}>
                      🔒 Not accessible - {caseItem.status === 'closed' ? 'case closed' : 'assigned to another admin'}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
      {error && <div className="form-error" style={{ marginTop: '16px' }}>{error}</div>}
    </div>
  );
}
