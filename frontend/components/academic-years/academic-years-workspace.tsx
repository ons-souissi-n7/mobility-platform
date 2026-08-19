"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

import { AcademicYearForm } from "@/components/academic-years/academic-year-form";
import { AcademicYearsTable } from "@/components/academic-years/academic-years-table";
import { ErrorBanner } from "@/components/ui/alert";
import { Btn } from "@/components/ui/btn";
import { useConfirm } from "@/components/ui/confirm-dialog";
import { Modal } from "@/components/ui/modal";
import {
  applyAcademicYearTransition,
  createAcademicYear,
  deleteAcademicYear,
  updateAcademicYear,
  type AcademicYearPayload,
  type AcademicYearTransition,
} from "@/lib/api/academic-year-mutations";
import type { AcademicYear } from "@/lib/api/types";
import { nextTransitions } from "@/components/academic-years/status";

type AcademicYearsWorkspaceProps = {
  years: AcademicYear[];
};

export function AcademicYearsWorkspace({
  years: initialYears,
}: Readonly<AcademicYearsWorkspaceProps>) {
  const [years, setYears] = useState(initialYears);
  const [modalItem, setModalItem] = useState<AcademicYear | null | "new">(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const { confirm, dialog: confirmDialog } = useConfirm();

  async function submitYear(payload: AcademicYearPayload) {
    if (modalItem && modalItem !== "new") {
      const updated = await updateAcademicYear(modalItem.id, payload);
      setYears((items) =>
        items.map((item) => (item.id === updated.id ? updated : item)),
      );
    } else {
      const created = await createAcademicYear(payload);
      setYears((items) => [created, ...items]);
    }

    setModalItem(null);
  }

  async function removeYear(year: AcademicYear) {
    if (!await confirm(`Supprimer l'annee universitaire "${year.label}" ?`)) return;
    setActionError(null);
    try {
      await deleteAcademicYear(year.id);
      setYears((items) => items.filter((item) => item.id !== year.id));
    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Impossible de supprimer l'annee universitaire.",
      );
    }
  }

  async function transitionYear(
    year: AcademicYear,
    transition: AcademicYearTransition,
  ) {
    if (transition === "complete-assignment") {
      const ok = await confirm(
        `Forcer la transition de « ${year.label} » de l'état Affectation vers Validation ?\n\nUtilisez cette action uniquement si l'algorithme Gale-Shapley a terminé mais la transition automatique a échoué.`,
        "Récupérer la transition",
      );
      if (!ok) return;
    } else {
      const next = nextTransitions[year.status];
      if (next?.confirmMessage) {
        const ok = await confirm(next.confirmMessage, next.label);
        if (!ok) return;
      }
    }
    setActionError(null);
    try {
      const updated = await applyAcademicYearTransition(year.id, transition);
      setYears((items) =>
        items.map((item) => (item.id === updated.id ? updated : item)),
      );

    } catch (err) {
      setActionError(
        err instanceof Error ? err.message : "Impossible d'appliquer la transition.",
      );
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <Btn variant="primary" onClick={() => setModalItem("new")}>
          <Plus className="h-4 w-4" />
          Ajouter une année
        </Btn>
      </div>

      <ErrorBanner message={actionError} onDismiss={() => setActionError(null)} />

      <AcademicYearsTable
        onDelete={removeYear}
        onEdit={(year) => setModalItem(year)}
        onTransition={transitionYear}
        years={years}
      />

      {modalItem ? (
        <Modal
          description="Configurez les dates de campagne et les jalons de l'annee."
          onClose={() => setModalItem(null)}
          title={
            modalItem === "new"
              ? "Ajouter une annee universitaire"
              : `Modifier ${modalItem.label}`
          }
        >
          <AcademicYearForm
            item={modalItem === "new" ? undefined : modalItem}
            onCancel={() => setModalItem(null)}
            onSubmit={submitYear}
          />
        </Modal>
      ) : null}
      {confirmDialog}
    </div>
  );
}
