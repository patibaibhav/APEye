import axios from 'axios';

export class ApiError extends Error {
  constructor({ status, code, message, details = null, requestId = null }) {
    super(message || 'An unexpected error occurred');
    this.name = 'ApiError';
    this.status = status;
    this.code = code || 'INTERNAL_ERROR';
    this.details = details;
    this.requestId = requestId;
  }
}

let inMemoryToken = null;

export function setClientToken(token) {
  inMemoryToken = token;
}

export function getClientToken() {
  if (inMemoryToken) return inMemoryToken;
  try {
    return sessionStorage.getItem('apeye_token');
  } catch {
    return null;
  }
}

export function clearClientToken() {
  inMemoryToken = null;
  try {
    sessionStorage.removeItem('apeye_token');
    sessionStorage.removeItem('apeye_user');
  } catch {
    // ignore
  }
}

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor: add Bearer token
apiClient.interceptors.request.use(
  (config) => {
    const token = getClientToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor: map envelope to ApiError, handle 401 token expiry
apiClient.interceptors.response.use(
  (response) => {
    // Return parsed body directly per contract
    return response.data;
  },
  async (error) => {
    if (!error.response) {
      const networkError = new ApiError({
        status: 0,
        code: 'NETWORK_ERROR',
        message: error.message || 'Network connection failed',
      });
      return Promise.reject(networkError);
    }

    const { status } = error.response;
    let { data } = error.response;

    // When responseType is 'blob', error bodies arrive as Blob — parse them
    if (data instanceof Blob) {
      try {
        const text = await data.text();
        data = JSON.parse(text);
      } catch {
        data = null;
      }
    }

    const envelopeError = data?.error;

    const apiError = new ApiError({
      status,
      code: envelopeError?.code || (status === 401 ? 'UNAUTHENTICATED' : 'INTERNAL_ERROR'),
      message: envelopeError?.message || error.message || 'Request failed',
      details: envelopeError?.details || null,
      requestId: envelopeError?.request_id || error.response.headers?.['x-request-id'] || null,
    });

    // Check for expired or invalid token
    if (status === 401 && (apiError.code === 'TOKEN_EXPIRED' || apiError.code === 'TOKEN_INVALID')) {
      clearClientToken();
      if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
        window.location.href = '/login?reason=expired';
      }
    }

    return Promise.reject(apiError);
  }
);

export default apiClient;
