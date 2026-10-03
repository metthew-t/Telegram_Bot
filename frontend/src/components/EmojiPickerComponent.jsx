import { useState, useRef, useEffect } from 'react';
import EmojiPicker from 'emoji-picker-react';

export default function EmojiPickerComponent({ onEmojiClick, inputRef }) {
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
    <div style={{ position: 'relative' }}>
      <button
        type="button"
        className="emoji-picker-btn"
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
            right: '0',
            zIndex: 1000,
            boxShadow: '0 10px 40px rgba(0, 0, 0, 0.5)',
            borderRadius: '12px',
            overflow: 'hidden',
          }}
        >
          <EmojiPicker
            onEmojiClick={handleEmojiClick}
            width={350}
            height={450}
            theme="dark"
            searchPlaceholder="Search emoji..."
            previewConfig={{
              showPreview: false
            }}
          />
        </div>
      )}
    </div>
  );
}
