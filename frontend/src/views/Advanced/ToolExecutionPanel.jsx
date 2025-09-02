import React from 'react';

export default function ToolExecutionPanel({ tools, currentTool }) {
  return (
    <div className="tool-execution-panel">
      <div className="tools-grid">
        {tools.map(tool => (
          <div 
            key={tool.id}
            className={`tool-card ${tool.status === 'inactive' ? 'inactive' : ''} ${
              currentTool && currentTool.includes(tool.id) ? 'executing' : ''
            }`}
          >
            <div className="tool-header">
              <span className="tool-icon">{tool.icon}</span>
              <span className={`tool-status ${tool.status}`}>
                {tool.status === 'active' ? '●' : '○'}
              </span>
            </div>
            
            <h4 className="tool-name">{tool.name}</h4>
            
            <div className="tool-stats">
              <div className="tool-stat">
                <span className="stat-label">Executions</span>
                <span className="stat-value">{tool.executions}</span>
              </div>
              <div className="tool-stat">
                <span className="stat-label">Avg Time</span>
                <span className="stat-value">{tool.avgTime}</span>
              </div>
            </div>
            
            {currentTool && currentTool.includes(tool.id) && (
              <div className="tool-executing">
                <span className="executing-pulse"></span>
                Executing...
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}