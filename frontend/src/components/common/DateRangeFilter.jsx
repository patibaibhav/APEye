import React, { useState } from 'react';
import { Calendar, Clock } from 'lucide-react';

export function DateRangeFilter({ from: _from, to: _to, onChange }) {
  const [isCustomOpen, setIsCustomOpen] = useState(false);
  const [customFrom, setCustomFrom] = useState('');
  const [customTo, setCustomTo] = useState('');

  const setPresetHours = (hours) => {
    const end = new Date();
    const start = new Date(end.getTime() - hours * 60 * 60 * 1000);
    onChange({
      from: start.toISOString(),
      to: end.toISOString(),
    });
    setIsCustomOpen(false);
  };

  const handleApplyCustom = (e) => {
    e.preventDefault();
    if (!customFrom || !customTo) return;

    try {
      const fromDate = new Date(customFrom);
      const toDate = new Date(customTo);

      if (fromDate >= toDate) {
        alert('"From" time must be strictly before "To" time');
        return;
      }

      onChange({
        from: fromDate.toISOString(),
        to: toDate.toISOString(),
      });
      setIsCustomOpen(false);
    } catch {
      alert('Invalid date format');
    }
  };

  return (
    <div className="relative inline-flex flex-wrap items-center gap-1.5 p-1 rounded-lg bg-matte-900 border border-matte-800 text-xs">
      <div className="flex items-center px-2 text-matte-500">
        <Clock className="w-3.5 h-3.5 mr-1" />
        <span className="font-medium">Time:</span>
      </div>

      <button
        type="button"
        onClick={() => setPresetHours(1)}
        className="px-2 py-1 rounded text-matte-300 hover:text-matte-100 hover:bg-matte-800 transition"
      >
        1h
      </button>
      <button
        type="button"
        onClick={() => setPresetHours(6)}
        className="px-2 py-1 rounded text-matte-300 hover:text-matte-100 hover:bg-matte-800 transition"
      >
        6h
      </button>
      <button
        type="button"
        onClick={() => setPresetHours(24)}
        className="px-2 py-1 rounded text-matte-300 hover:text-matte-100 hover:bg-matte-800 transition"
      >
        24h
      </button>
      <button
        type="button"
        onClick={() => setPresetHours(24 * 7)}
        className="px-2 py-1 rounded text-matte-300 hover:text-matte-100 hover:bg-matte-800 transition"
      >
        7d
      </button>

      <button
        type="button"
        onClick={() => setIsCustomOpen(!isCustomOpen)}
        className={`px-2 py-1 rounded flex items-center gap-1 transition ${
          isCustomOpen ? 'bg-matte-700 text-pastel-lavender' : 'text-matte-300 hover:bg-matte-800'
        }`}
      >
        <Calendar className="w-3 h-3" />
        <span>Custom</span>
      </button>

      {isCustomOpen && (
        <div className="absolute top-full left-0 mt-2 z-50 p-4 rounded-lg bg-matte-900 border border-matte-700 shadow-xl w-72">
          <form onSubmit={handleApplyCustom} className="space-y-3">
            <div>
              <label className="block text-[11px] font-medium text-matte-400 mb-1">From (UTC / Local):</label>
              <input
                type="datetime-local"
                value={customFrom}
                onChange={(e) => setCustomFrom(e.target.value)}
                required
                className="w-full bg-matte-950 border border-matte-800 text-matte-200 rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-matte-600"
              />
            </div>
            <div>
              <label className="block text-[11px] font-medium text-matte-400 mb-1">To (UTC / Local):</label>
              <input
                type="datetime-local"
                value={customTo}
                onChange={(e) => setCustomTo(e.target.value)}
                required
                className="w-full bg-matte-950 border border-matte-800 text-matte-200 rounded px-2.5 py-1.5 text-xs focus:outline-none focus:border-matte-600"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2 border-t border-matte-800">
              <button
                type="button"
                onClick={() => setIsCustomOpen(false)}
                className="px-2 py-1 rounded bg-matte-800 text-matte-300 text-xs hover:bg-matte-700"
              >
                Cancel
              </button>
              <button
                type="submit"
                className="px-3 py-1 rounded bg-pastel-lavender text-matte-950 text-xs font-medium hover:bg-pastel-lavender-light"
              >
                Apply
              </button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
}

export default DateRangeFilter;
