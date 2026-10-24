import apiClient from './client';
import { cleanQueryParams } from '../utils/queryParams';

export const alertsApi = {
  /**
   * List alerts with filters and pagination
   * @param {{
   *   severity?: string,
   *   category?: string,
   *   status?: string,
   *   source_ip?: string,
   *   from?: string,
   *   to?: string,
   *   page?: number,
   *   page_size?: number
   * }} params
   */
  async list(params = {}) {
    return apiClient.get('/alerts', {
      params: cleanQueryParams(params),
    });
  },

  /**
   * Get alert detail by ID
   * @param {number|string} id
   */
  async get(id) {
    return apiClient.get(`/alerts/${id}`);
  },

  /**
   * Update alert status
   * @param {number|string} id
   * @param {{ status: string }} data
   */
  async setStatus(id, data) {
    return apiClient.patch(`/alerts/${id}/status`, data);
  },

  /**
   * Add a note to an alert
   * @param {number|string} id
   * @param {{ note: string }} data
   */
  async addNote(id, data) {
    return apiClient.post(`/alerts/${id}/notes`, data);
  },
};

export default alertsApi;
