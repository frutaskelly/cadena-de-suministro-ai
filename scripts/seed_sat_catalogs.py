"""Seed catálogos SAT para CFDI 4.0.

Carga subsets útiles de los catálogos SAT a las tablas sat_*. Los catálogos
completos son enormes (c_ClaveProdServ tiene >50k filas); este script siembra
solo lo necesario para Frutas Kelly:

- formas_pago: las 10 más comunes (01-99) — desde MetodosPago.ini del legacy
- metodos_pago: PUE + PPD
- regimenes: 12 más comunes (601, 603, 605, 606, 608, 612, 614, 616, 621, 624, 625, 626)
- usos_cfdi: G01-G03, I01-I08, S01, CN01, D01-D10, P01
- unidades: KGM, H87, XBX, XPK, MTR, MT, BG, CMT, KMK, LTR, MGM
- productos_servicios: 50202301 (FyV genérico) + neighbors usados en sector

Para el catálogo completo de claves de producto/servicio (cuando vayamos a prod):
    https://www.sat.gob.mx/personas/resultado-busqueda?locale=1462228413195&tipobusqueda=predefinida&words=cat%C3%A1logos+catalogos

Ejecutar:
    cd backend && source venv/bin/activate
    python ../scripts/seed_sat_catalogs.py

Idempotente.
"""
import configparser
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
BACKEND = HERE.parent / "backend"
sys.path.insert(0, str(BACKEND))

from app.core.db import SessionLocal
from app.models import (
    SatFormaPago, SatMetodoPago, SatRegimenFiscal, SatUsoCfdi,
    SatUnidad, SatProductoServicio,
)

KELLY_SAAS_CONFIG = (
    HERE.parent.parent / "kelly_saas" / "docs" / "config"
)

# ─── MÉTODOS DE PAGO (CFDI 4.0: PUE / PPD) ─────────────────────────────────
METODOS_PAGO = [
    ("PUE", "Pago en una sola exhibición"),
    ("PPD", "Pago en parcialidades o diferido"),
]

# ─── RÉGIMENES FISCALES (subset CFDI 4.0) ──────────────────────────────────
# (clave, descripcion, aplica_fisica, aplica_moral)
REGIMENES = [
    ("601", "General de Ley Personas Morales", "No", "Sí"),
    ("603", "Personas Morales con Fines no Lucrativos", "No", "Sí"),
    ("605", "Sueldos y Salarios e Ingresos Asimilados a Salarios", "Sí", "No"),
    ("606", "Arrendamiento", "Sí", "No"),
    ("608", "Demás ingresos", "Sí", "No"),
    ("610", "Residentes en el Extranjero sin Establecimiento Permanente", "Sí", "Sí"),
    ("611", "Ingresos por Dividendos (socios y accionistas)", "Sí", "No"),
    ("612", "Personas Físicas con Actividades Empresariales y Profesionales", "Sí", "No"),
    ("614", "Ingresos por intereses", "Sí", "No"),
    ("615", "Régimen de los ingresos por obtención de premios", "Sí", "No"),
    ("616", "Sin obligaciones fiscales", "Sí", "No"),
    ("620", "Sociedades Cooperativas de Producción que optan por diferir sus ingresos", "No", "Sí"),
    ("621", "Incorporación Fiscal", "Sí", "No"),
    ("622", "Actividades Agrícolas, Ganaderas, Silvícolas y Pesqueras", "No", "Sí"),
    ("623", "Opcional para Grupos de Sociedades", "No", "Sí"),
    ("624", "Coordinados", "No", "Sí"),
    ("625", "Régimen de las Actividades Empresariales con ingresos a través de Plataformas Tecnológicas", "Sí", "No"),
    ("626", "Régimen Simplificado de Confianza", "Sí", "Sí"),
]

# ─── USOS DE CFDI (subset CFDI 4.0) ─────────────────────────────────────────
USOS_CFDI = [
    ("G01", "Adquisición de mercancías.", "Sí", "Sí"),
    ("G02", "Devoluciones, descuentos o bonificaciones.", "Sí", "Sí"),
    ("G03", "Gastos en general.", "Sí", "Sí"),
    ("I01", "Construcciones.", "Sí", "Sí"),
    ("I02", "Mobiliario y equipo de oficina por inversiones.", "Sí", "Sí"),
    ("I03", "Equipo de transporte.", "Sí", "Sí"),
    ("I04", "Equipo de cómputo y accesorios.", "Sí", "Sí"),
    ("I05", "Dados, troqueles, moldes, matrices y herramental.", "Sí", "Sí"),
    ("I06", "Comunicaciones telefónicas.", "Sí", "Sí"),
    ("I07", "Comunicaciones satelitales.", "Sí", "Sí"),
    ("I08", "Otra maquinaria y equipo.", "Sí", "Sí"),
    ("D01", "Honorarios médicos, dentales y gastos hospitalarios.", "Sí", "No"),
    ("D02", "Gastos médicos por incapacidad o discapacidad.", "Sí", "No"),
    ("D03", "Gastos funerales.", "Sí", "No"),
    ("D04", "Donativos.", "Sí", "No"),
    ("D05", "Intereses reales efectivamente pagados por créditos hipotecarios (casa habitación).", "Sí", "No"),
    ("D06", "Aportaciones voluntarias al SAR.", "Sí", "No"),
    ("D07", "Primas por seguros de gastos médicos.", "Sí", "No"),
    ("D08", "Gastos de transportación escolar obligatoria.", "Sí", "No"),
    ("D09", "Depósitos en cuentas para el ahorro, primas que tengan como base planes de pensiones.", "Sí", "No"),
    ("D10", "Pagos por servicios educativos (colegiaturas).", "Sí", "No"),
    ("S01", "Sin efectos fiscales.", "Sí", "Sí"),
    ("CP01", "Pagos.", "Sí", "Sí"),
    ("CN01", "Nómina.", "Sí", "No"),
]

# ─── UNIDADES (subset c_ClaveUnidad) ────────────────────────────────────────
UNIDADES = [
    ("KGM", "Kilogramo", "kilogramo (unidad de masa)", "kg"),
    ("H87", "Pieza", "Unidad estándar para conteo", "pza"),
    ("XBX", "Caja", "caja", "caja"),
    ("XPK", "Paquete", "paquete", "pkg"),
    ("MTR", "Metro", "metro (unidad de longitud)", "m"),
    ("MTK", "Metro cuadrado", "metro cuadrado", "m²"),
    ("MTQ", "Metro cúbico", "metro cúbico", "m³"),
    ("LTR", "Litro", "litro", "L"),
    ("MGM", "Miligramo", "miligramo", "mg"),
    ("GRM", "Gramo", "gramo", "g"),
    ("TNE", "Tonelada", "tonelada métrica", "t"),
    ("E48", "Unidad de servicio", "Servicio", "servicio"),
    ("ACT", "Actividad", "Actividad", "act"),
    ("BG", "Bolsa", "bolsa", "bolsa"),
    ("HUR", "Hora", "hora (3600 s)", "h"),
    ("DAY", "Día", "día (24 horas)", "d"),
]

# ─── CLAVES DE PRODUCTO/SERVICIO (subset relevante para FyV) ────────────────
PRODUCTOS_SERVICIOS = [
    ("50100000", "Animales en pie y vivos", "50"),
    ("50200000", "Productos alimenticios y bebidas y tabaco", "50"),
    ("50202301", "Frutas y/o verduras frescas", "50202300"),
    ("50221200", "Vegetales frescos", "50221200"),
    ("50112000", "Carne y aves de corral", "50110000"),
    ("50130000", "Pescados y mariscos", "50130000"),
    ("50150000", "Granos y semillas y nueces y productos de panadería", "50150000"),
    ("50180000", "Productos de panadería", "50180000"),
    ("50190000", "Alimentos preparados y conservados", "50190000"),
    ("78000000", "Servicios de Transporte, Almacenaje y Correo", "78"),
    ("78100000", "Transporte de pasajeros", "78"),
    ("78101800", "Transporte de carga por carretera", "78"),
    ("80000000", "Servicios de gestión, servicios profesionales de empresa y servicios administrativos", "80"),
]


def upsert(db, model, pk_field: str, rows: list[tuple], cols: list[str]):
    inserted = 0
    skipped = 0
    for row in rows:
        pk_val = row[0]
        existing = db.query(model).filter(getattr(model, pk_field) == pk_val).first()
        if existing:
            skipped += 1
            continue
        kwargs = {col: val for col, val in zip(cols, row)}
        db.add(model(**kwargs))
        inserted += 1
    db.commit()
    return inserted, skipped


def parse_formas_pago():
    """Lee MetodosPago.ini del legacy y devuelve [(clave, desc), ...]."""
    path = KELLY_SAAS_CONFIG / "MetodosPago.ini"
    if not path.exists():
        # Fallback hardcoded si no está disponible el legacy config
        return [
            ("01", "Efectivo"),
            ("02", "Cheque nominativo"),
            ("03", "Transferencia electrónica de fondos"),
            ("04", "Tarjeta de crédito"),
            ("28", "Tarjeta de débito"),
            ("99", "Por definir"),
        ]
    text = path.read_bytes().decode("latin-1")
    cp = configparser.ConfigParser()
    cp.read_string(text)
    rows = []
    if cp.has_section("METODOS"):
        for k, v in cp.items("METODOS"):
            rows.append((k.zfill(2), v))
    return rows


def main():
    db = SessionLocal()
    try:
        print("Sembrando catálogos SAT…\n")

        formas = parse_formas_pago()
        i, s = upsert(db, SatFormaPago, "clave", formas, ["clave", "descripcion"])
        print(f"  formas_pago:        +{i} (skip {s})")

        i, s = upsert(db, SatMetodoPago, "clave", METODOS_PAGO, ["clave", "descripcion"])
        print(f"  metodos_pago:       +{i} (skip {s})")

        i, s = upsert(
            db, SatRegimenFiscal, "clave", REGIMENES,
            ["clave", "descripcion", "aplica_fisica", "aplica_moral"],
        )
        print(f"  regimenes:          +{i} (skip {s})")

        i, s = upsert(
            db, SatUsoCfdi, "clave", USOS_CFDI,
            ["clave", "descripcion", "aplica_fisica", "aplica_moral"],
        )
        print(f"  usos_cfdi:          +{i} (skip {s})")

        i, s = upsert(
            db, SatUnidad, "clave", UNIDADES,
            ["clave", "nombre", "descripcion", "simbolo"],
        )
        print(f"  unidades:           +{i} (skip {s})")

        i, s = upsert(
            db, SatProductoServicio, "clave", PRODUCTOS_SERVICIOS,
            ["clave", "descripcion", "categoria"],
        )
        print(f"  productos_servicios:+{i} (skip {s})")

        print("\nDone.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
