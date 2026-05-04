"""
PDF NEUTRAL para los dos co-fundadores: marco de negociacion sin tomar partido.

Tono: intermediario / mediador. Presenta opciones, trade-offs y datos objetivos
para que las partes decidan juntas.

Salida: docs/Marco_Acuerdo_CoFundadores.pdf
"""
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Table, TableStyle,
    HRFlowable
)

OUTPUT_PATH = Path(__file__).parent.parent / "docs" / "Marco_Acuerdo_CoFundadores.pdf"

# ---------- Estilos ----------
styles = getSampleStyleSheet()

NAVY = colors.HexColor("#1A2A44")
GOLD = colors.HexColor("#A67C00")
GRAY = colors.HexColor("#5C6B73")
LIGHT = colors.HexColor("#F4F1EA")
WARM = colors.HexColor("#8B5A3C")
SOFT_RED = colors.HexColor("#A93226")
SOFT_GREEN = colors.HexColor("#1E6B1E")

styles.add(ParagraphStyle(
    name="CoverTitle", fontName="Helvetica-Bold", fontSize=28, leading=34,
    alignment=TA_CENTER, textColor=NAVY, spaceAfter=10,
))
styles.add(ParagraphStyle(
    name="CoverSubtitle", fontName="Helvetica", fontSize=13, leading=17,
    alignment=TA_CENTER, textColor=GRAY, spaceAfter=20,
))
styles.add(ParagraphStyle(
    name="CoverMeta", fontName="Helvetica", fontSize=11, leading=15,
    alignment=TA_CENTER, textColor=GRAY,
))
styles.add(ParagraphStyle(
    name="H1", fontName="Helvetica-Bold", fontSize=18, leading=22,
    spaceBefore=14, spaceAfter=10, textColor=NAVY,
))
styles.add(ParagraphStyle(
    name="H2", fontName="Helvetica-Bold", fontSize=13, leading=16,
    spaceBefore=10, spaceAfter=6, textColor=NAVY,
))
styles.add(ParagraphStyle(
    name="H3", fontName="Helvetica-Bold", fontSize=11, leading=14,
    spaceBefore=6, spaceAfter=4, textColor=GOLD,
))
styles.add(ParagraphStyle(
    name="Body", fontName="Helvetica", fontSize=10, leading=14,
    alignment=TA_JUSTIFY, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="MyBullet", fontName="Helvetica", fontSize=10, leading=14,
    leftIndent=14, spaceAfter=2,
))
styles.add(ParagraphStyle(
    name="Quote", fontName="Helvetica-Oblique", fontSize=9.5, leading=13,
    leftIndent=20, rightIndent=20, textColor=GRAY,
    spaceBefore=6, spaceAfter=6,
))
styles.add(ParagraphStyle(
    name="Neutral", fontName="Helvetica-Bold", fontSize=10.5, leading=14,
    textColor=WARM, spaceBefore=6, spaceAfter=4,
))

_CELL = ParagraphStyle(
    name="Cell", fontName="Helvetica", fontSize=8.5, leading=11,
    alignment=TA_LEFT, textColor=colors.black,
)
_CELL_HDR = ParagraphStyle(
    name="CellHdr", fontName="Helvetica-Bold", fontSize=8.5, leading=11,
    alignment=TA_LEFT, textColor=colors.white,
)


def _wrap(data, header=True):
    out = []
    for r, row in enumerate(data):
        new_row = []
        for cell in row:
            if hasattr(cell, "wrap"):
                new_row.append(cell)
                continue
            text = "" if cell is None else str(cell)
            sty = _CELL_HDR if (header and r == 0) else _CELL
            new_row.append(Paragraph(text, sty))
        out.append(new_row)
    return out


def make_table(data, col_widths=None, header=True, zebra=True, header_color=NAVY):
    data = _wrap(data, header=header)
    t = Table(data, colWidths=col_widths, repeatRows=1 if header else 0)
    style = [
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("RIGHTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
    ]
    if header:
        style += [("BACKGROUND", (0, 0), (-1, 0), header_color)]
    if zebra:
        for i in range(1 if header else 0, len(data)):
            if i % 2 == (1 if header else 0):
                style.append(("BACKGROUND", (0, i), (-1, i), LIGHT))
    t.setStyle(TableStyle(style))
    return t


# ---------- Header / Footer ----------
def header_footer(canv, doc):
    canv.saveState()
    canv.setFont("Helvetica", 8)
    canv.setFillColor(GRAY)
    canv.drawString(72, 30, "Marco de Acuerdo Co-Fundadores · Documento neutral · Confidencial")
    canv.drawRightString(letter[0] - 72, 30, f"Pag. {doc.page}")
    if doc.page > 1:
        canv.setStrokeColor(GOLD)
        canv.setLineWidth(2)
        canv.line(72, letter[1] - 50, letter[0] - 72, letter[1] - 50)
        canv.setFont("Helvetica-Bold", 9)
        canv.setFillColor(NAVY)
        canv.drawString(72, letter[1] - 45, "MARCO DE ACUERDO CO-FUNDADORES")
        canv.setFont("Helvetica", 8)
        canv.setFillColor(GRAY)
        canv.drawRightString(letter[0] - 72, letter[1] - 45, "Cadena de Suministro AI")
    canv.restoreState()


# ---------- Helpers ----------
def hr(c=GOLD, t=1):
    return HRFlowable(width="100%", thickness=t, color=c, spaceBefore=4, spaceAfter=8)


def H1(text):
    return Paragraph(text, styles["H1"])


def H2(text):
    return Paragraph(text, styles["H2"])


def H3(text):
    return Paragraph(text, styles["H3"])


def p(text):
    return Paragraph(text, styles["Body"])


def b(text):
    return Paragraph(text, styles["MyBullet"])


def neutral(text):
    return Paragraph(text, styles["Neutral"])


def quote(text):
    return Paragraph(text, styles["Quote"])


# ---------- Documento ----------
story = []

# ============= COVER =============
story.append(Spacer(1, 1.2 * inch))
story.append(Paragraph("MARCO DE ACUERDO", styles["CoverTitle"]))
story.append(Paragraph("CO-FUNDADORES", styles["CoverTitle"]))
story.append(Paragraph(
    "Cadena de Suministro AI &mdash; Plataforma ERP B2B/B2G",
    styles["CoverSubtitle"]
))
story.append(Spacer(1, 0.2 * inch))
story.append(hr(c=GOLD, t=2))
story.append(Spacer(1, 0.25 * inch))
story.append(Paragraph("Documento neutral de negociacion", styles["H2"]))
story.append(Spacer(1, 0.1 * inch))
story.append(Paragraph(
    "Preparado para facilitar el acuerdo entre las partes:",
    styles["CoverMeta"]
))
story.append(Spacer(1, 0.15 * inch))
story.append(Paragraph("<b>Cristian Zarate</b>", styles["H3"]))
story.append(Paragraph("Idea, capital, cliente operativo (EHMO via Frutas Kelly)", styles["CoverMeta"]))
story.append(Spacer(1, 0.1 * inch))
story.append(Paragraph("<b>Michel Zarate</b>", styles["H3"]))
story.append(Paragraph("Ejecucion tecnica, AI, arquitectura SaaS", styles["CoverMeta"]))
story.append(Spacer(1, 0.4 * inch))
story.append(hr(c=GRAY, t=0.5))
story.append(Spacer(1, 0.15 * inch))
story.append(Paragraph(
    "<i>Este documento NO es un contrato. Es un marco de referencia que presenta "
    "opciones, trade-offs y datos objetivos para que las partes negocien y "
    "lleguen a un acuerdo formal con asesoria legal independiente.</i>",
    styles["CoverMeta"]
))
story.append(Spacer(1, 0.4 * inch))
story.append(Paragraph("Fecha: 4 de Mayo de 2026", styles["CoverMeta"]))
story.append(Paragraph("Version: 1.0 &mdash; Borrador para discusion", styles["CoverMeta"]))
story.append(PageBreak())


# ============= INDICE =============
story.append(H1("Indice"))
toc = [
    ["1.", "Proposito y alcance del documento", "3"],
    ["2.", "Resumen del proyecto y contexto", "4"],
    ["3.", "Las partes y sus aportaciones", "5"],
    ["4.", "Estimacion objetiva del esfuerzo", "7"],
    ["5.", "Modelos de compensacion de tiempo (3 opciones)", "8"],
    ["6.", "Modelos de reparto accionario (3 opciones)", "11"],
    ["7.", "Combinaciones tipicas en mercado", "14"],
    ["8.", "Vesting, cliff y proteccion de continuidad", "15"],
    ["9.", "Roles, autoridad y toma de decisiones", "16"],
    ["10.", "Estructura legal recomendable", "17"],
    ["11.", "Matriz de riesgos por parte", "18"],
    ["12.", "Clausulas estandar de proteccion mutua", "19"],
    ["13.", "Hoja de trabajo: decisiones a acordar", "20"],
    ["14.", "Proximos pasos sugeridos", "22"],
]
toc_tbl = Table(toc, colWidths=[0.4*inch, 4.6*inch, 0.6*inch])
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


# ============= 1. PROPOSITO =============
story.append(H1("1. Proposito y alcance del documento"))
story.append(hr())
story.append(p(
    "Este documento es un <b>marco neutral</b> elaborado para facilitar la negociacion "
    "entre dos co-fundadores con perfiles distintos pero complementarios para el proyecto "
    "<b>Cadena de Suministro AI</b>. Las partes son <b>Cristian Zarate</b> (idea, capital, "
    "cliente operativo) y <b>Michel Zarate</b> (ejecucion tecnica, AI, arquitectura SaaS)."
))
story.append(p(
    "El documento <b>no recomienda una opcion sobre otra</b>. En cambio, presenta:"
))
story.append(b("&bull; Datos objetivos del esfuerzo requerido (horas, plazos, costos)."))
story.append(b("&bull; Modelos validos de compensacion y reparto accionario, con sus trade-offs."))
story.append(b("&bull; Practicas estandar de mercado para sociedades tecnologicas en Mexico."))
story.append(b("&bull; Una hoja de trabajo final donde ambas partes pueden registrar sus preferencias."))

story.append(H2("Aclaraciones importantes"))
story.append(neutral("1. Este documento NO sustituye asesoria legal."))
story.append(p(
    "Antes de firmar cualquier acuerdo formal, las partes deben consultar a un abogado "
    "corporativo independiente que represente los intereses comunes de la sociedad y "
    "(idealmente) abogados separados que representen a cada parte en lo individual."
))
story.append(neutral("2. Este documento es confidencial entre las partes."))
story.append(p(
    "No debe compartirse con terceros (incluyendo EHMO, otros proveedores, o futuros "
    "inversionistas) sin consentimiento expreso de ambas partes."
))
story.append(neutral("3. Las cifras son estimaciones para discusion, no compromisos."))
story.append(p(
    "Los numeros de horas, costos y porcentajes presentados son punto de partida basado "
    "en estandares de mercado y datos del proyecto. Los acuerdos finales deben "
    "documentarse en contratos formales firmados."
))
story.append(PageBreak())


# ============= 2. RESUMEN DEL PROYECTO =============
story.append(H1("2. Resumen del proyecto y contexto"))
story.append(hr())
story.append(p(
    "<b>Cadena de Suministro AI</b> es una plataforma ERP vertical para distribuidores "
    "B2B/B2G de productos perecederos y no perecederos en Mexico. El sistema reemplaza "
    "una combinacion de sistemas dispersos (Odoo, Sicar, Excel, WhatsApp, correo) "
    "que actualmente usa <b>EHMO</b> &mdash; cliente operativo principal y socio comercial "
    "de Frutas Kelly."
))

story.append(H2("2.1 Estado actual del desarrollo (objetivo)"))
estado_data = [
    ["Indicador", "Cantidad"],
    ["Tablas en base de datos (Postgres)", "32 + alembic_version"],
    ["Endpoints REST documentados", "52"],
    ["Tests automatizados pasando", "56 / 56"],
    ["Sprints completados (1, 2, 3, 5, 6)", "5 de ~ 15"],
    ["Avance estimado del MVP", "~ 35 %"],
    ["Datos productivos migrados", "1 tenant, 110 productos, 42 pedidos, 27 unidades"],
    ["Repositorio versionado", "GitHub: frutaskelly/cadena-de-suministro-ai"],
]
story.append(make_table(estado_data, col_widths=[3.6*inch, 2.4*inch]))

story.append(H2("2.2 Objetivo del MVP a 6-9 meses"))
story.append(b("&bull; Sistema operando en EHMO produccion."))
story.append(b("&bull; Captura automatica de pedidos desde WhatsApp / correo / PDF / foto."))
story.append(b("&bull; Inventario triple-estado (fisico / remision / facturado)."))
story.append(b("&bull; Conversiones catalogado &harr; no-catalogado con merma y mezcla."))
story.append(b("&bull; CFDI bidireccional (EHMO emite + recibe de proveedores)."))
story.append(b("&bull; Cuentas por pagar y por cobrar con conciliacion automatica."))
story.append(b("&bull; Portal limitado para los ~100 proveedores."))
story.append(b("&bull; Migracion de datos historicos desde Odoo / Sicar / Excel."))

story.append(H2("2.3 Vision a 24 meses"))
story.append(p(
    "Plataforma SaaS multi-tenant que pueda escalar a otros distribuidores tipo-EHMO "
    "en Mexico. EHMO sigue siendo el primer tenant y caso de uso de referencia. "
    "Proyeccion: 5-15 tenants activos al ano 2."
))
story.append(PageBreak())


# ============= 3. LAS PARTES =============
story.append(H1("3. Las partes y sus aportaciones"))
story.append(hr())

story.append(H2("3.1 Cristian Zarate"))
cristian_data = [
    ["Categoria", "Aportacion"],
    ["Idea original", "Concepcion del producto vertical para la cadena alimentaria B2B/B2G"],
    ["Capital", "Capacidad de aportar $ 300,000 - 900,000 MXN segun modelo elegido"],
    ["Cliente operativo", "Acceso a EHMO (cliente de referencia) via Frutas Kelly"],
    ["Conocimiento de dominio", "Operacion real de proveedor (Frutas Kelly) hacia EHMO"],
    ["Tiempo dedicado", "Part-time desde su negocio principal &mdash; validacion, requerimientos, sales"],
    ["Riesgo principal", "Capital invertido (perdida total si proyecto fracasa)"],
    ["Vehiculo de ingresos paralelo", "Frutas Kelly continua operando independientemente"],
]
story.append(make_table(cristian_data, col_widths=[1.8*inch, 4.2*inch]))

story.append(H2("3.2 Michel Zarate"))
michel_data = [
    ["Categoria", "Aportacion"],
    ["Ejecucion tecnica", "Arquitectura, codigo, AI orchestration, deploy, mantenimiento"],
    ["Conocimiento especializado", "AI / LLMs aplicados, sistemas SaaS, integraciones complejas"],
    ["Capital", "No aporta capital cash"],
    ["Tiempo disponible", "Part-time &mdash; tiene empleo formal separado de tiempo completo"],
    ["IP creado", "Codigo, prompts, arquitectura, scripts, documentacion (asignado a la empresa)"],
    ["Riesgo principal", "Costo de oportunidad, conflicto con empleo, IP cedida sin garantia de upside"],
    ["Tarifa profesional declarada", "$ 40 USD/hr (estandar mercado); ofrece $ 30 USD/hr al proyecto"],
]
story.append(make_table(michel_data, col_widths=[1.8*inch, 4.2*inch]))

story.append(H2("3.3 Naturaleza complementaria"))
story.append(p(
    "Las aportaciones de las partes son <b>complementarias y dificilmente intercambiables</b>:"
))
story.append(b("&bull; Cristian no puede ejecutar el desarrollo tecnico sin contratar reemplazo costoso (~ $ 70-90k MXN/mes)."))
story.append(b("&bull; Michel no puede activar el cliente operativo (EHMO) sin la relacion comercial preexistente de Cristian."))
story.append(b("&bull; Ninguna parte puede continuar el proyecto sola: la separacion implicaria practicamente terminarlo."))
story.append(p(
    "Esta interdependencia es la razon principal por la que las practicas estandar "
    "de mercado para sociedades tecnologicas con perfiles asi suelen reflejar "
    "<b>paridad o cercana-paridad</b> en equity, ajustada por las contribuciones "
    "diferenciales de cada parte."
))
story.append(PageBreak())


# ============= 4. ESTIMACION OBJETIVA =============
story.append(H1("4. Estimacion objetiva del esfuerzo"))
story.append(hr())
story.append(p(
    "Esta seccion presenta numeros sin tomar partido. Son derivados de: (a) las horas "
    "ya invertidas en los Sprints 1-6 cerrados, (b) el alcance documentado de los "
    "Sprints 7-15 pendientes, (c) datos comparativos de proyectos similares en Mexico."
))

story.append(H2("4.1 Horas estimadas para terminar el MVP"))
horas_data = [
    ["Categoria de trabajo", "Horas estimadas", "Notas"],
    ["Desarrollo AI-asistido (Sprints 7-15)", "280 - 360", "Codigo + tests + integraciones"],
    ["Deploy y DevOps (Supabase, Render, dominio, CI/CD)", "50 - 70", "Setup productivo"],
    ["Migracion de datos legacy (Odoo, Sicar, Excel)", "60 - 100", "Variabilidad alta segun calidad de datos"],
    ["Testing con datos reales y bug fixing", "60 - 80", "Ciclos de iteracion con EHMO"],
    ["Documentacion y manuales", "30 - 50", "Auto-generada + curacion humana"],
    ["Reuniones, demos, iteracion stakeholders", "40 - 60", "Cristian + EHMO + proveedores"],
    ["Buffer para imprevistos (15-20 %)", "80 - 120", "Estandar en proyectos SaaS"],
    ["<b>TOTAL ESTIMADO</b>", "<b>500 - 800</b>", "<b>Punto medio: ~ 640 horas</b>"],
]
story.append(make_table(horas_data, col_widths=[2.6*inch, 1.4*inch, 2.0*inch]))

story.append(H2("4.2 Plazos por intensidad de dedicacion"))
plazos_data = [
    ["Horas/semana de Michel", "Semanas necesarias", "Meses", "Sostenibilidad"],
    ["12 hrs/semana (solo finde)", "53 semanas", "12 meses", "Alta &mdash; muy holgado"],
    ["16 hrs/semana", "40 semanas", "9 meses", "Alta &mdash; sostenible"],
    ["20 hrs/semana", "32 semanas", "8 meses", "Media-alta &mdash; sostenible"],
    ["25 hrs/semana", "26 semanas", "6 meses", "Media &mdash; agresivo"],
    ["30 hrs/semana", "21 semanas", "5 meses", "Baja &mdash; riesgo de burnout"],
    ["40 hrs/semana (full-time)", "16 semanas", "4 meses", "No aplica &mdash; Michel tiene otro empleo"],
]
story.append(make_table(plazos_data, col_widths=[2.0*inch, 1.4*inch, 1.0*inch, 1.6*inch]))

story.append(quote(
    "Las dos columnas extremas (12 hrs/sem y 40 hrs/sem) se incluyen como referencia "
    "pero no son recomendables: la primera retrasa el momentum comercial; la segunda "
    "no es compatible con el empleo formal de Michel."
))

story.append(H2("4.3 Costos operativos del proyecto (independientes de quien hace que)"))
costos_data = [
    ["Concepto", "Rango MXN", "Frecuencia"],
    ["Hardware Mac mini M4 + storage 100 TB + perifericos", "120,000 - 152,000", "One-time"],
    ["Hardware basico Mac mini + storage 8 TB", "55,000 - 70,000", "One-time (alternativa)"],
    ["Servicios cloud (Supabase, Render, Anthropic, GitHub)", "1,800 - 2,800 / mes", "Mensual"],
    ["Asesoria fiscal CFDI / SAT (one-shot)", "25,000 - 35,000", "One-time"],
    ["Asesoria legal constitucion + acuerdo socios", "25,000 - 40,000", "One-time"],
    ["QA humano part-time (validacion)", "20,000 - 30,000 / mes", "2-3 meses"],
    ["Migracion de datos legacy", "30,000 - 50,000", "One-time"],
    ["Capacitacion a operadores EHMO", "15,000 - 25,000", "One-time"],
    ["Reserva de contingencia (10-15 %)", "Variable", "&mdash;"],
]
story.append(make_table(costos_data, col_widths=[3.0*inch, 1.6*inch, 1.4*inch]))
story.append(PageBreak())


# ============= 5. MODELOS DE COMPENSACION =============
story.append(H1("5. Modelos de compensacion de tiempo (3 opciones)"))
story.append(hr())
story.append(p(
    "Existen tres formas validas y comunes en mercado de compensar las horas que invierte "
    "Michel. Cada modelo tiene implicaciones distintas en cash flow, riesgo, y la "
    "aportacion neta de cada parte. <b>Ningun modelo es universalmente mejor</b>: "
    "depende de la tolerancia al riesgo y el cash flow disponible."
))

story.append(p(
    "<i>Para los calculos se asume punto medio de 640 horas y tipo de cambio 20 MXN/USD.</i>"
))

# ----- MODELO COMP A -----
story.append(H2("5.1 Modelo A &mdash; Sweat equity puro (sin compensacion en efectivo)"))
story.append(p(
    "Michel no recibe pago durante el desarrollo del MVP. Su tiempo se aporta integramente "
    "como sweat equity (trabajo a cambio de participacion accionaria). Este modelo requiere "
    "que Michel tenga capacidad financiera personal para sostener 8 meses sin ingreso del "
    "proyecto."
))
modelo_a = [
    ["Concepto", "Valor"],
    ["Pago en efectivo a Michel durante MVP", "$ 0 MXN"],
    ["Tarifa implicita (mercado)", "$ 40 USD/hr"],
    ["Sweat equity acumulado de Michel", "640 hrs &times; $ 40 USD &times; 20 = <b>$ 512,000 MXN</b>"],
    ["Cash que aporta Cristian (solo costos operativos)", "<b>~ $ 350,000 MXN</b>"],
    ["Valor total proyecto", "$ 862,000 MXN"],
]
story.append(make_table(modelo_a, col_widths=[3.6*inch, 2.4*inch]))
story.append(H3("Pros desde la perspectiva de Cristian"))
story.append(b("&bull; Menor desembolso de cash al inicio (~ $ 350K vs $ 700-850K)."))
story.append(b("&bull; Mayor alineacion: Michel solo gana si el proyecto tiene exito."))
story.append(b("&bull; Si el proyecto fracasa, no hay pagos comprometidos a Michel."))
story.append(H3("Contras desde la perspectiva de Cristian"))
story.append(b("&bull; Dependencia total: si Michel se va, Cristian queda con codigo sin desarrollador."))
story.append(b("&bull; Michel puede pedir mayor equity (50+ %) para justificar el sacrificio."))
story.append(b("&bull; Si el proyecto se demora, Michel puede salir sin haber recibido nada &mdash; mayor incentivo de abandono."))
story.append(H3("Pros desde la perspectiva de Michel"))
story.append(b("&bull; Mayor equity (justificable por sacrificio cash)."))
story.append(b("&bull; Mayor upside si el proyecto escala como SaaS."))
story.append(b("&bull; No hay obligacion fiscal de emitir CFDIs durante MVP."))
story.append(H3("Contras desde la perspectiva de Michel"))
story.append(b("&bull; Cero ingreso del proyecto durante 6-9 meses."))
story.append(b("&bull; Carga total del costo de oportunidad (~ $ 512K MXN)."))
story.append(b("&bull; Si el proyecto fracasa, perdida total del tiempo invertido."))
story.append(b("&bull; Stress financiero personal &mdash; puede afectar calidad del trabajo."))
story.append(PageBreak())

# ----- MODELO COMP B -----
story.append(H2("5.2 Modelo B &mdash; Honorarios a tarifa de mercado completa"))
story.append(p(
    "Michel cobra su tarifa profesional completa de $ 40 USD/hr por todas las horas "
    "trabajadas. Funciona como contractor profesional especializado. La compensacion "
    "no se mezcla con la participacion accionaria."
))
modelo_b = [
    ["Concepto", "Valor"],
    ["Pago en efectivo a Michel durante MVP", "640 hrs &times; $ 40 USD &times; 20 = <b>$ 512,000 MXN</b>"],
    ["Tarifa", "$ 40 USD/hr (mercado)"],
    ["Sweat equity acumulado", "$ 0 MXN (no hay descuento)"],
    ["Cash que aporta Cristian (costos + honorarios)", "<b>~ $ 862,000 MXN</b>"],
    ["Valor total proyecto", "$ 862,000 MXN"],
]
story.append(make_table(modelo_b, col_widths=[3.6*inch, 2.4*inch]))
story.append(H3("Pros desde la perspectiva de Cristian"))
story.append(b("&bull; Modelo limpio: paga lo que vale en mercado, sin reclamos posteriores."))
story.append(b("&bull; Equity de Michel se justifica solo por rol founder (no por aportacion en especie)."))
story.append(b("&bull; Cristian puede argumentar mayor porcentaje de equity (todos los recursos los puso el)."))
story.append(H3("Contras desde la perspectiva de Cristian"))
story.append(b("&bull; Mayor desembolso cash inicial (~ $ 862K vs $ 350K en modelo A)."))
story.append(b("&bull; Michel puede tratar el proyecto mas como cliente que como socio (menor compromiso emocional)."))
story.append(H3("Pros desde la perspectiva de Michel"))
story.append(b("&bull; Cash flow estable durante el desarrollo &mdash; cubre costo de oportunidad."))
story.append(b("&bull; Trato profesional como en cualquier proyecto de consultoria."))
story.append(b("&bull; No esta expuesto al fracaso del proyecto (ya cobro las horas)."))
story.append(H3("Contras desde la perspectiva de Michel"))
story.append(b("&bull; Menor case para reclamar 50 % de equity (no aporto en especie)."))
story.append(b("&bull; Menor upside si el proyecto escala (probable 25-35 %)."))
story.append(b("&bull; Trato menos como co-fundador, mas como vendor."))
story.append(PageBreak())

# ----- MODELO COMP C -----
story.append(H2("5.3 Modelo C &mdash; Tarifa descontada (hibrido cash + sweat)"))
story.append(p(
    "Michel cobra $ 30 USD/hr (descuento de $ 10 USD/hr respecto a su tarifa estandar). "
    "El descuento se documenta como aportacion de capital en especie (sweat equity) que "
    "justifica una porcion de su participacion accionaria."
))
modelo_c = [
    ["Concepto", "Valor"],
    ["Tarifa cobrada al proyecto", "$ 30 USD/hr (descontada)"],
    ["Tarifa de mercado declarada", "$ 40 USD/hr"],
    ["Pago en efectivo a Michel", "640 hrs &times; $ 30 &times; 20 = <b>$ 384,000 MXN</b>"],
    ["Sweat equity acumulado de Michel", "640 hrs &times; $ 10 &times; 20 = <b>$ 128,000 MXN</b>"],
    ["Cash que aporta Cristian (costos + honorarios)", "<b>~ $ 734,000 MXN</b>"],
    ["Valor total proyecto", "$ 862,000 MXN"],
]
story.append(make_table(modelo_c, col_widths=[3.6*inch, 2.4*inch]))
story.append(H3("Pros desde la perspectiva de Cristian"))
story.append(b("&bull; Outlay cash menor que modelo B (~ $ 734K vs $ 862K)."))
story.append(b("&bull; Michel comparte algo del riesgo (descuento del 25 %)."))
story.append(b("&bull; Compromiso de Michel mayor que en modelo B (algo de skin in the game)."))
story.append(H3("Contras desde la perspectiva de Cristian"))
story.append(b("&bull; Tiene que documentar y honrar el sweat equity acumulado."))
story.append(b("&bull; Michel mantiene case para equity sustancial (35-45 %)."))
story.append(H3("Pros desde la perspectiva de Michel"))
story.append(b("&bull; Cash flow razonable durante desarrollo (~ $ 48K MXN/mes promedio)."))
story.append(b("&bull; Reconocimiento del sweat equity aportado."))
story.append(b("&bull; Balance entre seguridad financiera y upside accionario."))
story.append(H3("Contras desde la perspectiva de Michel"))
story.append(b("&bull; Sacrificio real del 25 % de su tarifa (~ $ 128K MXN sin pagar)."))
story.append(b("&bull; Requiere documentacion mas compleja (ledger de horas + sweat)."))
story.append(b("&bull; Si la empresa fracasa, pierde el descuento aportado."))

story.append(H2("5.4 Comparativa rapida de los 3 modelos"))
comp_models = [
    ["Variable", "Modelo A (sweat puro)", "Modelo B (mercado)", "Modelo C (hibrido)"],
    ["Cash a Michel durante MVP", "$ 0", "$ 512,000", "$ 384,000"],
    ["Sweat equity Michel", "$ 512,000", "$ 0", "$ 128,000"],
    ["Cash que aporta Cristian", "$ 350,000", "$ 862,000", "$ 734,000"],
    ["Riesgo financiero Michel", "Alto", "Bajo", "Medio"],
    ["Outlay cash Cristian", "Bajo", "Alto", "Medio"],
    ["Skin in the game ambos", "Michel mayor", "Cristian mayor", "Equilibrado"],
    ["Comun en mercado tech MX", "Si (early-stage)", "Si (consultor seniors)", "Si (co-founders)"],
]
story.append(make_table(comp_models, col_widths=[1.7*inch, 1.4*inch, 1.4*inch, 1.5*inch]))
story.append(PageBreak())


# ============= 6. MODELOS DE EQUITY =============
story.append(H1("6. Modelos de reparto accionario (3 opciones)"))
story.append(hr())
story.append(p(
    "El reparto de equity es independiente del modelo de compensacion en efectivo. "
    "Sin embargo, ambos estan correlacionados: cuanto mas sweat equity aporta Michel, "
    "mas case tiene para mayor porcentaje. Cuanto mas cash Cristian, mas case tiene "
    "el para mayor porcentaje. <b>Ninguna formula matematica es vinculante</b>: el "
    "reparto refleja un acuerdo de valor entre las partes."
))

# ----- EQUITY A -----
story.append(H2("6.1 Modelo Equity 1 &mdash; Paridad 50 / 50"))
eq1 = [
    ["Socio", "Equity inicial", "Equity post-cliff (12 mes)", "Equity vesting completo (36 mes)"],
    ["Cristian Zarate", "50 %", "16.7 % consolidado", "50 % consolidado"],
    ["Michel Zarate", "50 %", "16.7 % consolidado", "50 % consolidado"],
]
story.append(make_table(eq1, col_widths=[1.5*inch, 1.2*inch, 1.6*inch, 1.7*inch]))
story.append(H3("Cuando este modelo es razonable"))
story.append(b("&bull; Ambas partes consideran sus aportaciones igualmente irreemplazables."))
story.append(b("&bull; Hay alta confianza mutua y vision compartida de largo plazo."))
story.append(b("&bull; El modelo de compensacion elegido es A (sweat puro) o C (hibrido)."))
story.append(H3("Riesgo del modelo 50/50"))
story.append(p(
    "El principal riesgo es <b>parlisis decisional</b>: si las partes no estan de acuerdo "
    "en una decision critica, no hay tie-breaker. Mitigacion: asignar reas de autoridad "
    "individuales claras (seccion 9), definir mecanismo de resolucion (mediacion &rarr; arbitraje)."
))

# ----- EQUITY B -----
story.append(H2("6.2 Modelo Equity 2 &mdash; 60 / 40 (favor capital)"))
eq2 = [
    ["Socio", "Equity inicial", "Equity post-cliff", "Equity vesting completo"],
    ["Cristian Zarate", "60 %", "20 % consolidado", "60 % consolidado"],
    ["Michel Zarate", "40 %", "13.3 % consolidado", "40 % consolidado"],
]
story.append(make_table(eq2, col_widths=[1.5*inch, 1.2*inch, 1.6*inch, 1.7*inch]))
story.append(H3("Cuando este modelo es razonable"))
story.append(b("&bull; Cristian aporta capital significativo (modelo de compensacion B)."))
story.append(b("&bull; Cristian aporta acceso a customer (EHMO) ademas del capital."))
story.append(b("&bull; Las partes valoran que un socio tenga voto de mayoria para evitar parlisis."))
story.append(H3("Implicacion practica"))
story.append(p(
    "Cristian tiene mayoria simple. Decisiones cotidianas las puede tomar el (con consulta "
    "a Michel para temas tecnicos). Decisiones extraordinarias (venta, fundraising, salida "
    "de socio, cambio de objeto social) tipicamente requieren mayoria calificada de 75 %, "
    "lo que si requiere acuerdo mutuo."
))

# ----- EQUITY C -----
story.append(H2("6.3 Modelo Equity 3 &mdash; 70 / 30 con earn-back por hitos"))
eq3 = [
    ["Hito", "Cristian", "Michel"],
    ["Constitucion", "70 %", "30 %"],
    ["Entrega del MVP a EHMO produccion", "65 %", "35 %"],
    ["Primer tenant SaaS post-EHMO firmado", "60 %", "40 %"],
    ["Break-even operativo (mes 18-24)", "55 %", "45 %"],
    ["Sin mas earn-backs", "55 %", "45 %"],
]
story.append(make_table(eq3, col_widths=[3.0*inch, 1.5*inch, 1.5*inch]))
story.append(H3("Cuando este modelo es razonable"))
story.append(b("&bull; Cristian quiere proteger su inversion fuerte hasta validar viabilidad."))
story.append(b("&bull; Michel acepta condicionar parte de su equity a desempeno demostrable."))
story.append(b("&bull; Las partes confian en que Michel ejecutara los hitos."))
story.append(H3("Trade-offs"))
story.append(p(
    "Pros: alinea incentivos a largo plazo, protege capital. Contras: crea posibles "
    "tensiones cuando llegue el momento del earn-back (\"se cumplio el hito o no?\"). "
    "Requiere definicion muy precisa de cada hito en el contrato."
))
story.append(PageBreak())


# ============= 7. COMBINACIONES TIPICAS =============
story.append(H1("7. Combinaciones tipicas en mercado"))
story.append(hr())
story.append(p(
    "La compensacion (Modelo A/B/C) y el equity (Modelo 1/2/3) se combinan. La siguiente "
    "matriz muestra que combinaciones son <b>comunes en sociedades tecnologicas en Mexico</b> "
    "para perfiles similares (un socio capital + un socio tecnico)."
))

combo_data = [
    ["", "Modelo A: Sweat puro", "Modelo B: Honorarios mercado", "Modelo C: Hibrido descontado"],
    [
        "Equity 1: 50/50",
        "<b>COMUN</b><br/>Caso: ambos arriesgan parejo, cero compensacion ambos",
        "Atipico<br/>Caso: Cristian paga 100 % cash y aun cede 50 % equity &mdash; raro",
        "<b>COMUN</b><br/>Caso: el modelo balanceado mas usado",
    ],
    [
        "Equity 2: 60/40",
        "Posible<br/>Cristian quiere mayoria aunque Michel no cobre",
        "<b>COMUN</b><br/>Cristian paga todo y mantiene mayoria",
        "<b>COMUN</b><br/>Equilibrio cash + equity con ligera mayoria capital",
    ],
    [
        "Equity 3: 70/30 + earn-back",
        "Atipico<br/>Doble desventaja para Michel",
        "Posible<br/>Cash full pero menor equity inicial",
        "Posible<br/>Si las partes priorizan validacion antes de paridad",
    ],
]
combo_styled = []
for row in combo_data:
    combo_styled.append([Paragraph(c.replace("<br/>", "<br/>"), _CELL) for c in row])
combo_tbl = Table(
    combo_styled,
    colWidths=[1.4*inch, 1.6*inch, 1.6*inch, 1.6*inch],
    repeatRows=1,
)
combo_tbl.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("BACKGROUND", (0, 0), (-1, 0), NAVY),
    ("BACKGROUND", (0, 0), (0, -1), NAVY),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("TEXTCOLOR", (0, 1), (0, -1), colors.white),
    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
    ("FONTNAME", (0, 1), (0, -1), "Helvetica-Bold"),
    ("FONTSIZE", (0, 0), (-1, -1), 8.5),
    ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#CCCCCC")),
]))
# fix header text color (since header is row 0 col 0+; column 0 is also styled as header)
story.append(combo_tbl)

story.append(quote(
    "<b>Las celdas marcadas como COMUN</b> son las combinaciones que con mayor "
    "frecuencia se ven firmadas en sociedades tecnologicas mexicanas. No son "
    "recomendaciones &mdash; son observaciones de mercado."
))

story.append(H2("7.1 Tres combinaciones validas que las partes pueden considerar"))
combinaciones_validas = [
    ["Combinacion", "Descripcion", "Cash Cristian", "Equity Michel"],
    [
        "Comp A + Equity 1",
        "Sweat puro + 50/50: ambos arriesgan parejo, sin cash a Michel",
        "$ 350,000",
        "50 %",
    ],
    [
        "Comp B + Equity 2",
        "Honorarios completos + 60/40: trato profesional + mayoria capital",
        "$ 862,000",
        "40 %",
    ],
    [
        "Comp C + Equity 1",
        "Hibrido descontado + 50/50: balance riesgo y compromiso",
        "$ 734,000",
        "50 %",
    ],
]
story.append(make_table(combinaciones_validas, col_widths=[1.5*inch, 2.5*inch, 1.0*inch, 1.0*inch]))
story.append(p(
    "<i>Estas tres no agotan las opciones &mdash; son ejemplos balanceados. Las partes pueden "
    "construir cualquier otra combinacion que les acomode.</i>"
))
story.append(PageBreak())


# ============= 8. VESTING =============
story.append(H1("8. Vesting, cliff y proteccion de continuidad"))
story.append(hr())
story.append(p(
    "Independiente del modelo elegido, las practicas estandar de mercado para sociedades "
    "tecnologicas incluyen mecanismos de vesting y cliff. Estos protegen a ambas partes "
    "del riesgo de salida temprana."
))

story.append(H2("8.1 Estandar de mercado"))
vesting_data = [
    ["Concepto", "Estandar de mercado", "Funcion"],
    ["Periodo de vesting", "36 - 48 meses", "Tiempo en que el equity se consolida"],
    ["Cliff inicial", "12 meses", "Si alguien sale antes, no se lleva nada"],
    ["Vesting mensual post-cliff", "1 / 36 cada mes", "Acumulacion gradual"],
    ["Aceleracion en cambio de control", "50 - 100 % single trigger", "Si la empresa se vende, el vesting se acelera"],
    ["Aceleracion en muerte / discapacidad", "100 %", "Vesting se completa a herederos"],
]
story.append(make_table(vesting_data, col_widths=[1.8*inch, 1.7*inch, 2.5*inch]))

story.append(H2("8.2 Por que el cliff de 12 meses protege a ambos"))
story.append(neutral("Protege a Cristian:"))
story.append(b("&bull; Si Michel se va al mes 6, no se lleva equity &mdash; Cristian queda con codigo y empresa intacta."))
story.append(b("&bull; Si la quimica entre socios no funciona, hay 12 meses de validacion antes de comprometer equity."))
story.append(neutral("Protege a Michel:"))
story.append(b("&bull; Si Cristian decide cancelar el proyecto antes del mes 12, Michel tiene derecho a renegociar terminos."))
story.append(b("&bull; Cristian no puede \"diluir\" sin el consentimiento de Michel durante este periodo."))

story.append(H2("8.3 Escenarios de salida temprana (todos a 36 meses de vesting)"))
salida_data = [
    ["Mes de salida", "Equity vested Michel", "Equity vested Cristian", "Notas"],
    ["Mes 6 (pre-cliff)", "0 %", "0 %", "Si alguien sale, queda en pool sin asignar"],
    ["Mes 12 (cliff)", "16.7 %", "16.7 %", "Primera ventana de consolidacion"],
    ["Mes 18", "25 %", "25 %", "Vesting acelerado en venta"],
    ["Mes 24", "33.3 %", "33.3 %", ""],
    ["Mes 30", "41.7 %", "41.7 %", ""],
    ["Mes 36", "50 % (consolidado)", "50 % (consolidado)", "Vesting completo en modelo 50/50"],
]
story.append(make_table(salida_data, col_widths=[1.3*inch, 1.4*inch, 1.4*inch, 1.9*inch]))
story.append(PageBreak())


# ============= 9. ROLES =============
story.append(H1("9. Roles, autoridad y toma de decisiones"))
story.append(hr())
story.append(p(
    "Aun en una sociedad 50/50, es importante delimitar areas de autoridad individual "
    "para agilizar decisiones y evitar parlisis. Las decisiones criticas se reservan al "
    "consenso de ambas partes."
))

story.append(H2("9.1 Distribucion sugerida de autoridad"))
roles_data = [
    ["Tipo de decision", "Quien decide", "Quien consulta"],
    ["Vision de producto y prioridades", "Conjunta", "&mdash;"],
    ["Requerimientos funcionales y validacion con cliente", "Cristian", "Informa a Michel"],
    ["Arquitectura tecnica y stack", "Michel", "Informa a Cristian"],
    ["Pricing comercial al cliente", "Cristian", "Consulta con Michel"],
    ["Eleccion de proveedores tecnologicos", "Michel", "Informa a Cristian"],
    ["Hiring de personal externo", "Conjunta", "&mdash;"],
    ["Inversion adicional de capital", "Conjunta", "&mdash;"],
    ["Fundraising externo", "Conjunta", "Asesoria legal"],
    ["Salida de socio", "Conjunta", "Asesoria legal"],
    ["Venta de la empresa", "Conjunta (mayoria 75 %)", "Asesoria legal"],
    ["Cambio de objeto social", "Conjunta (mayoria 75 %)", "Asesoria legal"],
    ["Aprobacion de gastos > $ 50,000 MXN", "Conjunta", "&mdash;"],
    ["Aprobacion de gastos < $ 50,000 MXN", "Cualquiera con notificacion", "&mdash;"],
]
story.append(make_table(roles_data, col_widths=[3.0*inch, 1.6*inch, 1.4*inch]))

story.append(H2("9.2 Mecanismo de resolucion de disputas"))
story.append(p(
    "En caso de desacuerdo en una decision conjunta, se sugiere el siguiente protocolo:"
))
story.append(b("&bull; <b>Paso 1:</b> Discusion directa con periodo de enfriamiento de 7 dias."))
story.append(b("&bull; <b>Paso 2:</b> Mediacion con un tercero neutral (asesor de confianza, mentor, abogado mediador)."))
story.append(b("&bull; <b>Paso 3:</b> Arbitraje vinculante (si es comercial) o disolucion (si es estructural)."))
story.append(b("&bull; <b>Buy-sell:</b> en caso de desacuerdo irreconciliable, una parte puede ofrecer comprar a la otra a un precio; la otra parte tiene 30 dias para aceptar el precio o invertir los roles (compra ella al mismo precio)."))
story.append(PageBreak())


# ============= 10. ESTRUCTURA LEGAL =============
story.append(H1("10. Estructura legal recomendable"))
story.append(hr())

story.append(H2("10.1 Tipo de sociedad sugerido"))
story.append(p(
    "Para sociedades tecnologicas con 2 fundadores en Mexico, la <b>S.A.S. de C.V.</b> "
    "(Sociedad por Acciones Simplificada de Capital Variable) es generalmente la opcion "
    "mas eficiente:"
))
sas_data = [
    ["Caracteristica", "S.A.S. de C.V.", "S.A. de C.V.", "S.C. Civil"],
    ["Constitucion", "Online en gob.mx (gratis)", "Notario (~$15K MXN)", "Notario (~$10K MXN)"],
    ["Tiempo de constitucion", "1-2 dias", "2-4 semanas", "1-2 semanas"],
    ["Numero minimo de socios", "1 (puede ser unico)", "2", "2"],
    ["Capital minimo", "$1 MXN simbolico", "$50,000 MXN", "Variable"],
    ["Limita responsabilidad", "Si", "Si", "No (excepto comanditados)"],
    ["Permite acciones", "Si", "Si", "No (cuotas)"],
    ["Flexibilidad de gobierno", "Alta", "Media", "Baja"],
    ["Migrable a S.A.P.I. para fundraising", "Si", "Si", "No"],
    ["<b>Recomendable para SaaS</b>", "<b>Si</b>", "Si", "No"],
]
story.append(make_table(sas_data, col_widths=[2.0*inch, 1.4*inch, 1.4*inch, 1.2*inch]))

story.append(H2("10.2 Documentos legales minimos a firmar"))
docs_data = [
    ["Documento", "Proposito", "Costo aprox MXN", "Plazo"],
    ["Acta constitutiva S.A.S. de C.V.", "Crea la entidad legal", "$ 0 - 5,000", "1-2 dias"],
    ["Acuerdo de Socios (Founders Agreement)", "Formaliza equity, vesting, IP, salida", "$ 15,000 - 25,000", "1-2 semanas"],
    ["Contrato de aportacion de capital", "Cristian aporta cash", "Incluido en anterior", "&mdash;"],
    ["Contrato de prestacion de servicios", "Michel factura horas", "$ 3,000 - 5,000", "1 semana"],
    ["IP Assignment Agreement", "Codigo y prompts a la empresa", "Incluido en Founders", "&mdash;"],
    ["Aviso de privacidad LFPDPPP", "Cumplimiento de datos personales", "$ 5,000", "1 semana"],
    ["Politica de seguridad de informacion", "Cumplimiento ISO/SAT", "$ 3,000", "1 semana"],
    ["<b>TOTAL costos legales aprox</b>", "", "<b>$ 26,000 - 43,000</b>", "<b>3-5 semanas</b>"],
]
story.append(make_table(docs_data, col_widths=[2.2*inch, 1.7*inch, 1.2*inch, 0.9*inch]))
story.append(PageBreak())


# ============= 11. RIESGOS POR PARTE =============
story.append(H1("11. Matriz de riesgos por parte"))
story.append(hr())
story.append(p(
    "Cada parte enfrenta riesgos diferentes. Esta matriz documenta ambos lados y propone "
    "mitigaciones simetricas."
))

story.append(H2("11.1 Riesgos para Cristian (capital)"))
risk_c = [
    ["Riesgo", "Probabilidad", "Impacto", "Mitigacion"],
    [
        "Michel sale antes del MVP",
        "Baja-Media",
        "Alto",
        "Cliff 12 meses + IP assignment desde dia 1 + documentacion exhaustiva",
    ],
    [
        "Codigo dependiente del estilo de Michel",
        "Media",
        "Medio",
        "Documentacion auto-generada + tests + revision codigo por tercero ocasional",
    ],
    [
        "EHMO no adopta el sistema",
        "Baja-Media",
        "Alto",
        "Validacion temprana con usuarios EHMO + capacitacion presencial",
    ],
    [
        "Capital invertido se pierde por proyecto fallido",
        "Media",
        "Alto",
        "Hardware reusable; codigo IP de la empresa puede venderse o licenciarse",
    ],
    [
        "Conflicto de interes Frutas Kelly &harr; EHMO",
        "Baja",
        "Medio",
        "Frutas Kelly facturando a la empresa por su rol de cliente, no de socio",
    ],
]
story.append(make_table(risk_c, col_widths=[1.8*inch, 0.9*inch, 0.7*inch, 2.6*inch]))

story.append(H2("11.2 Riesgos para Michel (tiempo y reputacion)"))
risk_m = [
    ["Riesgo", "Probabilidad", "Impacto", "Mitigacion"],
    [
        "Cristian decide cancelar el proyecto",
        "Baja-Media",
        "Alto",
        "Clausula de pago por horas pendientes + 2 meses de buyout",
    ],
    [
        "Conflicto con empleo formal (cláusulas de moonlighting / IP)",
        "Media",
        "Alto",
        "Revisar contrato laboral antes de firmar; obtener autorizacion escrita si aplica",
    ],
    [
        "Burnout por exceso de horas",
        "Media",
        "Medio",
        "Tope contractual de 100 hrs/mes + ritmo sostenible 18-22 hrs/sem",
    ],
    [
        "Sweat equity diluido por inversionistas externos",
        "Media-Alta",
        "Medio",
        "Clausula anti-dilucion para fundadores en primera ronda",
    ],
    [
        "Cristian contrata reemplazo paralelo sin notificar",
        "Baja",
        "Alto",
        "Right of refusal en hiring tecnico; aceleracion de equity si ocurre",
    ],
    [
        "IP que crea pertenece a la empresa, no a el",
        "Cierta (por diseño)",
        "Bajo (esperado)",
        "Equity es la compensacion; vesting protege el reclamo a largo plazo",
    ],
]
story.append(make_table(risk_m, col_widths=[1.8*inch, 0.9*inch, 0.7*inch, 2.6*inch]))
story.append(PageBreak())


# ============= 12. CLAUSULAS ESTANDAR =============
story.append(H1("12. Clausulas estandar de proteccion mutua"))
story.append(hr())
story.append(p(
    "Las siguientes clausulas son estandar en sociedades tecnologicas y benefician a "
    "ambas partes simultaneamente. Se sugiere incluirlas en el Acuerdo de Socios."
))

clausulas_data = [
    ["#", "Clausula", "Que protege"],
    ["1", "Vesting 36 meses + cliff 12", "Que ambos completen el periodo critico"],
    ["2", "IP Assignment desde dia 1", "Que el codigo sea de la empresa, no personal"],
    ["3", "Confidencialidad mutua perpetua", "Que ambos protejan la informacion sensible"],
    ["4", "No-compete limitado para Cristian", "Que no construya un competidor identico"],
    ["5", "Right of First Refusal en venta de acciones", "Si uno vende, el otro tiene preferencia de compra"],
    ["6", "Drag-along en venta de empresa", "Mayoria puede arrastrar a minoria en venta"],
    ["7", "Tag-along en venta de acciones", "Minoria puede sumarse a venta de mayoria"],
    ["8", "Buy-sell en disputa irreconciliable", "Mecanismo de salida con valuacion justa"],
    ["9", "Aceleracion en cambio de control", "Vesting se acelera si se vende la empresa"],
    ["10", "Aceleracion en muerte / discapacidad", "Vesting se completa a herederos"],
    ["11", "Politica de gastos con limite por socio", "Evita decisiones unilaterales costosas"],
    ["12", "Reportes financieros mensuales transparentes", "Ambos ven la salud de la empresa"],
    ["13", "Reuniones formales registradas en minutas", "Decisiones documentadas"],
    ["14", "Mecanismo de resolucion de disputas en 3 pasos", "Escalado: dialogo &rarr; mediacion &rarr; arbitraje"],
    ["15", "Clausula de no-replazo no-pagado de socio tecnico", "Cristian no puede contratar reemplazo de Michel sin OK"],
    ["16", "Clausula de pago no rescindible al socio tecnico", "Si Cristian cancela, Michel cobra horas pendientes + buyout"],
]
story.append(make_table(clausulas_data, col_widths=[0.4*inch, 2.6*inch, 3.0*inch]))
story.append(PageBreak())


# ============= 13. HOJA DE TRABAJO =============
story.append(H1("13. Hoja de trabajo: decisiones a acordar"))
story.append(hr())
story.append(p(
    "Esta seccion contiene una <b>hoja de trabajo</b> que las partes pueden completar "
    "por separado y luego comparar. Es una herramienta de negociacion, no un compromiso. "
    "Sirve para identificar donde hay acuerdo natural y donde hay que negociar."
))
story.append(quote(
    "Cada parte llena su columna por separado, sin ver la del otro. Despues comparan. "
    "Las celdas donde coinciden son acuerdos naturales; las que difieren son los puntos "
    "a negociar."
))

# Worksheet items
worksheet_data = [
    ["Decision", "Preferencia Cristian", "Preferencia Michel"],
    ["1. Modelo de compensacion (A / B / C)", "_______________", "_______________"],
    ["2. Modelo de equity (1 / 2 / 3)", "_______________", "_______________"],
    ["3. Plazo objetivo del MVP (4-9 meses)", "_______________", "_______________"],
    ["4. Horas/semana objetivo de Michel (12-25)", "_______________", "_______________"],
    ["5. Cash a aportar por Cristian (rango MXN)", "_______________", "_______________"],
    ["6. Tarifa hora a Michel (USD/hr)", "_______________", "_______________"],
    ["7. Hardware: completo Mac M4 + 100 TB / basico", "_______________", "_______________"],
    ["8. Vesting: 36 / 48 meses", "_______________", "_______________"],
    ["9. Cliff: 6 / 12 / 18 meses", "_______________", "_______________"],
    ["10. Tipo de sociedad (S.A.S. / S.A.)", "_______________", "_______________"],
    ["11. Reembolso prioritario a Cristian si / no", "_______________", "_______________"],
    ["12. Pool de incentivos para futuras contrataciones (% reservado)", "_______________", "_______________"],
    ["13. Tope de horas mensuales para Michel", "_______________", "_______________"],
    ["14. Pago a Michel: semanal / quincenal / mensual", "_______________", "_______________"],
    ["15. Quien lleva la administracion legal y fiscal de la empresa", "_______________", "_______________"],
    ["16. Frecuencia de reuniones formales", "_______________", "_______________"],
    ["17. Fecha objetivo de constitucion de la sociedad", "_______________", "_______________"],
    ["18. Asesor legal independiente (nombre / firma)", "_______________", "_______________"],
    ["19. Asesor fiscal CFDI / SAT", "_______________", "_______________"],
    ["20. Frecuencia de revision de este acuerdo (anual / semestral)", "_______________", "_______________"],
]
story.append(make_table(worksheet_data, col_widths=[3.2*inch, 1.4*inch, 1.4*inch]))
story.append(PageBreak())

story.append(H2("13.1 Items abiertos para discusion (preguntas guia)"))
story.append(p("Las siguientes preguntas no tienen respuesta correcta &mdash; ayudan a las partes a alinearse antes de redactar el contrato:"))
story.append(b("&bull; <b>Vision de salida:</b> Es esto un negocio para vender a 5 anos, o construir un cash-cow indefinido?"))
story.append(b("&bull; <b>Cliente concentrado:</b> Que pasa si EHMO se va? Es viable el SaaS multi-tenant sin EHMO?"))
story.append(b("&bull; <b>Frutas Kelly como cliente:</b> Frutas Kelly seguira siendo proveedor en el sistema, pagando subscription como otros?"))
story.append(b("&bull; <b>Conflicto de interes:</b> Si Cristian quiere usar el sistema solo para su empresa y no escalarlo, como se compensa a Michel?"))
story.append(b("&bull; <b>Ownership de la marca:</b> Quien es dueño de \"Cadena de Suministro AI\" como marca registrable?"))
story.append(b("&bull; <b>Reinversion de utilidades:</b> Cuanto reinvierte la empresa vs distribuir a socios?"))
story.append(b("&bull; <b>Sueldo a futuro:</b> Cuando los socios empiezan a cobrar sueldo (cuando la empresa pueda)?"))
story.append(b("&bull; <b>Plan B si Michel cambia de empleo:</b> Si Michel deja su empleo formal, sube a 100 % en este proyecto? Cambio de equity?"))
story.append(b("&bull; <b>Plan B si Cristian sale de Frutas Kelly:</b> Mantiene su rol como inversionista o se convierte en operador?"))
story.append(PageBreak())


# ============= 14. PROXIMOS PASOS =============
story.append(H1("14. Proximos pasos sugeridos"))
story.append(hr())

steps_data = [
    ["#", "Paso", "Plazo", "Responsable"],
    ["1", "Cada parte lee este documento individualmente", "1 semana", "Ambos"],
    ["2", "Cada parte llena la hoja de trabajo (seccion 13) por separado", "1 semana", "Ambos"],
    ["3", "Reunion conjunta para comparar hojas de trabajo y negociar items", "1 dia (3-4 hrs)", "Ambos"],
    ["4", "Michel verifica con su empleador si hay restriccion de moonlighting / IP", "1 semana", "Michel"],
    ["5", "Identificar y contactar abogado corporativo para Acuerdo de Socios", "1-2 semanas", "Cristian"],
    ["6", "Sesion con abogado para redactar borrador de Acuerdo de Socios", "1-2 semanas", "Ambos + abogado"],
    ["7", "Revision del borrador por cada parte (idealmente con abogado independiente)", "1-2 semanas", "Ambos"],
    ["8", "Firma del Acuerdo de Socios + Constitucion de S.A.S. de C.V.", "1 semana", "Ambos"],
    ["9", "Apertura de cuenta bancaria empresa + aportacion de capital de Cristian", "1 semana", "Cristian"],
    ["10", "Reanudar desarrollo formalmente bajo el nuevo marco (Sprint 1.5)", "Continuo", "Michel"],
]
story.append(make_table(steps_data, col_widths=[0.4*inch, 3.4*inch, 1.0*inch, 1.2*inch]))

story.append(quote(
    "Tiempo total estimado del proceso: 6 a 10 semanas desde leer este documento hasta "
    "tener la sociedad constituida y el desarrollo continuando bajo marco formal."
))

story.append(H2("14.1 Que NO hacer"))
story.append(b("&bull; <b>No firmar el contrato sin asesoria legal independiente.</b> Esto NO es opcional &mdash; es la unica manera de proteger a ambas partes."))
story.append(b("&bull; No basar el acuerdo en \"confianza personal\" sin documentar. Las relaciones se mueven; los documentos quedan."))
story.append(b("&bull; No empezar el desarrollo formal post-MVP sin acuerdo firmado. Cualquier hora que Michel ponga sin contrato sigue las reglas no acordadas."))
story.append(b("&bull; No mostrar este documento a EHMO, proveedores o terceros. Es interno entre socios."))
story.append(b("&bull; No tomar la primera decision como definitiva. Es un borrador para iterar."))

story.append(H2("14.2 Recursos sugeridos"))
recursos_data = [
    ["Recurso", "Para que sirve"],
    ["Asesor legal corporativo (independiente)", "Redactar Acuerdo de Socios y constituir empresa"],
    ["Asesor fiscal especializado en SaaS / honorarios", "Estructura tributaria de honorarios y dividendos"],
    ["Plataforma para tracking de horas (Toggl, Clockify)", "Documentar horas de Michel"],
    ["Software de minutas (Notion, Coda, Google Docs)", "Documentar decisiones y reuniones"],
    ["Plataforma de governance (Carta, Pulley)", "Cap table, vesting, opciones"],
    ["Plantilla de Founders Agreement (Y Combinator SAFE, Ironclad)", "Punto de partida para abogado"],
]
story.append(make_table(recursos_data, col_widths=[2.6*inch, 3.4*inch]))

story.append(Spacer(1, 0.3 * inch))
story.append(hr(c=NAVY, t=2))
story.append(Spacer(1, 0.2 * inch))
story.append(Paragraph("ACUSE DE LECTURA", styles["H2"]))
story.append(Spacer(1, 0.2 * inch))
story.append(p(
    "Las partes acusan haber leido este Marco de Acuerdo Co-Fundadores en su totalidad y "
    "se comprometen a participar de buena fe en el proceso de negociacion descrito en la "
    "seccion 14. <b>Esta firma NO constituye obligacion legal de firmar un Acuerdo de "
    "Socios &mdash; es solo confirmacion de lectura del marco neutral.</b>"
))
story.append(Spacer(1, 0.4 * inch))

firma_data = [
    ["", ""],
    ["______________________________", "______________________________"],
    ["<b>Cristian Zarate</b>", "<b>Michel Zarate</b>"],
    ["Co-fundador (capital + cliente)", "Co-fundador (tecnico)"],
    ["Fecha: ____________", "Fecha: ____________"],
]
firma_styled = []
for row in firma_data:
    firma_styled.append([Paragraph(c, ParagraphStyle(
        name="firma", fontName="Helvetica", fontSize=10, alignment=TA_CENTER, leading=14
    )) for c in row])
firma_tbl = Table(firma_styled, colWidths=[3.0*inch, 3.0*inch])
firma_tbl.setStyle(TableStyle([
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(firma_tbl)

story.append(Spacer(1, 0.4 * inch))
story.append(hr(c=GRAY, t=0.5))
story.append(Paragraph(
    "<i>Documento neutral preparado como insumo para negociacion entre las partes. "
    "No representa la opinion legal o financiera de ningun tercero. La firma del Acuerdo "
    "de Socios definitivo requiere asesoria legal independiente para cada parte.</i>",
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
        leftMargin=72, rightMargin=72,
        topMargin=72, bottomMargin=54,
        title="Marco de Acuerdo Co-Fundadores - Cadena de Suministro AI",
        author="Documento neutral preparado para Cristian + Michel Zarate",
        subject="Marco de negociacion para sociedad tecnologica",
    )
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)
    print(f"PDF generado: {OUTPUT_PATH}")
    print(f"Tamano: {OUTPUT_PATH.stat().st_size / 1024:.1f} KB")


if __name__ == "__main__":
    main()
