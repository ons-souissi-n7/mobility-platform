import type { ReactNode } from "react";

import { Sidebar } from "@/components/layout/sidebar";

type AdminShellProps = {
  children: ReactNode;
};

export function AdminShell({ children }: AdminShellProps) {
  return (
    <div className="flex min-h-screen bg-[#F9FAFB]">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-x-hidden">
        <div className="mx-auto w-full max-w-7xl px-8 py-8">{children}</div>
      </main>
    </div>
  );
}
