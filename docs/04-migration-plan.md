# 04 — Plan de migración: Frutas Kelly → Cadena de Suministro AI

> Cómo mover los datos actuales (JSONs + Excel + SAE10) a la nueva DB sin romper la operación.

## Inventario de fuentes actuales

| Origen | Formato | Destino en Cadena de Suministro AI |
|---|---|---|
| `Whatsapp_agent/storage/clientes.json` | JSON | `clientes` + `unidades_entrega` (split) |
| `Whatsapp_agent/storage/agentes.json` | JSON | `clientes.config_agente` (custom_fields) |
| `Whatsapp_agent/data/Lista_Precios_EHMO.xlsx` | Excel | `productos` + `listas_precios` + `precios` |
| `Whatsapp_agent/data/Lista_Precios_SURENA.xlsx` | Excel | (ídem para lista SURENA) |
| `Whatsapp_agent/data/Lista_Precios_EHMO_DIF.xlsx` | Excel | (ídem) |
| `Whatsapp_agent/storage/pedidos_dia/*.json` | JSON (uno por día) | `pedidos` + `lineas_pedido` |
| `Whatsapp_agent/storage/extras_dia/*.json` | JSON | `pedidos` con `tipo=EXTRA` |
| `Whatsapp_agent/storage/folio_counter*.json` | JSON | Inicializa `tenants.config.folio_next` |
| `Whatsapp_agent/storage/event_log.jsonl` | JSONL | `events_log` (mejor esfuerzo) |
| `Whatsapp_agent/storage/message_log.jsonl` | JSONL | `mensajes_log` |
| `Whatsapp_agent/storage/conversations/*` | JSON | `mensajes_log` con threading |
| **SAE10** (DB SQL Server local) | tablas `CLIE02`, `CFDI02`, etc. | Histórico de facturas y CXC (read-only para consulta) |

---

## Estrategia general

**3 fases con dual-running:**

1. **Pre-migración (Sprint 1-2):** seedear catálogos SAT + crear tenant Frutas Kelly + migrar catálogos (clientes, productos, precios). El agente sigue operando con JSONs.
2. **Dual-write (Sprint 3):** el agente escribe a JSON Y a la nueva DB. Validamos paridad durante 1-2 semanas.
3. **Cutover (final Sprint 3):** apagamos los writes a JSON. La DB es la única fuente de verdad.

**SAE10 nunca se escribe.** Solo lectura para consulta histórica de facturas anteriores. Las nuevas facturas nacen en Cadena de Suministro AI vía Facturama.

---

## Sprint 1: Pre-requisitos

### 1.1 Crear tenant inicial

```python
# scripts/seed_frutas_kelly.py
tenant = create_tenant(
    tier="SUB",
    parent_tenant_id=None,
    slug="frutas-kelly",
    legal_name="CRISTIAN ZARATE OCHOA",  # o razón social oficial
    rfc="ZAOC830517RF9",
    regimen_fiscal_sat="612",  # personas físicas con actividades empresariales
    domicilio_fiscal_cp="78390",
    domicilio_fiscal={
        "calle": "LEGUMBRES",
        "num_exterior": "302",
        "num_interior": "A",
        "colonia": "ABASTOS",
        "municipio": "SAN LUIS POTOSI",
        "estado": "SAN LUIS POTOSI",
        "pais": "MEXICO"
    }
)
```

### 1.2 Seedear catálogos SAT

Fuentes:
- `kelly_saas/docs/config/PARAMETROSDEFAULT.ini`
- `kelly_saas/docs/config/MetodosPago.ini`
- `kelly_saas/docs/config/complementosSAT4.ini`
- Catálogos públicos del SAT (descarga directa de http://omawww.sat.gob.mx/tramitesyservicios/Paginas/catalogos_emision_cfdi_complemento_ce.htm)

Script `scripts/seed_sat_catalogs.py` parsea y carga las tablas `sat_*`.

---

## Sprint 2: Migración de catálogos

### 2.1 Clientes (split en 2 entidades)

**Hoy en `clientes.json`:**
```json
{
  "id": "EHMO",
  "nombre": "GRUPO OPERADOR DE ALIMENTOS EHMO",
  "rfc": "GOA180712SF5",
  "direccion": "Calle: LEGUMBRES 302 ...",
  "cp": "78390",
  "tipo_cliente": "hospitales",
  "agente": "EHMO_PHONE",
  "lista_precios_id": "EHMO",
  "linea_tipo": "ehmo",
  "folio_file": "folio_counter.json",
  "notas": "Cliente principal. Manda diariamente Excel BD..."
}
```

**Mapping a Cadena de Suministro AI:**

```python
cliente = create_cliente(
    tenant_id=frutas_kelly.id,
    codigo="EHMO",
    tipo="PRINCIPAL_GOV",
    legal_name="GRUPO OPERADOR DE ALIMENTOS EHMO",
    rfc="GOA180712SF5",
    regimen_fiscal="601",  # General de Ley Personas Morales (verificar en CFDI real)
    domicilio_fiscal={...},
    lista_precios_id=lista_ehmo.id,
    custom_fields={
        "tipo_cliente": "hospitales",
        "agente_whatsapp_phone_env": "EHMO_PHONE",
        "linea_tipo": "ehmo",
        "notas": "Cliente principal. Manda diariamente Excel BD..."
    }
)

# Las 20 unidades de EHMO en `pedido_processor.HOSPITALES_CONOCIDOS_SI`
# se crean como unidades_entrega ligadas al contrato
```

### 2.2 Contratos y unidades

**Hoy son implícitos** (constantes en `pedido_processor.py`). Los hacemos explícitos:

```python
contrato_ehmo_chiapas = create_contrato(
    tenant_id=frutas_kelly.id,
    contratante="EHMO (que a su vez tiene contrato gobierno)",
    estado_mx="Chiapas",
    vigencia_desde="2025-01-01",
    vigencia_hasta="2026-12-31",
    notas="Lote 5 Frutas y Verduras hospitales DIF/IMSS Chiapas"
)

contratos_lotes_5 = create_contrato_lote(
    contrato_id=contrato_ehmo_chiapas.id,
    numero_lote=5,
    descripcion="Lote 5 — Frutas y Verduras",
    asignado_a_tenant=frutas_kelly.id,  # él mismo lo surte
    lista_precios_id=lista_ehmo.id
)

# Crear las 20 unidades de Chiapas (HOSPITALES_CONOCIDOS_SI)
for hospital_nombre in HOSPITALES_CONOCIDOS_SI:
    create_unidad_entrega(
        contrato_id=contrato_ehmo_chiapas.id,
        nombre=hospital_nombre,
        tipo="HOSPITAL",
        estado_mx="Chiapas",
        frecuencia_entrega="diaria",
    )
```

Lo mismo para los otros 9 estados de EHMO + 2 estados de Chaneques.

### 2.3 Lista de precios y productos

**Hoy:** `data/Lista_Precios_EHMO.xlsx` con ~110 filas (producto + presentación + precio).

**Migración:**

```python
# scripts/import_lista_precios.py
df = pd.read_excel("Lista_Precios_EHMO.xlsx")

lista = create_lista_precios(
    tenant_id=frutas_kelly.id,
    codigo="EHMO",
    nombre="Lista oficial EHMO Hospitales",
    vigencia_desde="2025-01-01"
)

for _, row in df.iterrows():
    # Match contra catálogo SAT (Claude tool: classify_product)
    clave_sat = ai_classify_product(row["nombre"])  # ej. "50202301" para frutas
    unidad_sat = "KGM" if row["presentacion"] == "KILO" else "H87"

    producto = upsert_producto(
        tenant_id=frutas_kelly.id,
        sku_interno=row["sku"] or generate_sku(row["nombre"]),
        nombre=row["nombre"],
        nombre_normalizado=normalize(row["nombre"]),
        clave_sat=clave_sat,
        unidad_sat=unidad_sat,
        iva_tasa=0,  # FyV exenta
        presentaciones={"KILO": 1},
        sinonimos=detect_sinonimos(row["nombre"]),  # del agente actual
    )

    create_precio(
        lista_id=lista.id,
        producto_id=producto.id,
        presentacion="KILO",
        precio_unitario=row["precio"],
        vigencia_desde="2025-01-01"
    )
```

**Sinónimos:** los aliases del agente actual (`pricing.py:_ALIAS_BUSQUEDA`, `_SINONIMOS`) se cargan en `productos.sinonimos[]`.

### 2.4 Validación

Al final del Sprint 2, debe cuadrar:

```python
assert count(clientes WHERE tenant_id=frutas_kelly.id) >= 12  # 10 EHMO + 2 Chaneques + ...
assert count(productos WHERE tenant_id=frutas_kelly.id) >= 110
assert count(unidades_entrega WHERE contrato_id IN frutas_kelly_contratos) >= 30
assert count(precios WHERE lista_id IN frutas_kelly_listas) >= 110
```

---

## Sprint 3: Migración de pedidos históricos + dual-write

### 3.1 Backfill de pedidos del día

**Hoy:** archivos `storage/pedidos_dia/2026-04-30.json`, `2026-05-01.json`, etc.

**Estructura del JSON:**
```json
{
  "fecha": "2026-04-30",
  "hospitales": {
    "Hospital X": {
      "folio_remision": "0000000094",
      "estado": "modificado",
      "productos": [
        {"alimento": "Cebolla blanca", "cantidad": 2.0, "precio_unitario": 15.5, ...}
      ]
    }
  }
}
```

**Script de migración:**

```python
# scripts/migrate_pedidos_historicos.py
for archivo in glob("storage/pedidos_dia/*.json"):
    fecha = parse_fecha_from_filename(archivo)
    data = json.load(open(archivo))

    for nombre_hospital, info in data["hospitales"].items():
        unidad = find_unidad_entrega(tenant_id=frutas_kelly.id, nombre=nombre_hospital)

        pedido = create_pedido(
            tenant_id=frutas_kelly.id,
            folio_interno=info["folio_remision"],
            contrato_lote_id=contrato_lote_5_chiapas.id,  # según el cliente
            cliente_facturacion_id=cliente_ehmo.id,
            unidad_entrega_id=unidad.id,
            fecha_pedido=fecha,
            estado=map_estado(info["estado"]),  # "modificado" → "FACTURADO"
            canal="EXCEL_BD",
            raw_payload=info,  # backup para debugging
        )

        for idx, prod in enumerate(info["productos"]):
            producto = match_producto(prod["alimento"])  # usa pricing.py logic
            create_linea_pedido(
                pedido_id=pedido.id,
                numero_linea=idx + 1,
                producto_id=producto.id if producto else None,
                presentacion=prod["presentacion"],
                cantidad_solicitada=prod["cantidad_original"],
                cantidad_surtida=prod["cantidad"],
                precio_unitario=prod["precio_unitario"],
                importe=prod["importe"],
                texto_original=prod["alimento"],
            )
```

### 3.2 Dual-write durante validación

**El agente escribe a ambos** durante 1-2 semanas:

```python
# app/processing_runner.py (después del refactor)
def procesar_pedido_dia(...):
    # Lectura: nueva DB primero, fallback a JSON
    pedido_existente = api.get_pedido_dia(fecha) or json_legacy.get_pedido(fecha)

    # Escritura: dual
    api.upsert_pedido(...)        # nueva DB
    json_legacy.upsert_pedido(...)  # legacy (temporal, 1-2 semanas)

    # Comparación: alerta si difieren
    if api.checksum != json_legacy.checksum:
        log.warning(f"Divergencia en pedido {fecha}: {diff}")
```

**Fin de Sprint 3:** revisamos logs de divergencia. Si están limpios 1 semana → cutover (apagar writes a JSON).

### 3.3 Folios

**Hoy:** `storage/folio_counter.json` = `{"next": 113}`.

**Migración:** el siguiente folio se inicializa en `tenants.config.folio_next = 113`. El sistema lo gestiona transaccionalmente con `SELECT ... FOR UPDATE` en cada generación de pedido/factura.

---

## Sprint 4: Cutover de SAE10

### 4.1 Migración de facturas históricas (read-only)

**Importante:** las facturas viejas SAE10 **no se reemiten**. Solo se importan como **registro histórico** para que el estado de cuenta de un cliente sea completo.

```python
# scripts/import_sae10_facturas.py (corre en la PC con SAE10)
import pyodbc
conn = pyodbc.connect("DRIVER=...; SERVER=localhost\\SQLEXPRESS; DATABASE=EMPRESA_SQL")

cur = conn.execute("""
    SELECT FOLIO, SERIE, FECHA_DOC, CVE_CLPV, TOTAL, UUID, ...
    FROM FACTF02
    WHERE STATUS = 'E'
""")

for row in cur:
    factura = create_factura_historica(
        tenant_id=frutas_kelly.id,
        serie=row.SERIE,
        folio=row.FOLIO,
        cliente_id=find_cliente_by_clave_sae(row.CVE_CLPV).id,
        fecha_timbrado=row.FECHA_TIM,
        uuid_sat=row.UUID,
        total=row.TOTAL,
        estado="TIMBRADA",  # solo registro
        pac="aspel_sellado_legacy",
        # XML/PDF se descargan de C:\DACASPEL\Comprobantes\SAE\Empresa NN\ y se suben a Storage
        xml_storage_path=upload_to_storage(read_xml(row.UUID)),
        pdf_storage_path=upload_to_storage(read_pdf(row.UUID)),
    )

# Patrón análogo para CXC (cargos+abonos) y pagos.
```

### 4.2 Validación cutover

Antes de apagar SAE10:

- [ ] 1 semana de facturas reales emitidas correctamente desde Cadena de Suministro AI/Facturama
- [ ] Contador externo valida 5-10 XMLs aleatorios (estructura, addendas, totales)
- [ ] Saldo de cliente principal (EHMO) en Cadena de Suministro AI = saldo en SAE10 ± $0.01
- [ ] Backup completo de DB SAE10 guardado antes del corte
- [ ] Acceso read-only a SAE10 disponible por 6+ meses para consultas SAT

### 4.3 Comunicación

- Avisar a contador externo: nuevas facturas vienen de Cadena de Suministro AI, mismo formato CFDI 4.0
- Avisar a EHMO/Chaneques: cambia el PAC (de Aspel Sellado a Facturama). XML válido SAT, sin diferencias visibles
- Si hay otro personal admin: capacitación 1-2 horas en la torre de control

---

## Tabla de mapeo: campos legacy → Cadena de Suministro AI

### `clientes.json` → `clientes` + `unidades_entrega`

| Campo legacy | Campo Cadena de Suministro AI | Notas |
|---|---|---|
| `id` | `clientes.codigo` | "EHMO" se mantiene |
| `cliente_id_interno` | (ignorar) | Se reemplaza por UUID |
| `nombre` | `legal_name` | |
| `rfc` | `rfc` | |
| `direccion` | `domicilio_fiscal` (parsear) | Split en JSONB |
| `cp` | `domicilio_fiscal.cp` | |
| `agente` | `custom_fields.agente_whatsapp` | Hasta que se modele agentes |
| `tipo_cliente` | `custom_fields.tipo_cliente` | |
| `linea_tipo` | `custom_fields.linea_tipo` | |
| `folio_file` | (ignorar) | Folios en `tenants.config` |
| `lista_precios_id` | `lista_precios_id` UUID | Vía lookup |
| `notas` | `custom_fields.notas` | |

### Producto Excel → `productos`

| Columna Excel | Campo Cadena de Suministro AI | Notas |
|---|---|---|
| `nombre` | `nombre` | |
| `presentacion` | `presentaciones` JSONB key | |
| `precio` | → `precios.precio_unitario` | |
| (no existe) | `clave_sat` | AI classify (Claude) |
| (no existe) | `unidad_sat` | KGM/H87 según presentación |
| (sinónimos del agente) | `sinonimos[]` | Hardcoded en pricing.py hoy |

### Pedido JSON → `pedidos` + `lineas_pedido`

| Campo legacy | Campo Cadena de Suministro AI |
|---|---|
| `fecha` | `pedidos.fecha_pedido` |
| `hospitales.<X>.folio_remision` | `pedidos.folio_interno` |
| `hospitales.<X>.estado` | `pedidos.estado` (mapear) |
| `hospitales.<X>` (nombre) | `pedidos.unidad_entrega_id` (lookup) |
| `productos[].alimento` | `lineas_pedido.texto_original` |
| `productos[].cantidad` | `lineas_pedido.cantidad_surtida` |
| `productos[].cantidad_original` | `lineas_pedido.cantidad_solicitada` |
| `productos[].precio_unitario` | `lineas_pedido.precio_unitario` |
| `productos[].importe` | `lineas_pedido.importe` |

---

## Rollback plan

Si algo va mal en cualquier sprint:

1. **Sprint 1-2 (catálogos):** sin riesgo operativo. Borrar tenant y rehacer.
2. **Sprint 3 (pedidos + dual-write):** mantener legacy JSON activo. El agente lee de JSON si la API falla. Rollback = apagar dual-write.
3. **Sprint 4 (cutover SAE10):** mantener SAE10 como standby. Si Cadena de Suministro AI falla en producción, emitir facturas en SAE10 mientras se arregla. Tener pre-cargados los datos del día en ambos sistemas durante 1 semana.
4. **Sprint 5+ (frontend, email parser, etc.):** features adicionales, no bloquean operación.

---

## Resumen ejecutivo del plan

```
S1 ─────► Backend deployado, tablas creadas, RLS funcionando, 1 user puede crear tenant
S2 ─────► Frutas Kelly tiene en DB sus 12 contratos, 30-40 unidades, 110 productos, 2 listas
S3 ─────► WhatsApp agent escribe pedidos en DB; PDFs idénticos al legacy
S4 ─────► Frutas Kelly emite facturas reales por Facturama; SAE10 apagado
S5 ─────► Operador trabaja desde dashboard web sin tocar JSON ni Excel
S6 ─────► Lotes con caducidad activos; FEFO al surtir
S7 ─────► EHMO manda Excel BD por correo; sistema lo procesa solo
S8 ─────► Primer sub externo onboardeado; suscripción mensual cobrando
```
