import { PageTabBar } from "@/components/ui/page-tab-bar";

type ReferenceTabsProps = {
  countriesCount: number;
  departmentsCount: number;
  levelsCount: number;
  universitiesCount: number;
  parcoursCount: number;
};

export function ReferenceTabs({
  departmentsCount,
  levelsCount,
  universitiesCount,
  countriesCount,
  parcoursCount,
}: ReferenceTabsProps) {
  return (
    <PageTabBar
      tabs={[
        { label: "Départements", value: departmentsCount, href: "#departements" },
        { label: "Parcours", value: parcoursCount, href: "#parcours" },
        { label: "Niveaux", value: levelsCount, href: "#niveaux" },
        { label: "Universités", value: universitiesCount, href: "#universites" },
        { label: "Pays", value: countriesCount, href: "#pays" },
      ]}
    />
  );
}
