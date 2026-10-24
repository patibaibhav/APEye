import React from 'react';
import { Filter, X } from 'lucide-react';
import { ThreatCategory, ThreatCategoryLabels, Severity, AlertStatus } from '../../utils/constants';
import DateRangeFilter from '../common/DateRangeFilter';

export function AlertFilters({ filters, onChange, onReset }) {
  const updateField = (field, val) => {
    onChange({ ...filters, [field]: val, page: 1 });
  };

  const handleDateChange = ({ from, to }) => {
    onChange({ ...filters, from, to, page: 1 });
  };

  const hasActiveFilters = Boolean(
    filters.severity ||
    filters.category ||
    filters.status ||
    filters.source_ip
  );

  return (
    <div className="matte-card p-4 space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-matte-300">
          <Filter className="w-3.5 h-3.5 text-pastel-lavender" />
          <span>Filter Alerts</span>
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
              <span>Clear</span>
            </button>
          )}
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-3 pt-1">
        {/* Severity */}
        <div>
          <label className="block text-[11px] font-medium text-matte-400 mb-1">Severity</label>
          <select
            value={filters.severity || ''}
            onChange={(e) => updateField('severity', e.target.value)}
            className="input-matte w-full text-xs"
          >
            <option value="">All Severities</option>
            {Object.values(Severity).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

        {/* Category */}
        <div>
          <label className="block text-[11px] font-medium text-matte-400 mb-1">Threat Category</label>
          <select
            value={filters.category || ''}
            onChange={(e) => updateField('category', e.target.value)}
            className="input-matte w-full text-xs"
          >
            <option value="">All Categories</option>
            {Object.entries(ThreatCategory).map(([k, val]) => (
              <option key={k} value={val}>{ThreatCategoryLabels[val] || val}</option>
            ))}
          </select>
        </div>

        {/* Status */}
        <div>
          <label className="block text-[11px] font-medium text-matte-400 mb-1">Status</label>
          <select
            value={filters.status || ''}
            onChange={(e) => updateField('status', e.target.value)}
            className="input-matte w-full text-xs"
          >
            <option value="">All Statuses</option>
            {Object.values(AlertStatus).map((s) => (
              <option key={s} value={s}>{s}</option>
            ))}
          </select>
        </div>

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
      </div>
    </div>
  );
}

export default AlertFilters;
