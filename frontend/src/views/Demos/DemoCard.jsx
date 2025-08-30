import { memo } from 'react';

function DemoCard({ demo, isSelected, isRunning, onRun, disabled }) {
  return (
    <div className={`demo-card ${isSelected ? 'selected' : ''} ${isRunning ? 'running' : ''}`}>
      <div className="demo-icon">{demo.icon}</div>
      <h3 className="demo-title">{demo.title}</h3>
      <p className="demo-description">{demo.description}</p>
      
      <div className="demo-tags">
        {demo.tags.map(tag => (
          <span key={tag} className="demo-tag">{tag}</span>
        ))}
      </div>
      
      <div className="demo-footer">
        <span className="demo-time">⏱️ {demo.estimatedTime}</span>
        <button 
          className="run-demo-btn"
          onClick={onRun}
          disabled={disabled || isRunning}
        >
          {isRunning ? 'Running...' : 'Run Demo'}
        </button>
      </div>
    </div>
  );
}

export default memo(DemoCard);