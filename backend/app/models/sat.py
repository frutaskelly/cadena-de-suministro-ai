"""Catálogos SAT (sin tenant_id, globales)."""
from sqlalchemy import Column, String, Date, Text
from ..core.db import Base


class SatProductoServicio(Base):
    __tablename__ = "sat_productos_servicios"
    clave = Column(String(8), primary_key=True)
    descripcion = Column(Text, nullable=False)
    categoria = Column(String(8))
    vigencia_desde = Column(Date)
    vigencia_hasta = Column(Date)


class SatUnidad(Base):
    __tablename__ = "sat_unidades"
    clave = Column(String(3), primary_key=True)
    nombre = Column(String(100), nullable=False)
    descripcion = Column(Text)
    simbolo = Column(String(10))


class SatRegimenFiscal(Base):
    __tablename__ = "sat_regimenes"
    clave = Column(String(4), primary_key=True)
    descripcion = Column(String(254), nullable=False)
    aplica_fisica = Column(String(2), default="No")
    aplica_moral = Column(String(2), default="No")


class SatUsoCfdi(Base):
    __tablename__ = "sat_usos_cfdi"
    clave = Column(String(5), primary_key=True)
    descripcion = Column(String(254), nullable=False)
    aplica_fisica = Column(String(2), default="No")
    aplica_moral = Column(String(2), default="No")


class SatFormaPago(Base):
    __tablename__ = "sat_formas_pago"
    clave = Column(String(5), primary_key=True)
    descripcion = Column(String(254), nullable=False)


class SatMetodoPago(Base):
    __tablename__ = "sat_metodos_pago"
    clave = Column(String(5), primary_key=True)
    descripcion = Column(String(254), nullable=False)


class SatCodigoPostal(Base):
    __tablename__ = "sat_codigos_postales"
    cp = Column(String(5), primary_key=True)
    estado = Column(String(50))
    municipio = Column(String(100))
    zona_horaria = Column(String(20))
