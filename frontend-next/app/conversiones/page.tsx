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
import { api, fmtNumber, getTenantId } from "@/lib/api";
import type { Conversion, Producto } from "@/lib/types";

export default function ConversionesPage() {
  const [tenant, setTenant] = useState<string | null>(null);
  const [convs, setConvs] = useState<Conversion[]>([]);
  const [productos, setProductos] = useState<Map<string, Producto>>(new Map());
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
        const [c, p] = await Promise.all([
          api<Conversion[]>(`/api/v1/conversiones?limit=500`),
          api<Producto[]>(`/api/v1/productos?limit=500`),
        ]);
        setConvs(c);
        const map = new Map<string, Producto>();
        p.forEach((prod) => map.set(prod.id, prod));
        setProductos(map);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    })();
  }, [tenant]);

  function nombreOf(id: string): string {
    return productos.get(id)?.nombre || id.slice(0, 8);
  }

  return (
    <>
      <Topbar title="Conversiones" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="Conversiones de producto"
              description="Mapeo no-catalogado → catalogado para sustituciones de inventario"
            />

            <Card padding="p-5" className="mb-7 card-soft">
              <div className="text-overline mb-2">Cómo funciona</div>
              <div className="text-[13px] leading-relaxed" style={{ color: "var(--text-secondary)" }}>
                Hospital pide <span className="font-medium" style={{ color: "var(--foreground)" }}>Manzana Roja</span> (catalogada).
                Bodega tiene <span className="font-medium" style={{ color: "var(--foreground)" }}>Manzana Royal Gala</span> (no-catalogada).
                Esta tabla mapea la sustitución con factor + merma + precio override.
                Se factura el producto catalogado, se descarga el no-catalogado del inventario.
              </div>
            </Card>

            {error && <ErrorBox error={error} />}
            {loading ? (
              <Loading />
            ) : convs.length === 0 ? (
              <Card padding="p-10" className="text-center">
                <div className="text-title mb-1">Sin conversiones registradas</div>
                <div className="text-caption mb-3">
                  Cuando agregues productos no-catalogados podrás mapear sus equivalencias aquí.
                </div>
                <button className="btn-primary" disabled>
                  Crear conversión (próximamente)
                </button>
              </Card>
            ) : (
              <Card padding="p-0" className="overflow-hidden">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>Catalogado</th>
                      <th>No-catalogado</th>
                      <th style={{ textAlign: "right" }}>Factor</th>
                      <th style={{ textAlign: "right" }}>Merma</th>
                      <th style={{ textAlign: "right" }}>Prioridad</th>
                      <th>Aprobación</th>
                      <th>Estado</th>
                    </tr>
                  </thead>
                  <tbody>
                    {convs.map((c) => (
                      <tr key={c.id}>
                        <td className="font-medium">
                          {nombreOf(c.producto_catalogado_id)}
                        </td>
                        <td>
                          <span style={{ color: "var(--text-secondary)" }}>
                            {nombreOf(c.producto_no_catalogado_id)}
                          </span>
                        </td>
                        <td style={{ textAlign: "right" }} className="font-mono">
                          {fmtNumber(parseFloat(c.factor))}
                        </td>
                        <td style={{ textAlign: "right" }} className="font-mono">
                          {(parseFloat(c.merma_pct) * 100).toFixed(1)}%
                        </td>
                        <td style={{ textAlign: "right", color: "var(--text-secondary)" }}>
                          {c.prioridad}
                        </td>
                        <td>
                          {c.requiere_aprobacion ? <Badge>Requerida</Badge> : (
                            <span style={{ color: "var(--text-tertiary)" }}>—</span>
                          )}
                        </td>
                        <td>
                          {c.activo ? <Badge>Activo</Badge> : <Badge>Inactivo</Badge>}
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
