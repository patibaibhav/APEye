import React from 'react';
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import TrafficTrendChart from '../components/charts/TrafficTrendChart';
import StatusDistributionChart from '../components/charts/StatusDistributionChart';
import TopEndpointsChart from '../components/charts/TopEndpointsChart';
import ResponseTimeChart from '../components/charts/ResponseTimeChart';
import SeverityDistributionChart from '../components/charts/SeverityDistributionChart';

describe('Chart Components Unit Tests', () => {
  it('TrafficTrendChart renders empty message when no points provided', () => {
    render(<TrafficTrendChart points={[]} />);
    expect(screen.getByText(/No traffic data recorded/i)).toBeInTheDocument();
  });

  it('TrafficTrendChart renders container when points are supplied', () => {
    const points = [{ bucket_start: '2026-01-15T00:00:00Z', total: 10, successful: 8, failed: 2 }];
    const { container } = render(<TrafficTrendChart points={points} />);
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });

  it('StatusDistributionChart renders empty state when classes is empty', () => {
    render(<StatusDistributionChart classes={[]} />);
    expect(screen.getByText(/No status code data available/i)).toBeInTheDocument();
  });

  it('StatusDistributionChart renders total count when data is provided', () => {
    const classes = [
      { status_class: '2xx', count: 80 },
      { status_class: '4xx', count: 20 },
    ];
    render(<StatusDistributionChart classes={classes} />);
    expect(screen.getByText('100')).toBeInTheDocument(); // total sum
  });

  it('TopEndpointsChart renders empty message when no items provided', () => {
    render(<TopEndpointsChart items={[]} />);
    expect(screen.getByText(/No endpoint traffic recorded/i)).toBeInTheDocument();
  });

  it('TopEndpointsChart renders container when items provided', () => {
    const items = [{ endpoint: '/api/logs', request_count: 50, error_count: 2 }];
    const { container } = render(<TopEndpointsChart items={items} />);
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });

  it('ResponseTimeChart renders empty message when no points provided', () => {
    render(<ResponseTimeChart points={[]} />);
    expect(screen.getByText(/No latency data recorded/i)).toBeInTheDocument();
  });

  it('ResponseTimeChart renders container when points provided', () => {
    const points = [{ bucket_start: '2026-01-15T00:00:00Z', avg_ms: 20, p95_ms: 50, max_ms: 100 }];
    const { container } = render(<ResponseTimeChart points={points} />);
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });

  it('SeverityDistributionChart renders empty message when items empty', () => {
    render(<SeverityDistributionChart items={[]} />);
    expect(screen.getByText(/No alert severity data/i)).toBeInTheDocument();
  });

  it('SeverityDistributionChart renders container with items', () => {
    const items = [
      { severity: 'LOW', count: 3 },
      { severity: 'HIGH', count: 1 },
    ];
    const { container } = render(<SeverityDistributionChart items={items} />);
    expect(container.querySelector('.recharts-responsive-container')).toBeInTheDocument();
  });
});
