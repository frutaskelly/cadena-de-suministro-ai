"use client";

import { ChatConversacion } from "@/lib/types";
import { fmtDateTime } from "@/lib/api";

export default function ChatSidebar({
  conversaciones,
  activeId,
  onSelect,
  onNew,
  onDelete,
  loading,
}: {
  conversaciones: ChatConversacion[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onNew: () => void;
  onDelete: (id: string) => void;
  loading?: boolean;
}) {
  return (
    <aside
      className="w-72 border-r flex flex-col flex-shrink-0"
      style={{
        borderColor: "var(--border-subtle)",
        background: "var(--surface)",
      }}
    >
      <div className="p-3 border-b" style={{ borderColor: "var(--border-subtle)" }}>
        <button
          onClick={onNew}
          className="w-full btn-primary justify-center"
          style={{ width: "100%" }}
        >
          + Nueva conversación
        </button>
      </div>

      <div className="flex-1 overflow-y-auto py-2">
        {loading && (
          <div className="px-3 py-2 text-caption">Cargando…</div>
        )}
        {!loading && conversaciones.length === 0 && (
          <div className="px-3 py-4 text-caption text-center">
            Sin conversaciones aún.
            <br />
            Crea una nueva para empezar.
          </div>
        )}
        {conversaciones.map((c) => (
          <div
            key={c.id}
            onClick={() => onSelect(c.id)}
            className={
              "group cursor-pointer px-3 py-2.5 mx-2 my-0.5 rounded-lg transition-all " +
              (activeId === c.id ? "bg-[var(--surface-2)]" : "hover:bg-[var(--surface)]")
            }
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1 min-w-0">
                <div
                  className={
                    "text-[13px] truncate " +
                    (activeId === c.id ? "font-medium" : "")
                  }
                >
                  {c.titulo}
                </div>
                <div
                  className="text-[11px] mt-0.5"
                  style={{ color: "var(--text-tertiary)" }}
                >
                  {c.mensajes_count} msgs · {fmtDateTime(c.ultima_actividad)}
                </div>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm("¿Borrar esta conversación?")) onDelete(c.id);
                }}
                className="opacity-0 group-hover:opacity-60 hover:!opacity-100 text-[11px] px-1"
                style={{
                  color: "var(--text-tertiary)",
                  background: "transparent",
                  border: "none",
                }}
                aria-label="Borrar conversación"
                title="Borrar"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>
    </aside>
  );
}
