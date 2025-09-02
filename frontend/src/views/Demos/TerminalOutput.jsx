import React, { useEffect, useRef } from 'react';

export default function TerminalOutput({ output, isRunning }) {
  const terminalRef = useRef(null);
  
  useEffect(() => {
    // Auto-scroll to bottom when new output is added
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [output]);
  
  const formatTime = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour12: false,
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
  };
  
  return (
    <div className="terminal-output" ref={terminalRef}>
      {output.length === 0 ? (
        <div className="terminal-empty">
          <span className="terminal-prompt">$</span>
          <span className="terminal-cursor">_</span>
          <span className="terminal-hint">Select a demo to begin...</span>
        </div>
      ) : (
        output.map((line, index) => (
          <div key={index} className={`terminal-line ${line.type}`}>
            <span className="terminal-timestamp">[{formatTime(line.timestamp)}]</span>
            {line.type === 'command' && <span className="terminal-prompt">$ </span>}
            <span className="terminal-text">{line.text}</span>
          </div>
        ))
      )}
      {isRunning && (
        <div className="terminal-line terminal-running">
          <span className="terminal-cursor blinking">▊</span>
        </div>
      )}
    </div>
  );
}