"use client";

import { useState } from "react";
import Topbar from "@/components/Topbar";
import { Card, PageHeader, NoTenant, ErrorBox } from "@/components/ui";
import { api, getTenantId } from "@/lib/api";

export default function CFDIPage() {
  const [tenant] = useState<string | null>(getTenantId());
  const [pedidoId, setPedidoId] = useState("");
  const [data, setData] = useState<unknown>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function preview() {
    if (!pedidoId.trim()) return;
    setLoading(true);
    setError(null);
    setData(null);
    try {
      const d = await api(`/api/v1/pedidos/${pedidoId.trim()}/cfdi-preview`);
      setData(d);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  }

  return (
    <>
      <Topbar title="CFDI Preview" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="CFDI 4.0 Preview"
              description="Genera el payload Facturama para un pedido sin timbrar"
            />

            <Card padding="p-5" className="mb-5">
              <div className="flex gap-2 items-end">
                <div className="flex-1">
                  <div className="text-overline mb-1.5">Pedido ID</div>
                  <input
                    className="input"
                    placeholder="UUID del pedido (copia desde /pedidos)"
                    value={pedidoId}
                    onChange={(e) => setPedidoId(e.target.value)}
                    style={{ fontFamily: "ui-monospace, monospace", fontSize: 12 }}
                  />
                </div>
                <button
                  className="btn-primary"
                  onClick={preview}
                  disabled={loading || !pedidoId.trim()}
                >
                  {loading ? "Generando…" : "Generar preview"}
                </button>
              </div>
            </Card>

            {error && <ErrorBox error={error} />}

            {data && (
              <Card padding="p-0" className="overflow-hidden">
                <div className="px-5 py-3 border-b" style={{ borderColor: "var(--border-subtle)" }}>
                  <div className="text-title">Payload Facturama</div>
                  <div className="text-caption">
                    JSON listo para POST a Facturama API (no se ha timbrado)
                  </div>
                </div>
                <pre
                  className="px-5 py-4 text-[11px] font-mono overflow-x-auto"
                  style={{
                    background: "var(--surface)",
                    color: "var(--foreground)",
                    lineHeight: 1.6,
                  }}
                >
                  {JSON.stringify(data, null, 2)}
                </pre>
              </Card>
            )}
          </>
        )}
      </main>
    </>
  );
}
