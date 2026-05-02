"""Construye payloads CFDI 4.0 a partir de modelos internos.

Toma un `Pedido` (con sus líneas) + el `Tenant` emisor + el `Cliente` receptor
y arma el dict que la API de Facturama espera. Aún no timbra — solo arma.

Útil para:
- Pre-validar antes de timbrar (catch de campos faltantes)
- Preview "cómo se verá la factura" en frontend antes del clic timbrar
- Tests offline
"""
from __future__ import annotations
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from sqlalchemy.orm import Session

from ..models import Tenant, Cliente, Pedido, LineaPedido, Producto


@dataclass
class CfdiValidationError:
    field: str
    message: str


@dataclass
class CfdiBuildResult:
    payload: Optional[dict]
    errors: list[CfdiValidationError] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.payload is not None and not self.errors


def _q4(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


def _q2(v: Decimal) -> Decimal:
    return v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def build_cfdi_from_pedido(
    db: Session,
    pedido: Pedido,
    serie: str = "F",
    folio: Optional[int] = None,
    forma_pago: Optional[str] = None,
    metodo_pago: Optional[str] = None,
    uso_cfdi: Optional[str] = None,
) -> CfdiBuildResult:
    """Mapea `Pedido` → payload Facturama API.

    Defaults:
      - forma_pago: cliente.forma_pago_default o '99'
      - metodo_pago: cliente.metodo_pago_default o 'PPD'
      - uso_cfdi: cliente.uso_cfdi_default o 'G03'
    """
    errors: list[CfdiValidationError] = []
    warnings: list[str] = []

    if not pedido.lineas:
        errors.append(CfdiValidationError("lineas", "Pedido sin líneas"))

    cliente = db.query(Cliente).filter(Cliente.id == pedido.cliente_facturacion_id).first()
    if not cliente:
        errors.append(CfdiValidationError("cliente", "Cliente no encontrado"))
        return CfdiBuildResult(payload=None, errors=errors)

    tenant = db.query(Tenant).filter(Tenant.id == pedido.tenant_id).first()
    if not tenant:
        errors.append(CfdiValidationError("tenant", "Tenant no encontrado"))
        return CfdiBuildResult(payload=None, errors=errors)

    # Validaciones del emisor
    if not tenant.rfc:
        errors.append(CfdiValidationError("emisor.rfc", "Tenant sin RFC"))
    if not tenant.regimen_fiscal_sat:
        errors.append(CfdiValidationError("emisor.regimen_fiscal", "Tenant sin régimen"))
    if not tenant.domicilio_fiscal_cp:
        errors.append(CfdiValidationError("emisor.cp", "Tenant sin CP"))

    # Validaciones del receptor
    if not cliente.rfc:
        errors.append(CfdiValidationError("receptor.rfc", "Cliente sin RFC"))
    receptor_cp = (cliente.domicilio_fiscal or {}).get("cp") if cliente.domicilio_fiscal else None
    if not receptor_cp:
        errors.append(CfdiValidationError("receptor.cp", "Cliente sin CP fiscal"))
    if not cliente.regimen_fiscal:
        errors.append(CfdiValidationError("receptor.regimen", "Cliente sin régimen fiscal"))

    if errors:
        return CfdiBuildResult(payload=None, errors=errors)

    # Construir conceptos
    conceptos = []
    subtotal = Decimal("0")
    total_iva = Decimal("0")

    productos_idx = {}
    for ln in pedido.lineas:
        if ln.producto_id and ln.producto_id not in productos_idx:
            p = db.query(Producto).filter(Producto.id == ln.producto_id).first()
            if p:
                productos_idx[ln.producto_id] = p

    for ln in pedido.lineas:
        producto = productos_idx.get(ln.producto_id)
        if not producto and not ln.texto_original:
            errors.append(CfdiValidationError(
                f"linea[{ln.numero_linea}]",
                "Línea sin producto y sin texto_original",
            ))
            continue

        descripcion = producto.nombre if producto else (ln.texto_original or "Producto")
        clave_sat = producto.clave_sat if producto else "01010101"
        unidad_sat = producto.unidad_sat if producto else "H87"
        iva_tasa = Decimal(str(producto.iva_tasa or 0)) if producto else Decimal("0")
        objeto_imp = producto.objeto_imp if producto else "02"

        cantidad = Decimal(str(ln.cantidad_solicitada))
        precio = Decimal(str(ln.precio_unitario))
        importe = _q4(cantidad * precio)
        subtotal += importe

        impuestos = []
        if iva_tasa > 0:
            iva_importe = _q4(importe * iva_tasa)
            total_iva += iva_importe
            impuestos = [{
                "Total": float(iva_importe),
                "Name": "IVA",
                "Base": float(importe),
                "Rate": float(iva_tasa),
                "IsRetention": False,
                "IsQuotaFixed": False,
            }]

        conceptos.append({
            "ProductCode": clave_sat,
            "IdentificationNumber": (producto.sku_interno if producto else ""),
            "Description": descripcion,
            "Unit": "UNIDAD" if unidad_sat == "H87" else "KILO",
            "UnitCode": unidad_sat,
            "UnitPrice": float(precio),
            "Quantity": float(cantidad),
            "Subtotal": float(importe),
            "Discount": 0,
            "TaxObject": objeto_imp,
            "Taxes": impuestos,
            "Total": float(importe + (impuestos[0]["Total"] if impuestos else 0)),
        })

    if errors:
        return CfdiBuildResult(payload=None, errors=errors)

    total = subtotal + total_iva

    payload = {
        "NameId": "1",  # CFDI ingresos básico
        "CfdiType": "I",
        "ExpeditionPlace": tenant.domicilio_fiscal_cp,
        "PaymentForm": forma_pago or cliente.forma_pago_default or "99",
        "PaymentMethod": metodo_pago or cliente.metodo_pago_default or "PPD",
        "Currency": "MXN",
        "Date": pedido.fecha_pedido.isoformat() + "T00:00:00",
        "Serie": serie,
        "Folio": folio,
        "Issuer": {
            "Rfc": tenant.rfc,
            "Name": tenant.legal_name,
            "FiscalRegime": tenant.regimen_fiscal_sat,
        },
        "Receiver": {
            "Rfc": cliente.rfc,
            "Name": cliente.legal_name,
            "CfdiUse": uso_cfdi or cliente.uso_cfdi_default or "G03",
            "FiscalRegime": cliente.regimen_fiscal,
            "TaxZipCode": receptor_cp,
        },
        "Items": conceptos,
        "Subtotal": float(_q2(subtotal)),
        "Total": float(_q2(total)),
    }

    if not folio:
        warnings.append("Folio sin asignar; Facturama lo asigna automáticamente si NameId=1")

    if pedido.estado not in ("CONFIRMADO", "ENVIADO", "ENTREGADO"):
        warnings.append(
            f"Pedido en estado {pedido.estado} — usualmente se factura solo CONFIRMADO/ENVIADO/ENTREGADO"
        )

    return CfdiBuildResult(payload=payload, errors=[], warnings=warnings)
