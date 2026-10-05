import { useEffect, useState, useRef } from 'react';
import { getUser } from '../auth.js';
import { fetchInternalMessages, sendInternalMessage } from '../api.js';
import LoadingButton from '../components/LoadingButton.jsx';
import VoiceRecorder from '../components/VoiceRecorder.jsx';
import AudioPlayer from '../components/AudioPlayer.jsx';
import EmojiPickerComponent from '../components/EmojiPickerComponent.jsx';

const POLL_INTERVAL = 10000; // 10 seconds

export default function SystemChatPage() {
    const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'report'
    const [messages, setMessages] = useState([]);
    const [messageContent, setMessageContent] = useState('');
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState('');
    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isSending, setIsSending] = useState(false);
    const [showVoiceRecorder, setShowVoiceRecorder] = useState(false);
    const messagesEndRef = useRef(null);
    const pollRef = useRef(null);
    const chatInputRef = useRef(null);
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

    const handleSendMessage = async (e, voiceData = null) => {
        e?.preventDefault();
        
        if (voiceData) {
            // Sending voice message
            setIsSending(true);
            try {
                await sendInternalMessage({
                    content: '[Voice Message]',
                    message_type: activeTab,
                    message_format: 'voice',
                    voice_data: voiceData.voice_data,
                    voice_duration: voiceData.voice_duration,
                });
                setShowVoiceRecorder(false);
                setError('');
                await fetchMessages(false);
            } catch (err) {
                setError('Failed to send voice message');
            } finally {
                setIsSending(false);
            }
        } else {
            // Sending text or file message
            const contentText = messageContent.trim();
            const submissionContent = contentText || (selectedFile ? `Uploaded report: ${selectedFile.name}` : '');
            if (!submissionContent) return;

            setIsSending(true);
            try {
                await sendInternalMessage({
                    content: submissionContent,
                    message_type: activeTab,
                    message_format: 'text',
                    file_name: selectedFile ? selectedFile.name : null,
                    file_content: selectedFile ? selectedFile.content : null,
                });
                setMessageContent('');
                setSelectedFile(null);
                setError('');
                await fetchMessages(false);
            } catch (err) {
                setError('Failed to send message');
            } finally {
                setIsSending(false);
            }
        }
    };

    const handleDeleteMessage = async (messageId) => {
        if (user?.role !== 'owner') {
            alert('Only owners can delete messages');
            return;
        }
        
        if (!window.confirm('Delete this message permanently?')) return;
        
        try {
            const authData = JSON.parse(localStorage.getItem('telegram_counselling_auth'));
            const token = authData?.access;
            
            const response = await fetch(`https://telegram-bot-backend-bwu4.onrender.com/api/internal-messages/${messageId}/`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (response.ok) {
                // Remove message from list
                setMessages(prevMessages => prevMessages.filter(m => m.id !== messageId));
            } else {
                alert('Failed to delete message');
            }
        } catch (err) {
            console.error('Delete error:', err);
            alert('Failed to delete message');
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

            <div className="case-detail glass-panel" style={{ padding: 'var(--space-lg)', marginLeft: '20px', marginRight: '20px' }}>
                {activeTab === 'chat' ? (
                    /* ─── CHAT SECTION ─── */
                    <div className="messages-section" style={{ marginTop: 0, paddingLeft: '10px', paddingRight: '10px' }}>
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
                                            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px', flexWrap: 'wrap', justifyContent: 'space-between' }}>
                                                <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                                                    {/* Profile Photo */}
                                                    {msg.sender_profile_photo ? (
                                                        <img 
                                                            src={msg.sender_profile_photo} 
                                                            alt="Profile" 
                                                            style={{ 
                                                                width: '32px', 
                                                                height: '32px', 
                                                                borderRadius: '50%', 
                                                                objectFit: 'cover',
                                                                border: '2px solid rgba(255, 215, 0, 0.3)'
                                                            }} 
                                                        />
                                                    ) : (
                                                        <div style={{ 
                                                            width: '32px', 
                                                            height: '32px', 
                                                            borderRadius: '50%', 
                                                            background: 'linear-gradient(135deg, #6366f1, #818cf8)',
                                                            display: 'flex',
                                                            alignItems: 'center',
                                                            justifyContent: 'center',
                                                            fontSize: '14px',
                                                            fontWeight: 700,
                                                            color: '#fff'
                                                        }}>
                                                            {getSenderLabel(msg).charAt(0).toUpperCase()}
                                                        </div>
                                                    )}
                                                    <strong style={{ color: 'var(--accent-primary-hover)', fontSize: '15px', fontWeight: 700 }}>{getSenderLabel(msg)}</strong>
                                                    {msg.sender_role && (
                                                        <span className={`role-badge role-${msg.sender_role}`} style={{ fontSize: '11px', padding: '4px 10px' }}>
                                                            {msg.sender_role}
                                                        </span>
                                                    )}
                                                </div>
                                                
                                                {/* Delete Button (Owner Only) */}
                                                {user?.role === 'owner' && (
                                                    <button
                                                        onClick={() => handleDeleteMessage(msg.id)}
                                                        style={{
                                                            background: 'rgba(239, 68, 68, 0.1)',
                                                            border: '1px solid rgba(239, 68, 68, 0.3)',
                                                            color: '#ef4444',
                                                            padding: '4px 10px',
                                                            borderRadius: '6px',
                                                            cursor: 'pointer',
                                                            fontSize: '12px',
                                                            fontWeight: 600,
                                                            transition: 'all 0.2s'
                                                        }}
                                                        onMouseEnter={(e) => {
                                                            e.currentTarget.style.background = 'rgba(239, 68, 68, 0.2)';
                                                        }}
                                                        onMouseLeave={(e) => {
                                                            e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)';
                                                        }}
                                                    >
                                                        🗑️ Delete
                                                    </button>
                                                )}
                                            </div>
                                            
                                            {/* Voice Message */}
                                            {msg.message_format === 'voice' && msg.voice_data ? (
                                                <div style={{ margin: '8px 0' }}>
                                                    <AudioPlayer voiceData={msg.voice_data} duration={msg.voice_duration} />
                                                </div>
                                            ) : (
                                                <p style={{ margin: 0 }}>{msg.content}</p>
                                            )}
                                            
                                            <small>{new Date(msg.timestamp).toLocaleString()}</small>
                                        </div>
                                    ))
                                )}
                                <div ref={messagesEndRef} />
                            </div>
                        )}

                        {/* Voice Recorder or Regular Form */}
                        {showVoiceRecorder ? (
                            <div>
                                <VoiceRecorder 
                                    onRecordingComplete={(voiceData) => handleSendMessage(null, voiceData)} 
                                />
                                <button
                                    onClick={() => setShowVoiceRecorder(false)}
                                    className="button"
                                    style={{ marginTop: '8px', fontSize: '13px', padding: '6px 12px' }}
                                >
                                    ← Back to Text
                                </button>
                            </div>
                        ) : (
                            <form className="form-inline" onSubmit={handleSendMessage}>
                                <div className="input-with-emoji">
                                    <input
                                        ref={chatInputRef}
                                        type="text"
                                        value={messageContent}
                                        onChange={(e) => setMessageContent(e.target.value)}
                                        placeholder="Post an internal coordinate update..."
                                        required={!showVoiceRecorder}
                                        disabled={loading}
                                    />
                                    <EmojiPickerComponent
                                        onEmojiClick={(emoji) => {
                                            setMessageContent(prev => prev + emoji);
                                            if (chatInputRef.current) {
                                                chatInputRef.current.focus();
                                            }
                                        }}
                                        inputRef={chatInputRef}
                                    />
                                </div>
                                
                                {/* Voice button */}
                                <button
                                    type="button"
                                    onClick={() => setShowVoiceRecorder(true)}
                                    className="button"
                                    style={{
                                        padding: '10px',
                                        fontSize: '18px',
                                        minWidth: 'auto',
                                        background: 'linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 140, 0, 0.1) 100%)',
                                        border: '1px solid rgba(255, 215, 0, 0.3)'
                                    }}
                                    title="Send voice message"
                                >
                                    🎤
                                </button>
                                
                                <LoadingButton 
                                    className="button button-primary" 
                                    type="submit" 
                                    disabled={!messageContent.trim()}
                                    loading={isSending}
                                    loadingText="Sending..."
                                >
                                    Send
                                </LoadingButton>
                            </form>
                        )}
                    </div>
                ) : (
                    /* ─── SYSTEM REPORTS SECTION ─── */
                    <div className="messages-section" style={{ marginTop: 0, paddingLeft: '10px', paddingRight: '10px' }}>
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
                                                        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-xs)', overflow: 'hidden', flex: 1 }}>
                                                            <span style={{ fontSize: '1.2rem' }}>📄</span>
                                                            <span style={{ 
                                                                color: 'var(--text-primary)', 
                                                                fontSize: 'var(--font-sm)', 
                                                                fontWeight: 500,
                                                                textOverflow: 'ellipsis',
                                                                whiteSpace: 'nowrap',
                                                                overflow: 'hidden',
                                                                paddingLeft: '8px'
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
                                                                padding: '8px 16px',
                                                                background: 'linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%)',
                                                                border: '2px solid var(--gold)',
                                                                borderRadius: 'var(--radius-sm)',
                                                                color: '#000000',
                                                                fontSize: 'var(--font-sm)',
                                                                fontWeight: 700,
                                                                textDecoration: 'none',
                                                                cursor: 'pointer',
                                                                transition: 'all var(--transition-fast) ease',
                                                                boxShadow: '0 0 15px rgba(255, 215, 0, 0.4)',
                                                                textTransform: 'uppercase',
                                                                letterSpacing: '0.05em',
                                                                flexShrink: 0
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
                                        background: 'linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%)',
                                        color: '#000000',
                                        border: '2px solid var(--gold)',
                                        display: 'flex',
                                        alignItems: 'center',
                                        gap: '6px',
                                        whiteSpace: 'nowrap',
                                        fontWeight: 700,
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.05em',
                                        padding: '10px 20px',
                                        fontSize: '0.875rem',
                                        boxShadow: '0 0 15px rgba(255, 215, 0, 0.4)'
                                    }}
                                    disabled={loading || isUploading}
                                >
                                    📎 {selectedFile ? 'CHANGE FILE' : 'ATTACH FILE'}
                                </button>
                                <LoadingButton
                                    className="button button-success"
                                    type="submit"
                                    style={{
                                        background: 'linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%)',
                                        color: '#000000',
                                        border: '2px solid var(--gold)',
                                        whiteSpace: 'nowrap',
                                        fontWeight: 700,
                                        textTransform: 'uppercase',
                                        letterSpacing: '0.05em',
                                        padding: '10px 20px',
                                        fontSize: '0.875rem',
                                        boxShadow: '0 0 15px rgba(255, 215, 0, 0.4)'
                                    }}
                                    disabled={isUploading || (!messageContent.trim() && !selectedFile)}
                                    loading={isSending}
                                    loadingText="Reporting..."
                                >
                                    FILE REPORT
                                </LoadingButton>
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
