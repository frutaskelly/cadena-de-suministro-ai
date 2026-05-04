"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useRef, useState } from "react";

type Item = { href: string; label: string };
type Section = { id: string; title: string; items: Item[] };

const sections: Section[] = [
  {
    id: "operaciones",
    title: "Operaciones",
    items: [
      { href: "/", label: "Dashboard" },
      { href: "/chat", label: "Chat AI" },
      { href: "/pedidos", label: "Pedidos" },
      { href: "/remisiones", label: "Remisiones" },
      { href: "/inventario", label: "Inventario" },
    ],
  },
  {
    id: "whatsapp",
    title: "WhatsApp",
    items: [
      { href: "/agentes-whatsapp", label: "Agentes" },
      { href: "/documentos", label: "Documentos" },
    ],
  },
  {
    id: "compras",
    title: "Compras",
    items: [{ href: "/ordenes-compra", label: "Órdenes de compra" }],
  },
  {
    id: "catalogo",
    title: "Catálogo",
    items: [
      { href: "/productos", label: "Productos" },
      { href: "/conversiones", label: "Conversiones" },
      { href: "/listas-precios", label: "Listas de precios" },
      { href: "/clientes", label: "Clientes" },
    ],
  },
  {
    id: "facturacion",
    title: "Facturación",
    items: [{ href: "/cfdi", label: "CFDI Preview" }],
  },
];

const STORAGE_KEY = "sidebar:open-sections";

function isActive(itemHref: string, pathname: string | null): boolean {
  if (!pathname) return false;
  if (itemHref === "/") return pathname === "/";
  return pathname === itemHref || pathname.startsWith(itemHref + "/");
}

function sectionHasActive(section: Section, pathname: string | null): boolean {
  return section.items.some((it) => isActive(it.href, pathname));
}

export default function Sidebar() {
  const pathname = usePathname();
  const [hydrated, setHydrated] = useState(false);
  const [open, setOpen] = useState<Record<string, boolean>>(() => {
    // Sin pathname al SSR — defaults: solo Operaciones abierto
    const init: Record<string, boolean> = {};
    sections.forEach((s) => {
      init[s.id] = s.id === "operaciones";
    });
    return init;
  });

  // Hidratar desde localStorage + auto-abrir la sección activa
  useEffect(() => {
    let stored: Record<string, boolean> = {};
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (raw) stored = JSON.parse(raw);
    } catch {
      // ignore
    }
    const next: Record<string, boolean> = {};
    sections.forEach((s) => {
      const active = sectionHasActive(s, pathname);
      const remembered = stored[s.id];
      // Auto-abrir la sección con la ruta activa siempre.
      // Caso contrario: usar memoria, default true para Operaciones.
      next[s.id] = active || remembered === true || (remembered === undefined && s.id === "operaciones");
    });
    setOpen(next);
    setHydrated(true);
  }, [pathname]);

  function toggle(id: string) {
    setOpen((prev) => {
      const next = { ...prev, [id]: !prev[id] };
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
      } catch {
        // ignore
      }
      return next;
    });
  }

  return (
    <aside
      className="fixed left-0 top-0 h-screen w-60 border-r flex flex-col"
      style={{
        borderColor: "var(--border-subtle)",
        background: "var(--surface)",
      }}
    >
      <div className="px-5 pt-6 pb-5">
        <Link
          href="/"
          className="flex items-center gap-2 group"
          aria-label="Inicio"
        >
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs font-semibold transition-transform group-hover:scale-105"
            style={{ background: "var(--accent)" }}
          >
            C
          </div>
          <div>
            <div className="font-semibold text-[14px] tracking-tight">
              Cadena
            </div>
            <div
              className="text-[11px]"
              style={{ color: "var(--text-tertiary)" }}
            >
              Suministro AI
            </div>
          </div>
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto px-2 pb-4">
        {sections.map((section) => (
          <SidebarSection
            key={section.id}
            section={section}
            pathname={pathname}
            isOpen={!!open[section.id]}
            onToggle={() => toggle(section.id)}
            hydrated={hydrated}
          />
        ))}
      </nav>

      <div
        className="px-5 py-3 border-t text-[10px]"
        style={{
          borderColor: "var(--border-subtle)",
          color: "var(--text-tertiary)",
        }}
      >
        v0.2 · Sprint 10
      </div>
    </aside>
  );
}

function SidebarSection({
  section,
  pathname,
  isOpen,
  onToggle,
  hydrated,
}: {
  section: Section;
  pathname: string | null;
  isOpen: boolean;
  onToggle: () => void;
  hydrated: boolean;
}) {
  const hasActive = useMemo(
    () => sectionHasActive(section, pathname),
    [section, pathname]
  );

  return (
    <div className="mb-0.5">
      <button
        type="button"
        onClick={onToggle}
        aria-expanded={isOpen}
        aria-controls={`sidebar-section-${section.id}`}
        className="w-full flex items-center justify-between px-3 py-1.5 rounded-md transition-colors hover:bg-[var(--surface)]"
        style={{
          background: "transparent",
          border: "none",
          cursor: "pointer",
        }}
      >
        <span
          className="text-[10px] font-medium uppercase tracking-[0.06em]"
          style={{
            color: hasActive ? "var(--foreground)" : "var(--text-secondary)",
          }}
        >
          {section.title}
        </span>
        <Chevron open={isOpen} />
      </button>

      {/* Grid trick para animar de 0fr a 1fr — sin medir scrollHeight */}
      <div
        id={`sidebar-section-${section.id}`}
        style={{
          display: "grid",
          gridTemplateRows: isOpen ? "1fr" : "0fr",
          transition: hydrated
            ? "grid-template-rows 0.22s cubic-bezier(0.4, 0, 0.2, 1), opacity 0.18s ease"
            : "none",
          opacity: isOpen ? 1 : 0,
        }}
        aria-hidden={!isOpen}
      >
        <div style={{ minHeight: 0, overflow: "hidden" }}>
          <div className="flex flex-col gap-0.5 pt-0.5 pb-2">
            {section.items.map((item) => {
              const active = isActive(item.href, pathname);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`sidebar-link ${active ? "active" : ""}`}
                  tabIndex={isOpen ? 0 : -1}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </div>
      </div>
    </div>
  );
}

function Chevron({ open }: { open: boolean }) {
  return (
    <svg
      width="10"
      height="10"
      viewBox="0 0 10 10"
      fill="none"
      style={{
        transform: open ? "rotate(90deg)" : "rotate(0deg)",
        transition: "transform 0.18s cubic-bezier(0.4, 0, 0.2, 1)",
        color: "var(--text-tertiary)",
      }}
      aria-hidden="true"
    >
      <path
        d="M3.5 2L6.5 5L3.5 8"
        stroke="currentColor"
        strokeWidth="1.5"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}
