import { useState, useRef, useEffect } from 'react';
import EmojiPicker from 'emoji-picker-react';

export default function EmojiPickerComponent({ onEmojiClick, inputRef, position = 'right' }) {
  const [showPicker, setShowPicker] = useState(false);
  const pickerRef = useRef(null);

  // Close picker when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (pickerRef.current && !pickerRef.current.contains(event.target)) {
        setShowPicker(false);
      }
    };

    if (showPicker) {
      document.addEventListener('mousedown', handleClickOutside);
    }

    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, [showPicker]);

  const handleEmojiClick = (emojiData) => {
    onEmojiClick(emojiData.emoji);
    setShowPicker(false);
  };

  return (
    <>
      <button
        type="button"
        className={`emoji-picker-btn ${position === 'left' ? 'emoji-picker-btn-left' : ''}`}
        onClick={() => setShowPicker(!showPicker)}
        title="Click to open emoji picker"
      >
        😊
      </button>

      {showPicker && (
        <div
          ref={pickerRef}
          style={{
            position: 'absolute',
            bottom: '50px',
            left: position === 'left' ? '0' : 'auto',
            right: position === 'left' ? 'auto' : '0',
            maxWidth: 'calc(100vw - 32px)',
            zIndex: 1000,
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
            borderRadius: '12px',
            overflow: 'hidden',
          }}
        >
          <EmojiPicker
            onEmojiClick={handleEmojiClick}
            width={Math.min(350, typeof window !== 'undefined' ? window.innerWidth - 32 : 320)}
            height={400}
            theme="dark"
            searchPlaceholder="Search emoji..."
            previewConfig={{
              showPreview: false
            }}
          />
        </div>
      )}
    </>
  );
}
