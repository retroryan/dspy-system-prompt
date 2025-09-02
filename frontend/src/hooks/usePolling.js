import { useEffect, useRef } from 'react';

/**
 * Custom hook for polling at regular intervals
 * @param {Function} callback - Function to call at each interval
 * @param {number} interval - Interval in milliseconds
 * @param {boolean} enabled - Whether polling is enabled
 * @param {Array} deps - Dependencies array for the callback
 */
export function usePolling(callback, interval, enabled = true, deps = []) {
  const savedCallback = useRef();

  // Remember the latest callback
  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  // Set up the interval
  useEffect(() => {
    if (!enabled || !interval) return;

    const tick = () => {
      if (savedCallback.current) {
        savedCallback.current();
      }
    };

    const id = setInterval(tick, interval);
    return () => clearInterval(id);
  }, [interval, enabled, ...deps]);
}