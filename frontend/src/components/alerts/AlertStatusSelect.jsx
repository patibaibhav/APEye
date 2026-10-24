import React, { useState } from 'react';
import { AlertStatus } from '../../utils/constants';

const ALLOWED_TRANSITIONS = {
  [AlertStatus.ACTIVE]: [AlertStatus.INVESTIGATING, AlertStatus.RESOLVED],
  [AlertStatus.INVESTIGATING]: [AlertStatus.ACTIVE, AlertStatus.RESOLVED],
  [AlertStatus.RESOLVED]: [AlertStatus.ACTIVE],
};

export function AlertStatusSelect({ currentStatus, onStatusChange, isLoading = false }) {
  const [selected, setSelected] = useState(currentStatus);

  const allowedNextStatuses = ALLOWED_TRANSITIONS[currentStatus] || [];

  const handleApply = async () => {
    if (selected === currentStatus) return;
    await onStatusChange(selected);
  };

  return (
    <div className="flex items-center gap-2">
      <select
        value={selected}
        onChange={(e) => setSelected(e.target.value)}
        disabled={isLoading || allowedNextStatuses.length === 0}
        className="bg-matte-900 border border-matte-700 text-matte-200 rounded-lg px-3 py-1.5 text-xs focus:outline-none focus:border-pastel-lavender disabled:opacity-50"
      >
        <option value={currentStatus}>{currentStatus} (Current)</option>
        {allowedNextStatuses.map((st) => (
          <option key={st} value={st}>
            Mark as {st}
          </option>
        ))}
      </select>

      {selected !== currentStatus && (
        <button
          type="button"
          onClick={handleApply}
          disabled={isLoading}
          className="btn-primary text-xs py-1.5 px-3 flex items-center gap-1"
        >
          {isLoading ? 'Updating...' : 'Save Status'}
        </button>
      )}
    </div>
  );
}

export default AlertStatusSelect;
