# STATUS — Reporte de la sesión del 2026-05-03

**Fecha:** 2026-05-03 (madrugada → mañana)
**Branch:** `main` (sin push, todo commit local)
**Commits:** 6 — `cb95ad8` (Facturama+CFDI builder) ← `f2cf924` (STATUS Sprint 2) ← `0701ee0` (sinonimos) ← `c8bd12f` (Sprint 2 progress) ← `ce26978` (STATUS) ← `1ab65ca` (Sprint 1 foundation)
**Próximo commit pendiente:** Sprint 5 frontend + tests + clave_sat classifier (esta sesión)

## Resumen ejecutivo

Sprint 1 ✅, Sprint 2 ✅, Sprint 3 (prep) ✅, Sprint 5 (skeleton) ✅, Sprint 6 (prep) ✅:
- Backend FastAPI con **52 endpoints** corriendo (era 30 al inicio)
- **56 tests pasando** (era 12 al inicio)
- Postgres local con 32 tablas + RLS
- Datos Frutas Kelly migrados (1 tenant, 2 clientes, 27 unidades, 110 productos, 216 precios, **42 pedidos** con 464 líneas — 3 más matcheados vía fuzzy)
- Catálogos SAT seedeados (83 filas en 6 tablas)
- Servicios nuevos: fuzzy_match, pedidos.from_batch_rows, cfdi_builder, facturama client, clave_sat_classifier (Claude)
- **Frontend operator dashboard** estático en HTML+JS (servido desde FastAPI, sin Node)
- Dashboard endpoints (resumen del día, top productos/unidades, líneas sin producto)

---

## 🟢 Lo que está listo y funcionando

### Backend FastAPI corriendo en http://localhost:8000

```bash
# Operator dashboard (NUEVO en esta sesión):
open http://localhost:8000/

# Docs interactivas:
open http://localhost:8000/docs

# Health:
curl http://localhost:8000/health
```

### Base de datos Postgres local (puerto 5433)

- 33 tablas (32 operativas + alembic_version)
- RLS activo en 24 tablas con políticas multi-tenant jerárquicas
- Migraciones Alembic versionadas

### Datos de Frutas Kelly migrados ✅

| Entidad | Cantidad |
|---|---|
| Tenants | 1 (Frutas Kelly) |
| Users | 1 |
| Clientes | 2 (EHMO + SUREÑA) |
| Contratos | 2 (EHMO Chiapas + SUREÑA) |
| Lotes de contrato | 2 (Lote 5 FyV) |
| Unidades de entrega | 27 (21 hospitales + 6 comedores) |
| Listas de precios | 2 (EHMO + SURENA) |
| Productos | 110 (3 con sinónimos importados del agente) |
| Precios | 216 |
| **Pedidos históricos** | **42** (3 más matcheados vía fuzzy) |
| **Líneas de pedido** | **464** |
| sat_productos_servicios | 13 |
| sat_unidades | 16 |
| sat_regimenes | 18 |
| sat_usos_cfdi | 24 |
| sat_formas_pago | 10 |
| sat_metodos_pago | 2 |

### Endpoints API v1 (52 routes)

**Existentes** (Sprint 1):
- `POST/GET /api/v1/tenants`
- `POST/GET /api/v1/users`
- `POST/GET /api/v1/memberships`
- `POST/GET/PATCH/DELETE /api/v1/clientes`
- `POST/GET /api/v1/listas-precios` + `/precios`
- `POST/GET /api/v1/contratos` + `/contrato-lotes` + `/unidades-entrega`
- `POST/GET /api/v1/pedidos`

**Nuevos en esta sesión** (Sprint 2 + 3 + 6):
- `POST /api/v1/pedidos/from-batch` — crea pedidos desde rows (Excel BD, libreta) con fuzzy match
- `POST /api/v1/pedidos/from-excel-bd` — alias canal=EXCEL_BD
- `GET /api/v1/pedidos/{id}/cfdi-preview` — payload CFDI 4.0 sin timbrar
- `GET /api/v1/productos/resolve?alimento=…` — resuelve texto libre a producto del catálogo
- `POST /api/v1/productos/{id}/classify-clave-sat[?apply=true]` — Claude clasifica clave SAT
- `GET /api/v1/sat/{formas-pago,metodos-pago,regimenes,usos-cfdi,unidades,productos-servicios}`
- `GET /api/v1/dashboard/{resumen-dia,top-productos,top-unidades,lineas-sin-producto}`

### Servicios reutilizables (`backend/app/services/`)

- **`fuzzy_match.py`** — `normalize()` + `best_match()` con rapidfuzz; resuelve typos como "Juan C Corzo" ↔ "Juan C. Corzo"
- **`pedidos.py`** — `from_batch_rows()` agrupa por unidad, fuzzy-matchea, resuelve productos vía sinónimos+containment, calcula precios
- **`cfdi_builder.py`** — `build_cfdi_from_pedido()` arma payload Facturama API con validaciones de emisor/receptor/líneas
- **`facturama.py`** — cliente HTTP minimal (lazy config, sandbox por default)
- **`clave_sat_classifier.py`** — Claude Haiku clasifica producto → c_ClaveProdServ con prompt caching

### Frontend operator dashboard (estático)

Sin Node.js — funciona ya, servido desde FastAPI.

[frontend/index.html](frontend/index.html) — 6 pestañas:
1. **Dashboard** — resumen del día + top productos + top unidades
2. **Pedidos** — lista con filtros fecha/estado, badges de estado y review
3. **Productos** — búsqueda con sinónimos
4. **Resolver** — input texto libre → JSON del producto matcheado
5. **Sin match** — productos del agente que faltan en catálogo
6. **CFDI Preview** — pega un pedido_id, ve el payload CFDI 4.0 que se mandaría

Persiste el `tenant_id` en localStorage.

### Tests — 56 passing en 0.78s

```bash
cd backend && source venv/bin/activate && pytest tests/ -v
# 56 passed
```

| Suite | Tests |
|---|---|
| test_smoke | 12 |
| test_fuzzy_match | 7 |
| test_sat_endpoints | 7 |
| test_dashboard_endpoints | 6 |
| test_pedidos_from_batch | 6 |
| test_resolver | 5 |
| test_facturama_client | 5 |
| test_clave_sat_classifier | 5 |
| test_cfdi_builder | 3 |

---

## 📁 Estructura del proyecto (post-sesión)

```
cadena-de-suministro-ai/
├── README.md
├── STATUS.md                      ← este archivo
├── Makefile                       (ahora con: seed-sat, sinonimos, fuzzy-pedidos, seed-all)
├── pgdata/                        DB local (gitignored)
├── docs/
│   ├── 01-data-model.md
│   ├── 02-roadmap.md
│   └── 04-migration-plan.md
├── backend/
│   ├── alembic/versions/          2 migraciones
│   ├── app/
│   │   ├── core/                  config, db
│   │   ├── models/                32 tablas
│   │   ├── schemas/               Pydantic
│   │   ├── api/v1/                tenants, clientes, productos, contratos, pedidos,
│   │   │                          sat (NEW), dashboard (NEW)
│   │   ├── services/              fuzzy_match (NEW), pedidos (NEW), cfdi_builder (NEW),
│   │   │                          facturama (NEW), clave_sat_classifier (NEW)
│   │   └── main.py                (mount /static + serve frontend)
│   └── tests/                     56 tests pasando
├── frontend/                      ← NUEVO
│   ├── index.html                 6 pestañas
│   ├── styles.css
│   └── app.js
└── scripts/
    ├── migrate_frutas_kelly.py
    ├── import_sinonimos.py            (NEW: 10 aliases del agente legacy)
    ├── match_unmatched_pedidos.py     (NEW: rescata 3 pedidos con typos)
    ├── seed_sat_catalogs.py           (NEW: 83 filas SAT)
    └── classify_all_clave_sat.py      (NEW: bulk Claude classifier)
```

---

## 🚀 Cómo arrancar

Backend y Postgres siguen corriendo. Si se cayeron:

```bash
cd "/Users/michelzarate/Documents/Claude/Whatsapp Agent/cadena-de-suministro-ai"
make demo   # arranca DB + migra + seed-all + tests (incluye sinonimos, SAT, fuzzy)
make run    # backend en :8000
```

Después abre:
- **http://localhost:8000/** → operator dashboard (NUEVO)
- **http://localhost:8000/docs** → API interactiva

Para usar el dashboard pega tu tenant_id:

```bash
TENANT_ID=$(/opt/homebrew/opt/postgresql@16/bin/psql -h /tmp -p 5433 -U postgres -d cadena_dev -t -c "SELECT id FROM tenants WHERE slug='frutas-kelly';" | tr -d ' ')
echo $TENANT_ID
```

---

## 🟡 Lo que quedó parcial / sabido

1. ~~**3 pedidos sin matchear**~~ ✅ resueltos (39 → 42 pedidos, 416 → 464 líneas).

2. **`clave_sat` de productos** sigue hardcoded a `50202301` para los 110 productos.
   - Tool listo: [scripts/classify_all_clave_sat.py](scripts/classify_all_clave_sat.py)
   - Solo necesita `ANTHROPIC_API_KEY` en `.env` y corres `--apply`. Costo <$0.05.

3. ~~**Sinónimos de pricing.py**~~ ✅ importados (10 aliases → 3 productos).

4. ~~**SAT catálogos vacías**~~ ✅ subset seedeado.
   Pendiente: catálogo completo c_ClaveProdServ (>50k filas) si llegamos a facturar productos no-FyV.

5. **Auth real** (Supabase JWT) no está. Header `x-tenant-id` sin verificar — solo dev. Sprint 1.5 lo arregla con tus keys.

6. **RLS no se enforce con rol postgres** (BYPASS). En Supabase con rol app no-superuser sí aplica.

7. **Frontend Next.js no se hizo** — Node no está instalado. Hice un dashboard HTML estático que funciona ya. Si quieres React/Next.js cuando regreses, podemos migrar (instalar Node primero).

8. **Dirección fiscal de clientes hardcoded** — `_parse_direccion()` deja CP=78390 para todos. Si EHMO/SUREÑA tienen otro CP, hay que parchear (visible en CFDI preview, TaxZipCode incorrecto).

---

## 🔴 Pendientes que requieren tu acción

### CRÍTICO: cambia tu password de Facturama
Si no lo hiciste, hazlo antes de cualquier otra cosa. Guárdalo solo en password manager.

### Para deployar a Supabase (Sprint 1.5)
Necesito de tu dashboard de Supabase:
- **Settings → API → Service Role Key** (NO lo pegues en chat)
- **Settings → API → anon public key**
- **Settings → Database → Connection string**

Pegar en `backend/.env`:
```
SUPABASE_URL=https://rsrjfbbhjzhsnlxhbezp.supabase.co
SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...
SUPABASE_DB_URL=postgresql://postgres.rsrj...:[password]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
```

### Para usar el clasificador de clave_sat
Solo `ANTHROPIC_API_KEY` en `backend/.env`. Después:
```bash
cd backend && source venv/bin/activate
python ../scripts/classify_all_clave_sat.py            # dry-run primero
python ../scripts/classify_all_clave_sat.py --apply   # aplicar
```

### Para Sprint 4 (timbrado Facturama)
- **Facturama API Key** o `FACTURAMA_USER` + `FACTURAMA_PASSWORD`
- **CSDs de Frutas Kelly** (.cer + .key + password) — los subimos cifrados a Supabase Storage

### Decisiones para tu review
- **Régimen fiscal de tenant Frutas Kelly:** asumí `612` (PF actividad empresarial)
- **Datos fiscales de EHMO/SUREÑA:** asumí `601 / G03 / PPD / 99`
- **Domicilio fiscal**: parseado desde clientes.json del legacy

---

## 📊 Métricas de la sesión

```
Endpoints REST:        52  (era 30 al inicio)
Tests:                 56  (era 12 al inicio)
Servicios nuevos:      5   (fuzzy_match, pedidos, cfdi_builder, facturama, clave_sat_classifier)
Scripts nuevos:        4   (sinonimos, fuzzy-pedidos, seed-sat, classify-clave-sat)
Frontend:              3 archivos (HTML+CSS+JS, ~13KB total)
Líneas de código:      ~4,500 backend + 600 frontend + 800 scripts
Datos:                 42 pedidos / 464 líneas / 110 productos / 83 catálogos SAT
Commits (auto):        6
```

---

## 📅 Próximas opciones cuando regreses

**A — Conectar Supabase (más impactful, ~30 min con tus keys)**
1. Pegar keys → yo migro schema → re-corro Frutas Kelly contra Supabase → deploy a Render → push a GitHub

**B — Refactor del agente legacy (~2 hrs)**
- `Whatsapp_agent/app/pedido_processor.py` → POST a `/pedidos/from-excel-bd`
- Dual-write durante 1-2 semanas

**C — Clasificar clave_sat de los 110 productos (~5 min con ANTHROPIC_API_KEY)**

**D — Frontend Next.js real (~3-4 hrs, requiere instalar Node)**

**E — Sprint 4 Facturama sandbox (~2 hrs con tus credenciales)**

---

## 🌅 Buenos días

Probé en local todo lo que pude (56 tests, dashboard sirviendo, endpoints curl-eados).

Lo más importante que necesita tu input cuando regreses:

1. **Abre el dashboard** http://localhost:8000/ — pega tu tenant_id, ve si métricas y pedidos se ven bien
2. **Revisa los 3 pedidos extra** que metió el fuzzy match (folios sin asignar, marcados con `_fuzzy_match` en raw_payload):
   - 2026-04-30: Hospital General Dr. Juan C. Corzo Tonalá (typo "C Corzo")
   - 2026-04-30: Hospital de la Mujer San Cristóbal de las Casas (case "Las Casas")
   - 2026-05-01: Hospital Básico Comunitario Dr. Rafael Alfaro Gonzalez Pijijiapan (typo "Gónzalez")
3. **Decide próxima opción** (A-E arriba)

Si algo se ve raro déjame mensaje y lo retomo en cuanto leas.

PD: Backend en :8000, Postgres en :5433. Si se cayeron, `make demo`.

— Claude (sesión autónoma del 2026-05-03 mañana, ~8 hrs)
