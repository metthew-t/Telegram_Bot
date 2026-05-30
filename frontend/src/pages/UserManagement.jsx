import { useEffect, useState } from 'react';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';

export default function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const user = getUser();

  useEffect(() => {
    fetchUsers();
  }, []);

  const fetchUsers = async () => {
    setLoading(true);
    try {
      const data = await apiCall('/api/users/', 'GET');
      setUsers(data || []);
    } catch (err) {
      setError('Failed to load users. You may not have permission.');
    } finally {
      setLoading(false);
    }
  };

  const filtered = users.filter((u) => {
    const matchesSearch =
      u.username?.toLowerCase().includes(search.toLowerCase()) ||
      u.email?.toLowerCase().includes(search.toLowerCase()) ||
      (u.telegram_id && u.telegram_id.includes(search));
    const matchesRole = roleFilter === 'all' || u.role === roleFilter;
    return matchesSearch && matchesRole;
  });

  const stats = {
    total: users.length,
    owners: users.filter((u) => u.role === 'owner').length,
    admins: users.filter((u) => u.role === 'admin').length,
    users: users.filter((u) => u.role === 'user').length,
  };

  if (user?.role !== 'owner') {
    return (
      <div className="page-panel">
        <div className="panel-header">
          <h1>Access Denied</h1>
          <p>Only owners can view user management.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-panel">
      <div className="panel-header">
        <h1>User Management</h1>
        <p>Browse and manage all platform users</p>
      </div>

      {/* Stats */}
      <div className="stats-row">
        <div className="stat-card">
          <span className="stat-value">{stats.total}</span>
          <span className="stat-label">Total Users</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.owners}</span>
          <span className="stat-label">Owners</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.admins}</span>
          <span className="stat-label">Admins</span>
        </div>
        <div className="stat-card">
          <span className="stat-value">{stats.users}</span>
          <span className="stat-label">Users</span>
        </div>
      </div>

      {/* Filters */}
      <div className="filter-tabs glass-panel">
        {['all', 'owner', 'admin', 'user'].map((role) => (
          <button
            key={role}
            className={`tab ${roleFilter === role ? 'active' : ''}`}
            onClick={() => setRoleFilter(role)}
          >
            {role === 'all' ? 'All' : role.charAt(0).toUpperCase() + role.slice(1) + 's'}
          </button>
        ))}
      </div>

      {/* Search */}
      <div className="search-bar">
        <input
          type="text"
          placeholder="Search by username, email, or Telegram ID..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
      </div>

      {/* Users Table */}
      <div className="glass-panel" style={{ padding: 0, overflow: 'hidden' }}>
        {loading ? (
          <div className="loading-spinner" />
        ) : error ? (
          <div className="form-error" style={{ margin: '1rem' }}>{error}</div>
        ) : (
          <div className="data-table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Username</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Telegram ID</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.length === 0 ? (
                  <tr>
                    <td colSpan="5" style={{ textAlign: 'center', padding: '2rem' }}>
                      No users found
                    </td>
                  </tr>
                ) : (
                  filtered.map((u) => (
                    <tr key={u.id}>
                      <td>#{u.id}</td>
                      <td style={{ fontWeight: 600, color: 'var(--text-primary)' }}>
                        {u.username}
                      </td>
                      <td>{u.email || '—'}</td>
                      <td>
                        <span className={`role-badge role-${u.role}`}>{u.role}</span>
                      </td>
                      <td style={{ fontFamily: 'monospace', fontSize: 'var(--font-xs)' }}>
                        {u.telegram_id || '—'}
                      </td>
                      <td>
                        {u.id !== user?.id && (
                          <button
                            className="button button-danger button-sm"
                            onClick={async () => {
                              if (window.confirm(`Are you sure you want to delete user ${u.username}?`)) {
                                try {
                                  await apiCall(`/api/users/${u.id}/`, 'DELETE');
                                  fetchUsers();
                                } catch (err) {
                                  alert('Failed to delete user.');
                                }
                              }
                            }}
                          >
                            Delete
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
