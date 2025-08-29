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
  async executeQuery(sessionId, query, maxIterations = 5) {
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
  }
};