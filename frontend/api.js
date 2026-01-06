const API = {
  baseUrl: localStorage.getItem('apiUrl') || 'http://localhost:8000',
  apiKey: localStorage.getItem('apiKey') || 'dev-api-key-change-in-production',
  
  setConfig(url, key) {
    this.baseUrl = url;
    this.apiKey = key;
    localStorage.setItem('apiUrl', url);
    localStorage.setItem('apiKey', key);
  },
  
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const headers = {
      'Content-Type': 'application/json',
      'X-API-Key': this.apiKey,
      ...options.headers
    };
    
    try {
      const response = await fetch(url, { ...options, headers });
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  },
  
  async getGraph(threshold = 0.7) {
    return this.request(`/memory/graph?threshold=${threshold}`);
  },
  
  async queryMemories(query, limit = 10) {
    return this.request(`/memory/query?query=${encodeURIComponent(query)}&limit=${limit}`);
  },
  
  async getMemory(id) {
    return this.request(`/memory/${id}`);
  },
  
  async deleteMemory(id) {
    return this.request(`/memory/${id}`, { method: 'DELETE' });
  },
  
  async healthCheck() {
    return this.request('/health');
  }
};
