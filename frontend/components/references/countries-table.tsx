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

function getColumns(
  onEdit: (country: Country) => void,
  onDelete: (country: Country) => void,
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
          onDelete={() => onDelete(country)}
          onEdit={() => onEdit(country)}
        />
      ),
    },
  ];
}

type CountriesTableProps = {
  countries: Country[];
  onDelete: (country: Country) => void;
  onEdit: (country: Country) => void;
};

export function CountriesTable({
  countries,
  onDelete,
  onEdit,
}: CountriesTableProps) {
  return (
    <DataTable
      columns={getColumns(onEdit, onDelete)}
      data={countries}
      emptyLabel="Aucun pays reference"
      getRowKey={(country) => country.id}
      maxHeight="32rem"
      pageSize={5}
    />
  );
}
