# 02 — Roadmap por sprints

> Sprints de 2 semanas. 8 sprints = 16 semanas = ~4 meses al primer cliente externo de pago. Asume 1-2 ingenieros.

## Hitos clave

| Hito | Sprint | Resultado |
|---|---|---|
| **MVP interno** | S1-S3 | Backend + DB; agente refactorizado; Frutas Kelly opera contra la nueva API |
| **Apaga SAE10** | S4 | Facturación 100% por Facturama; Frutas Kelly ya no usa SAE10 para nada |
| **Torre de control** | S5-S6 | Dashboard web operativo (interno) |
| **Email parser** | S7 | Recepción de pedidos por correo (Excel/PDF) |
| **Multi-tenant + venta** | S8 | Onboarding de 1 sub externo; billing Stripe/Conekta |

---

## Sprint 1 (semanas 1-2) — Backend foundation

**Objetivo:** Backend deployable que sirve el modelo de datos.

**Entregables:**
- Repo `cadena/backend/` con FastAPI + Pydantic + SQLAlchemy
- Supabase project creado (Postgres 16)
- Alembic + primera migración con las ~32 tablas de `01-data-model.md`
- RLS policies para todas las tablas con `tenant_id`
- Seed de catálogos SAT (productos/servicios, unidades, regímenes, usos CFDI, formas/métodos de pago, CPs)
- Auth con Supabase Auth (login email + magic link)
- Endpoints CRUD básicos: `tenants`, `users`, `memberships`, `clientes`, `productos`
- Tests unitarios de RLS (un usuario de tenant A no ve datos de tenant B)
- Deploy a Render staging

**Definición de done:** un usuario puede crear cuenta, crear su tenant, agregar 1 cliente y 1 producto. Otro usuario en otro tenant no los ve.

---

## Sprint 2 (semanas 3-4) — Modelo operativo

**Objetivo:** Modelar contratos, lotes, unidades, listas de precios.

**Entregables:**
- Endpoints CRUD: `contratos`, `contratos_lotes`, `unidades_entrega`, `listas_precios`, `precios`, `almacenes`
- Importador Excel para listas de precios (preserva el flujo actual de Frutas Kelly)
- Endpoint `POST /api/import/lista-precios` que parsea xlsx y crea/actualiza productos+precios
- Endpoint `POST /api/import/clientes` desde JSON (migra `clientes.json` y `agentes.json` actuales)
- Endpoints de búsqueda con full-text: `GET /api/productos?q=mango`, `GET /api/clientes?q=ehmo`
- Documentación API auto-generada (FastAPI/OpenAPI)

**Definición de done:** Frutas Kelly tiene en la DB sus 12 contratos, 30-40 unidades, 110 productos, 2 listas de precios (EHMO + SUREÑA). Equivalente al estado actual de JSONs.

---

## Sprint 3 (semanas 5-6) — Pedidos + refactor del agente

**Objetivo:** El WhatsApp agent escribe pedidos en la DB en vez de JSONs.

**Entregables:**
- Endpoints CRUD: `pedidos`, `lineas_pedido`
- Endpoint `POST /api/pedidos/process-excel-bd` que toma el Excel diario de EHMO y crea pedidos
- Endpoint `POST /api/pedidos/from-message` que recibe texto + cliente y crea pedido (lo que hoy hace `pedido_processor`)
- Refactor de `app/pedido_processor.py` y `app/processing_runner.py` del agente: en vez de leer/escribir `storage/pedidos_dia/*.json`, llaman al backend
- Mantener generación de PDFs y Drive uploads exactamente como están (no tocar)
- Migración de pedidos históricos: script que lee `storage/pedidos_dia/*.json` → crea pedidos en DB
- Tests E2E: simulación de mensaje WhatsApp → pedido creado en DB → PDFs generados igual que antes

**Definición de done:** Frutas Kelly opera 1 día completo con el flujo nuevo. Los PDFs y notas de remisión salen idénticas a hoy. El operador no nota la diferencia.

⚠️ **Riesgo alto.** Es la refactorización más grande. Puede tomar 3 sprints en lugar de 1. Plan B: paralelización (agente sigue con JSONs Y escribe a DB; cuando se valida durante 1-2 semanas, se quita el legacy).

---

## Sprint 4 (semanas 7-8) — Facturama integration (apagar SAE10)

**Objetivo:** Frutas Kelly factura desde la nueva plataforma vía Facturama.

**Entregables:**
- Servicio `app/services/facturama_client.py`: timbrado, cancelación, complemento de pago
- Endpoint `POST /api/facturas/from-pedido/:id` que toma un pedido y emite CFDI 4.0
- Soporte para addendas básicas (template engine con Jinja sobre los .xml de `kelly_saas/templates/`)
- Endpoint `POST /api/facturas/:id/cancelar` con motivos SAT
- Endpoint `POST /api/pagos` + `POST /api/pagos/:id/complemento` (PPD)
- Storage de XMLs y PDFs en Supabase Storage
- CSDs: upload cifrado en KMS (Supabase Vault o AWS KMS); refactor para que cada tenant gestione el suyo
- Reportes básicos: estado de cuenta de cliente, libro de facturas del mes
- Pruebas en sandbox de Facturama con 5-10 facturas reales
- Cutover: Frutas Kelly emite primera factura real desde Cadena de Suministro AI

**Definición de done:** Frutas Kelly emite 1 semana completa de facturas desde Cadena de Suministro AI. Verifica con contador externo que las facturas son correctas (XML válido, addendas correctas, totales cuadran). **SAE10 deja de usarse para emitir.** Queda solo como consulta histórica.

---

## Sprint 5 (semanas 9-10) — Torre de control (frontend)

**Objetivo:** Dashboard web para operar el día a día sin ir a la DB.

**Stack:** Next.js 15 + Tailwind + shadcn/ui + tRPC.

**Entregables:**
- Login Supabase Auth
- Selector de tenant (para usuarios con múltiples memberships)
- **Inbox del día:** todos los pedidos entrantes hoy, con filtros por canal, estado, requires_review
- **Detalle de pedido:** ver/editar líneas, asignar lotes, marcar surtido, generar factura
- **Catálogo de clientes:** lista, crear/editar, ver historial
- **Catálogo de productos:** lista, crear/editar, ver kardex (movimientos de inventario)
- **Listas de precios:** ver, importar Excel, editar precio individual
- **Estados de cuenta:** filtro por cliente, ver facturas + abonos + saldo, descargar PDF
- **Reportes básicos:** ventas hoy/semana/mes, top clientes, top productos

**Definición de done:** un operador en almacén puede gestionar el día completo desde la web sin tocar JSON, Excel ni terminal.

---

## Sprint 6 (semanas 11-12) — Inventario + lotes + mermas

**Objetivo:** Manejo real de inventario con FEFO.

**Entregables:**
- Endpoints CRUD: `lotes_inventario`, `movimientos_inventario`, `mermas`
- Lógica FEFO al surtir un pedido: el sistema asigna automáticamente del lote más próximo a caducar
- UI: pantalla de "recibir mercancía" (entrada), "merma del día", "ajuste de inventario"
- Reporte: kardex por producto, lotes próximos a caducar, valor de inventario
- Notas de crédito automáticas cuando se registra una merma vinculada a una factura ya emitida
- Cutover: Frutas Kelly empieza a registrar lotes con caducidad

**Definición de done:** un día de operación normal genera entrada de mercancía, salidas por pedidos asignadas vía FEFO, y mermas registradas con motivo.

---

## Sprint 7 (semanas 13-14) — Email parser AI

**Objetivo:** Recibir pedidos por correo (con Excel/PDF adjunto) y procesarlos automáticamente.

**Entregables:**
- Servicio `app/services/email_parser.py` que conecta IMAP (cuenta dedicada `pedidos@frutaskelly.com`)
- Detección de remitente → match contra `clientes` + `unidades_entrega`
- Extracción de adjuntos (Excel/PDF/imagen) → vision/OCR con Claude
- Creación automática de pedido en DB con `canal=EMAIL` y `requires_review=TRUE` para los primeros casos
- UI: vista "pedidos pendientes de revisión" con diff entre AI extraction y formato canónico
- Aprendizaje activo: cuando el operador corrige, se guarda en `productos.aliases_clientes` para mejorar match futuro

**Definición de done:** EHMO manda el Excel BD diario al correo en vez de WhatsApp; el sistema lo parsea y crea los 20 pedidos del día con review humano para los primeros 3 días.

---

## Sprint 8 (semanas 15-16) — Multi-tenant onboarding + venta

**Objetivo:** Vender el sistema a 1 sub externo.

**Entregables:**
- Wizard de onboarding: crear tenant, RFC, datos fiscales, primer cliente, primer producto, primera factura de prueba
- Self-service para subir CSD (CFDI) cifrado en KMS
- Stripe o Conekta integrado para suscripción mensual
- Plan tiers: Trial 30 días → Sub Solo $1,500 MXN/mes → Sub Pro $3,000 MXN/mes → Enterprise (negociado)
- Página de marketing landing (`cadena.ai` o similar) con form de demo
- Documentación pública de onboarding (README cliente)
- Onboardear 1 sub piloto (ofrecer 3 meses gratis a cambio de feedback)

**Definición de done:** un sub externo puede crear su cuenta, conectar su CSD, importar su lista de precios, recibir pedidos por WhatsApp, facturar a sus clientes. Sin intervención del equipo.

---

## Sprint 9+ (semanas 17+) — Crecimiento

A partir de aquí el roadmap depende del feedback del primer sub externo y del primer principal interesado. Pista de prioridades probable:

- **Reportes para principales** (cuando EHMO o Chaneques entren): dashboard cross-sub, % cumplimiento, productos no surtidos, tiempos de entrega
- **App móvil** (PWA primero, React Native después): para repartidores, captura de acuse de recibo con foto/firma
- **Carta Porte** (si tienes flota propia)
- **Voz** (Whisper): pedidos por audio de WhatsApp procesados
- **AI copilot** (chat conversacional dentro de la app): "muéstrame ventas de mango en abril", "qué clientes me deben más de 30 días"
- **Integraciones**: Aspel COI / Contpaqi / QuickBooks para que el contador no se queje
- **Mercado horizontal**: si llega un caso de uso fuera de gobierno (carnicerías, restaurantes mayoristas), evaluar

---

## Riesgos y mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigación |
|---|---|---|---|
| Refactor del agente (S3) sale más largo | Alta | Alto | Plan B: dual-write durante 2 semanas |
| Facturama no soporta una addenda específica | Media | Alto | Probar todas las addendas reales en S4. Si falla una, evaluar PAC alterno (Solfact, Finkok) |
| RLS performance con 100k+ pedidos | Baja | Medio | Particionado por tenant_id si se ve degradación en S6 |
| Primer sub externo no cierra | Media | Alto | Tener 2-3 candidatos warm desde S6 |
| EHMO/Chaneques rechazan demo | Media | Bajo | Las ventas Tier 3 no son gating para Tier 2; puedes vivir 12 meses con Tier 1+2 |
| Equipo solo de 1 persona | Alta | Alto | Aceptar que el roadmap se duplica en duración. Vale la pena por el control de producto |

---

## Métricas que vamos a monitorear

- **Operativas (Frutas Kelly como tenant):** % pedidos sin intervención humana, tiempo promedio de pedido a factura, errores de captura/mes
- **Producto (cuando haya 2+ tenants):** DAU, retention, NPS, % features usados
- **Negocio:** MRR, CAC, LTV, churn

---

## Decisiones explícitas sobre lo que NO hacemos en MVP

- **No reescribir el WhatsApp agent en TypeScript.** Sigue en Python.
- **No microservicios.** Monolito modular hasta justificar split.
- **No Kafka/ClickHouse/Temporal.** Postgres LISTEN/NOTIFY + queue simple en Redis si hace falta.
- **No app móvil nativa.** PWA es suficiente para v1.
- **No marketplaces (MELI/Amazon).** No aplica a gobierno.
- **No Carta Porte.** Hasta que tengas flota propia.
- **No copilot conversacional dentro de la app.** Después de validar el flujo operativo.
- **No multi-país.** México only.
- **No multi-moneda.** MXN only (estructura DB lo soporta para futuro).
