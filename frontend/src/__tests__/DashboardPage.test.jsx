import React from 'react';
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import DashboardPage from '../pages/DashboardPage';
import * as dashboardApi from '../api/dashboardApi';
import summaryFixture from '../mocks/fixtures/dashboard-summary.json';
import trafficFixture from '../mocks/fixtures/traffic.json';
import statusFixture from '../mocks/fixtures/status-distribution.json';
import endpointsFixture from '../mocks/fixtures/top-endpoints.json';
import latencyFixture from '../mocks/fixtures/response-times.json';
import severityFixture from '../mocks/fixtures/alert-severity.json';

describe('DashboardPage Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();

    vi.spyOn(dashboardApi, 'getDashboardSummary').mockResolvedValue(summaryFixture);
    vi.spyOn(dashboardApi, 'getTraffic').mockResolvedValue(trafficFixture);
    vi.spyOn(dashboardApi, 'getStatusDistribution').mockResolvedValue(statusFixture);
    vi.spyOn(dashboardApi, 'getTopEndpoints').mockResolvedValue(endpointsFixture);
    vi.spyOn(dashboardApi, 'getResponseTimes').mockResolvedValue(latencyFixture);
    vi.spyOn(dashboardApi, 'getAlertSeverity').mockResolvedValue(severityFixture);
  });

  it('renders metric cards with formatted data from summary contract', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Security Dashboard/i)).toBeInTheDocument();
      expect(screen.getAllByText('1,420')[0]).toBeInTheDocument(); // total_requests
      expect(screen.getByText('1,285')).toBeInTheDocument(); // successful_requests
      expect(screen.getByText('135')).toBeInTheDocument();   // failed_requests
    });
  });

  it('renders all five dashboard chart panels', async () => {
    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/API Traffic Trend/i)).toBeInTheDocument();
      expect(screen.getByText(/Status Distribution/i)).toBeInTheDocument();
      expect(screen.getByText(/Latency Profile/i)).toBeInTheDocument();
      expect(screen.getByText(/Alerts by Severity/i)).toBeInTheDocument();
      expect(screen.getByText(/Top API Endpoints/i)).toBeInTheDocument();
    });
  });

  it('renders error state when summary API fails', async () => {
    vi.spyOn(dashboardApi, 'getDashboardSummary').mockRejectedValue({
      message: 'Failed to communicate with DB',
      requestId: 'err-req-999',
    });

    render(
      <MemoryRouter>
        <DashboardPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to load dashboard data/i)).toBeInTheDocument();
      expect(screen.getByText(/Failed to communicate with DB/i)).toBeInTheDocument();
    });
  });
});
