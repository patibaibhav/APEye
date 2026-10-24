import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import SeverityBadge from '../components/common/SeverityBadge';
import StatusBadge from '../components/common/StatusBadge';
import Pagination from '../components/common/Pagination';

describe('Common Component Four States and UI Primitives', () => {
  it('renders LoadingState with skeleton rows and sr-only message', () => {
    render(<LoadingState message="Custom loading text..." rows={3} />);
    expect(screen.getByRole('status', { name: /loading/i })).toBeInTheDocument();
    expect(screen.getByText('Custom loading text...')).toBeInTheDocument();
  });

  it('renders LoadingState with spinner', () => {
    render(<LoadingState spinner message="Spinner loading..." />);
    expect(screen.getByText('Spinner loading...')).toBeInTheDocument();
  });

  it('renders ErrorState with message, request ID, and fires retry callback', () => {
    const onRetry = vi.fn();
    render(
      <ErrorState
        title="Operation Failed"
        message="Critical error encountered"
        requestId="test-uuid-999"
        onRetry={onRetry}
      />
    );

    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Operation Failed')).toBeInTheDocument();
    expect(screen.getByText('Critical error encountered')).toBeInTheDocument();
    expect(screen.getByText('test-uuid-999')).toBeInTheDocument();

    const retryBtn = screen.getByRole('button', { name: /try again/i });
    fireEvent.click(retryBtn);
    expect(onRetry).toHaveBeenCalledTimes(1);
  });

  it('renders EmptyState with explanatory text and action trigger', () => {
    const action = <button type="button">Create First Entry</button>;
    render(
      <EmptyState
        title="No Telemetry Data"
        description="Please adjust your date filter."
        action={action}
      />
    );

    expect(screen.getByText('No Telemetry Data')).toBeInTheDocument();
    expect(screen.getByText('Please adjust your date filter.')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /create first entry/i })).toBeInTheDocument();
  });

  it('renders SeverityBadge for HIGH, MEDIUM, LOW', () => {
    const { rerender } = render(<SeverityBadge severity="HIGH" />);
    expect(screen.getByText('HIGH')).toBeInTheDocument();

    rerender(<SeverityBadge severity="MEDIUM" />);
    expect(screen.getByText('MEDIUM')).toBeInTheDocument();

    rerender(<SeverityBadge severity="LOW" />);
    expect(screen.getByText('LOW')).toBeInTheDocument();
  });

  it('renders StatusBadge for ACTIVE, INVESTIGATING, RESOLVED', () => {
    const { rerender } = render(<StatusBadge status="ACTIVE" />);
    expect(screen.getByText('ACTIVE')).toBeInTheDocument();

    rerender(<StatusBadge status="INVESTIGATING" />);
    expect(screen.getByText('INVESTIGATING')).toBeInTheDocument();

    rerender(<StatusBadge status="RESOLVED" />);
    expect(screen.getByText('RESOLVED')).toBeInTheDocument();
  });

  it('renders Pagination and disables previous button on page 1', () => {
    const onPageChange = vi.fn();
    render(
      <Pagination
        page={1}
        pageSize={25}
        totalItems={50}
        totalPages={2}
        onPageChange={onPageChange}
      />
    );

    const prevBtn = screen.getByRole('button', { name: /previous page/i });
    const nextBtn = screen.getByRole('button', { name: /next page/i });

    expect(prevBtn).toBeDisabled();
    expect(nextBtn).not.toBeDisabled();

    fireEvent.click(nextBtn);
    expect(onPageChange).toHaveBeenCalledWith(2);
  });
});
