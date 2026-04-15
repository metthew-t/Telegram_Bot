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

function Header({ user, onLogout, selectedRole }) {
  const location = useLocation();
  const isAdminOrOwner = user?.role === 'admin' || user?.role === 'owner';
  const isOwner = user?.role === 'owner';
  const isLoginPage = location.pathname === '/login';

  return (
    <header className="topbar glass-panel">
      <div className="brand">
        <span className="brand-badge">Counsel</span>
        <span>Telegram Support</span>
      </div>
      <nav>
        {user && (
          <Link className={location.pathname === '/' ? 'active' : ''} to="/">
            Dashboard
          </Link>
        )}
        {user && (
          <Link className={location.pathname === '/profile' ? 'active' : ''} to="/profile">
            Profile
          </Link>
        )}
        {user?.role === 'admin' && (
          <Link className={location.pathname === '/admin' ? 'active' : ''} to="/admin">
            Admin Panel
          </Link>
        )}
        {user?.role === 'owner' && (
          <Link className={location.pathname === '/owner' ? 'active' : ''} to="/owner">
            Owner Tower
          </Link>
        )}
        {isOwner && (
          <>
            <Link className={location.pathname === '/users' ? 'active' : ''} to="/users">
              Users
            </Link>
            <Link className={location.pathname === '/audit-logs' ? 'active' : ''} to="/audit-logs">
              Audit Logs
            </Link>
          </>
        )}
        {isAdminOrOwner && (
          <Link className={location.pathname === '/system-chat' ? 'active' : ''} to="/system-chat">
            System Chat
          </Link>
        )}
        {user ? (
          <button className="button button-secondary" onClick={onLogout}>
            Logout
          </button>
        ) : (
          <>
            <Link className={location.pathname === '/login' ? 'active' : ''} to="/login">
              Login
            </Link>
            {(!isLoginPage || selectedRole !== 'owner') && (
              <Link className={location.pathname === '/register' ? 'active' : ''} to="/register">
                Register
              </Link>
            )}
          </>
        )}
      </nav>
    </header>
  );
}

export default function App() {
  const [user, setUser] = useState(getUser());
  const [selectedRole, setSelectedRole] = useState('admin');

  useEffect(() => {
    const listener = () => setUser(getUser());
    window.addEventListener('storage', listener);
    return () => window.removeEventListener('storage', listener);
  }, []);

  const handleLogout = () => {
    logoutUser();
    setUser(null);
  };

  return (
    <BrowserRouter>
      <div className="app-shell">
        <Header user={user} onLogout={handleLogout} selectedRole={selectedRole} />
        <main className="page-content">
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
              path="/system-chat"
              element={
                <ProtectedRoute>
                  <SystemChatPage />
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
            <Route path="/register" element={!user ? <RegisterPage onLogin={setUser} /> : <Navigate to="/" />} />
            <Route path="/login" element={!user ? <LoginPage onLogin={setUser} selectedRole={selectedRole} setSelectedRole={setSelectedRole} /> : <Navigate to={user?.role === 'owner' ? '/owner' : (user?.role === 'admin' ? '/admin' : '/')} />} />
            <Route path="*" element={<Navigate to={user?.role === 'owner' ? '/owner' : (user?.role === 'admin' ? '/admin' : '/')} />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
