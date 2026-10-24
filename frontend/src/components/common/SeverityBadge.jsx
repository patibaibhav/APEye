import React from 'react';
import { Severity } from '../../utils/constants';

export function SeverityBadge({ severity }) {
  const normalized = (severity || '').toUpperCase();

  let styles = 'bg-matte-800 text-matte-300 border-matte-700';

  if (normalized === Severity.HIGH) {
    styles = 'bg-pastel-rose-bg text-pastel-rose-light border-pastel-rose-border';
  } else if (normalized === Severity.MEDIUM) {
    styles = 'bg-pastel-amber-bg text-pastel-amber-light border-pastel-amber-border';
  } else if (normalized === Severity.LOW) {
    styles = 'bg-pastel-mint-bg text-pastel-mint-light border-pastel-mint-border';
  }

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles}`}
    >
      <span className="w-1.5 h-1.5 rounded-full mr-1.5 bg-current opacity-80" />
      {normalized || 'UNKNOWN'}
    </span>
  );
}

export default SeverityBadge;
