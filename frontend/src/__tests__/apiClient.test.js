import { describe, it, expect, beforeEach, vi } from 'vitest';
import apiClient, {
  ApiError,
  setClientToken,
  getClientToken,
  clearClientToken,
} from '../api/client';

describe('API Client and Interceptors', () => {
  beforeEach(() => {
    sessionStorage.clear();
    clearClientToken();
    vi.restoreAllMocks();
  });

  it('manages client token in memory and sessionStorage', () => {
    expect(getClientToken()).toBeNull();
    setClientToken('test-token-123');
    expect(getClientToken()).toBe('test-token-123');

    clearClientToken();
    expect(getClientToken()).toBeNull();
  });

  it('instantiates ApiError with envelope properties', () => {
    const error = new ApiError({
      status: 404,
      code: 'ALERT_NOT_FOUND',
      message: 'Alert does not exist',
      details: { id: 99 },
      requestId: 'req-uuid-1',
    });

    expect(error.name).toBe('ApiError');
    expect(error.status).toBe(404);
    expect(error.code).toBe('ALERT_NOT_FOUND');
    expect(error.message).toBe('Alert does not exist');
    expect(error.details).toEqual({ id: 99 });
    expect(error.requestId).toBe('req-uuid-1');
  });

  it('request interceptor adds Bearer authorization when token is set', async () => {
    setClientToken('auth-jwt-token');

    // Test request config interceptor handler directly
    const requestHandler = apiClient.interceptors.request.handlers[0].fulfilled;
    const config = { headers: {} };
    const modifiedConfig = requestHandler(config);

    expect(modifiedConfig.headers.Authorization).toBe('Bearer auth-jwt-token');
  });

  it('response interceptor unwraps response data', () => {
    const responseHandler = apiClient.interceptors.response.handlers[0].fulfilled;
    const fakeResponse = {
      data: { success: true, count: 5 },
      status: 200,
    };

    const result = responseHandler(fakeResponse);
    expect(result).toEqual({ success: true, count: 5 });
  });

  it('response interceptor maps backend error envelope to ApiError', async () => {
    const errorHandler = apiClient.interceptors.response.handlers[0].rejected;
    const axiosError = {
      response: {
        status: 409,
        data: {
          error: {
            code: 'INVALID_TRANSITION',
            message: 'Cannot transition from RESOLVED to INVESTIGATING',
            details: null,
            request_id: 'test-req-err',
          },
        },
      },
    };

    await expect(errorHandler(axiosError)).rejects.toThrow('Cannot transition from RESOLVED to INVESTIGATING');

    try {
      await errorHandler(axiosError);
    } catch (err) {
      expect(err).toBeInstanceOf(ApiError);
      expect(err.status).toBe(409);
      expect(err.code).toBe('INVALID_TRANSITION');
      expect(err.requestId).toBe('test-req-err');
    }
  });

  it('clears token on 401 TOKEN_EXPIRED', async () => {
    setClientToken('expired-token');
    const errorHandler = apiClient.interceptors.response.handlers[0].rejected;

    const axiosError = {
      response: {
        status: 401,
        data: {
          error: {
            code: 'TOKEN_EXPIRED',
            message: 'Access token has expired',
            request_id: 'exp-req',
          },
        },
      },
    };

    try {
      await errorHandler(axiosError);
    } catch (err) {
      expect(err.code).toBe('TOKEN_EXPIRED');
      expect(getClientToken()).toBeNull();
    }
  });
});
