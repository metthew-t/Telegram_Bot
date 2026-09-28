import { useState, useRef, useEffect } from 'react';

export default function AudioPlayer({ voiceData, duration }) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [currentTime, setCurrentTime] = useState(0);
  const [audioDuration, setAudioDuration] = useState(duration || 0);
  const audioRef = useRef(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (voiceData) {
      // Create audio element
      const audio = new Audio(`data:audio/webm;base64,${voiceData}`);
      audioRef.current = audio;

      audio.onloadedmetadata = () => {
        setAudioDuration(Math.round(audio.duration));
      };

      audio.onended = () => {
        setIsPlaying(false);
        setCurrentTime(0);
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }

    return () => {
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [voiceData]);

  const togglePlay = () => {
    if (!audioRef.current) return;

    if (isPlaying) {
      audioRef.current.pause();
      setIsPlaying(false);
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    } else {
      audioRef.current.play();
      setIsPlaying(true);
      
      // Update current time
      intervalRef.current = setInterval(() => {
        if (audioRef.current) {
          setCurrentTime(Math.round(audioRef.current.currentTime));
        }
      }, 100);
    }
  };

  const handleSeek = (e) => {
    if (!audioRef.current) return;
    
    const seekTime = parseInt(e.target.value);
    audioRef.current.currentTime = seekTime;
    setCurrentTime(seekTime);
  };

  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      gap: '12px',
      padding: '10px 14px',
      background: 'linear-gradient(135deg, rgba(255, 215, 0, 0.08) 0%, rgba(255, 140, 0, 0.08) 100%)',
      border: '1px solid rgba(255, 215, 0, 0.25)',
      borderRadius: '8px',
      minWidth: '250px',
      maxWidth: '400px'
    }}>
      {/* Play/Pause Button */}
      <button
        onClick={togglePlay}
        style={{
          width: '36px',
          height: '36px',
          borderRadius: '50%',
          background: 'linear-gradient(135deg, var(--gold) 0%, var(--gold-light) 100%)',
          border: 'none',
          color: '#000',
          fontSize: '16px',
          cursor: 'pointer',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          transition: 'var(--transition)',
          boxShadow: '0 0 15px rgba(255, 215, 0, 0.4)'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.1)';
          e.currentTarget.style.boxShadow = '0 0 20px rgba(255, 215, 0, 0.6)';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)';
          e.currentTarget.style.boxShadow = '0 0 15px rgba(255, 215, 0, 0.4)';
        }}
      >
        {isPlaying ? '⏸' : '▶'}
      </button>

      {/* Waveform/Progress Bar */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '4px' }}>
        <input
          type="range"
          min="0"
          max={audioDuration}
          value={currentTime}
          onChange={handleSeek}
          style={{
            width: '100%',
            height: '4px',
            borderRadius: '2px',
            outline: 'none',
            background: `linear-gradient(to right, var(--gold) 0%, var(--gold) ${(currentTime / audioDuration) * 100}%, rgba(255, 215, 0, 0.2) ${(currentTime / audioDuration) * 100}%, rgba(255, 215, 0, 0.2) 100%)`,
            WebkitAppearance: 'none',
            cursor: 'pointer'
          }}
        />
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          fontSize: '11px',
          color: 'var(--gold-light)',
          fontWeight: 500
        }}>
          <span>{formatTime(currentTime)}</span>
          <span>{formatTime(audioDuration)}</span>
        </div>
      </div>

      {/* Voice Icon */}
      <div style={{
        fontSize: '20px',
        flexShrink: 0,
        animation: isPlaying ? 'pulse 1s infinite' : 'none'
      }}>
        🎤
      </div>
    </div>
  );
}
