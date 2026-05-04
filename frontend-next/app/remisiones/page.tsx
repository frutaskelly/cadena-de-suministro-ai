"use client";

import { useEffect, useState } from "react";
import Topbar from "@/components/Topbar";
import {
  Card,
  PageHeader,
  NoTenant,
  Loading,
  ErrorBox,
  Badge,
  StatCard,
} from "@/components/ui";
import { api, fmtMoney, fmtDate, getTenantId } from "@/lib/api";
import type { Remision } from "@/lib/types";

const ESTADOS = [
  "GENERADA",
  "EN_TRANSITO",
  "ENTREGADA",
  "CONFIRMADA",
  "FACTURADA",
  "CANCELADA",
];

export default function RemisionesPage() {
  const [tenant, setTenant] = useState<string | null>(null);
  const [remisiones, setRemisiones] = useState<Remision[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [estadoFilter, setEstadoFilter] = useState<string>("");
  const [transitioning, setTransitioning] = useState<string | null>(null);

  useEffect(() => {
    setTenant(getTenantId());
    const id = setInterval(() => setTenant(getTenantId()), 1000);
    return () => clearInterval(id);
  }, []);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ limit: "100" });
      if (estadoFilter) params.set("estado", estadoFilter);
      const data = await api<Remision[]>(`/api/v1/remisiones?${params}`);
      setRemisiones(data);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : "Error");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!tenant) return;
    load();
  }, [tenant, estadoFilter]);

  async function transition(id: string, nuevoEstado: string) {
    setTransitioning(id);
    try {
      await api(`/api/v1/remisiones/${id}/transition`, {
        method: "POST",
        body: { nuevo_estado: nuevoEstado },
      });
      await load();
    } catch (e: unknown) {
      alert((e as Error).message);
    } finally {
      setTransitioning(null);
    }
  }

  function nextStates(estado: string): string[] {
    const map: Record<string, string[]> = {
      GENERADA: ["EN_TRANSITO", "CANCELADA"],
      EN_TRANSITO: ["ENTREGADA", "CANCELADA"],
      ENTREGADA: ["CONFIRMADA", "CANCELADA"],
      CONFIRMADA: ["FACTURADA", "CANCELADA"],
    };
    return map[estado] || [];
  }

  // Stats
  const counts = ESTADOS.reduce(
    (acc, e) => {
      acc[e] = remisiones.filter((r) => r.estado === e).length;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <>
      <Topbar title="Remisiones" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="Remisiones"
              description="Entregas físicas pendientes de facturar — flujo triple-estado"
              actions={
                <select
                  className="input"
                  value={estadoFilter}
                  onChange={(e) => setEstadoFilter(e.target.value)}
                  style={{ width: 180 }}
                >
                  <option value="">Todos los estados</option>
                  {ESTADOS.map((e) => (
                    <option key={e} value={e}>
                      {e}
                    </option>
                  ))}
                </select>
              }
            />

            {error && <ErrorBox error={error} />}

            <div className="grid grid-cols-6 gap-3 mb-7">
              {ESTADOS.map((e) => (
                <StatCard key={e} label={e.replace("_", " ")} value={counts[e] || 0} />
              ))}
            </div>

            {loading ? (
              <Loading />
            ) : (
              <Card padding="p-0" className="overflow-hidden">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>Folio</th>
                      <th>Pedido origen</th>
                      <th>Fecha</th>
                      <th>Estado</th>
                      <th style={{ textAlign: "right" }}>Líneas</th>
                      <th style={{ textAlign: "right" }}>Total</th>
                      <th>Acciones</th>
                    </tr>
                  </thead>
                  <tbody>
                    {remisiones.map((r) => {
                      const next = nextStates(r.estado);
                      return (
                        <tr key={r.id}>
                          <td className="font-mono text-[12px]">{r.folio}</td>
                          <td className="font-mono text-[12px]" style={{ color: "var(--text-tertiary)" }}>
                            {r.pedido_id ? r.pedido_id.slice(0, 8) : "—"}
                          </td>
                          <td>{fmtDate(r.fecha_generada)}</td>
                          <td>
                            <Badge>{r.estado}</Badge>
                          </td>
                          <td style={{ textAlign: "right" }}>
                            {r.lineas?.length ?? 0}
                          </td>
                          <td style={{ textAlign: "right" }} className="font-medium">
                            {fmtMoney(r.total)}
                          </td>
                          <td>
                            <div className="flex gap-1.5">
                              {next.map((n) => (
                                <button
                                  key={n}
                                  className={
                                    n === "CANCELADA" ? "btn-ghost" : "btn-outline"
                                  }
                                  style={{ fontSize: 11, padding: "4px 9px" }}
                                  disabled={transitioning === r.id}
                                  onClick={() => transition(r.id, n)}
                                >
                                  → {n.replace("_", " ").toLowerCase()}
                                </button>
                              ))}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    {remisiones.length === 0 && (
                      <tr>
                        <td colSpan={7} className="text-center py-8 text-caption">
                          Sin remisiones. Crea una desde un pedido en /pedidos.
                        </td>
                      </tr>
                    )}
                  </tbody>
                </table>
              </Card>
            )}
          </>
        )}
      </main>
    </>
  );
}
