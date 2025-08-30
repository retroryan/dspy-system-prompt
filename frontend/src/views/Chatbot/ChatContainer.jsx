import React from 'react';
import Message from './Message';
import WelcomeScreen from './WelcomeScreen';
import LoadingIndicator from '../../components/LoadingIndicator';

export default function ChatContainer({ messages, isLoading, onSuggestedPrompt }) {
  const hasMessages = messages && messages.length > 0;
  
  return (
    <div className="chat-container">
      <div className="chat-messages" id="chatMessages">
        {!hasMessages ? (
          <WelcomeScreen onSuggestedPrompt={onSuggestedPrompt} />
        ) : (
          <>
            {messages.map((message, index) => (
              <Message key={index} message={message} />
            ))}
            {isLoading && <LoadingIndicator />}
          </>
        )}
      </div>
    </div>
  );
}