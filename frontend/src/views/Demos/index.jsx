import React, { useState, useEffect } from 'react';
import DemoCard from './DemoCard';
import TerminalOutput from './TerminalOutput';
import { api } from '../../services/api';
import { POLLING_INTERVALS } from '../../constants/app';
import './styles.css';

const AVAILABLE_DEMOS = [
  {
    id: 'agriculture',
    title: 'Agriculture Assistant',
    description: 'Complete farming workflow demonstrating weather analysis and planting decisions',
    icon: '🌾',
    tags: ['Weather', 'Planning', 'Analysis'],
    estimatedTime: '2 min'
  },
  {
    id: 'ecommerce',
    title: 'E-commerce Shopping',
    description: 'Complete shopping workflow from browsing to checkout with recommendations',
    icon: '🛒',
    tags: ['Shopping', 'Orders', 'Checkout'],
    estimatedTime: '3 min'
  },
  {
    id: 'weather',
    title: 'Weather Comparison',
    description: 'Compare weather conditions between multiple cities with detailed analysis',
    icon: '🌤️',
    tags: ['Weather', 'Comparison', 'Data'],
    estimatedTime: '1 min'
  },
  {
    id: 'memory',
    title: 'Memory Management',
    description: 'Test conversation memory and context management across multiple queries',
    icon: '🧠',
    tags: ['Memory', 'Context', 'Testing'],
    estimatedTime: '2 min'
  }
];

export default function Demos() {
  const [selectedDemo, setSelectedDemo] = useState(null);
  const [currentDemoId, setCurrentDemoId] = useState(null);
  const [isRunning, setIsRunning] = useState(false);
  const [output, setOutput] = useState([]);
  const [currentStep, setCurrentStep] = useState('');
  const [error, setError] = useState(null);
  
  // Real-time output polling
  useEffect(() => {
    let interval;
    
    if (currentDemoId && isRunning) {
      interval = setInterval(async () => {
        try {
          const outputResponse = await api.getDemoOutput(currentDemoId, output.length);
          
          if (outputResponse.output && outputResponse.output.length > 0) {
            setOutput(prev => [...prev, ...outputResponse.output]);
          }
          
          // Check demo status
          const demoInfo = await api.getDemo(currentDemoId);
          
          if (demoInfo.status === 'completed') {
            setIsRunning(false);
            setCurrentStep('');
            setCurrentStep(`✅ Demo completed! Total time: ${demoInfo.execution_time?.toFixed(1)}s`);
          } else if (demoInfo.status === 'failed') {
            setIsRunning(false);
            setCurrentStep('');
            setError(demoInfo.error_message || 'Demo execution failed');
          } else if (demoInfo.status === 'cancelled') {
            setIsRunning(false);
            setCurrentStep('');
            setCurrentStep('Demo cancelled');
          } else if (demoInfo.status === 'running') {
            // Update current step based on output
            const lastOutput = outputResponse.output?.[outputResponse.output.length - 1];
            if (lastOutput && lastOutput.type === 'info' && lastOutput.text.startsWith('Query')) {
              setCurrentStep(lastOutput.text);
            }
          }
          
        } catch (err) {
          console.error('Failed to fetch demo output:', err);
          if (err.status === 404) {
            // Demo not found, stop polling
            setIsRunning(false);
            setError('Demo not found');
          }
        }
      }, POLLING_INTERVALS.DEMO_OUTPUT); // Poll for demo output
    }
    
    return () => {
      if (interval) {
        clearInterval(interval);
      }
    };
  }, [currentDemoId, isRunning, output.length]);

  const runDemo = async (demoId) => {
    setSelectedDemo(demoId);
    setIsRunning(true);
    setOutput([]);
    setCurrentStep('Starting demo...');
    setError(null);
    setCurrentDemoId(null);

    try {
      // Start the demo via API
      const demoResponse = await api.startDemo(
        demoId,
        'demo_user',  // User ID
        true  // Verbose output
      );
      
      setCurrentDemoId(demoResponse.demo_id);
      setCurrentStep('Demo initialized...');
      
      // Initial output fetch
      const outputResponse = await api.getDemoOutput(demoResponse.demo_id, 0);
      if (outputResponse.output) {
        setOutput(outputResponse.output);
      }
      
    } catch (err) {
      console.error('Failed to start demo:', err);
      setError(err.message || 'Failed to start demo');
      setIsRunning(false);
      setCurrentStep('');
    }
  };

  const cancelDemo = async () => {
    if (!currentDemoId) return;
    
    try {
      await api.cancelDemo(currentDemoId);
      setIsRunning(false);
      setCurrentStep('Cancelling demo...');
    } catch (err) {
      console.error('Failed to cancel demo:', err);
      setError(err.message || 'Failed to cancel demo');
    }
  };

  const clearOutput = () => {
    setOutput([]);
    setSelectedDemo(null);
    setCurrentDemoId(null);
    setCurrentStep('');
    setError(null);
  };

  return (
    <div className="demos-view">
      <header className="page-header">
        <h1 className="page-title">Demo Runner</h1>
        <p className="page-subtitle">Explore pre-configured demos showcasing DSPy agent capabilities</p>
      </header>

      <div className="demos-container">
        <div className="demo-cards-section">
          <h2 className="section-title">Available Demos</h2>
          <div className="demo-cards-grid">
            {AVAILABLE_DEMOS.map(demo => (
              <DemoCard
                key={demo.id}
                demo={demo}
                isSelected={selectedDemo === demo.id}
                isRunning={isRunning && selectedDemo === demo.id}
                onRun={() => runDemo(demo.id)}
                disabled={isRunning}
              />
            ))}
          </div>
        </div>

        <div className="terminal-section">
          <div className="terminal-header">
            <h2 className="section-title">Terminal Output</h2>
            <div className="terminal-controls">
              {isRunning && (
                <span className="running-indicator">
                  <span className="pulse"></span>
                  {currentStep}
                </span>
              )}
              {error && (
                <span className="error-indicator">
                  ❌ {error}
                </span>
              )}
              <div className="terminal-buttons">
                {isRunning && (
                  <button 
                    className="cancel-btn"
                    onClick={cancelDemo}
                  >
                    Cancel Demo
                  </button>
                )}
                <button 
                  className="clear-btn"
                  onClick={clearOutput}
                  disabled={isRunning}
                >
                  Clear Output
                </button>
              </div>
            </div>
          </div>
          <TerminalOutput 
            output={output}
            isRunning={isRunning}
            error={error}
          />
        </div>
      </div>
    </div>
  );
}