"""
ClienteOS - Sistema Simplificado de Gestión de Negocios
Cobros, Consultorios, Finanzas y Ventas por WhatsApp
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Importar routers (sin importaciones relativas problemáticas por ahora)
# from routers import auth, clients, payments, appointments, whatsapp, dashboard

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manejo del ciclo de vida"""
    logger.info("🚀 Iniciando ClienteOS...")
    # Aquí puedes inicializar la DB, cache, etc.
    yield
    logger.info("👋 Deteniendo ClienteOS...")

# Crear app
app = FastAPI(
    title="ClienteOS",
    description="Sistema de gestión para negocios: cobros, citas, finanzas",
    version="1.0.0",
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción, especifica los dominios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check
@app.get("/")
async def root():
    return {
        "name": "ClienteOS",
        "status": "running",
        "version": "1.0.0",
        "message": "Sistema de gestión para PyMEs mexicanas"
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# API endpoints temporales para prueba
@app.get("/api/test")
async def test_endpoint():
    return {
        "message": "API funcionando correctamente",
        "features": [
            "Gestión de clientes",
            "Cobros con Stripe",
            "Citas para consultorios",
            "WhatsApp Business Integration",
            "Dashboard y reportes"
        ]
    }

# Por ahora comentado hasta arreglar las importaciones
# app.include_router(auth.router, prefix="/api/auth", tags=["Auth"])
# app.include_router(clients.router, prefix="/api/clients", tags=["Clients"])
# app.include_router(payments.router, prefix="/api/payments", tags=["Payments"])
# app.include_router(appointments.router, prefix="/api/appointments", tags=["Appointments"])
# app.include_router(whatsapp.router, prefix="/api/whatsapp", tags=["WhatsApp"])
# app.include_router(dashboard.router, prefix="/api/dashboard", tags=["Dashboard"])

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    logger.info(f"🌐 Servidor iniciando en http://localhost:{port}")
    logger.info(f"📚 Documentación disponible en http://localhost:{port}/docs")
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)