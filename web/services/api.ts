import axios from 'axios';

// Use localhost for development, production URL for production
const API_URL = import.meta.env.VITE_API_URL || 'https://splitwiser-production.up.railway.app';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
}, (error) => Promise.reject(error));

// Response interceptor to handle token refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    // If 401 and we haven't retried yet, try to refresh the token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');
        if (!refreshToken) {
          // No refresh token, redirect to login
          localStorage.removeItem('access_token');
          window.location.href = '/login';
          return Promise.reject(error);
        }

        // Try to refresh the token
        const response = await axios.post(`${API_URL}/auth/refresh`, {
          refresh_token: refreshToken
        });

        const { access_token, refresh_token: newRefreshToken } = response.data;
        localStorage.setItem('access_token', access_token);
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken);
        }

        // Retry the original request with new token
        originalRequest.headers.Authorization = `Bearer ${access_token}`;
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed, redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    return Promise.reject(error);
  }
);

// Auth
export const login = async (data: any) => api.post('/auth/login/email', data);
export const signup = async (data: any) => api.post('/auth/signup/email', data);
export const loginWithGoogle = async (idToken: string) => api.post('/auth/login/google', { id_token: idToken });
export const getProfile = async () => api.get('/users/me');

// Groups
export const getGroups = async () => api.get('/groups');
export const createGroup = async (data: { name: string, currency?: string }) => api.post('/groups', data);
export const getGroupDetails = async (id: string) => api.get(`/groups/${id}`);
export const updateGroup = async (id: string, data: { name?: string, imageUrl?: string, currency?: string }) => api.patch(`/groups/${id}`, data);
export const deleteGroup = async (id: string) => api.delete(`/groups/${id}`);
export const getGroupMembers = async (id: string) => api.get(`/groups/${id}/members`);
export const joinGroup = async (joinCode: string) => api.post('/groups/join', { joinCode });

// Expenses
export const getExpenses = async (groupId: string, page: number = 1, limit: number = 20) => api.get(`/groups/${groupId}/expenses?page=${page}&limit=${limit}`);
export const createExpense = async (groupId: string, data: any) => api.post(`/groups/${groupId}/expenses`, data);
export const updateExpense = async (groupId: string, expenseId: string, data: any) => api.patch(`/groups/${groupId}/expenses/${expenseId}`, data);
export const deleteExpense = async (groupId: string, expenseId: string) => api.delete(`/groups/${groupId}/expenses/${expenseId}`);

// Settlements
export const getSettlements = async (groupId: string) => api.get(`/groups/${groupId}/settlements?status=pending`);
export const createSettlement = async (groupId: string, data: { payer_id: string, payee_id: string, amount: number }) => api.post(`/groups/${groupId}/settlements`, data);
export const getOptimizedSettlements = async (groupId: string) => api.post(`/groups/${groupId}/settlements/optimize`);
export const markSettlementPaid = async (groupId: string, settlementId: string) => api.patch(`/groups/${groupId}/settlements/${settlementId}`, { status: 'completed' });

// Users
export const getBalanceSummary = async () => api.get('/users/me/balance-summary');
export const getFriendsBalance = async () => api.get('/users/me/friends-balance');
export const updateProfile = async (data: { name?: string; imageUrl?: string }) => api.patch('/users/me', data);

// Splitwise Import
export const getSplitwiseAuthUrl = async () => api.get('/import/splitwise/authorize');
export const handleSplitwiseCallback = async (code?: string, state?: string, selectedGroupIds?: string[], accessToken?: string) => {
  const payload: any = {};

  if (accessToken) {
    payload.accessToken = accessToken;
  } else if (code) {
    payload.code = code;
    payload.state = state || '';
  }

  if (selectedGroupIds && selectedGroupIds.length > 0) {
    payload.options = { selectedGroupIds };
  }

  return api.post('/import/splitwise/callback', payload);
};
export const getSplitwisePreview = async (accessToken: string) => api.post('/import/splitwise/preview', { access_token: accessToken });
export const startSplitwiseImport = async (apiKey: string) => api.post('/import/splitwise/start', { api_key: apiKey });
export const getImportStatus = async (importJobId: string) => api.get(`/import/status/${importJobId}`);
export const rollbackImport = async (importJobId: string) => api.post(`/import/rollback/${importJobId}`);

// Group Management
export const leaveGroup = async (groupId: string) => api.post(`/groups/${groupId}/leave`);
export const removeMember = async (groupId: string, userId: string) => api.delete(`/groups/${groupId}/members/${userId}`);

export default api;