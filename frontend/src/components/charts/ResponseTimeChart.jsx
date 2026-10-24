import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
} from 'recharts';
import { formatTimestamp, formatDuration } from '../../utils/formatters';

const CustomTooltip = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    return (
      <div className="matte-card p-3 shadow-xl border border-matte-700 bg-matte-900/95 text-xs space-y-1">
        <p className="font-medium text-matte-300">{formatTimestamp(label)}</p>
        {payload.map((entry, index) => (
          <div key={`entry-${index}`} className="flex items-center justify-between gap-4">
            <div className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full" style={{ backgroundColor: entry.color }} />
              <span className="text-matte-400 capitalize">{entry.name}:</span>
            </div>
            <span className="font-semibold text-matte-100">{formatDuration(entry.value)}</span>
          </div>
        ))}
      </div>
    );
  }
  return null;
};

export function ResponseTimeChart({ points = [] }) {
  if (!points || points.length === 0) {
    return (
      <div className="h-64 flex items-center justify-center text-matte-500 text-xs">
        No latency data recorded
      </div>
    );
  }

  return (
    <div className="w-full h-64">
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={points} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
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
          <YAxis
            stroke="#525260"
            tick={{ fill: '#717180', fontSize: 10 }}
            tickFormatter={(val) => `${val}ms`}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            verticalAlign="top"
            align="right"
            wrapperStyle={{ paddingBottom: '10px', fontSize: '11px', color: '#9e9ea9' }}
          />
          <Line
            type="monotone"
            dataKey="avg_ms"
            name="Avg Latency"
            stroke="#6ee7b7"
            strokeWidth={1.5}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="p95_ms"
            name="p95 Latency"
            stroke="#fbbf24"
            strokeWidth={1.5}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="max_ms"
            name="Max Latency"
            stroke="#f87171"
            strokeWidth={1.5}
            strokeDasharray="4 2"
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}

export default ResponseTimeChart;
