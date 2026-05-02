# Cadena de Suministro AI — Plataforma para cadena gobierno-alimentos

> **Repo:** `frutaskelly/cadena-de-suministro-ai`
> **Producto:** plataforma SaaS para coordinación de la cadena de suministro de alimentos en contratos gubernamentales mexicanos.

## Visión

Plataforma SaaS para la cadena de suministro de alimentos en contratos gubernamentales mexicanos. Conecta tres actores:

1. **Contratistas principales** (EHMO, Chaneques, etc.) — los que ganan licitaciones de SEDENA / IMSS-Bienestar / DIF / etc.
2. **Subcontratistas** (Frutas Kelly y similares) — los que surten lotes específicos en zonas asignadas.
3. **Unidades de entrega** — hospitales, comedores, militares, escuelas, reclusorios.

El producto resuelve la coordinación entre las 3 capas. Reduce errores administrativos, da visibilidad real-time al principal, estandariza la entrada de pedidos al sub, y deja acuse digital en la unidad.

## Diferenciador

**No es un ERP genérico ni un AI chatbot.** Es una plataforma vertical con AI nativo, diseñada específicamente para la cadena gobierno-alimentos. La inteligencia está en:

- Ingesta multi-canal (WhatsApp + email + Excel BD + libreta foto + voz)
- Normalización inteligente de pedidos no estándar (cada unidad pide diferente)
- Manejo de lotes con caducidad / FEFO
- Generación CFDI 4.0 + complemento de pago + addendas específicas (Walmart, hospitales DIF, etc.)
- Coordinación multi-sub para el principal (visibilidad cross-sub)

## Stack

| Capa | Tecnología | Hosting |
|---|---|---|
| Backend | Python 3.11 + FastAPI (monolito modular) | Render |
| Database | PostgreSQL 16 + RLS | Supabase managed |
| Cache | Redis | Render add-on |
| Frontend | Next.js 15 + Tailwind + shadcn/ui | Vercel |
| Auth | Supabase Auth | Supabase |
| File storage | Supabase Storage (S3 detrás) | Supabase |
| Facturación | Facturama API | externo |
| AI | Claude Sonnet 4.6 (Anthropic) | externo |
| WhatsApp | Meta WhatsApp Business API | externo |
| Email parser | Claude (vision + tool use) | externo |

**Costo infra estimado al inicio:** $50-150 USD/mes para 1-3 tenants. Escala lineal.

## Estructura del repo (cuando exista)

```
cadena/
├── README.md
├── docs/
│   ├── 01-data-model.md       Modelo de datos PostgreSQL completo
│   ├── 02-roadmap.md          Plan por sprints
│   ├── 03-api-contract.md     Endpoints REST + tRPC
│   └── 04-migration-plan.md   Migración Frutas Kelly → Cadena de Suministro AI
├── backend/
│   ├── pyproject.toml
│   ├── alembic/              Migraciones DB
│   ├── app/
│   │   ├── core/             config, db, auth
│   │   ├── modules/          tenants, clientes, productos, pedidos, facturas, etc.
│   │   ├── services/         lógica de negocio (procesador, facturador, etc.)
│   │   └── main.py
│   └── tests/
├── frontend/
│   ├── app/                  Next.js 15 App Router
│   ├── components/
│   └── lib/
├── agent/                    El WhatsApp agent (refactorizado para llamar API)
└── infra/
    ├── supabase/             Migraciones + RLS policies
    └── render.yaml
```

## Estado actual

**Fase de diseño.** Estos docs (`docs/01-data-model.md` y `docs/02-roadmap.md`) son el contrato antes de escribir código.

## Reusos

- **`../Whatsapp_agent/`** — agente actual de Frutas Kelly. ~9,700 LOC Python en producción. Se refactoriza en Sprint 2-3 para llamar a la API en vez de leer JSONs.
- **`../kelly_saas/`** — reverse engineering completo de Aspel-SAE 10. Referencia para schema, plantillas CFDI 4.0, catálogos SAT, reglas de negocio.

## Decisiones tomadas

| Decisión | Razón |
|---|---|
| Nicho vertical (cadena gov-alimentos), no ERP horizontal | Defensible, network effects, mercado real desatendido |
| Python + FastAPI (no TypeScript) | Reutilizar 10K LOC del agente; cero re-skill |
| Monolito modular (no microservicios) | Velocidad > pureza arquitectónica al inicio |
| PostgreSQL + RLS multi-tenant jerárquico | Principal tenant ve a sus sub-tenants |
| Facturama como PAC | Decisión del usuario; soporta CFDI 4.0 + pagos + cancelación |
| Reusar agente WhatsApp existente | Está probado en producción |
| Email parser temprano (sprint 4-5) | Es como pide EHMO (Excel adjunto al correo) |

## Decisiones pendientes

- Nombre comercial final (¿Cadena de Suministro AI? ¿Otro?)
- ¿Auth0 o Supabase Auth? (default propuesto: Supabase)
- ¿Stripe o Conekta para billing? (Conekta tiene mejor experiencia MX)
- ¿Carbone.io o WeasyPrint para PDFs? (default propuesto: WeasyPrint para empezar)
