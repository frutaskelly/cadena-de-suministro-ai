"use client";

import { useEffect, useState } from "react";
import Topbar from "@/components/Topbar";
import { useTenant } from "@/components/TenantProvider";
import {
  Card,
  PageHeader,
  NoTenant,
  Loading,
  ErrorBox,
  Badge,
  StatCard,
} from "@/components/ui";
import { api, fmtMoney, fmtDate } from "@/lib/api";
import type { OrdenCompra } from "@/lib/types";

const ESTADOS = [
  "BORRADOR",
  "ENVIADA",
  "ACEPTADA",
  "EN_TRANSITO",
  "RECIBIDA_PARCIAL",
  "RECIBIDA",
  "CANCELADA",
];

export default function OrdenesCompraPage() {
  const { tenant } = useTenant();
  const [ordenes, setOrdenes] = useState<OrdenCompra[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [estadoFilter, setEstadoFilter] = useState("");

  useEffect(() => {
    if (!tenant) return;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({ limit: "100" });
        if (estadoFilter) params.set("estado", estadoFilter);
        const data = await api<OrdenCompra[]>(`/api/v1/ordenes-compra?${params}`);
        setOrdenes(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    })();
  }, [tenant, estadoFilter]);

  const counts = ESTADOS.reduce(
    (acc, e) => {
      acc[e] = ordenes.filter((o) => o.estado === e).length;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <>
      <Topbar title="Órdenes de compra" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="Órdenes de compra"
              description="Compras a proveedores · ciclo BORRADOR → RECIBIDA"
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

            <div className="grid grid-cols-7 gap-3 mb-7">
              {ESTADOS.map((e) => (
                <StatCard
                  key={e}
                  label={e.replace("_", " ")}
                  value={counts[e] || 0}
                />
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
                      <th>Proveedor</th>
                      <th>Fecha</th>
                      <th>Estado</th>
                      <th style={{ textAlign: "right" }}>Líneas</th>
                      <th style={{ textAlign: "right" }}>Total estimado</th>
                      <th style={{ textAlign: "right" }}>Recibido</th>
                    </tr>
                  </thead>
                  <tbody>
                    {ordenes.map((o) => (
                      <tr key={o.id}>
                        <td className="font-mono text-[12px]">{o.folio || o.id.slice(0, 8)}</td>
                        <td className="font-mono text-[12px]" style={{ color: "var(--text-tertiary)" }}>
                          {o.proveedor_id.slice(0, 8)}
                        </td>
                        <td>{fmtDate(o.fecha)}</td>
                        <td>
                          <Badge>{o.estado}</Badge>
                        </td>
                        <td style={{ textAlign: "right" }}>{o.lineas?.length ?? 0}</td>
                        <td style={{ textAlign: "right" }} className="font-medium">
                          {fmtMoney(o.total_estimado)}
                        </td>
                        <td style={{ textAlign: "right", color: "var(--text-secondary)" }}>
                          {fmtMoney(o.total_recibido)}
                        </td>
                      </tr>
                    ))}
                    {ordenes.length === 0 && (
                      <tr>
                        <td colSpan={7} className="text-center py-8 text-caption">
                          Sin órdenes de compra registradas todavía.
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
