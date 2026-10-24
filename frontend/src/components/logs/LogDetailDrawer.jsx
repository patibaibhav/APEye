import React from 'react';
import { X, Copy, Check } from 'lucide-react';
import { formatTimestamp, formatDuration } from '../../utils/formatters';

export function LogDetailDrawer({ log, onClose }) {
  const [copied, setCopied] = React.useState(false);

  if (!log) return null;

  const handleCopyRequestId = () => {
    if (log.request_id) {
      navigator.clipboard.writeText(log.request_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex justify-end">
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm transition-opacity"
        onClick={onClose}
      />

      <div className="relative w-full max-w-lg bg-[#141419] border-l border-matte-800 h-full p-6 shadow-2xl flex flex-col z-10 overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-matte-800">
          <div>
            <h2 className="text-base font-bold text-matte-100">API Request Details</h2>
            <p className="text-xs text-matte-400 font-mono mt-0.5">ID: #{log.id}</p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1.5 rounded-lg text-matte-400 hover:text-matte-100 hover:bg-matte-800"
            aria-label="Close drawer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="mt-6 space-y-5 text-xs">
          {/* Request ID */}
          <div className="matte-card p-3.5 space-y-1">
            <span className="text-[11px] font-medium text-matte-400">Request ID (X-Request-ID)</span>
            <div className="flex items-center justify-between gap-2 mt-1">
              <span className="font-mono text-matte-200 select-all break-all">{log.request_id}</span>
              <button
                type="button"
                onClick={handleCopyRequestId}
                className="p-1.5 rounded bg-matte-800 text-matte-300 hover:text-matte-100"
                title="Copy Request ID"
              >
                {copied ? <Check className="w-3.5 h-3.5 text-pastel-mint" /> : <Copy className="w-3.5 h-3.5" />}
              </button>
            </div>
          </div>

          {/* Key metadata grid */}
          <div className="grid grid-cols-2 gap-3">
            <div className="matte-card p-3">
              <span className="text-[11px] font-medium text-matte-400 block mb-1">Method</span>
              <span className="font-mono font-bold text-sm text-matte-100">{log.method}</span>
            </div>
            <div className="matte-card p-3">
              <span className="text-[11px] font-medium text-matte-400 block mb-1">Status Code</span>
              <span className="font-mono font-bold text-sm text-matte-100">{log.status_code}</span>
            </div>
            <div className="matte-card p-3">
              <span className="text-[11px] font-medium text-matte-400 block mb-1">Response Time</span>
              <span className="font-mono text-sm text-matte-100">{formatDuration(log.response_time_ms)}</span>
            </div>
            <div className="matte-card p-3">
              <span className="text-[11px] font-medium text-matte-400 block mb-1">Auth Outcome</span>
              <span className="font-semibold text-xs text-pastel-lavender">{log.auth_outcome || 'NONE'}</span>
            </div>
          </div>

          {/* Full Path */}
          <div className="matte-card p-3.5 space-y-1">
            <span className="text-[11px] font-medium text-matte-400">Request Path</span>
            <p className="font-mono text-matte-100 select-all break-all pt-1">{log.path}</p>
          </div>

          {/* Client IP & User */}
          <div className="grid grid-cols-2 gap-3">
            <div className="matte-card p-3">
              <span className="text-[11px] font-medium text-matte-400 block mb-1">Client IP</span>
              <span className="font-mono text-matte-200">{log.source_ip}</span>
            </div>
            <div className="matte-card p-3">
              <span className="text-[11px] font-medium text-matte-400 block mb-1">User ID</span>
              <span className="font-mono text-matte-200">{log.user_id !== null && log.user_id !== undefined ? `#${log.user_id}` : 'Anonymous'}</span>
            </div>
          </div>

          {/* Timestamp */}
          <div className="matte-card p-3.5 space-y-1">
            <span className="text-[11px] font-medium text-matte-400">Occurred At (UTC)</span>
            <p className="font-mono text-matte-300">{formatTimestamp(log.occurred_at, true)}</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LogDetailDrawer;
