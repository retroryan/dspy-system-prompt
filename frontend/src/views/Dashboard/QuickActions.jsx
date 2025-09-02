import React from 'react';

const ACTIONS = [
  { id: 'demo', icon: '🎯', label: 'Quick Demo' },
  { id: 'logs', icon: '📊', label: 'View Logs' },
  { id: 'diagnostics', icon: '🔍', label: 'Diagnostics' },
  { id: 'docs', icon: '📚', label: 'Documentation' }
];

export default function QuickActions({ onAction }) {
  const handleAction = (actionId) => {
    if (onAction) {
      onAction(actionId);
    } else {
      alert(`Action: ${actionId}`);
    }
  };

  return (
    <div className="quick-actions">
      {ACTIONS.map(action => (
        <button 
          key={action.id}
          className="action-btn" 
          onClick={() => handleAction(action.id)}
        >
          <div className="action-icon">{action.icon}</div>
          <div className="action-label">{action.label}</div>
        </button>
      ))}
    </div>
  );
}