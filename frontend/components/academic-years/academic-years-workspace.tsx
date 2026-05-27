"use client";

import { Plus } from "lucide-react";
import { useState } from "react";

import { AcademicYearForm } from "@/components/academic-years/academic-year-form";
import { AcademicYearsTable } from "@/components/academic-years/academic-years-table";
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

type AcademicYearsWorkspaceProps = {
  years: AcademicYear[];
};

export function AcademicYearsWorkspace({
  years: initialYears,
}: AcademicYearsWorkspaceProps) {
  const [years, setYears] = useState(initialYears);
  const [modalItem, setModalItem] = useState<AcademicYear | null | "new">(null);
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

    await deleteAcademicYear(year.id);
    setYears((items) => items.filter((item) => item.id !== year.id));
  }

  async function transitionYear(
    year: AcademicYear,
    transition: AcademicYearTransition,
  ) {
    const updated = await applyAcademicYearTransition(year.id, transition);
    setYears((items) =>
      items.map((item) => (item.id === updated.id ? updated : item)),
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex justify-end">
        <button
          className="inline-flex items-center gap-2 rounded-md bg-[#1E3A8A] px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-900"
          onClick={() => setModalItem("new")}
          type="button"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Ajouter une annee
        </button>
      </div>

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
