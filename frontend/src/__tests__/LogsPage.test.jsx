import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import LogsPage from '../pages/LogsPage';
import logsApi from '../api/logsApi';
import logsFixture from '../mocks/fixtures/logs-page.json';

describe('LogsPage Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(logsApi, 'list').mockResolvedValue(logsFixture);
  });

  it('renders log records and pagination from contract response', async () => {
    render(
      <MemoryRouter>
        <LogsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Request Logs Explorer/i)).toBeInTheDocument();
      expect(screen.getAllByText('203.0.113.10')[0]).toBeInTheDocument();
      expect(screen.getAllByText('/api/auth/login')[0]).toBeInTheDocument();
    });
  });

  it('opens detail drawer when clicking a log entry', async () => {
    render(
      <MemoryRouter>
        <LogsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getAllByText('203.0.113.10')[0]).toBeInTheDocument();
    });

    const row = screen.getAllByText('203.0.113.10')[0].closest('tr');
    fireEvent.click(row);

    await waitFor(() => {
      expect(screen.getByText(/API Request Details/i)).toBeInTheDocument();
      expect(screen.getByText('8f8f7b32-9009-4dcb-b214-01b6f3397629')).toBeInTheDocument();
    });
  });

  it('renders empty state when no logs match filter', async () => {
    vi.spyOn(logsApi, 'list').mockResolvedValue({
      items: [],
      page: 1,
      page_size: 25,
      total_items: 0,
      total_pages: 0,
    });

    render(
      <MemoryRouter>
        <LogsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No logs found/i)).toBeInTheDocument();
    });
  });

  it('renders error state when log API fails', async () => {
    vi.spyOn(logsApi, 'list').mockRejectedValue({
      message: 'Log repository connection timeout',
      requestId: 'req-err-456',
    });

    render(
      <MemoryRouter>
        <LogsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Failed to load request logs/i)).toBeInTheDocument();
      expect(screen.getByText(/Log repository connection timeout/i)).toBeInTheDocument();
    });
  });
});
