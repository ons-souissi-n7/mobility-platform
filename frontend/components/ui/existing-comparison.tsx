"use client";

function renderVal(v: unknown): string {
  if (v === null || v === undefined || v === "") return "—";
  if (Array.isArray(v)) return v.length ? v.join(", ") : "—";
  if (typeof v === "object") {
    const obj = v as Record<string, unknown>;
    return obj.name ? String(obj.name) : JSON.stringify(v);
  }
  return String(v);
}

export function ExistingComparisonView({
  newData,
  existingData,
  labels = {},
}: Readonly<{
  newData: Record<string, unknown>;
  existingData: Record<string, unknown>;
  labels?: Record<string, string>;
}>) {
  const keys = Array.from(
    new Set([
      ...Object.keys(newData).filter((k) => k !== "_existing"),
      ...Object.keys(existingData),
    ])
  );

  return (
    <div className="overflow-x-auto rounded-md border border-gray-200">
      <table className="w-full border-collapse text-xs">
        <thead>
          <tr className="border-b border-gray-200 bg-gray-50">
            <th className="w-1/3 px-3 py-2 text-left font-semibold text-gray-500">
              Champ
            </th>
            <th className="w-1/3 px-3 py-2 text-left font-semibold text-blue-700">
              Source (import)
            </th>
            <th className="w-1/3 px-3 py-2 text-left font-semibold text-amber-700">
              En base actuellement
            </th>
          </tr>
        </thead>
        <tbody>
          {keys.map((key) => {
            const nv = renderVal(newData[key]);
            const ev = renderVal(existingData[key]);
            const differs = nv !== ev && nv !== "—" && ev !== "—";
            return (
              <tr key={key} className={differs ? "bg-amber-50" : ""}>
                <td className="border-b border-gray-100 px-3 py-1.5 font-medium text-gray-500">
                  {labels[key] ?? key}
                </td>
                <td
                  className={`break-all border-b border-gray-100 px-3 py-1.5 font-mono ${
                    differs ? "font-semibold text-blue-700" : "text-gray-700"
                  }`}
                >
                  {nv}
                </td>
                <td
                  className={`break-all border-b border-gray-100 px-3 py-1.5 font-mono ${
                    differs ? "font-semibold text-amber-700" : "text-gray-700"
                  }`}
                >
                  {ev}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
