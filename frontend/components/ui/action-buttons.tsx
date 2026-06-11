import { Pencil, Trash2 } from "lucide-react";

type ActionButtonsProps = {
  onEdit?: () => void;
  editDisabled?: boolean;
  editDisabledTitle?: string;
  onDelete: () => void;
  deleteDisabled?: boolean;
  deleteDisabledTitle?: string;
};

export function ActionButtons({
  onEdit,
  editDisabled = false,
  editDisabledTitle = "Modification non autorisée",
  onDelete,
  deleteDisabled = false,
  deleteDisabledTitle = "Suppression non autorisée",
}: ActionButtonsProps) {
  const isEditDisabled = editDisabled || !onEdit;

  return (
    <div className="flex items-center justify-end gap-2">
      <button
        className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
          isEditDisabled
            ? "cursor-not-allowed border-gray-100 bg-gray-50 text-gray-300"
            : "border-gray-200 bg-white text-gray-700 hover:bg-blue-50 hover:text-[#1E3A8A]"
        }`}
        disabled={isEditDisabled}
        onClick={isEditDisabled ? undefined : onEdit}
        title={isEditDisabled ? editDisabledTitle : "Modifier"}
        type="button"
      >
        <Pencil className="h-4 w-4" aria-hidden="true" />
        Modifier
      </button>
      <button
        className={`inline-flex items-center gap-1.5 rounded-md border px-3 py-1.5 text-xs font-medium transition-colors ${
          deleteDisabled
            ? "cursor-not-allowed border-gray-100 bg-gray-50 text-gray-300"
            : "border-gray-200 bg-white text-gray-700 hover:bg-red-50 hover:text-red-700"
        }`}
        disabled={deleteDisabled}
        onClick={deleteDisabled ? undefined : onDelete}
        title={deleteDisabled ? deleteDisabledTitle : "Supprimer"}
        type="button"
      >
        <Trash2 className="h-4 w-4" aria-hidden="true" />
        Supprimer
      </button>
    </div>
  );
}
