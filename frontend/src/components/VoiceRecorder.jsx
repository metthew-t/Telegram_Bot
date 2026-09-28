import { useState, useRef } from 'react';

export default function VoiceRecorder({ onRecordingComplete }) {
  const [isRecording, setIsRecording] = useState(false);
  const [recordingTime, setRecordingTime] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        
        // Convert to base64
        const reader = new FileReader();
        reader.readAsDataURL(audioBlob);
        reader.onloadend = () => {
          const base64data = reader.result.split(',')[1];
          
          // Calculate duration
          const audio = new Audio(URL.createObjectURL(audioBlob));
          audio.onloadedmetadata = () => {
            onRecordingComplete({
              voice_data: base64data,
              voice_duration: Math.round(audio.duration),
              message_type: 'voice'
            });
          };
        };

        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
      setRecordingTime(0);

      // Start timer
      timerRef.current = setInterval(() => {
        setRecordingTime(prev => prev + 1);
      }, 1000);

    } catch (error) {
      console.error('Error accessing microphone:', error);
      alert('Could not access microphone. Please grant permission.');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }
    }
  };

  const cancelRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setRecordingTime(0);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
        timerRef.current = null;
      }

      // Stop all tracks without saving
      mediaRecorderRef.current.stream.getTracks().forEach(track => track.stop());
    }
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (isRecording) {
    return (
      <div style={{
        display: 'flex',
        alignItems: 'center',
        gap: '12px',
        padding: '12px',
        background: 'linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 140, 0, 0.1) 100%)',
        border: '1px solid rgba(255, 215, 0, 0.3)',
        borderRadius: '8px',
        animation: 'pulse 2s infinite'
      }}>
        <div style={{
          width: '12px',
          height: '12px',
          background: '#ef4444',
          borderRadius: '50%',
          animation: 'blink 1s infinite'
        }} />
        <span style={{ 
          color: 'var(--gold)', 
          fontWeight: 600,
          flex: 1
        }}>
          Recording... {formatTime(recordingTime)}
        </span>
        <button
          onClick={stopRecording}
          className="button button-primary"
          style={{ 
            padding: '6px 16px',
            fontSize: '13px',
            minWidth: 'auto'
          }}
        >
          ✓ Done
        </button>
        <button
          onClick={cancelRecording}
          className="button"
          style={{ 
            padding: '6px 16px',
            fontSize: '13px',
            minWidth: 'auto',
            background: 'rgba(239, 68, 68, 0.1)',
            border: '1px solid rgba(239, 68, 68, 0.3)',
            color: '#ef4444'
          }}
        >
          ✕ Cancel
        </button>
      </div>
    );
  }

  return (
    <button
      onClick={startRecording}
      className="button"
      style={{
        padding: '8px 16px',
        fontSize: '14px',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        background: 'linear-gradient(135deg, rgba(255, 215, 0, 0.1) 0%, rgba(255, 140, 0, 0.1) 100%)',
        border: '1px solid rgba(255, 215, 0, 0.3)',
        color: 'var(--gold)',
        minWidth: 'auto'
      }}
      title="Record voice message"
    >
      🎤 Record Voice
    </button>
  );
}
