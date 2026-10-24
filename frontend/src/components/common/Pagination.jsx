import React from 'react';
import { ChevronLeft, ChevronRight } from 'lucide-react';
import { formatNumber } from '../../utils/formatters';

export function Pagination({
  page = 1,
  pageSize = 25,
  totalItems = 0,
  totalPages = 1,
  onPageChange,
  onPageSizeChange,
}) {
  const startItem = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const endItem = Math.min(page * pageSize, totalItems);

  return (
    <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-3 px-4 border-t border-matte-800 text-xs text-matte-400">
      <div className="flex items-center gap-2">
        <span>
          Showing <span className="font-medium text-matte-200">{formatNumber(startItem)}</span> to{' '}
          <span className="font-medium text-matte-200">{formatNumber(endItem)}</span> of{' '}
          <span className="font-medium text-matte-200">{formatNumber(totalItems)}</span> results
        </span>

        {onPageSizeChange && (
          <div className="flex items-center gap-1.5 ml-4">
            <span>Per page:</span>
            <select
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="bg-matte-800 border border-matte-700 text-matte-200 rounded px-2 py-1 text-xs focus:outline-none focus:border-matte-500"
            >
              <option value={10}>10</option>
              <option value={25}>25</option>
              <option value={50}>50</option>
              <option value={100}>100</option>
            </select>
          </div>
        )}
      </div>

      <div className="flex items-center gap-2">
        <span className="mr-2">
          Page <span className="font-medium text-matte-200">{page}</span> of{' '}
          <span className="font-medium text-matte-200">{Math.max(1, totalPages)}</span>
        </span>
        <button
          type="button"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          className="p-1.5 rounded bg-matte-800 border border-matte-700 text-matte-300 hover:bg-matte-700 disabled:opacity-40 disabled:hover:bg-matte-800 transition"
          aria-label="Previous page"
        >
          <ChevronLeft className="w-4 h-4" />
        </button>
        <button
          type="button"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          className="p-1.5 rounded bg-matte-800 border border-matte-700 text-matte-300 hover:bg-matte-700 disabled:opacity-40 disabled:hover:bg-matte-800 transition"
          aria-label="Next page"
        >
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}

export default Pagination;
