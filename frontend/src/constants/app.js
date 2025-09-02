// Timing constants (in milliseconds)
export const POLLING_INTERVALS = {
  DEMO_OUTPUT: 1000,        // Demo output polling interval
  SYSTEM_HEALTH: 10000,     // System health check interval  
  DASHBOARD_METRICS: 30000, // Dashboard metrics refresh interval
  ACTIVITY_REFRESH: 1000    // Activity feed refresh after action
};

export const API_TIMEOUTS = {
  DEFAULT: 30000,    // Default API timeout
  QUERY: 120000,     // Query execution timeout
  DEMO: 300000       // Demo execution timeout
};

export const NOTIFICATION_DURATIONS = {
  SUCCESS: 5000,     // Success message duration
  ERROR: 7000,       // Error message duration
  WARNING: 6000,     // Warning message duration
  INFO: 5000         // Info message duration
};

// UI Constants
export const MAX_ITERATIONS = {
  DEFAULT: 5,
  QUERY: 10,
  DEMO: 20
};

export const LIMITS = {
  MAX_MESSAGE_LENGTH: 10000,
  MAX_DEMO_OUTPUT_LINES: 1000,
  MAX_ACTIVITIES: 5,
  MAX_RECENT_DEMOS: 10,
  RETRY_ATTEMPTS: 3
};

// Performance thresholds
export const PERFORMANCE = {
  GOOD_RESPONSE_TIME: 2,     // seconds
  MAX_MEMORY_PERCENT: 80,    // percentage
  MAX_CPU_PERCENT: 75         // percentage
};