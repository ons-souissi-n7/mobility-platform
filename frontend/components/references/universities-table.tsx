import { ExternalLink } from "lucide-react";

import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn, type ServerSidePagination } from "@/components/ui/data-table";
import type { PartnerUniversity } from "@/lib/api/types";

type UniversityRow = PartnerUniversity & {
  countryName: string;
};

const LOCKED_TITLE = "Modifications disponibles en phase Initialisation uniquement";

function getColumns(
  onEdit: (university: PartnerUniversity) => void,
  onDelete: (university: PartnerUniversity) => void,
  readOnly: boolean,
): DataTableColumn<UniversityRow>[] {
  return [
    {
      key: "name",
      header: "Université",
      render: (university) => (
        <div className="min-w-0">
          <p className="font-medium text-gray-900">{university.name}</p>
          <p className="mt-1 text-xs text-gray-500">
            {university.short_name ||
              university.translated_name ||
              "Nom court non renseigne"}
          </p>
        </div>
      ),
    },
    {
      key: "country",
      header: "Pays",
      render: (university) => university.countryName,
    },
    {
      key: "city",
      header: "Ville",
      render: (university) => university.city || "-",
    },
    {
      key: "erasmus_code",
      header: "Code Erasmus",
      render: (university) => university.erasmus_code || "-",
    },
    {
      key: "moveon_id",
      header: "MoveON",
      render: (university) => university.moveon_id ?? "-",
    },
    {
      key: "url",
      header: "Site",
      align: "right",
      render: (university) =>
        university.url ? (
          <a
            className="inline-flex items-center justify-end gap-1 text-sm font-medium text-[#1E3A8A] hover:text-blue-900"
            href={university.url}
            rel="noreferrer"
            target="_blank"
          >
            Ouvrir
            <ExternalLink className="h-4 w-4" aria-hidden="true" />
          </a>
        ) : (
          <span className="text-gray-400">-</span>
        ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (university) => (
        <ActionButtons
          onEdit={() => onEdit(university)}
          editDisabled={readOnly}
          editDisabledTitle={LOCKED_TITLE}
          onDelete={() => onDelete(university)}
          deleteDisabled={readOnly}
          deleteDisabledTitle={LOCKED_TITLE}
        />
      ),
    },
  ];
}

type UniversitiesTableProps = {
  onDelete: (university: PartnerUniversity) => void;
  onEdit: (university: PartnerUniversity) => void;
  universities: PartnerUniversity[];
  readOnly?: boolean;
  serverSidePagination?: ServerSidePagination;
};

export function UniversitiesTable({
  onDelete,
  onEdit,
  universities,
  readOnly = false,
  serverSidePagination,
}: Readonly<UniversitiesTableProps>) {
  const rows = universities.map((university) => ({
    ...university,
    countryName: university.country_name_fr || "-",
  }));

  return (
    <DataTable
      columns={getColumns(onEdit, onDelete, readOnly)}
      data={rows}
      emptyLabel="Aucune universite partenaire referencee"
      getRowKey={(university) => university.id}
      maxHeight="36rem"
      serverSidePagination={serverSidePagination}
    />
  );
}
