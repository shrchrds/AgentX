import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach API key from localStorage or default development key
api.interceptors.request.use((config) => {
  const apiKey = localStorage.getItem('agentx_api_key') || 'agentx-dev-key';
  config.headers['X-API-Key'] = apiKey;
  return config;
});

export default api;

