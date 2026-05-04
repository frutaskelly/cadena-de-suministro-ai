"use client";

import { useEffect, useState } from "react";
import Topbar from "@/components/Topbar";
import { useTenant } from "@/components/TenantProvider";
import {
  Card,
  StatCard,
  PageHeader,
  NoTenant,
  Loading,
  ErrorBox,
  Badge,
} from "@/components/ui";
import { api, fmtMoney, fmtNumber } from "@/lib/api";
import type {
  DashboardResumen,
  TopProductos,
  TopUnidades,
} from "@/lib/types";

export default function DashboardPage() {
  const { tenant } = useTenant();
  const [resumen, setResumen] = useState<DashboardResumen | null>(null);
  const [topProds, setTopProds] = useState<TopProductos | null>(null);
  const [topUnits, setTopUnits] = useState<TopUnidades | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fecha, setFecha] = useState(() =>
    new Date().toISOString().slice(0, 10)
  );

  useEffect(() => {
    if (!tenant) return;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [r, p, u] = await Promise.all([
          api<DashboardResumen>(`/api/v1/dashboard/resumen-dia?fecha=${fecha}`),
          api<TopProductos>(`/api/v1/dashboard/top-productos?limit=10`),
          api<TopUnidades>(`/api/v1/dashboard/top-unidades?limit=10`),
        ]);
        setResumen(r);
        setTopProds(p);
        setTopUnits(u);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error desconocido");
      } finally {
        setLoading(false);
      }
    })();
  }, [tenant, fecha]);

  return (
    <>
      <Topbar title="Dashboard" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="Vista general"
              description={`Resumen operativo del día ${fecha}`}
              actions={
                <input
                  type="date"
                  className="input"
                  value={fecha}
                  onChange={(e) => setFecha(e.target.value)}
                  style={{ width: 160 }}
                />
              }
            />

            {error && <ErrorBox error={error} />}
            {loading && !resumen ? (
              <Loading />
            ) : (
              resumen && (
                <>
                  <div className="grid grid-cols-4 gap-4 mb-7">
                    <StatCard
                      label="Pedidos"
                      value={resumen.pedidos_count}
                      helper={`${resumen.lineas_count} líneas totales`}
                    />
                    <StatCard
                      label="Total facturable"
                      value={fmtMoney(resumen.total_dia)}
                    />
                    <StatCard
                      label="Para revisar"
                      value={resumen.pedidos_requires_review}
                      helper="Requieren ajuste manual"
                    />
                    <StatCard
                      label="Promedio/pedido"
                      value={fmtMoney(
                        resumen.pedidos_count > 0
                          ? resumen.total_dia / resumen.pedidos_count
                          : 0
                      )}
                    />
                  </div>

                  {resumen.por_estado &&
                    Object.keys(resumen.por_estado).length > 0 && (
                      <Card className="mb-7" padding="p-5">
                        <div className="text-overline mb-3">Por estado</div>
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(resumen.por_estado).map(
                            ([estado, count]) => (
                              <div
                                key={estado}
                                className="flex items-center gap-2 px-3 py-1.5 card-soft"
                              >
                                <Badge>{estado}</Badge>
                                <span className="text-[13px] font-medium">
                                  {count}
                                </span>
                              </div>
                            )
                          )}
                        </div>
                      </Card>
                    )}

                  <div className="grid grid-cols-2 gap-5">
                    <Card padding="p-0" className="overflow-hidden">
                      <div className="px-5 pt-5 pb-3">
                        <div className="text-title">Top productos</div>
                        <div className="text-caption">
                          Más solicitados últimos 30 días
                        </div>
                      </div>
                      {!topProds || topProds.items.length === 0 ? (
                        <div className="px-5 pb-5 text-caption">Sin datos.</div>
                      ) : (
                        <table className="tbl">
                          <thead>
                            <tr>
                              <th>Producto</th>
                              <th style={{ textAlign: "right" }}>Cantidad</th>
                              <th style={{ textAlign: "right" }}>Importe</th>
                            </tr>
                          </thead>
                          <tbody>
                            {topProds.items.map((p) => (
                              <tr key={p.producto_id}>
                                <td>{p.nombre}</td>
                                <td style={{ textAlign: "right" }}>
                                  {fmtNumber(p.cantidad_total)}
                                </td>
                                <td
                                  style={{
                                    textAlign: "right",
                                    color: "var(--text-secondary)",
                                  }}
                                >
                                  {fmtMoney(p.importe_total)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </Card>

                    <Card padding="p-0" className="overflow-hidden">
                      <div className="px-5 pt-5 pb-3">
                        <div className="text-title">Top unidades de entrega</div>
                        <div className="text-caption">
                          Hospitales y comedores con mayor flujo
                        </div>
                      </div>
                      {!topUnits || topUnits.items.length === 0 ? (
                        <div className="px-5 pb-5 text-caption">Sin datos.</div>
                      ) : (
                        <table className="tbl">
                          <thead>
                            <tr>
                              <th>Unidad</th>
                              <th style={{ textAlign: "right" }}>Pedidos</th>
                              <th style={{ textAlign: "right" }}>Revenue</th>
                            </tr>
                          </thead>
                          <tbody>
                            {topUnits.items.map((u) => (
                              <tr key={u.unidad_id}>
                                <td>{u.nombre}</td>
                                <td style={{ textAlign: "right" }}>
                                  {u.pedidos_count}
                                </td>
                                <td
                                  style={{
                                    textAlign: "right",
                                    color: "var(--text-secondary)",
                                  }}
                                >
                                  {fmtMoney(u.total_revenue)}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      )}
                    </Card>
                  </div>
                </>
              )
            )}
          </>
        )}
      </main>
    </>
  );
}
