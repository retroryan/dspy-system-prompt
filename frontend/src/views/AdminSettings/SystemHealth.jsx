import React from 'react';

export default function SystemHealth({ health, onAction }) {
  const getStatusColor = (status) => {
    switch (status) {
      case 'healthy': return '#10b981';
      case 'warning': return '#f59e0b';
      case 'error': return '#ef4444';
      default: return '#6b7280';
    }
  };
  
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', {
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };
  
  const handleActionClick = (action) => {
    if (onAction) {
      onAction(action);
    }
  };
  
  if (!health) {
    return (
      <div className="system-health">
        <h2 className="section-title">System Health Status</h2>
        <div className="health-loading">
          <div className="loading-spinner"></div>
          <p>Loading system health...</p>
        </div>
      </div>
    );
  }
  
  return (
    <div className="system-health">
      <h2 className="section-title">System Health Status</h2>
      
      <div className="health-overview">
        <div className="health-status">
          <span 
            className="status-indicator"
            style={{ backgroundColor: getStatusColor(health.status) }}
          ></span>
          <span className="status-text">
            System is {health.status}
          </span>
        </div>
        <div className="last-check">
          Last checked: {formatTime(health.lastCheck)}
        </div>
      </div>
      
      <div className="health-metrics">
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-icon">⏱️</span>
            <span className="metric-label">Uptime</span>
          </div>
          <div className="metric-value">{health.uptime}</div>
        </div>
        
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-icon">💾</span>
            <span className="metric-label">Memory Usage</span>
          </div>
          <div className="metric-value">
            {health.memory.used}MB / {health.memory.total}MB
          </div>
          <div className="metric-bar">
            <div 
              className="metric-bar-fill"
              style={{ width: `${(health.memory.used / health.memory.total) * 100}%` }}
            ></div>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-icon">🔥</span>
            <span className="metric-label">CPU Usage</span>
          </div>
          <div className="metric-value">{health.cpu}%</div>
          <div className="metric-bar">
            <div 
              className="metric-bar-fill"
              style={{ 
                width: `${health.cpu}%`,
                backgroundColor: health.cpu > 80 ? '#ef4444' : health.cpu > 60 ? '#f59e0b' : '#10b981'
              }}
            ></div>
          </div>
        </div>
        
        <div className="metric-card">
          <div className="metric-header">
            <span className="metric-icon">🔗</span>
            <span className="metric-label">Active Connections</span>
          </div>
          <div className="metric-value">{health.activeConnections}</div>
        </div>
      </div>
      
      <div className="health-actions">
        <button className="btn-secondary" onClick={() => handleActionClick('view_logs')}>
          <span>📊</span> View Logs
        </button>
        <button className="btn-secondary" onClick={() => handleActionClick('restart_services')}>
          <span>🔄</span> Restart Services
        </button>
        <button className="btn-secondary" onClick={() => handleActionClick('clear_cache')}>
          <span>💾</span> Clear Cache
        </button>
        <button className="btn-secondary" onClick={() => handleActionClick('export_diagnostics')}>
          <span>📥</span> Export Diagnostics
        </button>
      </div>
    </div>
  );
}