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
  StatCard,
} from "@/components/ui";
import { api, fmtNumber } from "@/lib/api";
import type { InventarioEstado } from "@/lib/types";

export default function InventarioPage() {
  const { tenant } = useTenant();
  const [data, setData] = useState<InventarioEstado[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenant) return;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const d = await api<InventarioEstado[]>(
          `/api/v1/remisiones/inventario/triple-estado`
        );
        setData(d);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    })();
  }, [tenant]);

  const totalFisico = data.reduce(
    (s, r) => s + parseFloat(r.cantidad_fisica),
    0
  );
  const totalRemision = data.reduce(
    (s, r) => s + parseFloat(r.cantidad_remision),
    0
  );
  const totalFacturada = data.reduce(
    (s, r) => s + parseFloat(r.cantidad_facturada_acumulada),
    0
  );

  return (
    <>
      <Topbar title="Inventario" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="Inventario triple-estado"
              description="Físico en bodega · Remisión pendiente · Facturado acumulado"
            />

            <div className="grid grid-cols-3 gap-4 mb-7">
              <StatCard
                label="Físico en bodega"
                value={fmtNumber(totalFisico)}
                helper={`${data.length} SKUs activos`}
              />
              <StatCard
                label="En remisión pendiente"
                value={fmtNumber(totalRemision)}
                helper="Entregado, esperando facturar"
              />
              <StatCard
                label="Facturado acumulado"
                value={fmtNumber(totalFacturada)}
                helper="Histórico ya cerrado"
              />
            </div>

            <Card padding="p-5" className="mb-7 card-soft">
              <div className="text-overline mb-2">Ecuación maestra</div>
              <div
                className="font-mono text-[12px] leading-relaxed"
                style={{ color: "var(--text-secondary)" }}
              >
                inventario_físico = compras_recibidas − ventas_facturadas
                − remisiones_pendientes − mermas − ajustes
              </div>
            </Card>

            {error && <ErrorBox error={error} />}
            {loading ? (
              <Loading />
            ) : data.length === 0 ? (
              <Card padding="p-10" className="text-center">
                <div className="text-title mb-1">Sin lotes registrados</div>
                <div className="text-caption">
                  Cuando entren productos vía órdenes de compra, aparecerán aquí.
                </div>
              </Card>
            ) : (
              <Card padding="p-0" className="overflow-hidden">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>Producto</th>
                      <th style={{ textAlign: "right" }}>Físico</th>
                      <th style={{ textAlign: "right" }}>Remisión</th>
                      <th style={{ textAlign: "right" }}>Facturado</th>
                      <th style={{ textAlign: "right" }}>Disponible efectivo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.map((r) => (
                      <tr key={`${r.producto_id}-${r.almacen_id}`}>
                        <td>{r.producto_nombre}</td>
                        <td style={{ textAlign: "right" }} className="font-medium">
                          {fmtNumber(r.cantidad_fisica)}
                        </td>
                        <td style={{ textAlign: "right", color: "var(--text-secondary)" }}>
                          {fmtNumber(r.cantidad_remision)}
                        </td>
                        <td style={{ textAlign: "right", color: "var(--text-tertiary)" }}>
                          {fmtNumber(r.cantidad_facturada_acumulada)}
                        </td>
                        <td style={{ textAlign: "right" }} className="font-medium">
                          {fmtNumber(r.total_disponible_efectivo)}
                        </td>
                      </tr>
                    ))}
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
