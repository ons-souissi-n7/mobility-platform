"use client";

import type { ReactNode } from "react";
import { ChevronLeft, ChevronRight } from "lucide-react";

export function Pagination({
  page,
  totalPages,
  totalItems,
  pageSize,
  pageSizeOptions = [10, 25, 50, 100],
  onPageChange,
  onPageSizeChange,
  emptyLabel = "Aucun élément",
}: {
  page: number;
  totalPages: number;
  totalItems: number;
  pageSize: number;
  pageSizeOptions?: number[];
  onPageChange: (page: number) => void;
  onPageSizeChange?: (size: number) => void;
  emptyLabel?: string;
}) {
  const firstItem = totalItems === 0 ? 0 : (page - 1) * pageSize + 1;
  const lastItem = Math.min(page * pageSize, totalItems);

  return (
    <div className="flex items-center justify-between border-t border-gray-200 px-4 py-3">
      <p className="text-sm text-gray-500">
        {totalItems === 0
          ? emptyLabel
          : `${firstItem}–${lastItem} sur ${totalItems}`}
      </p>
      <div className="flex items-center gap-3">
        {onPageSizeChange && (
          <select
            className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#1E3A8A]"
            value={pageSize}
            onChange={(e) => { onPageSizeChange(Number(e.target.value)); onPageChange(1); }}
          >
            {pageSizeOptions.map((s) => (
              <option key={s} value={s}>{s} / page</option>
            ))}
          </select>
        )}
        <div className="flex items-center gap-1">
          <PagBtn disabled={page === 1} onClick={() => onPageChange(1)} title="Première page">
            <ChevronLeft className="h-3.5 w-3.5" />
            <ChevronLeft className="-ml-2 h-3.5 w-3.5" />
          </PagBtn>
          <PagBtn disabled={page === 1} onClick={() => onPageChange(page - 1)} title="Page précédente">
            <ChevronLeft className="h-3.5 w-3.5" />
          </PagBtn>

          {buildPageNumbers(page, totalPages).map((p, i) =>
            p === "..." ? (
              <span key={`e${i}`} className="px-1 text-xs text-gray-400">…</span>
            ) : (
              <button
                key={p}
                className={`min-w-[2rem] rounded-md border px-2 py-1 text-xs font-medium ${
                  p === page
                    ? "border-[#1E3A8A] bg-[#1E3A8A] text-white"
                    : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
                }`}
                onClick={() => onPageChange(p as number)}
                type="button"
              >
                {p}
              </button>
            ),
          )}

          <PagBtn disabled={page === totalPages} onClick={() => onPageChange(page + 1)} title="Page suivante">
            <ChevronRight className="h-3.5 w-3.5" />
          </PagBtn>
          <PagBtn disabled={page === totalPages} onClick={() => onPageChange(totalPages)} title="Dernière page">
            <ChevronRight className="h-3.5 w-3.5" />
            <ChevronRight className="-ml-2 h-3.5 w-3.5" />
          </PagBtn>
        </div>
      </div>
    </div>
  );
}

function PagBtn({
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

export function buildPageNumbers(current: number, total: number): (number | "...")[] {
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
