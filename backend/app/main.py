"""Cadena de Suministro AI — FastAPI entry point."""
import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core.config import settings
from .api.v1 import tenants, clientes, productos, contratos, pedidos

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
log = logging.getLogger(__name__)

app = FastAPI(
    title="Cadena de Suministro AI",
    version="0.1.0",
    description="Plataforma SaaS para coordinación de cadena gobierno-alimentos.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version, "env": settings.ENVIRONMENT}


@app.get("/")
def root():
    return {
        "service": "cadena-de-suministro-ai",
        "docs": "/docs",
        "health": "/health",
    }


# ─── API v1 routers ─────────────────────────────────────────────────────────
app.include_router(tenants.router, prefix="/api/v1")
app.include_router(tenants.users_router, prefix="/api/v1")
app.include_router(tenants.memberships_router, prefix="/api/v1")
app.include_router(clientes.router, prefix="/api/v1")
app.include_router(productos.router, prefix="/api/v1")
app.include_router(productos.listas_router, prefix="/api/v1")
app.include_router(productos.precios_router, prefix="/api/v1")
app.include_router(contratos.router, prefix="/api/v1")
app.include_router(contratos.lotes_router, prefix="/api/v1")
app.include_router(contratos.unidades_router, prefix="/api/v1")
app.include_router(pedidos.router, prefix="/api/v1")


@app.on_event("startup")
def on_startup():
    log.info(f"Cadena de Suministro AI starting — env={settings.ENVIRONMENT}, port={settings.PORT}")
