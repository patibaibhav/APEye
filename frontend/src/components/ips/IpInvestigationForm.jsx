import React, { useState, useEffect } from 'react';
import { X, ShieldCheck, AlertCircle } from 'lucide-react';
import { InvestigationStatus } from '../../utils/constants';

export function IpInvestigationForm({ ipData, onClose, onSave, isSaving = false }) {
  const [status, setStatus] = useState(ipData?.investigation_status || InvestigationStatus.NEW);
  const [note, setNote] = useState(ipData?.investigation_note || '');
  const [errorMsg, setErrorMsg] = useState('');

  useEffect(() => {
    if (ipData) {
      setStatus(ipData.investigation_status || InvestigationStatus.NEW);
      setNote(ipData.investigation_note || '');
    }
  }, [ipData]);

  if (!ipData) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (note && note.length > 2000) {
      setErrorMsg('Note cannot exceed 2000 characters');
      return;
    }

    setErrorMsg('');
    try {
      await onSave(ipData.source_ip, { status, note: note.trim() || undefined });
      onClose();
    } catch (err) {
      setErrorMsg(err.message || 'Failed to update investigation');
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-hidden flex items-center justify-center p-4">
      {/* Backdrop */}
      <div className="fixed inset-0 bg-black/60 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-lg matte-card p-6 shadow-2xl z-10 border border-matte-700 bg-matte-900">
        <div className="flex items-center justify-between pb-4 border-b border-matte-800">
          <div className="flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-pastel-lavender" />
            <div>
              <h2 className="text-base font-bold text-matte-100">IP Investigation</h2>
              <p className="text-xs font-mono text-matte-400">{ipData.source_ip}</p>
            </div>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="p-1 rounded text-matte-400 hover:text-matte-100"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4 text-xs">
          {/* Status select */}
          <div>
            <label htmlFor="investigation-status" className="block text-[11px] font-medium text-matte-400 mb-1.5">
              Investigation Status
            </label>
            <select
              id="investigation-status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="input-matte w-full"
            >
              <option value={InvestigationStatus.NEW}>NEW (Pending Review)</option>
              <option value={InvestigationStatus.INVESTIGATING}>INVESTIGATING (Under Analysis)</option>
              <option value={InvestigationStatus.RESOLVED}>RESOLVED (Action Taken / Benign)</option>
            </select>
          </div>

          {/* Investigation note */}
          <div>
            <label htmlFor="case-notes" className="block text-[11px] font-medium text-matte-400 mb-1.5">
              Case Notes (optional, max 2000 chars)
            </label>
            <textarea
              id="case-notes"
              rows={4}
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Record forensic intelligence, attribution, or mitigating actions..."
              maxLength={2000}
              className="input-matte w-full resize-none"
            />
            <span className="text-[10px] text-matte-500 font-mono block text-right mt-1">
              {note.length}/2000
            </span>
          </div>

          {errorMsg && (
            <div className="p-2 rounded bg-pastel-rose-bg border border-pastel-rose-border text-pastel-rose-light text-xs flex items-center gap-1.5">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
          )}

          <div className="flex justify-end gap-2 pt-3 border-t border-matte-800">
            <button
              type="button"
              onClick={onClose}
              disabled={isSaving}
              className="btn-secondary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSaving}
              className="btn-primary"
            >
              {isSaving ? 'Saving...' : 'Update Investigation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default IpInvestigationForm;
