import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';

export default function OwnerDashboardPage() {
    const [allCases, setAllCases] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const user = getUser();
    const navigate = useNavigate();

    useEffect(() => {
        fetchCases();
    }, []);

    const fetchCases = async () => {
        setLoading(true);
        try {
            const data = await apiCall('/api/cases/', 'GET');
            setAllCases(data || []);
        } catch (err) {
            setError('Failed to load system data');
        } finally {
            setLoading(false);
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
                <h1>Control Tower</h1>
                <p>Global oversight of the Counselling Platform</p>
            </div>

            <div className="stats-row">
                <div className="stat-card">
                    <span className="stat-value">{stats.total}</span>
                    <span className="stat-label">Total Cases</span>
                </div>
                <div className="stat-card">
                    <span className="stat-value">{stats.open}</span>
                    <span className="stat-label">Open Now</span>
                </div>
            </div>

            <div className="quick-actions-grid" style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem', marginTop: '1rem' }}>
                <Link to="/users" className="glass-panel stat-card" style={{ textDecoration: 'none', textAlign: 'center' }}>
                    <h3 style={{ margin: '0.5rem 0' }}>User Management</h3>
                    <p style={{ fontSize: 'var(--font-xs)', opacity: 0.7 }}>Manage staff & clients</p>
                </Link>
                <Link to="/audit-logs" className="glass-panel stat-card" style={{ textDecoration: 'none', textAlign: 'center' }}>
                    <h3 style={{ margin: '0.5rem 0' }}>Audit Logs</h3>
                    <p style={{ fontSize: 'var(--font-xs)', opacity: 0.7 }}>Review all system actions</p>
                </Link>
                <Link to="/all-cases" className="glass-panel stat-card" style={{ textDecoration: 'none', textAlign: 'center' }}>
                    <h3 style={{ margin: '0.5rem 0' }}>Global Cases</h3>
                    <p style={{ fontSize: 'var(--font-xs)', opacity: 0.7 }}>Review every interaction</p>
                </Link>
            </div>

            <div className="recent-activity glass-panel" style={{ marginTop: '2rem' }}>
                <div className="panel-header" style={{ borderBottom: '1px solid var(--border-subtle)', marginBottom: '1rem' }}>
                    <h2>System Health</h2>
                </div>
                <p>Dashboard is connected to <strong>{apiCall.baseUrl || 'Backend API'}</strong></p>
                <p>Current User Role: <span className="role-badge role-owner">{user?.role}</span></p>
            </div>
        </div>
    );
}
