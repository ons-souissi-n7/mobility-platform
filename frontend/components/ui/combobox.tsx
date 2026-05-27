"use client";

import { useMemo, useState } from "react";

export type ComboboxOption = {
  id: number;
  label: string;
  keywords?: string;
};

export function Combobox({
  disabled = false,
  label,
  onChange,
  options,
  placeholder = "Rechercher...",
  required = false,
  value,
}: {
  label: string;
  options: ComboboxOption[];
  value: number | null;
  onChange: (value: number | null) => void;
  placeholder?: string;
  required?: boolean;
  disabled?: boolean;
}) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);

  const selected = useMemo(
    () => (value == null ? null : options.find((option) => option.id === value) ?? null),
    [options, value],
  );

  const normalizedQuery = query.trim().toLowerCase();
  const filtered = useMemo(() => {
    if (!normalizedQuery) return options.slice(0, 50);
    return options
      .filter((option) => {
        const haystack = `${option.label} ${option.keywords ?? ""}`.toLowerCase();
        return haystack.includes(normalizedQuery);
      })
      .slice(0, 50);
  }, [normalizedQuery, options]);

  function commit(option: ComboboxOption) {
    onChange(option.id);
    setQuery("");
    setIsOpen(false);
  }

  return (
    <label className="block">
      <span className="text-sm font-medium text-gray-700">{label}</span>
      <div className="relative mt-1">
        <input
          aria-invalid={required && value == null ? true : undefined}
          className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm text-gray-900 focus:border-transparent focus:ring-2 focus:ring-[#1E3A8A] disabled:cursor-not-allowed disabled:bg-gray-50"
          disabled={disabled}
          onBlur={() => {
            // Let clicks on options register before closing.
            window.setTimeout(() => setIsOpen(false), 150);
          }}
          onChange={(event) => {
            setQuery(event.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder={selected ? selected.label : placeholder}
          value={query}
        />

        {value != null ? (
          <button
            className="absolute right-2 top-1/2 -translate-y-1/2 text-xs text-gray-500 hover:text-gray-700"
            onClick={(event) => {
              event.preventDefault();
              onChange(null);
              setQuery("");
            }}
            type="button"
          >
            Effacer
          </button>
        ) : null}

        {isOpen ? (
          <div className="absolute z-20 mt-1 max-h-64 w-full overflow-auto rounded-md border border-gray-200 bg-white shadow-lg">
            {filtered.length ? (
              filtered.map((option) => (
                <button
                  className="block w-full px-3 py-2 text-left text-sm text-gray-900 hover:bg-gray-50"
                  key={option.id}
                  onMouseDown={(event) => {
                    event.preventDefault();
                    commit(option);
                  }}
                  type="button"
                >
                  {option.label}
                </button>
              ))
            ) : (
              <div className="px-3 py-2 text-sm text-gray-500">Aucun resultat</div>
            )}
          </div>
        ) : null}
      </div>

      {selected ? (
        <div className="mt-1 text-xs text-gray-500">Selection: {selected.label}</div>
      ) : null}
    </label>
  );
}

