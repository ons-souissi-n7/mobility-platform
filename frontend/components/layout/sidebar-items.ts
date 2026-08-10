import {
  BarChart3,
  Briefcase,
  CalendarRange,
  ClipboardCheck,
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
    href: "/admin/analytiques",
    label: "Tableau de bord",
    icon: LayoutDashboard,
  },
  {
    href: "/admin/etudiants",
    label: "Étudiants",
    icon: Users,
  },
  {
    href: "/admin/sortantes",
    label: "Mobilites sortantes",
    icon: PlaneTakeoff,
  },
  {
    href: "/admin/entrantes",
    label: "Mobilites entrantes",
    icon: PlaneLanding,
  },
  {
    href: "/admin/internships",
    label: "Stages internationaux",
    icon: Briefcase,
  },
  {
    href: "/admin/mobilites-complementaires",
    label: "Mobilités complémentaires",
    icon: ClipboardCheck,
  },
  {
    href: "/admin/mobility",
    label: "Accords et quotas",
    icon: FileText,
  },
  {
    href: "/admin/statistiques",
    label: "Statistiques CTI",
    icon: BarChart3,
  },
  {
    href: "/admin/references",
    label: "Referentiels",
    icon: Settings,
  },
  {
    href: "/admin/academic-years",
    label: "Années universitaires",
    icon: CalendarRange,
  },
  {
    href: "/admin/rapports-import",
    label: "Rapports d'import",
    icon: FileBarChart,
  },
  {
    href: "/admin/audit",
    label: "Journal d'audit",
    icon: ScrollText,
  },
];
