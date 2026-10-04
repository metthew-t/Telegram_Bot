import { useEffect, useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';
import LoadingButton from '../components/LoadingButton.jsx';

export default function OwnerDashboardPage() {
    const [allCases, setAllCases] = useState([]);
    const [assignmentRequests, setAssignmentRequests] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [processingRequestId, setProcessingRequestId] = useState(null);
    const user = getUser();
    const navigate = useNavigate();

    useEffect(() => {
        fetchCases();
        fetchAssignmentRequests();
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

    const fetchAssignmentRequests = async () => {
        try {
            const data = await apiCall('/api/assignment-requests/', 'GET');
            setAssignmentRequests(data || []);
        } catch (err) {
            console.error('Failed to load assignment requests:', err);
        }
    };

    const handleApproveRequest = async (requestId) => {
        setProcessingRequestId(requestId);
        try {
            await apiCall(`/api/assignment-requests/${requestId}/approve/`, 'POST');
            await fetchAssignmentRequests();
            await fetchCases();
            alert('Assignment request approved!');
        } catch (err) {
            alert('Failed to approve request: ' + (err.message || 'Unknown error'));
        } finally {
            setProcessingRequestId(null);
        }
    };

    const handleRejectRequest = async (requestId) => {
        setProcessingRequestId(requestId);
        try {
            await apiCall(`/api/assignment-requests/${requestId}/reject/`, 'POST');
            await fetchAssignmentRequests();
            alert('Assignment request rejected');
        } catch (err) {
            alert('Failed to reject request: ' + (err.message || 'Unknown error'));
        } finally {
            setProcessingRequestId(null);
        }
    };

    const pendingRequests = assignmentRequests.filter(r => r.status === 'pending');

    const stats = {
        total: allCases.length,
        open: allCases.filter((c) => c.status === 'open').length,
        assigned: allCases.filter((c) => c.status === 'assigned').length,
        resolved: allCases.filter((c) => c.status === 'resolved').length,
        closed: allCases.filter((c) => c.status === 'closed').length,
        pendingRequests: pendingRequests.length,
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
                <div className="stat-card" style={{ background: stats.pendingRequests > 0 ? 'linear-gradient(135deg, rgba(255, 193, 7, 0.1) 0%, rgba(255, 152, 0, 0.1) 100%)' : undefined }}>
                    <span className="stat-value" style={{ color: stats.pendingRequests > 0 ? '#f59e0b' : undefined }}>
                        {stats.pendingRequests}
                    </span>
                    <span className="stat-label">Pending Assignment Requests</span>
                </div>
            </div>

            {/* Assignment Requests Section */}
            {pendingRequests.length > 0 && (
                <div className="glass-panel" style={{ marginTop: '2rem' }}>
                    <div className="panel-header" style={{ borderBottom: '1px solid var(--border-subtle)', marginBottom: '1rem' }}>
                        <h2>🔔 Assignment Requests</h2>
                        <p style={{ fontSize: 'var(--font-sm)', opacity: 0.8 }}>
                            Admins requesting case assignments
                        </p>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                        {pendingRequests.map(request => (
                            <div 
                                key={request.id}
                                style={{
                                    padding: '16px',
                                    background: 'rgba(255, 215, 0, 0.05)',
                                    border: '1px solid rgba(255, 215, 0, 0.2)',
                                    borderRadius: '8px',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    flexWrap: 'wrap',
                                    gap: '12px'
                                }}
                            >
                                <div style={{ flex: 1, minWidth: '200px' }}>
                                    <div style={{ fontWeight: 600, marginBottom: '4px' }}>
                                        <span className="case-id-badge">Case #{request.case_id}</span> - {request.case_title}
                                    </div>
                                    <div style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>
                                        Requested by: <strong>{request.admin_name}</strong>
                                    </div>
                                    <div style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)', marginTop: '4px' }}>
                                        {new Date(request.created_at).toLocaleString()}
                                    </div>
                                </div>
                                <div style={{ display: 'flex', gap: '8px' }}>
                                    <LoadingButton
                                        className="button button-primary button-sm"
                                        onClick={() => handleApproveRequest(request.id)}
                                        loading={processingRequestId === request.id}
                                        loadingText="Approving..."
                                        style={{ background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)' }}
                                    >
                                        ✓ Approve
                                    </LoadingButton>
                                    <LoadingButton
                                        className="button button-sm"
                                        onClick={() => handleRejectRequest(request.id)}
                                        loading={processingRequestId === request.id}
                                        loadingText="Rejecting..."
                                        style={{ 
                                            background: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
                                            color: 'white'
                                        }}
                                    >
                                        ✗ Reject
                                    </LoadingButton>
                                    <button
                                        className="button button-sm"
                                        onClick={() => navigate(`/cases/${request.case_id}`)}
                                        style={{ minWidth: 'auto', padding: '8px 12px' }}
                                    >
                                        View Case →
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

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
                <Link to="/analytics" className="glass-panel stat-card" style={{ textDecoration: 'none', textAlign: 'center' }}>
                    <h3 style={{ margin: '0.5rem 0' }}>📊 Analytics</h3>
                    <p style={{ fontSize: 'var(--font-xs)', opacity: 0.7 }}>Reports & Statistics</p>
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
