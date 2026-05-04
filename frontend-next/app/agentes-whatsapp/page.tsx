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
import { api, getTenantId } from "@/lib/api";
import type { AgenteWhatsapp } from "@/lib/types";

export default function AgentesWhatsappPage() {
  const [tenant, setTenant] = useState<string | null>(null);
  const [agentes, setAgentes] = useState<AgenteWhatsapp[]>([]);
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
        const data = await api<AgenteWhatsapp[]>(`/api/v1/agentes-whatsapp`);
        setAgentes(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    })();
  }, [tenant]);

  return (
    <>
      <Topbar title="Agentes WhatsApp" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="Agentes WhatsApp"
              description="Configuración del bot de pedidos por canal — clonado del legacy v1"
            />

            <div className="grid grid-cols-3 gap-4 mb-7">
              <StatCard label="Agentes activos" value={agentes.filter((a) => a.activo).length} />
              <StatCard
                label="Folio EHMO Hospitales"
                value={agentes.find((a) => a.codigo === "ehmo_hospitales")?.proximo_folio || 0}
                helper="Próximo número a emitir"
              />
              <StatCard
                label="Folio Comedores SUREÑA"
                value={agentes.find((a) => a.codigo === "surena_comedores")?.proximo_folio || 0}
                helper="Próximo número a emitir"
              />
            </div>

            {error && <ErrorBox error={error} />}
            {loading ? (
              <Loading />
            ) : (
              <div className="grid grid-cols-3 gap-5">
                {agentes.map((a) => (
                  <Card key={a.id} padding="p-6">
                    <div className="flex items-start gap-3 mb-4">
                      <div
                        className="w-10 h-10 rounded-xl flex items-center justify-center text-lg"
                        style={{
                          background: a.color_hex
                            ? `${a.color_hex}15`
                            : "var(--surface-2)",
                          color: a.color_hex || "var(--foreground)",
                        }}
                      >
                        {a.icono || "🤖"}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="text-overline mb-1">{a.tipo}</div>
                        <div className="text-title">{a.nombre}</div>
                      </div>
                    </div>
                    {a.descripcion && (
                      <div
                        className="text-[12.5px] leading-relaxed mb-4"
                        style={{ color: "var(--text-secondary)" }}
                      >
                        {a.descripcion}
                      </div>
                    )}
                    <div className="grid grid-cols-2 gap-x-4 gap-y-3 text-[12px] mb-4">
                      <div>
                        <div className="text-caption">Código</div>
                        <div className="font-mono mt-0.5">{a.codigo}</div>
                      </div>
                      <div>
                        <div className="text-caption">Próximo folio</div>
                        <div className="font-mono mt-0.5">{a.proximo_folio}</div>
                      </div>
                      <div>
                        <div className="text-caption">Estado</div>
                        <div className="mt-0.5">
                          {a.activo ? (
                            <Badge>Activo</Badge>
                          ) : (
                            <Badge>Inactivo</Badge>
                          )}
                        </div>
                      </div>
                      <div>
                        <div className="text-caption">Pesos requeridos</div>
                        <div className="mt-0.5">
                          {(a as unknown as { requires_pesos: boolean }).requires_pesos
                            ? "Sí (libreta)"
                            : "No"}
                        </div>
                      </div>
                    </div>
                    {a.system_prompt_addendum && (
                      <details
                        className="mt-4 pt-4"
                        style={{ borderTop: "1px solid var(--border-subtle)" }}
                      >
                        <summary
                          className="text-caption cursor-pointer hover:text-[var(--foreground)]"
                          style={{ outline: "none" }}
                        >
                          System prompt (specialización del agente) →
                        </summary>
                        <pre
                          className="mt-3 text-[10.5px] font-mono whitespace-pre-wrap leading-relaxed max-h-[200px] overflow-y-auto p-3 card-soft"
                          style={{ color: "var(--text-secondary)" }}
                        >
                          {a.system_prompt_addendum.slice(0, 800)}
                          {a.system_prompt_addendum.length > 800 ? "…" : ""}
                        </pre>
                      </details>
                    )}
                  </Card>
                ))}
              </div>
            )}
          </>
        )}
      </main>
    </>
  );
}
