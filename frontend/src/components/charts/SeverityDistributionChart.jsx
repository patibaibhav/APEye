import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
} from 'recharts';
import { formatNumber } from '../../utils/formatters';

const SEVERITY_COLOR_MAP = {
  LOW: '#4ade80',
  MEDIUM: '#fbbf24',
  HIGH: '#f87171',
};

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div className="matte-card p-2.5 shadow-xl border border-matte-700 bg-matte-900/95 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: data.payload.color }} />
          <span className="text-matte-300 font-medium">{data.payload.severity}:</span>
          <span className="text-matte-100 font-bold">{formatNumber(data.value)}</span>
        </div>
      </div>
    );
  }
  return null;
};

export function SeverityDistributionChart({ items = [] }) {
  if (!items || items.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-matte-500 text-xs">
        No alert severity data
      </div>
    );
  }

  const chartData = ['LOW', 'MEDIUM', 'HIGH'].map((sev) => {
    const found = items.find((i) => (i.severity || '').toUpperCase() === sev);
    return {
      severity: sev,
      count: found ? found.count : 0,
      color: SEVERITY_COLOR_MAP[sev],
    };
  });

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={chartData} margin={{ top: 15, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#23232b" vertical={false} />
          <XAxis dataKey="severity" stroke="#525260" tick={{ fill: '#717180', fontSize: 11 }} />
          <YAxis stroke="#525260" tick={{ fill: '#717180', fontSize: 10 }} allowDecimals={false} />
          <Tooltip content={<CustomTooltip />} />
          <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={38}>
            {chartData.map((entry, index) => (
              <Cell key={`sev-cell-${index}`} fill={entry.color} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default SeverityDistributionChart;
