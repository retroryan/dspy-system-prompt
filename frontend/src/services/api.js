// API client for DSPy Agentic Loop Demo
// Connects to the DSPy backend API with clean request-response patterns
const API_URL = import.meta.env.VITE_API_URL || '';

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
    this.name = 'ApiError';
  }
}

async function handleResponse(response) {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(
      errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
      response.status
    );
  }
  return response.json();
}

export const api = {
  // Session Management
  async createSession(toolSet, userId) {
    const response = await fetch(`${API_URL}/sessions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        tool_set: toolSet,
        user_id: userId,
        config: {}
      })
    });
    return handleResponse(response);
  },

  async getSession(sessionId) {
    const response = await fetch(`${API_URL}/sessions/${sessionId}`);
    return handleResponse(response);
  },

  async deleteSession(sessionId) {
    const response = await fetch(`${API_URL}/sessions/${sessionId}`, {
      method: 'DELETE'
    });
    
    if (!response.ok && response.status !== 204) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status
      );
    }
    
    return { success: true };
  },

  async resetSession(sessionId) {
    const response = await fetch(`${API_URL}/sessions/${sessionId}/reset`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' }
    });
    return handleResponse(response);
  },

  // Query Execution
  async executeQuery(sessionId, query, maxIterations = 10) {
    const response = await fetch(`${API_URL}/sessions/${sessionId}/query`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        max_iterations: maxIterations
      })
    });
    return handleResponse(response);
  },

  // Tool Sets
  async getToolSets() {
    const response = await fetch(`${API_URL}/tool-sets`);
    return handleResponse(response);
  },

  async getToolSet(name) {
    const response = await fetch(`${API_URL}/tool-sets/${name}`);
    return handleResponse(response);
  },

  // Health Check
  async getHealth() {
    const response = await fetch(`${API_URL}/health`);
    return handleResponse(response);
  },

  async getMetrics() {
    const response = await fetch(`${API_URL}/metrics`);
    return handleResponse(response);
  },

  // Demo Execution
  async startDemo(demoType, userId, verbose = true) {
    const response = await fetch(`${API_URL}/demos`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        demo_type: demoType,
        user_id: userId,
        verbose
      })
    });
    return handleResponse(response);
  },

  async getDemo(demoId) {
    const response = await fetch(`${API_URL}/demos/${demoId}`);
    return handleResponse(response);
  },

  async getDemoOutput(demoId, sinceLine = 0) {
    const response = await fetch(`${API_URL}/demos/${demoId}/output?since_line=${sinceLine}`);
    return handleResponse(response);
  },

  async cancelDemo(demoId) {
    const response = await fetch(`${API_URL}/demos/${demoId}`, {
      method: 'DELETE'
    });
    
    if (!response.ok && response.status !== 204) {
      const errorData = await response.json().catch(() => ({}));
      throw new ApiError(
        errorData.detail || `HTTP ${response.status}: ${response.statusText}`,
        response.status
      );
    }
    
    return { success: true };
  },

  async listDemos(userId = null, limit = 50) {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (limit) params.append('limit', limit.toString());
    
    const response = await fetch(`${API_URL}/demos?${params}`);
    return handleResponse(response);
  },

  // Configuration Management
  async getConfig(section) {
    const response = await fetch(`${API_URL}/config/${section}`);
    return handleResponse(response);
  },

  async updateConfig(section, config) {
    const response = await fetch(`${API_URL}/config/${section}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        section,
        config
      })
    });
    return handleResponse(response);
  },

  // System Administration
  async getSystemStatus() {
    const response = await fetch(`${API_URL}/system/status`);
    return handleResponse(response);
  },

  async getEnhancedMetrics() {
    const response = await fetch(`${API_URL}/system/metrics`);
    return handleResponse(response);
  },

  async performSystemAction(action, parameters = null) {
    const response = await fetch(`${API_URL}/system/actions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        action,
        parameters
      })
    });
    return handleResponse(response);
  }
};