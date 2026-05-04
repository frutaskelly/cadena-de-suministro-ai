"use client";

import { useEffect, useRef } from "react";
import { ChatMensaje } from "@/lib/types";
import { fmtDateTime } from "@/lib/api";

export default function ChatThread({
  mensajes,
  loading,
  emptyState,
}: {
  mensajes: ChatMensaje[];
  loading?: boolean;
  emptyState?: React.ReactNode;
}) {
  const endRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth", block: "end" });
  }, [mensajes.length, loading]);

  if (mensajes.length === 0 && !loading) {
    return (
      <div className="flex-1 overflow-y-auto flex items-center justify-center px-7">
        {emptyState ?? (
          <div className="text-center max-w-md">
            <div className="text-headline mb-2">Empezar conversación</div>
            <div className="text-caption">
              Sube un Excel BD, foto de libreta, PDF, o pregunta cualquier cosa
              sobre pedidos, productos, listas de precios.
            </div>
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="flex-1 overflow-y-auto px-7 py-6">
      <div className="max-w-3xl mx-auto space-y-6">
        {mensajes.map((m) => (
          <Message key={m.id} m={m} />
        ))}
        {loading && (
          <div className="flex gap-3">
            <Avatar role="assistant" />
            <div className="flex-1 pt-1.5">
              <div className="inline-block">
                <span
                  className="w-1.5 h-1.5 rounded-full bg-black inline-block mr-1 animate-pulse"
                  style={{ animationDelay: "0s" }}
                />
                <span
                  className="w-1.5 h-1.5 rounded-full bg-black inline-block mr-1 animate-pulse"
                  style={{ animationDelay: "0.15s" }}
                />
                <span
                  className="w-1.5 h-1.5 rounded-full bg-black inline-block animate-pulse"
                  style={{ animationDelay: "0.3s" }}
                />
              </div>
            </div>
          </div>
        )}
        <div ref={endRef} />
      </div>
    </div>
  );
}

function Avatar({ role }: { role: string }) {
  if (role === "user") {
    return (
      <div
        className="w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-semibold flex-shrink-0"
        style={{
          background: "var(--surface-2)",
          color: "var(--text-secondary)",
        }}
        aria-hidden="true"
      >
        Tú
      </div>
    );
  }
  return (
    <div
      className="w-7 h-7 rounded-full flex items-center justify-center text-white text-[11px] font-semibold flex-shrink-0"
      style={{ background: "var(--accent)" }}
      aria-hidden="true"
    >
      AI
    </div>
  );
}

function Message({ m }: { m: ChatMensaje }) {
  return (
    <div className="flex gap-3 fade-in">
      <Avatar role={m.role} />
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-1.5">
          <span className="text-[12px] font-medium">
            {m.role === "user" ? "Tú" : "Asistente"}
          </span>
          <span className="text-[11px]" style={{ color: "var(--text-tertiary)" }}>
            {fmtDateTime(m.created_at)}
          </span>
          {m.accion && (
            <span
              className="text-[10px] uppercase tracking-wider px-2 py-0.5 rounded"
              style={{
                background: "var(--surface-2)",
                color: "var(--text-secondary)",
              }}
            >
              {m.accion}
            </span>
          )}
        </div>

        {/* Adjuntos */}
        {m.adjuntos.length > 0 && (
          <div className="flex flex-wrap gap-2 mb-2">
            {m.adjuntos.map((a, i) => (
              <Attachment key={i} att={a} />
            ))}
          </div>
        )}

        {/* Contenido */}
        <div
          className="text-[14px] leading-relaxed whitespace-pre-wrap break-words"
          style={{ color: "var(--foreground)" }}
        >
          {renderContent(m.contenido)}
        </div>
      </div>
    </div>
  );
}

function Attachment({ att }: { att: { nombre: string; mime: string; size: number; data_b64?: string } }) {
  const isImg = att.mime.startsWith("image/");
  const sizeKB = (att.size / 1024).toFixed(1);

  if (isImg && att.data_b64) {
    return (
      <div className="card p-2" style={{ maxWidth: 280 }}>
        <img
          src={`data:${att.mime};base64,${att.data_b64}`}
          alt={att.nombre}
          className="rounded-lg max-h-48 w-full object-contain"
        />
        <div className="text-[10.5px] mt-1.5 truncate" style={{ color: "var(--text-tertiary)" }}>
          {att.nombre} · {sizeKB} KB
        </div>
      </div>
    );
  }

  // Non-image attachments
  const ext = att.nombre.split(".").pop()?.toUpperCase() || "FILE";
  return (
    <div className="card-soft px-3 py-2 inline-flex items-center gap-2.5" style={{ maxWidth: 280 }}>
      <div
        className="w-9 h-9 rounded-md flex items-center justify-center text-[10px] font-semibold flex-shrink-0"
        style={{
          background: "var(--background)",
          border: "1px solid var(--border-subtle)",
          color: "var(--text-secondary)",
        }}
      >
        {ext}
      </div>
      <div className="min-w-0">
        <div className="text-[12px] font-medium truncate">{att.nombre}</div>
        <div className="text-[10.5px]" style={{ color: "var(--text-tertiary)" }}>
          {sizeKB} KB
        </div>
      </div>
    </div>
  );
}

// minimal markdown-ish: bold **x**, code `x`, blocks ```lang ... ```
function renderContent(text: string): React.ReactNode {
  // Strip the action JSON block from the visible text — we already show it as a badge
  const visible = text.replace(/```action[\s\S]*?```/g, "").trim();
  return visible || text;
}
