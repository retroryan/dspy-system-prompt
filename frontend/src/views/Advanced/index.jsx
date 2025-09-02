import React, { useState, useEffect } from 'react';
import LoopVisualization from './LoopVisualization';
import ToolExecutionPanel from './ToolExecutionPanel';
import './styles.css';

const SAMPLE_TRAJECTORY = [
  {
    iteration: 1,
    thought: "I need to check the weather for Tokyo and Paris to compare them",
    tool: "weather_tool",
    args: { city: "Tokyo" },
    observation: "Tokyo: 22°C, Partly cloudy, Humidity: 65%",
    duration: 1.2
  },
  {
    iteration: 2,
    thought: "Now I need to get weather data for Paris",
    tool: "weather_tool",
    args: { city: "Paris" },
    observation: "Paris: 18°C, Sunny, Humidity: 45%",
    duration: 0.9
  },
  {
    iteration: 3,
    thought: "I have both weather data, let me compare and provide the analysis",
    tool: "final_answer",
    args: null,
    observation: "Tokyo is warmer at 22°C compared to Paris at 18°C. Tokyo has partly cloudy conditions with higher humidity (65%) while Paris is sunny with lower humidity (45%).",
    duration: 0.5
  }
];

const AVAILABLE_TOOLS = [
  { id: 'weather', name: 'Weather Tool', icon: '🌤️', executions: 234, avgTime: '1.2s', status: 'active' },
  { id: 'search', name: 'Search Tool', icon: '🔍', executions: 189, avgTime: '2.1s', status: 'active' },
  { id: 'calculator', name: 'Calculator', icon: '🧮', executions: 456, avgTime: '0.3s', status: 'active' },
  { id: 'memory', name: 'Memory Store', icon: '💾', executions: 78, avgTime: '0.5s', status: 'active' },
  { id: 'database', name: 'Database Query', icon: '🗄️', executions: 92, avgTime: '1.8s', status: 'inactive' },
  { id: 'api', name: 'API Caller', icon: '🔌', executions: 145, avgTime: '3.2s', status: 'active' }
];

export default function Advanced() {
  const [query, setQuery] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [trajectory, setTrajectory] = useState(SAMPLE_TRAJECTORY);
  const [selectedIteration, setSelectedIteration] = useState(null);
  const [tools, setTools] = useState(AVAILABLE_TOOLS);
  const [activeToolFilter, setActiveToolFilter] = useState('all');

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!query.trim() || isProcessing) return;

    setIsProcessing(true);
    setTrajectory([]);
    
    // Simulate step-by-step processing
    SAMPLE_TRAJECTORY.forEach((step, index) => {
      setTimeout(() => {
        setTrajectory(prev => [...prev, step]);
        if (index === SAMPLE_TRAJECTORY.length - 1) {
          setIsProcessing(false);
        }
      }, (index + 1) * 1500);
    });
  };

  const filteredTools = tools.filter(tool => {
    if (activeToolFilter === 'all') return true;
    return tool.status === activeToolFilter;
  });

  return (
    <div className="advanced-view">
      <header className="page-header">
        <h1 className="page-title">Advanced Chatbot</h1>
        <p className="page-subtitle">Interactive agent with real-time loop visualization</p>
      </header>

      <div className="advanced-container">
        <div className="input-section">
          <form onSubmit={handleSubmit} className="advanced-form">
            <input
              type="text"
              className="advanced-input"
              placeholder="Enter your query to see the agent's reasoning process..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              disabled={isProcessing}
            />
            <button 
              type="submit" 
              className="submit-btn"
              disabled={!query.trim() || isProcessing}
            >
              {isProcessing ? 'Processing...' : 'Analyze'}
            </button>
          </form>
        </div>

        <div className="visualization-grid">
          <div className="loop-section">
            <div className="section-header">
              <h2 className="section-title">React Loop Visualization</h2>
              <div className="loop-stats">
                <span className="stat-item">
                  <span className="stat-label">Iterations:</span>
                  <span className="stat-value">{trajectory.length}</span>
                </span>
                <span className="stat-item">
                  <span className="stat-label">Total Time:</span>
                  <span className="stat-value">
                    {trajectory.reduce((sum, t) => sum + t.duration, 0).toFixed(1)}s
                  </span>
                </span>
              </div>
            </div>
            <LoopVisualization 
              trajectory={trajectory}
              selectedIteration={selectedIteration}
              onIterationSelect={setSelectedIteration}
              isProcessing={isProcessing}
            />
          </div>

          <div className="tools-section">
            <div className="section-header">
              <h2 className="section-title">Tool Execution</h2>
              <div className="tool-filters">
                <button 
                  className={`filter-btn ${activeToolFilter === 'all' ? 'active' : ''}`}
                  onClick={() => setActiveToolFilter('all')}
                >
                  All
                </button>
                <button 
                  className={`filter-btn ${activeToolFilter === 'active' ? 'active' : ''}`}
                  onClick={() => setActiveToolFilter('active')}
                >
                  Active
                </button>
                <button 
                  className={`filter-btn ${activeToolFilter === 'inactive' ? 'active' : ''}`}
                  onClick={() => setActiveToolFilter('inactive')}
                >
                  Inactive
                </button>
              </div>
            </div>
            <ToolExecutionPanel 
              tools={filteredTools}
              currentTool={trajectory[trajectory.length - 1]?.tool}
            />
          </div>
        </div>

        {selectedIteration !== null && trajectory[selectedIteration] && (
          <div className="iteration-details">
            <h3 className="details-title">Iteration {selectedIteration + 1} Details</h3>
            <div className="details-grid">
              <div className="detail-item">
                <span className="detail-label">Thought:</span>
                <span className="detail-value">{trajectory[selectedIteration].thought}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Tool:</span>
                <span className="detail-value">{trajectory[selectedIteration].tool}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Arguments:</span>
                <span className="detail-value">
                  {trajectory[selectedIteration].args ? 
                    JSON.stringify(trajectory[selectedIteration].args) : 
                    'None'}
                </span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Observation:</span>
                <span className="detail-value">{trajectory[selectedIteration].observation}</span>
              </div>
              <div className="detail-item">
                <span className="detail-label">Duration:</span>
                <span className="detail-value">{trajectory[selectedIteration].duration}s</span>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}