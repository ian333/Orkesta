#!/usr/bin/env python3
"""
🚀 ORKESTA LAUNCHER
===================

Servidor principal del sistema Orkesta con todos los componentes.
"""

import uvicorn
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

if __name__ == "__main__":
    print("🧠 ORKESTA - Sistema Multi-Tenant con Cerebro Compartido")
    print("=" * 60)
    print("🚀 Iniciando servidor en http://localhost:8000")
    print("📊 Control Tower en http://localhost:8000/dashboard/overview")
    print("🧪 Lab de Testing en http://localhost:8000/simulation/lab")
    print("💳 Stripe Connect en http://localhost:8000/api/connect/accounts")
    print("=" * 60)
    
    uvicorn.run(
        "control_tower_enhanced_api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )