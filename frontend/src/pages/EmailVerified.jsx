import { useNavigate } from 'react-router-dom';

export default function EmailVerifiedPage() {
  const navigate = useNavigate();

  return (
    <section className="page-panel" style={{ minHeight: '60vh', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
      {/* Animated success icon */}
      <div style={{ textAlign: 'center', marginBottom: '24px' }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '88px',
          height: '88px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, rgba(16,185,129,0.15), rgba(16,185,129,0.05))',
          border: '2px solid rgba(16,185,129,0.4)',
          fontSize: '40px',
          animation: 'pulse 2s ease-in-out infinite',
          boxShadow: '0 0 32px rgba(16,185,129,0.2)',
        }}>
          ✅
        </div>
      </div>

      {/* Heading */}
      <div className="panel-header" style={{ textAlign: 'center', paddingTop: 0 }}>
        <h1 style={{ color: '#10b981', marginBottom: '8px' }}>Email Verified!</h1>
        <p style={{
          fontSize: '16px',
          color: '#94a3b8',
          maxWidth: '440px',
          margin: '0 auto',
          lineHeight: 1.7,
        }}>
          Your email address has been successfully verified.
          Your account is now <strong style={{ color: '#e2e8f0' }}>fully activated</strong> — you will
          receive platform notifications going forward.
        </p>
      </div>

      {/* Detail card */}
      <div style={{
        background: 'rgba(16, 185, 129, 0.06)',
        border: '1px solid rgba(16, 185, 129, 0.2)',
        borderRadius: '12px',
        padding: '20px 28px',
        margin: '28px auto',
        maxWidth: '460px',
        width: '100%',
      }}>
        <p style={{ margin: 0, fontSize: '14px', color: '#94a3b8', lineHeight: 1.8 }}>
          <strong style={{ color: '#e2e8f0' }}>🔔 You will now receive email alerts for:</strong>
          <br />
          • New support cases submitted by users<br />
          • New messages on your assigned cases<br />
          • Case assignments and status changes<br />
          • Case closures
        </p>
      </div>

      {/* CTA */}
      <div style={{ textAlign: 'center', marginTop: '8px' }}>
        <button
          id="email-verified-login-btn"
          className="button button-primary"
          onClick={() => navigate('/login')}
          style={{
            padding: '14px 40px',
            fontSize: '15px',
            fontWeight: 700,
            background: 'linear-gradient(135deg, #10b981, #059669)',
            boxShadow: '0 4px 16px rgba(16,185,129,0.3)',
            border: 'none',
          }}
        >
          Log In to Your Account →
        </button>
      </div>

      <p style={{
        textAlign: 'center',
        marginTop: '20px',
        fontSize: '13px',
        color: '#475569',
      }}>
        Need help? Contact your system administrator.
      </p>
    </section>
  );
}
