import { useState } from 'react';
import { Link } from 'react-router-dom';
import LoadingButton from '../components/LoadingButton.jsx';

export default function ForgotPasswordPage() {
    const [email, setEmail] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [emailSent, setEmailSent] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('');
        setError('');
        setLoading(true);

        try {
            const response = await fetch('https://telegram-bot-backend-bwu4.onrender.com/api/forgot-password/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ email: email.trim().toLowerCase() }),
            });

            const data = await response.json();

            if (response.ok) {
                setMessage(data.message || 'If that email is registered, a password reset link has been sent.');
                setEmailSent(true);
                setEmail('');
            } else {
                setError(data.error || 'Failed to send reset email. Please try again.');
            }
        } catch (err) {
            setError('Network error. Please check your connection and try again.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{
            minHeight: '100vh',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'linear-gradient(135deg, #0f1117 0%, #1a1d27 100%)',
            padding: 'var(--space-lg)'
        }}>
            <div className="glass-panel" style={{
                maxWidth: '480px',
                width: '100%',
                padding: 'var(--space-xl)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
            }}>
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: 'var(--space-lg)' }}>
                    <div style={{ fontSize: '48px', marginBottom: 'var(--space-sm)' }}>🔐</div>
                    <h1 style={{ fontSize: 'var(--font-2xl)', fontWeight: 800, marginBottom: 'var(--space-xs)', color: 'var(--text-primary)' }}>
                        Forgot Password
                    </h1>
                    <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>
                        Enter your email address and we'll send you a link to reset your password.
                    </p>
                </div>

                {/* Success Message */}
                {emailSent && (
                    <div style={{
                        padding: 'var(--space-md)',
                        background: 'rgba(16, 185, 129, 0.1)',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        borderRadius: 'var(--radius-md)',
                        marginBottom: 'var(--space-lg)',
                        animation: 'fadeIn 0.3s ease-out'
                    }}>
                        <div style={{ display: 'flex', alignItems: 'flex-start', gap: 'var(--space-sm)' }}>
                            <span style={{ fontSize: '20px' }}>✅</span>
                            <div>
                                <p style={{ color: 'var(--success)', fontWeight: 600, marginBottom: '4px', fontSize: 'var(--font-sm)' }}>
                                    Email Sent Successfully!
                                </p>
                                <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-xs)', lineHeight: 1.5 }}>
                                    {message}
                                    <br /><br />
                                    Please check your inbox (and spam folder) for the reset link. The link will expire in 24 hours.
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* Form */}
                {!emailSent && (
                    <form onSubmit={handleSubmit} style={{ marginBottom: 'var(--space-lg)' }}>
                        <div style={{ marginBottom: 'var(--space-md)' }}>
                            <label style={{
                                display: 'block',
                                fontSize: 'var(--font-sm)',
                                fontWeight: 600,
                                marginBottom: '8px',
                                color: 'var(--text-secondary)'
                            }}>
                                Email Address
                            </label>
                            <input
                                type="email"
                                value={email}
                                onChange={(e) => setEmail(e.target.value)}
                                placeholder="admin@example.com"
                                required
                                disabled={loading}
                                style={{
                                    width: '100%',
                                    padding: '12px 16px',
                                    background: 'rgba(255, 255, 255, 0.03)',
                                    border: '1px solid rgba(255, 255, 255, 0.1)',
                                    borderRadius: 'var(--radius-md)',
                                    color: '#ffffff',
                                    fontSize: '14px',
                                }}
                            />
                        </div>

                        {error && (
                            <div className="form-error" style={{ marginBottom: 'var(--space-md)' }}>
                                ⚠️ {error}
                            </div>
                        )}

                        <LoadingButton
                            type="submit"
                            className="button button-primary"
                            disabled={!email.trim() || loading}
                            loading={loading}
                            loadingText="Sending..."
                            style={{ width: '100%', marginTop: 'var(--space-sm)' }}
                        >
                            Send Reset Link
                        </LoadingButton>
                    </form>
                )}

                {/* Footer Links */}
                <div style={{
                    paddingTop: 'var(--space-md)',
                    borderTop: '1px solid rgba(255, 255, 255, 0.05)',
                    textAlign: 'center'
                }}>
                    <Link
                        to="/login"
                        style={{
                            color: 'var(--accent-primary)',
                            fontSize: 'var(--font-sm)',
                            fontWeight: 500,
                            textDecoration: 'none',
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '4px'
                        }}
                    >
                        ← Back to Login
                    </Link>
                </div>

                {/* Info Note */}
                <div style={{
                    marginTop: 'var(--space-lg)',
                    padding: 'var(--space-md)',
                    background: 'rgba(99, 102, 241, 0.05)',
                    border: '1px solid rgba(99, 102, 241, 0.1)',
                    borderRadius: 'var(--radius-md)'
                }}>
                    <p style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', lineHeight: 1.5, margin: 0 }}>
                        <strong style={{ color: 'var(--text-secondary)' }}>Note:</strong> Password reset is only available for administrators and owners. Regular users should contact support if they need assistance.
                    </p>
                </div>
            </div>
        </div>
    );
}
