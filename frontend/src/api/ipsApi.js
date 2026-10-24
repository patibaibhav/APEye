import apiClient from './client';
import { cleanQueryParams } from '../utils/queryParams';

export const ipsApi = {
  /**
   * List suspicious IPs with pagination
   * @param {{
   *   status?: string,
   *   from?: string,
   *   to?: string,
   *   page?: number,
   *   page_size?: number
   * }} params
   */
  async list(params = {}) {
    return apiClient.get('/suspicious-ips', {
      params: cleanQueryParams(params),
    });
  },

  /**
   * Get suspicious IP detail with related alerts
   * @param {string} ip
   */
  async get(ip) {
    return apiClient.get(`/suspicious-ips/${encodeURIComponent(ip)}`);
  },

  /**
   * Update IP investigation status and note
   * @param {string} ip
   * @param {{ status: string, note?: string }} data
   */
  async setInvestigation(ip, data) {
    return apiClient.patch(`/suspicious-ips/${encodeURIComponent(ip)}/investigation`, data);
  },
};

export default ipsApi;
