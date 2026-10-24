import React from 'react';
import { ShieldAlert } from 'lucide-react';
import { formatNumber } from '../../utils/formatters';

export function AlertEvidencePanel({ evidence = {}, threshold, windowSeconds, requestCount }) {
  const hasEvidence = evidence && Object.keys(evidence).length > 0;

  return (
    <div className="matte-card p-5 space-y-4">
      <div className="flex items-center gap-2 border-b border-matte-800 pb-3">
        <ShieldAlert className="w-4 h-4 text-pastel-rose" />
        <h3 className="text-sm font-semibold text-matte-200">Detection Evidence</h3>
      </div>

      {/* Threshold comparison */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="p-3 rounded-lg bg-matte-900 border border-matte-800">
          <span className="text-[11px] font-medium text-matte-400 block mb-1">Trigger Threshold</span>
          <span className="font-mono text-base font-bold text-matte-200">{formatNumber(threshold)} requests</span>
        </div>
        <div className="p-3 rounded-lg bg-matte-900 border border-matte-800">
          <span className="text-[11px] font-medium text-matte-400 block mb-1">Observed Count</span>
          <span className="font-mono text-base font-bold text-pastel-rose-light">{formatNumber(requestCount)} requests</span>
        </div>
        <div className="p-3 rounded-lg bg-matte-900 border border-matte-800">
          <span className="text-[11px] font-medium text-matte-400 block mb-1">Detection Window</span>
          <span className="font-mono text-base font-bold text-matte-200">{windowSeconds}s</span>
        </div>
      </div>

      {/* Structured Evidence Payload */}
      {hasEvidence ? (
        <div className="space-y-2">
          <span className="text-[11px] font-medium text-matte-400 block">Rule Evidence Metadata:</span>
          <div className="rounded-lg bg-matte-950 p-4 border border-matte-800 overflow-x-auto">
            <pre className="font-mono text-xs text-pastel-lavender-light whitespace-pre-wrap break-all">
              {JSON.stringify(evidence, null, 2)}
            </pre>
          </div>
        </div>
      ) : (
        <p className="text-xs text-matte-500 italic">No additional evidence metadata provided.</p>
      )}
    </div>
  );
}

export default AlertEvidencePanel;
