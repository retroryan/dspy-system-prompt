import { useState, useCallback } from 'react';
import { usePolling } from './usePolling';
import { api } from '../services/api';

/**
 * Custom hook for polling query execution progress
 * @param {string} sessionId - The session ID to poll progress for
 * @param {boolean} isProcessing - Whether a query is currently processing
 * @param {number} interval - Polling interval in milliseconds (default 500ms)
 */
export function useProgress(sessionId, isProcessing, interval = 500) {
  const [progress, setProgress] = useState(null);
  const [error, setError] = useState(null);

  const fetchProgress = useCallback(async () => {
    if (!sessionId || !isProcessing) return;

    try {
      const progressData = await api.getProgress(sessionId);
      setProgress(progressData);
      setError(null);
    } catch (err) {
      console.error('Error fetching progress:', err);
      setError(err);
    }
  }, [sessionId, isProcessing]);

  // Poll for progress while processing
  usePolling(fetchProgress, interval, isProcessing, [sessionId]);

  // Clear progress when not processing
  const clearProgress = useCallback(() => {
    setProgress(null);
    setError(null);
  }, []);

  return { progress, error, clearProgress };
}