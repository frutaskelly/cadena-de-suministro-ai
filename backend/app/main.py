"""Cadena de Suministro AI — FastAPI entry point."""
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .core.config import settings
from .api.v1 import (
    tenants, clientes, productos, contratos, pedidos, sat, dashboard,
    remisiones, ordenes_compra, conversiones, whatsapp,
)

FRONTEND_DIR = Path(__file__).resolve().parent.parent.parent / "frontend"

logging.basicConfig(level=getattr(logging, settings.LOG_LEVEL))
log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info(
        f"Cadena de Suministro AI starting — env={settings.ENVIRONMENT}, "
        f"port={settings.PORT}, allowed_origins={settings.allowed_origins_list()}"
    )
    yield
    log.info("Shutting down")


app = FastAPI(
    title="Cadena de Suministro AI",
    version="0.2.0",
    description="Plataforma SaaS para coordinación de cadena gobierno-alimentos.",
    lifespan=lifespan,
)

# CORS — origins explicitos desde env. Por default solo localhost dev.
# AUDIT C3: cerrado el wildcard que era CSRF/XSS prone en prod.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "x-tenant-id"],
    expose_headers=["x-request-id"],
    max_age=3600,
)


@app.get("/health")
def health():
    return {"status": "ok", "version": app.version, "env": settings.ENVIRONMENT}


@app.get("/api")
def api_root():
    return {
        "service": "cadena-de-suministro-ai",
        "docs": "/docs",
        "health": "/health",
    }


# ─── Frontend estático (operator dashboard) ────────────────────────────────
if FRONTEND_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")

    @app.get("/")
    def frontend_index():
        return FileResponse(str(FRONTEND_DIR / "index.html"))
else:
    @app.get("/")
    def root():
        return {"service": "cadena-de-suministro-ai", "docs": "/docs"}


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
app.include_router(sat.router, prefix="/api/v1")
app.include_router(dashboard.router, prefix="/api/v1")
app.include_router(remisiones.router, prefix="/api/v1")
app.include_router(ordenes_compra.router, prefix="/api/v1")
app.include_router(conversiones.router, prefix="/api/v1")
app.include_router(whatsapp.router_agentes, prefix="/api/v1")
app.include_router(whatsapp.router_docs, prefix="/api/v1")
