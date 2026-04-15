import { useState } from 'react';
import { getUser } from '../auth.js';
import { updateProfile } from '../api.js';

export default function ProfilePage() {
    const user = getUser();
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setMessage('');
        setError('');

        if (password !== confirmPassword) {
            setError('Passwords do not match.');
            return;
        }

        if (password.length < 8) {
            setError('Password must be at least 8 characters long.');
            return;
        }

        setLoading(true);
        try {
            await updateProfile(user.id, { password });
            setMessage('Password updated successfully!');
            setPassword('');
            setConfirmPassword('');
        } catch (err) {
            setError(err.response?.data?.password?.[0] || 'Failed to update password.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <section className="page-panel">
            <div className="panel-header">
                <h1>My Profile</h1>
                <p>Manage your account settings and security.</p>
            </div>

            <div className="card glass-panel" style={{ maxWidth: '400px', margin: '0 auto' }}>
                <div style={{ marginBottom: '20px' }}>
                    <strong>Username:</strong> {user?.username}
                </div>
                <div style={{ marginBottom: '20px' }}>
                    <strong>Role:</strong> <span className="badge">{user?.role}</span>
                </div>

                <hr style={{ margin: '20px 0', borderColor: 'rgba(255,255,255,0.1)' }} />

                <h3>Change Password</h3>
                <form onSubmit={handleSubmit} className="form-grid">
                    <label>
                        New Password
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            placeholder="Minimum 8 characters"
                            required
                        />
                    </label>
                    <label>
                        Confirm New Password
                        <input
                            type="password"
                            value={confirmPassword}
                            onChange={(e) => setConfirmPassword(e.target.value)}
                            required
                        />
                    </label>

                    {message && <div style={{ color: '#4caf50', marginBottom: '10px' }}>{message}</div>}
                    {error && <div className="form-error">{error}</div>}

                    <button className="button button-primary" type="submit" disabled={loading}>
                        {loading ? 'Updating...' : 'Update Password'}
                    </button>
                </form>
            </div>
        </section>
    );
}
