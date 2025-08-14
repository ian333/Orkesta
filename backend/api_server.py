"""
ClienteOS API Server - Sistema completo con todos los endpoints
"""
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import json
import os
import sys
import logging
import hashlib
from pathlib import Path

# Agregar el directorio actual al path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Importar agentes
from agents.catalog_agent import CatalogAgent
from agents.sales_agent import SalesAgent, ConversationState

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MODELOS ====================

class ChatMessage(BaseModel):
    phone: str
    message: str
    business_name: Optional[str] = "ClienteOS Demo"

class CatalogUpload(BaseModel):
    name: str
    content: str
    organization_id: Optional[str] = "org_001"

class Product(BaseModel):
    sku: str
    name: str
    price: float
    unit: str = "PZA"
    category: Optional[str] = None
    stock: Optional[int] = 0

class Organization(BaseModel):
    id: str
    name: str
    phone: str
    email: str
    plan: str = "trial"
    catalog_count: int = 0
    client_count: int = 0
    total_sales: float = 0.0

class DashboardMetrics(BaseModel):
    total_conversations: int
    active_conversations: int
    completed_sales: int
    conversion_rate: float
    total_revenue: float
    top_products: List[Dict]
    recent_activity: List[Dict]

class WebhookEvent(BaseModel):
    event_type: str
    data: Dict
    timestamp: datetime

# ==================== APLICACIÓN ====================

app = FastAPI(
    title="ClienteOS + Catálogo IQ",
    description="Convierte PDFs en ventas por WhatsApp",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== ALMACENAMIENTO EN MEMORIA ====================

# Base de datos en memoria (para demo)
database = {
    "organizations": {},
    "catalogs": {},
    "products": {},
    "conversations": {},
    "webhooks": [],
    "metrics": {
        "total_messages": 0,
        "total_sales": 0,
        "total_revenue": 0.0
    }
}

# Agentes
catalog_agent = CatalogAgent()
sales_agent = SalesAgent(catalog_agent)

# Catálogo demo
demo_catalog = [
    {"sku": "TUB001", "canonical_name": "Tubo PVC 3/4\"", "price": 45.00, "unit": "PZA", "aliases": ["tubo pvc 3/4", "tuberia 3/4"], "category": "Plomería"},
    {"sku": "TUB002", "canonical_name": "Tubo PVC 1/2\"", "price": 28.50, "unit": "PZA", "aliases": ["tubo pvc media", "tuberia 1/2"], "category": "Plomería"},
    {"sku": "CEM001", "canonical_name": "Cemento Cruz Azul 50kg", "price": 145.00, "unit": "BULTO", "aliases": ["cemento gris", "mortero"], "category": "Construcción"},
    {"sku": "PIN001", "canonical_name": "Pintura Vinílica Blanca 19L", "price": 780.00, "unit": "CUBETA", "aliases": ["pintura blanca"], "category": "Pintura"},
    {"sku": "TOR001", "canonical_name": "Tornillo 1/4 x 2\"", "price": 2.50, "unit": "PZA", "aliases": ["tornillo"], "category": "Ferretería"},
]

database["catalogs"]["demo"] = demo_catalog

# ==================== ENDPOINTS ====================

@app.get("/")
async def root():
    """Endpoint raíz con información del sistema"""
    return {
        "name": "ClienteOS + Catálogo IQ",
        "version": "2.0.0",
        "status": "running",
        "endpoints": {
            "chat": "/api/chat",
            "catalog": "/api/catalog",
            "dashboard": "/dashboard",
            "webhooks": "/api/webhooks"
        },
        "documentation": "/docs"
    }

# ==================== CHAT / WHATSAPP ====================

@app.post("/api/chat")
async def chat_endpoint(message: ChatMessage):
    """
    Endpoint principal de chat/WhatsApp
    Procesa mensajes y genera respuestas inteligentes
    """
    try:
        # Incrementar contador
        database["metrics"]["total_messages"] += 1
        
        # Obtener catálogo
        catalog = database["catalogs"].get("demo", demo_catalog)
        
        # Procesar mensaje con el agente
        response = sales_agent.process_message(
            phone=message.phone,
            message=message.message,
            business_name=message.business_name,
            catalog=catalog
        )
        
        # Guardar conversación
        if message.phone not in database["conversations"]:
            database["conversations"][message.phone] = []
        
        database["conversations"][message.phone].append({
            "timestamp": datetime.now().isoformat(),
            "message": message.message,
            "response": response["text"],
            "state": sales_agent.conversations[message.phone]["state"].value if message.phone in sales_agent.conversations else "new"
        })
        
        # Si hay link de pago, incrementar ventas
        if response.get("payment_link"):
            database["metrics"]["total_sales"] += 1
            if response.get("order"):
                database["metrics"]["total_revenue"] += response["order"]["total"]
        
        return {
            "success": True,
            "response": response["text"],
            "quick_replies": response.get("quick_replies", []),
            "payment_link": response.get("payment_link"),
            "products": response.get("products", []),
            "conversation_state": sales_agent.conversations.get(message.phone, {}).get("state", ConversationState.GREETING).value
        }
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chat/history/{phone}")
async def get_chat_history(phone: str):
    """Obtener historial de conversación"""
    history = database["conversations"].get(phone, [])
    return {
        "phone": phone,
        "messages": history,
        "total": len(history)
    }

@app.get("/api/chat/active")
async def get_active_chats():
    """Obtener conversaciones activas"""
    active = []
    for phone, conv in sales_agent.conversations.items():
        if conv["state"] != ConversationState.COMPLETED:
            active.append({
                "phone": phone,
                "state": conv["state"].value,
                "started_at": conv["context"]["started_at"].isoformat(),
                "messages_count": len(conv["context"]["messages"])
            })
    return {"active_conversations": active, "total": len(active)}

# ==================== CATÁLOGO ====================

@app.post("/api/catalog/upload")
async def upload_catalog(file: UploadFile = File(...)):
    """Subir catálogo PDF/Excel"""
    try:
        content = await file.read()
        content_str = content.decode('utf-8', errors='ignore')
        
        # Procesar con el agente
        products = catalog_agent.extract_from_pdf(content_str)
        
        # Guardar en base de datos
        catalog_id = f"cat_{hashlib.md5(content).hexdigest()[:8]}"
        database["catalogs"][catalog_id] = products
        
        return {
            "success": True,
            "catalog_id": catalog_id,
            "products_extracted": len(products),
            "sample": products[:3] if products else []
        }
        
    except Exception as e:
        logger.error(f"Error uploading catalog: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/catalog/{catalog_id}")
async def get_catalog(catalog_id: str):
    """Obtener catálogo por ID"""
    if catalog_id not in database["catalogs"]:
        raise HTTPException(status_code=404, detail="Catalog not found")
    
    catalog = database["catalogs"][catalog_id]
    return {
        "catalog_id": catalog_id,
        "products": catalog,
        "total": len(catalog)
    }

@app.post("/api/catalog/search")
async def search_catalog(query: str = Body(...), catalog_id: str = Body(default="demo")):
    """Buscar productos en el catálogo"""
    if catalog_id not in database["catalogs"]:
        raise HTTPException(status_code=404, detail="Catalog not found")
    
    catalog = database["catalogs"][catalog_id]
    results = catalog_agent.search_products(query, catalog)
    
    return {
        "query": query,
        "results": results,
        "total": len(results)
    }

@app.post("/api/catalog/normalize")
async def normalize_products(products: List[Dict] = Body(...)):
    """Normalizar lista de productos"""
    normalized = catalog_agent._normalize_products(products)
    return {
        "original_count": len(products),
        "normalized_count": len(normalized),
        "products": normalized
    }

# ==================== DASHBOARD ====================

@app.get("/api/dashboard/metrics")
async def get_dashboard_metrics():
    """Obtener métricas para el dashboard"""
    # Calcular métricas
    total_conversations = len(database["conversations"])
    active_conversations = len([c for c in sales_agent.conversations.values() 
                                if c["state"] not in [ConversationState.COMPLETED, ConversationState.ABANDONED]])
    
    # Top productos (simulado)
    top_products = [
        {"name": "Tubo PVC 3/4\"", "sales": 45, "revenue": 2025.00},
        {"name": "Cemento Cruz Azul", "sales": 32, "revenue": 4640.00},
        {"name": "Pintura Blanca", "sales": 18, "revenue": 14040.00}
    ]
    
    # Actividad reciente
    recent_activity = []
    for phone, messages in list(database["conversations"].items())[-5:]:
        if messages:
            recent_activity.append({
                "phone": phone,
                "last_message": messages[-1]["message"],
                "timestamp": messages[-1]["timestamp"]
            })
    
    return DashboardMetrics(
        total_conversations=total_conversations,
        active_conversations=active_conversations,
        completed_sales=database["metrics"]["total_sales"],
        conversion_rate=(database["metrics"]["total_sales"] / total_conversations * 100) if total_conversations > 0 else 0,
        total_revenue=database["metrics"]["total_revenue"],
        top_products=top_products,
        recent_activity=recent_activity
    )

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    """Dashboard HTML de administrador"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>ClienteOS Dashboard</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f5f5f5; }
            .header { background: #2563eb; color: white; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
            .metrics { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px; margin: 20px 0; }
            .metric-card { background: white; padding: 20px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .metric-value { font-size: 32px; font-weight: bold; color: #2563eb; }
            .metric-label { color: #666; margin-top: 5px; }
            .section { background: white; padding: 20px; border-radius: 8px; margin: 20px 0; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
            .chat-test { display: flex; gap: 10px; margin-top: 20px; }
            .chat-test input { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }
            .chat-test button { padding: 10px 20px; background: #2563eb; color: white; border: none; border-radius: 4px; cursor: pointer; }
            .response { margin-top: 20px; padding: 15px; background: #f0f9ff; border-radius: 4px; white-space: pre-wrap; }
            table { width: 100%; margin-top: 10px; }
            th { text-align: left; padding: 10px; background: #f5f5f5; }
            td { padding: 10px; border-bottom: 1px solid #eee; }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>ClienteOS Dashboard</h1>
            <p>Sistema de gestión inteligente para PyMEs</p>
        </div>
        
        <div class="container">
            <div class="metrics" id="metrics">
                <div class="metric-card">
                    <div class="metric-value" id="totalConversations">0</div>
                    <div class="metric-label">Conversaciones Totales</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="activeSales">0</div>
                    <div class="metric-label">Ventas Activas</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="conversionRate">0%</div>
                    <div class="metric-label">Tasa de Conversión</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value" id="totalRevenue">$0</div>
                    <div class="metric-label">Ingresos Totales</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Probar Chat de WhatsApp</h2>
                <div class="chat-test">
                    <input type="text" id="chatInput" placeholder="Escribe un mensaje... ej: 'necesito 10 tubos pvc 3/4'" />
                    <button onclick="sendMessage()">Enviar</button>
                </div>
                <div id="chatResponse" class="response" style="display:none;"></div>
            </div>
            
            <div class="section">
                <h2>Productos Más Vendidos</h2>
                <table id="topProducts">
                    <thead>
                        <tr>
                            <th>Producto</th>
                            <th>Ventas</th>
                            <th>Ingresos</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
            
            <div class="section">
                <h2>Actividad Reciente</h2>
                <table id="recentActivity">
                    <thead>
                        <tr>
                            <th>Cliente</th>
                            <th>Mensaje</th>
                            <th>Hora</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
            </div>
        </div>
        
        <script>
            // Cargar métricas
            async function loadMetrics() {
                try {
                    const response = await fetch('/api/dashboard/metrics');
                    const data = await response.json();
                    
                    document.getElementById('totalConversations').textContent = data.total_conversations;
                    document.getElementById('activeSales').textContent = data.active_conversations;
                    document.getElementById('conversionRate').textContent = data.conversion_rate.toFixed(1) + '%';
                    document.getElementById('totalRevenue').textContent = '$' + data.total_revenue.toFixed(2);
                    
                    // Top productos
                    const productsTable = document.querySelector('#topProducts tbody');
                    productsTable.innerHTML = '';
                    data.top_products.forEach(product => {
                        const row = productsTable.insertRow();
                        row.innerHTML = `
                            <td>${product.name}</td>
                            <td>${product.sales}</td>
                            <td>$${product.revenue.toFixed(2)}</td>
                        `;
                    });
                    
                    // Actividad reciente
                    const activityTable = document.querySelector('#recentActivity tbody');
                    activityTable.innerHTML = '';
                    data.recent_activity.forEach(activity => {
                        const row = activityTable.insertRow();
                        const time = new Date(activity.timestamp).toLocaleTimeString();
                        row.innerHTML = `
                            <td>${activity.phone}</td>
                            <td>${activity.last_message}</td>
                            <td>${time}</td>
                        `;
                    });
                } catch (error) {
                    console.error('Error loading metrics:', error);
                }
            }
            
            // Enviar mensaje de prueba
            async function sendMessage() {
                const input = document.getElementById('chatInput');
                const message = input.value.trim();
                if (!message) return;
                
                const responseDiv = document.getElementById('chatResponse');
                responseDiv.style.display = 'block';
                responseDiv.textContent = 'Procesando...';
                
                try {
                    const response = await fetch('/api/chat', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            phone: '+52' + Math.random().toString().slice(2, 12),
                            message: message,
                            business_name: 'Ferretería Demo'
                        })
                    });
                    
                    const data = await response.json();
                    
                    let responseText = '🤖 Respuesta:\\n' + data.response;
                    
                    if (data.products && data.products.length > 0) {
                        responseText += '\\n\\n📦 Productos encontrados:\\n';
                        data.products.forEach((p, i) => {
                            responseText += `${i+1}. ${p.canonical_name} - $${p.price} ${p.unit}\\n`;
                        });
                    }
                    
                    if (data.payment_link) {
                        responseText += '\\n💳 Link de pago: ' + data.payment_link;
                    }
                    
                    if (data.quick_replies && data.quick_replies.length > 0) {
                        responseText += '\\n\\n🔘 Respuestas rápidas: ' + data.quick_replies.join(' | ');
                    }
                    
                    responseDiv.textContent = responseText;
                    
                    // Recargar métricas
                    setTimeout(loadMetrics, 1000);
                    
                } catch (error) {
                    responseDiv.textContent = '❌ Error: ' + error.message;
                }
                
                input.value = '';
            }
            
            // Enter para enviar
            document.getElementById('chatInput').addEventListener('keypress', function(e) {
                if (e.key === 'Enter') sendMessage();
            });
            
            // Cargar métricas al inicio
            loadMetrics();
            
            // Actualizar cada 10 segundos
            setInterval(loadMetrics, 10000);
        </script>
    </body>
    </html>
    """
    return html_content

# ==================== WEBHOOKS ====================

@app.post("/api/webhooks/whatsapp")
async def whatsapp_webhook(event: WebhookEvent):
    """Webhook para recibir mensajes de WhatsApp"""
    database["webhooks"].append({
        "type": "whatsapp",
        "event": event.event_type,
        "data": event.data,
        "timestamp": event.timestamp.isoformat()
    })
    
    # Si es un mensaje entrante, procesarlo
    if event.event_type == "message":
        phone = event.data.get("from")
        message = event.data.get("text", {}).get("body", "")
        
        response = await chat_endpoint(ChatMessage(
            phone=phone,
            message=message
        ))
        
        return response
    
    return {"status": "received"}

@app.post("/api/webhooks/stripe")
async def stripe_webhook(event: WebhookEvent):
    """Webhook para pagos de Stripe"""
    database["webhooks"].append({
        "type": "stripe",
        "event": event.event_type,
        "data": event.data,
        "timestamp": event.timestamp.isoformat()
    })
    
    # Procesar según tipo de evento
    if event.event_type == "payment_intent.succeeded":
        database["metrics"]["total_sales"] += 1
        database["metrics"]["total_revenue"] += event.data.get("amount", 0) / 100
    
    return {"status": "received"}

@app.get("/api/webhooks/history")
async def get_webhook_history(limit: int = 50):
    """Obtener historial de webhooks"""
    return {
        "webhooks": database["webhooks"][-limit:],
        "total": len(database["webhooks"])
    }

# ==================== ORGANIZACIONES ====================

@app.get("/api/organizations")
async def get_organizations():
    """Obtener todas las organizaciones"""
    return {"organizations": list(database["organizations"].values())}

@app.post("/api/organizations")
async def create_organization(org: Organization):
    """Crear nueva organización"""
    database["organizations"][org.id] = org.dict()
    return {"success": True, "organization": org}

# ==================== HEALTH CHECK ====================

@app.get("/health")
async def health_check():
    """Health check del sistema"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "agents": {
            "catalog": "ready",
            "sales": "ready"
        },
        "database": {
            "catalogs": len(database["catalogs"]),
            "conversations": len(database["conversations"]),
            "webhooks": len(database["webhooks"])
        }
    }

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 ClienteOS + Catálogo IQ - API Server")
    print("="*60)
    print("\n📍 Endpoints disponibles:")
    print("   - Dashboard: http://localhost:8000/dashboard")
    print("   - API Docs: http://localhost:8000/docs")
    print("   - Chat API: POST http://localhost:8000/api/chat")
    print("   - Health: http://localhost:8000/health")
    print("\n✨ El sistema está listo para recibir mensajes de WhatsApp")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)