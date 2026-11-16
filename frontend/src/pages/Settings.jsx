import { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import { apiCall } from '../api.js';
import { getUser } from '../auth.js';
import LoadingButton from '../components/LoadingButton.jsx';

export default function SettingsPage() {
  const user = getUser();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Diagnostic Action states
  const [actionLoading, setActionLoading] = useState({});
  const [actionFeedback, setActionFeedback] = useState({});
  const [testEmail, setTestEmail] = useState('');

  // Telegram Broadcast Announcement states (Counselees only)
  const [broadcastMessage, setBroadcastMessage] = useState('');
  const [isBroadcastModalOpen, setIsBroadcastModalOpen] = useState(false);
  const [broadcastLoading, setBroadcastLoading] = useState(false);
  const [broadcastFeedback, setBroadcastFeedback] = useState(null);

  // Danger Zone / Purge Modal states
  const [isPurgeModalOpen, setIsPurgeModalOpen] = useState(false);
  const [purgeConfirmText, setPurgeConfirmText] = useState('');
  const [isPurging, setIsPurging] = useState(false);
  const [purgeError, setPurgeError] = useState('');
  const [purgeSuccess, setPurgeSuccess] = useState('');

  // Backup & Restore states
  const [isDownloadingBackup, setIsDownloadingBackup] = useState(false);
  const [backupFeedback, setBackupFeedback] = useState(null);
  const [isRestoring, setIsRestoring] = useState(false);
  const [restoreFeedback, setRestoreFeedback] = useState(null);
  const [isRestoreModalOpen, setIsRestoreModalOpen] = useState(false);
  const [restoreFileInfo, setRestoreFileInfo] = useState(null);
  const [restoreFileParsed, setRestoreFileParsed] = useState(null);
  const restoreFileRef = useRef(null);

  useEffect(() => {
    fetchSettings();
  }, []);

  useEffect(() => {
    if (isPurgeModalOpen || isBroadcastModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isPurgeModalOpen, isBroadcastModalOpen]);

  useEffect(() => {
    if (isRestoreModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => { document.body.style.overflow = ''; };
  }, [isRestoreModalOpen]);

  const fetchSettings = async () => {
    setLoading(true);
    setError('');
    try {
      const res = await apiCall('/api/system/settings/', 'GET');
      setData(res);
      if (res && user?.email && !testEmail) {
        setTestEmail(user.email);
      }
    } catch (err) {
      setError(err.message || 'Failed to load system settings');
    } finally {
      setLoading(false);
    }
  };

  const runAction = async (actionKey, payload = {}) => {
    setActionLoading((prev) => ({ ...prev, [actionKey]: true }));
    setActionFeedback((prev) => ({ ...prev, [actionKey]: null }));
    try {
      const res = await apiCall('/api/system/action/', 'POST', { action: actionKey, ...payload });
      setActionFeedback((prev) => ({
        ...prev,
        [actionKey]: { type: 'success', message: res.message || 'Action executed successfully.' },
      }));
      // Refresh metrics after action
      fetchSettings();
    } catch (err) {
      setActionFeedback((prev) => ({
        ...prev,
        [actionKey]: { type: 'error', message: err.message || 'Action failed.' },
      }));
    } finally {
      setActionLoading((prev) => ({ ...prev, [actionKey]: false }));
    }
  };

  const handleOpenBroadcastModal = (e) => {
    if (e) e.preventDefault();
    if (!broadcastMessage.trim()) {
      setBroadcastFeedback({ type: 'error', message: 'Please enter a message before dispatching.' });
      return;
    }
    setBroadcastFeedback(null);
    setIsBroadcastModalOpen(true);
  };

  const handleSendBroadcast = async () => {
    setBroadcastLoading(true);
    setBroadcastFeedback(null);
    try {
      const res = await apiCall('/api/system/action/', 'POST', {
        action: 'broadcast_telegram',
        message: broadcastMessage.trim()
      });
      setBroadcastFeedback({
        type: res.status === 'ok' ? 'success' : 'error',
        message: res.message || 'Broadcast completed successfully.'
      });
      if (res.status === 'ok') {
        setBroadcastMessage('');
        setIsBroadcastModalOpen(false);
      }
    } catch (err) {
      setBroadcastFeedback({
        type: 'error',
        message: err.message || 'Failed to dispatch broadcast.'
      });
    } finally {
      setBroadcastLoading(false);
    }
  };

  const handlePurgeTestData = async () => {
    if (purgeConfirmText.trim() !== 'RESET') {
      setPurgeError('Please type RESET in all capital letters to confirm.');
      return;
    }
    setIsPurging(true);
    setPurgeError('');
    setPurgeSuccess('');
    try {
      const res = await apiCall('/api/purge-test-data/', 'POST', { confirm: true });
      setPurgeSuccess(res.message || 'System reset successfully. All test data cleared and sequences reset to #1.');
      setIsPurgeModalOpen(false);
      setPurgeConfirmText('');
      fetchSettings();
    } catch (err) {
      setPurgeError(err.message || 'Failed to purge test data');
    } finally {
      setIsPurging(false);
    }
  };

  // ── Backup Download ──────────────────────────────────────────────────────────
  const handleDownloadBackup = async () => {
    setIsDownloadingBackup(true);
    setBackupFeedback(null);
    try {
      const auth = JSON.parse(localStorage.getItem('telegram_counselling_auth') || '{}');
      const token = auth?.access || '';
      // Use the same backend base URL that api.js uses (Render in prod, localhost in dev)
      const apiBase = import.meta.env.VITE_API_URL ||
        (import.meta.env.PROD
          ? 'https://telegram-bot-backend-bwu4.onrender.com'
          : 'http://localhost:8000');
      const response = await fetch(`${apiBase}/api/system/backup/`, {
        method: 'GET',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      if (!response.ok) {
        const errData = await response.json().catch(() => ({}));
        throw new Error(errData.error || `Server error: ${response.status}`);
      }
      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      const dateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
      a.download = `focus_astu_backup_${dateStr}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      setBackupFeedback({ type: 'success', message: 'Backup downloaded successfully to your device!' });
    } catch (err) {
      setBackupFeedback({ type: 'error', message: err.message || 'Failed to download backup.' });
    } finally {
      setIsDownloadingBackup(false);
    }
  };

  // ── Restore: File picker handler ─────────────────────────────────────────────
  const handleRestoreFileSelect = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setRestoreFeedback(null);
    const reader = new FileReader();
    reader.onload = (evt) => {
      try {
        const parsed = JSON.parse(evt.target.result);
        if (!parsed.users || !parsed.backup_version) {
          setRestoreFeedback({ type: 'error', message: 'Invalid backup file. This does not appear to be a Focus ASTU backup.' });
          return;
        }
        setRestoreFileInfo({ name: file.name, size: (file.size / 1024).toFixed(1) + ' KB' });
        setRestoreFileParsed(parsed);
        setIsRestoreModalOpen(true);
      } catch {
        setRestoreFeedback({ type: 'error', message: 'Could not read file — it may be corrupt or not a valid JSON backup.' });
      }
    };
    reader.readAsText(file);
    // Reset input so same file can be re-selected
    e.target.value = '';
  };

  // ── Restore: Send to backend ─────────────────────────────────────────────────
  const handleRestoreBackup = async () => {
    if (!restoreFileParsed) return;
    setIsRestoring(true);
    setRestoreFeedback(null);
    try {
      const res = await apiCall('/api/system/backup/', 'POST', restoreFileParsed);
      setRestoreFeedback({ type: 'success', message: res.message });
      setIsRestoreModalOpen(false);
      setRestoreFileInfo(null);
      setRestoreFileParsed(null);
      fetchSettings();
    } catch (err) {
      setRestoreFeedback({ type: 'error', message: err.message || 'Restore failed. Please try again.' });
      setIsRestoreModalOpen(false);
    } finally {
      setIsRestoring(false);
    }
  };

  if (user?.role !== 'owner') {
    return (
      <div className="page-container">
        <div className="glass-panel" style={{ textAlign: 'center', padding: '3rem' }}>
          <h2 style={{ color: '#ef4444' }}>Access Restricted</h2>
          <p style={{ color: 'var(--text-muted)' }}>Only platform Owners can access Technical System Settings.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="page-container" style={{ maxWidth: '1200px', margin: '0 auto', padding: '2rem 1rem' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '2rem' }}>
        <div>
          <h1 style={{ margin: 0, fontSize: '28px', color: 'var(--gold, #d4af37)', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
            ⚙️ System & Technical Settings
          </h1>
          <p style={{ margin: '0.5rem 0 0 0', color: '#94a3b8', fontSize: '14px' }}>
            Centralized technical control panel for platform health, service diagnostics, and launch management.
          </p>
        </div>
        <button
          className="button button-secondary"
          onClick={fetchSettings}
          disabled={loading}
          style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}
        >
          🔄 {loading ? 'Refreshing...' : 'Refresh Status'}
        </button>
      </div>

      {error && (
        <div style={{ padding: '1rem', background: 'rgba(239, 68, 68, 0.1)', border: '1px solid #ef4444', borderRadius: '8px', color: '#ef4444', marginBottom: '1.5rem' }}>
          ⚠️ {error}
        </div>
      )}

      {/* Top 4 Health Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '1rem', marginBottom: '2rem' }}>
        {/* Database */}
        <div className="glass-panel stat-card" style={{ padding: '1.25rem', border: '1px solid rgba(212, 175, 55, 0.2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Database Engine</span>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: data?.database?.status === 'connected' ? '#10b981' : '#ef4444', display: 'inline-block' }} />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc', marginTop: '0.5rem' }}>
            {data?.database?.vendor?.toUpperCase() || 'POSTGRESQL'}
          </div>
          <div style={{ fontSize: '13px', color: '#10b981', marginTop: '0.25rem' }}>
            ✓ {data?.database?.status || 'Connected'} {data?.database?.latency_ms ? `(${data.database.latency_ms} ms)` : ''}
          </div>
        </div>

        {/* Telegram Bot */}
        <div className="glass-panel stat-card" style={{ padding: '1.25rem', border: '1px solid rgba(212, 175, 55, 0.2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Telegram Bot</span>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: data?.telegram?.status === 'online' ? '#10b981' : '#f59e0b', display: 'inline-block' }} />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc', marginTop: '0.5rem' }}>
            {data?.telegram?.bot_info?.username ? `@${data.telegram.bot_info.username}` : 'Bot Service'}
          </div>
          <div style={{ fontSize: '13px', color: data?.telegram?.status === 'online' ? '#10b981' : '#f59e0b', marginTop: '0.25rem' }}>
            ● Status: {data?.telegram?.status?.toUpperCase() || 'UNKNOWN'}
          </div>
        </div>

        {/* Email Engine */}
        <div className="glass-panel stat-card" style={{ padding: '1.25rem', border: '1px solid rgba(212, 175, 55, 0.2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Email Service</span>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: data?.email?.configured ? '#10b981' : '#f59e0b', display: 'inline-block' }} />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc', marginTop: '0.5rem' }}>
            Brevo (Sendinblue)
          </div>
          <div style={{ fontSize: '13px', color: data?.email?.configured ? '#10b981' : '#f59e0b', marginTop: '0.25rem' }}>
            {data?.email?.configured ? '✓ API Key & Sender Active' : '⚠️ API Key Not Set'}
          </div>
        </div>

        {/* 24h Busy Engine */}
        <div className="glass-panel stat-card" style={{ padding: '1.25rem', border: '1px solid rgba(212, 175, 55, 0.2)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '13px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px' }}>24h Busy Notice Engine</span>
            <span style={{ width: '10px', height: '10px', borderRadius: '50%', background: '#10b981', display: 'inline-block' }} />
          </div>
          <div style={{ fontSize: '20px', fontWeight: 700, color: '#f8fafc', marginTop: '0.5rem' }}>
            {data?.counts?.cases?.busy_notices_sent || 0} Sent
          </div>
          <div style={{ fontSize: '13px', color: '#10b981', marginTop: '0.25rem' }}>
            ✓ Auto-scan active (10m loop)
          </div>
        </div>
      </div>

      {/* Database Overview & Entity Counters */}
      <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ margin: '0 0 1.25rem 0', fontSize: '18px', color: 'var(--gold)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          📊 Live Database State & Record Counters
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          {/* User Breakdown */}
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ color: '#94a3b8', fontSize: '13px', fontWeight: 600 }}>USER ACCOUNTS</div>
            <div style={{ fontSize: '26px', fontWeight: 700, color: '#f8fafc', margin: '0.4rem 0' }}>{data?.counts?.users?.total || 0}</div>
            <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <span>👑 Owners: <strong>{data?.counts?.users?.owners || 0}</strong></span>
              <span>🛡️ Admins: <strong>{data?.counts?.users?.admins || 0}</strong></span>
              <span>👤 Users: <strong>{data?.counts?.users?.users || 0}</strong></span>
              <span>✉️ Verified: <strong>{data?.counts?.users?.verified_emails || 0}</strong></span>
            </div>
          </div>

          {/* Case Breakdown */}
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ color: '#94a3b8', fontSize: '13px', fontWeight: 600 }}>COUNSELLING CASES</div>
            <div style={{ fontSize: '26px', fontWeight: 700, color: '#f8fafc', margin: '0.4rem 0' }}>{data?.counts?.cases?.total || 0}</div>
            <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <span>🟢 Open: <strong>{data?.counts?.cases?.open || 0}</strong></span>
              <span>🟡 Assigned: <strong>{data?.counts?.cases?.assigned || 0}</strong></span>
              <span>🟣 Closed: <strong>{data?.counts?.cases?.closed || 0}</strong></span>
              <span>⏳ Unassigned &gt;24h: <strong style={{ color: data?.counts?.cases?.unassigned_over_24h > 0 ? '#f59e0b' : '#94a3b8' }}>{data?.counts?.cases?.unassigned_over_24h || 0}</strong></span>
            </div>
          </div>

          {/* Messages Breakdown */}
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)' }}>
            <div style={{ color: '#94a3b8', fontSize: '13px', fontWeight: 600 }}>MESSAGES & ACTIVITY</div>
            <div style={{ fontSize: '26px', fontWeight: 700, color: '#f8fafc', margin: '0.4rem 0' }}>
              {(data?.counts?.messages?.case_messages || 0) + (data?.counts?.messages?.internal_messages || 0)}
            </div>
            <div style={{ fontSize: '12px', color: '#94a3b8', display: 'flex', flexDirection: 'column', gap: '3px' }}>
              <span>💬 Case Chats: <strong>{data?.counts?.messages?.case_messages || 0}</strong></span>
              <span>🔒 System Chats: <strong>{data?.counts?.messages?.internal_messages || 0}</strong></span>
              <span>📋 Audit Logs: <strong>{data?.counts?.messages?.audit_logs || 0}</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* Technical Operations & Diagnostic Controls */}
      <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2rem' }}>
        <h2 style={{ margin: '0 0 1.25rem 0', fontSize: '18px', color: 'var(--gold)', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          🛠️ Technical Operations & Integrations
        </h2>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.25rem' }}>
          {/* Action 1: Run 24h Busy Check */}
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '16px', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                ⏳ 24h Busy Notice Scanner
              </div>
              <p style={{ color: '#94a3b8', fontSize: '13px', margin: '0.5rem 0 1rem 0' }}>
                Manually scan all open cases. If any case has been unassigned for 24+ hours, dispatches the polite reassurance message to the user on Telegram and records it in Audit Logs.
              </p>
            </div>
            <div>
              <LoadingButton
                className="button button-primary"
                onClick={() => runAction('run_busy_check')}
                loading={actionLoading['run_busy_check']}
                loadingText="Scanning cases..."
                style={{ width: '100%' }}
              >
                ▶ Run 24h Scan Now
              </LoadingButton>
              {actionFeedback['run_busy_check'] && (
                <div style={{ marginTop: '0.75rem', fontSize: '12px', padding: '0.5rem', borderRadius: '4px', background: actionFeedback['run_busy_check'].type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: actionFeedback['run_busy_check'].type === 'success' ? '#10b981' : '#ef4444' }}>
                  {actionFeedback['run_busy_check'].message}
                </div>
              )}
            </div>
          </div>

          {/* Action 2: Test Telegram Bot */}
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '16px', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                🤖 Telegram Bot Health Test
              </div>
              <p style={{ color: '#94a3b8', fontSize: '13px', margin: '0.5rem 0 1rem 0' }}>
                Sends an immediate ping to Telegram's <code>getMe</code> API endpoint to verify token validity, bot identity, and network reachability.
              </p>
            </div>
            <div>
              <LoadingButton
                className="button button-secondary"
                onClick={() => runAction('test_bot')}
                loading={actionLoading['test_bot']}
                loadingText="Testing connection..."
                style={{ width: '100%' }}
              >
                📡 Test Bot Connection
              </LoadingButton>
              {actionFeedback['test_bot'] && (
                <div style={{ marginTop: '0.75rem', fontSize: '12px', padding: '0.5rem', borderRadius: '4px', background: actionFeedback['test_bot'].type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: actionFeedback['test_bot'].type === 'success' ? '#10b981' : '#ef4444' }}>
                  {actionFeedback['test_bot'].message}
                </div>
              )}
            </div>
          </div>

          {/* Action 3: Test Email Service */}
          <div style={{ background: 'rgba(255,255,255,0.02)', padding: '1.25rem', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.05)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: '16px', color: '#f8fafc', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                ✉️ Email Delivery Diagnostic
              </div>
              <p style={{ color: '#94a3b8', fontSize: '13px', margin: '0.5rem 0 0.5rem 0' }}>
                Dispatches an immediate diagnostic email via Brevo to confirm SMTP/API reachability and DKIM deliverability.
              </p>
              <input
                type="email"
                className="input"
                placeholder="Target Email Address"
                value={testEmail}
                onChange={(e) => setTestEmail(e.target.value)}
                style={{ marginBottom: '0.75rem', fontSize: '13px', padding: '0.5rem 0.75rem' }}
              />
            </div>
            <div>
              <LoadingButton
                className="button button-secondary"
                onClick={() => runAction('test_email', { email: testEmail })}
                loading={actionLoading['test_email']}
                loadingText="Dispatching email..."
                style={{ width: '100%' }}
              >
                📨 Send Diagnostic Email
              </LoadingButton>
              {actionFeedback['test_email'] && (
                <div style={{ marginTop: '0.75rem', fontSize: '12px', padding: '0.5rem', borderRadius: '4px', background: actionFeedback['test_email'].type === 'success' ? 'rgba(16, 185, 129, 0.1)' : 'rgba(239, 68, 68, 0.1)', color: actionFeedback['test_email'].type === 'success' ? '#10b981' : '#ef4444' }}>
                  {actionFeedback['test_email'].message}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* 📢 Owner Broadcast Announcement to Counselees on Telegram */}
      <div className="glass-panel" style={{ padding: '1.5rem', marginBottom: '2rem', border: '1px solid rgba(212, 175, 55, 0.35)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1rem', marginBottom: '1rem' }}>
          <div>
            <h2 style={{ margin: 0, fontSize: '18px', color: 'var(--gold)', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              📢 Official Broadcast to Telegram Counselees
            </h2>
            <p style={{ margin: '0.35rem 0 0 0', color: '#94a3b8', fontSize: '13px' }}>
              Manually compose and send critical platform updates, rule changes, or encouraging messages directly to all registered students on Telegram.
            </p>
          </div>
          <span style={{ fontSize: '11px', padding: '0.35rem 0.65rem', borderRadius: '12px', background: 'rgba(212, 175, 55, 0.1)', color: 'var(--gold)', border: '1px solid rgba(212, 175, 55, 0.25)', fontWeight: 600 }}>
            🛡️ Safe Anti-Spam Throttled
          </span>
        </div>

        <div style={{ background: 'rgba(212, 175, 55, 0.05)', border: '1px solid rgba(212, 175, 55, 0.2)', borderRadius: '8px', padding: '0.85rem 1rem', marginBottom: '1.25rem', display: 'flex', alignItems: 'center', gap: '0.75rem', flexWrap: 'wrap' }}>
          <span style={{ fontSize: '18px' }}>🎓</span>
          <div style={{ fontSize: '13px', color: '#cbd5e1', lineHeight: '1.5', flex: 1 }}>
            <strong>Audience: All Counselees (Students) on Telegram.</strong> Staff and Counselors communicate internally via the <a href="/chat" style={{ color: 'var(--gold)', fontWeight: 600, textDecoration: 'underline' }}>System Chat</a>.
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', fontSize: '12px', color: '#cbd5e1', fontWeight: 600, marginBottom: '0.35rem' }}>
            Announcement Message (Supports Plain Text & Emojis)
          </label>
          <textarea
            className="input"
            rows={4}
            placeholder="Write your announcement or rule update here... e.g. 📢 Notice: Our counseling team has updated our guidelines. In case of urgent assistance..."
            value={broadcastMessage}
            onChange={(e) => setBroadcastMessage(e.target.value)}
            style={{ width: '100%', resize: 'vertical', fontSize: '13.5px', lineHeight: '1.5', fontFamily: 'inherit' }}
          />
        </div>

        {broadcastFeedback && (
          <div style={{
            marginBottom: '1rem',
            padding: '0.75rem 1rem',
            borderRadius: '6px',
            fontSize: '13px',
            background: broadcastFeedback.type === 'success' ? 'rgba(16, 185, 129, 0.12)' : 'rgba(239, 68, 68, 0.12)',
            border: `1px solid ${broadcastFeedback.type === 'success' ? '#10b981' : '#ef4444'}`,
            color: broadcastFeedback.type === 'success' ? '#10b981' : '#ef4444'
          }}>
            {broadcastFeedback.type === 'success' ? '✅ ' : '⚠️ '}{broadcastFeedback.message}
          </div>
        )}

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.75rem' }}>
          <button
            type="button"
            className="button button-primary"
            onClick={handleOpenBroadcastModal}
            disabled={broadcastLoading || !broadcastMessage.trim()}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}
          >
            📢 Preview & Dispatch Broadcast
          </button>
        </div>
      </div>

      {/* 💾 Database Backup & Restore */}
      <div className="glass-panel" style={{ marginTop: '2rem', padding: '1.75rem', border: '1px solid rgba(99,102,241,0.35)', background: 'rgba(99,102,241,0.04)' }}>
        <h3 style={{ color: '#818cf8', margin: '0 0 0.5rem 0', fontSize: '19px', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
          💾 Database Backup &amp; Restore
        </h3>
        <p style={{ margin: '0 0 1.5rem 0', color: '#94a3b8', fontSize: '13.5px', lineHeight: '1.6' }}>
          Download a complete backup of all platform data (users, cases, messages, audit logs, internal chat) or restore from a previous backup file.
          Restore is <strong style={{ color: '#c4b5fd' }}>non-destructive</strong> — existing records are never overwritten.
        </p>

        <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', alignItems: 'center' }}>
          <LoadingButton
            className="button button-primary"
            onClick={handleDownloadBackup}
            loading={isDownloadingBackup}
            loadingText="Generating backup..."
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}
          >
            📥 Download Full Backup
          </LoadingButton>

          <button
            className="button button-secondary"
            onClick={() => { setRestoreFeedback(null); restoreFileRef.current?.click(); }}
            style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 600 }}
          >
            📤 Restore from Backup
          </button>
          {/* Hidden file input */}
          <input
            ref={restoreFileRef}
            type="file"
            accept=".json,application/json"
            style={{ display: 'none' }}
            onChange={handleRestoreFileSelect}
          />
        </div>

        {backupFeedback && (
          <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', borderRadius: '6px', fontSize: '13px', background: backupFeedback.type === 'success' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', color: backupFeedback.type === 'success' ? '#10b981' : '#ef4444', border: `1px solid ${backupFeedback.type === 'success' ? '#10b981' : '#ef4444'}` }}>
            {backupFeedback.type === 'success' ? '✅ ' : '⚠️ '}{backupFeedback.message}
          </div>
        )}

        {restoreFeedback && (
          <div style={{ marginTop: '1rem', padding: '0.75rem 1rem', borderRadius: '6px', fontSize: '13px', background: restoreFeedback.type === 'success' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', color: restoreFeedback.type === 'success' ? '#10b981' : '#ef4444', border: `1px solid ${restoreFeedback.type === 'success' ? '#10b981' : '#ef4444'}` }}>
            {restoreFeedback.type === 'success' ? '✅ ' : '⚠️ '}{restoreFeedback.message}
          </div>
        )}
      </div>

      {/* ⚠️ Danger Zone: Pre-Launch System Reset */}
      <div className="card glass-panel" style={{ marginTop: '2rem', border: '1px solid rgba(239, 68, 68, 0.4)', background: 'rgba(239, 68, 68, 0.04)', padding: '1.75rem' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '1.5rem' }}>
          <div style={{ maxWidth: '750px' }}>
            <h3 style={{ color: '#ef4444', margin: 0, fontSize: '19px', display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              ⚠️ Danger Zone: Pre-Launch System Reset
            </h3>
            <p style={{ margin: '0.75rem 0 0 0', color: '#cbd5e1', fontSize: '14px', lineHeight: '1.6' }}>
              Purge all test cases, chat messages, internal reports, and non-owner accounts. <strong style={{ color: '#fff' }}>Your Owner account is strictly preserved.</strong> Database case auto-increment IDs will reset to start cleanly at <strong style={{ color: '#10b981' }}>#1</strong> for public launch.
            </p>
          </div>
          <button
            className="button"
            style={{
              background: 'linear-gradient(135deg, rgba(239, 68, 68, 0.8) 0%, rgba(220, 38, 38, 0.9) 100%)',
              color: '#ffffff',
              border: '1px solid #ef4444',
              fontWeight: 700,
              padding: '0.75rem 1.5rem',
              boxShadow: '0 4px 14px rgba(239, 68, 68, 0.3)',
              cursor: 'pointer'
            }}
            onClick={() => {
              setPurgeError('');
              setPurgeConfirmText('');
              setIsPurgeModalOpen(true);
            }}
          >
            🗑️ Reset System for Launch
          </button>
        </div>

        {purgeSuccess && (
          <div style={{ marginTop: '1.25rem', padding: '0.75rem 1rem', background: 'rgba(16, 185, 129, 0.1)', border: '1px solid #10b981', borderRadius: '6px', color: '#10b981', fontWeight: 600 }}>
            ✅ {purgeSuccess}
          </div>
        )}
      </div>

      {/* Portaled Reset System Confirmation Modal */}
      {isPurgeModalOpen && createPortal(
        <div
          className="modal-overlay"
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 99999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(8px)',
            padding: '1rem',
            boxSizing: 'border-box'
          }}
          onClick={() => !isPurging && setIsPurgeModalOpen(false)}
        >
          <div
            className="modal-content glass-panel"
            style={{
              maxHeight: '90vh',
              overflowY: 'auto',
              border: '1px solid #ef4444',
              maxWidth: '520px',
              width: '100%',
              padding: '2rem',
              background: '#0d1117',
              boxShadow: '0 20px 40px rgba(0,0,0,0.8), 0 0 30px rgba(239, 68, 68, 0.2)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ color: '#ef4444', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '20px' }}>
              ⚠️ Confirm Pre-Launch Reset
            </h2>
            <p style={{ color: '#cbd5e1', fontSize: '14px', lineHeight: '1.6' }}>
              This action is <strong style={{ color: '#ef4444' }}>irreversible</strong>. It will permanently delete:
            </p>
            <ul style={{ color: '#94a3b8', fontSize: '13px', lineHeight: '1.8', margin: '0.5rem 0 1rem 1.25rem' }}>
              <li>All counselling cases, user messages, and voice recordings</li>
              <li>All internal messages, chats, and shared files</li>
              <li>All user feedback, ratings, and audit trail logs</li>
              <li>All test admin, counselor, and user accounts</li>
            </ul>
            <p style={{ color: '#10b981', fontSize: '13px', background: 'rgba(16, 185, 129, 0.08)', padding: '0.6rem 0.8rem', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              🛡️ <strong>Owner Protection:</strong> Your Owner account and credentials are safe and will NOT be touched. The next case created will start cleanly at <strong>Case #1</strong>.
            </p>

            {purgeError && (
              <div className="form-error" style={{ marginBottom: '1rem', padding: '0.6rem', borderRadius: '4px', background: 'rgba(239, 68, 68, 0.1)', color: '#ef4444' }}>
                {purgeError}
              </div>
            )}

            <div className="form-group" style={{ marginTop: '1.25rem' }}>
              <label style={{ color: '#cbd5e1', fontSize: '13px' }}>Type <strong>RESET</strong> in all capital letters to confirm:</label>
              <input
                type="text"
                className="input"
                placeholder="RESET"
                value={purgeConfirmText}
                onChange={(e) => setPurgeConfirmText(e.target.value)}
                disabled={isPurging}
                autoFocus
                style={{ marginTop: '0.5rem', borderColor: purgeConfirmText === 'RESET' ? '#ef4444' : undefined, fontWeight: 700, letterSpacing: '1px' }}
              />
            </div>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button
                type="button"
                className="button button-secondary"
                onClick={() => setIsPurgeModalOpen(false)}
                disabled={isPurging}
                style={{ flex: 1 }}
              >
                CANCEL
              </button>
              <LoadingButton
                type="button"
                className="button"
                style={{
                  background: purgeConfirmText === 'RESET' ? '#ef4444' : 'rgba(239, 68, 68, 0.3)',
                  color: '#fff',
                  flex: 1,
                  cursor: purgeConfirmText === 'RESET' ? 'pointer' : 'not-allowed',
                  fontWeight: 700
                }}
                onClick={handlePurgeTestData}
                loading={isPurging}
                loadingText="Purging..."
                disabled={purgeConfirmText !== 'RESET'}
              >
                CONFIRM RESET
              </LoadingButton>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Portaled Telegram Broadcast Confirmation Modal */}
      {isBroadcastModalOpen && createPortal(
        <div
          className="modal-overlay"
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 99999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(8px)',
            padding: '1rem',
            boxSizing: 'border-box'
          }}
          onClick={() => !broadcastLoading && setIsBroadcastModalOpen(false)}
        >
          <div
            className="modal-content glass-panel"
            style={{
              maxHeight: '90vh',
              overflowY: 'auto',
              border: '1px solid var(--gold)',
              maxWidth: '560px',
              width: '100%',
              padding: '2rem',
              background: '#0d1117',
              boxShadow: '0 20px 40px rgba(0,0,0,0.8), 0 0 30px rgba(212, 175, 55, 0.2)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ color: 'var(--gold)', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '20px' }}>
              📢 Confirm Telegram Broadcast
            </h2>
            <p style={{ color: '#cbd5e1', fontSize: '14px', lineHeight: '1.6' }}>
              You are about to dispatch an official announcement to <strong>All Registered Counselees (Students)</strong> on Telegram.
            </p>

            <div style={{ background: 'rgba(255, 255, 255, 0.03)', border: '1px solid rgba(212, 175, 55, 0.2)', borderRadius: '8px', padding: '1rem', margin: '1rem 0' }}>
              <div style={{ fontSize: '11px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '0.5rem', fontWeight: 700 }}>
                Message Preview
              </div>
              <div style={{ color: '#f8fafc', fontSize: '13.5px', whiteSpace: 'pre-wrap', lineHeight: '1.6', maxHeight: '180px', overflowY: 'auto' }}>
                {broadcastMessage}
              </div>
            </div>

            <p style={{ color: '#10b981', fontSize: '12.5px', background: 'rgba(16, 185, 129, 0.08)', padding: '0.6rem 0.8rem', borderRadius: '6px', border: '1px solid rgba(16, 185, 129, 0.3)' }}>
              🛡️ <strong>Safety Guarantee:</strong> Throttled at 0.35s delay per message to fully comply with Telegram's strict anti-spam limits.
            </p>

            <div style={{ display: 'flex', gap: '1rem', marginTop: '1.5rem' }}>
              <button
                type="button"
                className="button button-secondary"
                onClick={() => setIsBroadcastModalOpen(false)}
                disabled={broadcastLoading}
                style={{ flex: 1 }}
              >
                Cancel
              </button>
              <LoadingButton
                type="button"
                className="button button-primary"
                style={{ flex: 1, fontWeight: 700 }}
                onClick={handleSendBroadcast}
                loading={broadcastLoading}
                loadingText="Broadcasting..."
              >
                Confirm & Dispatch
              </LoadingButton>
            </div>
          </div>
        </div>,
        document.body
      )}

      {/* Portaled Restore Confirmation Modal */}
      {isRestoreModalOpen && createPortal(
        <div
          className="modal-overlay"
          style={{
            position: 'fixed',
            inset: 0,
            zIndex: 99999,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            background: 'rgba(0, 0, 0, 0.85)',
            backdropFilter: 'blur(8px)',
            padding: '1rem',
            boxSizing: 'border-box'
          }}
          onClick={() => !isRestoring && setIsRestoreModalOpen(false)}
        >
          <div
            className="modal-content glass-panel"
            style={{
              maxHeight: '90vh',
              overflowY: 'auto',
              border: '1px solid rgba(99,102,241,0.6)',
              maxWidth: '540px',
              width: '100%',
              padding: '2rem',
              background: '#0d1117',
              boxShadow: '0 20px 40px rgba(0,0,0,0.8), 0 0 30px rgba(99,102,241,0.2)'
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h2 style={{ color: '#818cf8', margin: '0 0 1rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '20px' }}>
              📤 Confirm Database Restore
            </h2>
            <p style={{ color: '#cbd5e1', fontSize: '14px', lineHeight: '1.6' }}>
              You are about to restore platform data from the following backup file:
            </p>

            {restoreFileInfo && (
              <div style={{ background: 'rgba(99,102,241,0.08)', border: '1px solid rgba(99,102,241,0.3)', borderRadius: '8px', padding: '1rem', margin: '1rem 0' }}>
                <div style={{ fontSize: '12px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 700, marginBottom: '0.5rem' }}>Backup File</div>
                <div style={{ color: '#f8fafc', fontSize: '13.5px', fontWeight: 600 }}>📄 {restoreFileInfo.name}</div>
                <div style={{ color: '#94a3b8', fontSize: '12px', marginTop: '0.3rem' }}>Size: {restoreFileInfo.size}</div>
              </div>
            )}

            {restoreFileParsed && (
              <div style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: '8px', padding: '1rem', margin: '0.5rem 0 1rem 0' }}>
                <div style={{ fontSize: '12px', color: '#94a3b8', textTransform: 'uppercase', letterSpacing: '0.5px', fontWeight: 700, marginBottom: '0.75rem' }}>Backup Contents</div>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
                  {Object.entries(restoreFileParsed.counts || {}).map(([key, count]) => (
                    <div key={key} style={{ background: 'rgba(255,255,255,0.03)', borderRadius: '6px', padding: '0.5rem 0.75rem' }}>
                      <span style={{ color: '#94a3b8', fontSize: '12px', textTransform: 'capitalize' }}>{key.replace(/_/g, ' ')}: </span>
                      <span style={{ color: '#c4b5fd', fontWeight: 700 }}>{count}</span>
                    </div>
                  ))}
                </div>
                {restoreFileParsed.created_at && (
                  <div style={{ marginTop: '0.75rem', fontSize: '12px', color: '#64748b' }}>
                    Created: {new Date(restoreFileParsed.created_at).toLocaleString()}
                  </div>
                )}
              </div>
            )}

            <p style={{ color: '#10b981', fontSize: '12.5px', background: 'rgba(16,185,129,0.08)', padding: '0.6rem 0.8rem', borderRadius: '6px', border: '1px solid rgba(16,185,129,0.3)', margin: '0 0 1.5rem 0' }}>
              🛡️ <strong>Non-Destructive Restore:</strong> Existing records are never overwritten. Only missing data is re-imported from the backup.
            </p>

            <div style={{ display: 'flex', gap: '1rem' }}>
              <button
                type="button"
                className="button button-secondary"
                onClick={() => setIsRestoreModalOpen(false)}
                disabled={isRestoring}
                style={{ flex: 1 }}
              >
                Cancel
              </button>
              <LoadingButton
                type="button"
                className="button button-primary"
                style={{ flex: 1, fontWeight: 700, background: 'linear-gradient(135deg, #6366f1 0%, #818cf8 100%)' }}
                onClick={handleRestoreBackup}
                loading={isRestoring}
                loadingText="Restoring..."
              >
                ✅ Confirm Restore
              </LoadingButton>
            </div>
          </div>
        </div>,
        document.body
      )}
    </div>
  );
}

