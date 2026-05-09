import type { ReactNode } from "react";
import { X } from "lucide-react";

type ModalProps = {
  title: string;
  description: string;
  children: ReactNode;
  onClose: () => void;
};

export function Modal({ title, description, children, onClose }: ModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-900/40 px-4">
      <div className="max-h-[90vh] w-full max-w-2xl overflow-y-auto rounded-lg bg-white shadow-xl">
        <div className="flex items-start justify-between border-b border-gray-200 px-6 py-5">
          <div>
            <h2 className="text-lg font-bold text-gray-900">{title}</h2>
            <p className="mt-1 text-sm text-gray-500">{description}</p>
          </div>
          <button
            className="rounded-md p-2 text-gray-400 transition-colors hover:bg-gray-100 hover:text-gray-700"
            onClick={onClose}
            title="Fermer"
            type="button"
          >
            <X className="h-5 w-5" aria-hidden="true" />
          </button>
        </div>
        <div className="px-6 py-5">{children}</div>
      </div>
    </div>
  );
}
