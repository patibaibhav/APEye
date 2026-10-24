import React, { useState } from 'react';
import { Download, RefreshCw, ScrollText } from 'lucide-react';
import useApiQuery from '../hooks/useApiQuery';
import logsApi from '../api/logsApi';
import reportsApi from '../api/reportsApi';
import { getDefaultDateRange } from '../utils/queryParams';
import LogFilters from '../components/logs/LogFilters';
import LogsTable from '../components/logs/LogsTable';
import LogDetailDrawer from '../components/logs/LogDetailDrawer';
import Pagination from '../components/common/Pagination';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';

export function LogsPage() {
  const [filters, setFilters] = useState(() => ({
    ...getDefaultDateRange(24),
    source_ip: '',
    endpoint: '',
    method: '',
    status_class: '',
    status_code: '',
    page: 1,
    page_size: 25,
  }));

  const [selectedLog, setSelectedLog] = useState(null);
  const [isExporting, setIsExporting] = useState(false);

  const logsQuery = useApiQuery(
    () => logsApi.list(filters),
    [
      filters.source_ip,
      filters.endpoint,
      filters.method,
      filters.status_class,
      filters.status_code,
      filters.from,
      filters.to,
      filters.page,
      filters.page_size,
    ]
  );

  const handleResetFilters = () => {
    setFilters({
      ...getDefaultDateRange(24),
      source_ip: '',
      endpoint: '',
      method: '',
      status_class: '',
      status_code: '',
      page: 1,
      page_size: filters.page_size,
    });
  };

  const handleExportCsv = async () => {
    setIsExporting(true);
    try {
      // Export using same filters, no pagination
      const { page: _p, page_size: _ps, ...exportParams } = filters;
      const blob = await reportsApi.downloadLogsCsv(exportParams);
      const url = window.URL.createObjectURL(new Blob([blob]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `api_request_logs_${Date.now()}.csv`);
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

  const pageData = logsQuery.data;
  const items = pageData?.items || [];
  const isLoading = logsQuery.isLoading && !logsQuery.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-matte-100 flex items-center gap-2">
            <ScrollText className="w-5 h-5 text-pastel-lavender" />
            <span>Request Logs Explorer</span>
          </h1>
          <p className="text-xs text-matte-400 mt-0.5">
            Audit API request metadata, HTTP status codes, latencies, and security headers
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={handleExportCsv}
            disabled={isExporting || items.length === 0}
            className="btn-secondary text-xs py-2 px-3 flex items-center gap-1.5 disabled:opacity-50"
            title="Export filtered logs as CSV"
          >
            <Download className="w-3.5 h-3.5" />
            <span>{isExporting ? 'Exporting...' : 'Export CSV'}</span>
          </button>
          <button
            type="button"
            onClick={() => logsQuery.refetch()}
            className="p-2 rounded-lg bg-matte-800 border border-matte-700 text-matte-300 hover:text-matte-100 hover:bg-matte-700 transition"
            title="Refresh logs"
            aria-label="Refresh logs"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${logsQuery.isLoading ? 'animate-spin text-pastel-lavender' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter Component */}
      <LogFilters
        filters={filters}
        onChange={(newFilters) => setFilters(newFilters)}
        onReset={handleResetFilters}
      />

      {/* Main Content States */}
      {isLoading && <LoadingState message="Fetching log events..." rows={8} />}

      {!isLoading && logsQuery.error && (
        <ErrorState
          title="Failed to load request logs"
          message={logsQuery.error.message || 'Error querying log repository.'}
          requestId={logsQuery.error.requestId}
          onRetry={() => logsQuery.refetch()}
        />
      )}

      {!isLoading && !logsQuery.error && items.length === 0 && (
        <EmptyState
          title="No logs found"
          description="No request logs matched the specified filter criteria. Try expanding your date range or clearing filters."
          action={
            <button type="button" onClick={handleResetFilters} className="btn-secondary text-xs">
              Clear All Filters
            </button>
          }
        />
      )}

      {!isLoading && !logsQuery.error && items.length > 0 && (
        <div className="matte-card overflow-hidden">
          <LogsTable logs={items} onSelectLog={(log) => setSelectedLog(log)} />
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

      {/* Detail Drawer */}
      <LogDetailDrawer log={selectedLog} onClose={() => setSelectedLog(null)} />
    </div>
  );
}

export default LogsPage;
