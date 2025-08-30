import './ThinkingIndicator.css';

export default function ThinkingIndicator() {
  return (
    <div className="thinking-indicator">
      <div className="thinking-avatar">
        <span className="thinking-icon">🤖</span>
      </div>
      <div className="thinking-content">
        <div className="thinking-text">AI is thinking</div>
        <div className="thinking-dots">
          <span className="thinking-dot"></span>
          <span className="thinking-dot"></span>
          <span className="thinking-dot"></span>
        </div>
      </div>
    </div>
  );
}