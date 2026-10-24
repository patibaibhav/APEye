import React from 'react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { truncateText, formatNumber } from '../../utils/formatters';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="matte-card p-3 shadow-xl border border-matte-700 bg-matte-900/95 text-xs space-y-1">
        <p className="font-mono text-matte-300 break-all">{label}</p>
        {payload.map((entry, index) => (
          <div key={`entry-${index}`} className="flex items-center justify-between gap-4">
            <span className="text-matte-400 capitalize">{entry.name}:</span>
            <span className="font-semibold text-matte-100">{formatNumber(entry.value)}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function TopEndpointsChart({ items = [] }) {
  if (!items || items.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-matte-500 text-xs">
        No endpoint traffic recorded
      </div>
    );
  }

  // Slice to top 7 for neat layout
  const displayItems = items.slice(0, 7);

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          layout="vertical"
          data={displayItems}
          margin={{ top: 10, right: 10, left: 20, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="#23232b" horizontal={false} />
          <XAxis type="number" stroke="#525260" tick={{ fill: '#717180', fontSize: 10 }} />
          <YAxis
            type="category"
            dataKey="endpoint"
            stroke="#525260"
            tick={{ fill: '#9e9ea9', fontSize: 10 }}
            tickFormatter={(val) => truncateText(val, 20)}
            width={120}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="top"
            align="right"
            wrapperStyle={{ paddingBottom: '10px', fontSize: '11px', color: '#9e9ea9' }}
          />
          <Bar dataKey="request_count" name="Requests" fill="#b4a2f8" radius={[0, 4, 4, 0]} maxBarSize={16} />
          <Bar dataKey="error_count" name="Errors" fill="#f87171" radius={[0, 4, 4, 0]} maxBarSize={16} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TopEndpointsChart;
