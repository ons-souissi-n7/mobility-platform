import { Pencil, Trash2 } from "lucide-react";

type ActionButtonsProps = {
  onEdit?: () => void;
  editDisabled?: boolean;
  editDisabledTitle?: string;
  onDelete?: () => void;
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
}: Readonly<ActionButtonsProps>) {
  const isEditDisabled = editDisabled || !onEdit;

  return (
    <div className="flex items-center justify-end gap-1">
      {onEdit !== undefined && (
        <button
          className={`rounded-md p-1.5 transition-colors ${
            isEditDisabled
              ? "cursor-not-allowed text-gray-200"
              : "text-gray-400 hover:bg-gray-100 hover:text-gray-700"
          }`}
          disabled={isEditDisabled}
          onClick={isEditDisabled ? undefined : onEdit}
          title={isEditDisabled ? editDisabledTitle : "Modifier"}
          type="button"
        >
          <Pencil size={15} aria-hidden="true" />
        </button>
      )}
      {onDelete !== undefined && (
        <button
          className={`rounded-md p-1.5 transition-colors ${
            deleteDisabled
              ? "cursor-not-allowed text-gray-200"
              : "text-gray-400 hover:bg-red-50 hover:text-red-600"
          }`}
          disabled={deleteDisabled}
          onClick={deleteDisabled ? undefined : onDelete}
          title={deleteDisabled ? deleteDisabledTitle : "Supprimer"}
          type="button"
        >
          <Trash2 size={15} aria-hidden="true" />
        </button>
      )}
    </div>
  );
}
