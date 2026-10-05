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
  const [selectedFeedback, setSelectedFeedback] = useState(null); // For feedback modal
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
      console.log('Feedbacks received:', data);
      console.log('Feedbacks count:', data?.length);
      if (data && data.length > 0) {
        console.log('First feedback case ID:', data[0].case);
        console.log('First feedback rating:', data[0].rating);
      }
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

  const handleSelfAssign = async (caseId) => {
    setRequestingId(caseId);
    try {
      await apiCall(`/api/cases/${caseId}/assign/`, 'POST', {
        admin_id: user?.id,
      });
      fetchCases();
    } catch (err) {
      alert('Failed to assign case');
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
          <span className="stat-value">
            {(() => {
              const count = user?.role === 'owner' 
                ? feedbacks.length
                : feedbacks.filter(f => {
                    const feedbackCase = allCases.find(c => c.id === f.case);
                    const matches = feedbackCase?.assigned_admin?.id === user?.id;
                    console.log(`Feedback ${f.id} case ${f.case}: found case=${!!feedbackCase}, matches admin=${matches}`);
                    return matches;
                  }).length;
              console.log(`Total feedbacks displayed: ${count}`);
              console.log(`All cases IDs:`, allCases.map(c => c.id));
              return count;
            })()}
          </span>
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
              
              // For admins: only assigned cases are fully clickable and bright
              // For owners: all cases are clickable
              const isFullyAccessible = user?.role === 'owner' || isAssignedToMe;
              
              return (
                <div
                  key={caseItem.id}
                  className="case-card"
                  onClick={() => isFullyAccessible && navigate(`/cases/${caseItem.id}`)}
                  style={{
                    opacity: isFullyAccessible ? 1 : 0.5,
                    cursor: isFullyAccessible ? 'pointer' : 'not-allowed',
                    background: isFullyAccessible 
                      ? undefined 
                      : 'linear-gradient(135deg, rgba(0,0,0,0.03) 0%, rgba(0,0,0,0.08) 100%)',
                    filter: isFullyAccessible ? undefined : 'blur(0.3px)',
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

                  {/* Only show feedback for cases assigned to this admin */}
                  {caseFeedback && isAssignedToMe && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation(); // Prevent navigation to case detail
                        setSelectedFeedback(caseFeedback);
                      }}
                      style={{ 
                        marginTop: '8px', 
                        padding: '10px 14px', 
                        background: 'linear-gradient(135deg, #10b981, #059669)', 
                        border: 'none',
                        borderRadius: '8px',
                        fontSize: '0.85rem',
                        color: '#ffffff',
                        fontWeight: 600,
                        cursor: 'pointer',
                        width: '100%',
                        textAlign: 'left',
                        transition: 'all 0.2s',
                        boxShadow: '0 2px 8px rgba(16, 185, 129, 0.3)'
                      }}
                      onMouseEnter={(e) => {
                        e.currentTarget.style.transform = 'translateY(-2px)';
                        e.currentTarget.style.boxShadow = '0 4px 12px rgba(16, 185, 129, 0.4)';
                      }}
                      onMouseLeave={(e) => {
                        e.currentTarget.style.transform = 'translateY(0)';
                        e.currentTarget.style.boxShadow = '0 2px 8px rgba(16, 185, 129, 0.3)';
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                        <span>📝 Feedback Received</span>
                        {caseFeedback.rating && <span>⭐ {caseFeedback.rating}/5</span>}
                      </div>
                      <div style={{ fontSize: '0.75rem', opacity: 0.9, marginTop: '4px' }}>
                        Click to view full feedback
                      </div>
                    </button>
                  )}

                  {caseItem.status === 'open' && !caseItem.assigned_admin && user?.role !== 'owner' && (
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

                  {caseItem.status === 'open' && !caseItem.assigned_admin && user?.role === 'owner' && (
                    <LoadingButton
                      className="button button-primary button-sm"
                      style={{ marginTop: '0.75rem' }}
                      loading={requestingId === caseItem.id}
                      loadingText="Assigning..."
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSelfAssign(caseItem.id);
                      }}
                    >
                      Assign to Me
                    </LoadingButton>
                  )}
                  
                  {user?.role !== 'owner' && !isFullyAccessible && (
                    <div style={{ 
                      marginTop: '8px', 
                      padding: '6px 10px', 
                      background: 'rgba(0,0,0,0.05)', 
                      borderRadius: '4px',
                      fontSize: '0.85rem',
                      color: '#6b7280',
                      pointerEvents: 'none'
                    }}>
                      {caseItem.status === 'closed' 
                        ? '🔒 Case closed' 
                        : caseItem.assigned_admin 
                          ? `🔒 Assigned to ${caseItem.assigned_admin.label || caseItem.assigned_admin.username}`
                          : '🔒 Not assigned to you'}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>
      {error && <div className="form-error" style={{ marginTop: '16px' }}>{error}</div>}

      {/* Feedback Modal */}
      {selectedFeedback && (
        <div 
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(4px)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
            padding: '20px',
            animation: 'fadeIn 0.2s ease'
          }}
          onClick={() => setSelectedFeedback(null)}
        >
          <div 
            style={{
              background: 'linear-gradient(145deg, #ffffff, #f8f9fa)',
              borderRadius: '16px',
              padding: '32px',
              maxWidth: '650px',
              width: '100%',
              maxHeight: '85vh',
              overflow: 'auto',
              boxShadow: '0 24px 80px rgba(0, 0, 0, 0.4), 0 0 1px rgba(99, 102, 241, 0.5)',
              border: '1px solid rgba(99, 102, 241, 0.1)',
              animation: 'slideUp 0.3s ease'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', paddingBottom: '16px', borderBottom: '2px solid #e5e7eb' }}>
              <h3 style={{ 
                margin: 0, 
                color: '#111827',
                fontSize: '24px',
                fontWeight: '700',
                display: 'flex',
                alignItems: 'center',
                gap: '10px'
              }}>
                <span style={{ 
                  background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                  WebkitBackgroundClip: 'text',
                  WebkitTextFillColor: 'transparent',
                  backgroundClip: 'text'
                }}>📝 User Feedback</span>
              </h3>
              <button 
                onClick={() => setSelectedFeedback(null)}
                style={{
                  background: 'rgba(239, 68, 68, 0.1)',
                  border: '1px solid rgba(239, 68, 68, 0.2)',
                  borderRadius: '8px',
                  width: '36px',
                  height: '36px',
                  fontSize: '20px',
                  cursor: 'pointer',
                  color: '#ef4444',
                  transition: 'all 0.2s ease',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)';
                  e.currentTarget.style.transform = 'rotate(90deg)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                  e.currentTarget.style.transform = 'rotate(0deg)';
                }}
              >
                ×
              </button>
            </div>
            
            {selectedFeedback.rating && (
              <div style={{ 
                marginBottom: '20px',
                padding: '16px',
                background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05))',
                borderRadius: '12px',
                border: '1px solid rgba(99, 102, 241, 0.1)'
              }}>
                <strong style={{ color: '#374151', fontSize: '15px', display: 'block', marginBottom: '8px' }}>⭐ Rating:</strong>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <span style={{ fontSize: '24px', letterSpacing: '2px' }}>
                    {'⭐'.repeat(selectedFeedback.rating)}
                  </span>
                  <span style={{ 
                    color: '#6366f1',
                    fontWeight: '600',
                    fontSize: '18px'
                  }}>
                    {selectedFeedback.rating}/5
                  </span>
                </div>
              </div>
            )}
            
            <div>
              <strong style={{ 
                color: '#374151', 
                fontSize: '15px',
                display: 'block',
                marginBottom: '12px'
              }}>💬 Feedback Message:</strong>
              <p style={{ 
                marginTop: '0',
                color: '#1f2937',
                lineHeight: '1.7',
                whiteSpace: 'pre-wrap',
                padding: '20px',
                background: '#ffffff',
                borderLeft: '4px solid #6366f1',
                borderRadius: '12px',
                fontSize: '15px',
                boxShadow: '0 2px 8px rgba(0, 0, 0, 0.05)',
                border: '1px solid #e5e7eb',
                minHeight: '80px',
                wordBreak: 'break-word'
              }}>
                {selectedFeedback.content}
              </p>
            </div>
            
            {selectedFeedback.created_at && (
              <div style={{ 
                marginTop: '20px', 
                paddingTop: '16px',
                borderTop: '1px solid #e5e7eb',
                fontSize: '13px', 
                color: '#6b7280',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <span>🕐</span>
                <span>Submitted: {new Date(selectedFeedback.created_at).toLocaleString()}</span>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
