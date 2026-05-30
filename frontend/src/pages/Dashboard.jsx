import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';

export default function DashboardPage() {
  const [cases, setCases] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const user = getUser();
  const navigate = useNavigate();

  useEffect(() => {
    if (user?.role === 'owner') {
      navigate('/owner');
    } else if (user?.role === 'admin') {
      navigate('/admin');
    } else {
      fetchCases();
    }
  }, [user, navigate]);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/cases/', 'GET');
      setCases(data || []);
    } catch (err) {
      setError('Failed to load cases');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCase = async (e) => {
    e.preventDefault();
    try {
      const newCase = await apiCall('/api/cases/', 'POST', {
        title,
        description,
      });
      setCases([...cases, newCase]);
      setTitle('');
      setDescription('');
      setError('');
    } catch (err) {
      setError(err.response?.data?.error || 'Failed to create case');
    }
  };

  const handleCaseClick = (caseId) => {
    navigate(`/cases/${caseId}`);
  };

  return (
    <div className="page-panel">
      <div className="panel-header">
        <h1>Your Support Cases</h1>
        <p>View, manage, and update your support cases</p>
      </div>

      {/* Create New Case Form */}
      {user?.role === 'user' && (
        <div className="form-section glass-panel">
          <h2>Create New Case</h2>
          <form className="form-grid" onSubmit={handleCreateCase}>
            <label>
              Title
              <input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                required
                placeholder="Brief title of your issue"
              />
            </label>
            <label>
              Description
              <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                required
                placeholder="Detailed description of your issue"
                rows="4"
              />
            </label>
            {error && <div className="form-error">{error}</div>}
            <button className="button button-primary" type="submit">
              Create Case
            </button>
          </form>
        </div>
      )}

      {/* Cases List */}
      <div className="cases-section glass-panel">
        <h2>Cases {cases.length > 0 && `(${cases.length})`}</h2>
        {loading ? (
          <p>Loading cases...</p>
        ) : cases.length === 0 ? (
          <p className="empty-state">No cases yet. Create one to get started.</p>
        ) : (
          <div className="cases-grid">
            {cases.map((caseItem) => (
              <div key={caseItem.id} className="case-card" onClick={() => handleCaseClick(caseItem.id)}>
                <div className="case-header">
                  <h3>Case #{caseItem.id}</h3>
                  <span className={`status-badge status-${caseItem.status}`}>
                    {caseItem.status}
                  </span>
                </div>
                <h4>{caseItem.title}</h4>
                <p>{caseItem.description?.substring(0, 100)}...</p>
                <div className="case-meta">
                  {caseItem.assigned_admin && (
                    <span>Assigned to: {caseItem.assigned_admin}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
