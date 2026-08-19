import type { ButtonHTMLAttributes, ReactNode } from "react";

const BASE =
  "inline-flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors disabled:cursor-not-allowed disabled:opacity-60";

const VARIANTS = {
  ghost:   `${BASE} border border-gray-300 bg-white text-gray-700 hover:bg-gray-50`,
  primary: `${BASE} bg-[#1E3A8A] text-white hover:bg-blue-900`,
  success: `${BASE} border border-emerald-600 bg-emerald-50 text-emerald-700 hover:bg-emerald-100`,
  danger:  `${BASE} border border-red-300 bg-white text-red-700 hover:bg-red-50`,
} as const;

type Variant = keyof typeof VARIANTS;

export function Btn({
  variant = "ghost",
  className = "",
  children,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant; children: ReactNode }) {
  return (
    <button className={`${VARIANTS[variant]} ${className}`.trim()} type="button" {...props}>
      {children}
    </button>
  );
}

/** Wrapper <label> stylé comme un bouton pour les inputs de type file */
export function FileBtn({
  variant = "ghost",
  disabled,
  accept = ".xlsx,.xls",
  onFile,
  children,
  className = "",
}: Readonly<{
  variant?: Variant;
  disabled?: boolean;
  accept?: string;
  onFile: (file: File) => void;
  children: ReactNode;
  className?: string;
}>) {
  return (
    <label
      className={`cursor-pointer ${VARIANTS[variant]} ${disabled ? "cursor-not-allowed opacity-60 pointer-events-none" : ""} ${className}`.trim()}
    >
      <input
        accept={accept}
        className="sr-only"
        disabled={disabled}
        onChange={(e) => {
          const f = e.target.files?.[0];
          if (f) { onFile(f); e.target.value = ""; }
        }}
        type="file"
      />
      {children}
    </label>
  );
}
