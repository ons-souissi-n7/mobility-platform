import {
  BarChart3,
  CalendarRange,
  FileBarChart,
  FileText,
  LayoutDashboard,
  PlaneLanding,
  PlaneTakeoff,
  ScrollText,
  Settings,
  Users,
} from "lucide-react";

export const adminNavigation = [
  {
    href: "/",
    label: "Tableau de bord",
    icon: LayoutDashboard,
  },
  {
    href: "/etudiants",
    label: "Etudiants",
    icon: Users,
  },
  {
    href: "/sortantes",
    label: "Mobilites sortantes",
    icon: PlaneTakeoff,
  },
  {
    href: "/entrantes",
    label: "Mobilites entrantes",
    icon: PlaneLanding,
  },
  {
    href: "/mobility",
    label: "Accords et quotas",
    icon: FileText,
  },
  {
    href: "/statistiques",
    label: "Statistiques CTI",
    icon: BarChart3,
  },
  {
    href: "/references",
    label: "Referentiels",
    icon: Settings,
  },
  {
    href: "/academic-years",
    label: "Annees universitaires",
    icon: CalendarRange,
  },
  {
    href: "/rapports-import",
    label: "Rapports d'import",
    icon: FileBarChart,
  },
  {
    href: "/audit",
    label: "Journal d'audit",
    icon: ScrollText,
  },
];
