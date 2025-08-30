import { useCallback } from 'react';
import ChatContainer from './ChatContainer';
import MessageInput from './MessageInput';
import SessionPanel from './SessionPanel';
import { useSession } from '../../hooks/useSession';
import { useNotification } from '../../contexts/NotificationContext';
import './styles.css';

export default function Chatbot() {
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
  
  const { showInfo, showSuccess, showError } = useNotification();
  
  const handleSendMessage = (message) => {
    sendQuery(message);
  };
  
  const handleSuggestedPrompt = (prompt) => {
    sendQuery(prompt);
  };
  
  const handleCommand = useCallback((command) => {
    switch (command.trim()) {
      case '/clear':
        resetSession();
        showSuccess('Session cleared');
        break;
      case '/help':
        showInfo('Available commands: /clear (clear session), /export (download conversation), /tools (show current tools), /help (show this message)');
        break;
      case '/export':
        const data = JSON.stringify(messages, null, 2);
        const blob = new Blob([data], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `conversation-${sessionId}.json`;
        a.click();
        URL.revokeObjectURL(url);
        showSuccess('Conversation exported successfully');
        break;
      case '/tools':
        showInfo(`Current tool set: ${toolSet}`);
        break;
      default:
        if (command.startsWith('/')) {
          showError(`Unknown command: ${command}`);
        }
    }
  }, [messages, sessionId, toolSet, resetSession, showSuccess, showInfo, showError]);
  
  const handleToolSetChange = useCallback(async (newToolSet) => {
    try {
      await changeToolSet(newToolSet);
      const toolSetNames = {
        ecommerce: 'E-commerce',
        agriculture: 'Agriculture',
        events: 'Events'
      };
      showSuccess(`Switched to ${toolSetNames[newToolSet]} tools`);
    } catch (err) {
      showError('Failed to change tool set');
    }
  }, [changeToolSet, showSuccess, showError]);

  const handleQuickAction = (action) => {
    // Check tool set and show warning if incorrect
    if (action === 'agriculture' || action === 'weather' || action === 'historical') {
      if (toolSet !== 'agriculture') {
        showInfo('Tip: For best results with agriculture and weather queries, switch to Agriculture tools using the dropdown below.');
      }
    } else if (action === 'search') {
      if (toolSet !== 'ecommerce') {
        showInfo('Tip: For best results with product searches, switch to E-commerce tools using the dropdown below.');
      }
    }
    
    const actionPrompts = {
      agriculture: 'What crops should I plant this season in Fresno, California?',
      weather: 'What is the current weather in Fresno, California?',
      historical: 'Compare the current weather in Fresno, California to the weather from the same date last year. Based on the historical weather patterns and temperature trends, provide specific recommendations for when to plant crops this season. Include analysis of temperature changes, precipitation patterns, and any notable weather events that might affect planting decisions.',
      search: 'Search for products'
    };
    
    if (actionPrompts[action]) {
      sendQuery(actionPrompts[action]);
    }
  };
  
  const handleLoadConversation = useCallback((conversationId) => {
    console.log('Loading conversation:', conversationId);
    // In a real implementation, this would load a saved conversation
    showInfo(`Loading conversation #${conversationId} (feature coming soon)`);
  }, [showInfo]);
  
  return (
    <div className="chatbot-view">
      <div className="chat-wrapper">
        <div className="chat-main">
          <div className="chat-interface">
            <ChatContainer 
              messages={messages}
              isLoading={isLoading}
              onSuggestedPrompt={handleSuggestedPrompt}
            />
            
            {error && (
              <div className="error-banner">
                <span>Error: {error}</span>
                <button onClick={resetSession}>Reset Session</button>
              </div>
            )}
            
            <MessageInput 
              onSendMessage={handleSendMessage}
              isLoading={isLoading}
              onCommand={handleCommand}
              toolSet={toolSet}
              onToolSetChange={handleToolSetChange}
            />
          </div>
        </div>
        
        <SessionPanel
          sessionId={sessionId}
          queryCount={queryCount}
          toolSet={toolSet}
          userId={userId}
          onQuickAction={handleQuickAction}
        />
      </div>
    </div>
  );
}