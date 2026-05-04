"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const sections = [
  {
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
    title: "WhatsApp",
    items: [
      { href: "/agentes-whatsapp", label: "Agentes" },
      { href: "/documentos", label: "Documentos" },
    ],
  },
  {
    title: "Compras",
    items: [{ href: "/ordenes-compra", label: "Órdenes de compra" }],
  },
  {
    title: "Catálogo",
    items: [
      { href: "/productos", label: "Productos" },
      { href: "/conversiones", label: "Conversiones" },
      { href: "/listas-precios", label: "Listas de precios" },
      { href: "/clientes", label: "Clientes" },
    ],
  },
  {
    title: "Facturación",
    items: [{ href: "/cfdi", label: "CFDI Preview" }],
  },
];

export default function Sidebar() {
  const pathname = usePathname();
  return (
    <aside
      className="fixed left-0 top-0 h-screen w-60 border-r flex flex-col"
      style={{ borderColor: "var(--border-subtle)", background: "var(--surface)" }}
    >
      <div className="px-5 pt-6 pb-4">
        <div className="flex items-center gap-2">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center text-white text-xs font-semibold"
            style={{ background: "var(--accent)" }}
          >
            C
          </div>
          <div>
            <div className="font-semibold text-[14px] tracking-tight">
              Cadena
            </div>
            <div className="text-[11px]" style={{ color: "var(--text-tertiary)" }}>
              Suministro AI
            </div>
          </div>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 pb-4">
        {sections.map((section) => (
          <div key={section.title} className="mb-5">
            <div className="text-overline px-3 mb-1.5">{section.title}</div>
            <div className="flex flex-col gap-0.5">
              {section.items.map((item) => {
                const active =
                  item.href === "/"
                    ? pathname === "/"
                    : pathname?.startsWith(item.href);
                return (
                  <Link
                    key={item.href}
                    href={item.href}
                    className={`sidebar-link ${active ? "active" : ""}`}
                  >
                    {item.label}
                  </Link>
                );
              })}
            </div>
          </div>
        ))}
      </nav>

      <div
        className="px-5 py-4 border-t text-[11px]"
        style={{
          borderColor: "var(--border-subtle)",
          color: "var(--text-tertiary)",
        }}
      >
        v0.2 · Sprint 8
      </div>
    </aside>
  );
}
