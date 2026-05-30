import { useEffect, useState, useRef } from 'react';
import { getUser } from '../auth.js';
import { fetchInternalMessages, sendInternalMessage } from '../api.js';

const POLL_INTERVAL = 10000; // 10 seconds

export default function SystemChatPage() {
    const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'report'
    const [messages, setMessages] = useState([]);
    const [messageContent, setMessageContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const messagesEndRef = useRef(null);
    const pollRef = useRef(null);
    const user = getUser();

    // Reset selected file when tab changes
    useEffect(() => {
        setSelectedFile(null);
    }, [activeTab]);

    // Fetch messages when the active tab changes
    useEffect(() => {
        fetchMessages(true);

        // Reset and start polling for the active tab's message type
        if (pollRef.current) clearInterval(pollRef.current);
        pollRef.current = setInterval(() => {
            fetchMessages(false);
        }, POLL_INTERVAL);

        return () => {
            if (pollRef.current) clearInterval(pollRef.current);
        };
    }, [activeTab]);

    // Scroll to the bottom when messages update
    useEffect(() => {
        scrollToBottom();
    }, [messages]);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    };

    const fetchMessages = async (isInitial = false) => {
        if (isInitial) setLoading(true);
        try {
            const data = await fetchInternalMessages({ message_type: activeTab });
            setMessages(data || []);
            setError('');
        } catch (err) {
            if (isInitial) setError(`Failed to load system ${activeTab === 'chat' ? 'chat' : 'reports'}`);
        } finally {
            if (isInitial) setLoading(false);
        }
    };

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setIsUploading(true);
        const reader = new FileReader();
        reader.onload = (event) => {
            setSelectedFile({
                name: file.name,
                content: event.target.result, // Base64 Data URL
            });
            setIsUploading(false);
        };
        reader.onerror = () => {
            setError("Failed to read local file.");
            setIsUploading(false);
        };
        reader.readAsDataURL(file);
    };

    const handleSendMessage = async (e) => {
        e.preventDefault();
        const contentText = messageContent.trim();
        const submissionContent = contentText || (selectedFile ? `Uploaded report: ${selectedFile.name}` : '');
        if (!submissionContent) return;

        try {
            await sendInternalMessage({
                content: submissionContent,
                message_type: activeTab, // explicitly submit the active tab type
                file_name: selectedFile ? selectedFile.name : null,
                file_content: selectedFile ? selectedFile.content : null,
            });
            setMessageContent('');
            setSelectedFile(null);
            setError('');
            await fetchMessages(false);
        } catch (err) {
            setError(`Failed to post ${activeTab === 'chat' ? 'message' : 'report'}`);
        }
    };

    const getSenderLabel = (msg) => {
        if (msg.sender === user?.id) return 'You';
        return msg.sender_name || 'Staff';
    };

    const isOwnMessage = (msg) => {
        return msg.sender === user?.id;
    };

    return (
        <div className="page-panel">
            <div className="panel-header">
                <h1>Internal control center</h1>
                <p>Private workspace for Admins and Owners to coordinate and track updates</p>
            </div>

            {/* Premium Glassmorphic Tab Selector */}
            <div className="filter-tabs glass-panel">
                <button
                    className={`tab ${activeTab === 'chat' ? 'active' : ''}`}
                    onClick={() => {
                        setMessages([]);
                        setActiveTab('chat');
                    }}
                >
                    💬 Chat Thread
                </button>
                <button
                    className={`tab ${activeTab === 'report' ? 'active' : ''}`}
                    onClick={() => {
                        setMessages([]);
                        setActiveTab('report');
                    }}
                >
                    📋 System Reports
                </button>
            </div>

            <div className="case-detail glass-panel" style={{ padding: 'var(--space-lg)' }}>
                {activeTab === 'chat' ? (
                    /* ─── CHAT SECTION ─── */
                    <div className="messages-section" style={{ marginTop: 0 }}>
                        <h3 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span>Internal Staff Chat</span>
                            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', fontWeight: 400 }}>
                                Auto-refreshes every 10s
                            </span>
                        </h3>

                        {loading ? (
                            <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
                                <div className="loading-spinner" />
                            </div>
                        ) : (
                            <div className="messages-list" style={{ height: '400px', overflowY: 'auto' }}>
                                {messages.length === 0 ? (
                                    <p className="empty-state">No staff messages yet. Start the conversation below.</p>
                                ) : (
                                    messages.map((msg) => (
                                        <div
                                            key={msg.id}
                                            className={`message-item ${isOwnMessage(msg) ? 'own-message' : 'other-message'}`}
                                        >
                                            <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)', marginBottom: '4px' }}>
                                                <strong style={{ color: 'var(--accent-primary-hover)' }}>{getSenderLabel(msg)}</strong>
                                                {msg.sender_role && (
                                                    <span className={`role-badge role-${msg.sender_role}`} style={{ fontSize: '0.625rem' }}>
                                                        {msg.sender_role}
                                                    </span>
                                                )}
                                            </div>
                                            <p style={{ margin: 0 }}>{msg.content}</p>
                                            <small>{new Date(msg.timestamp).toLocaleString()}</small>
                                        </div>
                                    ))
                                )}
                                <div ref={messagesEndRef} />
                            </div>
                        )}

                        <form className="form-inline" onSubmit={handleSendMessage}>
                            <input
                                type="text"
                                value={messageContent}
                                onChange={(e) => setMessageContent(e.target.value)}
                                placeholder="Post an internal coordinate update..."
                                required
                                disabled={loading}
                            />
                            <button className="button button-primary" type="submit" disabled={loading || !messageContent.trim()}>
                                Send
                            </button>
                        </form>
                    </div>
                ) : (
                    /* ─── SYSTEM REPORTS SECTION ─── */
                    <div className="messages-section" style={{ marginTop: 0 }}>
                        <h3 style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                            <span>Formal System Reports</span>
                            <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)', fontWeight: 400 }}>
                                Auto-refreshes every 10s
                            </span>
                        </h3>

                        {loading ? (
                            <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
                                <div className="loading-spinner" />
                            </div>
                        ) : (
                            <div className="messages-list" style={{ height: '400px', overflowY: 'auto', background: 'transparent', border: 'none', padding: 0 }}>
                                {messages.length === 0 ? (
                                    <p className="empty-state">No system reports filed yet. Log the first report below.</p>
                                ) : (
                                    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-md)' }}>
                                        {messages.map((msg) => (
                                            <div
                                                key={msg.id}
                                                style={{
                                                    padding: 'var(--space-md)',
                                                    background: 'rgba(245, 158, 11, 0.04)',
                                                    border: '1px solid rgba(245, 158, 11, 0.15)',
                                                    borderRadius: 'var(--radius-md)',
                                                    boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
                                                    animation: 'fadeIn 0.3s ease-out',
                                                    position: 'relative',
                                                    overflow: 'hidden'
                                                }}
                                            >
                                                {/* Left Accent indicator for Report card */}
                                                <div
                                                    style={{
                                                        position: 'absolute',
                                                        left: 0,
                                                        top: 0,
                                                        bottom: 0,
                                                        width: '4px',
                                                        background: 'var(--warning)'
                                                    }}
                                                />
                                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-xs)' }}>
                                                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)' }}>
                                                        <span style={{ fontSize: '1rem' }}>📢</span>
                                                        <strong style={{ color: 'var(--warning)', letterSpacing: '0.02em', textTransform: 'uppercase', fontSize: '0.8rem' }}>
                                                            System Report
                                                        </strong>
                                                    </div>
                                                    <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>
                                                        {new Date(msg.timestamp).toLocaleString()}
                                                    </span>
                                                </div>
                                                <p style={{ margin: 'var(--space-xs) 0 var(--space-sm) 0', color: 'var(--text-primary)', fontSize: 'var(--font-base)', lineHeight: 1.6 }}>
                                                    {msg.content}
                                                </p>
                                                {msg.file_name && (
                                                    <div style={{
                                                        marginTop: 'var(--space-sm)',
                                                        marginBottom: 'var(--space-sm)',
                                                        padding: 'var(--space-sm)',
                                                        background: 'rgba(255, 255, 255, 0.02)',
                                                        border: '1px dashed rgba(245, 158, 11, 0.25)',
                                                        borderRadius: 'var(--radius-sm)',
                                                        display: 'flex',
                                                        alignItems: 'center',
                                                        justifyContent: 'space-between',
                                                        gap: 'var(--space-sm)'
                                                    }}>
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)', overflow: 'hidden' }}>
                                                            <span style={{ fontSize: '1.2rem' }}>📄</span>
                                                            <span style={{ 
                                                                color: 'var(--text-primary)', 
                                                                fontSize: 'var(--font-sm)', 
                                                                fontWeight: 500,
                                                                textOverflow: 'ellipsis',
                                                                whiteSpace: 'nowrap',
                                                                overflow: 'hidden'
                                                            }} title={msg.file_name}>
                                                                {msg.file_name}
                                                            </span>
                                                        </div>
                                                        <a 
                                                            href={msg.file_content} 
                                                            download={msg.file_name}
                                                            style={{
                                                                display: 'inline-flex',
                                                                alignItems: 'center',
                                                                gap: '4px',
                                                                padding: '4px 12px',
                                                                background: 'rgba(245, 158, 11, 0.15)',
                                                                border: '1px solid rgba(245, 158, 11, 0.3)',
                                                                borderRadius: 'var(--radius-sm)',
                                                                color: 'var(--warning)',
                                                                fontSize: 'var(--font-xs)',
                                                                fontWeight: 600,
                                                                textDecoration: 'none',
                                                                cursor: 'pointer',
                                                                transition: 'all var(--transition-fast) ease'
                                                            }}
                                                            onMouseOver={(e) => {
                                                                e.currentTarget.style.background = 'rgba(245, 158, 11, 0.25)';
                                                                e.currentTarget.style.boxShadow = '0 0 10px rgba(245, 158, 11, 0.2)';
                                                            }}
                                                            onMouseOut={(e) => {
                                                                e.currentTarget.style.background = 'rgba(245, 158, 11, 0.15)';
                                                                e.currentTarget.style.boxShadow = 'none';
                                                            }}
                                                        >
                                                            📥 Download
                                                        </a>
                                                    </div>
                                                )}
                                                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)', paddingTop: 'var(--space-xs)', borderTop: '1px solid rgba(255,255,255,0.04)' }}>
                                                    <span style={{ fontSize: 'var(--font-xs)', color: 'var(--text-muted)' }}>Filed by:</span>
                                                    <strong style={{ fontSize: 'var(--font-xs)', color: 'var(--text-secondary)' }}>{getSenderLabel(msg)}</strong>
                                                    {msg.sender_role && (
                                                        <span className={`role-badge role-${msg.sender_role}`} style={{ fontSize: '0.55rem', padding: '1px 6px' }}>
                                                            {msg.sender_role}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                                <div ref={messagesEndRef} />
                            </div>
                        )}

                        <form className="form-inline" onSubmit={handleSendMessage} style={{ marginTop: 'var(--space-md)', flexDirection: 'column', alignItems: 'stretch', gap: 'var(--space-sm)' }}>
                            <div style={{ display: 'flex', gap: 'var(--space-sm)', width: '100%' }}>
                                <input
                                    type="text"
                                    value={messageContent}
                                    onChange={(e) => setMessageContent(e.target.value)}
                                    placeholder={selectedFile ? "Add some custom notes for the file report (optional)..." : "Log a formal system report or incident status update..."}
                                    disabled={loading || isUploading}
                                    style={{ flex: 1 }}
                                />
                                <input
                                    type="file"
                                    id="report-file-input"
                                    style={{ display: 'none' }}
                                    onChange={handleFileChange}
                                />
                                <button
                                    type="button"
                                    className="button"
                                    onClick={() => document.getElementById('report-file-input').click()}
                                    style={{
                                        background: 'rgba(255, 255, 255, 0.04)',
                                        color: 'var(--text-secondary)',
                                        border: '1px solid var(--border-subtle)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        whiteSpace: 'nowrap'
                                    }}
                                    disabled={loading || isUploading}
                                >
                                    📎 {selectedFile ? 'Change File' : 'Attach File'}
                                </button>
                                <button
                                    className="button button-success"
                                    type="submit"
                                    style={{
                                        background: 'rgba(245, 158, 11, 0.12)',
                                        color: 'var(--warning)',
                                        border: '1px solid rgba(245, 158, 11, 0.2)',
                                        whiteSpace: 'nowrap'
                                    }}
                                    disabled={loading || isUploading || (!messageContent.trim() && !selectedFile)}
                                >
                                    File Report
                                </button>
                            </div>
                            
                            {selectedFile && (
                                <div style={{
                                    display: 'flex',
                                    alignItems: 'center',
                                    gap: 'var(--space-xs)',
                                    background: 'rgba(245, 158, 11, 0.08)',
                                    border: '1px solid rgba(245, 158, 11, 0.25)',
                                    padding: '6px 12px',
                                    borderRadius: 'var(--radius-sm)',
                                    width: 'fit-content',
                                    animation: 'fadeIn 0.2s ease-out'
                                }}>
                                    <span style={{ fontSize: '1rem' }}>📁</span>
                                    <span style={{ color: 'var(--text-primary)', fontSize: 'var(--font-sm)', fontWeight: 500 }}>
                                        {selectedFile.name}
                                    </span>
                                    <button
                                        type="button"
                                        onClick={() => setSelectedFile(null)}
                                        style={{
                                            background: 'none',
                                            border: 'none',
                                            color: 'var(--danger)',
                                            cursor: 'pointer',
                                            fontSize: '1rem',
                                            fontWeight: 'bold',
                                            padding: '0 4px',
                                            marginLeft: '4px',
                                            display: 'inline-flex',
                                            alignItems: 'center'
                                        }}
                                        title="Remove file"
                                    >
                                        ×
                                    </button>
                                </div>
                            )}
                        </form>
                    </div>
                )}

                {error && <div className="form-error" style={{ marginTop: 'var(--space-md)' }}>{error}</div>}
            </div>
        </div>
    );
}
