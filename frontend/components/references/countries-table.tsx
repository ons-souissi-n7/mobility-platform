import { ActionButtons } from "@/components/ui/action-buttons";
import { DataTable, type DataTableColumn } from "@/components/ui/data-table";
import type { Country } from "@/lib/api/types";

const regionLabels: Record<string, string> = {
  france: "France",
  europe_hors_france: "Europe hors France",
  canada_usa: "Canada / Etats-Unis",
  amerique: "Amerique",
  asie_moyen_orient: "Asie / Moyen-Orient",
  afrique: "Afrique",
  oceanie: "Oceanie",
};

const LOCKED_TITLE = "Modifications disponibles en phase Initialisation uniquement";

function getColumns(
  onEdit: (country: Country) => void,
  onDelete: (country: Country) => void,
  readOnly: boolean,
): DataTableColumn<Country>[] {
  return [
    {
      key: "iso2",
      header: "Code",
      render: (country) => (
        <span className="font-medium text-gray-900">{country.iso2}</span>
      ),
    },
    {
      key: "name_fr",
      header: "Nom francais",
      render: (country) => country.name_fr,
    },
    {
      key: "name_en",
      header: "Nom anglais",
      render: (country) => country.name_en,
    },
    {
      key: "cti_region",
      header: "Region CTI",
      render: (country) => (
        <span className="inline-flex rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-800">
          {regionLabels[country.cti_region] ?? country.cti_region}
        </span>
      ),
    },
    {
      key: "actions",
      header: "Actions",
      align: "right",
      render: (country) => (
        <ActionButtons
          onEdit={() => onEdit(country)}
          editDisabled={readOnly}
          editDisabledTitle={LOCKED_TITLE}
          onDelete={() => onDelete(country)}
          deleteDisabled={readOnly}
          deleteDisabledTitle={LOCKED_TITLE}
        />
      ),
    },
  ];
}

type CountriesTableProps = {
  countries: Country[];
  readOnly?: boolean;
  onDelete: (country: Country) => void;
  onEdit: (country: Country) => void;
};

export function CountriesTable({
  countries,
  readOnly = false,
  onDelete,
  onEdit,
}: CountriesTableProps) {
  return (
    <DataTable
      columns={getColumns(onEdit, onDelete, readOnly)}
      data={countries}
      emptyLabel="Aucun pays reference"
      getRowKey={(country) => country.id}
      maxHeight="32rem"
    />
  );
}
