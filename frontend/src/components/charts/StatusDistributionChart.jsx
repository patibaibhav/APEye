import React from 'react';
import {
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
} from 'recharts';
import { formatNumber } from '../../utils/formatters';

const STATUS_COLOR_MAP = {
  '2xx': '#4ade80',
  '3xx': '#94a3b8',
  '4xx': '#fbbf24',
  '5xx': '#f87171',
};

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0];
    return (
      <div className="matte-card p-2.5 shadow-xl border border-matte-700 bg-matte-900/95 text-xs">
        <div className="flex items-center gap-2">
          <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: data.payload.color }} />
          <span className="text-matte-300 font-medium">{data.name}:</span>
          <span className="text-matte-100 font-bold">{formatNumber(data.value)}</span>
        </div>
      </div>
    );
  }
  return null;
};

export function StatusDistributionChart({ classes = [] }) {
  if (!classes || classes.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-matte-500 text-xs">
        No status code data available
      </div>
    );
  }

  const chartData = classes.map((item) => ({
    name: item.status_class,
    value: item.count,
    color: STATUS_COLOR_MAP[item.status_class] || '#b4a2f8',
  }));

  const total = chartData.reduce((acc, curr) => acc + curr.value, 0);

  return (
    <div className="w-full h-64 relative flex items-center justify-center">
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={80}
            paddingAngle={3}
            dataKey="value"
          >
            {chartData.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={entry.color} stroke="#16161b" strokeWidth={2} />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="bottom"
            align="center"
            wrapperStyle={{ paddingTop: '10px', fontSize: '11px', color: '#9e9ea9' }}
          />
        </PieChart>
      </ResponsiveContainer>
      {/* Center Label */}
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 -mt-3 text-center pointer-events-none">
        <span className="block text-lg font-bold text-matte-100">{formatNumber(total)}</span>
        <span className="block text-[10px] text-matte-400 uppercase tracking-wider">Total</span>
      </div>
    </div>
  );
}

export default StatusDistributionChart;
