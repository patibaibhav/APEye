import React from 'react';

export function LoadingState({ message = 'Loading data...', rows = 4, spinner = false }) {
  if (spinner) {
    return (
      <div className="flex flex-col items-center justify-center p-12 text-center" role="status" aria-label="Loading">
        <div className="w-8 h-8 rounded-full border-2 border-matte-700 border-t-pastel-lavender animate-spin" />
        <p className="mt-4 text-sm text-matte-400 font-medium">{message}</p>
      </div>
    );
  }

  return (
    <div className="w-full space-y-4 p-6 matte-card animate-pulse" role="status" aria-label="Loading">
      <div className="h-5 bg-matte-800 rounded w-1/4 mb-4" />
      {Array.from({ length: rows }).map((_, idx) => (
        <div key={idx} className="space-y-2">
          <div className="h-4 bg-matte-800/80 rounded w-full" />
          <div className="h-4 bg-matte-850 rounded w-5/6" />
        </div>
      ))}
      <span className="sr-only">{message}</span>
    </div>
  );
}

export default LoadingState;
