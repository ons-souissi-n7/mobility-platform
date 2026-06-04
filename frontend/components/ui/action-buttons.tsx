import { Lock, Pencil, Trash2 } from "lucide-react";

type ActionButtonsProps = {
  onEdit?: () => void;
  onDelete: () => void;
  editDisabledTitle?: string;
};

export function ActionButtons({
  onEdit,
  onDelete,
  editDisabledTitle = "Non modifiable",
}: ActionButtonsProps) {
  return (
    <div className="flex items-center justify-end gap-2">
      {onEdit ? (
        <button
          className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-blue-50 hover:text-[#1E3A8A]"
          onClick={onEdit}
          title="Modifier"
          type="button"
        >
          <Pencil className="h-4 w-4" aria-hidden="true" />
          Modifier
        </button>
      ) : (
        <button
          className="inline-flex cursor-not-allowed items-center gap-1.5 rounded-md border border-gray-100 bg-gray-50 px-3 py-1.5 text-xs font-medium text-gray-400"
          disabled
          title={editDisabledTitle}
          type="button"
        >
          <Lock className="h-3.5 w-3.5" aria-hidden="true" />
          Verrouillé
        </button>
      )}
      <button
        className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-red-50 hover:text-red-700"
        onClick={onDelete}
        title="Supprimer"
        type="button"
      >
        <Trash2 className="h-4 w-4" aria-hidden="true" />
        Supprimer
      </button>
    </div>
  );
}
