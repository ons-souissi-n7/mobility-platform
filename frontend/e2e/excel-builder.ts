/**
 * Construit en mémoire un fichier .xlsx conforme au gabarit "Mobilités
 * entrantes" (voir backend/app/incoming/services/excel_template.py, colonnes
 * _COLUMNS de excel_importer.py) — utilisé pour tester un dépôt de fichier
 * réel dans les tests E2E, plutôt que de contourner l'upload via l'API.
 */

import ExcelJS from "exceljs";

const INCOMING_HEADERS = [
  "DEPARTEMENT",
  "CIVILITE",
  "NOM",
  "PRENOM",
  "PAYS",
  "UNIV ORIGINE",
  "DATE NAISSANCE",
  "CADRE",
  "MAIL",
  "MAIL ENSEEIHT",
  "DUREE",
  "ANNEE",
  "PARCOURS",
  "REMARQUES",
  "STAGE",
  "DIPLOME",
  "POURSUITE DOCTORAT",
];

export interface IncomingStudentRow {
  DEPARTEMENT: string;
  CIVILITE: string;
  NOM: string;
  PRENOM: string;
  PAYS: string;
  "UNIV ORIGINE": string;
  "DATE NAISSANCE": string;
  CADRE: string;
  MAIL: string;
  "MAIL ENSEEIHT": string;
  DUREE?: string;
  ANNEE: string;
  PARCOURS: string;
  REMARQUES?: string;
  STAGE?: string;
  DIPLOME?: string;
  "POURSUITE DOCTORAT"?: string;
}

/** Construit un classeur à une ligne conforme au gabarit d'import des mobilités entrantes. */
export async function buildIncomingXlsx(row: IncomingStudentRow): Promise<Buffer> {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet("Etudiants entrants");
  ws.addRow(INCOMING_HEADERS);
  ws.addRow(INCOMING_HEADERS.map((h) => (row as unknown as Record<string, string | undefined>)[h] ?? ""));
  const buf = await wb.xlsx.writeBuffer();
  return Buffer.from(buf);
}

// ── Gabarit étudiants (voir backend/app/students/api.py:download_student_template
//    et app/students/services/adapters/excel.py) ────────────────────────────

const STUDENTS_HEADERS = [
  "INE",
  "Nom",
  "Prénom",
  "Email",
  "Genre",
  "Département",
  "Niveau",
  "Parcours",
  "GPA",
  "Boursier",
  "FISE/FISA",
];

export interface StudentImportRow {
  INE: string;
  Nom: string;
  Prénom: string;
  Email?: string;
  Genre?: "M" | "F";
  Département: string;
  Niveau: string;
  Parcours?: string;
  GPA?: string;
  Boursier?: "Oui" | "Non";
  "FISE/FISA"?: "FISE" | "FISA";
}

/** Construit un classeur d'import étudiants avec une ou plusieurs lignes. */
export async function buildStudentsXlsx(rows: StudentImportRow[]): Promise<Buffer> {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet("Etudiants");
  ws.addRow(STUDENTS_HEADERS);
  for (const row of rows) {
    ws.addRow(STUDENTS_HEADERS.map((h) => (row as unknown as Record<string, string | undefined>)[h] ?? ""));
  }
  const buf = await wb.xlsx.writeBuffer();
  return Buffer.from(buf);
}

// ── Gabarit accords de mobilité (voir
//    backend/app/mobility/services/excel_importer.py:TEMPLATE_COLUMNS) ──────

const AGREEMENTS_HEADERS = [
  "Etablissement externe",
  "Nom de l'accord",
  "Departements concernes (codes, ex: SN;3EA)",
  "Niveaux concernes (codes, ex: 3A;2A)",
  "Cadre d'accord",
  "Nombre de places (entier ou 'illimite')",
  "Etablissements internes (nom court, ex: INP-ENSEEIHT;INP-ENSAT)",
  "Remarques",
  "Duree du sejour (semaines)",
];

export interface AgreementImportRow {
  "Etablissement externe": string;
  "Nom de l'accord": string;
  "Departements concernes (codes, ex: SN;3EA)"?: string;
  "Niveaux concernes (codes, ex: 3A;2A)"?: string;
  "Cadre d'accord"?: string;
  "Nombre de places (entier ou 'illimite')"?: string;
  "Etablissements internes (nom court, ex: INP-ENSEEIHT;INP-ENSAT)"?: string;
  Remarques?: string;
  "Duree du sejour (semaines)"?: string;
}

/** Construit un classeur d'import accords avec une ou plusieurs lignes. */
export async function buildAgreementsXlsx(rows: AgreementImportRow[]): Promise<Buffer> {
  const wb = new ExcelJS.Workbook();
  const ws = wb.addWorksheet("Accords");
  ws.addRow(AGREEMENTS_HEADERS);
  for (const row of rows) {
    ws.addRow(AGREEMENTS_HEADERS.map((h) => (row as unknown as Record<string, string | undefined>)[h] ?? ""));
  }
  const buf = await wb.xlsx.writeBuffer();
  return Buffer.from(buf);
}
