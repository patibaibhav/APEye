import React, { useState } from 'react';
import { UserCheck, RefreshCw, Filter, X } from 'lucide-react';
import useApiQuery from '../hooks/useApiQuery';
import ipsApi from '../api/ipsApi';
import { getDefaultDateRange } from '../utils/queryParams';
import { InvestigationStatus } from '../utils/constants';
import SuspiciousIpTable from '../components/ips/SuspiciousIpTable';
import IpInvestigationForm from '../components/ips/IpInvestigationForm';
import DateRangeFilter from '../components/common/DateRangeFilter';
import Pagination from '../components/common/Pagination';
import LoadingState from '../components/common/LoadingState';
import ErrorState from '../components/common/ErrorState';
import EmptyState from '../components/common/EmptyState';

export function SuspiciousIpsPage() {
  const [filters, setFilters] = useState(() => ({
    ...getDefaultDateRange(24 * 7),
    status: '',
    page: 1,
    page_size: 25,
  }));

  const [activeIpData, setActiveIpData] = useState(null);
  const [isSaving, setIsSaving] = useState(false);

  const ipsQuery = useApiQuery(
    () => ipsApi.list(filters),
    [filters.status, filters.from, filters.to, filters.page, filters.page_size]
  );

  const handleResetFilters = () => {
    setFilters({
      ...getDefaultDateRange(24 * 7),
      status: '',
      page: 1,
      page_size: filters.page_size,
    });
  };

  const handleSaveInvestigation = async (ip, data) => {
    setIsSaving(true);
    try {
      await ipsApi.setInvestigation(ip, data);
      await ipsQuery.refetch();
    } finally {
      setIsSaving(false);
    }
  };

  const pageData = ipsQuery.data;
  const items = pageData?.items || [];
  const isLoading = ipsQuery.isLoading && !ipsQuery.data;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold tracking-tight text-matte-100 flex items-center gap-2">
            <UserCheck className="w-5 h-5 text-pastel-lavender" />
            <span>Suspicious IP Directory</span>
          </h1>
          <p className="text-xs text-matte-400 mt-0.5">
            Client IP addresses flagged with security alerts, request anomalies, and triage cases
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => ipsQuery.refetch()}
            className="p-2 rounded-lg bg-matte-800 border border-matte-700 text-matte-300 hover:text-matte-100 hover:bg-matte-700 transition"
            title="Refresh list"
            aria-label="Refresh list"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${ipsQuery.isLoading ? 'animate-spin text-pastel-lavender' : ''}`} />
          </button>
        </div>
      </div>

      {/* Filter Bar */}
      <div className="matte-card p-4 flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-xs text-matte-400">
            <Filter className="w-3.5 h-3.5 text-pastel-lavender" />
            <span>Investigation Status:</span>
          </div>
          <select
            value={filters.status || ''}
            onChange={(e) => setFilters({ ...filters, status: e.target.value, page: 1 })}
            className="input-matte text-xs py-1 px-2.5"
          >
            <option value="">All Statuses</option>
            {Object.values(InvestigationStatus).map((st) => (
              <option key={st} value={st}>{st}</option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <DateRangeFilter
            from={filters.from}
            to={filters.to}
            onChange={({ from, to }) => setFilters({ ...filters, from, to, page: 1 })}
          />
          {filters.status && (
            <button
              type="button"
              onClick={handleResetFilters}
              className="btn-secondary text-xs py-1 px-2 flex items-center gap-1"
            >
              <X className="w-3 h-3" />
              <span>Reset</span>
            </button>
          )}
        </div>
      </div>

      {/* Main States */}
      {isLoading && <LoadingState message="Fetching suspicious IP directory..." rows={6} />}

      {!isLoading && ipsQuery.error && (
        <ErrorState
          title="Failed to load suspicious IPs"
          message={ipsQuery.error.message || 'Error querying suspicious IP aggregation.'}
          requestId={ipsQuery.error.requestId}
          onRetry={() => ipsQuery.refetch()}
        />
      )}

      {!isLoading && !ipsQuery.error && items.length === 0 && (
        <EmptyState
          title="No suspicious IPs found"
          description="There are no client IPs associated with active alerts in the selected time window."
        />
      )}

      {!isLoading && !ipsQuery.error && items.length > 0 && (
        <div className="matte-card overflow-hidden">
          <SuspiciousIpTable
            ips={items}
            onSelectIp={(ipItem) => setActiveIpData(ipItem)}
          />
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

      {/* Investigation Modal */}
      <IpInvestigationForm
        ipData={activeIpData}
        onClose={() => setActiveIpData(null)}
        onSave={handleSaveInvestigation}
        isSaving={isSaving}
      />
    </div>
  );
}

export default SuspiciousIpsPage;
