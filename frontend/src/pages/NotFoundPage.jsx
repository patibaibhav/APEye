import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Compass, ArrowLeft } from 'lucide-react';

export function NotFoundPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <div className="matte-card p-8 max-w-md w-full text-center space-y-4 bg-matte-900 shadow-2xl border border-matte-800">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-matte-800 text-pastel-lavender mb-1">
          <Compass className="w-8 h-8" />
        </div>
        <h1 className="text-xl font-bold text-matte-100">404 — Page Not Found</h1>
        <p className="text-xs text-matte-400">
          The security monitoring view you requested does not exist or has been relocated.
        </p>
        <div className="pt-2">
          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="btn-primary inline-flex items-center gap-2 text-xs py-2 px-4"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Return to Dashboard</span>
          </button>
        </div>
      </div>
    </div>
  );
}

export default NotFoundPage;
