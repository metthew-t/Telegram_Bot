/**
 * LoadingButton — A drop-in replacement for <button> that shows an
 * animated spinner + shimmer when loading={true}.
 *
 * Props:
 *  loading    {boolean}  — show spinner state
 *  loadingText {string}  — optional label while loading (default: "")
 *  className  {string}   — forwarded to <button>
 *  ...rest               — all other <button> props
 */
export default function LoadingButton({
  loading = false,
  loadingText,
  children,
  className = '',
  disabled,
  ...rest
}) {
  return (
    <button
      className={`btn-loading-wrapper ${className} ${loading ? 'btn-is-loading' : ''}`}
      disabled={disabled || loading}
      {...rest}
    >
      {loading && (
        <span className="btn-spinner" aria-hidden="true">
          <span className="btn-spinner-ring" />
        </span>
      )}
      <span className={`btn-label ${loading ? 'btn-label-loading' : ''}`}>
        {loading && loadingText ? loadingText : children}
      </span>
    </button>
  );
}
