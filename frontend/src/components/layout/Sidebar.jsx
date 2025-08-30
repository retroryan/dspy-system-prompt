import React from 'react';
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
  return (
    <aside className="sidebar">
      <div className="logo">
        <div className="logo-icon">D</div>
        <div className="logo-text">DSPy Agent</div>
      </div>
      
      <nav>
        <ul className="nav-menu">
          {NAVIGATION_ITEMS.map(item => (
            <li key={item.id} className="nav-item">
              <button
                className={`nav-link ${currentView === item.id ? 'active' : ''}`}
                onClick={() => onViewChange(item.id)}
              >
                <span className="nav-icon">{item.icon}</span>
                <span>{item.label}</span>
              </button>
            </li>
          ))}
        </ul>
      </nav>
    </aside>
  );
}