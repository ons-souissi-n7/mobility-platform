"use client";

import { useMemo, useState, type ReactNode } from "react";

import { Pagination } from "@/components/ui/pagination";
import { DEFAULT_PAGE_SIZE } from "@/lib/config";

export type DataTableColumn<T> = {
  key: string;
  header: string;
  render: (item: T) => ReactNode;
  align?: "left" | "right";
};

export type ServerSidePagination = {
  totalItems: number;
  page: number;
  pageSize: number;
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
};

type DataTableProps<T> = {
  columns: DataTableColumn<T>[];
  data: T[];
  emptyLabel: string;
  getRowKey: (item: T) => string | number;
  maxHeight?: string;
  pageSize?: number;
  serverSidePagination?: ServerSidePagination;
};

export function DataTable<T>({
  columns,
  data,
  emptyLabel,
  getRowKey,
  maxHeight = "28rem",
  pageSize: initialPageSize = DEFAULT_PAGE_SIZE,
  serverSidePagination,
}: DataTableProps<T>) {
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(initialPageSize);
  const pageSizeOptions = useMemo(() => {
    const defaults = [10, 25, 50, 100];
    if (initialPageSize !== undefined && !defaults.includes(initialPageSize)) {
      return [...defaults, initialPageSize].sort((a, b) => a - b);
    }
    return defaults;
  }, [initialPageSize]);

  const isServerSide = serverSidePagination !== undefined;

  const effectivePage = isServerSide ? serverSidePagination.page : Math.min(page, Math.max(1, Math.ceil(data.length / pageSize)));
  const effectivePageSize = isServerSide ? serverSidePagination.pageSize : pageSize;
  const effectiveTotalItems = isServerSide ? serverSidePagination.totalItems : data.length;
  const totalPages = effectivePageSize ? Math.max(1, Math.ceil(effectiveTotalItems / effectivePageSize)) : 1;

  const [prevData, setPrevData] = useState(data);
  if (!isServerSide && prevData !== data) {
    setPrevData(data);
    setPage(1);
  }

  const [prevPageSize, setPrevPageSize] = useState(pageSize);
  if (!isServerSide && prevPageSize !== pageSize) {
    setPrevPageSize(pageSize);
    setPage(1);
  }

  const visibleData = useMemo(() => {
    if (isServerSide) return data;
    if (!pageSize) return data;
    const start = (effectivePage - 1) * pageSize;
    return data.slice(start, start + pageSize);
  }, [isServerSide, effectivePage, data, pageSize]);

  function handlePageChange(p: number) {
    if (isServerSide) {
      serverSidePagination.onPageChange(p);
    } else {
      setPage(p);
    }
  }

  function handlePageSizeChange(s: number) {
    if (isServerSide) {
      serverSidePagination.onPageSizeChange?.(s);
    } else {
      setPageSize(s);
    }
  }

  return (
    <div className="overflow-hidden rounded-lg border border-gray-200 bg-white shadow-sm">
      <div className={effectivePageSize ? "overflow-x-auto" : "overflow-auto"} style={effectivePageSize ? undefined : { maxHeight }}>
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
            {effectiveTotalItems === 0 ? (
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

      {effectivePageSize ? (
        <Pagination
          page={effectivePage}
          totalPages={totalPages}
          totalItems={effectiveTotalItems}
          pageSize={effectivePageSize}
          pageSizeOptions={isServerSide ? undefined : pageSizeOptions}
          onPageChange={handlePageChange}
          onPageSizeChange={isServerSide ? undefined : handlePageSizeChange}
          emptyLabel="Aucun élément"
        />
      ) : (
        <div className="border-t border-gray-200 px-4 py-3">
          <p className="text-sm text-gray-500">
            {effectiveTotalItems === 0
              ? "Aucun élément"
              : `${effectiveTotalItems} élément${effectiveTotalItems > 1 ? "s" : ""}`}
          </p>
        </div>
      )}
    </div>
  );
}
