import apiClient from './client';
import { cleanQueryParams } from '../utils/queryParams';

export const usersApi = {
  /**
   * List users with pagination (ADMIN only)
   * @param {{ page?: number, page_size?: number }} params
   */
  async list(params = {}) {
    return apiClient.get('/users', {
      params: cleanQueryParams(params),
    });
  },

  /**
   * Create a new user (ADMIN only)
   * @param {{ username: string, password: string, role: string }} data
   */
  async create(data) {
    return apiClient.post('/users', data);
  },

  /**
   * Update an existing user's role or status (ADMIN only)
   * @param {number} id
   * @param {{ is_active?: boolean, role?: string }} data
   */
  async update(id, data) {
    return apiClient.patch(`/users/${id}`, data);
  },
};

export default usersApi;
