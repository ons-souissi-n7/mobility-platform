"use client";

import { Loader2 } from "lucide-react";

import { nextTransitions, statusLabels, statusTone } from "@/components/academic-years/status";
import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { AcademicYearTransition } from "@/lib/api/academic-year-mutations";
import type { AcademicYear } from "@/lib/api/types";
import { formatDate } from "@/lib/utils";

type AcademicYearsTableProps = {
  years: AcademicYear[];
  onDelete: (year: AcademicYear) => void;
  onEdit: (year: AcademicYear) => void;
  onTransition: (year: AcademicYear, transition: AcademicYearTransition) => void;
};

function getColumns({
  onDelete,
  onEdit,
  onTransition,
}: Omit<AcademicYearsTableProps, "years">): DataTableColumn<AcademicYear>[] {
  return [
    {
      key: "label",
      header: "Année",
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
      render: (year) =>
        year.status === "pre_assignment" ? (
          <span className="inline-flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium bg-purple-100 text-purple-800">
            <Loader2 className="h-3 w-3 animate-spin" />
            {statusLabels[year.status]}
          </span>
        ) : (
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
      key: "transition",
      header: "Transition",
      render: (year) => {
        const next = nextTransitions[year.status];

        if (year.status === "pre_assignment") {
          return (
            <span className="inline-flex items-center gap-1.5 text-sm text-purple-600">
              <Loader2 className="h-3.5 w-3.5 animate-spin" />
              Calcul en cours…
            </span>
          );
        }

        if (!next) {
          return <span className="text-sm text-gray-400">—</span>;
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
      render: (year) => {
        const canEdit = year.status === "initialization" || year.status === "recommendation";
        const canDelete = year.status === "initialization";
        return (
          <ActionButtons
            onEdit={() => onEdit(year)}
            editDisabled={!canEdit}
            editDisabledTitle="Modification non autorisée — seules les années en phase Initialisation, Recommandation ou Candidature peuvent être modifiées"
            onDelete={() => onDelete(year)}
            deleteDisabled={!canDelete}
            deleteDisabledTitle="Suppression non autorisée — seules les années en phase Initialisation peuvent être supprimées"
          />
        );
      },
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
    />
  );
}
