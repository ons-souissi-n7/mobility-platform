import type { ReactNode } from "react";
import { SearchInput } from "@/components/ui/search-input";

/**
 * Barre d'outils standard :
 *   Ligne 1 — boutons d'action (actions)
 *   Ligne 2 — recherche + filtres (search + filters) dans la même rangée
 */
export function Toolbar({
  search,
  actions,
  filters,
  searchClassName,
}: {
  search?: { value: string; onChange: (v: string) => void; placeholder?: string };
  actions?: ReactNode;
  filters?: ReactNode;
  searchClassName?: string;
}) {
  const hasBottomRow = search || filters;
  return (
    <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm space-y-3">
      {actions && (
        <div className="flex items-center gap-2 flex-wrap">
          {actions}
        </div>
      )}
      {hasBottomRow && (
        <div className={`flex items-center gap-2 overflow-x-auto${actions ? " pt-1 border-t border-gray-100" : ""}`}>
          {search && (
            <SearchInput
              value={search.value}
              onChange={search.onChange}
              placeholder={search.placeholder ?? ""}
              className={searchClassName ?? "w-56 shrink-0"}
            />
          )}
          {filters}
        </div>
      )}
    </div>
  );
}
