import axios from 'axios';
import { getAccessToken, logoutUser, saveAuth } from './auth.js';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:8000',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Attach access token to every request
api.interceptors.request.use((config) => {
  const token = getAccessToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 — attempt token refresh before logging out
let isRefreshing = false;
let failedQueue = [];

function processQueue(error, token = null) {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error);
    } else {
      prom.resolve(token);
    }
  });
  failedQueue = [];
}

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject });
        })
          .then((token) => {
            originalRequest.headers.Authorization = `Bearer ${token}`;
            return api(originalRequest);
          })
          .catch((err) => Promise.reject(err));
      }

      originalRequest._retry = true;
      isRefreshing = true;

      try {
        const stored = JSON.parse(localStorage.getItem('telegram_counselling_auth'));
        if (stored?.refresh) {
          const response = await axios.post(
            `${api.defaults.baseURL}/api/token/refresh/`,
            { refresh: stored.refresh }
          );
          const newAccess = response.data.access;
          const newRefresh = response.data.refresh || stored.refresh;

          saveAuth({
            ...stored,
            access: newAccess,
            refresh: newRefresh,
          });

          processQueue(null, newAccess);
          originalRequest.headers.Authorization = `Bearer ${newAccess}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        processQueue(refreshError, null);
        logoutUser();
        return Promise.reject(refreshError);
      } finally {
        isRefreshing = false;
      }
    }

    return Promise.reject(error);
  }
);

// ─── API Helpers ───

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

export async function assignCase(caseId, adminId) {
  const response = await api.post(`/api/cases/${caseId}/assign/`, { admin_id: adminId });
  return response.data;
}

export async function closeCase(caseId) {
  const response = await api.post(`/api/cases/${caseId}/close/`);
  return response.data;
}

export async function fetchMessages(caseId) {
  const url = caseId ? `/api/messages/?case=${caseId}` : '/api/messages/';
  const response = await api.get(url);
  return response.data;
}

export async function sendMessage(payload) {
  const response = await api.post('/api/messages/', payload);
  return response.data;
}

export async function fetchUsers() {
  const response = await api.get('/api/users/');
  return response.data;
}

export async function fetchAuditLogs() {
  const response = await api.get('/api/audit-logs/');
  return response.data;
}

export async function updateProfile(id, payload) {
  const response = await api.patch(`/api/users/${id}/`, payload);
  return response.data;
}

export async function fetchInternalMessages() {
  const response = await api.get('/api/internal-messages/');
  return response.data;
}

export async function sendInternalMessage(payload) {
  const response = await api.post('/api/internal-messages/', payload);
  return response.data;
}

export async function apiCall(endpoint, method = 'GET', data = null) {
  const response = await api({ method, url: endpoint, data });
  return response.data;
}
