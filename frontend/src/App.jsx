import { useState } from 'react';
import ChatWindow from './components/ChatWindow';
import ToolSetSelector from './components/ToolSetSelector';
import { useSession } from './hooks/useSession';
import './App.css';

export default function App() {
  const [inputValue, setInputValue] = useState('');
  const {
    sessionId,
    messages,
    isLoading,
    error,
    toolSet,
    queryCount,
    userId,
    sendQuery,
    resetSession,
    changeToolSet
  } = useSession();

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim() && !isLoading) {
      sendQuery(inputValue);
      setInputValue('');
    }
  };

  return (
    <div className="app">
      <header className="app-header">
        <h1>DSPy Agentic Loop Demo</h1>
        <div className="session-info">
          <span className="user-id">User: {userId}</span>
          {sessionId && (
            <span className="session-id">Session: {sessionId.substr(0, 8)}...</span>
          )}
          <span className="query-count">Queries: {queryCount}</span>
        </div>
        <ToolSetSelector 
          currentToolSet={toolSet} 
          onToolSetChange={changeToolSet}
          disabled={isLoading}
        />
      </header>

      <main className="app-main">
        <ChatWindow messages={messages} isLoading={isLoading} />
        
        {error && (
          <div className="error-message">
            <span>Error: {error}</span>
            <button onClick={resetSession}>Reset Session</button>
          </div>
        )}

        <form className="input-form" onSubmit={handleSubmit}>
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Type your message..."
            disabled={isLoading}
            className="message-input"
          />
          <button 
            type="submit" 
            disabled={isLoading || !inputValue.trim()}
            className="send-button"
          >
            Send
          </button>
        </form>

        {messages.length > 0 && (
          <button 
            onClick={resetSession}
            className="reset-button"
          >
            New Session
          </button>
        )}
      </main>
    </div>
  );
}
