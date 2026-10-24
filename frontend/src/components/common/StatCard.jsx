import React from 'react';

export function StatCard({
  title,
  value,
  subtitle,
  icon: Icon,
  accent = 'lavender', // 'lavender' | 'mint' | 'amber' | 'rose' | 'slate'
}) {
  const accentBorderMap = {
    lavender: 'border-l-pastel-lavender',
    mint: 'border-l-pastel-mint',
    amber: 'border-l-pastel-amber',
    rose: 'border-l-pastel-rose',
    slate: 'border-l-pastel-slate',
  };

  const accentIconMap = {
    lavender: 'text-pastel-lavender bg-pastel-lavender-bg',
    mint: 'text-pastel-mint bg-pastel-mint-bg',
    amber: 'text-pastel-amber bg-pastel-amber-bg',
    rose: 'text-pastel-rose bg-pastel-rose-bg',
    slate: 'text-pastel-slate bg-pastel-slate-bg',
  };

  return (
    <div className={`matte-card p-5 border-l-4 ${accentBorderMap[accent] || accentBorderMap.lavender}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-matte-400 tracking-wider uppercase">{title}</span>
        {Icon && (
          <div className={`p-2 rounded-lg ${accentIconMap[accent] || accentIconMap.lavender}`}>
            <Icon className="w-4 h-4" />
          </div>
        )}
      </div>
      <div className="mt-2 flex items-baseline">
        <span className="text-2xl font-bold text-matte-100 tracking-tight">{value}</span>
      </div>
      {subtitle && <p className="mt-1 text-xs text-matte-400">{subtitle}</p>}
    </div>
  );
}

export default StatCard;
