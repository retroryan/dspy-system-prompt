import { useEffect, useRef } from 'react';
import Message from './Message';
import WelcomeScreen from './WelcomeScreen';
import ThinkingIndicator from '../../components/ThinkingIndicator';

export default function ChatContainer({ messages, isLoading, onSuggestedPrompt, onToolSetChange, onDemoQuery }) {
  const hasMessages = messages && messages.length > 0;
  const messagesEndRef = useRef(null);
  
  // Auto-scroll to bottom when new messages or loading state changes
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [messages, isLoading]);
  
  return (
    <div className="chat-container">
      <div className="chat-messages" id="chatMessages">
        {!hasMessages ? (
          <WelcomeScreen 
            onSuggestedPrompt={onSuggestedPrompt} 
            onToolSetChange={onToolSetChange}
            onDemoQuery={onDemoQuery}
          />
        ) : (
          <>
            {messages.map((message, index) => (
              <Message key={index} message={message} />
            ))}
            {isLoading && <ThinkingIndicator />}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>
    </div>
  );
}