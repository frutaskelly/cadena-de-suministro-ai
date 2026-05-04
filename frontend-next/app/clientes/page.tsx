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
import type { Cliente } from "@/lib/types";

export default function ClientesPage() {
  const [tenant, setTenant] = useState<string | null>(null);
  const [clientes, setClientes] = useState<Cliente[]>([]);
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
        const data = await api<Cliente[]>(`/api/v1/clientes`);
        setClientes(data);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : "Error");
      } finally {
        setLoading(false);
      }
    })();
  }, [tenant]);

  return (
    <>
      <Topbar title="Clientes" />
      <main className="px-7 py-7 max-w-[1400px] mx-auto">
        {!tenant ? (
          <NoTenant />
        ) : (
          <>
            <PageHeader
              title="Clientes"
              description="Entidades fiscales que reciben CFDI"
            />

            <div className="grid grid-cols-3 gap-4 mb-7">
              <StatCard label="Total clientes" value={clientes.length} />
              <StatCard
                label="Gobierno"
                value={clientes.filter((c) => c.tipo.includes("GOV")).length}
              />
              <StatCard
                label="Activos"
                value={clientes.length}
                helper="Todos con lista de precios asignada"
              />
            </div>

            {error && <ErrorBox error={error} />}
            {loading ? (
              <Loading />
            ) : (
              <div className="grid grid-cols-2 gap-5">
                {clientes.map((c) => (
                  <Card key={c.id} padding="p-6">
                    <div className="flex items-start justify-between mb-4">
                      <div>
                        <div className="text-overline mb-1">{c.codigo}</div>
                        <div className="text-title">{c.legal_name}</div>
                      </div>
                      <Badge>{c.tipo}</Badge>
                    </div>
                    <div className="grid grid-cols-2 gap-x-6 gap-y-3 text-[13px]">
                      <div>
                        <div className="text-caption">RFC</div>
                        <div className="font-mono mt-0.5">{c.rfc || "—"}</div>
                      </div>
                      <div>
                        <div className="text-caption">Régimen fiscal</div>
                        <div className="font-mono mt-0.5">
                          {c.regimen_fiscal || "—"}
                        </div>
                      </div>
                      <div>
                        <div className="text-caption">Uso CFDI</div>
                        <div className="font-mono mt-0.5">
                          {c.uso_cfdi_default || "—"}
                        </div>
                      </div>
                      <div>
                        <div className="text-caption">Método pago</div>
                        <div className="mt-0.5">
                          {c.metodo_pago_default || "—"}
                        </div>
                      </div>
                      <div>
                        <div className="text-caption">Forma de pago</div>
                        <div className="mt-0.5">
                          {c.forma_pago_default || "—"}
                        </div>
                      </div>
                      <div>
                        <div className="text-caption">Días de crédito</div>
                        <div className="mt-0.5">
                          {c.dias_credito ?? 0} días
                        </div>
                      </div>
                    </div>
                    {c.domicilio_fiscal && (
                      <div className="mt-4 pt-4" style={{ borderTop: "1px solid var(--border-subtle)" }}>
                        <div className="text-caption mb-1">Domicilio fiscal</div>
                        <div className="text-[12px]" style={{ color: "var(--text-secondary)" }}>
                          {(c.domicilio_fiscal as { raw?: string }).raw || ""}
                        </div>
                      </div>
                    )}
                    {c.condiciones_pago && (
                      <div className="mt-4">
                        <Badge>Pago a {c.condiciones_pago}</Badge>
                      </div>
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
