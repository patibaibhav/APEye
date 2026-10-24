import React from 'react';
import DataTable from '../common/DataTable';
import { formatTimestamp, formatDuration } from '../../utils/formatters';

const METHOD_COLOR_MAP = {
  GET: 'text-pastel-mint-light bg-pastel-mint-bg border-pastel-mint-border',
  POST: 'text-pastel-lavender-light bg-pastel-lavender-bg border-pastel-lavender-border',
  PUT: 'text-pastel-amber-light bg-pastel-amber-bg border-pastel-amber-border',
  PATCH: 'text-pastel-amber-light bg-pastel-amber-bg border-pastel-amber-border',
  DELETE: 'text-pastel-rose-light bg-pastel-rose-bg border-pastel-rose-border',
};

function getStatusBadge(code) {
  let style = 'bg-matte-800 text-matte-300 border-matte-700';
  if (code >= 200 && code < 300) {
    style = 'bg-pastel-mint-bg text-pastel-mint-light border-pastel-mint-border';
  } else if (code >= 300 && code < 400) {
    style = 'bg-pastel-slate-bg text-pastel-slate-light border-pastel-slate-border';
  } else if (code >= 400 && code < 500) {
    style = 'bg-pastel-amber-bg text-pastel-amber-light border-pastel-amber-border';
  } else if (code >= 500) {
    style = 'bg-pastel-rose-bg text-pastel-rose-light border-pastel-rose-border';
  }

  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-mono font-medium border ${style}`}>
      {code}
    </span>
  );
}

export function LogsTable({ logs = [], onSelectLog }) {
  const columns = [
    {
      key: 'occurred_at',
      header: 'Timestamp',
      className: 'w-44',
      render: (row) => (
        <span className="font-mono text-matte-300 text-[11px]">
          {formatTimestamp(row.occurred_at)}
        </span>
      ),
    },
    {
      key: 'source_ip',
      header: 'Client IP',
      className: 'w-36',
      render: (row) => (
        <span className="font-mono text-matte-200 text-[11px] font-medium">
          {row.source_ip}
        </span>
      ),
    },
    {
      key: 'method',
      header: 'Method',
      className: 'w-20',
      render: (row) => {
        const style = METHOD_COLOR_MAP[row.method] || 'bg-matte-800 text-matte-400 border-matte-700';
        return (
          <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] font-mono font-bold border ${style}`}>
            {row.method}
          </span>
        );
      },
    },
    {
      key: 'path',
      header: 'Path',
      render: (row) => (
        <span className="font-mono text-matte-200 text-[11px] truncate block max-w-xs md:max-w-md">
          {row.path}
        </span>
      ),
    },
    {
      key: 'status_code',
      header: 'Status',
      className: 'w-20',
      render: (row) => getStatusBadge(row.status_code),
    },
    {
      key: 'response_time_ms',
      header: 'Latency',
      className: 'w-24',
      render: (row) => (
        <span className="font-mono text-matte-400 text-[11px]">
          {formatDuration(row.response_time_ms)}
        </span>
      ),
    },
    {
      key: 'auth_outcome',
      header: 'Auth Outcome',
      className: 'w-32',
      render: (row) => {
        const isSuccess = row.auth_outcome === 'AUTHENTICATED' || row.auth_outcome === 'LOGIN_SUCCESS';
        const isFail = row.auth_outcome === 'LOGIN_FAILED' || row.auth_outcome === 'TOKEN_EXPIRED' || row.auth_outcome === 'FORBIDDEN';
        let style = 'text-matte-500';
        if (isSuccess) style = 'text-pastel-mint-light';
        if (isFail) style = 'text-pastel-rose-light';
        return (
          <span className={`text-[10px] uppercase tracking-wider font-semibold ${style}`}>
            {row.auth_outcome || 'NONE'}
          </span>
        );
      },
    },
  ];

  return <DataTable columns={columns} data={logs} keyField="id" onRowClick={onSelectLog} />;
}

export default LogsTable;
