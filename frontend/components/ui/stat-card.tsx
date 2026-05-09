import type { LucideIcon } from "lucide-react";

type StatCardProps = {
  label: string;
  value: string | number;
  helper: string;
  icon: LucideIcon;
  tone: "blue" | "emerald" | "amber";
};

const toneStyles = {
  blue: "bg-blue-50 text-blue-600",
  emerald: "bg-emerald-50 text-emerald-600",
  amber: "bg-amber-50 text-amber-600",
};

export function StatCard({ label, value, helper, icon: Icon, tone }: StatCardProps) {
  return (
    <div className="flex flex-col rounded-lg border border-gray-100 bg-white p-6 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm font-medium text-gray-500">{label}</p>
          <p className="mt-2 text-3xl font-bold text-gray-900">{value}</p>
        </div>
        <div className={`rounded-lg p-3 ${toneStyles[tone]}`}>
          <Icon className="h-6 w-6" aria-hidden="true" />
        </div>
      </div>
      <p className="mt-4 text-sm font-medium text-gray-500">{helper}</p>
    </div>
  );
}
