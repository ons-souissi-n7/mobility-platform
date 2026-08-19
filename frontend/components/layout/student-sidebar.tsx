"use client";

import {
  Award,
  Globe,
  LayoutDashboard,
  LogOut,
  PlusCircle,
  Star,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useState } from "react";

import { getTokenPayload, logout, type TokenPayload } from "@/lib/auth";

const linkBase =
  "flex items-center gap-3 border-l-4 px-6 py-3 text-sm transition-colors";
const linkActive = "border-white bg-white/10 font-medium text-white";
const linkInactive =
  "border-transparent text-blue-100 hover:bg-white/5 hover:text-white";

const NAV_ITEMS = [
  { key: "tableau-de-bord", label: "Tableau de bord", icon: LayoutDashboard },
  { key: "accords", label: "Accords disponibles", icon: Globe },
  { key: "recommandations", label: "Recommandations", icon: Star },
  { key: "mobilite", label: "Ma mobilité", icon: Award },
  {
    key: "mobilite-complementaire",
    label: "Mobilité complémentaire",
    icon: PlusCircle,
  },
];

type Props = { isOpen?: boolean; onClose?: () => void };

function initials(email: string): string {
  const local = email.split("@")[0];
  return (local[0] ?? "E").toUpperCase();
}

async function handleLogout() {
  await logout();
}

export function StudentSidebar({ isOpen = false, onClose }: Readonly<Props>) {
  const pathname = usePathname();
  const [user, setUser] = useState<TokenPayload | null>(null);

  useEffect(() => {
    setUser(getTokenPayload());
  }, []);

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
          href="/student/tableau-de-bord"
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
          <X className="h-5 w-5" />
        </button>
      </div>

      <nav className="flex-1 overflow-y-auto py-2">
        <ul className="flex flex-col">
          {NAV_ITEMS.map(({ key, label, icon: Icon }) => {
            const href = `/student/${key}`;
            const isActive =
              pathname === href || pathname.startsWith(`${href}/`);
            return (
              <li key={key}>
                <Link
                  href={href}
                  className={`${linkBase} ${isActive ? linkActive : linkInactive}`}
                  onClick={onClose}
                >
                  <Icon className="h-5 w-5" aria-hidden="true" />
                  <span>{label}</span>
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
              {user ? initials(user.email) : "E"}
            </div>
            <div className="flex min-w-0 flex-col">
              <span className="truncate text-xs text-blue-200">
                {user?.email ?? "…"}
              </span>
              <span className="truncate text-xs text-blue-300">
                INE : {user?.ine ?? "…"}
              </span>
            </div>
          </div>

          <button
            className="flex-shrink-0 rounded-md p-2 text-blue-200 transition-colors hover:bg-white/10 hover:text-white"
            title="Déconnexion"
            type="button"
            onClick={handleLogout}
          >
            <LogOut className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
      </div>
    </aside>
  );
}
