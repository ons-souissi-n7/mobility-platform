"use client";

import { LogOut, X } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { adminNavigation } from "@/components/layout/sidebar-items";

type SidebarProps = {
  isOpen?: boolean;
  onClose?: () => void;
};

const linkBase =
  "flex items-center gap-3 border-l-4 px-6 py-3 text-sm transition-colors";
const linkActive = "border-white bg-white/10 font-medium text-white";
const linkInactive =
  "border-transparent text-blue-100 hover:bg-white/5 hover:text-white";

export function Sidebar({ isOpen = false, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={[
        "fixed left-0 top-0 z-40 flex h-screen w-64 flex-shrink-0 flex-col bg-[#1E3A8A]",
        "transition-transform duration-200 ease-in-out",
        isOpen ? "translate-x-0" : "-translate-x-full",
        "lg:translate-x-0",
      ].join(" ")}
    >
      <div className="flex h-20 items-center justify-between px-6">
        <Link
          href="/references"
          className="text-xl font-bold tracking-wider text-white"
        >
          N7 MOBILITE
        </Link>
        <button
          type="button"
          onClick={onClose}
          className="rounded-md p-1.5 text-blue-200 hover:bg-white/10 hover:text-white lg:hidden"
          aria-label="Fermer le menu"
        >
          <X className="h-5 w-5" aria-hidden="true" />
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-2" aria-label="Navigation principale">
        <ul className="flex flex-col">
          {adminNavigation.map((item) => {
            const Icon = item.icon;
            const isActive =
              item.href === "/"
                ? pathname === "/"
                : pathname === item.href || pathname.startsWith(`${item.href}/`);

            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={`${linkBase} ${isActive ? linkActive : linkInactive}`}
                  onClick={onClose}
                >
                  <Icon className="h-5 w-5" aria-hidden="true" />
                  <span>{item.label}</span>
                </Link>
              </li>
            );
          })}
        </ul>
      </nav>

      <div className="mt-auto border-t border-white/10">
        <div className="flex items-center justify-between p-4">
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-full bg-white/20 text-sm font-bold text-white">
              AD
            </div>
            <div className="flex min-w-0 flex-col">
              <span className="truncate text-sm font-medium text-white">Admin RI</span>
              <span className="truncate text-xs text-blue-200">
                admin.ri@ecole.fr
              </span>
            </div>
          </div>

          <button
            className="flex-shrink-0 rounded-md p-2 text-blue-200 transition-colors hover:bg-white/10 hover:text-white"
            title="Deconnexion"
            type="button"
          >
            <LogOut className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </aside>
  );
}
