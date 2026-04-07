import axios from 'axios';
import { getAccessToken, logoutUser } from './auth.js';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      logoutUser();
    }
    return Promise.reject(error);
  },
);

export async function login(payload) {
  const response = await api.post('/api/login/', payload);
  return response.data;
}

export async function register(payload) {
  const response = await api.post('/api/users/', payload);
  return response.data;
}

export async function fetchProfile() {
  const response = await api.get('/api/profile/');
  return response.data;
}

export async function fetchCases() {
  const response = await api.get('/api/cases/');
  return response.data;
}

export async function fetchCase(id) {
  const response = await api.get(`/api/cases/${id}/`);
  return response.data;
}

export async function createCase(payload) {
  const response = await api.post('/api/cases/', payload);
  return response.data;
}

export async function fetchMessages() {
  const response = await api.get('/api/messages/');
  return response.data;
}

export async function sendMessage(payload) {
  const response = await api.post('/api/messages/', payload);
  return response.data;
}

export async function apiCall(endpoint, method = 'GET', data = null) {
  try {
    if (method === 'GET') {
      const response = await api.get(endpoint);
      return response.data;
    } else if (method === 'POST') {
      const response = await api.post(endpoint, data);
      return response.data;
    } else if (method === 'PUT') {
      const response = await api.put(endpoint, data);
      return response.data;
    } else if (method === 'DELETE') {
      const response = await api.delete(endpoint);
      return response.data;
    }
  } catch (error) {
    throw error;
  }
}
