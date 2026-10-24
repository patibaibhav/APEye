import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import SuspiciousIpsPage from '../pages/SuspiciousIpsPage';
import ipsApi from '../api/ipsApi';
import ipsFixture from '../mocks/fixtures/suspicious-ips-page.json';

describe('SuspiciousIpsPage Component', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(ipsApi, 'list').mockResolvedValue(ipsFixture);
    vi.spyOn(ipsApi, 'setInvestigation').mockResolvedValue({
      ...ipsFixture.items[0],
      investigation_status: 'RESOLVED',
      investigation_note: 'Resolved false positive',
    });
  });

  it('renders suspicious IP directory table with categories and counts', async () => {
    render(
      <MemoryRouter>
        <SuspiciousIpsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Suspicious IP Directory/i)).toBeInTheDocument();
      expect(screen.getByText('203.0.113.10')).toBeInTheDocument();
      expect(screen.getByText('198.51.100.25')).toBeInTheDocument();
      expect(screen.getByText('Brute Force')).toBeInTheDocument();
      expect(screen.getByText('Reconnaissance')).toBeInTheDocument();
    });
  });

  it('opens investigation modal and updates status and note', async () => {
    render(
      <MemoryRouter>
        <SuspiciousIpsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('203.0.113.10')).toBeInTheDocument();
    });

    const investigateButtons = screen.getAllByRole('button', { name: /investigate/i });
    fireEvent.click(investigateButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/IP Investigation/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/investigation status/i)).toBeInTheDocument();
    });

    const statusSelect = screen.getByLabelText(/investigation status/i);
    fireEvent.change(statusSelect, { target: { value: 'RESOLVED' } });

    const noteInput = screen.getByLabelText(/case notes/i);
    fireEvent.change(noteInput, { target: { value: 'Blocked at firewall.' } });

    const updateBtn = screen.getByRole('button', { name: /update investigation/i });
    fireEvent.click(updateBtn);

    expect(ipsApi.setInvestigation).toHaveBeenCalledWith('203.0.113.10', {
      status: 'RESOLVED',
      note: 'Blocked at firewall.',
    });
  });

  it('renders empty state when no suspicious IPs found', async () => {
    vi.spyOn(ipsApi, 'list').mockResolvedValue({
      items: [],
      page: 1,
      page_size: 25,
      total_items: 0,
      total_pages: 0,
    });

    render(
      <MemoryRouter>
        <SuspiciousIpsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/No suspicious IPs found/i)).toBeInTheDocument();
    });
  });
});
