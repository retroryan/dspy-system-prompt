export default function SessionPanel({ 
  sessionId, 
  queryCount, 
  toolSet, 
  userId,
  onQuickAction
}) {
  const formatSessionId = (id) => {
    if (!id) return 'N/A';
    return id.length > 8 ? `#${id.substring(0, 4).toUpperCase()}` : id;
  };
  
  return (
    <div className="sidebar-panel">
      {/* Quick Actions */}
      <div className="panel-card">
        <div className="panel-header">
          <h3 className="panel-title">Quick Actions</h3>
        </div>
        <div className="quick-actions">
          <button className="quick-action" onClick={() => onQuickAction('demo')}>
            <div className="action-icon">🚀</div>
            <div className="action-label">Run Demo</div>
          </button>
          <button className="quick-action" onClick={() => onQuickAction('test')}>
            <div className="action-icon">🧪</div>
            <div className="action-label">Run Tests</div>
          </button>
          <button className="quick-action" onClick={() => onQuickAction('weather')}>
            <div className="action-icon">🌤️</div>
            <div className="action-label">Weather</div>
          </button>
          <button className="quick-action" onClick={() => onQuickAction('search')}>
            <div className="action-icon">🔍</div>
            <div className="action-label">Search</div>
          </button>
        </div>
      </div>
      
      {/* Session Context */}
      <div className="panel-card">
        <div className="panel-header">
          <h3 className="panel-title">Session Context</h3>
          <span className="panel-badge active">ACTIVE</span>
        </div>
        <div className="context-info">
          <div className="context-item">
            <span className="context-label">Session ID</span>
            <span className="context-value">{formatSessionId(sessionId)}</span>
          </div>
          <div className="context-item">
            <span className="context-label">User</span>
            <span className="context-value">{userId || 'Guest'}</span>
          </div>
          <div className="context-item">
            <span className="context-label">Messages</span>
            <span className="context-value">{queryCount * 2}</span>
          </div>
          <div className="context-item">
            <span className="context-label">Tool Set</span>
            <span className="context-value">{toolSet || 'ecommerce'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}