import apiClient from './client';

export const authApi = {
  /**
   * Log in with username and password
   * @param {{ username: string, password: string }} credentials
   * @returns {Promise<{ access_token: string, token_type: string, expires_at: string, user: { id: number, username: string, role: string } }>}
   */
  async login(credentials) {
    return apiClient.post('/auth/login', credentials);
  },

  /**
   * Log out of the current session
   * @returns {Promise<void>}
   */
  async logout() {
    return apiClient.post('/auth/logout');
  },

  /**
   * Fetch current authenticated user
   * @returns {Promise<{ id: number, username: string, role: string }>}
   */
  async me() {
    return apiClient.get('/auth/me');
  },
};

export default authApi;
