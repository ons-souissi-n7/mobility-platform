"use client";

import { useMemo, useState, type ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render: (item: T) => ReactNode;
  align?: "left" | "right";
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  data: T[];
  emptyLabel: string;
  getRowKey: (item: T) => string | number;
  maxHeight?: string;
  pageSize?: number;
};

export function DataTable<T>({
  columns,
  data,
  emptyLabel,
  getRowKey,
  maxHeight = "28rem",
  pageSize,
}: DataTableProps<T>) {
  const [page, setPage] = useState(1);
  const totalPages = pageSize ? Math.max(1, Math.ceil(data.length / pageSize)) : 1;
  const currentPage = Math.min(page, totalPages);

  const visibleData = useMemo(() => {
    if (!pageSize) {
      return data;
    }

    const start = (currentPage - 1) * pageSize;
    return data.slice(start, start + pageSize);
  }, [currentPage, data, pageSize]);

  const firstItem = data.length === 0 ? 0 : (currentPage - 1) * (pageSize ?? data.length) + 1;
  const lastItem = pageSize
    ? Math.min(currentPage * pageSize, data.length)
    : data.length;

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className="overflow-auto" style={{ maxHeight }}>
        <table className="w-full text-left text-sm">
          <thead className="sticky top-0 z-10 border-b border-gray-200 bg-gray-50 text-xs uppercase text-gray-500">
            <tr>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className={`px-6 py-4 font-medium ${
                    column.align === "right" ? "text-right" : "text-left"
                  }`}
                >
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {data.length === 0 ? (
              <tr>
                <td
                  className="px-6 py-8 text-center text-gray-500"
                  colSpan={columns.length}
                >
                  {emptyLabel}
                </td>
              </tr>
            ) : (
              visibleData.map((item) => (
                <tr key={getRowKey(item)} className="hover:bg-gray-50">
                  {columns.map((column) => (
                    <td
                      key={column.key}
                      className={`px-6 py-4 ${
                        column.align === "right" ? "text-right" : "text-left"
                      }`}
                    >
                      {column.render(item)}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {pageSize && data.length > pageSize ? (
        <div className="flex flex-col gap-3 border-t border-gray-200 px-4 py-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-gray-500">
            Affichage {firstItem}-{lastItem} sur {data.length}
          </p>
          <div className="flex items-center gap-2">
            <button
              className="inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={currentPage === 1}
              onClick={() => setPage((value) => Math.max(1, value - 1))}
              type="button"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              Precedent
            </button>
            <span className="min-w-20 text-center text-sm font-medium text-gray-700">
              {currentPage} / {totalPages}
            </span>
            <button
              className="inline-flex items-center gap-1 rounded-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={currentPage === totalPages}
              onClick={() => setPage((value) => Math.min(totalPages, value + 1))}
              type="button"
            >
              Suivant
              <ChevronRight className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        </div>
      ) : null}
    </div>
  );
}
