import { useState, useEffect } from 'react';
import { getUser } from '../auth.js';
import { updateProfile, apiCall } from '../api.js';
import LoadingButton from '../components/LoadingButton.jsx';

export default function ProfilePage() {
    const user = getUser();
    const [oldPassword, setOldPassword] = useState('');
    const [password, setPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [message, setMessage] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);
    const [activeSubTab, setActiveSubTab] = useState('security'); // 'security' | 'clearance' | 'notifications'
    const [emailNotificationsEnabled, setEmailNotificationsEnabled] = useState(user?.email_notifications_enabled ?? true);
    const [updatingEmailNotifs, setUpdatingEmailNotifs] = useState(false);
    const [profilePhoto, setProfilePhoto] = useState(user?.profile_photo || null);
    const [uploadingPhoto, setUploadingPhoto] = useState(false);
    
    // Email change states
    const [newEmail, setNewEmail] = useState('');
    const [emailLoading, setEmailLoading] = useState(false);
    const [emailMessage, setEmailMessage] = useState('');
    const [emailError, setEmailError] = useState('');

    // Notification Toggles saved in localStorage
    const [notifs, setNotifs] = useState(() => {
        const saved = localStorage.getItem('telegram_counselling_notifs');
        return saved ? JSON.parse(saved) : {
            telegramRelay: true,
            soundChime: true,
            browserAlert: false,
        };
    });

    // Copy states for credentials
    const [copiedUsername, setCopiedUsername] = useState(false);
    const [copiedRole, setCopiedRole] = useState(false);

    // Responsive window width logic to adapt grid columns
    const [isMobile, setIsMobile] = useState(window.innerWidth < 850);
    useEffect(() => {
        const handleResize = () => {
            setIsMobile(window.innerWidth < 850);
        };
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    const handleToggleNotif = (key) => {
        const updated = { ...notifs, [key]: !notifs[key] };
        setNotifs(updated);
        localStorage.setItem('telegram_counselling_notifs', JSON.stringify(updated));
    };

    const handleCopy = (text, setCopiedState) => {
        navigator.clipboard.writeText(text);
        setCopiedState(true);
        setTimeout(() => setCopiedState(false), 2000);
    };

    const handlePhotoUpload = async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Check file size (max 2MB)
        if (file.size > 2 * 1024 * 1024) {
            setError('Photo size must be less than 2MB');
            return;
        }

        // Check file type
        if (!file.type.startsWith('image/')) {
            setError('Please upload an image file');
            return;
        }

        setUploadingPhoto(true);
        setError('');
        setMessage('');

        try {
            const reader = new FileReader();
            reader.onload = async (event) => {
                const base64Photo = event.target.result;
                
                // Update profile with photo
                const response = await apiCall('/api/profile/', 'PATCH', {
                    profile_photo: base64Photo
                });

                // Update local state immediately
                setProfilePhoto(base64Photo);
                setMessage('Profile photo updated successfully!');
                
                // Update user in localStorage
                const authData = JSON.parse(localStorage.getItem('telegram_counselling_auth') || '{}');
                if (authData.user) {
                    authData.user.profile_photo = base64Photo;
                    localStorage.setItem('telegram_counselling_auth', JSON.stringify(authData));
                }
                
                // Force page refresh to update all instances
                setTimeout(() => {
                    window.location.reload();
                }, 1000);
            };
            reader.readAsDataURL(file);
        } catch (err) {
            setError('Failed to upload photo: ' + (err.message || 'Unknown error'));
            setUploadingPhoto(false);
        }
    };

    const handleRemovePhoto = async () => {
        if (!window.confirm('Remove your profile photo?')) return;

        setUploadingPhoto(true);
        setError('');
        setMessage('');
        
        try {
            await apiCall('/api/profile/', 'PATCH', {
                profile_photo: null
            });

            setProfilePhoto(null);
            setMessage('Profile photo removed');
            
            // Update user in localStorage
            const authData = JSON.parse(localStorage.getItem('telegram_counselling_auth') || '{}');
            if (authData.user) {
                authData.user.profile_photo = null;
                localStorage.setItem('telegram_counselling_auth', JSON.stringify(authData));
            }
            
            // Force page refresh
            setTimeout(() => {
                window.location.reload();
            }, 1000);
        } catch (err) {
            setError('Failed to remove photo: ' + (err.message || 'Unknown error'));
            setUploadingPhoto(false);
        }
    };

    const handleToggleEmailNotifications = async () => {
        setUpdatingEmailNotifs(true);
        try {
            const response = await fetch(`https://telegram-bot-backend-bwu4.onrender.com/api/users/${user.id}/`, {
                method: 'PATCH',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('telegram_counselling_auth') ? JSON.parse(localStorage.getItem('telegram_counselling_auth')).access : ''}`
                },
                body: JSON.stringify({
                    email_notifications_enabled: !emailNotificationsEnabled
                })
            });

            if (response.ok) {
                setEmailNotificationsEnabled(!emailNotificationsEnabled);
                
                // Update user in localStorage
                const authData = JSON.parse(localStorage.getItem('telegram_counselling_auth') || '{}');
                if (authData.user) {
                    authData.user.email_notifications_enabled = !emailNotificationsEnabled;
                    localStorage.setItem('telegram_counselling_auth', JSON.stringify(authData));
                }
            } else {
                alert('Failed to update email notification preferences');
            }
        } catch (err) {
            alert('Error updating email notifications');
        } finally {
            setUpdatingEmailNotifs(false);
        }
    };

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

    const strength = evaluatePasswordStrength(password);

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
            // Use the new change_password endpoint
            const response = await fetch(`https://telegram-bot-backend-bwu4.onrender.com/api/users/${user.id}/change_password/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('telegram_counselling_auth') ? JSON.parse(localStorage.getItem('telegram_counselling_auth')).access : ''}`
                },
                body: JSON.stringify({
                    old_password: oldPassword,
                    new_password: password
                })
            });

            // Check content-type to handle both JSON and HTML responses
            const contentType = response.headers.get('content-type');
            
            if (!response.ok) {
                // If response is HTML (Django error page), extract error or use generic message
                if (contentType && contentType.includes('text/html')) {
                    throw new Error('Failed to update password. Please check your current password.');
                }
                
                const data = await response.json();
                throw new Error(data.error || 'Failed to update password');
            }

            // Parse JSON response only if content-type is JSON
            let data;
            if (contentType && contentType.includes('application/json')) {
                data = await response.json();
            }

            setMessage('Password updated successfully!');
            setOldPassword('');
            setPassword('');
            setConfirmPassword('');
        } catch (err) {
            setError(err.message || 'Failed to update password.');
        } finally {
            setLoading(false);
        }
    };

    const handleEmailChange = async (e) => {
        e.preventDefault();
        setEmailMessage('');
        setEmailError('');

        if (!newEmail || !newEmail.trim()) {
            setEmailError('Email is required');
            return;
        }

        // Validate email format
        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailPattern.test(newEmail)) {
            setEmailError('Invalid email format');
            return;
        }

        setEmailLoading(true);
        try {
            console.log('[EmailChange] Sending request to:', `https://telegram-bot-backend-bwu4.onrender.com/api/users/${user.id}/change-email/`);
            console.log('[EmailChange] Payload:', { email: newEmail.trim().toLowerCase() });
            
            const response = await fetch(`https://telegram-bot-backend-bwu4.onrender.com/api/users/${user.id}/change-email/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('telegram_counselling_auth') ? JSON.parse(localStorage.getItem('telegram_counselling_auth')).access : ''}`
                },
                body: JSON.stringify({
                    email: newEmail.trim().toLowerCase()
                })
            });

            console.log('[EmailChange] Response status:', response.status);

            const contentType = response.headers.get('content-type');
            
            if (!response.ok) {
                if (contentType && contentType.includes('text/html')) {
                    throw new Error('Failed to update email. Please try again.');
                }
                
                const data = await response.json();
                console.error('[EmailChange] Error response:', data);
                throw new Error(data.error || 'Failed to update email');
            }

            const data = await response.json();
            console.log('[EmailChange] Success response:', data);
            setEmailMessage(data.message || 'Email updated successfully!');
            setNewEmail('');
            
            // Update user in localStorage
            const authData = JSON.parse(localStorage.getItem('telegram_counselling_auth') || '{}');
            if (authData.user) {
                authData.user.email = data.email;
                authData.user.email_verified = data.email_verified;
                localStorage.setItem('telegram_counselling_auth', JSON.stringify(authData));
            }
            
            // Refresh page after 2 seconds
            setTimeout(() => {
                window.location.reload();
            }, 2000);
        } catch (err) {
            console.error('[EmailChange] Exception:', err);
            setEmailError(err.message || 'Failed to update email.');
        } finally {
            setEmailLoading(false);
        }
    };

    // Generate dynamic avatar initials from the username
    const getInitials = () => {
        if (!user?.username) return 'U';
        return user.username.slice(0, 2).toUpperCase();
    };

    const roleIsOwner = user?.role === 'owner';

    return (
        <section className="page-panel" style={{ paddingLeft: '20px', paddingRight: '20px' }}>
            <div className="panel-header">
                <h1>My Profile</h1>
                <p>Manage your account settings, platform clearance, and notification alerts</p>
            </div>

            <div style={{
                display: 'grid',
                gridTemplateColumns: isMobile ? '1fr' : '350px 1fr',
                gap: 'var(--space-lg)',
                alignItems: 'start'
            }}>
                
                {/* ─── LEFT PANEL: GLOWING PROFILE CARD ─── */}
                <div className="card glass-panel" style={{
                    padding: 'var(--space-lg)',
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    textAlign: 'center',
                    position: 'relative',
                    overflow: 'hidden'
                }}>
                    {/* Glowing Top-Bar Ornament */}
                    <div style={{
                        position: 'absolute',
                        top: 0,
                        left: 0,
                        right: 0,
                        height: '4px',
                        background: roleIsOwner 
                            ? 'linear-gradient(90deg, #f59e0b, #d97706)' 
                            : 'linear-gradient(90deg, #6366f1, #8b5cf6)'
                    }} />

                    {/* Glowing Circular Avatar - Clickable to Upload */}
                    <div 
                        onClick={() => (user?.role === 'admin' || user?.role === 'owner') && document.getElementById('profile-photo-upload')?.click()}
                        style={{
                            width: '90px',
                            height: '90px',
                            borderRadius: '50%',
                            background: profilePhoto ? `url(${profilePhoto})` : 'rgba(255, 255, 255, 0.03)',
                            backgroundSize: 'cover',
                            backgroundPosition: 'center',
                            border: `2px solid ${roleIsOwner ? 'rgba(245, 158, 11, 0.35)' : 'rgba(99, 102, 241, 0.35)'}`,
                            boxShadow: roleIsOwner 
                                ? '0 0 25px rgba(245, 158, 11, 0.15)' 
                                : '0 0 25px rgba(99, 102, 241, 0.15)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            marginBottom: 'var(--space-md)',
                            position: 'relative',
                            marginTop: 'var(--space-sm)',
                            cursor: (user?.role === 'admin' || user?.role === 'owner') ? 'pointer' : 'default',
                            transition: 'transform 0.2s ease, box-shadow 0.2s ease'
                        }}
                        onMouseEnter={(e) => {
                            if (user?.role === 'admin' || user?.role === 'owner') {
                                e.currentTarget.style.transform = 'scale(1.05)';
                                e.currentTarget.style.boxShadow = roleIsOwner 
                                    ? '0 0 35px rgba(245, 158, 11, 0.3)' 
                                    : '0 0 35px rgba(99, 102, 241, 0.3)';
                            }
                        }}
                        onMouseLeave={(e) => {
                            e.currentTarget.style.transform = 'scale(1)';
                            e.currentTarget.style.boxShadow = roleIsOwner 
                                ? '0 0 25px rgba(245, 158, 11, 0.15)' 
                                : '0 0 25px rgba(99, 102, 241, 0.15)';
                        }}
                    >
                        {!profilePhoto && (
                            <span style={{
                                fontSize: 'var(--font-xl)',
                                fontWeight: 800,
                                letterSpacing: '0.05em',
                                background: roleIsOwner
                                    ? 'linear-gradient(135deg, #f59e0b, #fbbf24)'
                                    : 'linear-gradient(135deg, #6366f1, #818cf8)',
                                WebkitBackgroundClip: 'text',
                                WebkitTextFillColor: 'transparent',
                                backgroundClip: 'text'
                            }}>
                                {getInitials()}
                            </span>
                        )}
                        
                        {/* Camera overlay on hover for admin/owner */}
                        {(user?.role === 'admin' || user?.role === 'owner') && (
                            <div style={{
                                position: 'absolute',
                                top: 0,
                                left: 0,
                                right: 0,
                                bottom: 0,
                                borderRadius: '50%',
                                background: 'rgba(0, 0, 0, 0)',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                fontSize: '24px',
                                opacity: 0,
                                transition: 'all 0.2s ease',
                                pointerEvents: 'none'
                            }}
                            onMouseEnter={(e) => {
                                e.currentTarget.style.opacity = '1';
                                e.currentTarget.style.background = 'rgba(0, 0, 0, 0.7)';
                            }}
                            >
                                📷
                            </div>
                        )}
                        
                        {/* Dynamic Active Indicator Badge */}
                        <div style={{
                            position: 'absolute',
                            bottom: '2px',
                            right: '2px',
                            width: '12px',
                            height: '12px',
                            borderRadius: '50%',
                            background: 'var(--success)',
                            border: '2px solid var(--bg-primary)',
                            boxShadow: '0 0 10px var(--success)'
                        }} />
                    </div>

                    <h2 style={{ fontSize: 'var(--font-lg)', fontWeight: 700, margin: '0 0 var(--space-xs) 0' }}>
                        {user?.username}
                    </h2>

                    {/* Custom Styled Role Badge */}
                    <span style={{
                        display: 'inline-flex',
                        padding: '4px 14px',
                        borderRadius: 'var(--radius-full)',
                        fontSize: 'var(--font-xs)',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                        letterSpacing: '0.08em',
                        marginBottom: 'var(--space-md)',
                        background: roleIsOwner ? 'rgba(245, 158, 11, 0.1)' : 'rgba(99, 102, 241, 0.1)',
                        color: roleIsOwner ? '#fbbf24' : '#818cf8',
                        border: `1px solid ${roleIsOwner ? 'rgba(245, 158, 11, 0.2)' : 'rgba(99, 102, 241, 0.2)'}`,
                        boxShadow: roleIsOwner 
                            ? '0 0 15px rgba(245, 158, 11, 0.08)' 
                            : '0 0 15px rgba(99, 102, 241, 0.08)'
                    }}>
                        🛡️ {user?.role}
                    </span>

                    {/* Photo Upload Buttons (Admin/Owner only) */}
                    {(user?.role === 'admin' || user?.role === 'owner') && (
                        <div style={{ width: '100%', marginBottom: 'var(--space-md)' }}>
                            <input
                                type="file"
                                id="profile-photo-upload"
                                accept="image/*"
                                onChange={handlePhotoUpload}
                                style={{ display: 'none' }}
                            />
                            <div style={{ display: 'flex', gap: '8px', flexDirection: 'column' }}>
                                <button
                                    onClick={() => document.getElementById('profile-photo-upload').click()}
                                    disabled={uploadingPhoto}
                                    className="button button-secondary"
                                    style={{
                                        fontSize: '12px',
                                        padding: '8px 16px',
                                        width: '100%'
                                    }}
                                >
                                    {uploadingPhoto ? '⏳ Uploading...' : profilePhoto ? '📷 Change Photo' : '📷 Upload Photo'}
                                </button>
                                {profilePhoto && (
                                    <button
                                        onClick={handleRemovePhoto}
                                        disabled={uploadingPhoto}
                                        className="button"
                                        style={{
                                            fontSize: '12px',
                                            padding: '8px 16px',
                                            width: '100%',
                                            background: 'rgba(239, 68, 68, 0.1)',
                                            color: '#ef4444',
                                            border: '1px solid rgba(239, 68, 68, 0.3)'
                                        }}
                                    >
                                        🗑️ Remove Photo
                                    </button>
                                )}
                            </div>
                            <p style={{ 
                                fontSize: '11px', 
                                color: 'var(--text-muted)', 
                                marginTop: '8px',
                                textAlign: 'center'
                            }}>
                                Photo visible to staff only
                            </p>
                        </div>
                    )}

                    <hr style={{ width: '100%', margin: '0 0 var(--space-md) 0', border: 'none', borderTop: '1px solid var(--border-subtle)' }} />

                    {/* Quick copy credentials */}
                    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: 'var(--space-sm)' }}>
                        
                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: 'var(--space-xs) var(--space-sm)',
                            background: 'rgba(255,255,255,0.02)',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid rgba(255,255,255,0.03)'
                        }}>
                            <div style={{ textAlign: 'left' }}>
                                <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Username</span>
                                <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--text-primary)' }}>{user?.username}</strong>
                            </div>
                            <button 
                                onClick={() => handleCopy(user?.username || '', setCopiedUsername)}
                                style={{
                                    background: copiedUsername ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.04)',
                                    color: copiedUsername ? 'var(--success)' : 'var(--text-secondary)',
                                    border: `1px solid ${copiedUsername ? 'rgba(16, 185, 129, 0.2)' : 'var(--border-subtle)'}`,
                                    padding: '4px 8px',
                                    borderRadius: 'var(--radius-sm)',
                                    fontSize: '11px',
                                    cursor: 'pointer',
                                    fontWeight: 500,
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                {copiedUsername ? '✓ Copied' : '📋 Copy'}
                            </button>
                        </div>

                        <div style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            padding: 'var(--space-xs) var(--space-sm)',
                            background: 'rgba(255,255,255,0.02)',
                            borderRadius: 'var(--radius-md)',
                            border: '1px solid rgba(255,255,255,0.03)'
                        }}>
                            <div style={{ textAlign: 'left' }}>
                                <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Security Access</span>
                                <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--text-primary)' }}>{user?.role?.toUpperCase()} TOKEN</strong>
                            </div>
                            <button 
                                onClick={() => handleCopy(user?.role || '', setCopiedRole)}
                                style={{
                                    background: copiedRole ? 'rgba(16, 185, 129, 0.1)' : 'rgba(255,255,255,0.04)',
                                    color: copiedRole ? 'var(--success)' : 'var(--text-secondary)',
                                    border: `1px solid ${copiedRole ? 'rgba(16, 185, 129, 0.2)' : 'var(--border-subtle)'}`,
                                    padding: '4px 8px',
                                    borderRadius: 'var(--radius-sm)',
                                    fontSize: '11px',
                                    cursor: 'pointer',
                                    fontWeight: 500,
                                    transition: 'all 0.2s ease'
                                }}
                            >
                                {copiedRole ? '✓ Copied' : '📋 Copy'}
                            </button>
                        </div>
                    </div>
                </div>

                {/* ─── RIGHT PANEL: INTERACTIVE CONTROLS ─── */}
                <div className="card glass-panel" style={{ padding: 'var(--space-lg)' }}>
                    
                    {/* Glassmorphic Secondary Tabs Bar */}
                    <div className="filter-tabs glass-panel" style={{
                        marginBottom: 'var(--space-lg)',
                        background: 'rgba(255, 255, 255, 0.01)',
                        border: '1px solid rgba(255, 255, 255, 0.05)',
                        padding: '4px'
                    }}>
                        <button
                            className={`tab ${activeSubTab === 'security' ? 'active' : ''}`}
                            onClick={() => setActiveSubTab('security')}
                            style={{ padding: '8px 16px', fontSize: 'var(--font-sm)' }}
                        >
                            🔒 Security & Password
                        </button>
                        <button
                            className={`tab ${activeSubTab === 'clearance' ? 'active' : ''}`}
                            onClick={() => setActiveSubTab('clearance')}
                            style={{ padding: '8px 16px', fontSize: 'var(--font-sm)' }}
                        >
                            ⚡ System Clearance
                        </button>
                        <button
                            className={`tab ${activeSubTab === 'notifications' ? 'active' : ''}`}
                            onClick={() => setActiveSubTab('notifications')}
                            style={{ padding: '8px 16px', fontSize: 'var(--font-sm)' }}
                        >
                            🔔 Notifications
                        </button>
                    </div>

                    {/* ──── TAB CONTENT: SECURITY ──── */}
                    {activeSubTab === 'security' && (
                        <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
                            
                            {/* ── EMAIL CHANGE SECTION ── */}
                            <h3 style={{ fontSize: 'var(--font-lg)', marginBottom: 'var(--space-sm)', color: 'var(--text-primary)' }}>
                                Change Email Address
                            </h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)', marginBottom: 'var(--space-md)' }}>
                                Update your email address for notifications and account recovery.
                            </p>

                            <div style={{ 
                                background: 'rgba(99, 102, 241, 0.1)', 
                                border: '1px solid rgba(99, 102, 241, 0.3)',
                                borderRadius: 'var(--radius-md)',
                                padding: 'var(--space-md)',
                                marginBottom: 'var(--space-lg)',
                                marginLeft: '0',
                                marginRight: '0'
                            }}>
                                <div style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)', marginBottom: 'var(--space-sm)' }}>
                                    <strong>Current Email:</strong> {user?.email || 'Not set'}
                                    {user?.email_verified && (
                                        <span style={{ 
                                            marginLeft: 'var(--space-sm)', 
                                            color: 'var(--success)', 
                                            fontSize: '12px',
                                            fontWeight: 600
                                        }}>
                                            ✓ Verified
                                        </span>
                                    )}
                                    {user?.email && !user?.email_verified && (
                                        <span style={{ 
                                            marginLeft: 'var(--space-sm)', 
                                            color: 'var(--warning)', 
                                            fontSize: '12px',
                                            fontWeight: 600
                                        }}>
                                            ⚠ Not Verified
                                        </span>
                                    )}
                                </div>

                                <form onSubmit={handleEmailChange} style={{ marginTop: 'var(--space-md)', padding: '0 10px' }}>
                                    <label style={{ display: 'block', marginBottom: 'var(--space-sm)' }}>
                                        <span style={{ display: 'block', fontSize: 'var(--font-sm)', fontWeight: 500, marginBottom: '6px', color: 'var(--text-secondary)' }}>
                                            New Email Address
                                        </span>
                                        <input
                                            type="email"
                                            value={newEmail}
                                            onChange={(e) => setNewEmail(e.target.value)}
                                            placeholder="Enter your new email"
                                            disabled={emailLoading}
                                            style={{ 
                                                width: 'calc(100% - 20px)',
                                                padding: '12px 16px', 
                                                background: 'rgba(255, 255, 255, 0.03)',
                                                border: '1px solid rgba(255, 255, 255, 0.1)',
                                                borderRadius: 'var(--radius-md)',
                                                color: '#ffffff',
                                                fontSize: '14px',
                                                marginLeft: '0',
                                                marginRight: '0'
                                            }}
                                        />
                                    </label>

                                    {emailMessage && (
                                        <div style={{ 
                                            background: 'rgba(34, 197, 94, 0.1)', 
                                            border: '1px solid rgba(34, 197, 94, 0.3)',
                                            borderRadius: 'var(--radius-md)',
                                            padding: 'var(--space-sm)',
                                            marginTop: 'var(--space-sm)',
                                            color: 'var(--success)',
                                            fontSize: 'var(--font-sm)'
                                        }}>
                                            {emailMessage}
                                        </div>
                                    )}

                                    {emailError && (
                                        <div style={{ 
                                            background: 'rgba(239, 68, 68, 0.1)', 
                                            border: '1px solid rgba(239, 68, 68, 0.3)',
                                            borderRadius: 'var(--radius-md)',
                                            padding: 'var(--space-sm)',
                                            marginTop: 'var(--space-sm)',
                                            color: 'var(--danger)',
                                            fontSize: 'var(--font-sm)'
                                        }}>
                                            {emailError}
                                        </div>
                                    )}

                                    <LoadingButton
                                        type="submit"
                                        loading={emailLoading}
                                        style={{
                                            marginTop: 'var(--space-md)',
                                            background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                                            color: '#ffffff',
                                            padding: '12px 24px',
                                            borderRadius: 'var(--radius-md)',
                                            fontSize: 'var(--font-sm)',
                                            fontWeight: 600,
                                            border: 'none',
                                            cursor: emailLoading ? 'not-allowed' : 'pointer',
                                            opacity: emailLoading ? 0.6 : 1
                                        }}
                                    >
                                        {emailLoading ? 'Updating...' : 'Update Email'}
                                    </LoadingButton>
                                </form>
                            </div>

                            {/* ── PASSWORD CHANGE SECTION ── */}
                            <h3 style={{ fontSize: 'var(--font-lg)', marginBottom: 'var(--space-sm)', color: 'var(--text-primary)', marginTop: 'var(--space-xl)' }}>
                                Change Password
                            </h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)', marginBottom: 'var(--space-lg)' }}>
                                Update your account security credentials regularly. Ensure it is at least 8 characters.
                            </p>

                            <form onSubmit={handleSubmit} className="form-grid">
                                <label style={{ display: 'block', marginBottom: 'var(--space-md)' }}>
                                    <span style={{ display: 'block', fontSize: 'var(--font-sm)', fontWeight: 500, marginBottom: '6px', color: 'var(--text-secondary)' }}>
                                        Current Password
                                    </span>
                                    <input
                                        type="password"
                                        value={oldPassword}
                                        onChange={(e) => setOldPassword(e.target.value)}
                                        placeholder="Enter your current password"
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
                                            marginLeft: '10px',
                                            marginRight: '10px'
                                        }}
                                    />
                                </label>

                                <label style={{ display: 'block', marginBottom: 'var(--space-md)' }}>
                                    <span style={{ display: 'block', fontSize: 'var(--font-sm)', fontWeight: 500, marginBottom: '6px', color: 'var(--text-secondary)' }}>
                                        New Password
                                    </span>
                                    <input
                                        type="password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="Enter minimum 8 characters"
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
                                            marginLeft: '10px',
                                            marginRight: '10px'
                                        }}
                                    />
                                </label>

                                {/* Dynamic Password Strength Meter */}
                                {password && (
                                    <div style={{ marginBottom: 'var(--space-md)', animation: 'fadeIn 0.2s ease-out' }}>
                                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                            <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Strength Checker</span>
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

                                <label style={{ display: 'block', marginBottom: 'var(--space-lg)' }}>
                                    <span style={{ display: 'block', fontSize: 'var(--font-sm)', fontWeight: 500, marginBottom: '6px', color: 'var(--text-secondary)' }}>
                                        Confirm New Password
                                    </span>
                                    <input
                                        type="password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        placeholder="Re-enter password to confirm"
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
                                            marginLeft: '10px',
                                            marginRight: '10px'
                                        }}
                                    />
                                </label>

                                {message && <div style={{ color: 'var(--success)', marginBottom: 'var(--space-md)', fontSize: 'var(--font-sm)', fontWeight: 500 }}>✓ {message}</div>}
                                {error && <div className="form-error" style={{ marginBottom: 'var(--space-md)' }}>⚠️ {error}</div>}

                                <LoadingButton 
                                    className="button button-primary" 
                                    type="submit" 
                                    disabled={!password || (password !== confirmPassword)}
                                    style={{ alignSelf: 'start' }}
                                    loading={loading}
                                    loadingText="Updating Credentials..."
                                >
                                    Update Password
                                </LoadingButton>
                            </form>
                        </div>
                    )}

                    {/* ──── TAB CONTENT: SYSTEM CLEARANCE ──── */}
                    {activeSubTab === 'clearance' && (
                        <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
                            <h3 style={{ fontSize: 'var(--font-lg)', marginBottom: 'var(--space-sm)', color: 'var(--text-primary)' }}>
                                Account Capabilities & Clearance
                            </h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)', marginBottom: 'var(--space-lg)' }}>
                                Review the operations and data access clearance granted to your specific profile.
                            </p>

                            <div style={{
                                background: 'rgba(255, 255, 255, 0.02)',
                                border: '1px solid var(--border-subtle)',
                                borderRadius: 'var(--radius-md)',
                                padding: 'var(--space-md)',
                                marginBottom: 'var(--space-lg)'
                            }}>
                                <strong style={{
                                    display: 'block',
                                    fontSize: 'var(--font-xs)',
                                    color: roleIsOwner ? '#fbbf24' : '#818cf8',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.05em',
                                    marginBottom: 'var(--space-sm)'
                                }}>
                                    Active Permissions
                                </strong>

                                {roleIsOwner ? (
                                    /* Clearance List for Owners */
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 'var(--space-sm)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: 'var(--font-sm)' }}>
                                            <span style={{ color: 'var(--success)' }}>🟢</span>
                                            <span>Full User Database Read/Write Override</span>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: 'var(--font-sm)' }}>
                                            <span style={{ color: 'var(--success)' }}>🟢</span>
                                            <span>Staff Roles & Assignment Administration</span>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: 'var(--font-sm)' }}>
                                            <span style={{ color: 'var(--success)' }}>🟢</span>
                                            <span>System Reports Collection & Audit Log Inspection</span>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: 'var(--font-sm)' }}>
                                            <span style={{ color: 'var(--success)' }}>🟢</span>
                                            <span>Telegram Bot Webhook & Token Overwrites</span>
                                        </div>
                                    </div>
                                ) : (
                                    /* Clearance List for Admins */
                                    <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: 'var(--space-sm)' }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: 'var(--font-sm)' }}>
                                            <span style={{ color: 'var(--success)' }}>🟢</span>
                                            <span>Client Support Thread Interactions</span>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: 'var(--font-sm)' }}>
                                            <span style={{ color: 'var(--success)' }}>🟢</span>
                                            <span>Submit Formal System Reports</span>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: 'var(--font-sm)' }}>
                                            <span style={{ color: 'var(--success)' }}>🟢</span>
                                            <span>View Internal Staff General Chats</span>
                                        </div>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: 'var(--font-sm)' }}>
                                            <span style={{ color: 'var(--text-muted)' }}>🔴</span>
                                            <span style={{ color: 'var(--text-muted)' }}>Staff Credentials Modification (Disabled)</span>
                                        </div>
                                    </div>
                                )}
                            </div>

                            {/* Service Status Monitoring Panel */}
                            <div>
                                <strong style={{
                                    display: 'block',
                                    fontSize: 'var(--font-xs)',
                                    color: 'var(--text-muted)',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.05em',
                                    marginBottom: 'var(--space-sm)'
                                }}>
                                    System Status Indicators
                                </strong>
                                <div style={{
                                    display: 'grid',
                                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                                    gap: 'var(--space-sm)'
                                }}>
                                    <div style={{
                                        padding: 'var(--space-sm)',
                                        background: 'rgba(16, 185, 129, 0.03)',
                                        border: '1px solid rgba(16, 185, 129, 0.15)',
                                        borderRadius: 'var(--radius-sm)',
                                        textAlign: 'center'
                                    }}>
                                        <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Database</span>
                                        <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--success)' }}>ONLINE (sqlite)</strong>
                                    </div>
                                    <div style={{
                                        padding: 'var(--space-sm)',
                                        background: 'rgba(16, 185, 129, 0.03)',
                                        border: '1px solid rgba(16, 185, 129, 0.15)',
                                        borderRadius: 'var(--radius-sm)',
                                        textAlign: 'center'
                                    }}>
                                        <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Backend API</span>
                                        <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--success)' }}>RESPONSIVE</strong>
                                    </div>
                                    <div style={{
                                        padding: 'var(--space-sm)',
                                        background: 'rgba(16, 185, 129, 0.03)',
                                        border: '1px solid rgba(16, 185, 129, 0.15)',
                                        borderRadius: 'var(--radius-sm)',
                                        textAlign: 'center'
                                    }}>
                                        <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase' }}>Telegram Relay</span>
                                        <strong style={{ fontSize: 'var(--font-sm)', color: 'var(--success)' }}>CONNECTED</strong>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ──── TAB CONTENT: NOTIFICATIONS ──── */}
                    {activeSubTab === 'notifications' && (
                        <div style={{ animation: 'fadeIn 0.3s ease-out' }}>
                            <h3 style={{ fontSize: 'var(--font-lg)', marginBottom: 'var(--space-sm)', color: 'var(--text-primary)' }}>
                                Preferences & Alerts
                            </h3>
                            <p style={{ color: 'var(--text-secondary)', fontSize: 'var(--font-sm)', marginBottom: 'var(--space-lg)' }}>
                                Configure how you would like to receive push notifications and platform system alerts.
                            </p>

                            {/* Email Notifications Toggle - Only for Admin/Owner */}
                            {user?.role !== 'user' && (
                                <div style={{
                                    padding: 'var(--space-md)',
                                    background: 'rgba(99, 102, 241, 0.05)',
                                    border: '1px solid rgba(99, 102, 241, 0.2)',
                                    borderRadius: 'var(--radius-md)',
                                    marginBottom: 'var(--space-lg)'
                                }}>
                                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                        <div style={{ flex: 1, paddingRight: 'var(--space-md)' }}>
                                            <strong style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: 'var(--font-base)', color: 'var(--text-primary)', marginBottom: '6px' }}>
                                                <span style={{ fontSize: '20px' }}>📧</span>
                                                Email Notifications
                                            </strong>
                                            <p style={{ fontSize: 'var(--font-sm)', color: 'var(--text-secondary)', margin: 0, lineHeight: 1.5 }}>
                                                Receive email alerts for case messages and system updates. 
                                                {!user?.email_verified && (
                                                    <span style={{ color: '#f59e0b', fontWeight: 600 }}> ⚠️ Email not verified</span>
                                                )}
                                                {user?.email_verified && !user?.email_approved_by_owner && (
                                                    <span style={{ color: '#f59e0b', fontWeight: 600 }}> ⚠️ Awaiting owner approval</span>
                                                )}
                                            </p>
                                        </div>
                                        <button
                                            onClick={handleToggleEmailNotifications}
                                            disabled={updatingEmailNotifs || !user?.email_verified || !user?.email_approved_by_owner}
                                            style={{
                                                width: '56px',
                                                height: '30px',
                                                borderRadius: 'var(--radius-full)',
                                                background: emailNotificationsEnabled ? 'linear-gradient(135deg, #4f46e5, #7c3aed)' : 'rgba(255,255,255,0.08)',
                                                border: 'none',
                                                cursor: (!user?.email_verified || !user?.email_approved_by_owner || updatingEmailNotifs) ? 'not-allowed' : 'pointer',
                                                position: 'relative',
                                                transition: 'all var(--transition-fast) cubic-bezier(0.4, 0, 0.2, 1)',
                                                boxShadow: emailNotificationsEnabled ? '0 0 15px rgba(79, 70, 229, 0.4)' : 'none',
                                                opacity: (!user?.email_verified || !user?.email_approved_by_owner) ? 0.5 : 1
                                            }}
                                            title={
                                                !user?.email_verified ? 'Email must be verified first' :
                                                !user?.email_approved_by_owner ? 'Email must be approved by owner' :
                                                emailNotificationsEnabled ? 'Click to disable' : 'Click to enable'
                                            }
                                        >
                                            <div style={{
                                                width: '24px',
                                                height: '24px',
                                                borderRadius: '50%',
                                                background: '#fff',
                                                position: 'absolute',
                                                top: '3px',
                                                left: emailNotificationsEnabled ? '29px' : '3px',
                                                transition: 'all var(--transition-fast) cubic-bezier(0.4, 0, 0.2, 1)',
                                                display: 'flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                fontSize: '12px'
                                            }}>
                                                {updatingEmailNotifs ? '...' : emailNotificationsEnabled ? '✓' : ''}
                                            </div>
                                        </button>
                                    </div>
                                </div>
                            )}

                            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                                
                                <div style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    padding: 'var(--space-md)',
                                    background: 'rgba(255,255,255,0.01)',
                                    border: '1px solid var(--border-subtle)',
                                    borderRadius: 'var(--radius-md)'
                                }}>
                                    <div style={{ textAlign: 'left', paddingRight: 'var(--space-md)' }}>
                                        <strong style={{ display: 'block', fontSize: 'var(--font-sm)', color: 'var(--text-primary)', marginBottom: '2px' }}>
                                            Telegram Message Relay
                                        </strong>
                                        <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>
                                            Forward alert relays directly through your registered Telegram ID.
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => handleToggleNotif('telegramRelay')}
                                        style={{
                                            width: '50px',
                                            height: '26px',
                                            borderRadius: 'var(--radius-full)',
                                            background: notifs.telegramRelay ? 'var(--accent-primary)' : 'rgba(255,255,255,0.08)',
                                            border: 'none',
                                            cursor: 'pointer',
                                            position: 'relative',
                                            transition: 'all var(--transition-fast) cubic-bezier(0.4, 0, 0.2, 1)',
                                            boxShadow: notifs.telegramRelay ? '0 0 10px rgba(99, 102, 241, 0.3)' : 'none'
                                        }}
                                    >
                                        <div style={{
                                            width: '20px',
                                            height: '20px',
                                            borderRadius: '50%',
                                            background: '#fff',
                                            position: 'absolute',
                                            top: '3px',
                                            left: notifs.telegramRelay ? '27px' : '3px',
                                            transition: 'all var(--transition-fast) cubic-bezier(0.4, 0, 0.2, 1)'
                                        }} />
                                    </button>
                                </div>

                                <div style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    padding: 'var(--space-md)',
                                    background: 'rgba(255,255,255,0.01)',
                                    border: '1px solid var(--border-subtle)',
                                    borderRadius: 'var(--radius-md)'
                                }}>
                                    <div style={{ textAlign: 'left', paddingRight: 'var(--space-md)' }}>
                                        <strong style={{ display: 'block', fontSize: 'var(--font-sm)', color: 'var(--text-primary)', marginBottom: '2px' }}>
                                            Audio Chimes
                                        </strong>
                                        <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>
                                            Play standard notifications sound cues when support clients message.
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => handleToggleNotif('soundChime')}
                                        style={{
                                            width: '50px',
                                            height: '26px',
                                            borderRadius: 'var(--radius-full)',
                                            background: notifs.soundChime ? 'var(--accent-primary)' : 'rgba(255,255,255,0.08)',
                                            border: 'none',
                                            cursor: 'pointer',
                                            position: 'relative',
                                            transition: 'all var(--transition-fast) cubic-bezier(0.4, 0, 0.2, 1)',
                                            boxShadow: notifs.soundChime ? '0 0 10px rgba(99, 102, 241, 0.3)' : 'none'
                                        }}
                                    >
                                        <div style={{
                                            width: '20px',
                                            height: '20px',
                                            borderRadius: '50%',
                                            background: '#fff',
                                            position: 'absolute',
                                            top: '3px',
                                            left: notifs.soundChime ? '27px' : '3px',
                                            transition: 'all var(--transition-fast) cubic-bezier(0.4, 0, 0.2, 1)'
                                        }} />
                                    </button>
                                </div>

                                <div style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    padding: 'var(--space-md)',
                                    background: 'rgba(255,255,255,0.01)',
                                    border: '1px solid var(--border-subtle)',
                                    borderRadius: 'var(--radius-md)'
                                }}>
                                    <div style={{ textAlign: 'left', paddingRight: 'var(--space-md)' }}>
                                        <strong style={{ display: 'block', fontSize: 'var(--font-sm)', color: 'var(--text-primary)', marginBottom: '2px' }}>
                                            Browser Popups
                                        </strong>
                                        <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>
                                            Display operational windows system chimes even when inactive.
                                        </span>
                                    </div>
                                    <button
                                        onClick={() => handleToggleNotif('browserAlert')}
                                        style={{
                                            width: '50px',
                                            height: '26px',
                                            borderRadius: 'var(--radius-full)',
                                            background: notifs.browserAlert ? 'var(--accent-primary)' : 'rgba(255,255,255,0.08)',
                                            border: 'none',
                                            cursor: 'pointer',
                                            position: 'relative',
                                            transition: 'all var(--transition-fast) cubic-bezier(0.4, 0, 0.2, 1)',
                                            boxShadow: notifs.browserAlert ? '0 0 10px rgba(99, 102, 241, 0.3)' : 'none'
                                        }}
                                    >
                                        <div style={{
                                            width: '20px',
                                            height: '20px',
                                            borderRadius: '50%',
                                            background: '#fff',
                                            position: 'absolute',
                                            top: '3px',
                                            left: notifs.browserAlert ? '27px' : '3px',
                                            transition: 'all var(--transition-fast) cubic-bezier(0.4, 0, 0.2, 1)'
                                        }} />
                                    </button>
                                </div>

                            </div>
                        </div>
                    )}

                </div>

            </div>
        </section>
    );
}
