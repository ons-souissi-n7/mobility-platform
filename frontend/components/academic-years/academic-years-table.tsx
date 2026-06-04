"use client";

import { Pencil, Trash2 } from "lucide-react";

import { nextTransitions, statusLabels, statusTone } from "@/components/academic-years/status";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { AcademicYearTransition } from "@/lib/api/academic-year-mutations";
import type { AcademicYear } from "@/lib/api/types";

type AcademicYearsTableProps = {
  years: AcademicYear[];
  onDelete: (year: AcademicYear) => void;
  onEdit: (year: AcademicYear) => void;
  onTransition: (year: AcademicYear, transition: AcademicYearTransition) => void;
};

function formatDate(value: string | null) {
  if (!value) {
    return "-";
  }

  return new Intl.DateTimeFormat("fr-FR").format(new Date(value));
}

function getColumns({
  onDelete,
  onEdit,
  onTransition,
}: Omit<AcademicYearsTableProps, "years">): DataTableColumn<AcademicYear>[] {
  return [
    {
      key: "label",
      header: "Annee",
      render: (year) => <span className="font-medium text-gray-900">{year.label}</span>,
    },
    {
      key: "period",
      header: "Periode",
      render: (year) => `${formatDate(year.start_date)} - ${formatDate(year.end_date)}`,
    },
    {
      key: "status",
      header: "Statut",
      render: (year) => (
        <span
          className={`inline-flex rounded-full px-2.5 py-0.5 text-xs font-medium ${statusTone[year.status]}`}
        >
          {statusLabels[year.status]}
        </span>
      ),
    },
    {
      key: "wishes",
      header: "Voeux",
      render: (year) =>
        `${formatDate(year.wishes_open_date)} - ${formatDate(year.wishes_close_date)}`,
    },
    {
      key: "milestones",
      header: "Jalons",
      render: (year) => (
        <div className="text-xs text-gray-600">
          <p>Gel GPA: {formatDate(year.gpa_freeze_date)}</p>
          <p>Resultats: {formatDate(year.results_publication_date)}</p>
        </div>
      ),
    },
    {
      key: "transition",
      header: "Transition",
      render: (year) => {
        const next = nextTransitions[year.status];

        if (!next) {
          return <span className="text-sm text-gray-400">Aucune</span>;
        }

        return (
          <button
            className="rounded-md bg-[#1E3A8A] px-3 py-2 text-xs font-medium text-white hover:bg-blue-900"
            onClick={() => onTransition(year, next.transition)}
            type="button"
          >
            {next.label}
          </button>
        );
      },
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (year) => (
        <div className="flex items-center justify-end gap-2">
          <button
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-blue-50 hover:text-[#1E3A8A]"
            onClick={() => onEdit(year)}
            type="button"
          >
            <Pencil className="h-4 w-4" aria-hidden="true" />
            Modifier
          </button>
          <button
            className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 hover:bg-red-50 hover:text-red-700"
            onClick={() => onDelete(year)}
            type="button"
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
            Supprimer
          </button>
        </div>
      ),
    },
  ];
}

export function AcademicYearsTable({
  years,
  onDelete,
  onEdit,
  onTransition,
}: AcademicYearsTableProps) {
  return (
    <DataTable
      columns={getColumns({ onDelete, onEdit, onTransition })}
      data={years}
      emptyLabel="Aucune annee universitaire configuree"
      getRowKey={(year) => year.id}
      maxHeight="32rem"
      pageSize={5}
    />
  );
}
