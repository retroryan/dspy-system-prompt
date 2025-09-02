/**
 * Configuration transformation utilities.
 * 
 * Handles conversion between frontend (camelCase) and API (snake_case) formats.
 */

/**
 * Transform API configuration response to frontend format.
 * @param {Object} apiConfig - Configuration from API (snake_case)
 * @param {string} section - Configuration section name
 * @returns {Object} Frontend configuration (camelCase)
 */
export function transformConfigFromAPI(apiConfig, section) {
  switch (section) {
    case 'llm':
      return {
        provider: apiConfig.provider,
        model: apiConfig.model,
        temperature: apiConfig.temperature,
        maxTokens: apiConfig.max_tokens
      };
    
    case 'agent':
      return {
        maxIterations: apiConfig.max_iterations,
        timeout: apiConfig.timeout,
        memorySize: apiConfig.memory_size,
        debugMode: apiConfig.debug_mode
      };
    
    case 'tools':
      return {
        weatherEnabled: apiConfig.weather_enabled,
        searchEnabled: apiConfig.search_enabled,
        calculatorEnabled: apiConfig.calculator_enabled,
        memoryEnabled: apiConfig.memory_enabled
      };
    
    case 'api':
      return {
        endpoint: apiConfig.endpoint,
        timeout: apiConfig.timeout,
        retries: apiConfig.retries
      };
    
    default:
      return apiConfig;
  }
}

/**
 * Transform frontend configuration to API format.
 * @param {Object} frontendConfig - Frontend configuration (camelCase)
 * @param {string} section - Configuration section name
 * @returns {Object} API configuration (snake_case)
 */
export function transformConfigToAPI(frontendConfig, section) {
  switch (section) {
    case 'llm':
      return {
        provider: frontendConfig.provider,
        model: frontendConfig.model,
        temperature: frontendConfig.temperature,
        max_tokens: frontendConfig.maxTokens
      };
    
    case 'agent':
      return {
        max_iterations: frontendConfig.maxIterations,
        timeout: frontendConfig.timeout,
        memory_size: frontendConfig.memorySize,
        debug_mode: frontendConfig.debugMode
      };
    
    case 'tools':
      return {
        weather_enabled: frontendConfig.weatherEnabled,
        search_enabled: frontendConfig.searchEnabled,
        calculator_enabled: frontendConfig.calculatorEnabled,
        memory_enabled: frontendConfig.memoryEnabled
      };
    
    case 'api':
      return {
        endpoint: frontendConfig.endpoint,
        timeout: frontendConfig.timeout,
        retries: frontendConfig.retries
      };
    
    default:
      return frontendConfig;
  }
}

/**
 * Transform system action names between frontend and API formats.
 * @param {string} action - Frontend action name
 * @returns {string} API action name
 */
export function transformSystemAction(action) {
  const actionMap = {
    'view_logs': 'view_logs',
    'restart_services': 'restart_services', 
    'clear_cache': 'clear_cache',
    'export_diagnostics': 'export_diagnostics'
  };
  
  return actionMap[action] || action;
}