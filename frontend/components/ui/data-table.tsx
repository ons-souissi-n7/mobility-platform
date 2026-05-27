"use client";

import { useEffect, useMemo, useState, type ReactNode } from "react";
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

  useEffect(() => { setPage(1); }, [data]);
  useEffect(() => { setPage(1); }, [pageSize]);

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
      <div className={pageSize ? "overflow-hidden" : "overflow-auto"} style={pageSize ? undefined : { maxHeight }}>
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

      <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3">
        <p className="text-sm text-gray-500">
          {data.length === 0
            ? "Aucun element"
            : pageSize
            ? `${firstItem}–${lastItem} sur ${data.length}`
            : `${data.length} element${data.length > 1 ? "s" : ""}`}
        </p>
        {pageSize ? (
          <div className="flex items-center gap-3">
            <select
              className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#1E3A8A]"
              onChange={(e) => setPageSize(Number(e.target.value))}
              value={pageSize}
            >
              {pageSizeOptions.map((size) => (
                <option key={size} value={size}>{size} / page</option>
              ))}
            </select>
            <div className="flex items-center gap-1">
              <PaginationBtn
                disabled={currentPage === 1}
                onClick={() => setPage(1)}
                title="Premiere page"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
                <ChevronLeft className="-ml-2 h-3.5 w-3.5" />
              </PaginationBtn>
              <PaginationBtn
                disabled={currentPage === 1}
                onClick={() => setPage((p) => p - 1)}
                title="Page precedente"
              >
                <ChevronLeft className="h-3.5 w-3.5" />
              </PaginationBtn>

              {buildPageNumbers(currentPage, totalPages).map((p, i) =>
                p === "..." ? (
                  <span key={`e${i}`} className="px-1 text-xs text-gray-400">…</span>
                ) : (
                  <button
                    key={p}
                    className={`min-w-[2rem] rounded-md border px-2 py-1 text-xs font-medium ${
                      p === currentPage
                        ? "border-[#1E3A8A] bg-[#1E3A8A] text-white"
                        : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
                    }`}
                    onClick={() => setPage(p as number)}
                    type="button"
                  >
                    {p}
                  </button>
                ),
              )}

              <PaginationBtn
                disabled={currentPage === totalPages}
                onClick={() => setPage((p) => p + 1)}
                title="Page suivante"
              >
                <ChevronRight className="h-3.5 w-3.5" />
              </PaginationBtn>
              <PaginationBtn
                disabled={currentPage === totalPages}
                onClick={() => setPage(totalPages)}
                title="Derniere page"
              >
                <ChevronRight className="h-3.5 w-3.5" />
                <ChevronRight className="-ml-2 h-3.5 w-3.5" />
              </PaginationBtn>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}

function PaginationBtn({
  children,
  disabled,
  onClick,
  title,
}: {
  children: ReactNode;
  disabled: boolean;
  onClick: () => void;
  title: string;
}) {
  return (
    <button
      className="flex items-center rounded-md border border-gray-200 bg-white px-1.5 py-1 text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
      disabled={disabled}
      onClick={onClick}
      title={title}
      type="button"
    >
      {children}
    </button>
  );
}

function buildPageNumbers(current: number, total: number): (number | "...")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1);
  const pages: (number | "...")[] = [];
  const add = (p: number) => { if (!pages.includes(p)) pages.push(p); };
  add(1);
  if (current > 4) pages.push("...");
  for (let p = Math.max(2, current - 2); p <= Math.min(total - 1, current + 2); p++) add(p);
  if (current < total - 3) pages.push("...");
  add(total);
  return pages;
}
