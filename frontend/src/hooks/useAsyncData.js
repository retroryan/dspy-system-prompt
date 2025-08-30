import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook for async data fetching with loading and error states
 * @param {Function} fetchFunction - Async function that fetches data
 * @param {Array} deps - Dependencies that trigger refetch when changed
 * @param {Object} options - Options for the hook
 * @returns {Object} - { data, loading, error, refetch }
 */
export function useAsyncData(fetchFunction, deps = [], options = {}) {
  const {
    initialData = null,
    onSuccess = null,
    onError = null,
    autoFetch = true
  } = options;

  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(autoFetch);
  const [error, setError] = useState(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await fetchFunction();
      setData(result);
      if (onSuccess) {
        onSuccess(result);
      }
    } catch (err) {
      console.error('Async data fetch error:', err);
      setError(err.message || 'Failed to fetch data');
      if (onError) {
        onError(err);
      }
    } finally {
      setLoading(false);
    }
  }, [fetchFunction, onSuccess, onError]);

  // Auto-fetch on mount and when deps change
  useEffect(() => {
    if (autoFetch) {
      fetchData();
    }
  }, deps);

  const refetch = useCallback(() => {
    return fetchData();
  }, [fetchData]);

  return { data, loading, error, refetch };
}