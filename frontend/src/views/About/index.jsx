import React from 'react';
import './styles.css';

const SYSTEM_INFO = {
  version: '1.0.0',
  framework: 'DSPy',
  runtime: 'Python 3.11',
  lastUpdated: '2024-01-15',
  author: 'DSPy Team',
  license: 'MIT'
};

const FEATURES = [
  {
    icon: '🎯',
    title: 'Session-Based Architecture',
    description: 'AgentSession as the single entry point for all agent interactions with automatic context management'
  },
  {
    icon: '🔄',
    title: 'React Loop Pattern',
    description: 'Custom React implementation with manual control over each iteration and external tool execution'
  },
  {
    icon: '💾',
    title: 'Conversation Memory',
    description: 'Always-on conversation history with sliding window memory management'
  },
  {
    icon: '🔧',
    title: 'Tool Integration',
    description: 'Type-safe tool system with validation, test cases, and external execution control'
  },
  {
    icon: '📊',
    title: 'Performance Metrics',
    description: 'Track execution time, iterations, and tool usage with detailed observability'
  },
  {
    icon: '✅',
    title: 'Test Validation',
    description: '22+ e-commerce scenarios including complex multi-step workflows'
  }
];

const RESOURCES = [
  {
    title: 'Documentation',
    description: 'Complete API reference and guides',
    link: 'https://github.com/dspy/docs',
    icon: '📚'
  },
  {
    title: 'GitHub Repository',
    description: 'Source code and issue tracker',
    link: 'https://github.com/dspy/agent',
    icon: '💻'
  },
  {
    title: 'DSPy Framework',
    description: 'Learn more about the DSPy framework',
    link: 'https://dspy.ai',
    icon: '🌐'
  },
  {
    title: 'Community',
    description: 'Join our Discord community',
    link: 'https://discord.gg/dspy',
    icon: '💬'
  }
];

export default function About() {
  return (
    <div className="about-view">
      <header className="page-header">
        <h1 className="page-title">About DSPy Agent System</h1>
        <p className="page-subtitle">A powerful demonstration of agentic loop architecture</p>
      </header>

      <div className="about-container">
        {/* System Information */}
        <section className="info-section">
          <h2 className="section-title">System Information</h2>
          <div className="info-grid">
            {Object.entries(SYSTEM_INFO).map(([key, value]) => (
              <div key={key} className="info-item">
                <span className="info-label">{formatLabel(key)}:</span>
                <span className="info-value">{value}</span>
              </div>
            ))}
          </div>
        </section>

        {/* Key Features */}
        <section className="features-section">
          <h2 className="section-title">Key Features</h2>
          <div className="features-grid">
            {FEATURES.map((feature, index) => (
              <div key={index} className="feature-card">
                <div className="feature-icon">{feature.icon}</div>
                <h3 className="feature-title">{feature.title}</h3>
                <p className="feature-description">{feature.description}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Resources */}
        <section className="resources-section">
          <h2 className="section-title">Resources & Links</h2>
          <div className="resources-grid">
            {RESOURCES.map((resource, index) => (
              <a 
                key={index} 
                href={resource.link}
                className="resource-card"
                target="_blank"
                rel="noopener noreferrer"
              >
                <div className="resource-icon">{resource.icon}</div>
                <div className="resource-content">
                  <h4 className="resource-title">{resource.title}</h4>
                  <p className="resource-description">{resource.description}</p>
                </div>
                <div className="resource-arrow">→</div>
              </a>
            ))}
          </div>
        </section>

        {/* Architecture Overview */}
        <section className="architecture-section">
          <h2 className="section-title">Architecture Overview</h2>
          <div className="architecture-content">
            <div className="architecture-diagram">
              <div className="arch-layer">
                <div className="arch-component">Frontend (React + Vite)</div>
                <div className="arch-arrow">↓</div>
                <div className="arch-component">API Service (FastAPI)</div>
                <div className="arch-arrow">↓</div>
                <div className="arch-component">AgentSession</div>
                <div className="arch-arrow">↓</div>
                <div className="arch-component">React Loop + Tools</div>
                <div className="arch-arrow">↓</div>
                <div className="arch-component">DSPy Framework</div>
              </div>
            </div>
            <div className="architecture-description">
              <h3>How it Works</h3>
              <ol className="architecture-steps">
                <li>User submits query through the React frontend</li>
                <li>API service receives request and creates/retrieves session</li>
                <li>AgentSession manages context and conversation history</li>
                <li>React loop processes query with tool execution</li>
                <li>DSPy framework handles LLM interactions</li>
                <li>Results returned with full trajectory metadata</li>
              </ol>
            </div>
          </div>
        </section>
      </div>
    </div>
  );
}

function formatLabel(key) {
  return key
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, str => str.toUpperCase())
    .trim();
}