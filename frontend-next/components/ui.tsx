"use client";

import { ReactNode } from "react";

export function Card({
  children,
  className = "",
  padding = "p-6",
  onClick,
}: {
  children: ReactNode;
  className?: string;
  padding?: string;
  onClick?: () => void;
}) {
  return (
    <div className={`card ${padding} ${className}`} onClick={onClick}>
      {children}
    </div>
  );
}

export function StatCard({
  label,
  value,
  helper,
}: {
  label: string;
  value: string | number;
  helper?: string;
}) {
  return (
    <Card padding="p-5">
      <div className="text-overline">{label}</div>
      <div className="stat-value mt-3">{value}</div>
      {helper && (
        <div className="text-[11px] mt-1" style={{ color: "var(--text-tertiary)" }}>
          {helper}
        </div>
      )}
    </Card>
  );
}

const ESTADO_TONO: Record<string, { bg: string; fg: string }> = {
  // generales
  CONFIRMADO: { bg: "rgba(0, 0, 0, 0.06)", fg: "#1d1d1f" },
  BORRADOR: { bg: "rgba(0, 0, 0, 0.03)", fg: "#86868b" },
  ENVIADA: { bg: "rgba(0, 0, 0, 0.06)", fg: "#1d1d1f" },
  ACEPTADA: { bg: "rgba(0, 0, 0, 0.08)", fg: "#1d1d1f" },
  EN_TRANSITO: { bg: "rgba(0, 0, 0, 0.10)", fg: "#1d1d1f" },
  ENTREGADA: { bg: "rgba(0, 0, 0, 0.12)", fg: "#1d1d1f" },
  CONFIRMADA: { bg: "rgba(0, 0, 0, 0.14)", fg: "#1d1d1f" },
  GENERADA: { bg: "rgba(0, 0, 0, 0.04)", fg: "#6e6e73" },
  RECIBIDA_PARCIAL: { bg: "rgba(0, 0, 0, 0.10)", fg: "#1d1d1f" },
  RECIBIDA: { bg: "rgba(0, 0, 0, 0.16)", fg: "#1d1d1f" },
  FACTURADA: { bg: "#1d1d1f", fg: "#ffffff" },
  FACTURADO: { bg: "#1d1d1f", fg: "#ffffff" },
  CANCELADA: { bg: "rgba(0, 0, 0, 0.04)", fg: "#86868b" },
  CANCELADO: { bg: "rgba(0, 0, 0, 0.04)", fg: "#86868b" },
};

export function Badge({ children }: { children: ReactNode }) {
  const key = String(children).toUpperCase();
  const tone = ESTADO_TONO[key];
  return (
    <span
      className="badge"
      style={tone ? { background: tone.bg, color: tone.fg } : undefined}
    >
      {children}
    </span>
  );
}

export function Empty({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <Card padding="p-12" className="text-center">
      <div className="text-title mb-1">{title}</div>
      {description && <div className="text-caption">{description}</div>}
    </Card>
  );
}

export function Loading() {
  return (
    <Card padding="p-12" className="text-center">
      <div className="inline-block animate-pulse">
        <div className="w-2 h-2 rounded-full bg-black inline-block mr-1" />
        <div className="w-2 h-2 rounded-full bg-black inline-block mr-1" style={{ animationDelay: "0.1s" }} />
        <div className="w-2 h-2 rounded-full bg-black inline-block" style={{ animationDelay: "0.2s" }} />
      </div>
      <div className="text-caption mt-3">Cargando…</div>
    </Card>
  );
}

export function ErrorBox({ error }: { error: string }) {
  return (
    <Card padding="p-6" className="border-red-200">
      <div className="text-title mb-1">Error</div>
      <div className="text-caption font-mono">{error}</div>
    </Card>
  );
}

export function PageHeader({
  title,
  description,
  actions,
}: {
  title: string;
  description?: string;
  actions?: ReactNode;
}) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <div className="text-headline">{title}</div>
        {description && (
          <div className="text-caption mt-1.5">{description}</div>
        )}
      </div>
      {actions && <div className="flex gap-2 items-center">{actions}</div>}
    </div>
  );
}

export function NoTenant() {
  return (
    <Card padding="p-10" className="text-center max-w-md mx-auto">
      <div className="text-title mb-2">Configura tu tenant</div>
      <div className="text-caption">
        Ingresa el UUID de tu tenant en la barra superior para empezar a ver datos.
      </div>
    </Card>
  );
}
