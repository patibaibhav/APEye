import apiClient from './client';
import { cleanQueryParams } from '../utils/queryParams';

export const dashboardApi = {
  /**
   * Get dashboard summary cards data
   * @param {{ from?: string, to?: string }} params
   */
  async getDashboardSummary(params = {}) {
    return apiClient.get('/dashboard/summary', {
      params: cleanQueryParams(params),
    });
  },

  /**
   * Get traffic trend points over time
   * @param {{ from?: string, to?: string, interval?: string }} params
   */
  async getTraffic(params = {}) {
    return apiClient.get('/dashboard/traffic', {
      params: cleanQueryParams(params),
    });
  },

  /**
   * Get status class and status code distribution
   * @param {{ from?: string, to?: string }} params
   */
  async getStatusDistribution(params = {}) {
    return apiClient.get('/dashboard/status-distribution', {
      params: cleanQueryParams(params),
    });
  },

  /**
   * Get top endpoints by volume and errors
   * @param {{ from?: string, to?: string, limit?: number }} params
   */
  async getTopEndpoints(params = {}) {
    return apiClient.get('/dashboard/top-endpoints', {
      params: cleanQueryParams(params),
    });
  },

  /**
   * Get response time percentiles and averages
   * @param {{ from?: string, to?: string, interval?: string }} params
   */
  async getResponseTimes(params = {}) {
    return apiClient.get('/dashboard/response-times', {
      params: cleanQueryParams(params),
    });
  },

  /**
   * Get alert distribution by severity
   * @param {{ from?: string, to?: string }} params
   */
  async getAlertSeverity(params = {}) {
    return apiClient.get('/dashboard/alert-severity', {
      params: cleanQueryParams(params),
    });
  },
};

export const {
  getDashboardSummary,
  getTraffic,
  getStatusDistribution,
  getTopEndpoints,
  getResponseTimes,
  getAlertSeverity,
} = dashboardApi;

export default dashboardApi;
