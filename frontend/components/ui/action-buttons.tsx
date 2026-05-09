import { Pencil, Trash2 } from "lucide-react";

type ActionButtonsProps = {
  onEdit: () => void;
  onDelete: () => void;
};

export function ActionButtons({ onEdit, onDelete }: ActionButtonsProps) {
  return (
    <div className="flex items-center justify-end gap-2">
      <button
        className="inline-flex items-center gap-1.5 rounded-md border border-gray-200 bg-white px-3 py-1.5 text-xs font-medium text-gray-700 transition-colors hover:bg-blue-50 hover:text-[#1E3A8A]"
        onClick={onEdit}
        title="Modifier"
        type="button"
      >
        <Pencil className="h-4 w-4" aria-hidden="true" />
        Modifier
      </button>
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
