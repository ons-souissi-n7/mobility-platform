import {
  BarChart3,
  CalendarRange,
  ClipboardCheck,
  FileText,
  Heart,
  LayoutDashboard,
  PlaneLanding,
  PlaneTakeoff,
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
    href: "/voeux",
    label: "Voeux étudiants",
    icon: Heart,
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
    href: "/affectations",
    label: "Affectations",
    icon: ClipboardCheck,
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
];
