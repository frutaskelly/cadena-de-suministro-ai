"""
Genera el PDF de propuesta para el inversionista Cristian Zarate.
Salida: docs/Propuesta_Inversionista_Cristian_Zarate.pdf
"""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, cm
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    KeepTogether, ListFlowable, ListItem, HRFlowable, Image
)
from reportlab.pdfgen import canvas

OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "Propuesta_Inversionista_Cristian_Zarate.pdf"

# ---------- Estilos ----------
styles = getSampleStyleSheet()

NAVY = colors.HexColor("#0B2545")
TEAL = colors.HexColor("#13A89E")
GRAY = colors.HexColor("#5C6B73")
LIGHT = colors.HexColor("#F0F4F8")
ACCENT = colors.HexColor("#E07A5F")

styles.add(ParagraphStyle(
    name="CoverTitle",
    fontName="Helvetica-Bold",
    fontSize=32,
    leading=38,
    alignment=TA_CENTER,
    textColor=NAVY,
    spaceAfter=12,
))
styles.add(ParagraphStyle(
    name="CoverSubtitle",
    fontName="Helvetica",
    fontSize=14,
    leading=18,
    alignment=TA_CENTER,
    textColor=GRAY,
    spaceAfter=24,
))
styles.add(ParagraphStyle(
    name="CoverMeta",
    fontName="Helvetica",
    fontSize=11,
    leading=15,
    alignment=TA_CENTER,
    textColor=GRAY,
))
styles.add(ParagraphStyle(
    name="H1",
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=24,
    spaceBefore=16,
    spaceAfter=12,
    textColor=NAVY,
))
styles.add(ParagraphStyle(
    name="H2",
    fontName="Helvetica-Bold",
    fontSize=14,
    leading=18,
    spaceBefore=12,
    spaceAfter=8,
    textColor=NAVY,
))
styles.add(ParagraphStyle(
    name="H3",
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    spaceBefore=8,
    spaceAfter=4,
    textColor=TEAL,
))
styles.add(ParagraphStyle(
    name="Body",
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    alignment=TA_JUSTIFY,
    spaceAfter=6,
    textColor=colors.black,
))
styles.add(ParagraphStyle(
    name="BodySmall",
    fontName="Helvetica",
    fontSize=9,
    leading=12,
    spaceAfter=4,
))
styles.add(ParagraphStyle(
    name="MyBullet",
    fontName="Helvetica",
    fontSize=10,
    leading=14,
    leftIndent=14,
    spaceAfter=2,
))
styles.add(ParagraphStyle(
    name="Quote",
    fontName="Helvetica-Oblique",
    fontSize=10,
    leading=14,
    leftIndent=20,
    rightIndent=20,
    textColor=TEAL,
    spaceBefore=8,
    spaceAfter=8,
))
styles.add(ParagraphStyle(
    name="Highlight",
    fontName="Helvetica-Bold",
    fontSize=11,
    leading=14,
    textColor=ACCENT,
    spaceAfter=6,
))


# ---------- Header / Footer ----------
def header_footer(canv, doc):
    canv.saveState()
    # footer
    canv.setFont("Helvetica", 8)
    canv.setFillColor(GRAY)
    canv.drawString(72, 30, "Propuesta · Cadena de Suministro AI · Confidencial")
    canv.drawRightString(letter[0] - 72, 30, f"Pag. {doc.page}")
    # top bar
    if doc.page > 1:
        canv.setStrokeColor(TEAL)
        canv.setLineWidth(2)
        canv.line(72, letter[1] - 50, letter[0] - 72, letter[1] - 50)
        canv.setFont("Helvetica-Bold", 9)
        canv.setFillColor(NAVY)
        canv.drawString(72, letter[1] - 45, "CADENA DE SUMINISTRO AI")
        canv.setFont("Helvetica", 8)
        canv.setFillColor(GRAY)
        canv.drawRightString(letter[0] - 72, letter[1] - 45, "Propuesta para Cristian Zarate")
    canv.restoreState()


# ---------- Helpers ----------
def hr(color=TEAL, thickness=1):
    return HRFlowable(width="100%", thickness=thickness, color=color, spaceBefore=4, spaceAfter=8)


def section_title(text):
    return Paragraph(text, styles["H1"])


def sub(text):
    return Paragraph(text, styles["H2"])


def sub3(text):
    return Paragraph(text, styles["H3"])


def p(text):
    return Paragraph(text, styles["Body"])


def b(text):
    return Paragraph(text, styles["MyBullet"])


_CELL_STYLE = ParagraphStyle(
    name="TblCell",
    fontName="Helvetica",
    fontSize=8.5,
    leading=11,
    alignment=TA_LEFT,
    textColor=colors.black,
)
_CELL_HEADER = ParagraphStyle(
    name="TblHdr",
    fontName="Helvetica-Bold",
    fontSize=8.5,
    leading=11,
    alignment=TA_LEFT,
    textColor=colors.white,
)


def _wrap_cells(data, header=True):
    """Wrap every cell content in a Paragraph so it reflows inside fixed-width cells."""
    out = []
    for r, row in enumerate(data):
        new_row = []
        for c, cell in enumerate(row):
            if hasattr(cell, "wrap"):
                new_row.append(cell)
                continue
            text = "" if cell is None else str(cell)
            style = _CELL_HEADER if (header and r == 0) else _CELL_STYLE
            new_row.append(Paragraph(text, style))
        out.append(new_row)
    return out


def make_table(data, col_widths=None, header=True, zebra=True):
    data = _wrap_cells(data, header=header)
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCD6DD")),
    ]
    if header:
        style += [
            ("BACKGROUND", (0, 0), (-1, 0), NAVY),
        ]
    if zebra:
        for i in range(1 if header else 0, len(data)):
            if i % 2 == (1 if header else 0):
                style.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(style))
    return t


# ---------- Documento ----------
story = []


# ============= COVER =============
story.append(Spacer(1, 1.4 * inch))
story.append(Paragraph("CADENA DE SUMINISTRO AI", styles["CoverTitle"]))
story.append(Paragraph(
    "Plataforma ERP operativa para distribuidores B2B/B2G de productos perecederos y no perecederos",
    styles["CoverSubtitle"]
))
story.append(Spacer(1, 0.3 * inch))
story.append(hr(color=TEAL, thickness=2))
story.append(Spacer(1, 0.3 * inch))
story.append(Paragraph("Propuesta Tecnica y Comercial", styles["H2"]))
story.append(Spacer(1, 0.15 * inch))
story.append(Paragraph("Preparada para:", styles["CoverMeta"]))
story.append(Paragraph("<b>Cristian Zarate</b>", styles["H3"]))
story.append(Paragraph("Inversionista &mdash; Frutas Kelly", styles["CoverMeta"]))
story.append(Spacer(1, 0.4 * inch))
story.append(Paragraph("Cliente operativo: <b>EHMO</b>", styles["CoverMeta"]))
story.append(Paragraph("Proveedores integrados: <b>Frutas Kelly + 99 mas</b>", styles["CoverMeta"]))
story.append(Paragraph("Mercado meta: hospitales y comedores publicos en Mexico", styles["CoverMeta"]))
story.append(Spacer(1, 0.6 * inch))
story.append(hr(color=GRAY, thickness=0.5))
story.append(Spacer(1, 0.15 * inch))
story.append(Paragraph("Fecha: 4 de Mayo de 2026", styles["CoverMeta"]))
story.append(Paragraph("Version: 1.0", styles["CoverMeta"]))
story.append(Paragraph("Documento confidencial", styles["CoverMeta"]))
story.append(PageBreak())


# ============= TOC simple (manual) =============
story.append(section_title("Indice"))
toc = [
    ["1.", "Resumen Ejecutivo", "3"],
    ["2.", "El Problema (cuantificado)", "4"],
    ["3.", "La Solucion", "5"],
    ["4.", "Modelo de Negocio", "7"],
    ["5.", "Categorias de Productos", "8"],
    ["6.", "Arquitectura Tecnica", "9"],
    ["7.", "Estado Actual del Desarrollo", "11"],
    ["8.", "Roadmap y Tiempos de Entrega", "12"],
    ["9.", "Analisis de Costos: Tradicional vs AI-assisted", "14"],
    ["10.", "ROI y Justificacion del Hardware", "17"],
    ["11.", "Riesgos y Mitigaciones", "18"],
    ["12.", "KPIs y Metricas de Exito", "19"],
    ["13.", "Equipo y Gobernanza", "20"],
    ["14.", "Documentos Pre-Proyecto Requeridos", "21"],
    ["15.", "Siguientes Pasos y Aprobaciones", "23"],
]
toc_tbl = Table(toc, colWidths=[0.5*inch, 4.5*inch, 0.7*inch])
toc_tbl.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
    ("FONTSIZE", (0, 0), (-1, -1), 11),
    ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ("ALIGN", (2, 0), (2, -1), "RIGHT"),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ("TEXTCOLOR", (0, 0), (-1, -1), NAVY),
    ("LINEBELOW", (0, 0), (-1, -1), 0.3, colors.HexColor("#DDDDDD")),
]))
story.append(toc_tbl)
story.append(PageBreak())


# ============= 1. RESUMEN EJECUTIVO =============
story.append(section_title("1. Resumen Ejecutivo"))
story.append(hr())
story.append(p(
    "<b>Cadena de Suministro AI</b> es una plataforma ERP vertical especializada en la operacion de "
    "distribuidores B2B/B2G de productos alimenticios y de consumo (perecederos y no perecederos) "
    "que venden a hospitales, comedores y entidades publicas en Mexico."
))
story.append(p(
    "El sistema reemplaza la combinacion fragmentada de Odoo, Sicar, Excel, WhatsApp y correo "
    "que hoy usa <b>EHMO</b> (cliente operativo principal) con un solo producto digital integrado: "
    "ingesta multicanal de pedidos, inventario triple-estado con conversiones flexibles, "
    "facturacion CFDI 4.0 bidireccional, cuentas por cobrar y por pagar con conciliacion "
    "automatica, y portal de proveedores."
))
story.append(p(
    "<b>Frutas Kelly</b> participa con doble rol: (1) inversionista del software, "
    "(2) proveedor integrado en la plataforma. La vision a 24 meses es escalar el sistema "
    "como SaaS multi-tenant para distribuidores de alimentos similares en Mexico y Centroamerica."
))
story.append(Spacer(1, 0.15 * inch))
story.append(sub("Numeros clave de la propuesta"))

resumen_data = [
    ["Indicador", "Valor"],
    ["Inversion total estimada (MVP completo)", "$ 280,000 - 617,000 MXN (3 opciones)"],
    ["Opcion recomendada (B)", "$ 450,000 MXN"],
    ["Inversion en desarrollo tradicional equivalente", "$ 2,900,000 - 3,335,000 MXN"],
    ["Ahorro estimado vs tradicional", "80 - 91 % (~$ 2.5 - 2.9 M MXN)"],
    ["Tiempo de entrega MVP (con AI-assisted dev)", "3 a 4 meses"],
    ["Tiempo de entrega tradicional equivalente", "8 a 12 meses"],
    ["Avance actual del desarrollo", "~ 35 % del MVP (Sprints 1-6 cerrados)"],
    ["Volumen operativo MVP", "50 pedidos/dia, 100 proveedores, 600 SKUs"],
    ["KPI norte de exito", "Horas humanas absorbidas con cero errores"],
]
story.append(make_table(resumen_data, col_widths=[3.0*inch, 3.0*inch]))
story.append(Spacer(1, 0.15 * inch))
story.append(Paragraph(
    "<i>El proyecto ya tiene una base tecnica funcional (32 tablas, 52 endpoints REST, "
    "56 tests automatizados pasando) que puede demostrarse en vivo el dia de la "
    "presentacion al inversionista.</i>",
    styles["Quote"]
))
story.append(PageBreak())


# ============= 2. PROBLEMA =============
story.append(section_title("2. El Problema (cuantificado)"))
story.append(hr())
story.append(p(
    "EHMO opera como distribuidor central que recibe pedidos de hospitales y comedores publicos "
    "y los reparte a una red de ~100 proveedores (incluyendo Frutas Kelly). Esta operacion "
    "tiene los siguientes puntos de dolor verificados:"
))

story.append(sub("2.1 Captura manual masiva en multiples canales"))
story.append(b("&bull; Pedidos llegan via WhatsApp (texto, foto, audio), correo (Excel, PDF), o impresos."))
story.append(b("&bull; Operadores transcriben manualmente cada pedido a Excel y al ERP existente."))
story.append(b("&bull; Cambios constantes durante el dia: sustituciones, ajustes de peso, cancelaciones."))
story.append(b("&bull; Tiempo promedio estimado por operador: <b>4-6 horas/dia</b> solo en captura."))

story.append(sub("2.2 Falta de distincion catalogado vs no-catalogado"))
story.append(p(
    "Los hospitales contratan productos por SKU formal (ej. \"Manzana Roja\"), pero EHMO en bodega "
    "tiene multiples variedades (Royal Gala, Fuji, etc.) que deben sustituirse. Hoy esto se hace "
    "manualmente, sin trazabilidad, y genera errores de inventario y conciliacion fiscal."
))

story.append(sub("2.3 Sistemas fragmentados sin integracion"))
story.append(b("&bull; <b>Odoo</b> para parte contable, <b>Sicar</b> para punto de venta, <b>Excel</b> para inventario."))
story.append(b("&bull; <b>WhatsApp</b> y <b>correo</b> como canales de pedidos sin estandarizar."))
story.append(b("&bull; Reconciliacion manual entre sistemas: errores frecuentes, retrabajo, retrasos."))

story.append(sub("2.4 Conciliacion CFDI manual"))
story.append(b("&bull; Proveedores facturan en sus propios sistemas; EHMO recibe XMLs por correo."))
story.append(b("&bull; No existe matching automatico CFDI &harr; remision &harr; orden de compra."))
story.append(b("&bull; Errores fiscales que requieren cancelacion y re-emision (~3-5 % del volumen)."))

story.append(sub("2.5 Inventario opaco"))
story.append(b("&bull; No hay distincion entre <b>inventario fisico</b>, <b>remision pendiente de facturar</b>, y <b>venta facturada</b>."))
story.append(b("&bull; Mermas no documentadas; perdida de margen entre 2-7 % no rastreado."))
story.append(b("&bull; Multi-bodega futura (5 regiones) imposible de gestionar sin sistema."))

story.append(sub("2.6 Cuentas por pagar y por cobrar sin cruce"))
story.append(b("&bull; Hospitales gobierno pagan a 60-90 dias; proveedores requieren pago a 15-30."))
story.append(b("&bull; Riesgo de flujo de caja sin visibilidad consolidada."))
story.append(PageBreak())


# ============= 3. SOLUCION =============
story.append(section_title("3. La Solucion"))
story.append(hr())
story.append(p(
    "Un solo sistema digital, modular, accesible via web (operador EHMO + portal proveedor) "
    "y con AI integrado para automatizar las tareas que hoy consumen horas humanas."
))

story.append(sub("3.1 Modulos del sistema"))
modulos_data = [
    ["#", "Modulo", "Funcion", "Estado"],
    ["1", "Pedidos multicanal", "Ingesta desde WhatsApp, correo, Excel, PDF, foto, texto. AI normaliza.", "En desarrollo"],
    ["2", "Catalogo de productos", "600 SKUs en 12 categorias (perecederos + no perecederos).", "Listo (110 SKUs)"],
    ["3", "Conversiones flexibles", "Catalogado &harr; no-catalogado con merma, mezcla, factor variable.", "Sprint 8"],
    ["4", "Inventario triple-estado", "Fisico / remision pendiente / venta facturada.", "Sprint 7"],
    ["5", "Ordenes de compra", "EHMO &rarr; proveedor, con tracking de entrega.", "Sprint 7"],
    ["6", "Remisiones internas", "Entrega al cliente con ajustes en sitio (peso, cancelacion).", "Sprint 7"],
    ["7", "CFDI emitido", "EHMO factura al hospital con CSDs propios. Listo el builder.", "85 % listo"],
    ["8", "CFDI recibido", "Subida manual o AI-extracted desde correo. Matching automatico.", "Sprint 9-12"],
    ["9", "Cuentas por pagar (CxP)", "Cruce factura proveedor &harr; pago programado.", "Sprint 9"],
    ["10", "Cuentas por cobrar (CxC)", "Cruce factura hospital &harr; cobro recibido.", "Sprint 9"],
    ["11", "Conciliacion bancaria", "Match estados de cuenta &harr; pagos/cobros del sistema.", "Sprint 10"],
    ["12", "Portal de proveedor", "Login limitado: subir CFDI, ver entregas, ver pagos pendientes.", "Sprint 11"],
    ["13", "Reportes operativos", "Dashboard tiempo real: ventas, compras, mermas, margen.", "30 % listo"],
    ["14", "Reportes contables", "Exportable a contador / SAT.", "Sprint 13"],
    ["15", "Migracion legacy", "Importar Odoo, Sicar, Excel a la nueva plataforma.", "Sprint 13"],
]
story.append(make_table(modulos_data, col_widths=[0.3*inch, 1.6*inch, 3.2*inch, 1.0*inch]))

story.append(Spacer(1, 0.1 * inch))
story.append(sub("3.2 Diferenciador clave: el inventario triple-estado"))
story.append(p(
    "Es la innovacion conceptual que distingue este ERP de Odoo/Sicar/SAP genericos. "
    "El sistema reconoce que en distribucion alimentaria existen tres estados simultaneos del producto:"
))
story.append(b("&bull; <b>Inventario fisico:</b> producto real en bodega."))
story.append(b("&bull; <b>Remision pendiente:</b> entregado al cliente pero no facturado fiscalmente."))
story.append(b("&bull; <b>Venta facturada:</b> CFDI emitido, contable y fiscalmente cerrado."))
story.append(p("<b>Ecuacion maestra:</b>"))
story.append(Paragraph(
    "<font face='Courier' size='10'>"
    "inventario_fisico = compras_recibidas &minus; ventas_facturadas &minus; "
    "remisiones_pendientes &minus; mermas &minus; ajustes"
    "</font>",
    styles["Body"]
))

story.append(sub("3.3 AI integrado en puntos de mayor friccion"))
story.append(b("&bull; <b>Clasificacion de claves SAT</b> (c_ClaveProdServ): Claude Haiku, ~$0.05 USD por 110 productos."))
story.append(b("&bull; <b>Lectura de pedidos en formato libre</b> (WhatsApp/foto/texto): Claude Sonnet con OCR."))
story.append(b("&bull; <b>Extraccion de CFDI desde correo</b>: agente que lee bandeja y registra factura."))
story.append(b("&bull; <b>Matching difuso</b> de unidades de entrega y nombres de productos: rapidfuzz local."))
story.append(b("&bull; <b>Sugerencia de sustituciones</b>: Claude Haiku consultando tabla de conversiones."))
story.append(PageBreak())


# ============= 4. MODELO DE NEGOCIO =============
story.append(section_title("4. Modelo de Negocio"))
story.append(hr())

story.append(sub("4.1 Etapas evolutivas del modelo"))
modelo_data = [
    ["Etapa", "Plazo", "Quien paga", "Modalidad", "Volumen"],
    ["MVP interno", "Mes 0-4", "Frutas Kelly (inversionista)", "Inversion fija", "1 tenant (EHMO)"],
    ["Operacion EHMO", "Mes 4-12", "EHMO (operacion mensual)", "Subscription mensual", "1 tenant produccion"],
    ["Expansion proveedores", "Mes 6-18", "EHMO (asientos)", "Por usuario activo", "100+ usuarios proveedor"],
    ["SaaS multi-tenant", "Mes 12-24", "Distribuidores tipo-EHMO", "Subscription + uso", "5-15 tenants"],
    ["Plataforma regional", "Ano 2-3", "Distribuidores LATAM", "Subscription + revenue share", "30-100 tenants"],
]
story.append(make_table(modelo_data, col_widths=[1.2*inch, 0.8*inch, 1.4*inch, 1.4*inch, 1.4*inch]))

story.append(sub("4.2 Estructura de pricing futuro (estimacion)"))
pricing_data = [
    ["Concepto", "Estimacion", "Nota"],
    ["Subscription base por tenant", "$ 8,000 - 18,000 MXN/mes", "Segun volumen"],
    ["Asiento por usuario adicional", "$ 250 - 500 MXN/mes", "Operadores y proveedores"],
    ["Costo por CFDI emitido", "$ 0.80 - 2.00 MXN", "Pasa a Facturama PAC"],
    ["Setup / onboarding", "$ 25,000 - 80,000 MXN one-time", "Migracion de datos"],
    ["Soporte premium 24/7", "$ 5,000 - 15,000 MXN/mes", "Opcional"],
]
story.append(make_table(pricing_data, col_widths=[2.4*inch, 1.6*inch, 2.0*inch]))

story.append(sub("4.3 Unit economics estimados (por tenant tipo EHMO)"))
unit_data = [
    ["Concepto", "Mensual", "Anual"],
    ["Ingreso (subscription + asientos + CFDIs)", "$ 25,000 MXN", "$ 300,000 MXN"],
    ["Costos directos (Supabase + Anthropic + Render)", "$ 4,500 MXN", "$ 54,000 MXN"],
    ["Costos Facturama (pass-through)", "$ 1,800 MXN", "$ 21,600 MXN"],
    ["Soporte + mantenimiento (alocado)", "$ 6,000 MXN", "$ 72,000 MXN"],
    ["<b>Margen bruto por tenant</b>", "<b>$ 12,700 MXN</b>", "<b>$ 152,400 MXN</b>"],
    ["Margen %", "~ 51 %", "~ 51 %"],
]
story.append(make_table(unit_data, col_widths=[3.0*inch, 1.5*inch, 1.5*inch]))

story.append(sub("4.4 Punto de equilibrio (basado en Opcion B = $ 450,000)"))
story.append(p(
    "Con la inversion de la <b>Opcion B = $ 450,000 MXN</b> y un margen mensual de "
    "<b>$ 12,700 MXN/tenant</b>, el punto de equilibrio se alcanza con:"
))
story.append(b("&bull; <b>1 tenant (EHMO)</b> activo durante <b>~ 36 meses</b>, o"))
story.append(b("&bull; <b>3 tenants</b> activos durante <b>~ 12 meses</b>, o"))
story.append(b("&bull; <b>5 tenants</b> activos durante <b>~ 7 meses</b>."))
story.append(p(
    "<i>Con la Opcion A ($ 280,000) el break-even baja a 22 meses con 1 tenant. "
    "Con la Opcion C ($ 617,000) sube a 49 meses con 1 tenant pero el plazo de entrega "
    "es menor.</i>"
))
story.append(PageBreak())


# ============= 5. CATEGORIAS DE PRODUCTOS =============
story.append(section_title("5. Categorias de Productos"))
story.append(hr())
story.append(p(
    "El sistema soporta el espectro completo de productos que un distribuidor B2B/B2G "
    "alimentario maneja, no solo perecederos. Cada categoria tiene reglas distintas "
    "de inventario, vencimiento, almacenamiento y conversiones."
))

cat_data = [
    ["Categoria", "Tipo", "Reglas especiales", "Cold chain"],
    ["Frutas y verduras", "Perecedero", "FIFO estricto, conversiones por variedad", "Si (refrigeracion)"],
    ["Lacteos y embutidos", "Perecedero", "Caducidad obligatoria, lote requerido", "Si (refrigeracion)"],
    ["Proteina animal", "Perecedero", "Lote, caducidad, NOM-251, congelacion", "Si (congelado)"],
    ["Tortillas", "Perecedero corto", "Vencimiento 24-72h, distribucion diaria", "Ambiente / templado"],
    ["Pan", "Perecedero corto", "Vencimiento 1-7 dias", "Ambiente"],
    ["Granos / semillas / secos", "No perecedero", "Lotes, control de plagas, FIFO suave", "Ambiente seco"],
    ["Abarrote", "No perecedero", "Caducidad larga, control por unidad", "Ambiente"],
    ["Agua", "No perecedero", "Por garrafon o caja, devolucion de envase", "Ambiente"],
    ["Refresco", "No perecedero", "Por caja, devolucion de envase, IEPS", "Ambiente / refrig."],
    ["Productos de limpieza", "No perecedero", "Hojas de seguridad MSDS, no mezclar con alimento", "Ambiente"],
    ["Desechables", "No perecedero", "Volumen alto, baja rotacion por unidad", "Ambiente"],
    ["Otros (configurable)", "Variable", "Plantilla para futuras categorias", "Configurable"],
]
story.append(make_table(cat_data, col_widths=[1.5*inch, 1.0*inch, 2.5*inch, 1.0*inch]))

story.append(Spacer(1, 0.15 * inch))
story.append(sub("5.1 Implicaciones de soportar ambos tipos"))
story.append(b("&bull; <b>Tabla productos</b> con campos <i>perecedero</i>, <i>requiere_lote</i>, <i>requiere_caducidad</i>, <i>cold_chain</i>."))
story.append(b("&bull; <b>Tabla lotes</b> obligatoria para perecederos (lote, fecha_caducidad, fecha_recepcion)."))
story.append(b("&bull; <b>Tabla bodegas</b> con tipo (seca, refrigerada, congelada) para validar zonas."))
story.append(b("&bull; <b>Conversiones</b> aplican principalmente a F&V; los demas categorias son SKU directo."))
story.append(b("&bull; <b>Reportes</b> diferenciados: rotacion, mermas, vencimientos proximos por categoria."))
story.append(b("&bull; <b>Alertas</b> automaticas de vencimiento (perecederos), faltante (no-perec.)."))
story.append(PageBreak())


# ============= 6. ARQUITECTURA TECNICA =============
story.append(section_title("6. Arquitectura Tecnica"))
story.append(hr())

story.append(sub("6.1 Stack actual"))
stack_data = [
    ["Capa", "Tecnologia", "Justificacion"],
    ["Backend API", "FastAPI + Python 3.11", "Desempeno alto, OpenAPI auto, ecosystem maduro"],
    ["Base de datos", "PostgreSQL 17 (Supabase)", "RLS multi-tenant, full-text search, CDC"],
    ["Auth y RLS", "Supabase Auth (JWT)", "Cero-config, multi-rol, magic links, OTP"],
    ["Storage", "Supabase Storage", "CSDs cifrados, CFDI XMLs, fotos de pedidos"],
    ["Migraciones", "Alembic", "Versionado, rollback, idempotente"],
    ["Frontend operador", "HTML + JS (estatico) &rarr; Next.js (Sprint 5)", "Iteracion rapida primero, UX pulida despues"],
    ["AI / NLP", "Anthropic Claude (Haiku + Sonnet)", "Prompt caching, costo bajo, calidad alta"],
    ["Fuzzy matching", "rapidfuzz (local)", "Normalizacion de nombres, sin costo API"],
    ["CFDI / PAC", "Facturama (sandbox + prod)", "PAC autorizado SAT, API REST documentada"],
    ["Hosting backend", "Render (Starter $7/mes)", "CI/CD desde GitHub, escala vertical"],
    ["Repo y CI", "GitHub + GitHub Actions", "Tests automaticos en cada push"],
    ["Observabilidad", "Sentry + UptimeRobot", "Errores en tiempo real, alertas SLA"],
]
story.append(make_table(stack_data, col_widths=[1.6*inch, 2.2*inch, 2.2*inch]))

story.append(sub("6.2 Arquitectura multi-tenant"))
story.append(p(
    "Schema compartido con <b>Row-Level Security (RLS)</b> activado en 24 tablas. "
    "Cada query incluye automaticamente el filtro <i>tenant_id</i> impuesto a nivel base de datos. "
    "Migracion futura a schema-per-tenant es simple si crecemos a 50+ tenants."
))

story.append(sub("6.3 Esquema de seguridad"))
story.append(b("&bull; <b>JWT short-lived</b> (15 min) + refresh token (7 dias) via Supabase Auth."))
story.append(b("&bull; <b>RLS policies</b> jerarquicas por tenant + rol (operador, supervisor, proveedor, admin)."))
story.append(b("&bull; <b>CSDs SAT</b> cifrados en reposo (AES-256-GCM) en Supabase Storage privado."))
story.append(b("&bull; <b>Audit log</b> en tabla append-only para todas las operaciones criticas."))
story.append(b("&bull; <b>Backups diarios</b> Supabase + retencion 7 dias en Pro tier."))
story.append(b("&bull; <b>2FA</b> obligatorio para roles administrativos."))

story.append(sub("6.4 Escalabilidad esperada"))
escala_data = [
    ["Volumen", "Hoy MVP", "Capacidad stack actual", "Cuando upgrade"],
    ["Pedidos/dia", "50", "5,000+ sin cambio", "Nunca (sobra)"],
    ["Productos/tenant", "600", "100,000+ sin cambio", "Nunca (sobra)"],
    ["Usuarios concurrentes", "5-10", "200+ con Render Starter", "&gt; 200 usuarios"],
    ["CFDIs/mes", "1,500", "10,000+ via Facturama", "&gt; 10,000 (cambiar a Pro)"],
    ["Storage CFDIs / fotos", "&lt; 1 GB", "100 GB en Supabase Pro", "&gt; 80 GB"],
    ["Tenants", "1", "20-50 sin cambio", "&gt; 50 (schema-per-tenant)"],
]
story.append(make_table(escala_data, col_widths=[1.4*inch, 1.0*inch, 2.0*inch, 1.6*inch]))
story.append(PageBreak())


# ============= 7. ESTADO ACTUAL =============
story.append(section_title("7. Estado Actual del Desarrollo"))
story.append(hr())
story.append(Paragraph(
    "<b>Avance estimado: 35 % del MVP completo.</b>",
    styles["Highlight"]
))

story.append(sub("7.1 Lo que YA esta operativo (verificable)"))
estado_ok = [
    ["Item", "Cantidad", "Verificacion"],
    ["Tablas en base de datos", "32 + alembic_version", "Postgres local 5433"],
    ["Endpoints REST", "52", "GET /docs (OpenAPI)"],
    ["Tests automatizados pasando", "56 / 56", "pytest tests/ (0.78 s)"],
    ["Sprints completados", "1, 2, 3 (prep), 5 (skel.), 6 (prep)", "Git log"],
    ["Commits firmados", "6", "Branch main"],
    ["Tenant migrado", "Frutas Kelly", "1 tenant, 2 clientes (EHMO + Surena)"],
    ["Clientes operativos", "2 (EHMO Chiapas + SURENA)", "Tabla clientes"],
    ["Unidades de entrega", "27 (21 hospitales + 6 comedores)", "Tabla unidades_entrega"],
    ["Productos catalogados", "110", "Tabla productos"],
    ["Precios cargados", "216", "Tabla precios"],
    ["Pedidos historicos migrados", "42 (con 464 lineas)", "Tabla pedidos"],
    ["Catalogos SAT (subset)", "83 filas", "6 tablas SAT"],
    ["Frontend operador", "6 pestanas funcionales", "http://localhost:8000/"],
    ["CFDI builder", "Listo (sin timbrar)", "GET /pedidos/{id}/cfdi-preview"],
    ["Cliente Facturama", "Listo (sandbox)", "test_facturama_client (5 tests)"],
    ["Clasificador SAT con AI", "Listo (sin aplicar)", "scripts/classify_all_clave_sat.py"],
]
story.append(make_table(estado_ok, col_widths=[2.4*inch, 1.6*inch, 2.0*inch]))

story.append(sub("7.2 Lo que falta (Sprints 7-15)"))
falta_data = [
    ["Sprint", "Modulo", "Tiempo estimado AI"],
    ["1.5", "Deploy a Supabase + Render + auth real", "1-2 dias"],
    ["7", "Inventario triple-estado + remisiones + ordenes compra", "1-2 semanas"],
    ["8", "Conversiones catalogado/no-catalogado (merma + mezcla)", "1 semana"],
    ["9", "CxP / CxC + matching CFDI &harr; remision", "1.5 semanas"],
    ["10", "Ingest multicanal con AI (correo + WhatsApp + foto + PDF)", "2 semanas"],
    ["11", "Portal proveedor + auth segregada", "1 semana"],
    ["12", "AI extrae CFDI desde correo de proveedores", "1 semana"],
    ["13", "Migracion Odoo + Sicar + Excel a la nueva plataforma", "2-3 semanas"],
    ["14", "Multi-bodega + transferencias", "1 semana"],
    ["15", "Sustituciones con workflow de aprobacion", "1 semana"],
]
story.append(make_table(falta_data, col_widths=[0.7*inch, 3.7*inch, 1.6*inch]))
story.append(PageBreak())


# ============= 8. ROADMAP =============
story.append(section_title("8. Roadmap y Tiempos de Entrega"))
story.append(hr())

story.append(sub("8.1 Linea de tiempo MVP"))
roadmap_data = [
    ["Mes", "Hito", "Entregable", "Validacion"],
    ["Mes 0", "Estado actual", "Backend + datos migrados local", "56 tests pasando"],
    ["Mes 1", "Sprint 1.5 + 7", "Deploy nube + inventario + remisiones", "EHMO ve datos en cloud"],
    ["Mes 2", "Sprint 8 + 9", "Conversiones + CxP/CxC + conciliacion", "1 ciclo completo simulado"],
    ["Mes 3", "Sprint 10 + 11 + 12", "Ingest AI + portal proveedor + AI CFDIs", "Frutas Kelly subiendo facturas"],
    ["Mes 4", "Sprint 13 + 14 + 15", "Migracion legacy + multi-bodega + aprob.", "Go-live MVP en EHMO"],
    ["Mes 5", "Estabilizacion", "Bugs, UX polishing, capacitacion", "Operadores capacitados"],
    ["Mes 6", "Tenants 2-3", "Onboarding distribuidores adicionales", "SaaS demostrable"],
]
story.append(make_table(roadmap_data, col_widths=[0.7*inch, 1.1*inch, 2.7*inch, 1.5*inch]))

story.append(sub("8.2 Compromisos de fechas"))
fechas_data = [
    ["Hito", "Fecha objetivo", "Buffer"],
    ["Deploy a Supabase + Render", "15 May 2026", "+ 5 dias"],
    ["MVP modulo Inventario y Remisiones", "15 Jun 2026", "+ 1 semana"],
    ["MVP modulo Conversiones + CxP/CxC", "15 Jul 2026", "+ 1 semana"],
    ["Demo a EHMO con flujo completo", "15 Ago 2026", "+ 2 semanas"],
    ["Go-live MVP en EHMO produccion", "15 Sep 2026", "+ 2 semanas"],
    ["Estabilizacion + capacitacion", "30 Oct 2026", "+ 2 semanas"],
    ["Onboarding tenant 2 (otro distribuidor)", "1 Dic 2026", "Comercial"],
]
story.append(make_table(fechas_data, col_widths=[3.0*inch, 1.5*inch, 1.5*inch]))

story.append(sub("8.3 Velocidad ya demostrada"))
story.append(p(
    "En las primeras semanas de desarrollo (Sprints 1-6), con metodologia AI-assisted, "
    "se logro lo siguiente medido en velocidad de entrega:"
))
story.append(b("&bull; <b>52 endpoints REST</b> con tests, schemas y validaciones."))
story.append(b("&bull; <b>32 tablas</b> con migraciones Alembic versionadas."))
story.append(b("&bull; <b>56 tests automatizados</b> pasando en 0.78 segundos."))
story.append(b("&bull; <b>5 servicios reutilizables</b> (fuzzy, pedidos, cfdi, facturama, classifier)."))
story.append(b("&bull; <b>6 commits</b> firmados con co-autoria AI."))
story.append(b("&bull; <b>Tiempo invertido: ~ 8 horas de sesion AI autonoma + supervision.</b>"))
story.append(p(
    "Esta velocidad es <b>5-10 veces superior</b> a la de un equipo tradicional equivalente, "
    "y es la base de la proyeccion de costos en la siguiente seccion."
))
story.append(PageBreak())


# ============= 9. ANALISIS DE COSTOS =============
story.append(section_title("9. Analisis de Costos: Tradicional vs AI-assisted"))
story.append(hr())
story.append(p(
    "Comparacion directa entre el costo de desarrollar este sistema con un equipo humano tradicional "
    "vs el modelo AI-assisted (1 orquestador humano + Claude Code en hardware Apple Silicon)."
))

story.append(sub("9.1 Modelo TRADICIONAL (equipo humano)"))
trad_data = [
    ["Rol", "Tarifa MXN/mes", "Meses", "Subtotal MXN"],
    ["Tech Lead Senior (full-time)", "90,000", "8", "720,000"],
    ["Backend Senior (full-time)", "70,000", "8", "560,000"],
    ["Frontend Mid-Senior (full-time)", "60,000", "6", "360,000"],
    ["DevOps part-time", "40,000", "8", "320,000"],
    ["Project Manager", "55,000", "8", "440,000"],
    ["QA Engineer", "40,000", "5", "200,000"],
    ["Diseno UX/UI (one-shot)", "&mdash;", "&mdash;", "120,000"],
    ["Asesoria fiscal CFDI / SAT", "&mdash;", "&mdash;", "60,000"],
    ["Infraestructura cloud (AWS / GCP)", "&mdash;", "8", "80,000"],
    ["Licencias y herramientas", "&mdash;", "8", "40,000"],
    ["<b>SUBTOTAL TRADICIONAL</b>", "", "", "<b>2,900,000</b>"],
    ["Reserva contingencia 15 %", "", "", "435,000"],
    ["<b>TOTAL TRADICIONAL</b>", "", "", "<b>3,335,000 MXN</b>"],
]
story.append(make_table(trad_data, col_widths=[2.6*inch, 1.4*inch, 0.8*inch, 1.4*inch]))
story.append(p("<b>Tiempo de entrega tradicional: 8 a 12 meses</b> (con riesgo de extension)."))

story.append(sub("9.2 Modelo AI-ASSISTED (Claude Code + Mac mini M4)"))

story.append(sub3("9.2.1 Hardware (one-time)"))
hw_data = [
    ["Item", "Especificacion", "Costo MXN"],
    ["Apple Mac mini M4", "Chip M4, 32 GB RAM unificada, SSD 512 GB", "32,500"],
    ["Almacenamiento externo 100 TB", "DAS Synology DS1823xs+ con 8 x 16 TB Seagate IronWolf Pro", "95,000"],
    ["Monitor 4K 27 pulgadas", "Para desarrollo confortable", "12,000"],
    ["Teclado + raton + UPS 1500VA", "Periferics y respaldo electrico", "8,500"],
    ["Conectividad y cables", "Thunderbolt, ethernet 10G, etc.", "4,000"],
    ["<b>TOTAL HARDWARE one-time</b>", "", "<b>152,000</b>"],
]
story.append(make_table(hw_data, col_widths=[2.0*inch, 3.0*inch, 1.2*inch]))
story.append(p(
    "<i>El hardware se justifica porque (a) el storage 100 TB permite mantener todos "
    "los datos historicos y backups locales sin costo cloud recurrente, "
    "(b) el M4 + 32 GB RAM ejecuta workloads de AI local complementarios "
    "(rapidfuzz, parseo de PDFs, transcripcion de audio), "
    "(c) tiene vida util de 5+ anos &mdash; costo amortizado: ~$ 2,500 MXN/mes.</i>"
))

story.append(sub3("9.2.2 Servicios mensuales recurrentes (durante desarrollo)"))
svc_data = [
    ["Servicio", "Costo USD/mes", "Costo MXN/mes"],
    ["Claude Code (Pro / Max)", "20", "400"],
    ["Anthropic API (uso desarrollo)", "30 - 80", "600 - 1,600"],
    ["Supabase Pro (DB + auth + storage)", "25", "500"],
    ["Render Starter (backend)", "7", "140"],
    ["GitHub Pro", "4", "80"],
    ["Sentry (errores)", "0 (free tier)", "0"],
    ["UptimeRobot (monitoreo)", "0 (free tier)", "0"],
    ["Facturama sandbox (pruebas)", "0", "0"],
    ["<b>TOTAL servicios MXN/mes</b>", "", "<b>1,720 - 2,720</b>"],
    ["x 4 meses de desarrollo", "", "<b>~ 9,000 MXN</b>"],
]
story.append(make_table(svc_data, col_widths=[2.6*inch, 1.5*inch, 1.5*inch]))

story.append(sub3("9.2.3 Recursos humanos (AI-assisted)"))
rh_data = [
    ["Rol", "Tarifa MXN/mes", "Meses", "Subtotal MXN"],
    ["Owner / Orquestador (Michel)", "70,000", "4", "280,000"],
    ["QA humano part-time (validacion)", "25,000", "2", "50,000"],
    ["Asesoria fiscal CFDI / SAT (one-shot)", "&mdash;", "&mdash;", "30,000"],
    ["Migracion legacy Odoo / Sicar", "&mdash;", "&mdash;", "40,000"],
    ["<b>SUBTOTAL recursos humanos</b>", "", "", "<b>400,000</b>"],
]
story.append(make_table(rh_data, col_widths=[2.6*inch, 1.4*inch, 0.8*inch, 1.4*inch]))

story.append(p(
    "<i>Las tres categorias anteriores (hardware, servicios, recursos humanos) son los "
    "<b>ingredientes</b> que se combinan en distintas proporciones segun la opcion de "
    "inversion que se elija. La seccion 9.3 muestra tres opciones reales y validas, cada una "
    "con su desglose linea-por-linea, dentro del rango total de $ 280,000 a $ 617,000 MXN.</i>"
))
story.append(PageBreak())


# ============= 9.3 TRES OPCIONES DE INVERSION =============
story.append(sub("9.3 Tres opciones de inversion (desglose linea-por-linea)"))
story.append(p(
    "Cada opcion es un proyecto completo y entregable. Se diferencian en hardware, "
    "dedicacion del owner, presencia de equipo de apoyo y plazo de entrega. La opcion B "
    "es la <b>recomendada</b> por balance entre costo, plazo y riesgo."
))

# ---------- OPCION A LEAN ----------
story.append(sub3("9.3.1 OPCION A &mdash; LEAN ($ 280,000 MXN)"))
story.append(p(
    "Para arrancar de inmediato con capital minimo. Frutas Kelly aporta hardware basico; "
    "el owner trabaja part-time con pago parcial. Apropiado si el plazo no es critico "
    "o si se quiere validar la curva de gasto antes de comprometer mas capital."
))
opa_data = [
    ["Concepto", "Detalle", "MXN"],
    ["Mac mini M4 base", "Chip M4, 16 GB RAM, SSD 512 GB", "28,000"],
    ["Storage externo 8 TB", "NAS Synology DS224+ con 2 x 4 TB IronWolf", "12,000"],
    ["Monitor 27\" + teclado + UPS 850 VA", "Setup minimo funcional", "18,000"],
    ["<b>Subtotal hardware</b>", "", "<b>58,000</b>"],
    ["Claude Code Pro + Anthropic API", "$ 1,000 MXN/mes x 4 meses", "4,000"],
    ["Supabase Pro + Render + GitHub Pro", "$ 800 MXN/mes x 4 meses", "3,200"],
    ["<b>Subtotal servicios</b>", "", "<b>7,200</b>"],
    ["Owner part-time (50 % dedicacion)", "$ 25,000 MXN/mes x 4 meses", "100,000"],
    ["QA humano part-time", "$ 20,000 MXN/mes x 1.5 meses", "30,000"],
    ["Asesoria fiscal CFDI / SAT (one-shot)", "Validacion regimenes y claves", "25,000"],
    ["Migracion legacy (subset critico)", "Excel + Sicar parcial", "25,000"],
    ["<b>Subtotal humanos + servicios pro</b>", "", "<b>180,000</b>"],
    ["Capacitacion EHMO (online minima)", "Sesiones grabadas", "10,000"],
    ["Reserva de contingencia (~ 9 %)", "", "25,000"],
    ["<b>TOTAL OPCION A &mdash; LEAN</b>", "", "<b>$ 280,200 MXN</b>"],
]
story.append(make_table(opa_data, col_widths=[2.6*inch, 2.4*inch, 1.0*inch]))
story.append(p(
    "<b>Implicaciones de A:</b> 4-5 meses de plazo, hardware no permite AI local intensivo, "
    "el owner asume parte del costo (~$ 100,000 MXN no compensados). Riesgo de burnout o desviacion."
))
story.append(PageBreak())

# ---------- OPCION B RECOMENDADA ----------
story.append(sub3("9.3.2 OPCION B &mdash; RECOMENDADA ($ 450,000 MXN)"))
story.append(p(
    "<b>Default sugerido.</b> Hardware completo Mac mini M4 32 GB + storage 100 TB; "
    "owner pagado a tasa de mercado pero part-time (alta dedicacion); QA y asesoria adecuadas; "
    "reserva razonable. Mejor relacion costo / plazo / riesgo."
))
opb_data = [
    ["Concepto", "Detalle", "MXN"],
    ["Apple Mac mini M4", "Chip M4, 32 GB RAM unificada, SSD 1 TB", "38,000"],
    ["Storage 100 TB profesional", "DAS Synology DS1823xs+ con 8 x 16 TB IronWolf Pro", "95,000"],
    ["Monitor 4K 27\" + teclado + UPS 1500 VA + Thunderbolt", "Setup pro completo", "19,000"],
    ["<b>Subtotal hardware</b>", "", "<b>152,000</b>"],
    ["Claude Code Pro + Anthropic API", "$ 1,200 MXN/mes x 4 meses", "4,800"],
    ["Supabase Pro + Render Starter + GitHub Pro", "$ 1,000 MXN/mes x 4 meses", "4,000"],
    ["<b>Subtotal servicios</b>", "", "<b>8,800</b>"],
    ["Owner part-time alta dedicacion (70 %)", "$ 50,000 MXN/mes x 4 meses", "200,000"],
    ["QA humano part-time (validacion flujos criticos)", "$ 25,000 MXN/mes x 2 meses", "50,000"],
    ["Asesoria fiscal CFDI / SAT (one-shot)", "Regimenes, claves, multi-PAC", "30,000"],
    ["Migracion legacy completa", "Excel + Sicar + Odoo full", "40,000"],
    ["Capacitacion presencial a operadores EHMO", "2 semanas en sitio", "20,000"],
    ["<b>Subtotal recursos humanos + servicios pro</b>", "", "<b>340,000</b>"],
    ["Reserva de contingencia (~ 11 %)", "Imprevistos tecnicos / regulatorios", "50,000"],
    ["<b>TOTAL OPCION B &mdash; RECOMENDADA</b>", "", "<b>$ 450,800 MXN</b>"],
]
story.append(make_table(opb_data, col_widths=[2.6*inch, 2.4*inch, 1.0*inch]))
story.append(p(
    "<b>Implicaciones de B:</b> 3-4 meses de plazo, hardware como activo a 5+ anos "
    "(amortizado ~$ 2,500 MXN/mes), storage local elimina dependencia de cloud para "
    "backups grandes, owner pagado en linea con mercado. Es la opcion con mejor "
    "<i>risk-adjusted return</i>."
))
story.append(PageBreak())

# ---------- OPCION C ACELERADA ----------
story.append(sub3("9.3.3 OPCION C &mdash; ACELERADA ($ 617,000 MXN)"))
story.append(p(
    "Igual que B pero con owner full-time + 1 desarrollador junior de apoyo. Reduce el plazo "
    "a ~ 3 meses. Recomendable solo si EHMO tiene fecha-tope de adopcion no-negociable o "
    "si hay competencia en el mercado que justifique la velocidad."
))
opc_data = [
    ["Concepto", "Detalle", "MXN"],
    ["Hardware Mac mini M4 + 100 TB (mismo que B)", "Pro setup completo", "152,000"],
    ["<b>Subtotal hardware</b>", "", "<b>152,000</b>"],
    ["Claude Code + Anthropic + Supabase + Render + GitHub", "$ 2,500 MXN/mes x 3 meses (uso intensivo)", "7,500"],
    ["<b>Subtotal servicios</b>", "", "<b>7,500</b>"],
    ["Owner full-time (100 % dedicacion)", "$ 70,000 MXN/mes x 3 meses", "210,000"],
    ["Desarrollador junior con AI tooling", "$ 35,000 MXN/mes x 3 meses", "105,000"],
    ["QA humano part-time (validacion intensiva)", "$ 25,000 MXN/mes x 2 meses", "50,000"],
    ["Asesoria fiscal CFDI / SAT", "", "30,000"],
    ["Migracion legacy completa", "Excel + Sicar + Odoo full", "40,000"],
    ["Capacitacion presencial a operadores EHMO", "2 semanas en sitio", "20,000"],
    ["<b>Subtotal recursos humanos</b>", "", "<b>455,000</b>"],
    ["Reserva de contingencia (~ 10 %)", "Mayor por riesgo de junior + ritmo", "56,000"],
    ["<b>TOTAL OPCION C &mdash; ACELERADA</b>", "", "<b>$ 670,500 MXN</b>"],
]
story.append(make_table(opc_data, col_widths=[2.6*inch, 2.4*inch, 1.0*inch]))
story.append(p(
    "<b>Implicaciones de C:</b> 2.5-3 meses de plazo, mayor velocidad pero capital adicional "
    "+ riesgo de onboarding del junior. La cifra final puede ajustarse a $ 617,000 si se "
    "logra optimizar el alcance del junior o reducir el plazo del owner full-time."
))

# ---------- COMPARATIVO ----------
story.append(sub3("9.3.4 Tabla comparativa de las tres opciones"))
ops_compare = [
    ["Variable", "A &mdash; LEAN", "B &mdash; RECOMENDADA", "C &mdash; ACELERADA"],
    ["Inversion total MXN", "$ 280,000", "$ 450,000", "$ 617,000"],
    ["Plazo de entrega", "4-5 meses", "3-4 meses", "2.5-3 meses"],
    ["Hardware", "Base + 8 TB", "Pro + 100 TB", "Pro + 100 TB"],
    ["Dedicacion owner", "50 % (parcial)", "70 % (alta)", "100 % (full-time)"],
    ["Equipo de apoyo", "QA part-time", "QA part-time", "QA + Junior dev"],
    ["Migracion legacy", "Subset critico", "Completa", "Completa"],
    ["Capacitacion EHMO", "Online minima", "Presencial 2 sem.", "Presencial 2 sem."],
    ["Reserva contingencia", "9 %", "11 %", "10 %"],
    ["Riesgo principal", "Burnout owner", "Bajo", "Onboarding junior"],
    ["AI local en hardware", "Limitado", "Completo", "Completo"],
    ["Recomendacion", "Si capital limitado", "<b>DEFAULT</b>", "Si plazo critico"],
]
story.append(make_table(ops_compare, col_widths=[1.5*inch, 1.4*inch, 1.5*inch, 1.5*inch]))
story.append(PageBreak())


# ============= 9.4 COMPARATIVA TRADICIONAL VS AI =============
story.append(sub("9.4 Comparativa final: Tradicional vs AI-assisted (Opcion B)"))
comp_data = [
    ["Variable", "Tradicional", "AI-assisted (B)", "Diferencia"],
    ["Costo total", "$ 3,335,000", "$ 450,000", "&minus; 86 % (~ $ 2.88 M)"],
    ["Tiempo de entrega", "8-12 meses", "3-4 meses", "&minus; 60 % (~ 6 meses)"],
    ["Tamano de equipo", "5-6 personas", "1-2 personas", "&minus; 75 %"],
    ["Riesgo de retraso", "Alto (depend. equipo)", "Bajo (ya validado)", "Mucho menor"],
    ["Calidad de codigo", "Variable por persona", "Consistente (LLM)", "Equivalente o mejor"],
    ["Documentacion", "Manual, parcial", "Auto-generada", "Mejor"],
    ["Tests automatizados", "Variable", "Sistematicos", "Mejor"],
    ["Activos al final", "Solo software", "Software + hardware", "Hardware reusable 5+ anos"],
]
story.append(make_table(comp_data, col_widths=[1.4*inch, 1.4*inch, 1.4*inch, 1.7*inch]))
story.append(PageBreak())


# ============= 10. ROI =============
story.append(section_title("10. ROI y Justificacion del Hardware"))
story.append(hr())

story.append(sub("10.1 Ahorro directo de capital"))
story.append(p(
    "Comparativa usando la <b>Opcion B (recomendada)</b> a $ 450,000 MXN como referencia. "
    "Si se elige la Opcion A el ahorro es aun mayor; si se elige C, sigue siendo "
    "&gt; 80 % de ahorro vs tradicional."
))
roi_data = [
    ["Concepto", "Tradicional", "AI-assisted (B)", "Ahorro"],
    ["Inversion total proyecto", "$ 3,335,000", "$ 450,000", "$ 2,885,000"],
    ["Salida de caja inmediata (mes 1)", "$ 800,000", "$ 200,000", "$ 600,000"],
    ["Costo mensual durante desarrollo", "$ 350,000", "$ 75,000", "$ 275,000/mes"],
]
story.append(make_table(roi_data, col_widths=[2.0*inch, 1.4*inch, 1.4*inch, 1.4*inch]))

story.append(sub("10.2 Justificacion del hardware Mac mini M4 + 100 TB"))
story.append(p("El hardware NO es un gasto, es un <b>activo</b> con multiples beneficios:"))
story.append(b("&bull; <b>Capex amortizable 5+ anos</b>: $ 152,000 / 60 meses = ~ $ 2,500 MXN/mes."))
story.append(b("&bull; <b>Reduccion del cloud bill</b>: storage local 100 TB elimina costo de S3 / R2 (~$ 300-800 USD/mes a esa escala)."))
story.append(b("&bull; <b>Backups locales</b> y <b>data lake</b> historico para analytics futuros."))
story.append(b("&bull; <b>Procesamiento AI local</b>: OCR, transcripcion de audio WhatsApp, parseo de PDFs sin costo API."))
story.append(b("&bull; <b>Soberania de datos</b>: archivos sensibles (CSDs, CFDIs) no salen de Mexico."))
story.append(b("&bull; <b>Disaster recovery</b> rapido: si Supabase falla, hay copia local."))
story.append(b("&bull; <b>Reusable en otros proyectos</b> de la familia Frutas Kelly / EHMO."))
story.append(b("&bull; <b>Apreciacion / valor de reventa</b>: Apple mantiene 50-60 % del precio en mercado secundario a 3 anos."))

story.append(sub("10.3 Retorno proyectado del proyecto (Opcion B)"))
ret_data = [
    ["Periodo", "Ingresos acumulados", "Costos acumulados", "Flujo neto"],
    ["Mes 4 (MVP)", "$ 0", "$ 450,000", "&minus; $ 450,000"],
    ["Mes 8 (1 tenant activo)", "$ 100,000", "$ 495,000", "&minus; $ 395,000"],
    ["Mes 12 (1 tenant + ajustes)", "$ 300,000", "$ 555,000", "&minus; $ 255,000"],
    ["Mes 18 (3 tenants)", "$ 720,000", "$ 720,000", "$ 0 (break-even)"],
    ["Mes 24 (5 tenants)", "$ 1,500,000", "$ 940,000", "<b>+ $ 560,000</b>"],
    ["Mes 36 (10 tenants)", "$ 3,300,000", "$ 1,490,000", "<b>+ $ 1,810,000</b>"],
]
story.append(make_table(ret_data, col_widths=[1.5*inch, 1.7*inch, 1.7*inch, 1.4*inch]))
story.append(p(
    "<b>Break-even alrededor del mes 18</b> con curva de adopcion conservadora. "
    "Comparado con desarrollo tradicional ($ 3.3 M de inversion inicial), el break-even "
    "tradicional seria mes 36-40. <b>El modelo AI adelanta el break-even ~ 18 meses.</b>"
))
story.append(PageBreak())


# ============= 11. RIESGOS =============
story.append(section_title("11. Riesgos y Mitigaciones"))
story.append(hr())

riesgo_data = [
    ["#", "Riesgo", "Probabilidad", "Impacto", "Mitigacion"],
    [
        "R1",
        "Anthropic / Claude API caida o cambio de pricing",
        "Bajo",
        "Medio",
        "Arquitectura desacopla LLM via interfaz; swap a OpenAI / Llama local en 2 dias",
    ],
    [
        "R2",
        "Facturama (PAC) caida en facturacion",
        "Medio",
        "Alto",
        "Multi-PAC ready: SDK abstrae proveedor; alternativa SW Sapien o Sat.ws",
    ],
    [
        "R3",
        "Datos fiscales en US (Supabase us-east-1) violan ley local",
        "Bajo (hoy)",
        "Alto (futuro)",
        "Migrar a region MX si SAT lo exige; backup local en Mac mini cubre auditoria",
    ],
    [
        "R4",
        "Hospital cancela contrato con EHMO",
        "Bajo-Medio",
        "Alto",
        "Diversificar a otros distribuidores; producto vendible como SaaS",
    ],
    [
        "R5",
        "AI alucina en clasificacion CFDI / claves SAT",
        "Bajo",
        "Medio",
        "Human-in-the-loop hasta 99 % accuracy; revision manual de outliers",
    ],
    [
        "R6",
        "Disponibilidad del orquestador (Michel)",
        "Medio",
        "Alto",
        "Documentacion exhaustiva auto-generada; backup developer pre-trained en stack",
    ],
    [
        "R7",
        "Dependencia de un solo proveedor (Frutas Kelly)",
        "Medio",
        "Alto (financiero)",
        "Acelerar tenant 2; vender SaaS antes del mes 12",
    ],
    [
        "R8",
        "Hardware Mac mini falla durante desarrollo",
        "Bajo",
        "Bajo (activos en cloud)",
        "AppleCare+; codigo y datos en GitHub + Supabase, mac es solo terminal",
    ],
    [
        "R9",
        "Resistencia al cambio de operadores EHMO",
        "Medio",
        "Medio",
        "Onboarding gradual; UX simple; capacitacion presencial 2 semanas",
    ],
    [
        "R10",
        "Cambio regulatorio CFDI (SAT version 5.0)",
        "Bajo (proximos 2 anos)",
        "Medio",
        "PAC se actualiza primero; refactor de adapter <1 semana",
    ],
]
ri_styled = []
for row in riesgo_data:
    ri_styled.append([Paragraph(c, styles["BodySmall"]) for c in row])
ri_tbl = Table(ri_styled, colWidths=[0.3*inch, 2.0*inch, 0.9*inch, 0.7*inch, 2.4*inch], repeatRows=1)
ri_tbl.setStyle(TableStyle([
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 5),
    ("RIGHTPADDING", (0, 0), (-1, -1), 5),
    ("TOPPADDING", (0, 0), (-1, -1), 5),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCD6DD")),
]))
story.append(ri_tbl)
story.append(PageBreak())


# ============= 12. KPIs =============
story.append(section_title("12. KPIs y Metricas de Exito"))
story.append(hr())

story.append(Paragraph(
    "Norte estrategico: <b>horas humanas absorbidas con cero errores</b>",
    styles["Highlight"]
))

story.append(sub("12.1 KPIs operativos (medidos en EHMO)"))
kpi_op = [
    ["KPI", "Hoy (estimado)", "Meta MVP (mes 6)", "Meta SaaS (mes 18)"],
    ["Horas/dia capturando pedidos", "4-6 hrs", "&lt; 1 hr", "&lt; 0.3 hr"],
    ["% pedidos auto-procesados", "~ 0 %", "&gt; 70 %", "&gt; 90 %"],
    ["Errores fiscales por mil CFDIs", "30-50", "&lt; 10", "&lt; 3"],
    ["Tiempo CFDI desde entrega a timbrado", "1-3 dias", "&lt; 2 hrs", "&lt; 30 min"],
    ["Discrepancia inventario fisico vs sistema", "5-10 %", "&lt; 2 %", "&lt; 0.5 %"],
    ["Mermas no documentadas", "2-7 %", "&lt; 1 %", "&lt; 0.3 %"],
    ["Conciliacion CFDI &harr; remision", "Manual", "Auto 80 %", "Auto 99 %"],
    ["Dias de cobranza promedio", "60-90", "60-75", "45-60"],
]
story.append(make_table(kpi_op, col_widths=[2.2*inch, 1.3*inch, 1.3*inch, 1.3*inch]))

story.append(sub("12.2 KPIs tecnicos del software"))
kpi_tech = [
    ["KPI", "Meta", "Como se mide"],
    ["Uptime del backend", "&gt; 99.5 %", "UptimeRobot"],
    ["Latencia P95 endpoints", "&lt; 300 ms", "Supabase logs / APM"],
    ["Tests automatizados pasando", "100 %", "GitHub Actions"],
    ["Cobertura de tests", "&gt; 70 %", "pytest-cov"],
    ["Errores en produccion", "&lt; 5 / dia", "Sentry"],
    ["Tiempo deploy a produccion", "&lt; 5 min", "Render CI/CD"],
    ["Tiempo restore desde backup", "&lt; 1 hr", "Supabase PITR"],
]
story.append(make_table(kpi_tech, col_widths=[2.6*inch, 1.5*inch, 1.9*inch]))

story.append(sub("12.3 KPIs comerciales (post-MVP)"))
kpi_com = [
    ["KPI", "Meta mes 12", "Meta mes 24"],
    ["Tenants activos", "1-2", "5-8"],
    ["Usuarios totales (operadores + proveedores)", "20-40", "150-300"],
    ["MRR (Monthly Recurring Revenue)", "$ 25,000 MXN", "$ 150,000 MXN"],
    ["Churn mensual", "0 %", "&lt; 5 %"],
    ["NPS (Net Promoter Score)", "&gt; 30", "&gt; 50"],
    ["Tiempo de onboarding tenant nuevo", "30 dias", "7 dias"],
]
story.append(make_table(kpi_com, col_widths=[3.0*inch, 1.5*inch, 1.5*inch]))
story.append(PageBreak())


# ============= 13. EQUIPO =============
story.append(section_title("13. Equipo y Gobernanza"))
story.append(hr())

story.append(sub("13.1 Roles y responsabilidades"))
equipo_data = [
    ["Rol", "Persona / Entidad", "Responsabilidad principal"],
    ["Inversionista", "Cristian Zarate / Frutas Kelly", "Capital, validacion comercial, gobierno de proyecto"],
    ["Cliente operativo", "EHMO (Direccion Operaciones)", "Validacion funcional, datos reales, capacitacion"],
    ["Owner / Tech Lead AI", "Michel Zarate", "Arquitectura, orquestacion AI, deploy, soporte"],
    ["AI partner", "Anthropic Claude (Sonnet/Haiku)", "Codigo, tests, refactor, documentacion auto"],
    ["QA humano (part-time)", "Por definir", "Validacion de flujos criticos, edge cases"],
    ["Asesor fiscal CFDI", "Por definir (one-shot)", "Validar logica SAT, regimenes, formas pago"],
    ["Stakeholders proveedores", "Frutas Kelly + 99 mas", "Subir CFDIs, validar entregas, dar feedback"],
    ["Stakeholders cliente final", "Hospitales y comedores", "Recibir CFDIs y producto, dar feedback indirecto"],
]
story.append(make_table(equipo_data, col_widths=[1.6*inch, 1.8*inch, 2.6*inch]))

story.append(sub("13.2 Modelo de gobernanza"))
story.append(b("&bull; <b>Reuniones semanales</b> de revision (30 min) con inversionista + EHMO."))
story.append(b("&bull; <b>Demo quincenal</b> con datos reales y validacion funcional."))
story.append(b("&bull; <b>Reportes mensuales</b> escritos: avance, costos, riesgos."))
story.append(b("&bull; <b>Pull requests</b> con co-autoria humana + AI; revision antes de merge."))
story.append(b("&bull; <b>Tablero Kanban</b> publico en GitHub Projects para transparencia."))
story.append(b("&bull; <b>Slack / WhatsApp</b> dedicado para preguntas operativas en tiempo real."))

story.append(sub("13.3 Estructura de decisiones"))
gov_data = [
    ["Tipo de decision", "Quien decide", "Quien consulta"],
    ["Arquitectura tecnica", "Owner / Tech Lead", "&mdash;"],
    ["Funcionalidades nuevas", "EHMO (operativa)", "Owner aprueba viabilidad"],
    ["Pricing comercial", "Inversionista", "Consulta a mercado"],
    ["Inversion adicional", "Inversionista", "Owner justifica"],
    ["Contrataciones", "Inversionista + Owner", "&mdash;"],
    ["Salida a tenants nuevos", "Inversionista + EHMO", "Owner valida tecnica"],
]
story.append(make_table(gov_data, col_widths=[2.0*inch, 2.0*inch, 2.0*inch]))
story.append(PageBreak())


# ============= 14. DOCUMENTOS PRE-PROYECTO =============
story.append(section_title("14. Documentos Pre-Proyecto Requeridos"))
story.append(hr())
story.append(p(
    "Antes de continuar formalmente con la fase de produccion (Sprint 1.5 en adelante), "
    "es necesario que se firmen / preparen los siguientes documentos. Se agrupan por categoria."
))

story.append(sub("14.1 Documentos legales"))
legal_data = [
    ["Documento", "Quien firma", "Estado"],
    ["Contrato de inversion (Frutas Kelly &rarr; vehiculo del proyecto)", "Cristian Zarate + Owner", "Pendiente"],
    ["Acuerdo de propiedad intelectual del codigo", "Inversionista + Owner", "Pendiente"],
    ["Acuerdo de confidencialidad (NDA) con EHMO", "EHMO + Owner", "Pendiente"],
    ["Acuerdo de confidencialidad con proveedores integrados", "Cada proveedor + EHMO", "Pendiente"],
    ["Terminos y condiciones de uso del software", "Owner emite", "Pendiente"],
    ["Politica de privacidad y manejo de datos personales (LFPDPPP)", "Owner emite", "Pendiente"],
    ["Acuerdo de niveles de servicio (SLA) con EHMO", "EHMO + Owner", "Pendiente"],
    ["Acuerdo de procesamiento de datos (DPA)", "Owner + cada tenant", "Pendiente (futuro)"],
    ["Constitucion de entidad legal del proyecto (S.A. de C.V.)", "Inversionista", "A evaluar"],
]
story.append(make_table(legal_data, col_widths=[3.6*inch, 1.6*inch, 0.8*inch]))

story.append(sub("14.2 Documentos tecnicos / operativos"))
tec_data = [
    ["Documento", "Responsable", "Estado"],
    ["Documento de arquitectura tecnica firmada", "Owner", "Borrador (en docs/)"],
    ["Plan de migracion Odoo &rarr; nueva plataforma", "Owner + EHMO IT", "Pendiente"],
    ["Plan de migracion Sicar &rarr; nueva plataforma", "Owner + EHMO IT", "Pendiente"],
    ["Plan de migracion Excel &rarr; nueva plataforma", "Owner + EHMO IT", "Pendiente"],
    ["Inventario de fuentes de datos actuales en EHMO", "EHMO IT", "Pendiente"],
    ["Mapeo de productos catalogados / no-catalogados (600 SKUs)", "EHMO operacion", "Pendiente"],
    ["Listado completo de proveedores con datos fiscales", "EHMO operacion", "Pendiente"],
    ["Listado de hospitales / comedores con datos fiscales", "EHMO operacion", "Pendiente"],
    ["CSDs (.cer + .key + password) de EHMO", "EHMO contabilidad", "Pendiente"],
    ["CSDs de proveedores que facturen aqui", "Cada proveedor", "Pendiente"],
    ["Plan de continuidad de negocio (BCP) y DR", "Owner", "Borrador pendiente"],
    ["Politica de seguridad de informacion (ISMS)", "Owner", "Pendiente"],
    ["Plan de capacitacion a operadores EHMO", "Owner + EHMO", "Pendiente"],
    ["Manual de usuario operador", "Owner (auto-doc)", "Por generar"],
    ["Manual de usuario proveedor", "Owner (auto-doc)", "Por generar"],
]
story.append(make_table(tec_data, col_widths=[3.6*inch, 1.6*inch, 0.8*inch]))
story.append(PageBreak())

story.append(sub("14.3 Documentos comerciales / contables"))
com_data = [
    ["Documento", "Responsable", "Estado"],
    ["Acuerdo comercial Facturama (PAC) y limites mensuales", "Owner", "Pendiente"],
    ["Acuerdo comercial Anthropic API (org account)", "Owner", "Pendiente"],
    ["Acuerdo comercial Supabase (Pro)", "Owner", "Pendiente"],
    ["Acuerdo comercial Render (Starter)", "Owner", "Pendiente"],
    ["Plan de cuentas contable EHMO mapeado al sistema", "Contador EHMO", "Pendiente"],
    ["Catalogo SAT vigente (c_ClaveProdServ + c_ClaveUnidad)", "Owner / SAT", "Subset listo"],
    ["Estructura de costos y precios por categoria de producto", "EHMO", "Pendiente"],
    ["Politica de credito y cobranza por cliente", "EHMO finanzas", "Pendiente"],
    ["Politica de pago a proveedores", "EHMO finanzas", "Pendiente"],
]
story.append(make_table(com_data, col_widths=[3.6*inch, 1.6*inch, 0.8*inch]))

story.append(sub("14.4 Documentos de seguridad y cumplimiento"))
sec_data = [
    ["Documento", "Responsable", "Estado"],
    ["Aviso de privacidad (LFPDPPP) publicado", "Owner", "Pendiente"],
    ["Designacion de responsable de datos personales", "Inversionista", "Pendiente"],
    ["Procedimiento de respuesta a derechos ARCO", "Owner", "Pendiente"],
    ["Plan de respuesta a incidentes de seguridad", "Owner", "Pendiente"],
    ["Procedimiento de manejo de CSDs (cifrado, rotacion)", "Owner", "Pendiente"],
    ["Politica de retencion de datos (5 anos fiscales)", "Owner + asesor SAT", "Pendiente"],
    ["Bitacora de accesos privilegiados (audit log)", "Owner (auto)", "Implementar"],
]
story.append(make_table(sec_data, col_widths=[3.6*inch, 1.6*inch, 0.8*inch]))

story.append(sub("14.5 Documento integrador: Project Charter"))
story.append(p(
    "Se entregara un <b>Project Charter</b> de 4-6 paginas que consolida en un solo lugar:"
))
story.append(b("&bull; Vision, alcance dentro y fuera, criterios de exito."))
story.append(b("&bull; Stakeholders y matriz RACI."))
story.append(b("&bull; Hitos, dependencias, criterio de aceptacion."))
story.append(b("&bull; Presupuesto aprobado y autoridad de gasto."))
story.append(b("&bull; Riesgos top 5 con plan de mitigacion."))
story.append(b("&bull; Firmas de inversionista, owner y EHMO."))
story.append(PageBreak())


# ============= 15. SIGUIENTES PASOS =============
story.append(section_title("15. Siguientes Pasos y Aprobaciones"))
story.append(hr())

story.append(sub("15.1 Decisiones que se piden hoy al inversionista"))
dec_data = [
    ["#", "Decision", "Implicacion si se aprueba"],
    ["D1", "Aprobacion del modelo de negocio (Seccion 4)", "Cierra el alcance del MVP"],
    ["D2", "Eleccion de escenario A / B / C (Seccion 9.3)", "Define presupuesto y velocidad"],
    ["D3", "Aprobacion de inversion en hardware Mac mini M4 + 100 TB", "Habilita capex inmediato (~$ 152k MXN)"],
    ["D4", "Confirmacion de EHMO como cliente operativo principal", "Habilita acceso a datos reales de EHMO"],
    ["D5", "Designacion de responsable legal del proyecto", "Avanza contratos y constitucion legal"],
    ["D6", "Acuerdo de modelo de pago al owner (Michel)", "Cierra recursos humanos"],
    ["D7", "Autorizacion para gastar en servicios mensuales", "Habilita Supabase Pro, Anthropic, etc."],
]
story.append(make_table(dec_data, col_widths=[0.4*inch, 2.6*inch, 3.0*inch]))

story.append(sub("15.2 Cronograma post-aprobacion"))
crono_data = [
    ["Dia", "Actividad"],
    ["Dia 0", "Aprobacion del documento + decisiones D1-D7"],
    ["Dia 1-3", "Compra de hardware (Mac mini + storage), setup en oficina"],
    ["Dia 4-5", "Firma de NDAs (EHMO) y contratos comerciales (servicios cloud)"],
    ["Dia 6-10", "Sprint 1.5: deploy a Supabase + Render + auth real"],
    ["Dia 11-25", "Sprint 7: inventario triple-estado + remisiones + ordenes compra"],
    ["Dia 26-35", "Sprint 8: conversiones catalogado/no-catalogado"],
    ["Dia 36-50", "Sprint 9: CxP / CxC + matching CFDI &harr; remision"],
    ["Dia 51-65", "Sprint 10: ingest multicanal con AI"],
    ["Dia 66-75", "Sprint 11-12: portal proveedor + AI lee CFDIs de correo"],
    ["Dia 76-90", "Sprint 13-15: migracion legacy + multi-bodega + sustituciones"],
    ["Dia 91-105", "Estabilizacion, capacitacion, go-live MVP en EHMO"],
    ["Dia 106-120", "Soporte intensivo, ajustes, primer cierre mensual real"],
]
story.append(make_table(crono_data, col_widths=[1.0*inch, 5.0*inch]))

story.append(sub("15.3 Forma de aprobacion"))
story.append(p("Se solicita al inversionista <b>Cristian Zarate</b> aprobar este documento mediante:"))
story.append(b("&bull; Firma fisica o electronica del Project Charter (entregable separado)."))
story.append(b("&bull; Confirmacion por correo electronico al equipo del proyecto."))
story.append(b("&bull; O reunion ejecutiva donde se valide en vivo y se firme acta."))

story.append(Spacer(1, 0.3 * inch))
story.append(hr(color=NAVY, thickness=2))
story.append(Spacer(1, 0.2 * inch))
story.append(Paragraph("FIRMAS", styles["H2"]))
story.append(Spacer(1, 0.4 * inch))

firma_data = [
    ["", "", ""],
    ["_____________________________", "_____________________________", "_____________________________"],
    ["<b>Cristian Zarate</b>", "<b>Michel Zarate</b>", "<b>Representante EHMO</b>"],
    ["Inversionista &mdash; Frutas Kelly", "Owner &mdash; Tech Lead AI", "Cliente operativo"],
    ["Fecha: ____________", "Fecha: ____________", "Fecha: ____________"],
]
firma_styled = []
for row in firma_data:
    firma_styled.append([Paragraph(c, ParagraphStyle(
        name="firma", fontName="Helvetica", fontSize=10, alignment=TA_CENTER, leading=14
    )) for c in row])
firma_tbl = Table(firma_styled, colWidths=[2.1*inch, 2.1*inch, 2.1*inch])
firma_tbl.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 4),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
]))
story.append(firma_tbl)

story.append(Spacer(1, 0.4 * inch))
story.append(hr(color=GRAY, thickness=0.5))
story.append(Paragraph(
    "<i>Este documento es propiedad intelectual del proyecto Cadena de Suministro AI y "
    "Frutas Kelly. Su distribucion fuera de los firmantes mencionados requiere "
    "autorizacion expresa del inversionista.</i>",
    ParagraphStyle(
        name="conf", fontName="Helvetica-Oblique", fontSize=8, leading=11,
        alignment=TA_CENTER, textColor=GRAY, spaceBefore=8
    )
))


# ---------- BUILD ----------
def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT_PATH),
        pagesize=letter,
        leftMargin=72,
        rightMargin=72,
        topMargin=72,
        bottomMargin=54,
        title="Propuesta Cadena de Suministro AI - Cristian Zarate",
        author="Michel Zarate / Frutas Kelly",
        subject="Propuesta de inversion ERP de cadena de suministro alimentaria",
    )
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF generado: {OUTPUT_PATH}")
    print(f"Tamano: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
