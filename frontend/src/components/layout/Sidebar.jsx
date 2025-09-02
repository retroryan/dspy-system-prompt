import React, { useState } from 'react';
import './Sidebar.css';

const NAVIGATION_ITEMS = [
  { id: 'chatbot', label: 'Chatbot', icon: '💬' },
  { id: 'dashboard', label: 'Dashboard', icon: '🏠' },
  { id: 'demos', label: 'Demos', icon: '🚀' },
  { id: 'admin', label: 'Admin Settings', icon: '⚙️' },
  { id: 'advanced', label: 'Advanced', icon: '🤖' },
  { id: 'about', label: 'About', icon: 'ℹ️' }
];

export default function Sidebar({ currentView, onViewChange }) {
  const [isCollapsed, setIsCollapsed] = useState(false);

  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        <div className="logo">
          <div className="logo-icon">D</div>
          {!isCollapsed && <div className="logo-text">DSPy Agent</div>}
        </div>
        <button 
          className="collapse-btn"
          onClick={() => setIsCollapsed(!isCollapsed)}
          title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          {isCollapsed ? '→' : '←'}
        </button>
      </div>
      
      <nav>
        <ul className="nav-menu">
          {NAVIGATION_ITEMS.map(item => (
            <li key={item.id} className="nav-item">
              <button
                className={`nav-link ${currentView === item.id ? 'active' : ''}`}
                onClick={() => onViewChange(item.id)}
                title={isCollapsed ? item.label : ''}
              >
                <span className="nav-icon">{item.icon}</span>
                {!isCollapsed && <span>{item.label}</span>}
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}