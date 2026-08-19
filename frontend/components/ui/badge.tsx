export type BadgeStyle = { label: string; className: string };

/**
 * Generic colored badge.  The `map` object keys are the raw values from the
 * API; each entry defines the display label and Tailwind color classes.
 * Pass `label` to override the map's label (useful when the API already
 * provides a human-readable label, as with import-report sources).
 */
export function Badge({
  value,
  map,
  label,
}: Readonly<{
  value: string;
  map: Record<string, BadgeStyle>;
  label?: string;
}>) {
  const style = map[value] ?? { label: value, className: "bg-gray-100 text-gray-600" };
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${style.className}`}>
      {label ?? style.label}
    </span>
  );
}
