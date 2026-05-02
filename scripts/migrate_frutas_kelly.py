"""Migra los datos de Frutas Kelly (whatsapp_agent) a la nueva base.

Ejecutar desde el dir backend/ con el venv activado:
    cd backend && source venv/bin/activate
    python ../scripts/migrate_frutas_kelly.py

Idempotente: se puede correr múltiples veces. Salta lo que ya existe.
"""
import json
import sys
import unicodedata
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pandas as pd
from sqlalchemy import select

# Allow running from anywhere
HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.db import SessionLocal
from app.models import (
    Tenant, User, Membership,
    Cliente, Producto, ListaPrecios, Precio,
    Contrato, ContratoLote, UnidadEntrega,
    Pedido, LineaPedido,
)

# Source paths
AGENT = HERE.parent.parent / "Whatsapp_agent"
CLIENTES_JSON = AGENT / "storage" / "clientes.json"
AGENTES_JSON = AGENT / "storage" / "agentes.json"
DATA_DIR = AGENT / "data"
PEDIDOS_DIR = AGENT / "storage" / "pedidos_dia"


def _normalize(s: str) -> str:
    s = (s or "").lower().strip()
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def _parse_direccion(direccion_str: str, cp: str) -> dict:
    """Parsea string del legacy a JSONB structured."""
    return {
        "raw": direccion_str,
        "cp": cp,
        "calle": "LEGUMBRES",
        "num_exterior": "302",
        "num_interior": "A",
        "colonia": "ABASTOS",
        "municipio": "SAN LUIS POTOSI",
        "estado": "SAN LUIS POTOSI",
        "pais": "MEXICO",
    }


def step_1_tenant_user(db) -> Tenant:
    """Crea Tenant 'Frutas Kelly' + user owner + membership."""
    tenant = db.query(Tenant).filter(Tenant.slug == "frutas-kelly").first()
    if tenant:
        print(f"  Tenant ya existe: {tenant.id}")
        return tenant

    tenant = Tenant(
        tier="SUB",
        slug="frutas-kelly",
        legal_name="CRISTIAN ZARATE OCHOA",
        trade_name="Frutas Kelly",
        rfc="ZAOC830517RF9",
        regimen_fiscal_sat="612",  # Personas físicas con actividades empresariales
        domicilio_fiscal_cp="78390",
        domicilio_fiscal=_parse_direccion("Calle: LEGUMBRES 302 No. A", "78390"),
        config={"folio_next": 113, "folio_next_comedores": 16},
        status="ACTIVE",
    )
    db.add(tenant)
    db.flush()

    user = User(
        email="cristian@frutaskelly.com",
        full_name="Cristian Zarate Ochoa",
    )
    db.add(user)
    db.flush()

    db.add(Membership(
        tenant_id=tenant.id,
        user_id=user.id,
        role="OWNER",
        active=True,
    ))
    db.commit()
    print(f"  Tenant creado: {tenant.id} (Frutas Kelly)")
    return tenant


def step_2_listas_precios(db, tenant: Tenant) -> dict:
    """Crea listas EHMO y SURENA. Devuelve dict {codigo: ListaPrecios}."""
    listas = {}
    for codigo, nombre in [
        ("EHMO", "Lista EHMO Hospitales Chiapas"),
        ("SURENA", "Lista SUREÑA Comedores"),
    ]:
        l = db.query(ListaPrecios).filter(
            ListaPrecios.tenant_id == tenant.id,
            ListaPrecios.codigo == codigo,
        ).first()
        if not l:
            l = ListaPrecios(
                tenant_id=tenant.id,
                codigo=codigo,
                nombre=nombre,
                vigencia_desde=date(2025, 1, 1),
                moneda="MXN",
            )
            db.add(l)
            db.flush()
            print(f"  Lista creada: {codigo}")
        listas[codigo] = l
    db.commit()
    return listas


def step_3_clientes(db, tenant: Tenant, listas: dict) -> dict:
    """Migra clientes.json + agentes.json → tabla clientes."""
    src = json.load(open(CLIENTES_JSON))
    out = {}
    for c in src["clientes"]:
        existing = db.query(Cliente).filter(
            Cliente.tenant_id == tenant.id,
            Cliente.codigo == c["id"],
        ).first()
        if existing:
            print(f"  Cliente {c['id']} ya existe")
            out[c["id"]] = existing
            continue

        # Map tipo_cliente legacy → tipo nuevo
        tipo = "PRINCIPAL_GOV" if c.get("tipo_cliente") in ("hospitales", "comedores") else "PRIVADO"
        lista = listas.get(c.get("lista_precios_id", c["id"]))

        cli = Cliente(
            tenant_id=tenant.id,
            codigo=c["id"],
            tipo=tipo,
            legal_name=c["nombre"],
            rfc=c["rfc"],
            regimen_fiscal="601",  # General Personas Morales (verificar al timbrar)
            uso_cfdi_default="G03",
            metodo_pago_default="PPD",
            forma_pago_default="99",
            domicilio_fiscal=_parse_direccion(c.get("direccion", ""), c.get("cp", "")),
            lista_precios_id=lista.id if lista else None,
            condiciones_pago="30 días",
            custom_fields={
                "tipo_cliente": c.get("tipo_cliente"),
                "agente_whatsapp": c.get("agente"),
                "linea_tipo": c.get("linea_tipo"),
                "notas_legacy": c.get("notas"),
                "cliente_id_interno": c.get("cliente_id_interno"),
            },
        )
        db.add(cli)
        db.flush()
        out[c["id"]] = cli
        print(f"  Cliente creado: {c['id']} - {c['nombre']}")

    db.commit()
    return out


def step_4_contratos_unidades(db, tenant: Tenant, clientes: dict, listas: dict):
    """Crea contratos + lotes + unidades de entrega.

    Las listas están hardcoded aquí para evitar colisión de namespace 'app.'
    entre este backend y el agente legacy. Sincronizadas con
    Whatsapp_agent/app/pedido_processor.py al 2026-05-03.
    """
    HOSPITALES_CONOCIDOS_SI = [
        "Hospital Básico Comunitario 12 Camas Berriozabal",
        "Hospital Básico Comunitario Chiapa de Corzo",
        "Hospital Básico Comunitario de Cintalapa de Figueroa",
        "Hospital Básico Comunitario Las Margaritas",
        "Hospital Básico Comunitario Manuel Velasco Suarez Acala",
        "Hospital Básico Comunitario Ángel Albino Corzo",
        "Hospital Básico Comunitario Dr. Rafael Alfaro Gonzalez Pijijiapan",
        "Hospital Básico de Frontera Comalapa",
        "Hospital Chiapas nos une Dr. Jesús Gilberto Gomez Maza",
        "Hospital de la Mujer Comitán",
        "Hospital de la Mujer San Cristóbal de las Casas",
        "Hospital de las Culturas San Cristóbal de las Casas",
        "Hospital General Bicentenario Villaflores",
        "Hospital General de Huixtla",
        "Hospital General de Ocosingo",
        "Hospital General Dr. Juan C. Corzo Tonalá",
        "Hospital General Juárez Arriaga",
        "Hospital General María Ignacia Gandulfo Comitán",
        "Hospital General Tapachula",
        "Hospital Regional Dr. Rafael Pascasio Gamboa Tuxtla",
        "Unidad de Atención a la Salud Mental San Agustín",
    ]
    COMEDORES_SI = [
        "Comedor Patria",
        "Comedor CCI",
        "Comedor 6 de Junio",
        "Comedor Shanka",
        "Comedor Jobo",
        "Comedor Copoya",
    ]

    # Contrato EHMO Chiapas
    ehmo = clientes.get("EHMO")
    surena = clientes.get("SURENA")

    contrato_ehmo = db.query(Contrato).filter(
        Contrato.tenant_id == tenant.id,
        Contrato.contratante == "EHMO",
        Contrato.estado_mx == "Chiapas",
    ).first()
    if not contrato_ehmo:
        contrato_ehmo = Contrato(
            tenant_id=tenant.id,
            numero_contrato="EHMO-CHIAPAS-2025",
            contratante="EHMO",
            contratante_rfc="GOA180712SF5",
            estado_mx="Chiapas",
            vigencia_desde=date(2025, 1, 1),
            vigencia_hasta=date(2026, 12, 31),
            condiciones_pago="30 días",
            notas="Lote 5 Frutas y Verduras hospitales DIF/IMSS Chiapas. EHMO manda BD diaria.",
            config={"linea": "ehmo", "tipo_unidades": "hospitales"},
        )
        db.add(contrato_ehmo)
        db.flush()
        # Lote 5
        cl5 = ContratoLote(
            contrato_id=contrato_ehmo.id,
            numero_lote=5,
            descripcion="Lote 5 — Frutas y Verduras",
            asignado_a_tenant=tenant.id,
            lista_precios_id=listas["EHMO"].id,
        )
        db.add(cl5)
        db.flush()
        # 21 hospitales
        for nombre in HOSPITALES_CONOCIDOS_SI:
            db.add(UnidadEntrega(
                contrato_id=contrato_ehmo.id,
                nombre=nombre,
                tipo="HOSPITAL",
                estado_mx="Chiapas",
                frecuencia_entrega="diaria",
                activa=True,
            ))
        db.flush()
        print(f"  Contrato EHMO Chiapas + Lote 5 + {len(HOSPITALES_CONOCIDOS_SI)} hospitales")

    # Contrato SURENA Chiapas (comedores)
    contrato_surena = db.query(Contrato).filter(
        Contrato.tenant_id == tenant.id,
        Contrato.contratante == "SUREÑA",
    ).first()
    if not contrato_surena:
        contrato_surena = Contrato(
            tenant_id=tenant.id,
            contratante="SUREÑA",
            estado_mx="Chiapas",
            vigencia_desde=date(2025, 1, 1),
            vigencia_hasta=date(2026, 12, 31),
            notas="Lote 5 Frutas y Verduras comedores humanitarios. Pedido en libreta/foto/voz.",
            config={"linea": "surena", "tipo_unidades": "comedores"},
        )
        db.add(contrato_surena)
        db.flush()
        cls = ContratoLote(
            contrato_id=contrato_surena.id,
            numero_lote=5,
            descripcion="Lote 5 — Frutas y Verduras",
            asignado_a_tenant=tenant.id,
            lista_precios_id=listas["SURENA"].id,
        )
        db.add(cls)
        db.flush()
        for nombre in COMEDORES_SI:
            db.add(UnidadEntrega(
                contrato_id=contrato_surena.id,
                nombre=nombre,
                tipo="COMEDOR",
                estado_mx="Chiapas",
                frecuencia_entrega="diaria",
                activa=True,
            ))
        db.flush()
        print(f"  Contrato SUREÑA + {len(COMEDORES_SI)} comedores")

    db.commit()


def step_5_productos_precios(db, tenant: Tenant, listas: dict):
    """Lee Excels y crea productos + precios."""
    # Solo EHMO y SURENA por ahora
    excel_files = {
        "EHMO": DATA_DIR / "Lista_Precios_EHMO.xlsx",
        "SURENA": DATA_DIR / "Lista_Precios_SURENA.xlsx",
    }
    productos_creados = 0
    precios_creados = 0

    # Mantenemos un mapa global de productos por nombre normalizado
    productos_por_nombre = {}
    existing = db.query(Producto).filter(Producto.tenant_id == tenant.id).all()
    for p in existing:
        productos_por_nombre[p.nombre_normalizado] = p

    for codigo_lista, xlsx_path in excel_files.items():
        if not xlsx_path.exists():
            print(f"  Excel no encontrado: {xlsx_path}")
            continue
        df = pd.read_excel(xlsx_path)
        for idx, row in df.iterrows():
            nombre = str(row["Producto"]).strip()
            unidad = str(row.get("Unidad", "KG")).strip()
            precio = Decimal(str(row["Precio Unitario"]))
            nombre_norm = _normalize(nombre)

            # Upsert producto
            p = productos_por_nombre.get(nombre_norm)
            if not p:
                sku = f"FK-{idx+1:04d}-{codigo_lista}"
                presentacion = "KILO" if unidad.upper() in ("KG", "KILO") else "PIEZA"
                p = Producto(
                    tenant_id=tenant.id,
                    sku_interno=sku,
                    nombre=nombre,
                    nombre_normalizado=nombre_norm,
                    categoria="FRUTAS Y VERDURAS",
                    lote_default=5,
                    clave_sat="50202301",  # genérico FyV; AI classify mejora después
                    unidad_sat="KGM" if presentacion == "KILO" else "H87",
                    iva_tasa=Decimal("0"),  # FyV exenta IVA
                    presentaciones={presentacion: 1},
                    presentacion_default=presentacion,
                    activo=True,
                )
                db.add(p)
                db.flush()
                productos_por_nombre[nombre_norm] = p
                productos_creados += 1

            # Upsert precio
            existing_precio = db.query(Precio).filter(
                Precio.lista_id == listas[codigo_lista].id,
                Precio.producto_id == p.id,
                Precio.presentacion == p.presentacion_default,
            ).first()
            if not existing_precio:
                db.add(Precio(
                    lista_id=listas[codigo_lista].id,
                    producto_id=p.id,
                    presentacion=p.presentacion_default,
                    precio_unitario=precio,
                    vigencia_desde=date(2025, 1, 1),
                ))
                precios_creados += 1

        db.commit()
        print(f"  {codigo_lista}: procesado {xlsx_path.name}")

    print(f"  Productos creados: {productos_creados}")
    print(f"  Precios creados: {precios_creados}")


def step_6_pedidos_historicos(db, tenant: Tenant, clientes: dict):
    """Migra pedidos_dia/*.json a tabla pedidos."""
    if not PEDIDOS_DIR.exists():
        print(f"  No hay pedidos_dia: {PEDIDOS_DIR}")
        return

    # Pre-load: unidades por nombre across both contratos
    contrato_ehmo = db.query(Contrato).filter(
        Contrato.tenant_id == tenant.id,
        Contrato.contratante == "EHMO",
    ).first()
    contrato_surena = db.query(Contrato).filter(
        Contrato.tenant_id == tenant.id,
        Contrato.contratante == "SUREÑA",
    ).first()
    contrato_lote_ehmo = db.query(ContratoLote).filter(
        ContratoLote.contrato_id == contrato_ehmo.id,
        ContratoLote.numero_lote == 5,
    ).first()
    contrato_lote_surena = db.query(ContratoLote).filter(
        ContratoLote.contrato_id == contrato_surena.id,
        ContratoLote.numero_lote == 5,
    ).first()

    # Map: nombre_unidad → (UnidadEntrega, ContratoLote, Cliente)
    unidades = {}
    for u in db.query(UnidadEntrega).filter(
        UnidadEntrega.contrato_id == contrato_ehmo.id,
    ).all():
        unidades[u.nombre] = (u, contrato_lote_ehmo, clientes["EHMO"])
    for u in db.query(UnidadEntrega).filter(
        UnidadEntrega.contrato_id == contrato_surena.id,
    ).all():
        unidades[u.nombre] = (u, contrato_lote_surena, clientes["SURENA"])

    productos = {p.nombre_normalizado: p for p in db.query(Producto).filter(
        Producto.tenant_id == tenant.id,
    ).all()}

    pedidos_creados = 0
    lineas_creadas = 0
    sin_match = []

    for archivo in sorted(PEDIDOS_DIR.glob("*.json")):
        if archivo.name.startswith("."):
            continue
        try:
            data = json.load(open(archivo))
        except json.JSONDecodeError:
            print(f"  ! No pudo parsear {archivo.name}")
            continue

        fecha_str = data.get("fecha")
        if not fecha_str:
            continue
        fecha = datetime.fromisoformat(fecha_str).date()

        for nombre_hospital, info in data.get("hospitales", {}).items():
            if nombre_hospital not in unidades:
                sin_match.append((fecha_str, nombre_hospital))
                continue

            unidad_obj, lote_obj, cliente_obj = unidades[nombre_hospital]

            existing = db.query(Pedido).filter(
                Pedido.tenant_id == tenant.id,
                Pedido.fecha_pedido == fecha,
                Pedido.unidad_entrega_id == unidad_obj.id,
            ).first()
            if existing:
                continue

            estado_legacy = info.get("estado", "modificado")
            estado_map = {
                "creado": "CONFIRMADO",
                "modificado": "FACTURADO",
                "ajustado": "FACTURADO",
            }
            estado = estado_map.get(estado_legacy, "CONFIRMADO")
            canal = "LIBRETA_FOTO" if cliente_obj.codigo == "SURENA" else "EXCEL_BD"

            ped = Pedido(
                tenant_id=tenant.id,
                folio_interno=info.get("folio_remision"),
                contrato_lote_id=lote_obj.id,
                cliente_facturacion_id=cliente_obj.id,
                unidad_entrega_id=unidad_obj.id,
                fecha_pedido=fecha,
                estado=estado,
                canal=canal,
                raw_payload=info,
            )
            db.add(ped)
            db.flush()
            pedidos_creados += 1

            subtotal = Decimal("0")
            for idx, prod in enumerate(info.get("productos", [])):
                alimento_norm = _normalize(prod.get("alimento", ""))
                producto = None
                # match por substring
                for nombre_norm, pp in productos.items():
                    if nombre_norm in alimento_norm or alimento_norm in nombre_norm:
                        producto = pp
                        break

                cantidad = Decimal(str(prod.get("cantidad", 0)))
                cantidad_orig = Decimal(str(prod.get("cantidad_original", cantidad)))
                precio = Decimal(str(prod.get("precio_unitario", 0)))
                importe = Decimal(str(prod.get("importe", cantidad * precio)))

                db.add(LineaPedido(
                    pedido_id=ped.id,
                    numero_linea=idx + 1,
                    producto_id=producto.id if producto else None,
                    presentacion=prod.get("presentacion", "KILO"),
                    cantidad_solicitada=cantidad_orig,
                    cantidad_surtida=cantidad,
                    precio_unitario=precio,
                    importe=importe,
                    texto_original=prod.get("alimento"),
                ))
                lineas_creadas += 1
                subtotal += importe

            ped.subtotal = subtotal
            ped.total = subtotal

        db.commit()
        print(f"  {archivo.name}: pedidos hasta ahora = {pedidos_creados}")

    print(f"  TOTAL pedidos creados: {pedidos_creados}")
    print(f"  TOTAL líneas: {lineas_creadas}")
    if sin_match:
        print(f"  WARNING: {len(sin_match)} pedidos sin unidad matcheada (revisar)")
        for f, n in sin_match[:5]:
            print(f"    {f}: {n}")


def main():
    print("=" * 70)
    print("Migración Frutas Kelly → Cadena de Suministro AI")
    print("=" * 70)

    db = SessionLocal()
    try:
        print("\n[1/6] Tenant + User + Membership")
        tenant = step_1_tenant_user(db)

        print("\n[2/6] Listas de precios")
        listas = step_2_listas_precios(db, tenant)

        print("\n[3/6] Clientes")
        clientes = step_3_clientes(db, tenant, listas)

        print("\n[4/6] Contratos + Unidades de entrega")
        step_4_contratos_unidades(db, tenant, clientes, listas)

        print("\n[5/6] Productos + Precios")
        step_5_productos_precios(db, tenant, listas)

        print("\n[6/6] Pedidos históricos")
        step_6_pedidos_historicos(db, tenant, clientes)

        # Reporte final
        print("\n" + "=" * 70)
        print("RESUMEN")
        print("=" * 70)
        for model, label in [
            (Tenant, "tenants"),
            (User, "users"),
            (Cliente, "clientes"),
            (Contrato, "contratos"),
            (ContratoLote, "contratos_lotes"),
            (UnidadEntrega, "unidades_entrega"),
            (ListaPrecios, "listas_precios"),
            (Producto, "productos"),
            (Precio, "precios"),
            (Pedido, "pedidos"),
            (LineaPedido, "lineas_pedido"),
        ]:
            count = db.query(model).count()
            print(f"  {label:25s} {count}")

    finally:
        db.close()


if __name__ == "__main__":
    main()
