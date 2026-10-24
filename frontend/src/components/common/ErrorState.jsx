import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

export function ErrorState({
  title = 'Failed to load data',
  message = 'An unexpected error occurred while processing your request.',
  requestId = null,
  onRetry = null,
}) {
  return (
    <div className="w-full matte-card p-6 border-pastel-rose-border bg-pastel-rose-bg/20 text-center" role="alert">
      <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-pastel-rose-bg text-pastel-rose mb-3">
        <AlertCircle className="w-6 h-6" />
      </div>
      <h3 className="text-base font-semibold text-matte-100">{title}</h3>
      <p className="mt-1 text-sm text-matte-300 max-w-md mx-auto">{message}</p>

      {requestId && (
        <div className="mt-3 inline-flex items-center gap-1.5 px-2.5 py-1 rounded bg-background text-xs font-mono text-matte-400 border border-matte-800">
          <span className="text-matte-500">Request ID:</span>
          <span className="select-all">{requestId}</span>
        </div>
      )}

      {onRetry && (
        <div className="mt-5">
          <button
            type="button"
            onClick={onRetry}
            className="btn-secondary inline-flex items-center gap-2 text-xs py-2 px-3 hover:border-matte-600"
          >
            <RefreshCw className="w-3.5 h-3.5" />
            <span>Try Again</span>
          </button>
        </div>
      )}
    </div>
  );
}

export default ErrorState;
