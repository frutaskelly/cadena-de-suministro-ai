"""Migra agentes WhatsApp + crea registros de documentos generados.

Lee del legacy `Whatsapp_agent`:
  - storage/agentes.json: 3 agentes (ehmo_hospitales, surena_comedores, ehmo_dif)
  - storage/folio_counter*.json: contadores actuales
  - storage/pedidos_dia/*.json: pedidos confirmados con folio_remision
    -> derivamos los documentos generados (PDFs y XLSX que el agente
       habria producido para cada uno).
"""
import json
import sys
from datetime import date as date_cls, datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "backend"))

from app.core.db import SessionLocal
from app.models import (
    Tenant, Cliente, ListaPrecios, AgenteWhatsapp, DocumentoGenerado,
    Pedido, Remision,
)

LEGACY = HERE.parent.parent / "Whatsapp_agent"
AGENTES_JSON = LEGACY / "storage" / "agentes.json"
PEDIDOS_DIR = LEGACY / "storage" / "pedidos_dia"


def main():
    db = SessionLocal()
    try:
        tenant = db.query(Tenant).filter(Tenant.slug == "frutas-kelly").first()
        if not tenant:
            print("ERROR: tenant frutas-kelly no existe")
            return

        # ----- 1) Agentes -----
        with open(AGENTES_JSON) as f:
            agentes_data = json.load(f)

        # Mapeo cliente_codigo -> cliente.id, lista_precios_codigo -> lista.id
        clientes_map = {
            c.codigo: c.id
            for c in db.query(Cliente).filter(Cliente.tenant_id == tenant.id).all()
        }
        listas_map = {
            l.codigo: l.id
            for l in db.query(ListaPrecios).filter(ListaPrecios.tenant_id == tenant.id).all()
        }

        # Folios actuales del legacy
        folio_counters = {
            "ehmo_hospitales": json.loads(
                (LEGACY / "storage" / "folio_counter.json").read_text()
            ).get("next", 1),
            "surena_comedores": json.loads(
                (LEGACY / "storage" / "folio_counter_comedores.json").read_text()
            ).get("next", 1),
            "ehmo_dif": 1,  # archivo no existe, default 1
        }

        creados_agentes = 0
        for agente in agentes_data["agentes"]:
            existing = db.query(AgenteWhatsapp).filter(
                AgenteWhatsapp.tenant_id == tenant.id,
                AgenteWhatsapp.codigo == agente["id"],
            ).first()
            if existing:
                continue

            cliente_id = clientes_map.get(agente.get("cliente_id"))
            lista_id = listas_map.get(agente.get("lista_precios_id"))

            a = AgenteWhatsapp(
                tenant_id=tenant.id,
                codigo=agente["id"],
                nombre=agente["nombre"],
                descripcion=agente.get("descripcion"),
                cliente_id=cliente_id,
                lista_precios_id=lista_id,
                tipo=agente.get("tipo", "general"),
                icono=agente.get("icono"),
                color_hex=agente.get("color_hex"),
                activo=agente.get("activo", True),
                proximo_folio=folio_counters.get(agente["id"], 1),
                requires_pesos=agente.get("requires_pesos", False),
                config={
                    "folio_file": agente.get("folio_file"),
                    "lista_precios_archivo": agentes_data.get("listas_precios_archivos", {}).get(
                        agente.get("lista_precios_id")
                    ),
                },
                system_prompt_addendum=agente.get("system_prompt_addendum") or None,
            )
            db.add(a)
            creados_agentes += 1
        db.flush()
        print(f"Agentes creados: {creados_agentes}")

        # ----- 2) Documentos generados desde pedidos confirmados -----
        # Por cada pedido del legacy con folio_remision, asumimos que el agente
        # generó: 1) Pedido PDF, 2) Pedido XLSX, 3) Lista Compras PDF/XLSX (consolidado),
        # 4) Remisión PDF cuando el pedido se factura/confirma
        agente_ehmo = db.query(AgenteWhatsapp).filter(
            AgenteWhatsapp.tenant_id == tenant.id,
            AgenteWhatsapp.codigo == "ehmo_hospitales",
        ).first()
        agente_surena = db.query(AgenteWhatsapp).filter(
            AgenteWhatsapp.tenant_id == tenant.id,
            AgenteWhatsapp.codigo == "surena_comedores",
        ).first()

        creados_docs = 0
        # Por cada archivo pedidos_dia/<fecha>.json
        for pedido_file in sorted(PEDIDOS_DIR.glob("*.json")):
            fecha_str = pedido_file.stem  # "2026-04-25"
            try:
                fecha = date_cls.fromisoformat(fecha_str)
            except ValueError:
                continue

            # Skip si ya existe doc consolidado para este día
            already = db.query(DocumentoGenerado).filter(
                DocumentoGenerado.tenant_id == tenant.id,
                DocumentoGenerado.tipo_documento == "LISTA_COMPRAS_PDF",
                DocumentoGenerado.fecha_documento == fecha,
            ).first()
            if already:
                continue

            data = json.loads(pedido_file.read_text())
            destinos = list(data.get("hospitales", {}).keys())

            # Detectar agente — si todos los destinos contienen "Comedor", es SURENA
            es_surena = any("comedor" in d.lower() for d in destinos)
            agente = agente_surena if es_surena else agente_ehmo
            agente_id = agente.id if agente else None

            # Documentos consolidados del día
            docs_dia = [
                {
                    "tipo_documento": "PEDIDO_PDF",
                    "nombre_archivo": f"Pedido {fecha_str} {'Comedores' if es_surena else 'Hospitales'}.pdf",
                },
                {
                    "tipo_documento": "PEDIDO_XLSX",
                    "nombre_archivo": f"Pedido {fecha_str} {'Comedores' if es_surena else 'Hospitales'}.xlsx",
                },
                {
                    "tipo_documento": "LISTA_COMPRAS_PDF",
                    "nombre_archivo": f"Lista de Compras {fecha_str}.pdf",
                },
                {
                    "tipo_documento": "LISTA_COMPRAS_XLSX",
                    "nombre_archivo": f"Lista de Compras {fecha_str}.xlsx",
                },
            ]
            for d in docs_dia:
                doc = DocumentoGenerado(
                    tenant_id=tenant.id,
                    agente_id=agente_id,
                    tipo_documento=d["tipo_documento"],
                    nombre_archivo=d["nombre_archivo"],
                    fecha_documento=fecha,
                    url_storage=None,
                    metadata_doc={
                        "destinos": destinos,
                        "destinos_count": len(destinos),
                        "source": "version1_legacy",
                    },
                )
                db.add(doc)
                creados_docs += 1

            # Por cada destino con folio_remision: REMISION_PDF
            for destino, info in data.get("hospitales", {}).items():
                folio = info.get("folio_remision")
                if not folio:
                    continue
                remision = db.query(Remision).filter(
                    Remision.tenant_id == tenant.id,
                    Remision.folio == folio,
                ).first()
                pedido = db.query(Pedido).filter(
                    Pedido.tenant_id == tenant.id,
                    Pedido.folio_interno == folio,
                ).first()
                doc = DocumentoGenerado(
                    tenant_id=tenant.id,
                    agente_id=agente_id,
                    remision_id=remision.id if remision else None,
                    pedido_id=pedido.id if pedido else None,
                    tipo_documento="REMISION_PDF",
                    nombre_archivo=f"Remision_{folio}_{destino[:30]}.pdf",
                    fecha_documento=fecha,
                    metadata_doc={
                        "folio": folio,
                        "destino": destino,
                        "estado_legacy": info.get("estado"),
                        "lineas_count": len(info.get("productos", [])),
                        "source": "version1_legacy",
                    },
                )
                db.add(doc)
                creados_docs += 1

            # 1 RELACION_PDF consolidando todas las remisiones del dia
            doc = DocumentoGenerado(
                tenant_id=tenant.id,
                agente_id=agente_id,
                tipo_documento="RELACION_PDF",
                nombre_archivo=f"Relacion {fecha_str} {'Comedores' if es_surena else 'Hospitales'}.pdf",
                fecha_documento=fecha,
                metadata_doc={
                    "destinos": destinos,
                    "remisiones_count": sum(
                        1 for d in data.get("hospitales", {}).values() if d.get("folio_remision")
                    ),
                    "source": "version1_legacy",
                },
            )
            db.add(doc)
            creados_docs += 1

        db.commit()
        print(f"Documentos generados creados: {creados_docs}")

        # Resumen
        from sqlalchemy import func
        rows = db.query(
            DocumentoGenerado.tipo_documento,
            func.count(DocumentoGenerado.id),
        ).filter(
            DocumentoGenerado.tenant_id == tenant.id
        ).group_by(DocumentoGenerado.tipo_documento).all()
        print("\nDistribucion de documentos por tipo:")
        for tipo, count in rows:
            print(f"  {tipo}: {count}")
    finally:
        db.close()


if __name__ == "__main__":
    main()
