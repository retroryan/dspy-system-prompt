import React from 'react';
import { MESSAGE_ROLES } from '../../constants/messageRoles';

export default function Message({ message }) {
  const isUser = message.role === MESSAGE_ROLES.USER;
  const isAgent = message.role === MESSAGE_ROLES.AGENT;
  
  // Format timestamp
  const formatTime = (timestamp) => {
    if (!timestamp) return 'Just now';
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now - date;
    const minutes = Math.floor(diff / 60000);
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes} minute${minutes > 1 ? 's' : ''} ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours} hour${hours > 1 ? 's' : ''} ago`;
    return date.toLocaleDateString();
  };
  
  // Format content with metadata
  const formatContent = () => {
    if (!message.content) return '';
    
    // If there's metadata, display it
    if (message.metadata && isAgent) {
      const { execution_time, iterations, tools_used } = message.metadata;
      return (
        <div>
          <div className="message-text">{message.content}</div>
          {(execution_time || iterations || tools_used) && (
            <div className="message-metadata">
              {execution_time && <span>⏱️ {execution_time.toFixed(2)}s</span>}
              {iterations && <span>🔄 {iterations} iterations</span>}
              {tools_used && tools_used.length > 0 && (
                <span>🔧 {tools_used.join(', ')}</span>
              )}
            </div>
          )}
        </div>
      );
    }
    
    return <div className="message-text">{message.content}</div>;
  };
  
  return (
    <div className={`message ${isUser ? 'user' : 'agent'}`}>
      <div className="message-avatar">
        {isUser ? 'U' : 'AI'}
      </div>
      <div className="message-content">
        <div className="message-bubble">
          {formatContent()}
        </div>
        <div className="message-time">{formatTime(message.timestamp)}</div>
      </div>
    </div>
  );
}