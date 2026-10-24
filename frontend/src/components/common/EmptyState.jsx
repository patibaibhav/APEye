import React from 'react';
import { Inbox } from 'lucide-react';

export function EmptyState({
  title = 'No records found',
  description = 'There is no data matching your current filter criteria or time window.',
  action = null,
  icon: Icon = Inbox,
}) {
  return (
    <div className="w-full matte-card p-12 text-center flex flex-col items-center justify-center">
      <div className="w-12 h-12 rounded-xl bg-matte-800 border border-matte-700 flex items-center justify-center text-matte-400 mb-3">
        <Icon className="w-6 h-6" />
      </div>
      <h3 className="text-base font-medium text-matte-200">{title}</h3>
      <p className="mt-1 text-sm text-matte-400 max-w-sm">{description}</p>
      {action && <div className="mt-5">{action}</div>}
    </div>
  );
}

export default EmptyState;
