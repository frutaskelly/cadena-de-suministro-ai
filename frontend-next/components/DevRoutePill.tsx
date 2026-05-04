"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

/**
 * Pill flotante en bottom-right que muestra:
 * - Ruta actual (pathname)
 * - Archivo de la page (inferido)
 * - Click: copia path al clipboard
 *
 * Solo visible en development. En produccion retorna null.
 */
export default function DevRoutePill() {
  const pathname = usePathname();
  const [copied, setCopied] = useState(false);
  const [hidden, setHidden] = useState(false);

  // Detectar dev: NEXT_PUBLIC_NODE_ENV o el clasico NODE_ENV
  const isDev =
    process.env.NODE_ENV === "development" ||
    process.env.NEXT_PUBLIC_DEV === "true";

  useEffect(() => {
    setCopied(false);
  }, [pathname]);

  if (!isDev || hidden) return null;

  const fileGuess = pathname === "/" ? "app/page.tsx" : `app${pathname}/page.tsx`;

  async function copyAll() {
    const txt = `${pathname}\n→ ${fileGuess}`;
    try {
      await navigator.clipboard.writeText(txt);
      setCopied(true);
      setTimeout(() => setCopied(false), 1400);
    } catch {
      // ignore
    }
  }

  return (
    <div
      className="fixed bottom-4 right-4 z-[60] select-none"
      style={{ pointerEvents: "auto" }}
    >
      <div
        className="flex items-stretch overflow-hidden"
        style={{
          background: "rgba(29, 29, 31, 0.92)",
          color: "#fff",
          borderRadius: 12,
          backdropFilter: "blur(12px)",
          boxShadow:
            "0 4px 16px rgba(0,0,0,0.18), 0 0 0 1px rgba(255,255,255,0.06) inset",
          fontSize: 11,
          letterSpacing: "-0.005em",
        }}
      >
        <div
          className="flex items-center gap-1.5 px-2.5 py-1.5"
          style={{
            borderRight: "1px solid rgba(255,255,255,0.08)",
          }}
          aria-hidden="true"
        >
          <span
            className="w-1.5 h-1.5 rounded-full"
            style={{ background: "#34c759" }}
          />
          <span style={{ color: "rgba(255,255,255,0.55)", fontWeight: 500 }}>
            DEV
          </span>
        </div>

        <button
          onClick={copyAll}
          className="px-2.5 py-1.5 hover:bg-white/5 transition"
          style={{
            background: "transparent",
            border: "none",
            color: "#fff",
            cursor: "pointer",
            fontFamily: "ui-monospace, monospace",
            fontSize: 11,
            display: "flex",
            alignItems: "center",
            gap: 8,
          }}
          title="Click para copiar path + archivo"
        >
          <span style={{ color: "rgba(255,255,255,0.55)" }}>route</span>
          <span style={{ fontWeight: 500 }}>{pathname}</span>
        </button>

        <button
          onClick={copyAll}
          className="px-2 py-1.5 hover:bg-white/5 transition"
          style={{
            background: "transparent",
            border: "none",
            color: "rgba(255,255,255,0.55)",
            cursor: "pointer",
            fontFamily: "ui-monospace, monospace",
            fontSize: 11,
            borderLeft: "1px solid rgba(255,255,255,0.08)",
          }}
          title={fileGuess}
        >
          <span>{fileGuess.replace("app", "•")}</span>
        </button>

        {copied && (
          <div
            className="px-2 py-1.5"
            style={{
              borderLeft: "1px solid rgba(255,255,255,0.08)",
              color: "#34c759",
              fontWeight: 500,
            }}
          >
            ✓ copiado
          </div>
        )}

        <button
          onClick={() => setHidden(true)}
          className="px-2 hover:bg-white/5 transition"
          style={{
            background: "transparent",
            border: "none",
            color: "rgba(255,255,255,0.4)",
            cursor: "pointer",
            fontSize: 14,
            lineHeight: 1,
            borderLeft: "1px solid rgba(255,255,255,0.08)",
          }}
          aria-label="Ocultar dev pill"
          title="Ocultar (vuelve a aparecer al recargar)"
        >
          ×
        </button>
      </div>
    </div>
  );
}
