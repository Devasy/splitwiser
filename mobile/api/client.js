import axios from "axios";

const API_URL = "https://splitwiser-production.up.railway.app";

let accessToken = null;
let refreshToken = null;
let isRefreshing = false;
let refreshPromise = null;
let tokenUpdateListener = null; // function({ accessToken, refreshToken })

export const setTokenUpdateListener = (fn) => {
  tokenUpdateListener = fn;
};

export const setAuthTokens = async ({ newAccessToken, newRefreshToken }) => {
  if (newAccessToken) accessToken = newAccessToken;
  if (newRefreshToken) refreshToken = newRefreshToken;
};

export const clearAuthTokens = async () => {
  accessToken = null;
  refreshToken = null;
};

export const getAccessToken = () => accessToken;
export const getRefreshToken = () => refreshToken;

export const apiClient = axios.create({
  baseURL: API_URL,
  headers: { "Content-Type": "application/json" },
});

// Basic retry configuration
const MAX_RETRIES = 3;
const BASE_DELAY_MS = 300; // base backoff

function sleep(ms) {
  return new Promise((res) => setTimeout(res, ms));
}

// Attach Authorization header
apiClient.interceptors.request.use((config) => {
  if (accessToken && !config.headers?.Authorization) {
    config.headers = config.headers || {};
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

async function performRefresh() {
  // Avoid multiple refresh calls
  if (isRefreshing && refreshPromise) return refreshPromise;
  isRefreshing = true;
  refreshPromise = (async () => {
    try {
      if (!refreshToken) throw new Error("No refresh token");
      const resp = await axios.post(
        `${API_URL}/auth/refresh`,
        { refresh_token: refreshToken },
        { headers: { "Content-Type": "application/json" } }
      );
      const { access_token, refresh_token } = resp.data || {};
      accessToken = access_token || accessToken;
      refreshToken = refresh_token || refreshToken;
      // Notify listener (AuthContext) so it can persist & update state
      if (tokenUpdateListener) {
        tokenUpdateListener({ accessToken, refreshToken });
      }
      return accessToken;
    } finally {
      isRefreshing = false;
      // allow GC of the completed promise
      refreshPromise = null;
    }
  })();
  return refreshPromise;
}

// Retry logic on 401
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config || {};
    const status = error.response?.status;

    // Avoid refresh loop
    const isAuthRefreshCall = originalRequest.url?.includes("/auth/refresh");

    // 1. Handle 401 with refresh
    if (status === 401 && !originalRequest._retry && !isAuthRefreshCall) {
      originalRequest._retry = true;
      try {
        await performRefresh();
        originalRequest.headers = originalRequest.headers || {};
        if (accessToken)
          originalRequest.headers.Authorization = `Bearer ${accessToken}`;
        return apiClient(originalRequest);
      } catch (e) {
        return Promise.reject(error);
      }
    }

  // 2. Retry on network errors or 5xx (all methods; caller should ensure idempotency where needed)
  const transientError = !status || (status >= 500 && status < 600);
  if (transientError) {
      originalRequest._retryCount = originalRequest._retryCount || 0;
      if (originalRequest._retryCount < MAX_RETRIES) {
        originalRequest._retryCount += 1;
        const delay = BASE_DELAY_MS * 2 ** (originalRequest._retryCount - 1);
        await sleep(delay + Math.random() * 100); // jitter
        return apiClient(originalRequest);
      }
    }

    return Promise.reject(error);
  }
);

// Splitwise Import API
export const getSplitwiseAuthUrl = () => {
  return apiClient.get("/import/splitwise/authorize");
};

export const handleSplitwiseCallback = (code, state) => {
  return apiClient.post("/import/splitwise/callback", { code, state });
};

export const startSplitwiseImport = (apiKey) => {
  return apiClient.post("/import/splitwise/start", { api_key: apiKey });
};

export const getImportStatus = (importJobId) => {
  return apiClient.get(`/import/status/${importJobId}`);
};

export const rollbackImport = (importJobId) => {
  return apiClient.post(`/import/rollback/${importJobId}`);
};
