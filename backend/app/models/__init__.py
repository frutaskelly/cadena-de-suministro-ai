"""Importa todos los modelos para que SQLAlchemy/Alembic los detecte."""
from .tenant import Tenant, User, Membership
from .sat import (
    SatProductoServicio, SatUnidad, SatRegimenFiscal, SatUsoCfdi,
    SatFormaPago, SatMetodoPago, SatCodigoPostal,
)
from .contrato import Contrato, ContratoLote, UnidadEntrega
from .cliente import Cliente
from .producto import Producto, ListaPrecios, Precio
from .inventario import Almacen, LoteInventario, MovimientoInventario, Merma
from .pedido import Pedido, LineaPedido
from .factura import CSD, Factura, LineaFactura, Pago, AbonoFactura
from .proveedor import Proveedor, OrdenCompra, LineaOrdenCompra
from .remision import Remision, LineaRemision, AjusteRemision
from .conversion import ConversionProducto
from .whatsapp import AgenteWhatsapp, DocumentoGenerado
from .chat import ChatConversacion, ChatMensaje
from .log import EventLog, MensajeLog

__all__ = [
    "Tenant", "User", "Membership",
    "SatProductoServicio", "SatUnidad", "SatRegimenFiscal", "SatUsoCfdi",
    "SatFormaPago", "SatMetodoPago", "SatCodigoPostal",
    "Contrato", "ContratoLote", "UnidadEntrega",
    "Cliente",
    "Producto", "ListaPrecios", "Precio",
    "Almacen", "LoteInventario", "MovimientoInventario", "Merma",
    "Pedido", "LineaPedido",
    "CSD", "Factura", "LineaFactura", "Pago", "AbonoFactura",
    "Proveedor", "OrdenCompra", "LineaOrdenCompra",
    "Remision", "LineaRemision", "AjusteRemision",
    "ConversionProducto",
    "AgenteWhatsapp", "DocumentoGenerado",
    "ChatConversacion", "ChatMensaje",
    "EventLog", "MensajeLog",
]
