import { X } from "lucide-react";

export function ErrorBanner({
  message,
  onDismiss,
}: Readonly<{
  message: string | null | undefined;
  onDismiss?: () => void;
}>) {
  if (!message) return null;
  return (
    <div className="flex items-start justify-between gap-3 rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
      <span>{message}</span>
      {onDismiss && (
        <button
          className="shrink-0 text-red-400 hover:text-red-600"
          onClick={onDismiss}
          type="button"
          aria-label="Fermer"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
