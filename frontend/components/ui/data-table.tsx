"use client";

import { useMemo, useState, type ReactNode } from "react";

import { Pagination } from "@/components/ui/pagination";

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
  pageSize: initialPageSize,
}: DataTableProps<T>) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const pageSizeOptions = useMemo(() => {
    const defaults = [5, 10, 15, 20];
    if (initialPageSize !== undefined && !defaults.includes(initialPageSize)) {
      return [...defaults, initialPageSize].sort((a, b) => a - b);
    }
    return defaults;
  }, [initialPageSize]);
  const totalPages = pageSize ? Math.max(1, Math.ceil(data.length / pageSize)) : 1;
  const currentPage = Math.min(page, totalPages);

  const [prevData, setPrevData] = useState(data);
  if (prevData !== data) {
    setPrevData(data);
    setPage(1);
  }

  const [prevPageSize, setPrevPageSize] = useState(pageSize);
  if (prevPageSize !== pageSize) {
    setPrevPageSize(pageSize);
    setPage(1);
  }

  const visibleData = useMemo(() => {
    if (!pageSize) {
      return data;
    }

    const start = (currentPage - 1) * pageSize;
    return data.slice(start, start + pageSize);
  }, [currentPage, data, pageSize]);

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className={pageSize ? "overflow-x-auto" : "overflow-auto"} style={pageSize ? undefined : { maxHeight }}>
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

      {pageSize ? (
        <Pagination
          page={currentPage}
          totalPages={totalPages}
          totalItems={data.length}
          pageSize={pageSize}
          pageSizeOptions={pageSizeOptions}
          onPageChange={setPage}
          onPageSizeChange={setPageSize}
          emptyLabel="Aucun élément"
        />
      ) : (
        <div className="border-t border-gray-200 px-4 py-3">
          <p className="text-sm text-gray-500">
            {data.length === 0
              ? "Aucun élément"
              : `${data.length} élément${data.length > 1 ? "s" : ""}`}
          </p>
        </div>
      )}
    </div>
  );
}
