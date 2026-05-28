"use client";

import { useMemo, useState } from "react";
import { Plus, RefreshCw } from "lucide-react";

import { AgreementForm, type AgreementFullPayload } from "@/components/mobility/agreement-form";
import { MobilityCategoryForm } from "@/components/mobility/agreement-framework-form";
import { AgreementsTable } from "@/components/mobility/agreements-table";
import { DepartmentQuotaForm } from "@/components/mobility/department-quota-form";
import { MobilityImportErrorsPanel } from "@/components/mobility/mobility-import-errors-panel";
import { ActionButtons } from "@/components/ui/action-buttons";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { StatCard } from "@/components/ui/stat-card";
import { FileText, Gauge, Landmark, Layers } from "lucide-react";
import { MobilitySection } from "@/components/mobility/mobility-section";
import { Modal } from "@/components/ui/modal";
import { SearchInput } from "@/components/ui/search-input";
import {
  createAgreement,
  createAgreementAvailability,
  createAgreementDepartmentConstraint,
  createMobilityCategory,
  createAgreementLevelConstraint,
  createAgreementQuota,
  createDepartmentQuota,
  deleteAgreement,
  deleteAgreementDepartmentConstraint,
  deleteMobilityCategory,
  deleteAgreementLevelConstraint,
  deleteDepartmentQuota,
  downloadExcelTemplate,
  getMobilityCategories,
  getAgreementQuotas,
  getAgreementAvailabilities,
  getAgreements,
  getDepartmentQuotas,
  getMoveonMobilityImportErrors,
  ignoreMobilityImport,
  importAgreementsFromExcel,
  retryMobilityImport,
  syncMobilityFromMoveon,
  updateAgreement,
  updateAgreementAvailability,
  updateMobilityCategory,
  updateAgreementQuota,
  updateDepartmentQuota,
  validateAgreementQuota,
  validateDepartmentQuota,
  type MobilityCategoryPayload,
  type AgreementQuotaPayload,
  type DepartmentQuotaPayload,
  type MobilityImportRetryPayload,
} from "@/lib/api/mobility-mutations";
import type {
  AcademicYear,
  Agreement,
  AgreementDepartmentConstraint,
  MobilityCategory,
  AgreementLevelConstraint,
  AgreementQuota,
  AgreementYearAvailability,
  Department,
  DepartmentQuota,
  Level,
  PartnerUniversity,
  RawImport,
} from "@/lib/api/types";

type ModalState =
  | { kind: "agreement"; item?: Agreement }
  | { kind: "departmentQuota"; agreementQuotaId?: number; item?: DepartmentQuota }
  | { kind: "levelConstraint"; agreementId: number }
  | { kind: "deptConstraint"; agreementId: number }
  | { kind: "framework"; item?: MobilityCategory };

export function MobilityWorkspace({
  academicYears,
  agreementAvailabilities: initialAgreementAvailabilities,
  agreementDepartmentConstraints: initialAgreementDeptConstraints,
  mobilityCategories: initialMobilityCategories,
  agreementLevelConstraints,
  currentYear,
  initialAgreementQuotas,
  initialAgreements,
  initialDepartmentQuotas,
  initialImportErrors,
  departments,
  mobilityLevels,
  universities,
}: {
  academicYears: AcademicYear[];
  agreementAvailabilities: AgreementYearAvailability[];
  agreementDepartmentConstraints: AgreementDepartmentConstraint[];
  mobilityCategories: MobilityCategory[];
  agreementLevelConstraints: AgreementLevelConstraint[];
  currentYear: AcademicYear | null;
  initialAgreementQuotas: AgreementQuota[];
  initialAgreements: Agreement[];
  initialDepartmentQuotas: DepartmentQuota[];
  initialImportErrors: RawImport[];
  departments: Department[];
  mobilityLevels: Level[];
  universities: PartnerUniversity[];
}) {
  const [agreements, setAgreements] = useState(initialAgreements);
  const [agreementAvailabilities, setAgreementAvailabilities] = useState(
    initialAgreementAvailabilities,
  );
  const [mobilityCategories, setMobilityCategories] = useState(initialMobilityCategories);
  const [agreementQuotas, setAgreementQuotas] = useState(initialAgreementQuotas);
  const [agreementLvlConstraints, setAgreementLvlConstraints] = useState(agreementLevelConstraints);
  const [agreementDeptConstraints, setAgreementDeptConstraints] = useState(initialAgreementDeptConstraints);
  const [departmentQuotas, setDepartmentQuotas] = useState(initialDepartmentQuotas);
  const [importErrors, setImportErrors] = useState(initialImportErrors);
  const [excelImportInProgress, setExcelImportInProgress] = useState(false);
  const [modal, setModal] = useState<ModalState | null>(null);
  const { confirm, dialog: confirmDialog } = useConfirm();
  const [query, setQuery] = useState("");
  const [syncError, setSyncError] = useState("");
  const [syncInProgress, setSyncInProgress] = useState(false);
  const [yearFilter, setYearFilter] = useState<string>(currentYear?.label ?? "");
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [activityFilter, setActivityFilter] = useState<string>("active");

  const normalizedQuery = query.trim().toLowerCase();
  const universitiesById = useMemo(
    () => new Map(universities.map((university) => [university.id, university])),
    [universities],
  );

  const filteredAgreements = useMemo(() => {
    if (!normalizedQuery) return agreements;

    return agreements.filter((agreement) => {
      const university = universitiesById.get(agreement.partner_university_id);

      return [
        agreement.name,
        agreement.reference,
        agreement.moveon_relation_id,
        agreement.framework,
        university?.name,
        university?.city,
      ]
        .join(" ")
        .toLowerCase()
        .includes(normalizedQuery);
    });
  }, [agreements, normalizedQuery, universitiesById]);

  const agreementsForDisplay = useMemo(() => {
    let base =
      categoryFilter === "all"
        ? filteredAgreements
        : filteredAgreements.filter(
            (agreement) => agreement.framework_ref_id === Number(categoryFilter),
          );

    if (activityFilter === "active") {
      base = base.filter((agreement) =>
        isAgreementAvailableForSelectedYear(
          agreement,
          yearFilter,
          academicYears,
          agreementAvailabilities,
        ),
      );
    } else if (activityFilter === "inactive") {
      base = base.filter(
        (agreement) =>
          !isAgreementAvailableForSelectedYear(
            agreement,
            yearFilter,
            academicYears,
            agreementAvailabilities,
          ),
      );
    }

    if (yearFilter) {
      const selectedYear = academicYears.find((y) => y.label === yearFilter);
      if (selectedYear?.status === "closed") {
        const quotaAgreementIds = new Set(
          agreementQuotas
            .filter((q) => q.academic_year_label === yearFilter)
            .map((q) => q.agreement_id),
        );
        const availabilityAgreementIds = new Set(
          agreementAvailabilities
            .filter((a) => a.academic_year_label === yearFilter)
            .map((a) => a.agreement_id),
        );
        base = base.filter(
          (a) => quotaAgreementIds.has(a.id!) || availabilityAgreementIds.has(a.id!),
        );
      }
    }

    return base;
  }, [
    academicYears,
    activityFilter,
    agreementAvailabilities,
    agreementQuotas,
    filteredAgreements,
    categoryFilter,
    yearFilter,
  ]);

  const currentYearQuotas = useMemo(() => {
    if (!currentYear) return agreementQuotas;
    return agreementQuotas.filter((q) => q.academic_year_label === currentYear.label);
  }, [agreementQuotas, currentYear]);

  const statTotalPlaces = useMemo(
    () => currentYearQuotas.reduce((acc, q) => acc + q.total_places, 0),
    [currentYearQuotas],
  );

  const statRemainingPlaces = useMemo(
    () => currentYearQuotas.reduce((acc, q) => acc + q.remaining_places, 0),
    [currentYearQuotas],
  );

  async function submitAgreement(payload: AgreementFullPayload) {
    if (modal?.kind !== "agreement") return;

    if (modal.item) {
      const updated = await updateAgreement(modal.item.id!, payload);
      setAgreements((items) => items.map((item) => (item.id === updated.id ? updated : item)));
    } else {
      const created = await createAgreement(payload);
      setAgreements((items) => [...items, created]);

      for (const deptId of payload.department_ids) {
        const deptConstraint = await createAgreementDepartmentConstraint({
          agreement_id: created.id!,
          department_id: deptId,
          is_active: true,
          source: "manual",
          remarks: "",
        });
        setAgreementDeptConstraints((items) => [...items, deptConstraint]);
      }

      for (const levelId of payload.level_ids) {
        const constraint = await createAgreementLevelConstraint({
          agreement_id: created.id!,
          level_id: levelId,
          is_active: true,
          source: "manual",
          remarks: "",
        });
        setAgreementLvlConstraints((items) => [...items, constraint]);
      }

      const totalPlaces = payload.n7_places ?? payload.source_total_places;
      if (totalPlaces !== null && totalPlaces !== undefined && currentYear) {
        const newQuota = await createAgreementQuota({
          agreement_id: created.id!,
          academic_year_id: currentYear.id,
          academic_year_label: currentYear.label,
          period: "",
          total_places: totalPlaces,
          remaining_places: totalPlaces,
          source_total_places: payload.source_total_places,
          remarks: "",
          source_institutions: payload.source_institutions,
        });
        setAgreementQuotas((items) => [...items, newQuota]);
        const nextDeptQuotas = await getDepartmentQuotas();
        setDepartmentQuotas(nextDeptQuotas);
      }
    }

    setModal(null);
  }

  async function handleInlineQuotaSave(
    agreement: Agreement,
    places: number,
    existingQuota: AgreementQuota | null,
  ) {
    const year = academicYears.find((y) => y.label === yearFilter) ?? currentYear;
    if (!year) return;

    const payload: AgreementQuotaPayload = {
      agreement_id: agreement.id!,
      academic_year_id: year.id,
      academic_year_label: year.label,
      period: "",
      total_places: places,
      remaining_places: places,
      source_total_places: existingQuota?.source_total_places ?? null,
      remarks: existingQuota?.remarks ?? "",
      source_institutions: existingQuota?.source_institutions ?? "",
    };

    if (existingQuota) {
      const updated = await updateAgreementQuota(existingQuota.id, payload);
      setAgreementQuotas((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      const existingDeptQuotas = departmentQuotas.filter(
        (dq) => dq.agreement_quota_id === existingQuota.id && !dq.is_validated,
      );
      if (!existingQuota.is_validated) {
        const deptQuotasToRedistribute = await ensureAgreementDepartmentQuotas(
          agreement,
          existingQuota.id,
          existingDeptQuotas,
        );
        if (deptQuotasToRedistribute.length > 0) {
          await redistributeEqually(existingQuota.id, places, deptQuotasToRedistribute);
        }
      }
    } else {
      const created = await createAgreementQuota(payload);
      setAgreementQuotas((items) => [...items, created]);
      const nextDeptQuotas = await getDepartmentQuotas();
      setDepartmentQuotas(nextDeptQuotas);
    }
  }

  async function redistributeEqually(quotaId: number, totalPlaces: number, deptQuotas: DepartmentQuota[]) {
    if (deptQuotas.length === 0) {
      setDepartmentQuotas((prev) => prev.filter((dq) => dq.agreement_quota_id !== quotaId));
      return;
    }
    const targetPlaces = distributePlaces(totalPlaces, deptQuotas.length);
    const updated: DepartmentQuota[] = [];
    for (const [index, dq] of deptQuotas.entries()) {
      const places = targetPlaces[index] ?? 0;
      if (dq.places !== places) {
        const u = await updateDepartmentQuota(dq.id, {
          agreement_quota_id: dq.agreement_quota_id,
          department_id: dq.department_id,
          level_id: dq.level_id,
          places,
          is_estimated: dq.is_estimated,
          estimation_basis: dq.estimation_basis,
          remarks: dq.remarks,
        });
        updated.push(u);
      } else {
        updated.push(dq);
      }
    }
    setDepartmentQuotas((prev) => [
      ...prev.filter((dq) => dq.agreement_quota_id !== quotaId),
      ...updated,
    ]);
  }

  async function ensureAgreementDepartmentQuotas(
    agreement: Agreement,
    quotaId: number,
    existingDeptQuotas: DepartmentQuota[],
  ) {
    const activeDeptIds = agreementDeptConstraints
      .filter((constraint) => constraint.agreement_id === agreement.id && constraint.is_active)
      .map((constraint) => constraint.department_id);

    if (activeDeptIds.length === 0) return existingDeptQuotas;

    const nextDeptQuotas = [...existingDeptQuotas];
    for (const departmentId of activeDeptIds) {
      if (nextDeptQuotas.some((quota) => quota.department_id === departmentId)) continue;

      const created = await createDepartmentQuota({
        agreement_quota_id: quotaId,
        department_id: departmentId,
        level_id: null,
        places: 0,
        is_estimated: true,
        estimation_basis: "Repartition automatique sur les departements de l'accord.",
        remarks: "",
      });
      nextDeptQuotas.push(created);
    }

    return nextDeptQuotas.sort(
      (left, right) =>
        activeDeptIds.indexOf(left.department_id) - activeDeptIds.indexOf(right.department_id),
    );
  }

  async function submitDepartmentQuota(payload: DepartmentQuotaPayload) {
    if (modal?.kind !== "departmentQuota") return;

    if (modal.item) {
      const updated = await updateDepartmentQuota(modal.item.id, payload);
      setDepartmentQuotas((items) =>
        items.map((item) => (item.id === updated.id ? updated : item)),
      );
    } else {
      const created = await createDepartmentQuota(payload);
      const quotaId = payload.agreement_quota_id;
      const parentQuota = agreementQuotas.find((q) => q.id === quotaId);
      const allForQuota = [
        ...departmentQuotas.filter((dq) => dq.agreement_quota_id === quotaId),
        created,
      ];
      if (parentQuota && !parentQuota.is_validated && allForQuota.length > 1) {
        await redistributeEqually(quotaId, parentQuota.total_places, allForQuota);
        setModal(null);
        return;
      }
      setDepartmentQuotas((items) => [...items, created]);
    }

    setModal(null);
  }

  async function removeAgreement(agreement: Agreement) {
    if (!await confirm(`Supprimer l'accord "${agreement.name}" ?`)) return;
    setSyncError("");
    try {
      await deleteAgreement(agreement.id!);
      setAgreements((items) => items.filter((item) => item.id !== agreement.id));
      setAgreementQuotas((items) => items.filter((item) => item.agreement_id !== agreement.id));
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de supprimer l'accord.");
    }
  }

  async function removeDepartmentQuota(quota: DepartmentQuota) {
    if (!await confirm("Supprimer cette repartition departement ?")) return;
    setSyncError("");
    try {
      await deleteDepartmentQuota(quota.id);
      const parentQuota = agreementQuotas.find((q) => q.id === quota.agreement_quota_id);
      const remaining = departmentQuotas.filter(
        (dq) => dq.id !== quota.id && dq.agreement_quota_id === quota.agreement_quota_id,
      );
      if (parentQuota && !parentQuota.is_validated && remaining.length > 0) {
        await redistributeEqually(quota.agreement_quota_id, parentQuota.total_places, remaining);
      } else {
        setDepartmentQuotas((items) => items.filter((item) => item.id !== quota.id));
      }
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de supprimer la repartition.");
    }
  }

  async function confirmAgreementQuota(quota: AgreementQuota) {
    const validationError = getQuotaValidationError(quota, departmentQuotas);
    if (validationError) {
      setSyncError(validationError);
      return;
    }
    setSyncError("");
    try {
      const validated = await validateAgreementQuota(quota.id);
      setAgreementQuotas((items) =>
        items.map((item) => (item.id === validated.id ? validated : item)),
      );
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de valider le quota.");
    }
  }

  async function confirmDepartmentQuota(quota: DepartmentQuota) {
    const parentQuota = agreementQuotas.find((item) => item.id === quota.agreement_quota_id);
    if (parentQuota) {
      const validationError = getQuotaValidationError(parentQuota, departmentQuotas);
      if (validationError) {
        setSyncError(validationError);
        return;
      }
    }
    setSyncError("");
    try {
      const validated = await validateDepartmentQuota(quota.id);
      setDepartmentQuotas((items) =>
        items.map((item) => (item.id === validated.id ? validated : item)),
      );
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de valider le quota departement.");
    }
  }

  async function submitFramework(payload: MobilityCategoryPayload) {
    if (modal?.kind !== "framework") return;
    if (modal.item) {
      const updated = await updateMobilityCategory(modal.item.id, payload);
      setMobilityCategories((items) =>
        items.map((item) => (item.id === updated.id ? updated : item)),
      );
    } else {
      const created = await createMobilityCategory(payload);
      setMobilityCategories((items) => [...items, created]);
    }
    setModal(null);
  }

  async function removeFramework(framework: MobilityCategory) {
    if (!await confirm(`Supprimer le cadre "${framework.name}" ?`)) return;
    setSyncError("");
    try {
      await deleteMobilityCategory(framework.id);
      setMobilityCategories((items) => items.filter((item) => item.id !== framework.id));
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de supprimer le cadre.");
    }
  }

  async function submitLevelConstraint(agreementId: number, levelId: number) {
    const constraint = await createAgreementLevelConstraint({
      agreement_id: agreementId,
      level_id: levelId,
      is_active: true,
      source: "manual",
      remarks: "",
    });
    setAgreementLvlConstraints((items) => [...items, constraint]);
    setModal(null);
  }

  async function removeLevelConstraint(constraint: AgreementLevelConstraint) {
    setSyncError("");
    try {
      await deleteAgreementLevelConstraint(constraint.id);
      setAgreementLvlConstraints((items) => items.filter((c) => c.id !== constraint.id));
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de supprimer la contrainte niveau.");
    }
  }

  async function submitDepartmentConstraint(agreementId: number, departmentId: number) {
    const constraint = await createAgreementDepartmentConstraint({
      agreement_id: agreementId,
      department_id: departmentId,
      is_active: true,
      source: "manual",
      remarks: "",
    });
    setAgreementDeptConstraints((items) => [...items, constraint]);
    setModal(null);
  }

  async function removeDepartmentConstraint(constraint: AgreementDepartmentConstraint) {
    setSyncError("");
    try {
      await deleteAgreementDepartmentConstraint(constraint.id);
      setAgreementDeptConstraints((items) => items.filter((c) => c.id !== constraint.id));
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de supprimer la contrainte departement.");
    }
  }

  async function handleExcelImport(file: File) {
    setSyncError("");
    setExcelImportInProgress(true);
    try {
      await importAgreementsFromExcel(file);
      await delay(3000);
      await refreshMobilityData();
    } catch (error) {
      setSyncError(
        error instanceof Error ? error.message : "L'import Excel a echoue.",
      );
    } finally {
      setExcelImportInProgress(false);
    }
  }

  async function toggleAgreementAvailability(agreement: Agreement) {
    const selectedYear = academicYears.find((year) => year.label === yearFilter) ?? currentYear;
    if (!selectedYear) {
      setSyncError("Selectionnez une annee pour changer la disponibilite d'un accord.");
      return;
    }
    setSyncError("");

    const existing = agreementAvailabilities.find(
      (item) =>
        item.agreement_id === agreement.id &&
        item.academic_year_label === selectedYear.label,
    );
    const payload = {
      academic_year_id: selectedYear.id,
      academic_year_label: selectedYear.label,
      agreement_id: agreement.id!,
      is_available: !(existing?.is_available ?? isAgreementValidForYear(agreement, selectedYear)),
      remarks: existing?.remarks ?? "",
      source: "manual",
    };

    try {
      if (existing) {
        const updated = await updateAgreementAvailability(existing.id, payload);
        setAgreementAvailabilities((items) =>
          items.map((item) => (item.id === updated.id ? updated : item)),
        );
      } else {
        const created = await createAgreementAvailability(payload);
        setAgreementAvailabilities((items) => [...items, created]);
      }
    } catch (err) {
      setSyncError(err instanceof Error ? err.message : "Impossible de modifier la disponibilite.");
    }
  }

  async function handleSync() {
    setSyncError("");
    setSyncInProgress(true);
    const previousFingerprint = getSyncFingerprint(
      agreements,
      agreementQuotas,
      agreementAvailabilities,
      departmentQuotas,
      importErrors,
    );

    try {
      await syncMobilityFromMoveon();
      await waitForSyncRefresh(previousFingerprint);
    } catch (error) {
      setSyncError(
        error instanceof Error ? error.message : "La synchronisation MoveON a echoue.",
      );
    } finally {
      setSyncInProgress(false);
    }
  }

  async function refreshMobilityData() {
    const [
      nextMobilityCategories,
      nextAgreementQuotas,
      nextAgreementAvailabilities,
      nextAgreements,
      nextDepartmentQuotas,
      nextErrors,
    ] = await Promise.all([
      getMobilityCategories(),
      getAgreementQuotas(),
      getAgreementAvailabilities(),
      getAgreements(),
      getDepartmentQuotas(),
      getMoveonMobilityImportErrors(),
    ]);

    setMobilityCategories(nextMobilityCategories);
    setAgreementQuotas(nextAgreementQuotas);
    setAgreementAvailabilities(nextAgreementAvailabilities);
    setAgreements(nextAgreements);
    setDepartmentQuotas(nextDepartmentQuotas);
    setImportErrors(nextErrors);

    return {
      mobilityCategories: nextMobilityCategories,
      agreementQuotas: nextAgreementQuotas,
      agreementAvailabilities: nextAgreementAvailabilities,
      agreements: nextAgreements,
      departmentQuotas: nextDepartmentQuotas,
      importErrors: nextErrors,
    };
  }

  async function waitForSyncRefresh(previousFingerprint: string) {
    for (let i = 0; i < 30; i++) {
      await delay(1000);
      const refreshed = await refreshMobilityData();
      const nextFingerprint = getSyncFingerprint(
        refreshed.agreements,
        refreshed.agreementQuotas,
        refreshed.agreementAvailabilities,
        refreshed.departmentQuotas,
        refreshed.importErrors,
      );

      if (nextFingerprint !== previousFingerprint) return;
    }

    await refreshMobilityData();
  }

  async function ignoreImport(error: RawImport) {
    await ignoreMobilityImport(error.id);
    setImportErrors((items) => items.filter((item) => item.id !== error.id));
  }

  async function handleSaveSourceInfo(
    quota: AgreementQuota,
    sourceTotalPlaces: number | null,
    sourceInstitutions: string,
  ) {
    if (sourceTotalPlaces !== null && quota.total_places > sourceTotalPlaces) {
      setSyncError("Le quota N7 ne peut pas etre superieur au quota INP.");
      return;
    }
    setSyncError("");
    const payload: AgreementQuotaPayload = {
      agreement_id: quota.agreement_id,
      academic_year_id: quota.academic_year_id,
      academic_year_label: quota.academic_year_label,
      period: quota.period,
      total_places: quota.total_places,
      remaining_places: quota.remaining_places,
      source_total_places: sourceTotalPlaces,
      remarks: quota.remarks,
      source_institutions: sourceInstitutions,
    };
    const updated = await updateAgreementQuota(quota.id, payload);
    setAgreementQuotas((items) => items.map((item) => (item.id === updated.id ? updated : item)));
  }

  async function retryImport(
    error: RawImport,
    payload: MobilityImportRetryPayload,
  ) {
    await retryMobilityImport(error.id, payload);
    await refreshMobilityData();
    setImportErrors((items) => items.filter((item) => item.id !== error.id));
  }

  return (
    <>
      <div className="grid grid-cols-1 gap-6 md:grid-cols-4 mb-6">
        <StatCard
          helper={currentYear ? `${agreementsForDisplay.filter((a) => a.is_active).length} actifs en ${currentYear.label}` : "Aucune annee courante"}
          icon={FileText}
          label="Accords"
          tone="blue"
          value={agreements.length}
        />
        <StatCard
          helper="Cadres de mobilite synchronises"
          icon={Layers}
          label="Cadres"
          tone="blue"
          value={mobilityCategories.length}
        />
        <StatCard
          helper={currentYear ? `${statRemainingPlaces} restantes en ${currentYear.label}` : `${statRemainingPlaces} restantes`}
          icon={Gauge}
          label="Places"
          tone="emerald"
          value={statTotalPlaces}
        />
        <StatCard
          helper="Repartitions configurees"
          icon={Landmark}
          label="Departements"
          tone="amber"
          value={departmentQuotas.length}
        />
      </div>

      <div className="rounded-lg border border-gray-200 bg-white p-4 shadow-sm">
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <SearchInput
            onChange={setQuery}
            placeholder="Rechercher un accord, partenaire, annee, departement..."
            value={query}
          />

          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
            <label className="block">
              <span className="text-sm font-medium text-gray-700">Annee</span>
              <select
                className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
                onChange={(event) => setYearFilter(event.target.value)}
                value={yearFilter}
              >
                <option value="">Toutes</option>
                {[...academicYears]
                  .sort((a, b) => b.start_date.localeCompare(a.start_date))
                  .map((year) => (
                    <option key={year.id} value={year.label}>
                      {year.label}
                    </option>
                  ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium text-gray-700">Cadre</span>
              <select
                className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
                onChange={(event) => setCategoryFilter(event.target.value)}
                value={categoryFilter}
              >
                <option value="all">Tous</option>
                {mobilityCategories.filter((mc) => mc.is_active).map((mc) => (
                  <option key={mc.id} value={mc.id}>
                    {mc.name}
                  </option>
                ))}
              </select>
            </label>

            <label className="block">
              <span className="text-sm font-medium text-gray-700">Etat</span>
              <select
                className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
                onChange={(event) => setActivityFilter(event.target.value)}
                value={activityFilter}
              >
                <option value="all">Tous</option>
                <option value="active">Actifs</option>
                <option value="inactive">Inactifs</option>
              </select>
            </label>

          </div>
        </div>
      </div>

      {syncError ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {syncError}
        </div>
      ) : null}


      <div id="accords">
        <MobilitySection
          description={`Contrats de mobilite issus de MoveON ou geres manuellement. ${agreementDeptConstraints.length} contrainte(s) departement, ${agreementLvlConstraints.length} contrainte(s) niveau.`}
          title="Accords"
          toolbar={
            <>
              <AddButton label="Ajouter un accord" onClick={() => setModal({ kind: "agreement" })} />
              <ExcelImportButton
                isLoading={excelImportInProgress}
                onDownloadTemplate={downloadExcelTemplate}
                onImport={handleExcelImport}
              />
              <SyncButton isLoading={syncInProgress} onClick={handleSync} />
            </>
          }
        >
          <AgreementsTable
            academicYears={academicYears}
            agreements={agreementsForDisplay}
            agreementDepartmentConstraints={agreementDeptConstraints}
            agreementLevelConstraints={agreementLvlConstraints}
            agreementQuotas={agreementQuotas}
            departmentQuotas={departmentQuotas}
            departments={departments}
            levels={mobilityLevels}
            currentYear={currentYear}
            onAddDepartmentConstraint={(agreement) =>
              setModal({ kind: "deptConstraint", agreementId: agreement.id! })
            }
            onAddDepartmentQuota={(quota) =>
              setModal({ kind: "departmentQuota", agreementQuotaId: quota.id })
            }
            onAddLevelConstraint={(agreement) =>
              setModal({ kind: "levelConstraint", agreementId: agreement.id! })
            }
            onDelete={removeAgreement}
            onDeleteDepartmentConstraint={removeDepartmentConstraint}
            onDeleteDepartmentQuota={removeDepartmentQuota}
            onDeleteLevelConstraint={removeLevelConstraint}
            onEdit={(item) => setModal({ kind: "agreement", item })}
            onEditDepartmentQuota={(item) => setModal({ kind: "departmentQuota", item })}
            onValidateAgreementQuota={confirmAgreementQuota}
            onValidateDepartmentQuota={confirmDepartmentQuota}
            onSaveQuota={handleInlineQuotaSave}
            onSaveSourceInfo={handleSaveSourceInfo}
            onToggleAvailability={toggleAgreementAvailability}
            universities={universities}
            yearFilter={yearFilter}
            yearAvailabilities={agreementAvailabilities}
          />
          <MobilityImportErrorsPanel
            errors={importErrors.filter((e) => e.entity === "agreement")}
            isBusy={syncInProgress}
            onIgnore={ignoreImport}
            onRetry={retryImport}
            universities={universities}
          />
        </MobilitySection>
      </div>

      <div id="cadres">
        <MobilitySection
          description={`${mobilityCategories.length} cadre(s) de mobilite synchronise(s) depuis MoveON.`}
          title="Cadres de mobilite"
          toolbar={
            <>
              <AddButton
                label="Ajouter un cadre"
                onClick={() => setModal({ kind: "framework" })}
              />
              <SyncButton
                isLoading={syncInProgress}
                label="Sync MoveON"
                onClick={handleSync}
              />
            </>
          }
        >
          <MobilityCategoriesTable
            frameworks={mobilityCategories}
            onDelete={removeFramework}
            onEdit={(item) => setModal({ kind: "framework", item })}
          />
        </MobilitySection>
      </div>

      {modal ? (
        <Modal
          description={getModalDescription(modal.kind)}
          onClose={() => setModal(null)}
          title={`${"item" in modal && modal.item ? "Modifier" : "Ajouter"} ${getModalLabel(modal.kind)}`}
        >
          {modal.kind === "agreement" ? (
            <AgreementForm
              departments={departments}
              frameworks={mobilityCategories}
              item={modal.item}
              mobilityLevels={mobilityLevels}
              onCancel={() => setModal(null)}
              onSubmit={submitAgreement}
              universities={universities}
            />
          ) : null}

          {modal.kind === "departmentQuota" ? (
            <DepartmentQuotaForm
              departments={departments}
              existingDeptCount={
                modal.agreementQuotaId
                  ? departmentQuotas.filter((dq) => dq.agreement_quota_id === modal.agreementQuotaId).length
                  : 0
              }
              totalPlaces={
                modal.agreementQuotaId
                  ? (agreementQuotas.find((q) => q.id === modal.agreementQuotaId)?.total_places ?? 0)
                  : 0
              }
              initialAgreementQuotaId={modal.agreementQuotaId}
              item={modal.item}
              onCancel={() => setModal(null)}
              onSubmit={submitDepartmentQuota}
            />
          ) : null}

          {modal.kind === "levelConstraint" ? (
            <LevelConstraintForm
              agreementId={modal.agreementId}
              mobilityLevels={mobilityLevels}
              onCancel={() => setModal(null)}
              onSubmit={submitLevelConstraint}
            />
          ) : null}

          {modal.kind === "deptConstraint" ? (
            <DepartmentConstraintForm
              agreementId={modal.agreementId}
              departments={departments}
              onCancel={() => setModal(null)}
              onSubmit={submitDepartmentConstraint}
            />
          ) : null}

          {modal.kind === "framework" ? (
            <MobilityCategoryForm
              item={modal.item}
              onCancel={() => setModal(null)}
              onSubmit={submitFramework}
            />
          ) : null}
        </Modal>
      ) : null}
      {confirmDialog}
    </>
  );
}

function ExcelImportButton({
  isLoading,
  onDownloadTemplate,
  onImport,
}: {
  isLoading: boolean;
  onDownloadTemplate: () => void;
  onImport: (file: File) => void;
}) {
  return (
    <div className="flex items-center gap-1">
      <button
        className="inline-flex items-center gap-1.5 rounded-l-md border border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
        disabled={isLoading}
        onClick={onDownloadTemplate}
        title="Telecharger le template Excel"
        type="button"
      >
        ↓ Template
      </button>
      <label
        className={`inline-flex cursor-pointer items-center gap-1.5 rounded-r-md border border-l-0 border-gray-300 bg-white px-3 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 ${
          isLoading ? "cursor-not-allowed opacity-60" : ""
        }`}
        title="Importer depuis Excel"
      >
        <input
          accept=".xlsx,.xls"
          className="sr-only"
          disabled={isLoading}
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) {
              onImport(file);
              e.target.value = "";
            }
          }}
          type="file"
        />
        {isLoading ? "Import..." : "↑ Import Excel"}
      </label>
    </div>
  );
}

function AddButton({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button
      className="inline-flex items-center gap-2 rounded-md bg-[#1E3A8A] px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-900"
      onClick={onClick}
      type="button"
    >
      <Plus className="h-4 w-4" aria-hidden="true" />
      {label}
    </button>
  );
}

function SyncButton({
  isLoading,
  label = "Sync MoveON",
  onClick,
}: {
  isLoading: boolean;
  label?: string;
  onClick: () => void;
}) {
  return (
    <button
      className="inline-flex items-center gap-2 rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-60"
      disabled={isLoading}
      onClick={onClick}
      type="button"
    >
      <RefreshCw className={`h-4 w-4 ${isLoading ? "animate-spin" : ""}`} aria-hidden="true" />
      {isLoading ? "Synchronisation..." : label}
    </button>
  );
}

function getModalLabel(kind: ModalState["kind"]) {
  if (kind === "agreement") return "un accord";
  if (kind === "framework") return "un cadre de mobilite";
  if (kind === "levelConstraint") return "une contrainte niveau";
  if (kind === "deptConstraint") return "une contrainte departement";
  return "une repartition departement";
}

function getModalDescription(kind: ModalState["kind"]) {
  if (kind === "agreement") {
    return "Renseignez le partenaire, le cadre, la periode de validite et l'etat actif.";
  }
  if (kind === "framework") {
    return "Definissez le nom, l'identifiant externe et les types de relation du cadre.";
  }
  if (kind === "levelConstraint") {
    return "Choisissez le niveau academique concerne par cet accord.";
  }
  if (kind === "deptConstraint") {
    return "Choisissez le departement concerne par cet accord.";
  }
  return "Repartissez un quota annuel par departement.";
}

function isAgreementAvailableForSelectedYear(
  agreement: Agreement,
  yearFilter: string,
  academicYears: AcademicYear[],
  availabilities: AgreementYearAvailability[],
) {
  const selectedYear = academicYears.find((year) => year.label === yearFilter);
  if (!selectedYear) return agreement.is_active;

  const availability = availabilities.find(
    (item) =>
      item.agreement_id === agreement.id && item.academic_year_label === selectedYear.label,
  );
  if (availability) return availability.is_available;

  return isAgreementValidForYear(agreement, selectedYear);
}

function isAgreementValidForYear(agreement: Agreement, academicYear: AcademicYear) {
  if (!agreement.is_active) return false;
  if (
    ["closed", "archived", "inactive", "termine"].includes(
      (agreement.status ?? "").toLowerCase(),
    )
  ) {
    return false;
  }
  if (agreement.start_date && agreement.start_date > academicYear.end_date) return false;
  if (agreement.end_date && agreement.end_date < academicYear.start_date) return false;
  return true;
}

function distributePlaces(totalPlaces: number, bucketCount: number) {
  if (bucketCount <= 0) return [];
  const base = Math.floor(totalPlaces / bucketCount);
  const remainder = totalPlaces % bucketCount;
  return Array.from(
    { length: bucketCount },
    (_, index) => base + (index < remainder ? 1 : 0),
  );
}

function getQuotaValidationError(
  quota: AgreementQuota,
  departmentQuotas: DepartmentQuota[],
) {
  if (quota.source_total_places !== null && quota.total_places > quota.source_total_places) {
    return "Le quota N7 ne peut pas etre superieur au quota INP.";
  }

  const departmentTotal = departmentQuotas
    .filter((item) => item.agreement_quota_id === quota.id)
    .reduce((total, item) => total + item.places, 0);

  if (departmentTotal !== quota.total_places) {
    return "La somme des quotas departements doit etre egale au quota N7 avant validation.";
  }

  return "";
}

function getSyncFingerprint(
  agreements: Agreement[],
  quotas: AgreementQuota[],
  availabilities: AgreementYearAvailability[],
  departmentQuotas: DepartmentQuota[],
  errors: RawImport[],
) {
  return JSON.stringify({
    agreements: agreements.map((item) => ({ id: item.id, updated_at: item.updated_at })),
    availabilities: availabilities.map((item) => ({
      id: item.id,
      is_available: item.is_available,
      updated_at: item.updated_at,
    })),
    departmentQuotas: departmentQuotas.map((item) => ({
      id: item.id,
      updated_at: item.updated_at,
    })),
    errors: errors.map((item) => ({ id: item.id, status: item.status })),
    quotas: quotas.map((item) => ({ id: item.id, updated_at: item.updated_at })),
  });
}

function LevelConstraintForm({
  agreementId,
  mobilityLevels,
  onCancel,
  onSubmit,
}: {
  agreementId: number;
  mobilityLevels: Level[];
  onCancel: () => void;
  onSubmit: (agreementId: number, levelId: number) => Promise<void>;
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    const formData = new FormData(event.currentTarget);
    const levelId = Number(formData.get("level_id") || 0);
    if (!levelId) {
      setError("Veuillez choisir un niveau.");
      setIsSubmitting(false);
      return;
    }
    try {
      await onSubmit(agreementId, levelId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible d'enregistrer la contrainte.");
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Niveau</span>
        <select
          className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
          defaultValue=""
          name="level_id"
          required
        >
          <option value="">Choisir un niveau</option>
          {mobilityLevels.filter((l) => l.is_active).map((level) => (
            <option key={level.id} value={level.id}>
              {level.code} — {level.name}
            </option>
          ))}
        </select>
      </label>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="flex justify-end gap-3 border-t border-gray-200 pt-5">
        <button
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          onClick={onCancel}
          type="button"
        >
          Annuler
        </button>
        <button
          className="rounded-md bg-[#1E3A8A] px-4 py-2 text-sm font-medium text-white hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSubmitting}
          type="submit"
        >
          Enregistrer
        </button>
      </div>
    </form>
  );
}

function DepartmentConstraintForm({
  agreementId,
  departments,
  onCancel,
  onSubmit,
}: {
  agreementId: number;
  departments: Department[];
  onCancel: () => void;
  onSubmit: (agreementId: number, departmentId: number) => Promise<void>;
}) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(event: React.SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    setError(null);
    setIsSubmitting(true);
    const formData = new FormData(event.currentTarget);
    const departmentId = Number(formData.get("department_id") || 0);
    if (!departmentId) {
      setError("Veuillez choisir un departement.");
      setIsSubmitting(false);
      return;
    }
    try {
      await onSubmit(agreementId, departmentId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Impossible d'enregistrer la contrainte.");
      setIsSubmitting(false);
    }
  }

  return (
    <form className="space-y-5" onSubmit={handleSubmit}>
      <label className="block">
        <span className="text-sm font-medium text-gray-700">Departement</span>
        <select
          className="mt-1 w-full rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A]"
          defaultValue=""
          name="department_id"
          required
        >
          <option value="">Choisir un departement</option>
          {departments.map((dept) => (
            <option key={dept.id} value={dept.id}>
              {dept.code} — {dept.name}
            </option>
          ))}
        </select>
      </label>

      {error ? (
        <div className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
        </div>
      ) : null}

      <div className="flex justify-end gap-3 border-t border-gray-200 pt-5">
        <button
          className="rounded-md border border-gray-300 bg-white px-4 py-2 text-sm font-medium text-gray-700 hover:bg-gray-50"
          onClick={onCancel}
          type="button"
        >
          Annuler
        </button>
        <button
          className="rounded-md bg-[#1E3A8A] px-4 py-2 text-sm font-medium text-white hover:bg-blue-900 disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSubmitting}
          type="submit"
        >
          Enregistrer
        </button>
      </div>
    </form>
  );
}

function delay(ms: number) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

const FW_PAGE_SIZE_OPTIONS = [5, 10, 15, 20];

function MobilityCategoriesTable({
  frameworks,
  onDelete,
  onEdit,
}: {
  frameworks: MobilityCategory[];
  onDelete: (fw: MobilityCategory) => void;
  onEdit: (fw: MobilityCategory) => void;
}) {
  const [page, setPage] = useState(0);
  const [pageSize, setPageSize] = useState(10);

  const totalPages = Math.max(1, Math.ceil(frameworks.length / pageSize));
  const pageItems = frameworks.slice(page * pageSize, (page + 1) * pageSize);

  if (frameworks.length === 0) {
    return (
      <div className="rounded-md border border-dashed border-gray-300 px-4 py-8 text-center text-sm text-gray-500">
        Aucun cadre de mobilite. Ajoutez-en un ou lancez une synchronisation MoveON.
      </div>
    );
  }

  const pageNumbers = buildFwPageNumbers(page, totalPages);

  return (
    <div className="space-y-3">
      <div className="divide-y divide-gray-100 rounded-md border border-gray-200 bg-white">
        {pageItems.map((fw) => (
          <div key={fw.id} className="flex flex-wrap items-center gap-x-6 gap-y-2 px-4 py-3 hover:bg-gray-50/50">
            <div className="min-w-0 flex-[3]">
              <p className="font-medium text-gray-900 text-sm">{fw.name}</p>
              <p className="mt-0.5 font-mono text-xs text-gray-400">{fw.moveon_framework_id}</p>
            </div>
            <div className="flex-[3] text-sm text-gray-600">
              {fw.relation_types || <span className="text-xs text-gray-400 italic">—</span>}
            </div>
            <div className="flex flex-1 items-center justify-end gap-3 min-w-40">
              <span
                className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${
                  fw.is_active ? "bg-emerald-50 text-emerald-700" : "bg-gray-100 text-gray-500"
                }`}
              >
                {fw.is_active ? "Actif" : "Inactif"}
              </span>
              {fw.last_sync_moveon ? (
                <span className="text-xs text-gray-400">
                  Sync {new Date(fw.last_sync_moveon).toLocaleDateString("fr-FR")}
                </span>
              ) : null}
              <ActionButtons onEdit={() => onEdit(fw)} onDelete={() => onDelete(fw)} />
            </div>
          </div>
        ))}
      </div>

      <div className="flex items-center justify-between px-1 text-sm text-gray-600">
        <span>
          {frameworks.length} cadre{frameworks.length > 1 ? "s" : ""}
          {` — page ${page + 1} / ${totalPages}`}
        </span>
        <div className="flex items-center gap-3">
          <select
            className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs text-gray-700 focus:outline-none focus:ring-1 focus:ring-[#1E3A8A]"
            onChange={(e) => { setPageSize(Number(e.target.value)); setPage(0); }}
            value={pageSize}
          >
            {FW_PAGE_SIZE_OPTIONS.map((s) => (
              <option key={s} value={s}>{s} / page</option>
            ))}
          </select>
          <div className="flex items-center gap-1">
            <FwNavBtn disabled={page === 0} label="«" onClick={() => setPage(0)} title="Premiere page" />
            <FwNavBtn disabled={page === 0} label="‹" onClick={() => setPage((p) => p - 1)} title="Page precedente" />
            {pageNumbers.map((p, i) =>
              p === "..." ? (
                <span key={`ellipsis-${i}`} className="px-1 text-xs text-gray-400">…</span>
              ) : (
                <button
                  key={p}
                  className={`min-w-[2rem] rounded-md border px-2 py-1 text-xs font-medium ${
                    p === page
                      ? "border-[#1E3A8A] bg-[#1E3A8A] text-white"
                      : "border-gray-200 bg-white text-gray-700 hover:bg-gray-50"
                  }`}
                  onClick={() => setPage(p as number)}
                  type="button"
                >
                  {(p as number) + 1}
                </button>
              ),
            )}
            <FwNavBtn disabled={page >= totalPages - 1} label="›" onClick={() => setPage((p) => p + 1)} title="Page suivante" />
            <FwNavBtn disabled={page >= totalPages - 1} label="»" onClick={() => setPage(totalPages - 1)} title="Derniere page" />
          </div>
        </div>
      </div>
    </div>
  );
}

function FwNavBtn({ disabled, label, onClick, title }: { disabled: boolean; label: string; onClick: () => void; title: string }) {
  return (
    <button
      className="rounded-md border border-gray-200 bg-white px-2 py-1 text-xs font-medium text-gray-700 hover:bg-gray-50 disabled:cursor-not-allowed disabled:opacity-40"
      disabled={disabled}
      onClick={onClick}
      title={title}
      type="button"
    >
      {label}
    </button>
  );
}

function buildFwPageNumbers(current: number, total: number): (number | "...")[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i);
  const pages: (number | "...")[] = [];
  const add = (p: number) => { if (!pages.includes(p)) pages.push(p); };
  add(0);
  if (current > 3) pages.push("...");
  for (let p = Math.max(1, current - 2); p <= Math.min(total - 2, current + 2); p++) add(p);
  if (current < total - 4) pages.push("...");
  add(total - 1);
  return pages;
}
