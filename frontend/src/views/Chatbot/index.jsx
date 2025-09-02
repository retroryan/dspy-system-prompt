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
  
  const handleSuggestedPrompt = useCallback(async (prompt, newSessionId = null) => {
    // If a new session ID is provided, use it for the query
    if (newSessionId) {
      await sendQuery(prompt, newSessionId);
    } else {
      await sendQuery(prompt);
    }
  }, [sendQuery]);
  
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
      const newSessionId = await changeToolSet(newToolSet);
      const toolSetNames = {
        ecommerce: 'E-commerce',
        agriculture: 'Agriculture',
        events: 'Events',
        real_estate_mcp: 'Real Estate'
      };
      showSuccess(`Switched to ${toolSetNames[newToolSet]} tools`);
      return newSessionId; // Return the new session ID
    } catch (err) {
      showError('Failed to change tool set');
      throw err;
    }
  }, [changeToolSet, showSuccess, showError]);

  const handleQuickAction = useCallback(async (action) => {
    const actionConfig = {
      agriculture: {
        toolSet: 'agriculture',
        prompt: 'Looking at historical trends from last year what is the likelihood of rain in Fresno in September and how much rain was received'
      },
      weather: {
        toolSet: 'agriculture',
        prompt: 'Compare the weather forecast for San Francisco, Los Angeles, and San Diego over the next 7 days. Which city would be best for outdoor activities like hiking and beach visits? Include temperature ranges, precipitation chances, and wind conditions in your analysis.'
      },
      real_estate: {
        toolSet: 'real_estate_mcp',
        prompt: 'Find cozy family home near good schools and parks in Oakland'
      },
      search: {
        toolSet: 'ecommerce',
        prompt: 'Help me find a laptop under $1000'
      }
    };
    
    const config = actionConfig[action];
    if (config) {
      try {
        // Change tool set if needed and send query
        if (config.toolSet !== toolSet) {
          const newSessionId = await handleToolSetChange(config.toolSet);
          await sendQuery(config.prompt, newSessionId);
        } else {
          await sendQuery(config.prompt);
        }
      } catch (err) {
        console.error('Failed to execute quick action:', err);
      }
    }
  }, [toolSet, handleToolSetChange, sendQuery]);
  
  const handleLoadConversation = useCallback((conversationId) => {
    console.log('Loading conversation:', conversationId);
    // In a real implementation, this would load a saved conversation
    showInfo(`Loading conversation #${conversationId} (feature coming soon)`);
  }, [showInfo]);
  
  // Handler for welcome screen demo queries that need tool set changes
  const handleDemoQuery = useCallback(async (prompt, toolSet) => {
    try {
      if (toolSet) {
        // Change tool set and get new session ID
        const newSessionId = await handleToolSetChange(toolSet);
        // Send query with the new session ID
        await handleSuggestedPrompt(prompt, newSessionId);
      } else {
        // Just send the query with current session
        await handleSuggestedPrompt(prompt);
      }
    } catch (err) {
      console.error('Failed to handle demo query:', err);
    }
  }, [handleToolSetChange, handleSuggestedPrompt]);

  return (
    <div className="chatbot-view">
      <div className="chat-wrapper">
        <div className="chat-main">
          <div className="chat-interface">
            <ChatContainer 
              messages={messages}
              isLoading={isLoading}
              onSuggestedPrompt={handleSuggestedPrompt}
              onToolSetChange={handleToolSetChange}
              onDemoQuery={handleDemoQuery}
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