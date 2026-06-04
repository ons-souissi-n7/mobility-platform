type Tab = {
  label: string;
  value: number | string;
  href?: string;
};

export function PageTabBar({ tabs }: { tabs: Tab[] }) {
  return (
    <div className="flex flex-wrap gap-2 rounded-lg border border-gray-200 bg-white p-2 shadow-sm">
      {tabs.map((tab, index) => {
        const cls = [
          "rounded-md px-4 py-2 text-sm font-medium transition-colors",
          index === 0
            ? "bg-[#1E3A8A] text-white"
            : "text-gray-600 hover:bg-gray-100 hover:text-gray-900",
        ].join(" ");

        return tab.href ? (
          <a key={tab.label} className={cls} href={tab.href}>
            {tab.label}
            <span className="ml-2 text-xs opacity-75">{tab.value}</span>
          </a>
        ) : (
          <span key={tab.label} className={cls}>
            {tab.label}
            <span className="ml-2 text-xs opacity-75">{tab.value}</span>
          </span>
        );
      })}
    </div>
  );
}
