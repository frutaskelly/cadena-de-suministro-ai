"""Generador de Nota de Remision PDF (port v1).

Mantiene el formato fiscal del v1 (header proveedor, datos cliente, tabla
de 6 columnas con precios, total en letras) pero recibe una `Remision`
del nuevo schema en lugar de DataFrame.
"""
from __future__ import annotations

import logging
from datetime import date as date_cls, datetime
from decimal import Decimal
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)
from sqlalchemy.orm import Session

from ..models import Cliente, LineaRemision, Producto, Remision, UnidadEntrega

log = logging.getLogger(__name__)

NEGRO = colors.HexColor("#000000")
GRIS_CLARO = colors.HexColor("#F4F4F4")

# Datos del proveedor — en v1 estaban hardcoded; aqui hacemos lo mismo
# como default. Despues se podran tomar del Tenant con sus propios CSDs.
DEFAULT_PROVEEDOR = {
    "nombre": "CRISTIAN GERARDO ZARATE OROZCO",
    "rfc": "ZAOC830517RF9",
    "domicilio": (
        "Calle: SIMBOLOS PATRIOS No. 107, "
        "Col. Paraje el Cerritos, CP: 71260, "
        "San Agustín de las Juntas, Oaxaca"
    ),
    "lugar_expedicion": (
        "Calle: LEGUMBRES 302 No. A, "
        "Col. ABASTOS, CP: 78390, "
        "SAN LUIS POTOSI, SAN LUIS POTOSI, MEXICO"
    ),
}

DIAS_SEMANA = [
    "LUNES", "MARTES", "MIERCOLES", "JUEVES",
    "VIERNES", "SABADO", "DOMINGO",
]
MESES_NOMBRE = [
    "", "ENERO", "FEBRERO", "MARZO", "ABRIL",
    "MAYO", "JUNIO", "JULIO", "AGOSTO",
    "SEPTIEMBRE", "OCTUBRE", "NOVIEMBRE", "DICIEMBRE",
]


def _fmt_qty(v) -> str:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return str(v)
    return f"{f:.4f}"


def _fmt_money(v) -> str:
    try:
        return f"${float(v):,.2f}"
    except (TypeError, ValueError):
        return str(v)


def _total_en_letras(monto: float) -> str:
    """Convierte 1234.56 a '(MIL DOSCIENTOS TREINTA Y CUATRO PESOS 56/100 M.N.)'."""
    try:
        from num2words import num2words
        entero = int(monto)
        cents = round((monto - entero) * 100)
        letras = num2words(entero, lang="es").upper()
        return f"({letras} PESOS {cents:02d}/100 M.N.)"
    except ImportError:
        return f"(${monto:,.2f} M.N.)"


def _semana_iso(fecha: date_cls) -> int:
    return fecha.isocalendar().week


def generar_nota_remision_pdf(
    db: Session,
    remision: Remision,
    output_path: Path,
    *,
    proveedor: dict = None,
    tipo: str = "regular",
) -> Path:
    """Genera el PDF de Nota de Remision para una Remision."""
    proveedor = proveedor or DEFAULT_PROVEEDOR
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Cargar relaciones
    cliente = db.get(Cliente, remision.cliente_id)
    unidad = (
        db.get(UnidadEntrega, remision.unidad_entrega_id)
        if remision.unidad_entrega_id else None
    )
    if not cliente:
        raise ValueError(f"Cliente {remision.cliente_id} no existe")

    # Lineas con productos
    lineas_data = (
        db.query(LineaRemision, Producto)
        .join(Producto, Producto.id == LineaRemision.producto_id)
        .filter(LineaRemision.remision_id == remision.id)
        .order_by(Producto.nombre)
        .all()
    )

    fecha_entrega = (
        remision.fecha_entrega.date() if remision.fecha_entrega
        else remision.fecha_generada
    )
    fecha_doc_str = datetime.now().strftime("%d/%m/%Y")
    folio = remision.folio
    semana = _semana_iso(fecha_entrega)
    dia_sem = DIAS_SEMANA[fecha_entrega.weekday()]
    mes_nombre = MESES_NOMBRE[fecha_entrega.month]

    # Linea descriptiva
    lugar = (
        unidad.nombre if unidad
        else cliente.legal_name or cliente.codigo
    )
    if tipo == "extras":
        linea_desc = (
            f"SEMANA {semana}: EXTRA SOLICITADO PARA CUBRIR NECESIDADES ESPECIALES "
            f"DE {dia_sem} {fecha_entrega.day} DE {mes_nombre} EN {lugar}."
        )
    else:
        # Default: DIF ENTREGA (EHMO) o COMEDORES HUMANITARIOS (SUREÑA)
        prefijo = "DIF ENTREGA"
        if "comedor" in lugar.lower() or "surena" in (cliente.codigo or "").lower():
            prefijo = "COMEDORES HUMANITARIOS ENTREGA"
        linea_desc = (
            f"SEMANA {semana}: {prefijo} {dia_sem} "
            f"{fecha_entrega.day} DE {mes_nombre} EN {lugar}."
        )

    doc = SimpleDocTemplate(
        str(output_path), pagesize=letter,
        topMargin=1 * cm, bottomMargin=1 * cm,
        leftMargin=1.2 * cm, rightMargin=1.2 * cm,
        title=f"Nota Remision {folio}",
    )

    styles = getSampleStyleSheet()
    style_small = ParagraphStyle("sm", parent=styles["Normal"], fontSize=7, leading=8)
    style_pron = ParagraphStyle(
        "pn", parent=styles["Normal"], fontSize=9, leading=11,
        fontName="Helvetica-Bold", alignment=TA_RIGHT,
    )
    style_label_b = ParagraphStyle(
        "lb", parent=styles["Normal"], fontSize=8, leading=10,
        fontName="Helvetica-Bold",
    )
    style_descrip = ParagraphStyle(
        "desc", parent=styles["Normal"], fontSize=9, leading=11,
        fontName="Helvetica-Bold",
    )
    style_total_letras = ParagraphStyle(
        "tl", parent=styles["Normal"], fontSize=8, leading=10,
        fontName="Helvetica-Bold",
    )

    elements = []

    # Header
    header_data = [[
        Paragraph(
            f"<b>Lugar de expedición</b><br/>{proveedor['lugar_expedicion']}<br/><br/>"
            f"<b>Domicilio fiscal</b><br/>{proveedor['domicilio']}<br/>"
            f"<b>RFC:</b> {proveedor['rfc']}",
            style_small,
        ),
        Paragraph(
            f"<b>NOTA DE REMISIÓN</b><br/><br/>"
            f"<b>{proveedor['nombre']}</b><br/><br/>"
            f"<b>PEDIDO No.:</b> {folio}<br/>"
            f"{fecha_doc_str}<br/>"
            f"<b>R.F.C.:</b> {proveedor['rfc']}",
            style_pron,
        ),
    ]]
    htbl = Table(header_data, colWidths=[11 * cm, 7 * cm])
    htbl.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("BOX", (0, 0), (-1, -1), 0.5, NEGRO),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(htbl)

    # Cliente
    cp = ""
    if cliente.domicilio_fiscal:
        cp = cliente.domicilio_fiscal.get("cp", "") if isinstance(cliente.domicilio_fiscal, dict) else ""
    elements.append(Spacer(1, 0.2 * cm))
    cli_tbl = Table(
        [[Paragraph(
            f"<b>Cliente:</b> ( {cliente.codigo} ) {cliente.legal_name} "
            f"&nbsp;&nbsp;&nbsp; <b>RFC:</b> {cliente.rfc or ''} "
            f"&nbsp;&nbsp;&nbsp; <b>CP:</b> {cp}",
            style_label_b,
        )]],
        colWidths=[18 * cm],
    )
    cli_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), GRIS_CLARO),
        ("BOX", (0, 0), (-1, -1), 0.5, NEGRO),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    elements.append(cli_tbl)

    # Linea descriptiva
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(linea_desc, style_descrip))

    # Tabla de productos
    elements.append(Spacer(1, 0.3 * cm))
    table_rows = [
        ["Cantidad", "Unidad", "Descripción", "% Desc.", "P/U", "Importe"]
    ]
    subtotal = Decimal(0)
    for lr, prod in lineas_data:
        qty = lr.cantidad_facturada or lr.cantidad_entregada or Decimal(0)
        if qty <= 0:
            continue
        pu = lr.precio_unitario or Decimal(0)
        importe = qty * pu
        subtotal += importe
        table_rows.append([
            _fmt_qty(qty),
            (lr.presentacion or prod.presentacion_default or "KG").upper(),
            prod.nombre,
            "0.00%",
            _fmt_money(pu),
            _fmt_money(importe),
        ])

    iva = Decimal(0)
    total = subtotal + iva
    table_rows.append(["", "", "", "", "Subtotal:", _fmt_money(subtotal)])
    table_rows.append(["", "", "", "", "I.V.A.:", _fmt_money(iva)])
    table_rows.append(["", "", "", "", "Total:", _fmt_money(total)])

    items_tbl = Table(
        table_rows,
        colWidths=[2 * cm, 2 * cm, 7 * cm, 1.5 * cm, 2.5 * cm, 3 * cm],
        repeatRows=1,
    )
    items_tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), GRIS_CLARO),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ALIGN", (0, 0), (0, -1), "RIGHT"),
        ("ALIGN", (3, 0), (5, -1), "RIGHT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("GRID", (0, 0), (-1, len(table_rows) - 4), 0.3, NEGRO),
        ("BOX", (0, len(table_rows) - 3), (-1, -1), 0.5, NEGRO),
        ("FONTNAME", (4, -1), (-1, -1), "Helvetica-Bold"),
        ("BACKGROUND", (4, -1), (-1, -1), GRIS_CLARO),
    ]))
    elements.append(items_tbl)

    # Total en letras
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(
        Paragraph(_total_en_letras(float(total)), style_total_letras)
    )

    doc.build(elements)
    log.info(f"Nota remision PDF: {output_path.name} (folio {folio}, total ${total:.2f})")
    return output_path
