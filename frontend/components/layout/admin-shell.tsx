"use client";

import { Menu } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import type { ReactNode } from "react";

import { AlertBanner } from "@/components/layout/alert-banner";
import { Sidebar } from "@/components/layout/sidebar";

type AdminShellProps = {
  children: ReactNode;
};

export function AdminShell({ children }: Readonly<AdminShellProps>) {
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (  
    <div className="flex min-h-screen bg-[#F9FAFB]">
      {/* Mobile backdrop */}
      {sidebarOpen && (
        <button
          type="button"
          aria-label="Fermer le menu"
          className="fixed inset-0 z-30 cursor-default bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex min-w-0 flex-1 flex-col lg:ml-64">
        {/* Mobile top bar */}
        <header className="sticky top-0 z-20 flex h-14 items-center gap-3 border-b bg-white px-4 shadow-sm lg:hidden">
          <button
            type="button"
            onClick={() => setSidebarOpen(true)}
            className="rounded-md p-2 text-gray-600 hover:bg-gray-100"
            aria-label="Ouvrir le menu"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <Link
            href="/admin/analytiques"
            className="text-lg font-bold tracking-wider text-[#1E3A8A]"
          >
            N7 MOBILITE
          </Link>
        </header>

        <main className="min-w-0 flex-1 overflow-x-hidden">
          <AlertBanner />
          <div className="mx-auto w-full max-w-7xl px-4 py-6 sm:px-8 sm:py-8">
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}
