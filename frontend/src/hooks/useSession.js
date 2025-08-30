import { useState, useCallback, useEffect } from 'react';
import { api } from '../services/api';
import { MESSAGE_ROLES } from '../constants/messageRoles';

/**
 * Session management hook for DSPy agentic loop interaction
 */
export function useSession() {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [toolSet, setToolSet] = useState('ecommerce');
  const [queryCount, setQueryCount] = useState(0);
  const [userId] = useState('demo_user');

  // Generate unique message ID
  const generateId = () => `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;

  // Create session on mount
  useEffect(() => {
    const createSession = async () => {
      try {
        const response = await api.createSession(toolSet, userId);
        setSessionId(response.session_id);
      } catch (err) {
        setError(`Failed to create session: ${err.message}`);
        console.error('Failed to create session:', err);
      }
    };
    createSession();
  }, [toolSet, userId]);

  // Send query to session
  const sendQuery = useCallback(async (queryText) => {
    if (!queryText.trim() || !sessionId) return;

    setIsLoading(true);
    setError(null);

    // Add user message immediately
    const userMessage = {
      id: generateId(),
      content: queryText,
      role: MESSAGE_ROLES.USER,
      timestamp: new Date().toISOString()
    };
    setMessages(prev => [...prev, userMessage]);

    try {
      const response = await api.executeQuery(sessionId, queryText);
      
      // Add agent response
      const agentMessage = {
        id: generateId(),
        content: response.answer,
        role: MESSAGE_ROLES.AGENT,
        timestamp: new Date().toISOString(),
        metadata: {
          iterations: response.iterations,
          executionTime: response.execution_time,
          toolsUsed: response.tools_used
        }
      };
      setMessages(prev => [...prev, agentMessage]);
      setQueryCount(prev => prev + 1);
    } catch (err) {
      setError(err.message);
      console.error('Failed to execute query:', err);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId]);

  // Reset session
  const resetSession = useCallback(async () => {
    if (sessionId) {
      try {
        await api.deleteSession(sessionId);
      } catch (err) {
        console.error('Failed to delete session:', err);
      }
    }
    
    // Clear state and create new session
    setSessionId(null);
    setMessages([]);
    setIsLoading(false);
    setError(null);
    setQueryCount(0);
    
    // Create new session
    try {
      const response = await api.createSession(toolSet, userId);
      setSessionId(response.session_id);
    } catch (err) {
      setError(`Failed to create new session: ${err.message}`);
      console.error('Failed to create new session:', err);
    }
  }, [sessionId, toolSet, userId]);

  // Change tool set (creates new session)
  const changeToolSet = useCallback(async (newToolSet) => {
    if (newToolSet === toolSet) return;
    
    // End current session if exists
    if (sessionId) {
      try {
        await api.deleteSession(sessionId);
      } catch (err) {
        console.error('Failed to delete session:', err);
      }
    }
    
    // Update tool set and clear state
    setToolSet(newToolSet);
    setSessionId(null);
    setMessages([]);
    setIsLoading(false);
    setError(null);
    setQueryCount(0);
  }, [sessionId, toolSet]);

  return {
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
  };
}