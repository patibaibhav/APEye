import apiClient from './client';
import { cleanQueryParams } from '../utils/queryParams';

export const reportsApi = {
  /**
   * Get generated security summary
   * @param {{ from?: string, to?: string }} params
   */
  async summary(params = {}) {
    return apiClient.get('/reports/summary', {
      params: cleanQueryParams(params),
    });
  },

  /**
   * Request a report archive creation (ADMIN only)
   * @param {{ report_type: string, from: string, to: string, filters?: Record<string, any> }} data
   */
  async archive(data) {
    return apiClient.post('/reports/archive', data);
  },

  /**
   * List archived reports
   * @param {{ page?: number, page_size?: number }} params
   */
  async list(params = {}) {
    return apiClient.get('/reports', {
      params: cleanQueryParams(params),
    });
  },

  /**
   * Get download URL for report archive
   * @param {number|string} id
   * @returns {Promise<{ url: string, expires_at?: string }>}
   */
  async download(id) {
    return apiClient.get(`/reports/${id}/download`);
  },

  /**
   * Trigger download of logs CSV directly
   * @param {Record<string, any>} params
   */
  async downloadLogsCsv(params = {}) {
    return apiClient.get('/exports/logs.csv', {
      params: cleanQueryParams(params),
      responseType: 'blob',
    });
  },

  /**
   * Trigger download of alerts CSV directly
   * @param {Record<string, any>} params
   */
  async downloadAlertsCsv(params = {}) {
    return apiClient.get('/exports/alerts.csv', {
      params: cleanQueryParams(params),
      responseType: 'blob',
    });
  },
};

export default reportsApi;
