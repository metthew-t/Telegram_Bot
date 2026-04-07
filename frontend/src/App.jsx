import { useEffect, useState } from 'react';
import { BrowserRouter, Routes, Route, Link, Navigate, useLocation } from 'react-router-dom';
import LoginPage from './pages/Login.jsx';
import RegisterPage from './pages/Register.jsx';
import DashboardPage from './pages/Dashboard.jsx';
import CaseDetailPage from './pages/CaseDetail.jsx';
import AdminDashboardPage from './pages/AdminDashboard.jsx';
import { getUser, isAuthenticated, logoutUser } from './auth.js';

function ProtectedRoute({ children }) {
  if (!isAuthenticated()) {
    return <Navigate to="/login" replace />;
  }
  return children;
}

function Header({ user, onLogout }) {
  const location = useLocation();
  return (
    <header className="topbar glass-panel">
      <div className="brand">
        <span className="brand-badge">Counsel</span>
        <span>Telegram support</span>
      </div>
      <nav>
        <Link className={location.pathname === '/' ? 'active' : ''} to="/">
          Dashboard
        </Link>
        {user?.role === 'admin' && (
          <Link className={location.pathname === '/admin' ? 'active' : ''} to="/admin">
            Admin Panel
          </Link>
        )}
        {user?.role === 'owner' && (
          <Link className={location.pathname === '/admin' ? 'active' : ''} to="/admin">
            All Cases
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
            <Link className={location.pathname === '/register' ? 'active' : ''} to="/register">
              Register
            </Link>
          </>
        )}
      </nav>
    </header>
  );
}

export default function App() {
  const [user, setUser] = useState(getUser());

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
        <Header user={user} onLogout={handleLogout} />
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
                <ProtectedRoute>
                  <AdminDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={!user ? <LoginPage onLogin={setUser} /> : <Navigate to="/" />} />
            <Route path="/register" element={!user ? <RegisterPage onLogin={setUser} /> : <Navigate to="/" />} />
            <Route path="*" element={<Navigate to={user ? '/' : '/login'} />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
