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
} from "@/components/ui";
import { api, fmtMoney, fmtDate, getTenantId } from "@/lib/api";
import type { Pedido } from "@/lib/types";

export default function PedidosPage() {
  const [tenant, setTenant] = useState<string | null>(null);
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fechaDesde, setFechaDesde] = useState("2026-04-25");
  const [fechaHasta, setFechaHasta] = useState("2026-05-04");
  const [estadoFilter, setEstadoFilter] = useState<string>("");

  useEffect(() => {
    setTenant(getTenantId());
    const id = setInterval(() => setTenant(getTenantId()), 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    if (!tenant) return;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const params = new URLSearchParams({
          fecha_desde: fechaDesde,
          fecha_hasta: fechaHasta,
          limit: "200",
        });
        if (estadoFilter) params.set("estado", estadoFilter);
        const data = await api<Pedido[]>(`/api/v1/pedidos?${params}`);
        setPedidos(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    })();
  }, [tenant, fechaDesde, fechaHasta, estadoFilter]);

  return (
    <>
      <Topbar title="Pedidos" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="Pedidos"
              description={`${pedidos.length} pedidos en el rango`}
              actions={
                <div className="flex gap-2 items-center">
                  <input
                    type="date"
                    className="input"
                    value={fechaDesde}
                    onChange={(e) => setFechaDesde(e.target.value)}
                    style={{ width: 150 }}
                  />
                  <span className="text-caption">→</span>
                  <input
                    type="date"
                    className="input"
                    value={fechaHasta}
                    onChange={(e) => setFechaHasta(e.target.value)}
                    style={{ width: 150 }}
                  />
                  <select
                    className="input"
                    value={estadoFilter}
                    onChange={(e) => setEstadoFilter(e.target.value)}
                    style={{ width: 160 }}
                  >
                    <option value="">Todos los estados</option>
                    <option value="BORRADOR">Borrador</option>
                    <option value="CONFIRMADO">Confirmado</option>
                    <option value="EN_SURTIDO">En surtido</option>
                    <option value="ENVIADO">Enviado</option>
                    <option value="ENTREGADO">Entregado</option>
                    <option value="FACTURADO">Facturado</option>
                    <option value="CANCELADO">Cancelado</option>
                  </select>
                </div>
              }
            />

            {error && <ErrorBox error={error} />}
            {loading ? (
              <Loading />
            ) : (
              <Card padding="p-0" className="overflow-hidden">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>Folio</th>
                      <th>Fecha</th>
                      <th>Estado</th>
                      <th>Canal</th>
                      <th style={{ textAlign: "right" }}>Total</th>
                      <th>Review</th>
                    </tr>
                  </thead>
                  <tbody>
                    {pedidos.map((p) => (
                      <tr key={p.id}>
                        <td className="font-mono text-[12px]">
                          {p.folio_interno || p.id.slice(0, 8)}
                        </td>
                        <td>{fmtDate(p.fecha_pedido)}</td>
                        <td>
                          <Badge>{p.estado}</Badge>
                        </td>
                        <td>
                          <span style={{ color: "var(--text-secondary)" }}>
                            {p.canal}
                          </span>
                        </td>
                        <td style={{ textAlign: "right" }} className="font-medium">
                          {fmtMoney(p.total)}
                        </td>
                        <td>
                          {p.requires_review && <Badge>Revisar</Badge>}
                        </td>
                      </tr>
                    ))}
                    {pedidos.length === 0 && (
                      <tr>
                        <td colSpan={6} className="text-center py-8 text-caption">
                          Sin pedidos en el rango seleccionado.
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
