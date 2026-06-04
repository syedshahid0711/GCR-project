/**
 * API Client — centralized HTTP client for the Flask backend.
 */
import axios from 'axios';

const api = axios.create({
  baseURL: '/api',
  withCredentials: true,
  headers: { 'Content-Type': 'application/json' },
});

// Response interceptor for auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Redirect to login if not authenticated
      if (window.location.pathname !== '/' && window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);

// ──── Auth ────
export const authAPI = {
  getMe: () => api.get('/auth/me'),
  logout: () => api.post('/auth/logout'),
  refresh: () => api.post('/auth/refresh'),
};

// ──── Classroom ────
export const classroomAPI = {
  getCourses: () => api.get('/classroom/courses'),
  getCoursework: (courseId) => api.get(`/classroom/courses/${courseId}/work`),
  sync: () => api.post('/classroom/sync'),
  getAnnouncements: () => api.get('/classroom/announcements'),
};

// ──── Assignments ────
export const assignmentsAPI = {
  getAll: (params) => api.get('/assignments/', { params }),
  getById: (id) => api.get(`/assignments/${id}`),
  classify: (id) => api.post(`/ai/classify/${id}`),
  generate: (id, format) => api.post(`/ai/generate/${id}`, { format }),
  submit: (id) => api.post(`/assignments/${id}/submit`),
  cancel: (id) => api.post(`/assignments/${id}/cancel`),
  resubmit: (id) => api.post(`/assignments/${id}/resubmit`),
  updateState: (id, state) => api.patch(`/assignments/${id}/state`, { state }),
  getStats: () => api.get('/assignments/stats'),
  getBrowserSessionStatus: () => api.get('/assignments/browser-session-status'),
  setupBrowserLogin: () => api.post('/assignments/setup-browser-login'),
  importCookies: (cookies) => api.post('/assignments/import-cookies', cookies),
  getDownloadUrl: (id) => `/api/assignments/${id}/download`,
};

// ──── Notifications ────
export const notificationsAPI = {
  getAll: (params) => api.get('/notifications/', { params }),
  markRead: (id) => api.patch(`/notifications/${id}/read`),
  markAllRead: () => api.post('/notifications/read-all'),
};

// ──── Logs ────
export const logsAPI = {
  getAll: (params) => api.get('/logs/', { params }),
  getTimeline: () => api.get('/logs/timeline'),
};

// ──── Settings ────
export const settingsAPI = {
  get: () => api.get('/settings/'),
  update: (data) => api.patch('/settings/', data),
};

// ──── Seed (dev only) ────
export const seedAPI = {
  seed: () => api.post('/seed'),
};

export default api;
