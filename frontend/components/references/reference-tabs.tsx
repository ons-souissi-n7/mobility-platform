type ReferenceTabsProps = {
  countriesCount: number;
  departmentsCount: number;
  universitiesCount: number;
};

export function ReferenceTabs({
  countriesCount,
  departmentsCount,
  universitiesCount,
}: ReferenceTabsProps) {
  const tabs = [
    { label: "Pays", value: countriesCount },
    { label: "Departements", value: departmentsCount },
    { label: "Universites", value: universitiesCount },
  ];

  return (
    <div className="flex flex-wrap gap-2 rounded-lg border border-gray-200 bg-white p-2 shadow-sm">
      {tabs.map((tab, index) => (
        <a
          key={tab.label}
          className={`rounded-md px-4 py-2 text-sm font-medium transition-colors ${
            index === 0
              ? "bg-[#1E3A8A] text-white"
              : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
          }`}
          href={`#${tab.label.toLowerCase()}`}
        >
          {tab.label}
          <span className="ml-2 text-xs opacity-75">{tab.value}</span>
        </a>
      ))}
    </div>
  );
}
