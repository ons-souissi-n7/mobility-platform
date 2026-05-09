import { ExternalLink } from "lucide-react";

import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { Country, PartnerUniversity } from "@/lib/api/types";

type UniversityRow = PartnerUniversity & {
  countryIso2: string;
};

function getColumns(
  onEdit: (university: PartnerUniversity) => void,
  onDelete: (university: PartnerUniversity) => void,
): DataTableColumn<UniversityRow>[] {
  return [
    {
      key: "name",
      header: "Universite",
      render: (university) => (
        <div className="min-w-64">
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
      render: (university) => university.countryIso2,
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
          onDelete={() => onDelete(university)}
          onEdit={() => onEdit(university)}
        />
      ),
    },
  ];
}

type UniversitiesTableProps = {
  countries: Country[];
  onDelete: (university: PartnerUniversity) => void;
  onEdit: (university: PartnerUniversity) => void;
  universities: PartnerUniversity[];
};

export function UniversitiesTable({
  countries,
  onDelete,
  onEdit,
  universities,
}: UniversitiesTableProps) {
  const countriesById = new Map(countries.map((country) => [country.id, country]));
  const rows = universities.map((university) => ({
    ...university,
    countryIso2: countriesById.get(university.country_id)?.iso2 ?? "-",
  }));

  return (
    <DataTable
      columns={getColumns(onEdit, onDelete)}
      data={rows}
      emptyLabel="Aucune universite partenaire referencee"
      getRowKey={(university) => university.id}
      maxHeight="36rem"
      pageSize={20}
    />
  );
}
