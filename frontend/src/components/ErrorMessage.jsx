export default function ErrorMessage({ message, onRetry }) {
  if (!message) return null
  return (
    <div className="error-card" role="alert">
      <span>{message}</span>
      {onRetry && <button className="button secondary small" onClick={onRetry}>重试</button>}
    </div>
  )
}
