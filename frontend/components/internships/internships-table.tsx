"use client";

import { useRef, useState } from "react";
import { Pencil, Trash2 } from "lucide-react";

import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import { SearchInput } from "@/components/ui/search-input";
import type { Country, Internship } from "@/lib/api/types";

function formatDate(d: string | null): string {
  if (!d) return "—";
  return new Date(d).toLocaleDateString("fr-FR");
}

export function InternshipsTable({
  internships,
  totalCount,
  page,
  pageSize,
  countries,
  readOnly = false,
  showYear = false,
  onPageChange,
  onEdit,
  onDelete,
  onFilterChange,
}: {
  internships: Internship[];
  totalCount: number;
  page: number;
  pageSize: number;
  countries: Country[];
  readOnly?: boolean;
  showYear?: boolean;
  onPageChange: (page: number) => void;
  onEdit: (item: Internship) => void;
  onDelete: (item: Internship) => void;
  onFilterChange: (filters: { search?: string; country_id?: number }) => void;
}) {
  const [search, setSearch] = useState("");
  const [countryFilter, setCountryFilter] = useState<string>("all");
  const searchTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function emitFilters(s: string, c: string) {
    onFilterChange({
      search: s || undefined,
      country_id: c !== "all" ? Number(c) : undefined,
    });
  }

  function handleSearchChange(value: string) {
    setSearch(value);
    if (searchTimer.current) clearTimeout(searchTimer.current);
    searchTimer.current = setTimeout(() => {
      emitFilters(value, countryFilter);
    }, 350);
  }

  function handleCountryChange(value: string) {
    setCountryFilter(value);
    emitFilters(search, value);
  }

  const columns: DataTableColumn<Internship>[] = [
    {
      key: "etudiant",
      header: "Étudiant",
      render: (item) => (
        <div>
          <p className="font-mono text-xs text-gray-500">{item.student_ine}</p>
          <p className="font-medium text-gray-900">
            {item.student_name.replace(/\s*\([^)]*\)$/, "")}
          </p>
        </div>
      ),
    },
    {
      key: "entreprise",
      header: "Entreprise",
      render: (item) => (
        <p className="font-medium text-gray-900">{item.company_name}</p>
      ),
    },
    {
      key: "pays",
      header: "Pays",
      render: (item) => (
        <p className="text-sm text-gray-700">{item.country_name_fr ?? "—"}</p>
      ),
    },
    {
      key: "ville",
      header: "Ville",
      render: (item) => (
        <p className="text-sm text-gray-700">{item.city || "—"}</p>
      ),
    },
    {
      key: "type",
      header: "Type",
      render: (item) => (
        <span className="rounded-full bg-blue-100 px-2 py-0.5 text-xs font-medium text-blue-700">
          {item.internship_type || "—"}
        </span>
      ),
    },
    {
      key: "dates",
      header: "Dates",
      render: (item) => (
        <p className="whitespace-nowrap text-xs text-gray-600">
          {formatDate(item.start_date)} → {formatDate(item.end_date)}
        </p>
      ),
    },
    ...(showYear
      ? [
          {
            key: "annee",
            header: "Année",
            render: (item: Internship) => (
              <p className="whitespace-nowrap text-sm text-gray-600">
                {item.academic_year_label ?? "—"}
              </p>
            ),
          },
        ]
      : []),
    {
      key: "semaines",
      header: "Semaines",
      render: (item) => (
        <p className="text-center text-sm text-gray-700">
          {item.weeks_in_company ?? "—"}
        </p>
      ),
    },
    {
      key: "actions",
      header: "",
      align: "right",
      render: (item) =>
        readOnly ? null : (
          <div className="flex items-center justify-end gap-1">
            <button
              className="rounded-md p-1.5 text-gray-400 hover:bg-gray-100 hover:text-gray-700"
              onClick={() => onEdit(item)}
              title="Modifier"
              type="button"
            >
              <Pencil size={15} />
            </button>
            <button
              className="rounded-md p-1.5 text-gray-400 hover:bg-red-50 hover:text-red-600"
              onClick={() => onDelete(item)}
              title="Supprimer"
              type="button"
            >
              <Trash2 size={15} />
            </button>
          </div>
        ),
    },
  ];

  return (
    <div className="space-y-3">
      {/* Filtres */}
      <div className="flex flex-wrap items-center gap-2">
        <SearchInput
          onChange={handleSearchChange}
          placeholder="Rechercher étudiant ou entreprise…"
          value={search}
        />
        <select
          className="rounded-md border border-gray-200 bg-white px-2 py-1.5 text-xs text-gray-700"
          onChange={(e) => handleCountryChange(e.target.value)}
          value={countryFilter}
        >
          <option value="all">Tous les pays</option>
          {[...countries]
            .sort((a, b) => a.name_fr.localeCompare(b.name_fr))
            .map((c) => (
              <option key={c.id} value={c.id}>
                {c.name_fr}
              </option>
            ))}
        </select>
      </div>

      <DataTable
        columns={columns}
        data={internships}
        emptyLabel="Aucun stage trouvé."
        getRowKey={(item) => item.id}
        serverSidePagination={{
          totalItems: totalCount,
          page,
          pageSize,
          onPageChange,
        }}
      />
    </div>
  );
}
