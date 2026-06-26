import { useEffect, useState } from 'react';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';
import LoadingButton from '../components/LoadingButton.jsx';

export default function UserManagementPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('all');
  const [deletingId, setDeletingId] = useState(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [addFormData, setAddFormData] = useState({ username: '', email: '', password: '', role: 'admin' });
  const [isAdding, setIsAdding] = useState(false);
  const [addError, setAddError] = useState('');
  const [roleChangingId, setRoleChangingId] = useState(null);
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

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    setAddError('');
    setIsAdding(true);
    try {
      await apiCall('/api/users/', 'POST', addFormData);
      setAddFormData({ username: '', email: '', password: '', role: 'admin' });
      setIsAddModalOpen(false);
      fetchUsers();
    } catch (err) {
      setAddError(err.response?.data?.detail || err.response?.data?.username?.[0] || 'Failed to create user.');
    } finally {
      setIsAdding(false);
    }
  };

  const handleChangeRole = async (userId, newRole) => {
    setRoleChangingId(userId);
    try {
      await apiCall(`/api/users/${userId}/`, 'PATCH', { role: newRole });
      fetchUsers();
    } catch (err) {
      alert(err.response?.data?.detail || 'Failed to change role.');
    } finally {
      setRoleChangingId(null);
    }
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
      <div className="panel-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h1>User Management</h1>
          <p>Browse and manage all platform users</p>
        </div>
        <button className="button button-primary" onClick={() => setIsAddModalOpen(true)}>
          + Add User
        </button>
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
                        {u.id === user?.id ? (
                          <span className={`role-badge role-${u.role}`}>{u.role}</span>
                        ) : (
                          <select
                            className="input"
                            style={{ padding: '0.2rem', fontSize: '0.85rem' }}
                            value={u.role}
                            disabled={roleChangingId === u.id}
                            onChange={(e) => handleChangeRole(u.id, e.target.value)}
                          >
                            <option value="user">User</option>
                            <option value="admin">Admin</option>
                            <option value="owner">Owner</option>
                          </select>
                        )}
                      </td>
                      <td style={{ fontFamily: 'monospace', fontSize: 'var(--font-xs)' }}>
                        {u.telegram_id || '—'}
                      </td>
                      <td>
                        {u.id !== user?.id && (
                          <LoadingButton
                            className="button button-danger button-sm"
                            loading={deletingId === u.id}
                            loadingText="Deleting..."
                            onClick={async () => {
                              if (window.confirm(`Are you sure you want to delete user ${u.username}?`)) {
                                setDeletingId(u.id);
                                try {
                                  await apiCall(`/api/users/${u.id}/`, 'DELETE');
                                  fetchUsers();
                                } catch (err) {
                                  alert('Failed to delete user.');
                                } finally {
                                  setDeletingId(null);
                                }
                              }
                            }}
                          >
                            Delete
                          </LoadingButton>
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

      {/* Add User Modal */}
      {isAddModalOpen && (
        <div className="modal-overlay" onClick={() => !isAdding && setIsAddModalOpen(false)}>
          <div className="modal-content glass-panel" onClick={(e) => e.stopPropagation()}>
            <h2 style={{ marginBottom: '1rem' }}>Add New User</h2>
            {addError && <div className="form-error">{addError}</div>}
            <form onSubmit={handleAddSubmit}>
              <div className="form-group">
                <label>Username</label>
                <input
                  type="text"
                  className="input"
                  required
                  value={addFormData.username}
                  onChange={(e) => setAddFormData({ ...addFormData, username: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Email</label>
                <input
                  type="email"
                  className="input"
                  required
                  value={addFormData.email}
                  onChange={(e) => setAddFormData({ ...addFormData, email: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Password</label>
                <input
                  type="password"
                  className="input"
                  required
                  minLength={8}
                  value={addFormData.password}
                  onChange={(e) => setAddFormData({ ...addFormData, password: e.target.value })}
                />
              </div>
              <div className="form-group">
                <label>Role</label>
                <select
                  className="input"
                  value={addFormData.role}
                  onChange={(e) => setAddFormData({ ...addFormData, role: e.target.value })}
                >
                  <option value="user">User</option>
                  <option value="admin">Admin</option>
                  <option value="owner">Owner</option>
                </select>
              </div>
              <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
                <button
                  type="button"
                  className="button button-outline"
                  onClick={() => setIsAddModalOpen(false)}
                  disabled={isAdding}
                  style={{ flex: 1 }}
                >
                  Cancel
                </button>
                <LoadingButton
                  className="button button-primary"
                  type="submit"
                  loading={isAdding}
                  loadingText="Creating..."
                  style={{ flex: 1 }}
                >
                  Create User
                </LoadingButton>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
