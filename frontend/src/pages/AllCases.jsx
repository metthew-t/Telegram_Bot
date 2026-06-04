import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { apiCall } from '../api.js';
import LoadingButton from '../components/LoadingButton.jsx';

export default function AllCasesPage() {
    const [cases, setCases] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [deletingId, setDeletingId] = useState(null);
    const navigate = useNavigate();

    useEffect(() => {
        fetchCases();
    }, []);

    const fetchCases = async () => {
        setLoading(true);
        try {
            const data = await apiCall('/api/cases/', 'GET');
            setCases(data || []);
        } catch (err) {
            setError('Failed to load system cases');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="page-panel">
            <div className="panel-header">
                <h1>Global Case Registry</h1>
                <p>Full history of support across the platform</p>
            </div>

            <div className="cases-section glass-panel">
                {loading ? (
                    <div className="loading-spinner" />
                ) : (
                    <div className="cases-grid">
                        {cases.map((c) => (
                            <div key={c.id} className="case-card" onClick={() => navigate(`/cases/${c.id}`)}>
                                <div className="case-header">
                                    <h3>#{c.id}</h3>
                                    <span className={`status-badge status-${c.status}`}>{c.status}</span>
                                </div>
                                <h4>{c.title}</h4>
                                <div className="case-meta">
                                    <span>Admin: {c.assigned_admin?.username || '—'}</span>
                                    <LoadingButton
                                        className="button button-danger button-sm"
                                        loading={deletingId === c.id}
                                        loadingText="Deleting..."
                                        onClick={async (e) => {
                                            e.stopPropagation();
                                            if (window.confirm('Delete case?')) {
                                                setDeletingId(c.id);
                                                try {
                                                    await apiCall(`/api/cases/${c.id}/`, 'DELETE');
                                                    fetchCases();
                                                } catch (err) {
                                                    alert('Failed to delete case.');
                                                } finally {
                                                    setDeletingId(null);
                                                }
                                            }
                                        }}
                                    >
                                        Delete
                                    </LoadingButton>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}
