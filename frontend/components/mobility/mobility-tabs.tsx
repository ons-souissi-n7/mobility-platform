"use client";

import { FileText } from "lucide-react";

export function MobilityTabs({ agreementsCount }: { agreementsCount: number }) {
  return (
    <div className="flex flex-wrap gap-2 rounded-lg border border-gray-200 bg-white p-2 shadow-sm">
      <a
        className="inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium text-gray-700 transition-colors hover:bg-blue-50 hover:text-[#1E3A8A]"
        href="#accords"
      >
        <FileText className="h-4 w-4" aria-hidden="true" />
        Accords
        <span className="rounded-full bg-gray-100 px-2 py-0.5 text-xs text-gray-600">
          {agreementsCount}
        </span>
      </a>
    </div>
  );
}
