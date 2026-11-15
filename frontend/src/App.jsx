import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import LoginPage from './pages/Login.jsx';
import RegisterPage from './pages/Register.jsx';
import DashboardPage from './pages/Dashboard.jsx';
import CaseDetailPage from './pages/CaseDetail.jsx';
import AdminDashboardPage from './pages/AdminDashboard.jsx';
import OwnerDashboardPage from './pages/OwnerDashboard.jsx';
import UserManagementPage from './pages/UserManagement.jsx';
import AuditLogsPage from './pages/AuditLogs.jsx';
import ProfilePage from './pages/Profile.jsx';
import SystemChatPage from './pages/SystemChat.jsx';
import EmailVerifiedPage from './pages/EmailVerified.jsx';
import ForgotPasswordPage from './pages/ForgotPassword.jsx';
import ResetPasswordPage from './pages/ResetPassword.jsx';
import AnalyticsPage from './pages/Analytics.jsx';
import SettingsPage from './pages/Settings.jsx';
import Sidebar from './components/Sidebar.jsx';
import { getUser, isAuthenticated, logoutUser } from './auth.js';

function ProtectedRoute({ children, requiredRole }) {
  const user = getUser();
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  if (requiredRole && user?.role !== requiredRole) {
    return <Navigate to="/" replace />;
  }
  return children;
}

function Header({ user, onLogout, selectedRole, onToggleSidebar }) {
  const location = useLocation();
  const isLoginPage = location.pathname === '/login';

  return (
    <header className={`topbar glass-panel ${user ? 'topbar-logged-in' : ''}`}>
      <div className="topbar-left">
        {user && (
          <button
            type="button"
            className="sidebar-toggle-btn"
            onClick={onToggleSidebar}
            aria-label="Toggle navigation menu"
          >
            <span className="hamburger-line" />
            <span className="hamburger-line" />
            <span className="hamburger-line" />
          </button>
        )}
        <Link to={user?.role === 'owner' ? '/owner' : user?.role === 'admin' ? '/admin' : '/'} className="brand" style={{ textDecoration: 'none' }}>
          <span className="brand-badge">Counsel</span>
          <span className="brand-subtitle" style={{ color: '#ffffff', fontWeight: 700 }}>Telegram Support</span>
        </Link>
      </div>

      <nav className="topbar-nav">
        {user ? (
          <div className="topbar-user-section" style={{ display: 'flex', alignItems: 'center', flexShrink: 0, gap: '6px' }}>
            <Link to="/profile" className="topbar-user-badge" title="Go to profile" style={{ display: 'flex', alignItems: 'center', flexShrink: 0, textDecoration: 'none' }}>
              <span className="topbar-avatar">{user.username ? user.username.charAt(0).toUpperCase() : 'U'}</span>
              <span className="topbar-username">{user.username}</span>
              <span className={`topbar-role-pill role-${user.role}`}>
                {user.role === 'owner' ? '👑 Owner' : user.role === 'admin' ? '🛡️ Admin' : '👤 User'}
              </span>
            </Link>
            <button className="button button-danger logout-btn" onClick={onLogout} style={{ flexShrink: 0, width: 'auto' }}>
              LOGOUT
            </button>
          </div>
        ) : (
          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            <Link 
              className="button" 
              style={{ 
                background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', 
                color: '#ffffff', 
                border: '2px solid #10b981', 
                fontWeight: '700',
                boxShadow: '0 0 20px rgba(16, 185, 129, 0.4)',
                textShadow: 'none'
              }} 
              to="/login"
            >
              LOGIN
            </Link>
            {(!isLoginPage || selectedRole !== 'owner') && (
              <Link 
                className="button" 
                style={{ 
                  background: 'linear-gradient(135deg, #10b981 0%, #059669 100%)', 
                  color: '#ffffff', 
                  border: '2px solid #10b981', 
                  fontWeight: '700',
                  boxShadow: '0 0 20px rgba(16, 185, 129, 0.4)',
                  textShadow: 'none'
                }} 
                to="/register"
              >
                REGISTER
              </Link>
            )}
          </div>
        )}
      </nav>
    </header>
  );
}

export default function App() {
  const [user, setUser] = useState(getUser());
  const [selectedRole, setSelectedRole] = useState('admin');
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);

  useEffect(() => {
    const listener = () => setUser(getUser());
    window.addEventListener('storage', listener);
    return () => window.removeEventListener('storage', listener);
  }, []);

  const handleLogout = () => {
    logoutUser();
    setUser(null);
    setIsSidebarOpen(false);
  };

  return (
    <BrowserRouter>
      <div className="app-shell">
        <Sidebar
          isOpen={isSidebarOpen}
          onClose={() => setIsSidebarOpen(false)}
          user={user}
          onLogout={handleLogout}
        />
        <Header
          user={user}
          onLogout={handleLogout}
          selectedRole={selectedRole}
          onToggleSidebar={() => setIsSidebarOpen((prev) => !prev)}
        />
        <main className={`page-content ${user ? 'with-sidebar' : ''}`}>
          <Routes>
            <Route
              path="/"
              element={
                <ProtectedRoute>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/cases/:id"
              element={
                <ProtectedRoute>
                  <CaseDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/admin"
              element={
                <ProtectedRoute requiredRole="admin">
                  <AdminDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/owner"
              element={
                <ProtectedRoute requiredRole="owner">
                  <OwnerDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/all-cases"
              element={
                <ProtectedRoute requiredRole="owner">
                  {/* Reuse AdminDashboard for 'All Cases' view if needed, or create new */}
                  <AdminDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/users"
              element={
                <ProtectedRoute requiredRole="owner">
                  <UserManagementPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/audit-logs"
              element={
                <ProtectedRoute requiredRole="owner">
                  <AuditLogsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/settings"
              element={
                <ProtectedRoute requiredRole="owner">
                  <SettingsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/system-chat"
              element={
                <ProtectedRoute>
                  <SystemChatPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/analytics"
              element={
                <ProtectedRoute>
                  <AnalyticsPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/profile"
              element={
                <ProtectedRoute>
                  <ProfilePage />
                </ProtectedRoute>
              }
            />
            <Route path="/email-verified" element={<EmailVerifiedPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/register" element={!user ? <RegisterPage onLogin={setUser} /> : <Navigate to="/" />} />
            <Route path="/login" element={!user ? <LoginPage onLogin={setUser} selectedRole={selectedRole} setSelectedRole={setSelectedRole} /> : <Navigate to={user?.role === 'owner' ? '/owner' : (user?.role === 'admin' ? '/admin' : '/')} />} />
            <Route path="*" element={<Navigate to={user?.role === 'owner' ? '/owner' : (user?.role === 'admin' ? '/admin' : '/')} />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
