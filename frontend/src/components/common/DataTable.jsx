import React from 'react';

export function DataTable({ columns, data, keyField = 'id', onRowClick = null }) {
  return (
    <div className="w-full overflow-x-auto rounded-lg border border-matte-800">
      <table className="w-full text-left border-collapse text-xs">
        <thead className="bg-matte-900/80 border-b border-matte-800 text-matte-400 font-medium">
          <tr>
            {columns.map((col, idx) => (
              <th
                key={col.key || idx}
                scope="col"
                className={`py-3 px-4 ${col.className || ''}`}
              >
                {col.header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="divide-y divide-matte-800/60 bg-matte-950/40">
          {data.map((row, rowIdx) => {
            const key = row[keyField] !== undefined ? row[keyField] : rowIdx;
            return (
              <tr
                key={key}
                onClick={() => onRowClick && onRowClick(row)}
                className={`transition-colors ${
                  onRowClick ? 'cursor-pointer hover:bg-matte-800/40' : 'hover:bg-matte-800/20'
                }`}
              >
                {columns.map((col, colIdx) => (
                  <td
                    key={col.key || colIdx}
                    className={`py-3 px-4 ${col.cellClassName || ''}`}
                  >
                    {col.render ? col.render(row, rowIdx) : row[col.key]}
                  </td>
                ))}
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

export default DataTable;
