import { useEffect, useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { getUser } from '../auth.js';
import { fetchInternalMessages, sendInternalMessage } from '../api.js';

const POLL_INTERVAL = 10000; // 10 seconds

export default function SystemChatPage() {
    const [messages, setMessages] = useState([]);
    const [messageContent, setMessageContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const messagesEndRef = useRef(null);
    const pollRef = useRef(null);
    const user = getUser();
    const navigate = useNavigate();

    useEffect(() => {
        fetchMessages(true);

        // Start polling
        pollRef.current = setInterval(() => {
            fetchMessages(false);
        }, POLL_INTERVAL);

        return () => {
            if (pollRef.current) clearInterval(pollRef.current);
        };
    }, []);

    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const fetchMessages = async (isInitial = false) => {
        if (isInitial) setLoading(true);
        try {
            const data = await fetchInternalMessages();
            setMessages(data || []);
        } catch (err) {
            if (isInitial) setError('Failed to load system chat');
        } finally {
            if (isInitial) setLoading(false);
        }
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        if (!messageContent.trim()) return;
        try {
            await sendInternalMessage({
                content: messageContent,
            });
            setMessageContent('');
            setError('');
            await fetchMessages(false);
        } catch (err) {
            setError('Failed to send message');
        }
    };

    const getSenderLabel = (msg) => {
        if (msg.sender === user?.id) return 'You';
        return msg.sender_name || 'Staff';
    };

    const isOwnMessage = (msg) => {
        return msg.sender === user?.id;
    };

    if (loading) return <div className="page-panel"><div className="loading-spinner" /></div>;

    return (
        <div className="page-panel">
            <div className="panel-header">
                <h1>Internal System Chat</h1>
                <p>Live communication between Admins and Owners</p>
            </div>

            <div className="case-detail glass-panel">
                <div className="messages-section">
                    <h3>
                        Internal Thread
                        <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', fontWeight: 400, marginLeft: '0.5rem' }}>
                            Auto-refreshes every 10s
                        </span>
                    </h3>
                    <div className="messages-list" style={{ height: '400px', overflowY: 'auto' }}>
                        {messages.length === 0 ? (
                            <p className="empty-states">No internal messages yet.</p>
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

                    <form className="form-inline" onSubmit={handleSendMessage}>
                        <input
                            type="text"
                            value={messageContent}
                            onChange={(e) => setMessageContent(e.target.value)}
                            placeholder="Post an internal update..."
                            required
                        />
                        <button className="button button-primary" type="submit">
                            Post
                        </button>
                    </form>

                    {error && <div className="form-error" style={{ marginTop: '0.5rem' }}>{error}</div>}
                </div>
            </div>
        </div>
    );
}
