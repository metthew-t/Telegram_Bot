import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getUser } from '../auth.js';
import { apiCall } from '../api.js';

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
  const user = getUser();
  const navigate = useNavigate();

  useEffect(() => {
    fetchCaseDetail();
    if (user?.role === 'owner') {
      fetchAdmins();
    }
  }, [id]);

  const fetchCaseDetail = async () => {
    setLoading(true);
    try {
      const data = await apiCall(`/api/cases/${id}/`, 'GET');
      setCaseData(data);
      
      // Fetch messages for this case
      const allMessages = await apiCall('/api/messages/', 'GET');
      setMessages(allMessages.filter((m) => m.case === id) || []);
    } catch (err) {
      setError('Failed to load case details');
    } finally {
      setLoading(false);
    }
  };

  const fetchAdmins = async () => {
    try {
      const data = await apiCall('/api/users/', 'GET');
      // Filter only admins
      setAdmins(data.filter((u) => u.role === 'admin') || []);
    } catch (err) {
      console.error('Failed to load admins');
    }
  };

  const handleSendMessage = async (e) => {
    e.preventDefault();
    try {
      await apiCall('/api/messages/', 'POST', {
        case: id,
        content: messageContent,
      });
      setMessageContent('');
      fetchCaseDetail(); // Refresh messages
    } catch (err) {
      setError('Failed to send message');
    }
  };

  const handleAssignCase = async () => {
    if (!selectedAdmin) {
      alert('Please select an admin');
      return;
    }
    setIsAssigning(true);
    try {
      await apiCall(`/api/cases/${id}/assign/`, 'POST', {
        admin_id: selectedAdmin,
      });
      setSelectedAdmin('');
      fetchCaseDetail();
      alert('Case assigned successfully');
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
      navigate('/');
    } catch (err) {
      alert('Failed to close case');
    }
  };

  if (loading) return <div className="page-panel">Loading...</div>;
  if (error) return <div className="page-panel error">{error}</div>;
  if (!caseData) return <div className="page-panel">Case not found</div>;

  return (
    <div className="page-panel">
      <button className="back-button" onClick={() => navigate('/')}>
        ← Back to Dashboard
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
          {caseData.assigned_admin && (
            <p><strong>Assigned to:</strong> {caseData.assigned_admin}</p>
          )}
        </div>

        {/* Assign Case Section (Owner only) */}
        {user?.role === 'owner' && caseData.status === 'open' && (
          <div className="assign-section">
            <h3>Assign Case to Admin</h3>
            {admins.length > 0 ? (
              <div className="form-inline">
                <select value={selectedAdmin} onChange={(e) => setSelectedAdmin(e.target.value)}>
                  <option value="">Select an admin...</option>
                  {admins.map((admin) => (
                    <option key={admin.id} value={admin.id}>
                      {admin.username}
                    </option>
                  ))}
                </select>
                <button
                  className="button button-primary"
                  onClick={handleAssignCase}
                  disabled={isAssigning}
                >
                  {isAssigning ? 'Assigning...' : 'Assign'}
                </button>
              </div>
            ) : (
              <p>No admins available</p>
            )}
          </div>
        )}

        {/* Messages Section */}
        <div className="messages-section">
          <h3>Conversation</h3>
          <div className="messages-list">
            {messages.length === 0 ? (
              <p className="empty-state">No messages yet</p>
            ) : (
              messages.map((msg) => (
                <div key={msg.id} className="message-item">
                  <strong>{msg.sender}</strong>
                  <p>{msg.content}</p>
                  <small>{new Date(msg.created_at).toLocaleString()}</small>
                </div>
              ))
            )}
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
        </div>

        {/* Close Case Button */}
        {caseData.status !== 'closed' && (
          <div className="case-actions">
            <button className="button button-danger" onClick={handleCloseCase}>
              Close Case
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
