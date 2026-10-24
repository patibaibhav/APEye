import React from 'react';
import { Filter, X } from 'lucide-react';
import { HTTP_METHODS, STATUS_CLASSES } from '../../utils/constants';
import DateRangeFilter from '../common/DateRangeFilter';

export function LogFilters({ filters, onChange, onReset }) {
  const updateField = (field, val) => {
    onChange({ ...filters, [field]: val, page: 1 });
  };

  const handleDateChange = ({ from, to }) => {
    onChange({ ...filters, from, to, page: 1 });
  };

  const hasActiveFilters = Boolean(
    filters.source_ip ||
    filters.endpoint ||
    filters.method ||
    filters.status_class ||
    filters.status_code
  );

  return (
    <div className="matte-card p-4 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-matte-300">
          <Filter className="w-3.5 h-3.5 text-pastel-lavender" />
          <span>Filter Request Logs</span>
        </div>

        <div className="flex items-center gap-2">
          <DateRangeFilter
            from={filters.from}
            to={filters.to}
            onChange={handleDateChange}
          />
          {hasActiveFilters && (
            <button
              type="button"
              onClick={onReset}
              className="btn-secondary text-xs py-1 px-2.5 flex items-center gap-1 text-matte-400 hover:text-matte-100"
            >
              <X className="w-3 h-3" />
              <span>Clear Filters</span>
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 pt-1">
        {/* Source IP */}
        <div>
          <label className="block text-[11px] font-medium text-matte-400 mb-1">Source IP</label>
          <input
            type="text"
            placeholder="e.g. 203.0.113.10"
            value={filters.source_ip || ''}
            onChange={(e) => updateField('source_ip', e.target.value)}
            className="input-matte w-full text-xs"
          />
        </div>

        {/* Endpoint prefix */}
        <div>
          <label className="block text-[11px] font-medium text-matte-400 mb-1">Endpoint Path Prefix</label>
          <input
            type="text"
            placeholder="e.g. /api/auth"
            value={filters.endpoint || ''}
            onChange={(e) => updateField('endpoint', e.target.value)}
            className="input-matte w-full text-xs"
          />
        </div>

        {/* Method */}
        <div>
          <label className="block text-[11px] font-medium text-matte-400 mb-1">HTTP Method</label>
          <select
            value={filters.method || ''}
            onChange={(e) => updateField('method', e.target.value)}
            className="input-matte w-full text-xs"
          >
            <option value="">All Methods</option>
            {HTTP_METHODS.map((m) => (
              <option key={m} value={m}>{m}</option>
            ))}
          </select>
        </div>

        {/* Status Class */}
        <div>
          <label className="block text-[11px] font-medium text-matte-400 mb-1">Status Class</label>
          <select
            value={filters.status_class || ''}
            onChange={(e) => updateField('status_class', e.target.value)}
            className="input-matte w-full text-xs"
          >
            <option value="">All Classes</option>
            {STATUS_CLASSES.map((cls) => (
              <option key={cls} value={cls}>{cls}</option>
            ))}
          </select>
        </div>

        {/* Exact Status Code */}
        <div>
          <label className="block text-[11px] font-medium text-matte-400 mb-1">Status Code</label>
          <input
            type="number"
            placeholder="e.g. 401"
            value={filters.status_code || ''}
            onChange={(e) => updateField('status_code', e.target.value)}
            className="input-matte w-full text-xs"
          />
        </div>
      </div>
    </div>
  );
}

export default LogFilters;
