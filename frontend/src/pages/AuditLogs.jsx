import { useEffect, useState } from 'react';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';

const ACTION_ICONS = {
  assigned: '📌',
  reassigned: '🔄',
  closed: '✅',
  reply: '💬',
  submitted: '📝',
};

export default function AuditLogsPage() {
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [actionFilter, setActionFilter] = useState('all');
  const [groupByCase, setGroupByCase] = useState(true);
  const user = getUser();

  useEffect(() => {
    fetchLogs();
  }, []);

  const fetchLogs = async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/audit-logs/', 'GET');
      setLogs(data || []);
    } catch (err) {
      setError('Failed to load audit logs. You may not have permission.');
    } finally {
      setLoading(false);
    }
  };

  const filtered = actionFilter === 'all'
    ? logs
    : logs.filter((log) => log.action === actionFilter);

  const actionCounts = logs.reduce((acc, log) => {
    acc[log.action] = (acc[log.action] || 0) + 1;
    return acc;
  }, {});

  // Group logs by case ID
  const groupedLogs = filtered.reduce((acc, log) => {
    const caseId = log.case;
    if (!acc[caseId]) {
      acc[caseId] = [];
    }
    acc[caseId].push(log);
    return acc;
  }, {});

  // Sort case groups by most recent activity
  const sortedCaseIds = Object.keys(groupedLogs).sort((a, b) => {
    const aLatest = Math.max(...groupedLogs[a].map(l => new Date(l.created_at).getTime()));
    const bLatest = Math.max(...groupedLogs[b].map(l => new Date(l.created_at).getTime()));
    return bLatest - aLatest;
  });

  if (user?.role !== 'owner') {
    return (
      <div className="page-panel">
        <div className="panel-header">
          <h1>Access Denied</h1>
          <p>Only owners can view audit logs.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-panel">
      <div className="panel-header">
        <h1>Audit Logs</h1>
        <p>Track all actions performed across the platform</p>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <span className="stat-value">{logs.length}</span>
          <span className="stat-label">Total Actions</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{actionCounts.assigned || 0}</span>
          <span className="stat-label">Assignments</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{actionCounts.reply || 0}</span>
          <span className="stat-label">Replies</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{actionCounts.closed || 0}</span>
          <span className="stat-label">Closures</span>
        </div>
      </div>

      {/* Filter Tabs */}
      <div className="filter-tabs glass-panel">
        {['all', 'assigned', 'reassigned', 'closed', 'reply', 'submitted'].map((action) => (
          <button
            key={action}
            className={`tab ${actionFilter === action ? 'active' : ''}`}
            onClick={() => setActionFilter(action)}
          >
            {action === 'all' ? `All (${logs.length})` : `${action} (${actionCounts[action] || 0})`}
          </button>
        ))}
      </div>

      {/* Group by Case Toggle */}
      <div style={{ marginBottom: '24px', display: 'flex', alignItems: 'center', gap: '12px' }}>
        <label style={{ 
          display: 'flex', 
          alignItems: 'center', 
          gap: '10px', 
          cursor: 'pointer',
          color: '#ffffff',
          fontWeight: 600,
          fontSize: '14px'
        }}>
          <input 
            type="checkbox" 
            checked={groupByCase} 
            onChange={(e) => setGroupByCase(e.target.checked)}
            style={{ width: '20px', height: '20px', cursor: 'pointer' }}
          />
          Group by Case ID
        </label>
      </div>

      {/* Log List */}
      <div className="glass-panel" style={{ padding: 0 }}>
        {loading ? (
          <div className="loading-spinner" />
        ) : error ? (
          <div className="form-error" style={{ margin: '1rem' }}>{error}</div>
        ) : filtered.length === 0 ? (
          <p className="empty-state">No audit logs found</p>
        ) : groupByCase ? (
          // Grouped view by Case ID
          <div style={{ padding: 'var(--space-sm)' }}>
            {sortedCaseIds.map((caseId) => (
              <div key={caseId} className="audit-group">
                <div className="audit-group-header">
                  <div className="audit-group-title">
                    <span className="case-id-badge">Case #{caseId}</span>
                  </div>
                  <div className="audit-group-count">
                    {groupedLogs[caseId].length} {groupedLogs[caseId].length === 1 ? 'action' : 'actions'}
                  </div>
                </div>
                <div className="audit-group-items">
                  {groupedLogs[caseId]
                    .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
                    .map((log) => (
                      <div key={log.id} className="audit-item">
                        <div className={`audit-icon ${log.action}`}>
                          {ACTION_ICONS[log.action] || '📋'}
                        </div>
                        <div className="audit-body">
                          <div className="audit-title">
                            <span style={{ textTransform: 'capitalize' }}>{log.action}</span>
                          </div>
                          <div className="audit-detail">{log.details}</div>
                          <div className="audit-time">
                            {log.performer?.username || log.performer?.label || 'System'} ·{' '}
                            {new Date(log.created_at).toLocaleString()}
                          </div>
                        </div>
                      </div>
                    ))}
                </div>
              </div>
            ))}
          </div>
        ) : (
          // Flat view (original)
          <div style={{ padding: 'var(--space-sm)' }}>
            {filtered.map((log) => (
              <div key={log.id} className="audit-item">
                <div className={`audit-icon ${log.action}`}>
                  {ACTION_ICONS[log.action] || '📋'}
                </div>
                <div className="audit-body">
                  <div className="audit-title">
                    <span className="case-id-badge">Case #{log.case}</span> — <span style={{ textTransform: 'capitalize' }}>{log.action}</span>
                  </div>
                  <div className="audit-detail">{log.details}</div>
                  <div className="audit-time">
                    {log.performer?.username || log.performer?.label || 'System'} ·{' '}
                    {new Date(log.created_at).toLocaleString()}
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
