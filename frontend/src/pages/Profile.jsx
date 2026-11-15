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

    // Username change states
    const [newUsername, setNewUsername] = useState('');
    const [usernameLoading, setUsernameLoading] = useState(false);
    const [usernameMessage, setUsernameMessage] = useState('');
    const [usernameError, setUsernameError] = useState('');

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
    const [isMobile, setIsMobile] = useState(window.innerWidth < 900);
    useEffect(() => {
        const handleResize = () => {
            setIsMobile(window.innerWidth < 900);
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
        if (!text) return;
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
                
                await apiCall('/api/profile/', 'PATCH', {
                    profile_photo: base64Photo
                });

                setProfilePhoto(base64Photo);
                setMessage('Profile photo updated successfully!');
                
                const authData = JSON.parse(localStorage.getItem('telegram_counselling_auth') || '{}');
                if (authData.user) {
                    authData.user.profile_photo = base64Photo;
                    localStorage.setItem('telegram_counselling_auth', JSON.stringify(authData));
                }
                
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
            
            const authData = JSON.parse(localStorage.getItem('telegram_counselling_auth') || '{}');
            if (authData.user) {
                authData.user.profile_photo = null;
                localStorage.setItem('telegram_counselling_auth', JSON.stringify(authData));
            }
            
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
            return { text: 'Weak', color: '#ef4444', width: '25%', label: 'Weak' };
        } else if (score <= 3) {
            return { text: 'Moderate', color: '#f59e0b', width: '60%', label: 'Medium' };
        } else {
            return { text: 'Strong', color: '#10b981', width: '100%', label: 'Strong' };
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

            const contentType = response.headers.get('content-type');
            if (!response.ok) {
                if (contentType && contentType.includes('text/html')) {
                    throw new Error('Failed to update password. Please check your current password.');
                }
                const data = await response.json();
                throw new Error(data.error || 'Failed to update password');
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

        const emailPattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        if (!emailPattern.test(newEmail)) {
            setEmailError('Invalid email format');
            return;
        }

        setEmailLoading(true);
        try {
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

            const contentType = response.headers.get('content-type');
            if (!response.ok) {
                if (contentType && contentType.includes('text/html')) {
                    throw new Error('Failed to update email. Please try again.');
                }
                const data = await response.json();
                throw new Error(data.error || 'Failed to update email');
            }

            const data = await response.json();
            setEmailMessage(data.message || 'Email updated successfully!');
            setNewEmail('');
            
            const authData = JSON.parse(localStorage.getItem('telegram_counselling_auth') || '{}');
            if (authData.user) {
                authData.user.email = data.email;
                authData.user.email_verified = data.email_verified;
                localStorage.setItem('telegram_counselling_auth', JSON.stringify(authData));
            }
            
            setTimeout(() => {
                window.location.reload();
            }, 1800);
        } catch (err) {
            setEmailError(err.message || 'Failed to update email.');
        } finally {
            setEmailLoading(false);
        }
    };

    const handleUsernameChange = async (e) => {
        e.preventDefault();
        setUsernameMessage('');
        setUsernameError('');

        const trimmed = newUsername.trim();
        if (!trimmed) {
            setUsernameError('Username is required');
            return;
        }

        if (!/^[a-zA-Z0-9_]+$/.test(trimmed)) {
            setUsernameError('Username can only contain letters, numbers and underscores');
            return;
        }

        if (trimmed.length < 3) {
            setUsernameError('Username must be at least 3 characters');
            return;
        }

        if (trimmed.length > 150) {
            setUsernameError('Username cannot be more than 150 characters');
            return;
        }

        setUsernameLoading(true);
        try {
            const response = await fetch(`https://telegram-bot-backend-bwu4.onrender.com/api/users/${user.id}/change-username/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${localStorage.getItem('telegram_counselling_auth') ? JSON.parse(localStorage.getItem('telegram_counselling_auth')).access : ''}`
                },
                body: JSON.stringify({
                    username: trimmed
                })
            });

            const contentType = response.headers.get('content-type');
            if (!response.ok) {
                if (contentType && contentType.includes('text/html')) {
                    throw new Error('Failed to update username. Please try again.');
                }
                const data = await response.json();
                throw new Error(data.error || 'Failed to update username');
            }

            const data = await response.json();
            setUsernameMessage(data.message || 'Username updated successfully!');
            setNewUsername('');

            const authData = JSON.parse(localStorage.getItem('telegram_counselling_auth') || '{}');
            if (authData.user) {
                authData.user.username = data.username;
                localStorage.setItem('telegram_counselling_auth', JSON.stringify(authData));
            }

            setTimeout(() => {
                window.location.reload();
            }, 1500);
        } catch (err) {
            setUsernameError(err.message || 'Failed to update username.');
        } finally {
            setUsernameLoading(false);
        }
    };

    const getInitials = () => {
        if (!user?.username) return 'U';
        return user.username.slice(0, 2).toUpperCase();
    };

    const roleIsOwner = user?.role === 'owner';

    return (
        <section className="page-panel" style={{ padding: isMobile ? '16px' : '28px', maxWidth: '1300px', margin: '0 auto' }}>
            
            {/* ─── PAGE HEADER ─── */}
            <div className="panel-header" style={{ marginBottom: '28px' }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: '12px' }}>
                    <div>
                        <h1 style={{ fontSize: '26px', fontWeight: 700, margin: 0, display: 'flex', alignItems: 'center', gap: '10px' }}>
                            <span>Account Profile</span>
                            <span style={{
                                fontSize: '11px',
                                padding: '3px 10px',
                                borderRadius: '20px',
                                background: roleIsOwner ? 'rgba(255, 215, 0, 0.15)' : 'rgba(99, 102, 241, 0.15)',
                                color: roleIsOwner ? 'var(--gold)' : '#818cf8',
                                border: `1px solid ${roleIsOwner ? 'rgba(255, 215, 0, 0.35)' : 'rgba(99, 102, 241, 0.35)'}`,
                                textTransform: 'uppercase',
                                letterSpacing: '0.05em',
                                fontWeight: 600
                            }}>
                                {user?.role || 'Staff'}
                            </span>
                        </h1>
                        <p style={{ margin: '6px 0 0 0', color: 'var(--text-muted)', fontSize: '14px' }}>
                            Manage your personal credentials, communication channels, and security settings
                        </p>
                    </div>

                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '6px 12px',
                            background: 'rgba(16, 185, 129, 0.1)',
                            border: '1px solid rgba(16, 185, 129, 0.3)',
                            borderRadius: '20px',
                            color: '#10b981',
                            fontSize: '12px',
                            fontWeight: 600
                        }}>
                            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', boxShadow: '0 0 8px #10b981' }} />
                            Online & Authenticated
                        </span>
                    </div>
                </div>
            </div>

            {/* ─── MAIN TWO-COLUMN LAYOUT ─── */}
            <div style={{
                display: 'grid',
                gridTemplateColumns: isMobile ? '1fr' : '360px 1fr',
                gap: '24px',
                alignItems: 'start'
            }}>
                
                {/* ═══════════════════════════════════════════════════
                    LEFT COLUMN: SOCIAL MEDIA HERO PROFILE CARD
                   ═══════════════════════════════════════════════════ */}
                <div style={{
                    background: 'linear-gradient(135deg, rgba(20, 20, 24, 0.95) 0%, rgba(32, 32, 38, 0.9) 100%)',
                    border: '1px solid rgba(255, 215, 0, 0.25)',
                    borderRadius: '16px',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5), 0 0 25px rgba(255, 215, 0, 0.08)',
                    overflow: 'hidden',
                    position: 'relative'
                }}>
                    
                    {/* Social Banner / Cover Image */}
                    <div style={{
                        height: '110px',
                        width: '100%',
                        background: roleIsOwner
                            ? 'linear-gradient(135deg, #1f1402 0%, #3d2605 50%, #201300 100%)'
                            : 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #020617 100%)',
                        position: 'relative',
                        borderBottom: '1px solid rgba(255, 255, 255, 0.08)',
                        overflow: 'hidden'
                    }}>
                        <div style={{
                            position: 'absolute',
                            inset: 0,
                            backgroundImage: 'radial-gradient(circle at 20% 30%, rgba(255, 215, 0, 0.15) 0%, transparent 60%), radial-gradient(circle at 80% 70%, rgba(218, 165, 32, 0.12) 0%, transparent 50%)',
                            pointerEvents: 'none'
                        }} />
                        <div style={{
                            position: 'absolute',
                            top: '12px',
                            right: '12px',
                            fontSize: '11px',
                            color: 'rgba(255, 255, 255, 0.7)',
                            background: 'rgba(0, 0, 0, 0.4)',
                            padding: '4px 10px',
                            borderRadius: '12px',
                            backdropFilter: 'blur(4px)',
                            border: '1px solid rgba(255, 255, 255, 0.1)',
                            letterSpacing: '0.04em'
                        }}>
                            {roleIsOwner ? '👑 PLATFORM OWNER' : '🛡️ ADMINISTRATOR'}
                        </div>
                    </div>

                    {/* Profile Card Body */}
                    <div style={{ padding: '0 24px 24px 24px', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                        
                        {/* Overlapping Social Avatar */}
                        <div style={{ marginTop: '-55px', marginBottom: '16px', position: 'relative' }}>
                            <div 
                                onClick={() => (user?.role === 'admin' || user?.role === 'owner') && document.getElementById('profile-photo-upload')?.click()}
                                style={{
                                    width: '100px',
                                    height: '100px',
                                    borderRadius: '50%',
                                    background: profilePhoto ? `url(${profilePhoto})` : 'linear-gradient(135deg, #18181b 0%, #27272a 100%)',
                                    backgroundSize: 'cover',
                                    backgroundPosition: 'center',
                                    border: `3px solid ${roleIsOwner ? '#FFD700' : '#818cf8'}`,
                                    boxShadow: roleIsOwner 
                                        ? '0 0 25px rgba(255, 215, 0, 0.35), 0 8px 16px rgba(0, 0, 0, 0.6)' 
                                        : '0 0 25px rgba(99, 102, 241, 0.35), 0 8px 16px rgba(0, 0, 0, 0.6)',
                                    display: 'flex',
                                    alignItems: 'center',
                                    justifyContent: 'center',
                                    cursor: (user?.role === 'admin' || user?.role === 'owner') ? 'pointer' : 'default',
                                    transition: 'all 0.25s ease',
                                    position: 'relative',
                                    overflow: 'hidden'
                                }}
                                title="Click to upload profile photo"
                            >
                                {!profilePhoto && (
                                    <span style={{
                                        fontSize: '32px',
                                        fontWeight: 800,
                                        letterSpacing: '0.05em',
                                        color: roleIsOwner ? '#FFD700' : '#818cf8',
                                        textShadow: roleIsOwner ? '0 0 15px rgba(255, 215, 0, 0.6)' : '0 0 15px rgba(99, 102, 241, 0.6)'
                                    }}>
                                        {getInitials()}
                                    </span>
                                )}

                                {/* Hover Camera Overlay */}
                                {(user?.role === 'admin' || user?.role === 'owner') && (
                                    <div 
                                        style={{
                                            position: 'absolute',
                                            inset: 0,
                                            background: 'rgba(0, 0, 0, 0.6)',
                                            display: 'flex',
                                            flexDirection: 'column',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            opacity: 0,
                                            transition: 'opacity 0.2s ease',
                                            color: '#fff',
                                            fontSize: '11px',
                                            fontWeight: 600,
                                            gap: '2px'
                                        }}
                                        onMouseEnter={(e) => { e.currentTarget.style.opacity = '1'; }}
                                        onMouseLeave={(e) => { e.currentTarget.style.opacity = '0'; }}
                                    >
                                        <span style={{ fontSize: '20px' }}>📷</span>
                                        <span>Change</span>
                                    </div>
                                )}
                            </div>

                            {/* Online Badge */}
                            <div style={{
                                position: 'absolute',
                                bottom: '4px',
                                right: '4px',
                                width: '16px',
                                height: '16px',
                                borderRadius: '50%',
                                background: '#10b981',
                                border: '3px solid #141418',
                                boxShadow: '0 0 10px #10b981'
                            }} title="Online" />
                        </div>

                        {/* Name & Handle */}
                        <h2 style={{ fontSize: '20px', fontWeight: 700, margin: '0 0 4px 0', color: '#ffffff', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <span>{user?.username}</span>
                            <span style={{ color: roleIsOwner ? '#FFD700' : '#38bdf8', fontSize: '16px' }} title="Verified Staff">✓</span>
                        </h2>

                        <span style={{ fontSize: '13px', color: 'var(--text-muted)', marginBottom: '14px' }}>
                            @{user?.username?.toLowerCase()}
                        </span>

                        {/* Role Chip */}
                        <div style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '6px',
                            padding: '5px 16px',
                            borderRadius: '20px',
                            fontSize: '12px',
                            fontWeight: 700,
                            textTransform: 'uppercase',
                            letterSpacing: '0.06em',
                            background: roleIsOwner 
                                ? 'linear-gradient(135deg, rgba(255, 215, 0, 0.15) 0%, rgba(218, 165, 32, 0.08) 100%)' 
                                : 'linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(139, 92, 246, 0.08) 100%)',
                            color: roleIsOwner ? '#FFD700' : '#a5b4fc',
                            border: `1px solid ${roleIsOwner ? 'rgba(255, 215, 0, 0.4)' : 'rgba(99, 102, 241, 0.4)'}`,
                            boxShadow: roleIsOwner ? '0 0 15px rgba(255, 215, 0, 0.15)' : '0 0 15px rgba(99, 102, 241, 0.15)',
                            marginBottom: '18px'
                        }}>
                            <span>{roleIsOwner ? '👑' : '🛡️'}</span>
                            <span>{user?.role}</span>
                        </div>

                        {/* Photo Management Actions */}
                        {(user?.role === 'admin' || user?.role === 'owner') && (
                            <div style={{ width: '100%', marginBottom: '20px' }}>
                                <input
                                    type="file"
                                    id="profile-photo-upload"
                                    accept="image/*"
                                    onChange={handlePhotoUpload}
                                    style={{ display: 'none' }}
                                />
                                <div style={{ display: 'flex', gap: '8px', justifyContent: 'center', alignItems: 'center', width: '100%', maxWidth: '280px', margin: '0 auto' }}>
                                    <button
                                        type="button"
                                        onClick={() => document.getElementById('profile-photo-upload').click()}
                                        disabled={uploadingPhoto}
                                        className="button button-secondary button-sm"
                                        style={{
                                            fontSize: '12px',
                                            padding: '8px 14px',
                                            borderRadius: '8px',
                                            flex: '1 1 auto',
                                            minWidth: 0,
                                            whiteSpace: 'nowrap',
                                            display: 'inline-flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            height: '36px',
                                            width: 'auto'
                                        }}
                                    >
                                        {uploadingPhoto ? '⏳ Uploading...' : profilePhoto ? '📷 Change Avatar' : '📷 Add Avatar'}
                                    </button>
                                    {profilePhoto && (
                                        <button
                                            type="button"
                                            onClick={handleRemovePhoto}
                                            disabled={uploadingPhoto}
                                            style={{
                                                fontSize: '14px',
                                                width: '38px',
                                                minWidth: '38px',
                                                maxWidth: '38px',
                                                height: '36px',
                                                padding: 0,
                                                borderRadius: '8px',
                                                background: 'rgba(239, 68, 68, 0.15)',
                                                color: '#ef4444',
                                                border: '1px solid rgba(239, 68, 68, 0.4)',
                                                display: 'inline-flex',
                                                alignItems: 'center',
                                                justifyContent: 'center',
                                                flex: '0 0 38px',
                                                cursor: 'pointer'
                                            }}
                                            title="Delete photo"
                                        >
                                            🗑️
                                        </button>
                                    )}
                                </div>
                            </div>
                        )}

                        <div style={{ width: '100%', height: '1px', background: 'rgba(255, 215, 0, 0.15)', marginBottom: '18px' }} />

                        {/* Social Media Details Grid */}
                        <div style={{ width: '100%', display: 'flex', flexDirection: 'column', gap: '10px' }}>
                            
                            {/* Username row */}
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '10px 14px',
                                background: 'rgba(0, 0, 0, 0.35)',
                                borderRadius: '10px',
                                border: '1px solid rgba(255, 215, 0, 0.12)'
                            }}>
                                <div style={{ textAlign: 'left' }}>
                                    <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                                        User Handle
                                    </span>
                                    <strong style={{ fontSize: '13px', color: '#ffffff' }}>@{user?.username}</strong>
                                </div>
                                <button 
                                    type="button"
                                    onClick={() => handleCopy(user?.username || '', setCopiedUsername)}
                                    style={{
                                        background: copiedUsername ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                                        color: copiedUsername ? '#10b981' : 'var(--text-secondary)',
                                        border: `1px solid ${copiedUsername ? 'rgba(16, 185, 129, 0.3)' : 'rgba(255, 255, 255, 0.1)'}`,
                                        padding: '4px 10px',
                                        borderRadius: '6px',
                                        fontSize: '11px',
                                        cursor: 'pointer',
                                        fontWeight: 600,
                                        transition: 'all 0.2s ease'
                                    }}
                                >
                                    {copiedUsername ? '✓ Copied' : '📋 Copy'}
                                </button>
                            </div>

                            {/* Email display row */}
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '10px 14px',
                                background: 'rgba(0, 0, 0, 0.35)',
                                borderRadius: '10px',
                                border: '1px solid rgba(255, 215, 0, 0.12)'
                            }}>
                                <div style={{ textAlign: 'left', overflow: 'hidden', paddingRight: '8px' }}>
                                    <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                                        Official Email
                                    </span>
                                    <span style={{ fontSize: '13px', color: '#ffffff', display: 'block', textOverflow: 'ellipsis', overflow: 'hidden', whiteSpace: 'nowrap' }}>
                                        {user?.email || 'Not Configured'}
                                    </span>
                                </div>
                                {user?.email_verified ? (
                                    <span style={{
                                        padding: '3px 8px',
                                        borderRadius: '12px',
                                        background: 'rgba(16, 185, 129, 0.15)',
                                        color: '#10b981',
                                        fontSize: '11px',
                                        fontWeight: 700,
                                        border: '1px solid rgba(16, 185, 129, 0.3)',
                                        whiteSpace: 'nowrap'
                                    }}>
                                        ✓ Verified
                                    </span>
                                ) : (
                                    <span style={{
                                        padding: '3px 8px',
                                        borderRadius: '12px',
                                        background: 'rgba(245, 158, 11, 0.15)',
                                        color: '#f59e0b',
                                        fontSize: '11px',
                                        fontWeight: 700,
                                        border: '1px solid rgba(245, 158, 11, 0.3)',
                                        whiteSpace: 'nowrap'
                                    }}>
                                        Pending
                                    </span>
                                )}
                            </div>

                            {/* Role / Clearance row */}
                            <div style={{
                                display: 'flex',
                                justifyContent: 'space-between',
                                alignItems: 'center',
                                padding: '10px 14px',
                                background: 'rgba(0, 0, 0, 0.35)',
                                borderRadius: '10px',
                                border: '1px solid rgba(255, 215, 0, 0.12)'
                            }}>
                                <div style={{ textAlign: 'left' }}>
                                    <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 600 }}>
                                        Platform Clearance
                                    </span>
                                    <strong style={{ fontSize: '13px', color: roleIsOwner ? '#FFD700' : '#818cf8' }}>
                                        {user?.role?.toUpperCase()} ACCESS
                                    </strong>
                                </div>
                                <button 
                                    type="button"
                                    onClick={() => handleCopy(user?.role || '', setCopiedRole)}
                                    style={{
                                        background: copiedRole ? 'rgba(16, 185, 129, 0.15)' : 'rgba(255, 255, 255, 0.05)',
                                        color: copiedRole ? '#10b981' : 'var(--text-secondary)',
                                        border: `1px solid ${copiedRole ? 'rgba(16, 185, 129, 0.3)' : 'rgba(255, 255, 255, 0.1)'}`,
                                        padding: '4px 10px',
                                        borderRadius: '6px',
                                        fontSize: '11px',
                                        cursor: 'pointer',
                                        fontWeight: 600,
                                        transition: 'all 0.2s ease'
                                    }}
                                >
                                    {copiedRole ? '✓ Copied' : '📋 Copy'}
                                </button>
                            </div>

                        </div>
                    </div>
                </div>

                {/* ═══════════════════════════════════════════════════
                    RIGHT COLUMN: INTERACTIVE SETTINGS & TABS
                   ═══════════════════════════════════════════════════ */}
                <div style={{
                    background: 'linear-gradient(135deg, rgba(20, 20, 24, 0.95) 0%, rgba(30, 30, 36, 0.9) 100%)',
                    border: '1px solid rgba(255, 215, 0, 0.25)',
                    borderRadius: '16px',
                    boxShadow: '0 8px 32px rgba(0, 0, 0, 0.5), 0 0 25px rgba(255, 215, 0, 0.08)',
                    padding: isMobile ? '16px' : '28px'
                }}>
                    
                    {/* Modern Navigation Tabs */}
                    <div style={{
                        display: 'flex',
                        gap: '8px',
                        padding: '6px',
                        background: 'rgba(0, 0, 0, 0.4)',
                        border: '1px solid rgba(255, 215, 0, 0.15)',
                        borderRadius: '12px',
                        marginBottom: '28px',
                        overflowX: 'auto'
                    }}>
                        <button
                            type="button"
                            onClick={() => setActiveSubTab('security')}
                            style={{
                                flex: 1,
                                minWidth: '130px',
                                padding: '10px 16px',
                                fontSize: '13px',
                                fontWeight: 600,
                                borderRadius: '8px',
                                border: 'none',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                transition: 'all 0.2s ease',
                                background: activeSubTab === 'security'
                                    ? 'linear-gradient(135deg, #FFD700 0%, #DAA520 100%)'
                                    : 'transparent',
                                color: activeSubTab === 'security' ? '#000000' : 'var(--text-secondary)',
                                boxShadow: activeSubTab === 'security' ? '0 4px 15px rgba(255, 215, 0, 0.3)' : 'none'
                            }}
                        >
                            <span>🔒</span>
                            <span>Security & Auth</span>
                        </button>

                        <button
                            type="button"
                            onClick={() => setActiveSubTab('clearance')}
                            style={{
                                flex: 1,
                                minWidth: '130px',
                                padding: '10px 16px',
                                fontSize: '13px',
                                fontWeight: 600,
                                borderRadius: '8px',
                                border: 'none',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                transition: 'all 0.2s ease',
                                background: activeSubTab === 'clearance'
                                    ? 'linear-gradient(135deg, #FFD700 0%, #DAA520 100%)'
                                    : 'transparent',
                                color: activeSubTab === 'clearance' ? '#000000' : 'var(--text-secondary)',
                                boxShadow: activeSubTab === 'clearance' ? '0 4px 15px rgba(255, 215, 0, 0.3)' : 'none'
                            }}
                        >
                            <span>⚡</span>
                            <span>Clearance</span>
                        </button>

                        <button
                            type="button"
                            onClick={() => setActiveSubTab('notifications')}
                            style={{
                                flex: 1,
                                minWidth: '130px',
                                padding: '10px 16px',
                                fontSize: '13px',
                                fontWeight: 600,
                                borderRadius: '8px',
                                border: 'none',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                justifyContent: 'center',
                                gap: '8px',
                                transition: 'all 0.2s ease',
                                background: activeSubTab === 'notifications'
                                    ? 'linear-gradient(135deg, #FFD700 0%, #DAA520 100%)'
                                    : 'transparent',
                                color: activeSubTab === 'notifications' ? '#000000' : 'var(--text-secondary)',
                                boxShadow: activeSubTab === 'notifications' ? '0 4px 15px rgba(255, 215, 0, 0.3)' : 'none'
                            }}
                        >
                            <span>🔔</span>
                            <span>Alerts</span>
                        </button>
                    </div>

                    {/* ═══════════════════════════════════════════════════
                        TAB 1: SECURITY & CREDENTIALS
                       ═══════════════════════════════════════════════════ */}
                    {activeSubTab === 'security' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '28px', animation: 'fadeIn 0.3s ease-out' }}>
                            
                            {/* ── CARD A: EDIT USERNAME (Admin & Owner) ── */}
                            {(user?.role === 'admin' || user?.role === 'owner') && (
                                <div style={{
                                    background: 'rgba(0, 0, 0, 0.35)',
                                    border: '1px solid rgba(255, 215, 0, 0.2)',
                                    borderRadius: '12px',
                                    padding: '20px',
                                    position: 'relative'
                                }}>
                                    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                                        <div>
                                            <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: 'var(--gold)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                                <span>👤</span>
                                                <span>Change Username</span>
                                            </h3>
                                            <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-muted)' }}>
                                                Your public account handle used for logging in and displaying across chat threads.
                                            </p>
                                        </div>
                                        <div style={{ fontSize: '12px', padding: '4px 10px', background: 'rgba(255, 215, 0, 0.08)', border: '1px solid rgba(255, 215, 0, 0.2)', borderRadius: '6px', color: '#e0e0e0' }}>
                                            Current: <strong style={{ color: '#FFD700' }}>@{user?.username}</strong>
                                        </div>
                                    </div>

                                    <form onSubmit={handleUsernameChange} style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '16px' }}>
                                        <div>
                                            <label style={{ display: 'block', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '6px' }}>
                                                New Username
                                            </label>
                                            <div style={{ position: 'relative', width: '100%' }}>
                                                <span style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontSize: '14px', pointerEvents: 'none' }}>
                                                    @
                                                </span>
                                                <input
                                                    type="text"
                                                    value={newUsername}
                                                    onChange={(e) => setNewUsername(e.target.value)}
                                                    placeholder="Enter new username (e.g. counsel_admin)"
                                                    disabled={usernameLoading}
                                                    style={{ 
                                                        width: '100%',
                                                        padding: '12px 14px 12px 34px',
                                                        background: 'rgba(0, 0, 0, 0.5)',
                                                        border: '1px solid rgba(255, 215, 0, 0.3)',
                                                        borderRadius: '8px',
                                                        color: '#ffffff',
                                                        fontSize: '14px',
                                                        boxSizing: 'border-box'
                                                    }}
                                                />
                                            </div>
                                            <span style={{ display: 'block', fontSize: '11px', color: 'var(--text-muted)', marginTop: '4px' }}>
                                                Allowed: 3-150 characters, letters, numbers, and underscores only.
                                            </span>
                                        </div>

                                        {usernameMessage && (
                                            <div style={{ 
                                                background: 'rgba(16, 185, 129, 0.15)', 
                                                border: '1px solid rgba(16, 185, 129, 0.4)',
                                                borderRadius: '8px',
                                                padding: '10px 14px',
                                                color: '#10b981',
                                                fontSize: '13px',
                                                fontWeight: 500,
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '8px'
                                            }}>
                                                <span>✓</span>
                                                <span>{usernameMessage}</span>
                                            </div>
                                        )}

                                        {usernameError && (
                                            <div style={{ 
                                                background: 'rgba(239, 68, 68, 0.15)', 
                                                border: '1px solid rgba(239, 68, 68, 0.4)',
                                                borderRadius: '8px',
                                                padding: '10px 14px',
                                                color: '#ef4444',
                                                fontSize: '13px',
                                                fontWeight: 500,
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: '8px'
                                            }}>
                                                <span>⚠️</span>
                                                <span>{usernameError}</span>
                                            </div>
                                        )}

                                        <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                                            <LoadingButton
                                                type="submit"
                                                loading={usernameLoading}
                                                disabled={!newUsername.trim() || usernameLoading}
                                                className="button button-primary"
                                                style={{
                                                    fontSize: '13px',
                                                    padding: '10px 22px',
                                                    borderRadius: '8px',
                                                    fontWeight: 600
                                                }}
                                            >
                                                {usernameLoading ? 'Saving...' : 'Update Username'}
                                            </LoadingButton>
                                        </div>
                                    </form>
                                </div>
                            )}

                            {/* ── CARD B: EDIT EMAIL ── */}
                            <div style={{
                                background: 'rgba(0, 0, 0, 0.35)',
                                border: '1px solid rgba(255, 215, 0, 0.2)',
                                borderRadius: '12px',
                                padding: '20px'
                            }}>
                                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px', flexWrap: 'wrap', gap: '8px' }}>
                                    <div>
                                        <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: 'var(--gold)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                            <span>✉️</span>
                                            <span>Email Address</span>
                                        </h3>
                                        <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-muted)' }}>
                                            Primary email for receiving urgent case alerts, reports, and account recovery.
                                        </p>
                                    </div>
                                    <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Current:</span>
                                        <span style={{ fontSize: '12px', color: '#ffffff', fontWeight: 600 }}>{user?.email || 'None'}</span>
                                        {user?.email_verified && (
                                            <span style={{ color: '#10b981', fontSize: '11px', fontWeight: 700, marginLeft: '4px' }}>✓ Verified</span>
                                        )}
                                    </div>
                                </div>

                                <form onSubmit={handleEmailChange} style={{ display: 'flex', flexDirection: 'column', gap: '14px', marginTop: '16px' }}>
                                    <div>
                                        <label style={{ display: 'block', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '6px' }}>
                                            New Email Address
                                        </label>
                                        <div style={{ position: 'relative', width: '100%' }}>
                                            <span style={{ position: 'absolute', left: '14px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-muted)', fontSize: '14px', pointerEvents: 'none' }}>
                                                ✉
                                            </span>
                                            <input
                                                type="email"
                                                value={newEmail}
                                                onChange={(e) => setNewEmail(e.target.value)}
                                                placeholder="Enter new email (e.g. name@astu.edu.et)"
                                                disabled={emailLoading}
                                                style={{ 
                                                    width: '100%',
                                                    padding: '12px 14px 12px 34px',
                                                    background: 'rgba(0, 0, 0, 0.5)',
                                                    border: '1px solid rgba(255, 215, 0, 0.3)',
                                                    borderRadius: '8px',
                                                    color: '#ffffff',
                                                    fontSize: '14px',
                                                    boxSizing: 'border-box'
                                                }}
                                            />
                                        </div>
                                    </div>

                                    {emailMessage && (
                                        <div style={{ 
                                            background: 'rgba(16, 185, 129, 0.15)', 
                                            border: '1px solid rgba(16, 185, 129, 0.4)',
                                            borderRadius: '8px',
                                            padding: '10px 14px',
                                            color: '#10b981',
                                            fontSize: '13px',
                                            fontWeight: 500,
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '8px'
                                        }}>
                                            <span>✓</span>
                                            <span>{emailMessage}</span>
                                        </div>
                                    )}

                                    {emailError && (
                                        <div style={{ 
                                            background: 'rgba(239, 68, 68, 0.15)', 
                                            border: '1px solid rgba(239, 68, 68, 0.4)',
                                            borderRadius: '8px',
                                            padding: '10px 14px',
                                            color: '#ef4444',
                                            fontSize: '13px',
                                            fontWeight: 500,
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '8px'
                                        }}>
                                            <span>⚠️</span>
                                            <span>{emailError}</span>
                                        </div>
                                    )}

                                    <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                                        <LoadingButton
                                            type="submit"
                                            loading={emailLoading}
                                            disabled={!newEmail.trim() || emailLoading}
                                            className="button button-primary"
                                            style={{
                                                fontSize: '13px',
                                                padding: '10px 22px',
                                                borderRadius: '8px',
                                                fontWeight: 600
                                            }}
                                        >
                                            {emailLoading ? 'Updating...' : 'Update Email'}
                                        </LoadingButton>
                                    </div>
                                </form>
                            </div>

                            {/* ── CARD C: CHANGE PASSWORD ── */}
                            <div style={{
                                background: 'rgba(0, 0, 0, 0.35)',
                                border: '1px solid rgba(255, 215, 0, 0.2)',
                                borderRadius: '12px',
                                padding: '20px'
                            }}>
                                <div style={{ marginBottom: '16px' }}>
                                    <h3 style={{ fontSize: '16px', fontWeight: 700, margin: 0, color: 'var(--gold)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                        <span>🔑</span>
                                        <span>Change Password</span>
                                    </h3>
                                    <p style={{ margin: '4px 0 0 0', fontSize: '13px', color: 'var(--text-muted)' }}>
                                        Enhance your security by using a strong password with at least 8 characters.
                                    </p>
                                </div>

                                <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                                    <div>
                                        <label style={{ display: 'block', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '6px' }}>
                                            Current Password
                                        </label>
                                        <input
                                            type="password"
                                            value={oldPassword}
                                            onChange={(e) => setOldPassword(e.target.value)}
                                            placeholder="Enter your current password"
                                            required
                                            disabled={loading}
                                            style={{ 
                                                width: '100%', 
                                                padding: '12px 14px', 
                                                background: 'rgba(0, 0, 0, 0.5)',
                                                border: '1px solid rgba(255, 215, 0, 0.3)',
                                                borderRadius: '8px',
                                                color: '#ffffff',
                                                fontSize: '14px',
                                                boxSizing: 'border-box'
                                            }}
                                        />
                                    </div>

                                    <div>
                                        <label style={{ display: 'block', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '6px' }}>
                                            New Password
                                        </label>
                                        <input
                                            type="password"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            placeholder="Enter minimum 8 characters"
                                            required
                                            disabled={loading}
                                            style={{ 
                                                width: '100%', 
                                                padding: '12px 14px', 
                                                background: 'rgba(0, 0, 0, 0.5)',
                                                border: '1px solid rgba(255, 215, 0, 0.3)',
                                                borderRadius: '8px',
                                                color: '#ffffff',
                                                fontSize: '14px',
                                                boxSizing: 'border-box'
                                            }}
                                        />
                                        
                                        {/* Password Strength Meter */}
                                        {password && (
                                            <div style={{ marginTop: '8px', animation: 'fadeIn 0.2s ease-out' }}>
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '4px' }}>
                                                    <span style={{ fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Security Strength</span>
                                                    <span style={{ fontSize: '11px', color: strength.color, fontWeight: 700 }}>{strength.label}</span>
                                                </div>
                                                <div style={{ height: '4px', background: 'rgba(255, 255, 255, 0.08)', borderRadius: '4px', overflow: 'hidden' }}>
                                                    <div style={{
                                                        height: '100%',
                                                        width: strength.width,
                                                        background: strength.color,
                                                        transition: 'all 0.3s ease'
                                                    }} />
                                                </div>
                                            </div>
                                        )}
                                    </div>

                                    <div>
                                        <label style={{ display: 'block', fontSize: '11px', textTransform: 'uppercase', letterSpacing: '0.05em', color: 'var(--text-muted)', fontWeight: 600, marginBottom: '6px' }}>
                                            Confirm New Password
                                        </label>
                                        <input
                                            type="password"
                                            value={confirmPassword}
                                            onChange={(e) => setConfirmPassword(e.target.value)}
                                            placeholder="Re-enter new password to verify"
                                            required
                                            disabled={loading}
                                            style={{ 
                                                width: '100%', 
                                                padding: '12px 14px', 
                                                background: 'rgba(0, 0, 0, 0.5)',
                                                border: '1px solid rgba(255, 215, 0, 0.3)',
                                                borderRadius: '8px',
                                                color: '#ffffff',
                                                fontSize: '14px',
                                                boxSizing: 'border-box'
                                            }}
                                        />
                                    </div>

                                    {message && (
                                        <div style={{ 
                                            background: 'rgba(16, 185, 129, 0.15)', 
                                            border: '1px solid rgba(16, 185, 129, 0.4)',
                                            borderRadius: '8px',
                                            padding: '10px 14px',
                                            color: '#10b981',
                                            fontSize: '13px',
                                            fontWeight: 500,
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '8px'
                                        }}>
                                            <span>✓</span>
                                            <span>{message}</span>
                                        </div>
                                    )}

                                    {error && (
                                        <div style={{ 
                                            background: 'rgba(239, 68, 68, 0.15)', 
                                            border: '1px solid rgba(239, 68, 68, 0.4)',
                                            borderRadius: '8px',
                                            padding: '10px 14px',
                                            color: '#ef4444',
                                            fontSize: '13px',
                                            fontWeight: 500,
                                            display: 'flex',
                                            alignItems: 'center',
                                            gap: '8px'
                                        }}>
                                            <span>⚠️</span>
                                            <span>{error}</span>
                                        </div>
                                    )}

                                    <div style={{ display: 'flex', justifyContent: 'flex-start', marginTop: '6px' }}>
                                        <LoadingButton 
                                            className="button button-primary" 
                                            type="submit" 
                                            disabled={!password || (password !== confirmPassword) || loading}
                                            loading={loading}
                                            loadingText="Saving..."
                                            style={{
                                                fontSize: '13px',
                                                padding: '10px 22px',
                                                borderRadius: '8px',
                                                fontWeight: 600
                                            }}
                                        >
                                            Update Password
                                        </LoadingButton>
                                    </div>
                                </form>
                            </div>

                        </div>
                    )}

                    {/* ═══════════════════════════════════════════════════
                        TAB 2: SYSTEM CLEARANCE & PRIVILEGES
                       ═══════════════════════════════════════════════════ */}
                    {activeSubTab === 'clearance' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', animation: 'fadeIn 0.3s ease-out' }}>
                            <div>
                                <h3 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 6px 0', color: 'var(--gold)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <span>⚡</span>
                                    <span>Operational Clearance & Privileges</span>
                                </h3>
                                <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
                                    Review the administrative clearance levels and data rights provisioned to your profile.
                                </p>
                            </div>

                            {/* Active Permissions Box */}
                            <div style={{
                                background: 'rgba(0, 0, 0, 0.35)',
                                border: '1px solid rgba(255, 215, 0, 0.2)',
                                borderRadius: '12px',
                                padding: '20px'
                            }}>
                                <span style={{
                                    display: 'block',
                                    fontSize: '11px',
                                    fontWeight: 700,
                                    color: roleIsOwner ? '#FFD700' : '#818cf8',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.06em',
                                    marginBottom: '14px'
                                }}>
                                    {roleIsOwner ? '👑 Full Master Clearance Granted' : '🛡️ Standard Administrative Clearance'}
                                </span>

                                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
                                    {roleIsOwner ? (
                                        <>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#ffffff' }}>
                                                <span style={{ color: '#10b981', fontSize: '16px' }}>✓</span>
                                                <span>Full Database Read/Write & User Assignment Management</span>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#ffffff' }}>
                                                <span style={{ color: '#10b981', fontSize: '16px' }}>✓</span>
                                                <span>Staff Role Elevation & Administrative Account Control</span>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#ffffff' }}>
                                                <span style={{ color: '#10b981', fontSize: '16px' }}>✓</span>
                                                <span>System-Wide Analytics, Audit Logs & Case Deletion</span>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#ffffff' }}>
                                                <span style={{ color: '#10b981', fontSize: '16px' }}>✓</span>
                                                <span>Telegram Bot Integration, Token Sync & Webhook Control</span>
                                            </div>
                                        </>
                                    ) : (
                                        <>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#ffffff' }}>
                                                <span style={{ color: '#10b981', fontSize: '16px' }}>✓</span>
                                                <span>Active Client Support Case Communications</span>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#ffffff' }}>
                                                <span style={{ color: '#10b981', fontSize: '16px' }}>✓</span>
                                                <span>Create, Review and Submit Formal Counseling Reports</span>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: '#ffffff' }}>
                                                <span style={{ color: '#10b981', fontSize: '16px' }}>✓</span>
                                                <span>Internal Staff Team Collaboration & General Chat Access</span>
                                            </div>
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', fontSize: '13px', color: 'var(--text-muted)' }}>
                                                <span style={{ color: 'var(--text-muted)', fontSize: '16px' }}>✕</span>
                                                <span>Master Credentials & Staff Elevation Modification (Restricted)</span>
                                            </div>
                                        </>
                                    )}
                                </div>
                            </div>

                            {/* Service Status Monitoring Panel */}
                            <div>
                                <span style={{
                                    display: 'block',
                                    fontSize: '11px',
                                    fontWeight: 700,
                                    color: 'var(--text-muted)',
                                    textTransform: 'uppercase',
                                    letterSpacing: '0.06em',
                                    marginBottom: '12px'
                                }}>
                                    Infrastructure Health Status
                                </span>
                                <div style={{
                                    display: 'grid',
                                    gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))',
                                    gap: '12px'
                                }}>
                                    <div style={{
                                        padding: '12px 14px',
                                        background: 'rgba(16, 185, 129, 0.05)',
                                        border: '1px solid rgba(16, 185, 129, 0.25)',
                                        borderRadius: '10px',
                                        textAlign: 'center'
                                    }}>
                                        <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Database</span>
                                        <strong style={{ fontSize: '13px', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', marginTop: '2px' }}>
                                            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }} />
                                            POSTGRES (Neon)
                                        </strong>
                                    </div>
                                    <div style={{
                                        padding: '12px 14px',
                                        background: 'rgba(16, 185, 129, 0.05)',
                                        border: '1px solid rgba(16, 185, 129, 0.25)',
                                        borderRadius: '10px',
                                        textAlign: 'center'
                                    }}>
                                        <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Backend API</span>
                                        <strong style={{ fontSize: '13px', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', marginTop: '2px' }}>
                                            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }} />
                                            HEALTHY
                                        </strong>
                                    </div>
                                    <div style={{
                                        padding: '12px 14px',
                                        background: 'rgba(16, 185, 129, 0.05)',
                                        border: '1px solid rgba(16, 185, 129, 0.25)',
                                        borderRadius: '10px',
                                        textAlign: 'center'
                                    }}>
                                        <span style={{ display: 'block', fontSize: '10px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Telegram Relay</span>
                                        <strong style={{ fontSize: '13px', color: '#10b981', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '4px', marginTop: '2px' }}>
                                            <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#10b981' }} />
                                            ONLINE
                                        </strong>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* ═══════════════════════════════════════════════════
                        TAB 3: ALERTS & NOTIFICATIONS
                       ═══════════════════════════════════════════════════ */}
                    {activeSubTab === 'notifications' && (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '24px', animation: 'fadeIn 0.3s ease-out' }}>
                            <div>
                                <h3 style={{ fontSize: '18px', fontWeight: 700, margin: '0 0 6px 0', color: 'var(--gold)', display: 'flex', alignItems: 'center', gap: '8px' }}>
                                    <span>🔔</span>
                                    <span>Notification Channels & Sound Alerts</span>
                                </h3>
                                <p style={{ color: 'var(--text-muted)', fontSize: '13px', margin: 0 }}>
                                    Customize how and where you want to be alerted when clients or team members send messages.
                                </p>
                            </div>

                            {/* Email Notifications Toggle for Staff */}
                            {user?.role !== 'user' && (
                                <div style={{
                                    padding: '18px',
                                    background: 'rgba(0, 0, 0, 0.35)',
                                    border: '1px solid rgba(255, 215, 0, 0.25)',
                                    borderRadius: '12px',
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    gap: '16px'
                                }}>
                                    <div style={{ flex: 1 }}>
                                        <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '4px' }}>
                                            <span style={{ fontSize: '18px' }}>📧</span>
                                            <strong style={{ fontSize: '14px', color: '#ffffff' }}>Email Alerts</strong>
                                        </div>
                                        <p style={{ fontSize: '13px', color: 'var(--text-muted)', margin: 0, lineHeight: 1.4 }}>
                                            Receive real-time email dispatches for assigned cases and emergency reports.
                                            {!user?.email_verified && (
                                                <span style={{ color: '#f59e0b', display: 'block', fontWeight: 600, marginTop: '2px' }}>
                                                    ⚠️ Requires email verification first
                                                </span>
                                            )}
                                        </p>
                                    </div>

                                    {/* Toggle Switch */}
                                    <button
                                        type="button"
                                        onClick={handleToggleEmailNotifications}
                                        disabled={updatingEmailNotifs || !user?.email_verified || !user?.email_approved_by_owner}
                                        style={{
                                            width: '52px',
                                            height: '28px',
                                            borderRadius: '20px',
                                            background: emailNotificationsEnabled 
                                                ? 'linear-gradient(135deg, #FFD700 0%, #DAA520 100%)' 
                                                : 'rgba(255, 255, 255, 0.1)',
                                            border: 'none',
                                            cursor: (!user?.email_verified || !user?.email_approved_by_owner || updatingEmailNotifs) ? 'not-allowed' : 'pointer',
                                            position: 'relative',
                                            transition: 'all 0.25s ease',
                                            boxShadow: emailNotificationsEnabled ? '0 0 12px rgba(255, 215, 0, 0.4)' : 'none',
                                            opacity: (!user?.email_verified || !user?.email_approved_by_owner) ? 0.4 : 1
                                        }}
                                    >
                                        <div style={{
                                            width: '22px',
                                            height: '22px',
                                            borderRadius: '50%',
                                            background: emailNotificationsEnabled ? '#000000' : '#ffffff',
                                            position: 'absolute',
                                            top: '3px',
                                            left: emailNotificationsEnabled ? '27px' : '3px',
                                            transition: 'all 0.25s ease',
                                            display: 'flex',
                                            alignItems: 'center',
                                            justifyContent: 'center',
                                            fontSize: '11px',
                                            fontWeight: 700
                                        }}>
                                            {updatingEmailNotifs ? '·' : emailNotificationsEnabled ? '✓' : ''}
                                        </div>
                                    </button>
                                </div>
                            )}

                            {/* Additional Channel Toggles */}
                            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                                
                                {/* Telegram Message Relay */}
                                <div style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    padding: '16px 18px',
                                    background: 'rgba(0, 0, 0, 0.35)',
                                    border: '1px solid rgba(255, 215, 0, 0.15)',
                                    borderRadius: '12px'
                                }}>
                                    <div>
                                        <strong style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px', color: '#ffffff', marginBottom: '2px' }}>
                                            <span>✈️</span>
                                            <span>Telegram Bot Relay</span>
                                        </strong>
                                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                                            Forward case updates directly to your connected Telegram handle.
                                        </span>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleToggleNotif('telegramRelay')}
                                        style={{
                                            width: '52px',
                                            height: '28px',
                                            borderRadius: '20px',
                                            background: notifs.telegramRelay ? 'linear-gradient(135deg, #FFD700 0%, #DAA520 100%)' : 'rgba(255, 255, 255, 0.1)',
                                            border: 'none',
                                            cursor: 'pointer',
                                            position: 'relative',
                                            transition: 'all 0.25s ease',
                                            boxShadow: notifs.telegramRelay ? '0 0 12px rgba(255, 215, 0, 0.4)' : 'none'
                                        }}
                                    >
                                        <div style={{
                                            width: '22px',
                                            height: '22px',
                                            borderRadius: '50%',
                                            background: notifs.telegramRelay ? '#000000' : '#ffffff',
                                            position: 'absolute',
                                            top: '3px',
                                            left: notifs.telegramRelay ? '27px' : '3px',
                                            transition: 'all 0.25s ease'
                                        }} />
                                    </button>
                                </div>

                                {/* Audio Chimes */}
                                <div style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    padding: '16px 18px',
                                    background: 'rgba(0, 0, 0, 0.35)',
                                    border: '1px solid rgba(255, 215, 0, 0.15)',
                                    borderRadius: '12px'
                                }}>
                                    <div>
                                        <strong style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px', color: '#ffffff', marginBottom: '2px' }}>
                                            <span>🔊</span>
                                            <span>Audio Chime Notifications</span>
                                        </strong>
                                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                                            Play subtle acoustic cues whenever new messages arrive on active tabs.
                                        </span>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleToggleNotif('soundChime')}
                                        style={{
                                            width: '52px',
                                            height: '28px',
                                            borderRadius: '20px',
                                            background: notifs.soundChime ? 'linear-gradient(135deg, #FFD700 0%, #DAA520 100%)' : 'rgba(255, 255, 255, 0.1)',
                                            border: 'none',
                                            cursor: 'pointer',
                                            position: 'relative',
                                            transition: 'all 0.25s ease',
                                            boxShadow: notifs.soundChime ? '0 0 12px rgba(255, 215, 0, 0.4)' : 'none'
                                        }}
                                    >
                                        <div style={{
                                            width: '22px',
                                            height: '22px',
                                            borderRadius: '50%',
                                            background: notifs.soundChime ? '#000000' : '#ffffff',
                                            position: 'absolute',
                                            top: '3px',
                                            left: notifs.soundChime ? '27px' : '3px',
                                            transition: 'all 0.25s ease'
                                        }} />
                                    </button>
                                </div>

                                {/* Desktop / Browser Alerts */}
                                <div style={{
                                    display: 'flex',
                                    justifyContent: 'space-between',
                                    alignItems: 'center',
                                    padding: '16px 18px',
                                    background: 'rgba(0, 0, 0, 0.35)',
                                    border: '1px solid rgba(255, 215, 0, 0.15)',
                                    borderRadius: '12px'
                                }}>
                                    <div>
                                        <strong style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '14px', color: '#ffffff', marginBottom: '2px' }}>
                                            <span>💻</span>
                                            <span>Browser Push Badges</span>
                                        </strong>
                                        <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                                            Display unread badge counters on your browser tab while working in other apps.
                                        </span>
                                    </div>
                                    <button
                                        type="button"
                                        onClick={() => handleToggleNotif('browserAlert')}
                                        style={{
                                            width: '52px',
                                            height: '28px',
                                            borderRadius: '20px',
                                            background: notifs.browserAlert ? 'linear-gradient(135deg, #FFD700 0%, #DAA520 100%)' : 'rgba(255, 255, 255, 0.1)',
                                            border: 'none',
                                            cursor: 'pointer',
                                            position: 'relative',
                                            transition: 'all 0.25s ease',
                                            boxShadow: notifs.browserAlert ? '0 0 12px rgba(255, 215, 0, 0.4)' : 'none'
                                        }}
                                    >
                                        <div style={{
                                            width: '22px',
                                            height: '22px',
                                            borderRadius: '50%',
                                            background: notifs.browserAlert ? '#000000' : '#ffffff',
                                            position: 'absolute',
                                            top: '3px',
                                            left: notifs.browserAlert ? '27px' : '3px',
                                            transition: 'all 0.25s ease'
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
