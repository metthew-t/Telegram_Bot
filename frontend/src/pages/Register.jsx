import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { register } from '../api.js';
import LoadingButton from '../components/LoadingButton.jsx';

export default function RegisterPage() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [registered, setRegistered] = useState(false);
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    setError('');
    setLoading(true);

    try {
      await register({ username, email, password, role: 'admin' });
      // Don't auto-login — show "check your email" screen instead
      setRegistered(true);
    } catch (err) {
      if (err.response?.data) {
        const data = err.response.data;
        const msg =
          data.detail ||
          data.error ||
          (data.username ? `Username: ${data.username[0]}` : null) ||
          (data.password ? `Password: ${data.password[0]}` : null) ||
          (data.email ? `Email: ${data.email[0]}` : null) ||
          (data.role ? `Role: ${data.role[0]}` : null) ||
          'Unable to register.';
        setError(msg);
      } else {
        setError('Connection error. Is the backend running?');
      }
    } finally {
      setLoading(false);
    }
  };

  /* ── Success state: pending manual verification ────────────────────────── */
  if (registered) {
    return (
      <section className="page-panel">
        <div className="panel-header" style={{ textAlign: 'center' }}>
          <div style={{
            fontSize: '56px',
            marginBottom: '16px',
            animation: 'pulse 2s infinite',
          }}>⏳</div>
          <h1 style={{ color: 'var(--color-accent, #818cf8)' }}>Pending Verification</h1>
          <p style={{ maxWidth: '460px', margin: '12px auto 0', lineHeight: 1.7, color: '#475569' }}>
            Your account has been successfully created.
            <br /><br />
            However, for security reasons, <strong style={{ color: 'var(--color-text, #e2e8f0)' }}>
              your account must be manually verified
            </strong> by an administrator before you can log in.
          </p>
        </div>

        <div style={{
          background: 'rgba(79, 70, 229, 0.08)',
          border: '1px solid rgba(79, 70, 229, 0.25)',
          borderRadius: '12px',
          padding: '20px 24px',
          margin: '28px auto',
          maxWidth: '460px',
        }}>
          <p style={{ margin: 0, fontSize: '14px', color: 'var(--color-muted, #94a3b8)', lineHeight: 1.7 }}>
            <strong style={{ color: 'var(--color-text, #e2e8f0)' }}>📋 Next steps:</strong>
            <br />
            1. Wait for an administrator to approve your account.<br />
            2. Once approved, you will be able to log in.<br />
            3. Contact the system owner if your account remains unverified.
          </p>
        </div>

        {error && <div className="form-error" style={{ maxWidth: '460px', margin: '0 auto 16px' }}>{error}</div>}

        <div style={{ textAlign: 'center', display: 'flex', gap: '12px', justifyContent: 'center', flexWrap: 'wrap', marginTop: '8px' }}>
          <button
            className="button button-primary"
            onClick={() => navigate('/login')}
          >
            Go to Login
          </button>
        </div>
      </section>
    );
  }


  /* ── Registration form ─────────────────────────────────────────────────── */
  return (
    <section className="page-panel">
      <div className="panel-header">
        <h1>Support Staff Registration</h1>
        <p style={{ color: '#475569' }}>Create an account to join the support team and manage cases.</p>
      </div>

      <form className="form-grid" onSubmit={handleSubmit}>
        <label>
          Username
          <input
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            required
            autoComplete="username"
          />
        </label>

        <label>
          Email Address
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            placeholder="you@example.com"
            autoComplete="email"
          />
        </label>

        <label>
          Password
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            autoComplete="new-password"
          />
        </label>

        <div style={{
          background: 'rgba(245, 158, 11, 0.08)',
          border: '1px solid rgba(245, 158, 11, 0.25)',
          borderRadius: '8px',
          padding: '12px 16px',
          fontSize: '13px',
          color: '#94a3b8',
          lineHeight: 1.6,
        }}>
          ⚠️ After registering, your account must be <strong style={{ color: '#e2e8f0' }}>manually verified</strong> by an administrator before you can log in and receive notifications.
        </div>

        {error && <div className="form-error">{error}</div>}

        <LoadingButton
          className="button button-primary"
          type="submit"
          loading={loading}
          loadingText="Creating account..."
        >
          Register Account
        </LoadingButton>
      </form>
    </section>
  );
}
