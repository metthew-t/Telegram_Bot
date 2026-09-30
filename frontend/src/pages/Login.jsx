import { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { login } from '../api.js';
import { saveAuth } from '../auth.js';
import LoadingButton from '../components/LoadingButton.jsx';

export default function LoginPage({ onLogin, selectedRole, setSelectedRole }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMessage, setSuccessMessage] = useState('');
  const navigate = useNavigate();
  const location = useLocation();

  // Check if user just came from email verification
  useEffect(() => {
    if (location.state?.emailVerified) {
      setSuccessMessage('Your email has been verified successfully! You can now log in.');
      // Clear the state after showing message
      window.history.replaceState({}, document.title);
    }
  }, [location]);

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);
    try {
      const data = await login({ username, password });

      if (data.user.role !== selectedRole) {
        setError(`Access denied. You are not recorded as a ${selectedRole}.`);
        return;
      }

      saveAuth(data);
      onLogin(data.user);

      if (data.user.role === 'owner') {
        navigate('/owner');
      } else if (data.user.role === 'admin') {
        navigate('/admin');
      } else {
        navigate('/');
      }
    } catch (err) {
      setError(err.response?.data?.error || 'Unable to login.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="page-panel">
      <div className="panel-header">
        <h1>Welcome back</h1>
        <p style={{ color: '#475569' }}>Use your credentials to access the support dashboard.</p>
      </div>

      {successMessage && (
        <div style={{
          padding: '16px 20px',
          background: 'rgba(16, 185, 129, 0.12)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '10px',
          color: '#10b981',
          fontSize: '14px',
          fontWeight: '500',
          marginBottom: '24px',
          animation: 'fadeSlideUp 0.4s ease-out',
          display: 'flex',
          alignItems: 'center',
          gap: '10px',
        }}>
          <span style={{ fontSize: '20px' }}>✅</span>
          {successMessage}
        </div>
      )}

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          Username
          <input value={username} onChange={(event) => setUsername(event.target.value)} required />
        </label>

        <div className="role-selector">
          <label className="radio-label">
            <input type="radio" value="admin" checked={selectedRole === 'admin'} onChange={() => setSelectedRole('admin')} />
            Admin
          </label>
          <label className="radio-label">
            <input type="radio" value="owner" checked={selectedRole === 'owner'} onChange={() => setSelectedRole('owner')} />
            Owner
          </label>
        </div>

        <label>
          Password
          <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
        </label>

        {/* Forgot Password Link */}
        <div style={{ textAlign: 'right', marginTop: '-8px', marginBottom: '8px' }}>
          <a 
            href="/forgot-password" 
            style={{ 
              color: 'var(--accent-primary)', 
              fontSize: 'var(--font-sm)', 
              textDecoration: 'none',
              fontWeight: 500
            }}
          >
            Forgot password?
          </a>
        </div>

        {error && <div className="form-error">{error}</div>}

        <LoadingButton
          className="button button-primary"
          type="submit"
          loading={loading}
          loadingText="Signing in..."
        >
          Login
        </LoadingButton>
      </form>
    </section>
  );
}
