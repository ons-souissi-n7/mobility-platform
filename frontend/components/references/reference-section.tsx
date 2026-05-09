import type { ReactNode } from "react";

type ReferenceSectionProps = {
  title: string;
  description: string;
  toolbar?: ReactNode;
  children: ReactNode;
};

export function ReferenceSection({
  title,
  description,
  toolbar,
  children,
}: ReferenceSectionProps) {
  return (
    <section className="space-y-4">
      <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
        <div>
          <h2 className="text-lg font-bold text-gray-900">{title}</h2>
          <p className="mt-1 text-sm text-gray-500">{description}</p>
        </div>
        {toolbar}
      </div>
      {children}
    </section>
  );
}
