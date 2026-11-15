import { Link, useLocation } from 'react-router-dom';

export default function Sidebar({ isOpen, onClose, user, onLogout }) {
  const location = useLocation();

  if (!user) return null;

  const isOwner = user.role === 'owner';
  const isAdmin = user.role === 'admin';
  const isAdminOrOwner = isOwner || isAdmin;

  const navItems = [];

  // Primary Role Dashboard
  if (isOwner) {
    navItems.push({ to: '/owner', label: 'Owner Tower', icon: '👑' });
  } else if (isAdmin) {
    navItems.push({ to: '/admin', label: 'Admin Panel', icon: '🛡️' });
  } else {
    navItems.push({ to: '/dashboard', altTo: '/', label: 'My Cases', icon: '📊' });
  }

  // Owner Controls
  if (isOwner) {
    navItems.push({ to: '/users', label: 'Users', icon: '👥' });
    navItems.push({ to: '/audit-logs', label: 'Audit Logs', icon: '📋' });
    navItems.push({ to: '/settings', label: 'System Settings', icon: '⚙️' });
  }

  // Staff Operations
  if (isAdminOrOwner) {
    navItems.push({ to: '/system-chat', label: 'System Chat', icon: '💬' });
    navItems.push({ to: '/analytics', label: 'Analytics', icon: '📈' });
  }

  // User View (optional alternate for admins/owners to see user perspective)
  if (isAdminOrOwner) {
    navItems.push({ to: '/', label: 'User Cases View', icon: '📑' });
  }

  // Profile (All users)
  navItems.push({ to: '/profile', label: 'Profile', icon: '👤' });

  const isActive = (item) => {
    if (location.pathname === item.to) return true;
    if (item.altTo && location.pathname === item.altTo) return true;
    return false;
  };

  return (
    <>
      {/* Mobile Backdrop Overlay */}
      <div
        className={`sidebar-overlay ${isOpen ? 'open' : ''}`}
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Sidebar Container */}
      <aside className={`sidebar-container ${isOpen ? 'open' : ''}`}>
        {/* Sidebar Header / Brand */}
        <div className="sidebar-header">
          <Link to={isOwner ? '/owner' : isAdmin ? '/admin' : '/'} className="sidebar-brand" onClick={onClose}>
            <span className="sidebar-brand-badge">Counsel</span>
            <span className="sidebar-brand-title">Support</span>
          </Link>
          <button className="sidebar-close-btn" onClick={onClose} aria-label="Close menu">
            ✕
          </button>
        </div>

        {/* User Mini Profile Card */}
        <div className="sidebar-user-card">
          <div className="sidebar-user-avatar">
            {user.username ? user.username.charAt(0).toUpperCase() : 'U'}
          </div>
          <div className="sidebar-user-details">
            <div className="sidebar-username">{user.username}</div>
            <span className={`sidebar-role-badge role-${user.role}`}>
              {user.role === 'owner' ? '👑 OWNER' : user.role === 'admin' ? '🛡️ ADMIN' : '👤 USER'}
            </span>
          </div>
        </div>

        {/* Navigation Items */}
        <nav className="sidebar-nav">
          <div className="sidebar-section-title">NAVIGATION</div>
          {navItems.map((item) => {
            const active = isActive(item);
            return (
              <Link
                key={item.to}
                to={item.to}
                className={`sidebar-nav-item ${active ? 'active' : ''}`}
                onClick={onClose}
              >
                <span className="sidebar-nav-icon">{item.icon}</span>
                <span className="sidebar-nav-label">{item.label}</span>
                {active && <span className="sidebar-active-indicator" />}
              </Link>
            );
          })}
        </nav>

        {/* Sidebar Footer with Logout */}
        <div className="sidebar-footer">
          <button
            className="sidebar-logout-btn"
            onClick={() => {
              onClose();
              onLogout();
            }}
          >
            <span style={{ fontSize: '16px' }}>🚪</span>
            <span>LOGOUT</span>
          </button>
        </div>
      </aside>
    </>
  );
}

