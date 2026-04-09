import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';

export default function AdminDashboardPage() {
  const [cases, setCases] = useState([]);
  const [allCases, setAllCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('all');
  const [search, setSearch] = useState('');
  const user = getUser();
  const navigate = useNavigate();

  useEffect(() => {
    fetchCases();
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

  const handleSelfAssign = async (caseId) => {
    try {
      await apiCall(`/api/cases/${caseId}/assign/`, 'POST', {
        admin_id: user?.id,
      });
      fetchCases();
    } catch (err) {
      alert('Failed to assign case');
    }
  };

  const stats = {
    total: allCases.length,
    open: allCases.filter((c) => c.status === 'open').length,
    assigned: allCases.filter((c) => c.status === 'assigned').length,
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
      </div>

      {/* Search Bar */}
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search for a case ID or title..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs glass-panel">
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
      </div>

      {/* Cases List */}
      <div className="cases-section glass-panel">
        {loading ? (
          <div className="loading-spinner" />
        ) : cases.length === 0 ? (
          <p className="empty-state">No matching cases found</p>
        ) : (
          <div className="cases-grid">
            {cases.map((caseItem) => (
              <div
                key={caseItem.id}
                className="case-card"
                onClick={() => navigate(`/cases/${caseItem.id}`)}
              >
                <div className="case-header">
                  <h3>Case #{caseItem.id}</h3>
                  <span className={`status-badge status-${caseItem.status}`}>
                    {caseItem.status}
                  </span>
                </div>
                <h4>{caseItem.title}</h4>
                <p>{caseItem.description?.substring(0, 80)}...</p>

                <div className="case-meta">
                  <span>User: {caseItem.user?.username || 'Guest'}</span>
                </div>

                {caseItem.status === 'open' && (
                  <button
                    className="button button-primary button-sm"
                    style={{ marginTop: '0.75rem' }}
                    onClick={(e) => {
                      e.stopPropagation();
                      handleSelfAssign(caseItem.id);
                    }}
                  >
                    Assign to Me
                  </button>
                )}
              </div>
            ))}
          </div>
        )}
        {error && <div className="form-error">{error}</div>}
      </div>
    </div>
  );
}
