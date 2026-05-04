"use client";

import { useState } from "react";

export type DateRange = {
  desde: string; // ISO YYYY-MM-DD
  hasta: string;
  label: string;
};

type Preset = "este_mes" | "mes_pasado" | "ultimos_30" | "rango";

function pad(n: number): string {
  return String(n).padStart(2, "0");
}
function iso(d: Date): string {
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}`;
}

export function getPresetRange(preset: Preset): DateRange | null {
  const today = new Date();
  if (preset === "este_mes") {
    const start = new Date(today.getFullYear(), today.getMonth(), 1);
    return { desde: iso(start), hasta: iso(today), label: "Este mes" };
  }
  if (preset === "mes_pasado") {
    const start = new Date(today.getFullYear(), today.getMonth() - 1, 1);
    const end = new Date(today.getFullYear(), today.getMonth(), 0);
    return { desde: iso(start), hasta: iso(end), label: "Mes pasado" };
  }
  if (preset === "ultimos_30") {
    const start = new Date();
    start.setDate(today.getDate() - 30);
    return { desde: iso(start), hasta: iso(today), label: "Últimos 30 días" };
  }
  return null;
}

export default function DateRangePicker({
  value,
  onChange,
}: {
  value: DateRange;
  onChange: (range: DateRange) => void;
}) {
  const [activePreset, setActivePreset] = useState<Preset>("este_mes");
  const isCustom = activePreset === "rango";

  function applyPreset(p: Preset) {
    setActivePreset(p);
    if (p === "rango") return;
    const r = getPresetRange(p);
    if (r) onChange(r);
  }

  function applyCustom(desde: string, hasta: string) {
    onChange({ desde, hasta, label: `${desde} → ${hasta}` });
  }

  return (
    <div className="flex items-center gap-2">
      <div
        className="flex items-center rounded-xl p-0.5"
        style={{ background: "var(--surface-2)" }}
      >
        {[
          { id: "este_mes" as const, label: "Este mes" },
          { id: "mes_pasado" as const, label: "Mes pasado" },
          { id: "ultimos_30" as const, label: "Últimos 30" },
          { id: "rango" as const, label: "Rango" },
        ].map((opt) => (
          <button
            key={opt.id}
            onClick={() => applyPreset(opt.id)}
            className="px-3 py-1.5 text-[12px] font-medium rounded-lg transition-all"
            style={
              activePreset === opt.id
                ? {
                    background: "var(--background)",
                    color: "var(--foreground)",
                    boxShadow: "0 1px 2px rgba(0,0,0,0.06)",
                  }
                : {
                    background: "transparent",
                    color: "var(--text-secondary)",
                    border: "none",
                  }
            }
          >
            {opt.label}
          </button>
        ))}
      </div>

      {isCustom && (
        <div className="flex items-center gap-1.5">
          <input
            type="date"
            className="input"
            style={{ width: 145 }}
            value={value.desde}
            onChange={(e) => applyCustom(e.target.value, value.hasta)}
            aria-label="Desde"
          />
          <span className="text-caption">→</span>
          <input
            type="date"
            className="input"
            style={{ width: 145 }}
            value={value.hasta}
            onChange={(e) => applyCustom(value.desde, e.target.value)}
            aria-label="Hasta"
          />
        </div>
      )}
    </div>
  );
}
