import React from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldX, ArrowLeft } from 'lucide-react';

export function ForbiddenPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-[70vh] flex items-center justify-center p-4">
      <div className="matte-card p-8 max-w-md w-full text-center space-y-4 border-pastel-rose-border bg-matte-900 shadow-2xl">
        <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-pastel-rose-bg text-pastel-rose mb-1">
          <ShieldX className="w-8 h-8" />
        </div>
        <h1 className="text-xl font-bold text-matte-100">403 — Access Denied</h1>
        <p className="text-xs text-matte-400">
          Your account does not possess the required administrative privileges to access this resource.
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

export default ForbiddenPage;
