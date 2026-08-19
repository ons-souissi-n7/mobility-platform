"use client";

import { useState, useMemo } from "react";
import type { SelectOption } from "@/lib/api/analytics";

interface Props {
  options: SelectOption[];
  selected: (string | number)[];
  onChange: (selected: (string | number)[]) => void;
  placeholder?: string;
}

export function BreakdownFilter({
  options,
  selected,
  onChange,
  placeholder = "Rechercher…",
}: Readonly<Props>) {
  const [search, setSearch] = useState("");

  const filtered = useMemo(
    () =>
      options.filter((o) =>
        o.label.toLowerCase().includes(search.toLowerCase())
      ),
    [options, search]
  );

  const selectedSet = new Set(selected.map(String));

  function toggle(id: string | number) {
    const key = String(id);
    if (selectedSet.has(key)) {
      onChange(selected.filter((s) => String(s) !== key));
    } else {
      onChange([...selected, id]);
    }
  }

  return (
    <div className="flex flex-col gap-2">
      {/* Barre de recherche */}
      <input
        type="text"
        value={search}
        onChange={(e) => setSearch(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-md border bg-background px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary/30"
      />

      {/* Boutons Tout / Effacer */}
      <div className="flex gap-2">
        <button
          type="button"
          onClick={() => onChange(options.map((o) => o.id))}
          className="flex-1 rounded-md border px-2 py-1 text-xs text-muted-foreground hover:bg-muted transition-colors"
        >
          Tout sélectionner
        </button>
        <button
          type="button"
          onClick={() => onChange([])}
          className="flex-1 rounded-md border px-2 py-1 text-xs text-muted-foreground hover:bg-muted transition-colors"
        >
          Effacer
        </button>
      </div>

      {/* Liste à cocher */}
      <div className="max-h-52 overflow-y-auto rounded-md border bg-background divide-y divide-border">
        {filtered.length === 0 && (
          <p className="px-3 py-2 text-xs text-muted-foreground">
            Aucun résultat
          </p>
        )}
        {filtered.map((opt) => {
          const checked = selectedSet.has(String(opt.id));
          return (
            <label
              key={opt.id}
              className="flex items-start gap-2.5 px-3 py-2 text-sm cursor-pointer hover:bg-muted/50 transition-colors"
            >
              <input
                type="checkbox"
                checked={checked}
                onChange={() => toggle(opt.id)}
                className="mt-0.5 h-3.5 w-3.5 shrink-0 accent-primary"
              />
              <span className={checked ? "font-medium" : "text-muted-foreground"}>
                {opt.label}
              </span>
            </label>
          );
        })}
      </div>

      {/* Compteur */}
      {selected.length > 0 ? (
        <p className="text-xs text-primary font-medium">
          {selected.length} sélectionné{selected.length > 1 ? "s" : ""}
        </p>
      ) : (
        <p className="text-xs text-muted-foreground italic">
          Aucun filtre → top 10 par défaut
        </p>
      )}
    </div>
  );
}
