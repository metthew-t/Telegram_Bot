import { useState, useEffect } from 'react';
import { Link, useSearchParams, useNavigate } from 'react-router-dom';
import LoadingButton from '../components/LoadingButton.jsx';

export default function ResetPasswordPage() {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const token = searchParams.get('token');

    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [resetSuccess, setResetSuccess] = useState(false);

    useEffect(() => {
        if (!token) {
            setError('Invalid or missing reset token. Please request a new password reset link.');
        }
    }, [token]);

    const evaluatePasswordStrength = (pass) => {
        if (!pass) return { text: '', color: 'transparent', width: '0%', label: '' };
        
        let score = 0;
        if (pass.length >= 6) score += 1;
        if (pass.length >= 8) score += 1;
        if (/[A-Z]/.test(pass)) score += 1;
        if (/[0-9]/.test(pass)) score += 1;
        if (/[^A-Za-z0-9]/.test(pass)) score += 1;

        if (score <= 1) {
            return { text: 'Weak', color: 'var(--danger)', width: '25%', label: 'Weak' };
        } else if (score <= 3) {
            return { text: 'Moderate', color: '#f59e0b', width: '60%', label: 'Medium' };
        } else {
            return { text: 'Strong', color: 'var(--success)', width: '100%', label: 'Strong' };
        }
    };

    const strength = evaluatePasswordStrength(newPassword);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('');
        setError('');

        if (newPassword !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        if (newPassword.length < 8) {
            setError('Password must be at least 8 characters long.');
            return;
        }

        if (!token) {
            setError('Invalid reset token.');
            return;
        }

        setLoading(true);

        try {
            const response = await fetch('https://telegram-bot-backend-bwu4.onrender.com/api/reset-password/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    token,
                    new_password: newPassword,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                setMessage(data.message || 'Password reset successful!');
                setResetSuccess(true);
                setNewPassword('');
                setConfirmPassword('');
                
                // Redirect to login after 3 seconds
                setTimeout(() => {
                    navigate('/login');
                }, 3000);
            } else {
                setError(data.error || 'Failed to reset password. The link may have expired.');
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
                maxWidth: '520px',
                width: '100%',
                padding: 'var(--space-xl)',
                borderRadius: 'var(--radius-lg)',
                boxShadow: '0 8px 32px rgba(0, 0, 0, 0.4)',
            }}>
                {/* Header */}
                <div style={{ textAlign: 'center', marginBottom: 'var(--space-lg)' }}>
                    <div style={{ fontSize: '48px', marginBottom: 'var(--space-sm)' }}>
                        {resetSuccess ? '✅' : '🔑'}
                    </div>
                    <h1 style={{ fontSize: 'var(--font-2xl)', fontWeight: 800, marginBottom: 'var(--space-xs)', color: 'var(--text-primary)' }}>
                        {resetSuccess ? 'Password Reset!' : 'Reset Password'}
                    </h1>
                    <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)' }}>
                        {resetSuccess 
                            ? 'Your password has been successfully reset.' 
                            : 'Enter your new password below.'
                        }
                    </p>
                </div>

                {/* Success Message */}
                {resetSuccess && (
                    <div style={{
                        padding: 'var(--space-md)',
                        background: 'rgba(16, 185, 129, 0.1)',
                        border: '1px solid rgba(16, 185, 129, 0.3)',
                        borderRadius: 'var(--radius-md)',
                        marginBottom: 'var(--space-lg)',
                        animation: 'fadeIn 0.3s ease-out',
                        textAlign: 'center'
                    }}>
                        <p style={{ color: 'var(--success)', fontWeight: 600, marginBottom: '8px', fontSize: 'var(--font-base)' }}>
                            ✅ {message}
                        </p>
                        <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)' }}>
                            Redirecting to login page...
                        </p>
                    </div>
                )}

                {/* Form */}
                {!resetSuccess && (
                    <form onSubmit={handleSubmit} style={{ marginBottom: 'var(--space-lg)' }}>
                        <div style={{ marginBottom: 'var(--space-md)' }}>
                            <label style={{
                                display: 'block',
                                fontSize: 'var(--font-sm)',
                                fontWeight: 600,
                                marginBottom: '8px',
                                color: 'var(--text-secondary)'
                            }}>
                                New Password
                            </label>
                            <input
                                type="password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                placeholder="Enter minimum 8 characters"
                                required
                                disabled={loading || !token}
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

                        {/* Password Strength Meter */}
                        {newPassword && (
                            <div style={{ marginBottom: 'var(--space-md)', animation: 'fadeIn 0.2s ease-out' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                    <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Strength</span>
                                    <span style={{ fontSize: '11px', color: strength.color, fontWeight: 700 }}>{strength.label}</span>
                                </div>
                                <div style={{ height: '4px', background: 'rgba(255,255,255,0.05)', borderRadius: 'var(--radius-full)', overflow: 'hidden' }}>
                                    <div style={{
                                        height: '100%',
                                        width: strength.width,
                                        background: strength.color,
                                        transition: 'all 0.3s cubic-bezier(0.4, 0, 0.2, 1)'
                                    }} />
                                </div>
                            </div>
                        )}

                        <div style={{ marginBottom: 'var(--space-lg)' }}>
                            <label style={{
                                display: 'block',
                                fontSize: 'var(--font-sm)',
                                fontWeight: 600,
                                marginBottom: '8px',
                                color: 'var(--text-secondary)'
                            }}>
                                Confirm New Password
                            </label>
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                placeholder="Re-enter password to confirm"
                                required
                                disabled={loading || !token}
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
                            disabled={!newPassword || !confirmPassword || newPassword !== confirmPassword || !token || loading}
                            loading={loading}
                            loadingText="Resetting..."
                            style={{ width: '100%' }}
                        >
                            Reset Password
                        </LoadingButton>
                    </form>
                )}

                {/* Footer Link */}
                {!resetSuccess && (
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
                )}

                {/* Security Note */}
                {!resetSuccess && (
                    <div style={{
                        marginTop: 'var(--space-lg)',
                        padding: 'var(--space-md)',
                        background: 'rgba(99, 102, 241, 0.05)',
                        border: '1px solid rgba(99, 102, 241, 0.1)',
                        borderRadius: 'var(--radius-md)'
                    }}>
                        <p style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', lineHeight: 1.5, margin: 0 }}>
                            <strong style={{ color: 'var(--text-secondary)' }}>🔒 Security:</strong> This link can only be used once and will expire 24 hours after it was requested. Choose a strong password with at least 8 characters.
                        </p>
                    </div>
                )}
            </div>
        </div>
    );
}
