import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import AlertsPage from '../pages/AlertsPage';
import AlertDetailPage from '../pages/AlertDetailPage';
import alertsApi from '../api/alertsApi';
import alertsFixture from '../mocks/fixtures/alerts-page.json';
import alertDetailFixture from '../mocks/fixtures/alert-detail.json';

describe('Alerts Management and Detail', () => {
  beforeEach(() => {
    vi.restoreAllMocks();
    vi.spyOn(alertsApi, 'list').mockResolvedValue(alertsFixture);
    vi.spyOn(alertsApi, 'get').mockResolvedValue(alertDetailFixture);
    vi.spyOn(alertsApi, 'setStatus').mockResolvedValue({ ...alertDetailFixture, status: 'INVESTIGATING' });
    vi.spyOn(alertsApi, 'addNote').mockResolvedValue({
      id: 2,
      alert_id: 1,
      author_username: 'admin',
      note: 'New test investigation note',
      created_at: new Date().toISOString(),
    });
  });

  it('renders alerts list with badges and metadata', async () => {
    render(
      <MemoryRouter>
        <AlertsPage />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Threat Alerts/i)).toBeInTheDocument();
      expect(screen.getAllByText('Brute Force')[0]).toBeInTheDocument();
      expect(screen.getAllByText('HIGH')[0]).toBeInTheDocument();
      expect(screen.getAllByText('ACTIVE')[0]).toBeInTheDocument();
      expect(screen.getByText('203.0.113.10')).toBeInTheDocument();
    });
  });

  it('renders alert detail page with evidence and note history', async () => {
    render(
      <MemoryRouter initialEntries={['/alerts/1']}>
        <Routes>
          <Route path="/alerts/:id" element={<AlertDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Alert #1/i)).toBeInTheDocument();
      expect(screen.getByText(/Detection Evidence/i)).toBeInTheDocument();
      expect(screen.getByText(/Investigation Notes/i)).toBeInTheDocument();
      expect(screen.getByText(/Triaged by security team/i)).toBeInTheDocument();
    });
  });

  it('submits a new note on the alert detail page', async () => {
    render(
      <MemoryRouter initialEntries={['/alerts/1']}>
        <Routes>
          <Route path="/alerts/:id" element={<AlertDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Alert #1/i)).toBeInTheDocument();
    });

    const noteInput = screen.getByLabelText(/add an investigation note/i);
    const submitBtn = screen.getByRole('button', { name: /add note/i });

    fireEvent.change(noteInput, { target: { value: 'Verified malicious actor.' } });
    fireEvent.click(submitBtn);

    expect(alertsApi.addNote).toHaveBeenCalledWith('1', { note: 'Verified malicious actor.' });
  });

  it('updates alert status via status select', async () => {
    render(
      <MemoryRouter initialEntries={['/alerts/1']}>
        <Routes>
          <Route path="/alerts/:id" element={<AlertDetailPage />} />
        </Routes>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Alert #1/i)).toBeInTheDocument();
    });

    const select = screen.getByRole('combobox');
    fireEvent.change(select, { target: { value: 'INVESTIGATING' } });

    const saveBtn = screen.getByRole('button', { name: /save status/i });
    fireEvent.click(saveBtn);

    expect(alertsApi.setStatus).toHaveBeenCalledWith('1', { status: 'INVESTIGATING' });
  });
});
