import React, { useState } from 'react';
import {
  Activity,
  CheckCircle2,
  AlertOctagon,
  AlertTriangle,
  Flame,
  UserX,
  RefreshCw,
} from 'lucide-react';
import useApiQuery from '../hooks/useApiQuery';
import {
  getDashboardSummary,
  getTraffic,
  getStatusDistribution,
  getTopEndpoints,
  getResponseTimes,
  getAlertSeverity,
} from '../api/dashboardApi';
import { getDefaultDateRange } from '../utils/queryParams';
import { formatNumber } from '../utils/formatters';
import DateRangeFilter from '../components/common/DateRangeFilter';
import StatCard from '../components/common/StatCard';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';
import TrafficTrendChart from '../components/charts/TrafficTrendChart';
import StatusDistributionChart from '../components/charts/StatusDistributionChart';
import TopEndpointsChart from '../components/charts/TopEndpointsChart';
import ResponseTimeChart from '../components/charts/ResponseTimeChart';
import SeverityDistributionChart from '../components/charts/SeverityDistributionChart';

export function DashboardPage() {
  const [dateRange, setDateRange] = useState(() => getDefaultDateRange(24));

  // Fetch summary
  const summaryQuery = useApiQuery(
    () => getDashboardSummary({ from: dateRange.from, to: dateRange.to }),
    [dateRange.from, dateRange.to]
  );

  // Fetch traffic points
  const trafficQuery = useApiQuery(
    () => getTraffic({ from: dateRange.from, to: dateRange.to }),
    [dateRange.from, dateRange.to]
  );

  // Fetch status distribution
  const statusQuery = useApiQuery(
    () => getStatusDistribution({ from: dateRange.from, to: dateRange.to }),
    [dateRange.from, dateRange.to]
  );

  // Fetch top endpoints
  const topEndpointsQuery = useApiQuery(
    () => getTopEndpoints({ from: dateRange.from, to: dateRange.to, limit: 10 }),
    [dateRange.from, dateRange.to]
  );

  // Fetch response times
  const responseTimesQuery = useApiQuery(
    () => getResponseTimes({ from: dateRange.from, to: dateRange.to }),
    [dateRange.from, dateRange.to]
  );

  // Fetch severity distribution
  const severityQuery = useApiQuery(
    () => getAlertSeverity({ from: dateRange.from, to: dateRange.to }),
    [dateRange.from, dateRange.to]
  );

  const handleRefreshAll = () => {
    summaryQuery.refetch();
    trafficQuery.refetch();
    statusQuery.refetch();
    topEndpointsQuery.refetch();
    responseTimesQuery.refetch();
    severityQuery.refetch();
  };

  const isInitialLoading = summaryQuery.isLoading && !summaryQuery.data;
  const anyError = summaryQuery.error || trafficQuery.error;

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-matte-100">Security Dashboard</h1>
          <p className="text-xs text-matte-400 mt-0.5">
            Real-time API traffic telemetry, anomaly detection, and operational overview
          </p>
        </div>

        <div className="flex items-center gap-2">
          <DateRangeFilter
            from={dateRange.from}
            to={dateRange.to}
            onChange={(newRange) => setDateRange(newRange)}
          />
          <button
            type="button"
            onClick={handleRefreshAll}
            className="p-2 rounded-lg bg-matte-800 border border-matte-700 text-matte-300 hover:text-matte-100 hover:bg-matte-700 transition"
            title="Refresh Dashboard"
            aria-label="Refresh Dashboard"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${summaryQuery.isLoading ? 'animate-spin text-pastel-lavender' : ''}`} />
          </button>
        </div>
      </div>

      {/* Loading state */}
      {isInitialLoading && (
        <div className="space-y-6">
          <LoadingState message="Loading telemetry summary..." rows={2} />
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <LoadingState rows={4} />
            <LoadingState rows={4} />
          </div>
        </div>
      )}

      {/* Error state */}
      {!isInitialLoading && anyError && (
        <ErrorState
          title="Failed to load dashboard data"
          message={anyError.message || 'Error communicating with security telemetry services.'}
          requestId={anyError.requestId}
          onRetry={handleRefreshAll}
        />
      )}

      {/* Empty / Zero-state */}
      {!isInitialLoading && !anyError && summaryQuery.data && summaryQuery.data.total_requests === 0 && (
        <EmptyState
          title="No API activity in this window"
          description="There were no recorded API requests or security alerts during the selected time period. Send requests to see live data."
        />
      )}

      {/* Success Content */}
      {!isInitialLoading && !anyError && summaryQuery.data && (
        <div className="space-y-6">
          {/* Stat Cards Grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4">
            <StatCard
              title="Total Requests"
              value={formatNumber(summaryQuery.data.total_requests)}
              icon={Activity}
              accent="lavender"
            />
            <StatCard
              title="Successful"
              value={formatNumber(summaryQuery.data.successful_requests)}
              icon={CheckCircle2}
              accent="mint"
            />
            <StatCard
              title="Failed (4xx/5xx)"
              value={formatNumber(summaryQuery.data.failed_requests)}
              icon={AlertOctagon}
              accent="amber"
            />
            <StatCard
              title="Total Alerts"
              value={formatNumber(summaryQuery.data.total_alerts)}
              icon={AlertTriangle}
              accent="slate"
            />
            <StatCard
              title="High Severity"
              value={formatNumber(summaryQuery.data.high_severity_alerts)}
              icon={Flame}
              accent="rose"
            />
            <StatCard
              title="Suspicious IPs"
              value={formatNumber(summaryQuery.data.distinct_suspicious_ips)}
              icon={UserX}
              accent="amber"
            />
          </div>

          {/* Charts Grid Row 1: Traffic Trend + Status Breakdown */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <div className="lg:col-span-2 matte-card p-5">
              <div className="flex items-center justify-between mb-4 border-b border-matte-800 pb-3">
                <div>
                  <h2 className="text-sm font-semibold text-matte-200">API Traffic Trend</h2>
                  <p className="text-[11px] text-matte-500">Request throughput over time</p>
                </div>
              </div>
              <TrafficTrendChart points={trafficQuery.data?.points || []} />
            </div>

            <div className="matte-card p-5">
              <div className="flex items-center justify-between mb-4 border-b border-matte-800 pb-3">
                <div>
                  <h2 className="text-sm font-semibold text-matte-200">Status Distribution</h2>
                  <p className="text-[11px] text-matte-500">HTTP response class breakdown</p>
                </div>
              </div>
              <StatusDistributionChart classes={statusQuery.data?.classes || []} />
            </div>
          </div>

          {/* Charts Grid Row 2: Latency + Severity + Top Endpoints */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            <div className="matte-card p-5">
              <div className="flex items-center justify-between mb-4 border-b border-matte-800 pb-3">
                <div>
                  <h2 className="text-sm font-semibold text-matte-200">Latency Profile</h2>
                  <p className="text-[11px] text-matte-500">Average, p95, and max response times</p>
                </div>
              </div>
              <ResponseTimeChart points={responseTimesQuery.data?.points || []} />
            </div>

            <div className="matte-card p-5">
              <div className="flex items-center justify-between mb-4 border-b border-matte-800 pb-3">
                <div>
                  <h2 className="text-sm font-semibold text-matte-200">Alerts by Severity</h2>
                  <p className="text-[11px] text-matte-500">Active threat distribution</p>
                </div>
              </div>
              <SeverityDistributionChart items={severityQuery.data?.items || []} />
            </div>

            <div className="matte-card p-5 md:col-span-2 lg:col-span-1">
              <div className="flex items-center justify-between mb-4 border-b border-matte-800 pb-3">
                <div>
                  <h2 className="text-sm font-semibold text-matte-200">Top API Endpoints</h2>
                  <p className="text-[11px] text-matte-500">Most requested and error-prone routes</p>
                </div>
              </div>
              <TopEndpointsChart items={topEndpointsQuery.data?.items || []} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DashboardPage;
