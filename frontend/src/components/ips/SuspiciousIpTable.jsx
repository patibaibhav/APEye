import React from 'react';
import DataTable from '../common/DataTable';
import StatusBadge from '../common/StatusBadge';
import { ThreatCategoryLabels } from '../../utils/constants';
import { formatTimestamp, formatRelativeTime, formatNumber } from '../../utils/formatters';

export function SuspiciousIpTable({ ips = [], onSelectIp }) {
  const columns = [
    {
      key: 'source_ip',
      header: 'Source IP',
      className: 'w-40',
      render: (row) => (
        <span className="font-mono font-semibold text-matte-200 text-xs">{row.source_ip}</span>
      ),
    },
    {
      key: 'categories',
      header: 'Threat Categories',
      render: (row) => (
        <div className="flex flex-wrap gap-1">
          {(row.categories || []).map((cat) => (
            <span
              key={cat}
              className="inline-block px-2 py-0.5 rounded text-[10px] font-medium bg-matte-800 text-matte-300 border border-matte-700"
            >
              {ThreatCategoryLabels[cat] || cat}
            </span>
          ))}
        </div>
      ),
    },
    {
      key: 'suspicious_request_count',
      header: 'Suspicious Reqs',
      className: 'w-32',
      render: (row) => (
        <span className="font-mono font-medium text-pastel-rose-light">
          {formatNumber(row.suspicious_request_count)}
        </span>
      ),
    },
    {
      key: 'open_alert_count',
      header: 'Open / Total Alerts',
      className: 'w-36',
      render: (row) => (
        <span className="font-mono text-matte-300">
          <span className="text-pastel-amber-light font-bold">{row.open_alert_count}</span>
          {' / '}
          <span>{row.alert_count}</span>
        </span>
      ),
    },
    {
      key: 'latest_activity',
      header: 'Latest Activity',
      className: 'w-36',
      render: (row) => (
        <span className="text-matte-400" title={formatTimestamp(row.latest_activity)}>
          {formatRelativeTime(row.latest_activity)}
        </span>
      ),
    },
    {
      key: 'investigation_status',
      header: 'Status',
      className: 'w-32',
      render: (row) => <StatusBadge status={row.investigation_status} />,
    },
    {
      key: 'actions',
      header: '',
      className: 'w-24 text-right',
      render: (row) => (
        <button
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            onSelectIp(row);
          }}
          className="btn-secondary text-[11px] py-1 px-2 hover:border-pastel-lavender/50"
        >
          Investigate
        </button>
      ),
    },
  ];

  return <DataTable columns={columns} data={ips} keyField="source_ip" onRowClick={onSelectIp} />;
}

export default SuspiciousIpTable;
