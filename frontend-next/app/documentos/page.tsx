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
import { api, fmtDate, fmtDateTime, getTenantId } from "@/lib/api";
import type { DocumentoGenerado } from "@/lib/types";

const TIPOS = [
  "PEDIDO_PDF",
  "PEDIDO_XLSX",
  "LISTA_COMPRAS_PDF",
  "LISTA_COMPRAS_XLSX",
  "REMISION_PDF",
  "RELACION_PDF",
];

const TIPO_LABEL: Record<string, string> = {
  PEDIDO_PDF: "Pedido (PDF)",
  PEDIDO_XLSX: "Pedido (Excel)",
  LISTA_COMPRAS_PDF: "Lista de compras (PDF)",
  LISTA_COMPRAS_XLSX: "Lista de compras (Excel)",
  REMISION_PDF: "Remisión (PDF)",
  RELACION_PDF: "Relación (PDF)",
};

export default function DocumentosPage() {
  const [tenant, setTenant] = useState<string | null>(null);
  const [docs, setDocs] = useState<DocumentoGenerado[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tipoFilter, setTipoFilter] = useState("");

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
        const params = new URLSearchParams({ limit: "300" });
        if (tipoFilter) params.set("tipo_documento", tipoFilter);
        const data = await api<DocumentoGenerado[]>(
          `/api/v1/documentos?${params}`
        );
        setDocs(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    })();
  }, [tenant, tipoFilter]);

  const counts = TIPOS.reduce(
    (acc, t) => {
      acc[t] = docs.filter((d) => d.tipo_documento === t).length;
      return acc;
    },
    {} as Record<string, number>
  );

  return (
    <>
      <Topbar title="Documentos" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="Documentos generados"
              description="PDFs y XLSX producidos por los agentes WhatsApp (legacy v1)"
              actions={
                <select
                  className="input"
                  value={tipoFilter}
                  onChange={(e) => setTipoFilter(e.target.value)}
                  style={{ width: 220 }}
                >
                  <option value="">Todos los tipos</option>
                  {TIPOS.map((t) => (
                    <option key={t} value={t}>
                      {TIPO_LABEL[t]}
                    </option>
                  ))}
                </select>
              }
            />

            <div className="grid grid-cols-6 gap-3 mb-7">
              {TIPOS.map((t) => (
                <StatCard
                  key={t}
                  label={TIPO_LABEL[t].split("(")[0].trim()}
                  value={counts[t] || 0}
                />
              ))}
            </div>

            {error && <ErrorBox error={error} />}
            {loading ? (
              <Loading />
            ) : (
              <Card padding="p-0" className="overflow-hidden">
                <table className="tbl">
                  <thead>
                    <tr>
                      <th>Archivo</th>
                      <th>Tipo</th>
                      <th>Fecha</th>
                      <th>Generado</th>
                      <th>Detalles</th>
                    </tr>
                  </thead>
                  <tbody>
                    {docs.map((d) => {
                      const meta = d.metadata_doc || {};
                      return (
                        <tr key={d.id}>
                          <td className="font-mono text-[12px]">{d.nombre_archivo}</td>
                          <td>
                            <Badge>{TIPO_LABEL[d.tipo_documento] || d.tipo_documento}</Badge>
                          </td>
                          <td>{fmtDate(d.fecha_documento)}</td>
                          <td className="text-caption">{fmtDateTime(d.created_at)}</td>
                          <td>
                            <div className="text-[11.5px]" style={{ color: "var(--text-secondary)" }}>
                              {(meta as { destino?: string }).destino && (
                                <div>{(meta as { destino: string }).destino}</div>
                              )}
                              {(meta as { folio?: string }).folio && (
                                <div className="font-mono">
                                  Folio: {(meta as { folio: string }).folio}
                                </div>
                              )}
                              {(meta as { destinos_count?: number }).destinos_count !== undefined && (
                                <div>
                                  {(meta as { destinos_count: number }).destinos_count} destinos
                                </div>
                              )}
                              {(meta as { remisiones_count?: number }).remisiones_count !== undefined && (
                                <div>
                                  {(meta as { remisiones_count: number }).remisiones_count} remisiones
                                </div>
                              )}
                              {(meta as { lineas_count?: number }).lineas_count !== undefined && (
                                <div>
                                  {(meta as { lineas_count: number }).lineas_count} líneas
                                </div>
                              )}
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                    {docs.length === 0 && (
                      <tr>
                        <td colSpan={5} className="text-center py-8 text-caption">
                          Sin documentos para este filtro.
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
