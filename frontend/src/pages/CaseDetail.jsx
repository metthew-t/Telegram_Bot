import { useEffect, useState, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';

const POLL_INTERVAL = 10000; // 10 seconds

export default function CaseDetailPage() {
  const { id } = useParams();
  const [caseData, setCaseData] = useState(null);
  const [messages, setMessages] = useState([]);
  const [messageContent, setMessageContent] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [admins, setAdmins] = useState([]);
  const [selectedAdmin, setSelectedAdmin] = useState('');
  const [isAssigning, setIsAssigning] = useState(false);
  const messagesEndRef = useRef(null);
  const pollRef = useRef(null);
  const user = getUser();
  const navigate = useNavigate();

  useEffect(() => {
    fetchCaseDetail();
    if (user?.role === 'owner' || user?.role === 'admin') {
      fetchAdmins();
    }

    // Start polling
    pollRef.current = setInterval(() => {
      fetchMessages();
    }, POLL_INTERVAL);

    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, [id]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const fetchCaseDetail = async () => {
    setLoading(true);
    try {
      const data = await apiCall(`/api/cases/${id}/`, 'GET');
      setCaseData(data);
      await fetchMessages();
    } catch (err) {
      setError('Failed to load case details');
    } finally {
      setLoading(false);
    }
  };

  const fetchMessages = async () => {
    try {
      const allMessages = await apiCall(`/api/messages/?case=${id}`, 'GET');
      setMessages(allMessages || []);
    } catch (err) {
      // Silently fail for polling
    }
  };

  const fetchAdmins = async () => {
    try {
      const data = await apiCall('/api/users/', 'GET');
      setAdmins((data || []).filter((u) => u.role === 'admin'));
    } catch (err) {
      // Owner-only endpoint; admin won't have access to full user list
      // Admins will still see the self-assign button
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!messageContent.trim()) return;
    try {
      await apiCall('/api/messages/', 'POST', {
        case: parseInt(id),
        content: messageContent,
      });
      setMessageContent('');
      setError('');
      await fetchMessages();
    } catch (err) {
      setError('Failed to send message');
    }
  };

  const handleAssignCase = async (adminId) => {
    const assignId = adminId || selectedAdmin;
    if (!assignId) {
      alert('Please select an admin');
      return;
    }
    setIsAssigning(true);
    try {
      await apiCall(`/api/cases/${id}/assign/`, 'POST', {
        admin_id: parseInt(assignId),
      });
      setSelectedAdmin('');
      await fetchCaseDetail();
    } catch (err) {
      alert('Failed to assign case');
    } finally {
      setIsAssigning(false);
    }
  };

  const handleCloseCase = async () => {
    if (!window.confirm('Are you sure you want to close this case?')) return;
    try {
      await apiCall(`/api/cases/${id}/close/`, 'POST');
      await fetchCaseDetail();
    } catch (err) {
      alert('Failed to close case');
    }
  };

  const getSenderLabel = (msg) => {
    if (msg.sender?.label) return msg.sender.label;
    if (msg.sender?.username) return msg.sender.username;
    return 'Unknown';
  };

  const isOwnMessage = (msg) => {
    return msg.sender?.label === 'You' || msg.sender?.id === user?.id;
  };

  if (loading) return <div className="page-panel"><div className="loading-spinner" /></div>;
  if (error && !caseData) return <div className="page-panel"><div className="form-error">{error}</div></div>;
  if (!caseData) return <div className="page-panel"><p className="empty-state">Case not found</p></div>;

  const canAssign = user?.role === 'owner' || user?.role === 'admin';
  const canReassign = user?.role === 'owner';
  const showAssignSection =
    canAssign && (caseData.status === 'open' || (canReassign && caseData.status === 'assigned'));

  return (
    <div className="page-panel">
      <button className="back-button" onClick={() => navigate(-1)}>
        ← Back
      </button>

      <div className="case-detail glass-panel">
        <div className="case-header">
          <div>
            <h1>{caseData.title}</h1>
            <p className="case-id">Case #{caseData.id}</p>
          </div>
          <div className="case-actions">
            <span className={`status-badge status-${caseData.status}`}>
              {caseData.status}
            </span>
          </div>
        </div>

        <div className="case-info">
          <p><strong>Description:</strong></p>
          <p>{caseData.description}</p>
          {user?.role === 'owner' && caseData.user && (
            <p style={{ marginTop: '0.5rem' }}>
              <strong>Submitted by:</strong>{' '}
              {caseData.user?.username || caseData.user?.label || 'Anonymous'}
            </p>
          )}
          {caseData.assigned_admin && (
            <p style={{ marginTop: '0.5rem' }}>
              <strong>Assigned to:</strong>{' '}
              {caseData.assigned_admin?.label || caseData.assigned_admin?.username || 'Admin'}
            </p>
          )}
          <p style={{ marginTop: '0.5rem', fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>
            Created: {new Date(caseData.created_at).toLocaleString()}
            {caseData.updated_at && ` · Updated: ${new Date(caseData.updated_at).toLocaleString()}`}
          </p>
        </div>

        {/* Assign / Reassign Section */}
        {showAssignSection && (
          <div className="assign-section">
            <h3>
              {caseData.status === 'assigned' ? 'Reassign Case' : 'Assign Case'}
            </h3>
            {admins.length > 0 ? (
              <div className="form-inline">
                <select
                  value={selectedAdmin}
                  onChange={(e) => setSelectedAdmin(e.target.value)}
                >
                  <option value="">Select an admin...</option>
                  {admins.map((admin) => (
                    <option key={admin.id} value={admin.id}>
                      {admin.username}
                    </option>
                  ))}
                </select>
                <button
                  className="button button-primary"
                  onClick={() => handleAssignCase()}
                  disabled={isAssigning || !selectedAdmin}
                >
                  {isAssigning ? 'Assigning...' : caseData.status === 'assigned' ? 'Reassign' : 'Assign'}
                </button>
              </div>
            ) : user?.role === 'admin' ? (
              <button
                className="button button-primary"
                onClick={() => handleAssignCase(user.id)}
                disabled={isAssigning}
              >
                {isAssigning ? 'Assigning...' : 'Assign to Myself'}
              </button>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>No admins available</p>
            )}
          </div>
        )}

        {/* Messages Section */}
        <div className="messages-section">
          <h3>
            Conversation
            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', fontWeight: 400, marginLeft: '0.5rem' }}>
              Auto-refreshes every 10s
            </span>
          </h3>
          <div className="messages-list">
            {messages.length === 0 ? (
              <p className="empty-state">No messages yet. Start the conversation below.</p>
            ) : (
              messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`message-item ${isOwnMessage(msg) ? 'own-message' : 'other-message'}`}
                >
                  <strong>{getSenderLabel(msg)}</strong>
                  {msg.sender_role && (
                    <span
                      className={`role-badge role-${msg.sender_role}`}
                      style={{ marginLeft: '0.5rem', fontSize: '0.625rem' }}
                    >
                      {msg.sender_role}
                    </span>
                  )}
                  <p>{msg.content}</p>
                  <small>{new Date(msg.timestamp).toLocaleString()}</small>
                </div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Send Message Form */}
          {caseData.status !== 'closed' && (
            <form className="form-inline" onSubmit={handleSendMessage}>
              <input
                type="text"
                value={messageContent}
                onChange={(e) => setMessageContent(e.target.value)}
                placeholder="Type your message..."
                required
              />
              <button className="button button-primary" type="submit">
                Send
              </button>
            </form>
          )}

          {error && <div className="form-error" style={{ marginTop: '0.5rem' }}>{error}</div>}
        </div>

        {/* Close Case Button */}
        {caseData.status !== 'closed' && (
          <div className="case-actions">
            <button className="button button-danger" onClick={handleCloseCase}>
              Close Case
            </button>
          </div>
        )}

        {caseData.status === 'closed' && (
          <div style={{
            textAlign: 'center',
            padding: 'var(--space-lg)',
            marginTop: 'var(--space-lg)',
            background: 'var(--success-bg)',
            borderRadius: 'var(--radius-md)',
            border: '1px solid rgba(16, 185, 129, 0.2)',
          }}>
            <p style={{ color: 'var(--success)', fontWeight: 600 }}>
              This case has been closed
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
