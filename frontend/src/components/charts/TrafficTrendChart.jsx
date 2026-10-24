import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { formatTimestamp, formatNumber } from '../../utils/formatters';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="matte-card p-3 shadow-xl border border-matte-700 bg-matte-900/95 text-xs space-y-1.5">
        <p className="font-medium text-matte-300">{formatTimestamp(label)}</p>
        {payload.map((entry, index) => (
          <div key={`item-${index}`} className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
              <span className="text-matte-400 capitalize">{entry.name}:</span>
            </div>
            <span className="font-semibold text-matte-100">{formatNumber(entry.value)}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function TrafficTrendChart({ points = [] }) {
  if (!points || points.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-matte-500 text-xs">
        No traffic data recorded in this time window
      </div>
    );
  }

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={points} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="colorSuccess" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4ade80" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#4ade80" stopOpacity={0.0} />
            </linearGradient>
            <linearGradient id="colorFailed" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f87171" stopOpacity={0.25} />
              <stop offset="95%" stopColor="#f87171" stopOpacity={0.0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#23232b" vertical={false} />
          <XAxis
            dataKey="bucket_start"
            stroke="#525260"
            tick={{ fill: '#717180', fontSize: 10 }}
            tickFormatter={(val) => {
              try {
                const d = new Date(val);
                return `${d.getHours()}:${String(d.getMinutes()).padStart(2, '0')}`;
              } catch {
                return val;
              }
            }}
          />
          <YAxis stroke="#525260" tick={{ fill: '#717180', fontSize: 10 }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="top"
            align="right"
            wrapperStyle={{ paddingBottom: '10px', fontSize: '11px', color: '#9e9ea9' }}
          />
          <Area
            type="monotone"
            dataKey="successful"
            name="Successful"
            stroke="#4ade80"
            strokeWidth={1.75}
            fillOpacity={1}
            fill="url(#colorSuccess)"
          />
          <Area
            type="monotone"
            dataKey="failed"
            name="Failed"
            stroke="#f87171"
            strokeWidth={1.75}
            fillOpacity={1}
            fill="url(#colorFailed)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}

export default TrafficTrendChart;
