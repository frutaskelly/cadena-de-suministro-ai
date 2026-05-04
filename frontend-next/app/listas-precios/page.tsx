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
import type { ListaPrecios, Precio, Producto } from "@/lib/types";

export default function ListasPreciosPage() {
  const { tenant } = useTenant();
  const [listas, setListas] = useState<ListaPrecios[]>([]);
  const [precios, setPrecios] = useState<Precio[]>([]);
  const [productos, setProductos] = useState<Map<string, Producto>>(new Map());
  const [selectedLista, setSelectedLista] = useState<string>("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!tenant) return;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const [l, p] = await Promise.all([
          api<ListaPrecios[]>(`/api/v1/listas-precios`),
          api<Producto[]>(`/api/v1/productos?limit=500`),
        ]);
        setListas(l);
        const map = new Map<string, Producto>();
        p.forEach((prod) => map.set(prod.id, prod));
        setProductos(map);
        if (l.length > 0 && !selectedLista) {
          setSelectedLista(l[0].id);
        }
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    })();
  }, [tenant]);

  useEffect(() => {
    if (!selectedLista) return;
    (async () => {
      try {
        const data = await api<Precio[]>(
          `/api/v1/precios/by-lista/${selectedLista}?limit=500`
        );
        setPrecios(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      }
    })();
  }, [selectedLista]);

  const lista = listas.find((l) => l.id === selectedLista);
  const filteredPrecios = precios.filter(
    (p) => p.lista_id === selectedLista
  );

  return (
    <>
      <Topbar title="Listas de precios" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="Listas de precios"
              description={`${listas.length} listas activas · vigencia desde 2025-01-01`}
            />

            {error && <ErrorBox error={error} />}

            <div className="grid grid-cols-3 gap-4 mb-7">
              {listas.map((l) => (
                <Card
                  key={l.id}
                  padding="p-5"
                  className={
                    "cursor-pointer transition-all " +
                    (selectedLista === l.id ? "" : "hover:bg-[var(--surface)]")
                  }
                  onClick={() => setSelectedLista(l.id)}
                >
                  <div
                    className="cursor-pointer"
                    onClick={() => setSelectedLista(l.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-overline">{l.codigo}</div>
                      {selectedLista === l.id && <Badge>Activa</Badge>}
                    </div>
                    <div className="text-title">{l.nombre}</div>
                    <div className="text-caption mt-2">
                      {l.moneda} · desde {fmtDate(l.vigencia_desde)}
                    </div>
                    <div className="text-caption mt-3">
                      {selectedLista === l.id
                        ? `${filteredPrecios.length} precios`
                        : "Click para ver"}
                    </div>
                  </div>
                </Card>
              ))}
            </div>

            {loading ? (
              <Loading />
            ) : lista ? (
              <Card padding="p-0" className="overflow-hidden">
                <div
                  className="px-5 pt-5 pb-3 flex items-center justify-between"
                  style={{ borderBottom: "1px solid var(--border-subtle)" }}
                >
                  <div>
                    <div className="text-title">{lista.nombre}</div>
                    <div className="text-caption">
                      {filteredPrecios.length} productos con precio
                    </div>
                  </div>
                </div>
                <div className="max-h-[600px] overflow-y-auto">
                  <table className="tbl">
                    <thead style={{ position: "sticky", top: 0 }}>
                      <tr>
                        <th>Producto</th>
                        <th>Presentación</th>
                        <th style={{ textAlign: "right" }}>Precio</th>
                        <th>Vigencia</th>
                      </tr>
                    </thead>
                    <tbody>
                      {filteredPrecios.map((p) => {
                        const prod = productos.get(p.producto_id);
                        return (
                          <tr key={p.id}>
                            <td className="font-medium">
                              {prod?.nombre || p.producto_id.slice(0, 8)}
                            </td>
                            <td style={{ color: "var(--text-secondary)" }}>
                              {p.presentacion}
                            </td>
                            <td
                              style={{ textAlign: "right" }}
                              className="font-mono font-medium"
                            >
                              {fmtMoney(p.precio_unitario)}
                            </td>
                            <td className="text-caption">
                              {p.vigencia_desde
                                ? fmtDate(p.vigencia_desde)
                                : "—"}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </Card>
            ) : null}
          </>
        )}
      </main>
    </>
  );
}
