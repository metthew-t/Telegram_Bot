import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';

export default function AdminDashboardPage() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [filter, setFilter] = useState('assigned');
  const user = getUser();
  const navigate = useNavigate();

  useEffect(() => {
    fetchCases();
  }, [filter]);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/cases/', 'GET');
      const filtered = data.filter((caseItem) => {
        if (filter === 'assigned') {
          return caseItem.assigned_admin === user?.username;
        }
        if (filter === 'open') {
          return caseItem.status === 'open';
        }
        return true;
      });
      setCases(filtered || []);
    } catch (err) {
      setError('Failed to load cases');
    } finally {
      setLoading(false);
    }
  };

  const handleCaseClick = (caseId) => {
    navigate(`/cases/${caseId}`);
  };

  return (
    <div className="page-panel">
      <div className="panel-header">
        <h1>Admin Dashboard</h1>
        <p>Manage support cases and assist users</p>
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs glass-panel">
        <button
          className={`tab ${filter === 'assigned' ? 'active' : ''}`}
          onClick={() => setFilter('assigned')}
        >
          My Cases ({cases.length})
        </button>
        <button
          className={`tab ${filter === 'open' ? 'active' : ''}`}
          onClick={() => setFilter('open')}
        >
          Unassigned Cases
        </button>
        <button
          className={`tab ${filter === 'all' ? 'active' : ''}`}
          onClick={() => setFilter('all')}
        >
          All Cases
        </button>
      </div>

      {/* Cases List */}
      <div className="cases-section glass-panel">
        {loading ? (
          <p>Loading cases...</p>
        ) : cases.length === 0 ? (
          <p className="empty-state">No cases in this category</p>
        ) : (
          <div className="cases-grid">
            {cases.map((caseItem) => (
              <div
                key={caseItem.id}
                className="case-card"
                onClick={() => handleCaseClick(caseItem.id)}
              >
                <div className="case-header">
                  <h3>Case #{caseItem.id}</h3>
                  <span className={`status-badge status-${caseItem.status}`}>
                    {caseItem.status}
                  </span>
                </div>
                <h4>{caseItem.title}</h4>
                <p>{caseItem.description?.substring(0, 100)}...</p>
                <div className="case-meta">
                  <span>User: {caseItem.user}</span>
                </div>
              </div>
            ))}
          </div>
        )}
        {error && <div className="form-error">{error}</div>}
      </div>
    </div>
  );
}
