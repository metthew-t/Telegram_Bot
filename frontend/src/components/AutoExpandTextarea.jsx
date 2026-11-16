import React, { useRef, useEffect, forwardRef, useImperativeHandle } from 'react';

const AutoExpandTextarea = forwardRef(function AutoExpandTextarea(
  {
    value = '',
    onChange,
    onEnterSubmit,
    placeholder,
    disabled = false,
    required = false,
    minHeight = 42,
    maxHeight = 160,
    className = '',
    style = {},
    onFocus,
    onBlur,
    ...rest
  },
  ref
) {
  const internalRef = useRef(null);
  useImperativeHandle(ref, () => internalRef.current);

  const adjustHeight = () => {
    const el = internalRef.current;
    if (!el) return;

    // Reset height to compute actual scrollHeight accurately
    el.style.height = `${minHeight}px`;

    const scrollH = el.scrollHeight;

    if (scrollH <= minHeight) {
      el.style.height = `${minHeight}px`;
      el.style.overflowY = 'hidden';
    } else if (scrollH >= maxHeight) {
      el.style.height = `${maxHeight}px`;
      el.style.overflowY = 'auto';
    } else {
      el.style.height = `${scrollH}px`;
      el.style.overflowY = 'hidden';
    }
  };

  useEffect(() => {
    adjustHeight();
  }, [value]);

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      // Detect touch/mobile device
      const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
      if (isTouchDevice) {
        // On mobile: Enter always inserts newline, never sends
        // Don't prevent default — let the browser/keyboard handle the newline naturally
        return;
      }
      // On desktop: Enter sends, Shift+Enter for newline
      if (!e.shiftKey && onEnterSubmit) {
        e.preventDefault();
        onEnterSubmit(e);
      }
    }
  };

  return (
    <textarea
      ref={internalRef}
      value={value}
      onChange={(e) => {
        if (onChange) onChange(e);
        adjustHeight();
      }}
      onKeyDown={handleKeyDown}
      placeholder={placeholder}
      disabled={disabled}
      required={required}
      rows={1}
      onFocus={onFocus}
      onBlur={onBlur}
      className={`auto-expand-textarea ${className}`.trim()}
      style={{
        minHeight: `${minHeight}px`,
        maxHeight: `${maxHeight}px`,
        boxSizing: 'border-box',
        color: '#ffffff',
        caretColor: '#ffffff',
        ...style,
      }}
      {...rest}
    />
  );
});

export default AutoExpandTextarea;
