import apiClient from './client';
import { cleanQueryParams } from '../utils/queryParams';

export const logsApi = {
  /**
   * List API request logs with filters and pagination
   * @param {{
   *   source_ip?: string,
   *   endpoint?: string,
   *   method?: string,
   *   status_code?: number,
   *   status_class?: string,
   *   from?: string,
   *   to?: string,
   *   page?: number,
   *   page_size?: number
   * }} params
   */
  async list(params = {}) {
    return apiClient.get('/logs', {
      params: cleanQueryParams(params),
    });
  },

  /**
   * Get single log item by ID
   * @param {number|string} id
   */
  async get(id) {
    return apiClient.get(`/logs/${id}`);
  },
};

export default logsApi;
