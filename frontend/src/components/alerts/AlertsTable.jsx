import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ExternalLink } from 'lucide-react';
import DataTable from '../common/DataTable';
import SeverityBadge from '../common/SeverityBadge';
import StatusBadge from '../common/StatusBadge';
import { ThreatCategoryLabels } from '../../utils/constants';
import { formatTimestamp, formatRelativeTime } from '../../utils/formatters';

export function AlertsTable({ alerts = [] }) {
  const navigate = useNavigate();

  const columns = [
    {
      key: 'id',
      header: 'ID',
      className: 'w-16',
      render: (row) => <span className="font-mono text-matte-400">#{row.id}</span>,
    },
    {
      key: 'category',
      header: 'Category',
      render: (row) => (
        <div>
          <span className="font-semibold text-matte-200">
            {ThreatCategoryLabels[row.category] || row.category}
          </span>
          {row.endpoints && row.endpoints.length > 0 && (
            <span className="block font-mono text-[10px] text-matte-500 truncate max-w-xs">
              {row.endpoints[0]} {row.endpoints.length > 1 ? `(+${row.endpoints.length - 1})` : ''}
            </span>
          )}
        </div>
      ),
    },
    {
      key: 'severity',
      header: 'Severity',
      className: 'w-24',
      render: (row) => <SeverityBadge severity={row.severity} />,
    },
    {
      key: 'status',
      header: 'Status',
      className: 'w-28',
      render: (row) => <StatusBadge status={row.status} />,
    },
    {
      key: 'source_ip',
      header: 'Source IP',
      className: 'w-32',
      render: (row) => (
        <span className="font-mono font-medium text-matte-200">{row.source_ip}</span>
      ),
    },
    {
      key: 'request_count',
      header: 'Reqs / Window',
      className: 'w-28',
      render: (row) => (
        <span className="font-mono text-matte-300">
          {row.request_count} / {row.window_seconds}s
        </span>
      ),
    },
    {
      key: 'event_count',
      header: 'Events',
      className: 'w-20',
      render: (row) => (
        <span className="inline-block px-2 py-0.5 rounded bg-matte-800 text-matte-300 font-mono text-[11px]">
          {row.event_count}
        </span>
      ),
    },
    {
      key: 'last_detected_at',
      header: 'Last Detected',
      className: 'w-36',
      render: (row) => (
        <div title={formatTimestamp(row.last_detected_at)}>
          <span className="text-matte-300 block">{formatRelativeTime(row.last_detected_at)}</span>
        </div>
      ),
    },
    {
      key: 'actions',
      header: '',
      className: 'w-16 text-right',
      render: (row) => (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            navigate(`/alerts/${row.id}`);
          }}
          className="p-1 rounded text-matte-400 hover:text-pastel-lavender hover:bg-matte-800 transition"
          title="View Alert Details"
        >
          <ExternalLink className="w-4 h-4" />
        </button>
      ),
    },
  ];

  return (
    <DataTable
      columns={columns}
      data={alerts}
      keyField="id"
      onRowClick={(row) => navigate(`/alerts/${row.id}`)}
    />
  );
}

export default AlertsTable;
