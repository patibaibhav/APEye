import React, { useState } from 'react';
import { Download, RefreshCw, AlertTriangle } from 'lucide-react';
import useApiQuery from '../hooks/useApiQuery';
import alertsApi from '../api/alertsApi';
import reportsApi from '../api/reportsApi';
import { getDefaultDateRange } from '../utils/queryParams';
import AlertFilters from '../components/alerts/AlertFilters';
import AlertsTable from '../components/alerts/AlertsTable';
import Pagination from '../components/common/Pagination';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';

export function AlertsPage() {
  const [filters, setFilters] = useState(() => ({
    ...getDefaultDateRange(24 * 7), // 7 days default for alerts
    severity: '',
    category: '',
    status: '',
    source_ip: '',
    page: 1,
    page_size: 25,
  }));

  const [isExporting, setIsExporting] = useState(false);

  const alertsQuery = useApiQuery(
    () => alertsApi.list(filters),
    [
      filters.severity,
      filters.category,
      filters.status,
      filters.source_ip,
      filters.from,
      filters.to,
      filters.page,
      filters.page_size,
    ]
  );

  const handleResetFilters = () => {
    setFilters({
      ...getDefaultDateRange(24 * 7),
      severity: '',
      category: '',
      status: '',
      source_ip: '',
      page: 1,
      page_size: filters.page_size,
    });
  };

  const handleExportCsv = async () => {
    setIsExporting(true);
    try {
      const { page: _p, page_size: _ps, ...exportParams } = filters;
      const blob = await reportsApi.downloadAlertsCsv(exportParams);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `security_alerts_${Date.now()}.csv`);
      document.body.appendChild(link);
      link.click();
      link.parentNode.removeChild(link);
      window.URL.revokeObjectURL(url);
    } catch (err) {
      alert(`Export failed: ${err.message || 'Unknown error'}`);
    } finally {
      setIsExporting(false);
    }
  };

  const pageData = alertsQuery.data;
  const items = pageData?.items || [];
  const isLoading = alertsQuery.isLoading && !alertsQuery.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-matte-100 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-pastel-amber" />
            <span>Threat Alerts</span>
          </h1>
          <p className="text-xs text-matte-400 mt-0.5">
            Rule-based detection indicators (Brute Force, Excessive Requests, Reconnaissance, Unauthorized Access)
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleExportCsv}
            disabled={isExporting || items.length === 0}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5 disabled:opacity-50"
            title="Export filtered alerts as CSV"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{isExporting ? 'Exporting...' : 'Export CSV'}</span>
          </button>
          <button
            type="button"
            onClick={() => alertsQuery.refetch()}
            className="p-2 rounded-lg bg-matte-800 border border-matte-700 text-matte-300 hover:text-matte-100 hover:bg-matte-700 transition"
            title="Refresh alerts"
            aria-label="Refresh alerts"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${alertsQuery.isLoading ? 'animate-spin text-pastel-lavender' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filters */}
      <AlertFilters
        filters={filters}
        onChange={(newFilters) => setFilters(newFilters)}
        onReset={handleResetFilters}
      />

      {/* Main Content States */}
      {isLoading && <LoadingState message="Fetching security alerts..." rows={6} />}

      {!isLoading && alertsQuery.error && (
        <ErrorState
          title="Failed to load security alerts"
          message={alertsQuery.error.message || 'Error communicating with alerts service.'}
          requestId={alertsQuery.error.requestId}
          onRetry={() => alertsQuery.refetch()}
        />
      )}

      {!isLoading && !alertsQuery.error && items.length === 0 && (
        <EmptyState
          title="No security alerts found"
          description="No detection rules have fired matching your current filters. System is observing API traffic."
          action={
            <button type="button" onClick={handleResetFilters} className="btn-secondary text-xs">
              Reset Filters
            </button>
          }
        />
      )}

      {!isLoading && !alertsQuery.error && items.length > 0 && (
        <div className="matte-card overflow-hidden">
          <AlertsTable alerts={items} />
          <Pagination
            page={pageData.page}
            pageSize={pageData.page_size}
            totalItems={pageData.total_items}
            totalPages={pageData.total_pages}
            onPageChange={(p) => setFilters({ ...filters, page: p })}
            onPageSizeChange={(ps) => setFilters({ ...filters, page_size: ps, page: 1 })}
          />
        </div>
      )}
    </div>
  );
}

export default AlertsPage;
