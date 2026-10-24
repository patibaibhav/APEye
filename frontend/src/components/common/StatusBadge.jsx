import React from 'react';
import { AlertStatus, InvestigationStatus } from '../../utils/constants';

export function StatusBadge({ status }) {
  const normalized = (status || '').toUpperCase();

  let styles = 'bg-matte-800 text-matte-300 border-matte-700';

  if (normalized === AlertStatus.ACTIVE || normalized === InvestigationStatus.NEW) {
    styles = 'bg-pastel-amber-bg text-pastel-amber-light border-pastel-amber-border';
  } else if (normalized === AlertStatus.INVESTIGATING) {
    styles = 'bg-pastel-lavender-bg text-pastel-lavender-light border-pastel-lavender-border';
  } else if (normalized === AlertStatus.RESOLVED) {
    styles = 'bg-matte-800/80 text-matte-400 border-matte-700';
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles}`}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-75" />
      {normalized || 'UNKNOWN'}
    </span>
  );
}

export default StatusBadge;
