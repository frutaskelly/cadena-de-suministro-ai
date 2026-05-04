"use client";

import { useEffect, useState } from "react";
import { getTenantId, setTenantId, clearTenantId } from "@/lib/api";

export default function Topbar({ title }: { title: string }) {
  const [tenant, setTenant] = useState<string | null>(null);
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState("");

  useEffect(() => {
    const t = getTenantId();
    setTenant(t);
    if (t) setDraft(t);
  }, []);

  function save() {
    if (!draft.trim()) return;
    setTenantId(draft.trim());
    setTenant(draft.trim());
    setEditing(false);
  }

  function clear() {
    clearTenantId();
    setTenant(null);
    setDraft("");
    setEditing(true);
  }

  return (
    <header
      className="sticky top-0 z-30 backdrop-blur-md border-b"
      style={{
        background: "rgba(255, 255, 255, 0.78)",
        borderColor: "var(--border-subtle)",
      }}
    >
      <div className="flex items-center justify-between h-14 px-7">
        <h1 className="text-title">{title}</h1>
        <div className="flex items-center gap-2">
          {editing || !tenant ? (
            <>
              <input
                className="input"
                style={{ width: 320, fontFamily: "ui-monospace, monospace", fontSize: 12 }}
                placeholder="tenant_id (UUID)"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter") save();
                }}
                autoFocus
              />
              <button className="btn-primary" onClick={save}>
                Guardar
              </button>
              {tenant && (
                <button className="btn-ghost" onClick={() => setEditing(false)}>
                  Cancelar
                </button>
              )}
            </>
          ) : (
            <>
              <div className="flex items-center gap-2 px-3 py-1.5 card-soft">
                <span
                  className="w-1.5 h-1.5 rounded-full"
                  style={{ background: "#34c759" }}
                />
                <span
                  className="font-mono text-[11px]"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {tenant.slice(0, 8)}…{tenant.slice(-4)}
                </span>
              </div>
              <button className="btn-ghost" onClick={() => setEditing(true)}>
                Cambiar
              </button>
              <button className="btn-ghost" onClick={clear}>
                Salir
              </button>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
