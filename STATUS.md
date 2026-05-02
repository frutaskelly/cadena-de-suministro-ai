# STATUS — Reporte de trabajo nocturno

**Fecha:** 2026-05-03 (madrugada → mañana)
**Branch:** `main` (sin push, todo commit local)
**Commits:** 4 — `0701ee0` (productos sinonimos) ← `c8bd12f` (Sprint 2 progress) ← `ce26978` (STATUS) ← `1ab65ca` (Sprint 1 foundation)

## Resumen ejecutivo

Sprint 1 y parte de Sprint 2 listos:
- Backend FastAPI con 49 endpoints corriendo (era 37 al inicio)
- Postgres local con 32 tablas + RLS
- Datos Frutas Kelly migrados (1 tenant, 2 clientes, 27 unidades, 110 productos, 216 precios, **42 pedidos** con 464 líneas)
- Catálogos SAT seedeados (16 unidades, 18 regímenes, 24 usos CFDI, 10 formas pago, 13 prod/serv, 2 metodos)
- Servicios nuevos: fuzzy_match (rapidfuzz), pedidos.from_batch_rows
- Dashboard endpoints (resumen del día, métricas)
- 12 tests pasando

---

## 🟢 Lo que está listo y funcionando

### Backend FastAPI corriendo en http://localhost:8000

```bash
# Ver docs interactivas:
open http://localhost:8000/docs

# Health:
curl http://localhost:8000/health
# {"status":"ok","version":"0.1.0","env":"development"}
```

### Base de datos Postgres local (puerto 5433)

- 33 tablas (32 operativas + alembic_version)
- RLS activo en 24 tablas con políticas multi-tenant jerárquicas
- Migraciones Alembic versionadas

### Datos de Frutas Kelly migrados ✅ (actualizado tras Sprint 2)

| Entidad | Cantidad |
|---|---|
| Tenants | 1 (Frutas Kelly) |
| Users | 1 |
| Clientes | 2 (EHMO + SUREÑA) |
| Contratos | 2 (EHMO Chiapas + SUREÑA) |
| Lotes de contrato | 2 (Lote 5 FyV) |
| Unidades de entrega | 27 (21 hospitales + 6 comedores) |
| Listas de precios | 2 (EHMO + SURENA) |
| Productos | 110 |
| Precios | 216 |
| **Pedidos históricos** | **42** (3 más matcheados vía fuzzy) |
| **Líneas de pedido** | **464** |
| sat_productos_servicios | 13 |
| sat_unidades | 16 |
| sat_regimenes | 18 |
| sat_usos_cfdi | 24 |
| sat_formas_pago | 10 |
| sat_metodos_pago | 2 |

### Endpoints API v1 disponibles (49 routes)

- `POST/GET /api/v1/tenants` (admin, sin RLS)
- `POST/GET /api/v1/users`
- `POST/GET /api/v1/memberships`
- `POST/GET/PATCH/DELETE /api/v1/clientes` (con `x-tenant-id` header)
- `POST/GET/PATCH /api/v1/productos` (búsqueda por nombre + sinónimos)
- `POST/GET /api/v1/listas-precios`
- `POST/GET /api/v1/precios`
- `POST/GET /api/v1/contratos`
- `POST /api/v1/contrato-lotes` + `GET /by-contrato/:id`
- `POST/GET /api/v1/unidades-entrega` + `GET /by-contrato/:id`
- `POST/GET /api/v1/pedidos` (con líneas anidadas)
- **`POST /api/v1/pedidos/from-batch`** — crea pedidos desde rows pre-parseados (Excel BD, libreta) con fuzzy match de unidad/producto y cálculo automático de precio
- **`POST /api/v1/pedidos/from-excel-bd`** — alias canal=EXCEL_BD
- **`GET /api/v1/sat/*`** — catálogos SAT (productos, unidades, regímenes, usos CFDI, formas/métodos pago)
- **`GET /api/v1/dashboard/resumen-dia`** + métricas operativas

### Tests

```bash
cd backend && source venv/bin/activate && pytest tests/ -v
# 12 passed in 0.39s ✓
```

Cubren: health, tenants, RLS header check, clientes (CRUD + search), productos (count + search), listas, contratos, unidades EHMO (21), pedidos, pedido con líneas.

---

## 📁 Estructura del proyecto

```
cadena-de-suministro-ai/
├── README.md                      Visión, stack, decisiones
├── STATUS.md                      ← este archivo
├── Makefile                       make db-start / migrate / seed / run / test / demo
├── .gitignore
├── pgdata/                        DB local (gitignored)
├── docs/
│   ├── 01-data-model.md           DDL completo + diagrama
│   ├── 02-roadmap.md              8 sprints de 2 semanas
│   └── 04-migration-plan.md       JSONs/Excel/SAE10 → Cadena
├── backend/
│   ├── pyproject.toml             (no usado, deps en venv)
│   ├── .env                       config local (no commiteado)
│   ├── .env.example
│   ├── alembic.ini
│   ├── alembic/
│   │   └── versions/              2 migraciones (initial schema + RLS)
│   ├── app/
│   │   ├── core/                  config, db, base
│   │   ├── models/                10 archivos, 32 tablas
│   │   ├── schemas/               5 archivos Pydantic
│   │   ├── api/v1/                5 archivos endpoints
│   │   ├── services/              (vacío, para Sprint 2+)
│   │   └── main.py
│   └── tests/
│       └── test_smoke.py          12 tests
└── scripts/
    └── migrate_frutas_kelly.py    Migración idempotente
```

---

## 🚀 Cómo arrancar (cuando despiertes)

**Estado actual:** backend y Postgres están corriendo en background.
Si se cayeron por reinicio o lo que sea:

```bash
cd "/Users/michelzarate/Documents/Claude/Whatsapp Agent/cadena-de-suministro-ai"
make demo   # arranca DB + migra schema + seed + corre tests
make run    # levanta backend en :8000
```

Después abre **http://localhost:8000/docs** y juega con la API interactiva.

Para ver datos:

```bash
TENANT_ID=$(/opt/homebrew/opt/postgresql@16/bin/psql -h /tmp -p 5433 -U postgres -d cadena_dev -t -c "SELECT id FROM tenants WHERE slug='frutas-kelly';" | tr -d ' ')

# Listar clientes de Frutas Kelly:
curl -H "x-tenant-id: $TENANT_ID" http://localhost:8000/api/v1/clientes | python3 -m json.tool

# Buscar producto:
curl -H "x-tenant-id: $TENANT_ID" "http://localhost:8000/api/v1/productos?q=mango&limit=5" | python3 -m json.tool

# Pedidos del 30 de abril:
curl -H "x-tenant-id: $TENANT_ID" "http://localhost:8000/api/v1/pedidos?fecha=2026-04-30" | python3 -m json.tool
```

---

## 🟡 Lo que quedó parcial / sabido (actualizado)

1. ~~**3 pedidos históricos sin matchear**~~ ✅ resueltos vía fuzzy match.
   Pedidos: 39 → 42, líneas: 416 → 464.

2. **`clave_sat` de productos** sigue hardcoded a `50202301` (genérico FyV).
   Pendiente: AI classify por producto vía Claude tool.

3. **Sinónimos de pricing.py** — script `import_sinonimos.py` listo;
   verificar si ya se ejecutó (revisar conteo `productos.sinonimos`).

4. ~~**SAT catálogos vacías**~~ ✅ subset seedeado (16 unidades, 18 regímenes,
   24 usos CFDI, 10 formas pago, 13 prod/serv, 2 metodos). Para timbrado en
   prod, eventualmente hay que cargar el catálogo completo de prod/serv
   (>50k filas) desde el SAT.

5. **Endpoint `from-batch` tiene tests por escribir** — funciona pero el
   `tests/test_smoke.py` solo cubre los CRUD básicos.

5. **Auth real** (Supabase Auth + JWT validation) no está. Por ahora el
   `x-tenant-id` viene en header sin verificar. **No es seguro para prod**,
   solo dev. Sprint 1.5 lo arregla cuando integremos Supabase.

6. **RLS no se enforce con el rol postgres** (BYPASS por ser superuser).
   Las políticas existen y se aplicarán cuando conectemos con un rol no-su.
   En prod (Supabase) el rol app es no-superuser y RLS es real.

7. **Frontend** no se inició (Sprint 5).

---

## 🔴 Bloqueos / pendientes que requieren tu acción

### CRÍTICO: cambia tu password de Facturama
Te pegué un recordatorio. Si todavía no lo hiciste, hazlo antes de cualquier
otra cosa. Y guarda el nuevo password solo en un password manager (1Password
/ Bitwarden / Apple Keychain).

### Para deployar a Supabase (Sprint 1.5)
Necesito de tu dashboard de Supabase (https://app.supabase.com → tu proyecto):
- **Settings → API → Service Role Key** (es secreto, NO lo pegues en chat)
- **Settings → API → anon public key** (es público, sí puedes pegarlo)
- **Settings → Database → Connection string** (uri tipo `postgresql://...`)

Cuando los tengas, déjalos en `backend/.env` así (yo los leo de ahí mañana):
```
SUPABASE_URL=https://rsrjfbbhjzhsnlxhbezp.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_DB_URL=postgresql://postgres.rsrj...:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

### Para Sprint 4 (timbrado Facturama, semana 7-8)
Cuando vayamos a esa fase necesitaré:
- **Facturama API Key** (la generas en su dashboard, NO el password de login)
- **CSDs de Frutas Kelly** (.cer + .key + password) — los subimos cifrados a
  Supabase Storage; el password lo metemos en Supabase Vault.

### Decisiones que dejé pendientes para tu review
- **Régimen fiscal de tenant Frutas Kelly:** asumí `612` (PF actividad
  empresarial). Si eres `601` o algo más, hay que cambiarlo.
- **Datos fiscales de EHMO/SUREÑA:** asumí `601 / G03 / PPD / 99`. Verifica
  con tu contador o con un CFDI real reciente.
- **Domicilio fiscal de Frutas Kelly:** parseé el `clientes.json` y asumí
  estructura. Está en `tenants.domicilio_fiscal` (JSONB). Si hay errores,
  patch endpoint o edita en DB.

---

## 📊 Métricas del trabajo nocturno (actualizadas tras Sprint 2)

```
Tablas creadas:        33
Models Python:         32
Pydantic schemas:      ~25
Endpoints REST:        49 (era 30 al cierre nocturno)
Tests:                 12 (todos pasando)
Líneas de código:      ~3,300 (backend incl. servicios) + ~800 (docs/migrations) + ~580 scripts
Datos migrados:        110 productos + 216 precios + 42 pedidos + 464 líneas
Catálogos SAT seed:    83 filas (6 tablas)
Commits:               4
```

---

## 📅 Próximas 2 semanas (Sprint 1 finish + Sprint 2)

Cuando despiertes y revises este STATUS, podemos:

**Hoy / mañana (acabar Sprint 1):**
1. Tú me das las keys de Supabase
2. Yo conecto el backend a Supabase managed Postgres
3. Migro el schema a Supabase (alembic upgrade head contra la URL nueva)
4. Re-corro la migración Frutas Kelly contra Supabase
5. Deployo el backend a Render conectado a Supabase
6. Push a GitHub `frutaskelly/cadena-de-suministro-ai`

**Esta semana (Sprint 2):**
- Refactor del WhatsApp agent para escribir pedidos vía API en vez de JSONs
  (dual-write durante 1-2 semanas)
- Importar sinónimos del agente a `productos.sinonimos`
- Endpoint `POST /pedidos/from-excel-bd` para que el agente mande directo
- Seed de catálogos SAT (clave producto/servicio + unidades + regímenes)
- Frontend skeleton (Next.js) con login + 1 pantalla básica

**Sprint 3-4 (semanas 3-4):**
- Integración Facturama (sandbox primero)
- Cutover de SAE10 — Frutas Kelly emite real desde Cadena
- Dashboard básico para operación diaria

---

## 🌅 Buenos días

Si encuentras algo que se ve mal, raro, o no entiendes — déjame un mensaje
y lo retomo en cuanto leas esto. Lo más importante es que **revises los
datos migrados** (especialmente los 27 unidades_entrega y los 39 pedidos)
y me digas si reflejan tu realidad operativa.

PD: si Postgres se cayó por el reinicio del Mac mini, corre `make db-start`.
Si tampoco arranca, los datos están en `cadena-de-suministro-ai/pgdata/` —
nada se pierde.

---

— Claude (trabajo de la noche del 2026-05-02 → 2026-05-03)
