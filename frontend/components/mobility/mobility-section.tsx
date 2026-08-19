import type { ReactNode } from "react";

export function MobilitySection({
  children,
  description,
  id,
  title,
  toolbar,
}: Readonly<{
  children: ReactNode;
  description: string;
  id?: string;
  title: string;
  toolbar?: ReactNode;
}>) {
  return (
    <section id={id} className="space-y-4">
      <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold text-gray-900">{title}</h2>
          <p className="mt-1 text-sm text-gray-500">{description}</p>
        </div>
        {toolbar ? <div className="flex shrink-0 gap-2">{toolbar}</div> : null}
      </div>
      {children}
    </section>
  );
}
