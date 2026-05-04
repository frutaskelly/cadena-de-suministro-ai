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
import { api, fmtNumber, getTenantId } from "@/lib/api";
import type { Producto } from "@/lib/types";

const CATEGORIAS = [
  "FRUTAS_VERDURAS",
  "LACTEOS_EMBUTIDOS",
  "PROTEINA_ANIMAL",
  "TORTILLAS",
  "PAN",
  "GRANOS_SEMILLAS",
  "ABARROTE",
  "AGUA",
  "REFRESCO",
  "LIMPIEZA",
  "DESECHABLES",
  "OTRO",
];

export default function ProductosPage() {
  const [tenant, setTenant] = useState<string | null>(null);
  const [productos, setProductos] = useState<Producto[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [categoriaFilter, setCategoriaFilter] = useState("");
  const [esCatFilter, setEsCatFilter] = useState<string>("");

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
        const params = new URLSearchParams({ limit: "500" });
        if (search) params.set("search", search);
        const data = await api<Producto[]>(`/api/v1/productos?${params}`);
        setProductos(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    })();
  }, [tenant, search]);

  const filtered = productos.filter((p) => {
    if (categoriaFilter && p.categoria_extendida !== categoriaFilter) return false;
    if (esCatFilter === "cat" && !p.es_catalogado) return false;
    if (esCatFilter === "no-cat" && p.es_catalogado) return false;
    return true;
  });

  // Stats
  const perecederos = productos.filter((p) => p.perecedero).length;
  const catalogados = productos.filter((p) => p.es_catalogado).length;
  const conColdChain = productos.filter((p) => p.cold_chain).length;

  return (
    <>
      <Topbar title="Productos" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="Catálogo de productos"
              description={`${filtered.length} de ${productos.length} productos · 12 categorías soportadas`}
              actions={
                <div className="flex gap-2">
                  <input
                    className="input"
                    placeholder="Buscar por nombre…"
                    value={search}
                    onChange={(e) => setSearch(e.target.value)}
                    style={{ width: 240 }}
                  />
                  <select
                    className="input"
                    value={categoriaFilter}
                    onChange={(e) => setCategoriaFilter(e.target.value)}
                    style={{ width: 200 }}
                  >
                    <option value="">Todas las categorías</option>
                    {CATEGORIAS.map((c) => (
                      <option key={c} value={c}>
                        {c.replace(/_/g, " ")}
                      </option>
                    ))}
                  </select>
                  <select
                    className="input"
                    value={esCatFilter}
                    onChange={(e) => setEsCatFilter(e.target.value)}
                    style={{ width: 160 }}
                  >
                    <option value="">Catalogados / no</option>
                    <option value="cat">Solo catalogados</option>
                    <option value="no-cat">Solo no-catalogados</option>
                  </select>
                </div>
              }
            />

            <div className="grid grid-cols-4 gap-4 mb-7">
              <StatCard label="Total productos" value={productos.length} />
              <StatCard label="Catalogados" value={catalogados} helper={`${productos.length - catalogados} no-catalogados`} />
              <StatCard label="Perecederos" value={perecederos} />
              <StatCard label="Cold chain" value={conColdChain} helper="Requieren refrigeración" />
            </div>

            {error && <ErrorBox error={error} />}
            {loading ? (
              <Loading />
            ) : (
              <Card padding="p-0" className="overflow-hidden">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>SKU</th>
                      <th>Nombre</th>
                      <th>Categoría</th>
                      <th>Tipo</th>
                      <th>Atributos</th>
                      <th>Clave SAT</th>
                      <th style={{ textAlign: "right" }}>Vida útil</th>
                    </tr>
                  </thead>
                  <tbody>
                    {filtered.slice(0, 200).map((p) => (
                      <tr key={p.id}>
                        <td className="font-mono text-[11px]" style={{ color: "var(--text-tertiary)" }}>
                          {p.sku_interno}
                        </td>
                        <td className="font-medium">{p.nombre}</td>
                        <td>
                          <Badge>{(p.categoria_extendida || "OTRO").replace(/_/g, " ")}</Badge>
                        </td>
                        <td>
                          <span style={{ color: "var(--text-secondary)" }}>
                            {p.es_catalogado ? "Catalogado" : "No-cat"}
                          </span>
                        </td>
                        <td>
                          <div className="flex gap-1">
                            {p.perecedero && <Badge>Perecedero</Badge>}
                            {p.cold_chain && <Badge>Cold chain</Badge>}
                            {p.requiere_caducidad && <Badge>Caducidad</Badge>}
                          </div>
                        </td>
                        <td className="font-mono text-[11px]">{p.clave_sat}</td>
                        <td style={{ textAlign: "right", color: "var(--text-secondary)" }}>
                          {p.vida_util_dias ? `${p.vida_util_dias}d` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
                {filtered.length > 200 && (
                  <div className="px-5 py-3 text-caption border-t" style={{ borderColor: "var(--border-subtle)" }}>
                    Mostrando 200 de {filtered.length}. Refina la búsqueda para ver más.
                  </div>
                )}
              </Card>
            )}
          </>
        )}
      </main>
    </>
  );
}
