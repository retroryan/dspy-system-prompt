import React from 'react';

export default function LoopVisualization({ trajectory, selectedIteration, onIterationSelect, isProcessing }) {
  return (
    <div className="loop-visualization">
      {trajectory.length === 0 && !isProcessing && (
        <div className="empty-state">
          <div className="empty-icon">🔄</div>
          <p>Enter a query to visualize the agent's reasoning loop</p>
        </div>
      )}
      
      {(trajectory.length > 0 || isProcessing) && (
        <div className="loop-steps">
          {trajectory.map((step, index) => (
            <div 
              key={index}
              className={`loop-step ${selectedIteration === index ? 'selected' : ''}`}
              onClick={() => onIterationSelect(index)}
            >
              <div className="step-header">
                <span className="step-number">{index + 1}</span>
                <span className="step-tool">{step.tool.replace('_', ' ')}</span>
                <span className="step-time">{step.duration}s</span>
              </div>
              
              <div className="step-thought">{step.thought}</div>
              
              <div className="step-arrow">
                {index < trajectory.length - 1 && '↓'}
              </div>
            </div>
          ))}
          
          {isProcessing && (
            <div className="loop-step processing">
              <div className="processing-spinner"></div>
              <span>Processing next iteration...</span>
            </div>
          )}
        </div>
      )}
    </div>
  );
}