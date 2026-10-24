import React, { useState } from 'react';
import { FileArchive, Download, Plus, RefreshCw, Lock } from 'lucide-react';
import useApiQuery from '../hooks/useApiQuery';
import reportsApi from '../api/reportsApi';
import { useAuth } from '../context/AuthContext';
import { Role, ReportType, ReportTypeLabels } from '../utils/constants';
import { getDefaultDateRange } from '../utils/queryParams';
import { formatTimestamp, formatBytes, formatNumber } from '../utils/formatters';
import DateRangeFilter from '../components/common/DateRangeFilter';
import Pagination from '../components/common/Pagination';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';

export function ReportsPage() {
  const { hasRole } = useAuth();
  const isAdmin = hasRole(Role.ADMIN);

  const [dateRange, setDateRange] = useState(() => getDefaultDateRange(24 * 7));
  const [archivePage, setArchivePage] = useState(1);
  const [archivePageSize, setArchivePageSize] = useState(10);

  // Archive modal state
  const [isArchiveModalOpen, setIsArchiveModalOpen] = useState(false);
  const [selectedReportType, setSelectedReportType] = useState(ReportType.SUMMARY);
  const [isSubmittingArchive, setIsSubmittingArchive] = useState(false);
  const [archiveError, setArchiveError] = useState('');

  // Queries
  const summaryQuery = useApiQuery(
    () => reportsApi.summary({ from: dateRange.from, to: dateRange.to }),
    [dateRange.from, dateRange.to]
  );

  const archivesQuery = useApiQuery(
    () => reportsApi.list({ page: archivePage, page_size: archivePageSize }),
    [archivePage, archivePageSize]
  );

  const handleCreateArchive = async (e) => {
    e.preventDefault();
    if (!isAdmin) return;

    setIsSubmittingArchive(true);
    setArchiveError('');

    try {
      await reportsApi.archive({
        report_type: selectedReportType,
        from: dateRange.from,
        to: dateRange.to,
      });
      setIsArchiveModalOpen(false);
      archivesQuery.refetch();
    } catch (err) {
      setArchiveError(err.message || 'Failed to trigger report archive.');
    } finally {
      setIsSubmittingArchive(false);
    }
  };

  const handleDownloadArchive = async (id) => {
    try {
      const res = await reportsApi.download(id);
      if (res && res.url) {
        window.open(res.url, '_blank');
      }
    } catch (err) {
      alert(`Download failed: ${err.message || 'Unknown error'}`);
    }
  };

  const summary = summaryQuery.data;
  const archives = archivesQuery.data?.items || [];

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-matte-100 flex items-center gap-2">
            <FileArchive className="w-5 h-5 text-pastel-lavender" />
            <span>Security Reports & Archival</span>
          </h1>
          <p className="text-xs text-matte-400 mt-0.5">
            Periodic summary briefs, compliance auditing, and S3 / local archive storage
          </p>
        </div>

        <div className="flex items-center gap-2">
          {isAdmin ? (
            <button
              type="button"
              onClick={() => setIsArchiveModalOpen(true)}
              className="btn-primary text-xs py-2 px-3 flex items-center gap-1.5"
            >
              <Plus className="w-4 h-4" />
              <span>Archive Report</span>
            </button>
          ) : (
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-matte-900 border border-matte-800 text-[11px] text-matte-400">
              <Lock className="w-3.5 h-3.5 text-matte-500" />
              <span>Archival triggers require ADMIN role</span>
            </div>
          )}
        </div>
      </div>

      {/* Section 1: Security Summary Brief */}
      <div className="space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-matte-800 pb-3">
          <div>
            <h2 className="text-sm font-semibold text-matte-200">Executive Security Summary</h2>
            <p className="text-[11px] text-matte-500">Aggregated threat activity and anomaly totals</p>
          </div>
          <DateRangeFilter
            from={dateRange.from}
            to={dateRange.to}
            onChange={(newRange) => setDateRange(newRange)}
          />
        </div>

        {summaryQuery.isLoading && <LoadingState message="Generating security summary..." rows={3} />}

        {!summaryQuery.isLoading && summaryQuery.error && (
          <ErrorState
            title="Failed to generate summary"
            message={summaryQuery.error.message}
            requestId={summaryQuery.error.requestId}
            onRetry={() => summaryQuery.refetch()}
          />
        )}

        {!summaryQuery.isLoading && !summaryQuery.error && summary && (
          <div className="matte-card p-5 space-y-6">
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="p-3 rounded-lg bg-matte-900 border border-matte-800">
                <span className="text-[11px] font-medium text-matte-400 block mb-1">Total API Requests</span>
                <span className="font-mono text-lg font-bold text-matte-100">
                  {formatNumber(summary.totals?.total_requests || 0)}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-matte-900 border border-matte-800">
                <span className="text-[11px] font-medium text-matte-400 block mb-1">Total Alerts</span>
                <span className="font-mono text-lg font-bold text-pastel-amber-light">
                  {formatNumber(summary.totals?.total_alerts || 0)}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-matte-900 border border-matte-800">
                <span className="text-[11px] font-medium text-matte-400 block mb-1">High Severity Alerts</span>
                <span className="font-mono text-lg font-bold text-pastel-rose-light">
                  {formatNumber(summary.totals?.high_severity_alerts || 0)}
                </span>
              </div>
              <div className="p-3 rounded-lg bg-matte-900 border border-matte-800">
                <span className="text-[11px] font-medium text-matte-400 block mb-1">Suspicious IPs</span>
                <span className="font-mono text-lg font-bold text-matte-200">
                  {formatNumber(summary.totals?.distinct_suspicious_ips || 0)}
                </span>
              </div>
            </div>

            {/* Top Threat Indicators */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 pt-2">
              <div>
                <h3 className="text-xs font-semibold text-matte-300 uppercase tracking-wider mb-2">
                  Top Source IP Threats
                </h3>
                {summary.top_source_ips && summary.top_source_ips.length > 0 ? (
                  <div className="space-y-1.5">
                    {summary.top_source_ips.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2 rounded bg-matte-900 border border-matte-800 text-xs"
                      >
                        <span className="font-mono text-matte-200">{item.source_ip}</span>
                        <span className="font-mono font-semibold text-pastel-rose-light">
                          {item.alert_count} {item.alert_count === 1 ? 'alert' : 'alerts'}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-matte-500 italic">No suspicious IPs recorded in this period.</p>
                )}
              </div>

              <div>
                <h3 className="text-xs font-semibold text-matte-300 uppercase tracking-wider mb-2">
                  Top Targeted Endpoints
                </h3>
                {summary.top_endpoints && summary.top_endpoints.length > 0 ? (
                  <div className="space-y-1.5">
                    {summary.top_endpoints.map((item, idx) => (
                      <div
                        key={idx}
                        className="flex items-center justify-between p-2 rounded bg-matte-900 border border-matte-800 text-xs"
                      >
                        <span className="font-mono text-matte-200 truncate max-w-xs">{item.endpoint}</span>
                        <span className="font-mono text-matte-400">
                          {formatNumber(item.request_count || item.count || 0)} reqs
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-matte-500 italic">No endpoint data available.</p>
                )}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Section 2: Report Archives Table */}
      <div className="space-y-4">
        <div className="flex items-center justify-between border-b border-matte-800 pb-3">
          <div>
            <h2 className="text-sm font-semibold text-matte-200">Archived Reports Directory</h2>
            <p className="text-[11px] text-matte-500">Immutable storage records (S3 / Local)</p>
          </div>
          <button
            type="button"
            onClick={() => archivesQuery.refetch()}
            className="p-1.5 rounded-lg bg-matte-800 border border-matte-700 text-matte-300 hover:text-matte-100"
            title="Refresh Archives"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${archivesQuery.isLoading ? 'animate-spin' : ''}`} />
          </button>
        </div>

        {archivesQuery.isLoading && <LoadingState message="Loading archived reports..." rows={4} />}

        {!archivesQuery.isLoading && archivesQuery.error && (
          <ErrorState
            title="Failed to load archives"
            message={archivesQuery.error.message}
            requestId={archivesQuery.error.requestId}
            onRetry={() => archivesQuery.refetch()}
          />
        )}

        {!archivesQuery.isLoading && !archivesQuery.error && archives.length === 0 && (
          <EmptyState
            title="No report archives exist"
            description="No reports have been archived yet. Administrators can trigger a report archive above."
          />
        )}

        {!archivesQuery.isLoading && !archivesQuery.error && archives.length > 0 && (
          <div className="matte-card overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-matte-900/80 border-b border-matte-800 text-matte-400 font-medium">
                  <tr>
                    <th className="py-3 px-4">Type</th>
                    <th className="py-3 px-4">Storage Backend</th>
                    <th className="py-3 px-4">File Size</th>
                    <th className="py-3 px-4">Object Key</th>
                    <th className="py-3 px-4">Archived At</th>
                    <th className="py-3 px-4 text-right">Download</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-matte-800/60 bg-matte-950/40 font-mono">
                  {archives.map((item) => (
                    <tr key={item.id} className="hover:bg-matte-800/30">
                      <td className="py-3 px-4 font-sans font-semibold text-matte-200">
                        {ReportTypeLabels[item.report_type] || item.report_type}
                      </td>
                      <td className="py-3 px-4 uppercase text-pastel-lavender">
                        {item.storage_backend}
                      </td>
                      <td className="py-3 px-4 text-matte-400">
                        {formatBytes(item.size_bytes)}
                      </td>
                      <td className="py-3 px-4 text-matte-400 truncate max-w-xs">
                        {item.object_key}
                      </td>
                      <td className="py-3 px-4 text-matte-400">
                        {formatTimestamp(item.created_at)}
                      </td>
                      <td className="py-3 px-4 text-right font-sans">
                        <button
                          type="button"
                          onClick={() => handleDownloadArchive(item.id)}
                          className="btn-secondary text-[11px] py-1 px-2.5 inline-flex items-center gap-1.5 hover:border-pastel-lavender/50"
                        >
                          <Download className="w-3.5 h-3.5" />
                          <span>Download</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {archivesQuery.data && (
              <Pagination
                page={archivesQuery.data.page}
                pageSize={archivesQuery.data.page_size}
                totalItems={archivesQuery.data.total_items}
                totalPages={archivesQuery.data.total_pages}
                onPageChange={(p) => setArchivePage(p)}
                onPageSizeChange={(ps) => {
                  setArchivePageSize(ps);
                  setArchivePage(1);
                }}
              />
            )}
          </div>
        )}
      </div>

      {/* Archive Modal for Admins */}
      {isArchiveModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={() => setIsArchiveModalOpen(false)} />
          <div className="relative w-full max-w-md matte-card p-6 bg-matte-900 border border-matte-700 shadow-2xl z-10 space-y-4">
            <h3 className="text-base font-bold text-matte-100">Create Report Archive</h3>
            <p className="text-xs text-matte-400">
              Generates and securely stores an immutable report into the configured storage backend (S3 or local).
            </p>

            {archiveError && (
              <div className="p-2.5 rounded bg-pastel-rose-bg border border-pastel-rose-border text-pastel-rose-light text-xs">
                {archiveError}
              </div>
            )}

            <form onSubmit={handleCreateArchive} className="space-y-4 text-xs">
              <div>
                <label className="block text-[11px] font-medium text-matte-400 mb-1">Report Type</label>
                <select
                  value={selectedReportType}
                  onChange={(e) => setSelectedReportType(e.target.value)}
                  className="input-matte w-full"
                >
                  <option value={ReportType.SUMMARY}>{ReportTypeLabels.SUMMARY}</option>
                  <option value={ReportType.LOGS_CSV}>{ReportTypeLabels.LOGS_CSV}</option>
                  <option value={ReportType.ALERTS_CSV}>{ReportTypeLabels.ALERTS_CSV}</option>
                </select>
              </div>

              <div className="p-3 rounded bg-matte-950 border border-matte-800 text-[11px] text-matte-400 space-y-1">
                <div>From: <span className="font-mono text-matte-300">{formatTimestamp(dateRange.from, true)}</span></div>
                <div>To: <span className="font-mono text-matte-300">{formatTimestamp(dateRange.to, true)}</span></div>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-matte-800">
                <button
                  type="button"
                  onClick={() => setIsArchiveModalOpen(false)}
                  disabled={isSubmittingArchive}
                  className="btn-secondary"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingArchive}
                  className="btn-primary"
                >
                  {isSubmittingArchive ? 'Archiving...' : 'Trigger Archival'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default ReportsPage;
