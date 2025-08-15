"""
🎮 CONTROL TOWER API V2 - Con contexto de tenant aislado
Multi-tenant con aislamiento completo y sincronización entre pestañas
"""
from fastapi import FastAPI, HTTPException, Header, Depends, Body, Query, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any, Union
from datetime import datetime, timedelta, date
from enum import Enum
import json
import time
import random
import hashlib
import asyncio
from pathlib import Path
import os

# ==================== DEPENDENCIAS ====================

async def require_tenant(
    x_org_id: str = Header(None, alias="X-Org-Id"),
    x_requested_tenant: str = Header(None, alias="X-Requested-Tenant")
) -> str:
    """Dependencia que requiere tenant en headers"""
    tenant_id = x_org_id or x_requested_tenant
    if not tenant_id:
        raise HTTPException(
            status_code=400,
            detail="X-Org-Id header is required for all requests"
        )
    
    # Validar que el tenant existe
    if tenant_id not in db.tenants:
        raise HTTPException(
            status_code=404,
            detail=f"Tenant '{tenant_id}' not found"
        )
    
    return tenant_id

# ==================== MODELOS ====================

class TenantStatus(str, Enum):
    ACTIVE = "active"
    TRIAL = "trial"
    SUSPENDED = "suspended"
    CHURNED = "churned"

class Environment(str, Enum):
    SANDBOX = "sandbox"
    PRODUCTION = "production"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    PARTIAL = "partial"
    REFUNDED = "refunded"

class DunningStage(str, Enum):
    T_MINUS_3 = "T-3"
    T_MINUS_1 = "T-1"
    DUE = "DUE"
    T_PLUS_1 = "T+1"
    T_PLUS_3 = "T+3"
    T_PLUS_7 = "T+7"
    T_PLUS_15 = "T+15"
    T_PLUS_30 = "T+30"
    WRITE_OFF = "WRITE_OFF"

class Tenant(BaseModel):
    id: str                       # Slug estable (equipo-automotriz-javaz)
    display_name: str             # Nombre para UI
    status: TenantStatus
    environment: Environment = Environment.SANDBOX
    created_at: datetime
    # Integraciones
    whatsapp: Dict = {"status": "sandbox", "templates": {"approved": 0, "pending": 0, "rejected": 0}}
    telegram: Dict = {"status": "inactive", "bot_token": None}
    email: Dict = {"status": "active", "provider": "sendgrid"}
    psp: Dict = {"status": "test", "provider": "stripe"}
    # Métricas específicas por tenant
    catalog_size: int = 0
    last_import: Optional[datetime] = None
    active_customers: int = 0
    open_invoices: int = 0
    invoices_paid: int = 0
    throughput_mps: float = 0
    dunning_enabled: bool = True
    errors_24h: int = 0

class Invoice(BaseModel):
    id: str
    tenant_id: str
    customer_id: str
    amount: float
    due_date: date
    status: PaymentStatus = PaymentStatus.PENDING
    dunning_stage: DunningStage = DunningStage.T_MINUS_3
    payment_link: Optional[str] = None
    created_at: datetime
    paid_at: Optional[datetime] = None

# ==================== APLICACIÓN ====================

app = FastAPI(
    title="Orkesta Control Tower V2",
    description="Sistema Multi-tenant con Aislamiento Completo",
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

# ==================== BASE DE DATOS ====================

class ControlTowerDB:
    def __init__(self):
        self.tenants = {}
        self.invoices = {}
        self.events_by_tenant = {}
        self.metrics_by_tenant = {}
        
        # Cargar datos diferenciados por tenant
        self._seed_demo_data()
    
    def _seed_demo_data(self):
        """Carga 3 tenants con datos muy diferenciados"""
        
        # Tenant 1: Equipo Automotriz JAvaz
        self.tenants["equipo-automotriz-javaz"] = Tenant(
            id="equipo-automotriz-javaz",
            display_name="Equipo Automotriz JAvaz",
            status=TenantStatus.ACTIVE,
            environment=Environment.PRODUCTION,
            created_at=datetime.now() - timedelta(days=180),
            whatsapp={"status": "production", "templates": {"approved": 5, "pending": 2, "rejected": 1}},
            psp={"status": "production", "provider": "stripe"},
            catalog_size=2340,
            last_import=datetime.now() - timedelta(hours=3),
            active_customers=423,
            open_invoices=11,
            invoices_paid=23,
            throughput_mps=58.3,
            dunning_enabled=True,
            errors_24h=2
        )
        
        # Tenant 2: LB Productions
        self.tenants["lb-productions"] = Tenant(
            id="lb-productions",
            display_name="LB Productions",
            status=TenantStatus.ACTIVE,
            environment=Environment.PRODUCTION,
            created_at=datetime.now() - timedelta(days=90),
            whatsapp={"status": "production", "templates": {"approved": 2, "pending": 4, "rejected": 0}},
            telegram={"status": "active", "bot_token": "xxx"},
            psp={"status": "production", "provider": "mercadopago"},
            catalog_size=156,
            last_import=datetime.now() - timedelta(days=2),
            active_customers=89,
            open_invoices=3,
            invoices_paid=7,
            throughput_mps=31.2,
            dunning_enabled=True,
            errors_24h=0
        )
        
        # Tenant 3: Clínica Salud Plus
        self.tenants["clinica-salud-plus"] = Tenant(
            id="clinica-salud-plus",
            display_name="Clínica Salud Plus",
            status=TenantStatus.TRIAL,
            environment=Environment.SANDBOX,
            created_at=datetime.now() - timedelta(days=15),
            whatsapp={"status": "sandbox", "templates": {"approved": 4, "pending": 1, "rejected": 1}},
            psp={"status": "test", "provider": "stripe"},
            catalog_size=340,
            last_import=datetime.now() - timedelta(hours=12),
            active_customers=67,
            open_invoices=6,
            invoices_paid=15,
            throughput_mps=45.7,
            dunning_enabled=True,
            errors_24h=3
        )
        
        # Generar invoices diferenciados por tenant
        invoice_configs = {
            "equipo-automotriz-javaz": {
                "count": 34,
                "avg_amount": 3500,
                "overdue_rate": 0.32
            },
            "lb-productions": {
                "count": 10,
                "avg_amount": 15000,
                "overdue_rate": 0.30
            },
            "clinica-salud-plus": {
                "count": 21,
                "avg_amount": 1200,
                "overdue_rate": 0.28
            }
        }
        
        for tenant_id, config in invoice_configs.items():
            for i in range(config["count"]):
                # Determinar si está vencida
                is_overdue = random.random() < config["overdue_rate"]
                days_offset = random.randint(-30, 30) if is_overdue else random.randint(1, 60)
                
                # Determinar estado
                if is_overdue and days_offset < -7:
                    status = PaymentStatus.PENDING
                    dunning_stage = DunningStage.T_PLUS_7
                elif days_offset < 0:
                    status = PaymentStatus.PENDING
                    dunning_stage = DunningStage.T_PLUS_1
                elif i % 3 == 0:
                    status = PaymentStatus.SUCCEEDED
                    dunning_stage = DunningStage.DUE
                else:
                    status = PaymentStatus.PENDING
                    dunning_stage = DunningStage.T_MINUS_3
                
                invoice = Invoice(
                    id=f"INV-{tenant_id[:3].upper()}-{i:04d}",
                    tenant_id=tenant_id,
                    customer_id=f"CUST-{random.randint(1000, 9999)}",
                    amount=config["avg_amount"] * random.uniform(0.5, 2.0),
                    due_date=date.today() + timedelta(days=days_offset),
                    status=status,
                    dunning_stage=dunning_stage,
                    payment_link=f"https://pay.orkesta.mx/{tenant_id[:3]}-{i:04d}",
                    created_at=datetime.now() - timedelta(days=random.randint(0, 90)),
                    paid_at=datetime.now() if status == PaymentStatus.SUCCEEDED else None
                )
                self.invoices[invoice.id] = invoice
        
        # Métricas diferenciadas por tenant
        self.metrics_by_tenant = {
            "equipo-automotriz-javaz": {
                "messages_per_second": 58.3,
                "webhooks_per_second": 12.4,
                "queue_depth": 23,
                "dlq_count": 2,
                "wa_delivery_rate": 0.97,
                "p95_latency": 234
            },
            "lb-productions": {
                "messages_per_second": 31.2,
                "webhooks_per_second": 6.8,
                "queue_depth": 5,
                "dlq_count": 0,
                "wa_delivery_rate": 0.99,
                "p95_latency": 189
            },
            "clinica-salud-plus": {
                "messages_per_second": 45.7,
                "webhooks_per_second": 9.3,
                "queue_depth": 12,
                "dlq_count": 1,
                "wa_delivery_rate": 0.95,
                "p95_latency": 267
            }
        }

db = ControlTowerDB()

# ==================== ENDPOINTS ====================

@app.get("/api/tenants")
async def list_all_tenants():
    """Lista todos los tenants disponibles (no requiere X-Org-Id)"""
    return {
        "tenants": [
            {
                "id": t.id,
                "display_name": t.display_name,
                "status": t.status,
                "environment": t.environment
            }
            for t in db.tenants.values()
        ]
    }

@app.get("/api/tenants/{tenant_id}")
async def get_tenant_details(
    tenant_id: str,
    org_id: str = Depends(require_tenant)
):
    """Obtiene detalles de un tenant (debe coincidir con X-Org-Id)"""
    
    # Verificar que el tenant solicitado coincide con el header
    if tenant_id != org_id:
        raise HTTPException(
            status_code=403,
            detail=f"Access denied to tenant '{tenant_id}'"
        )
    
    tenant = db.tenants[tenant_id]
    
    # Agregar timestamp para ETags
    response_data = {
        **tenant.dict(),
        "updated_at": datetime.now().isoformat()
    }
    
    # Generar ETag basado en tenant + timestamp
    etag = hashlib.md5(f"{tenant_id}:{datetime.now().timestamp()}".encode()).hexdigest()
    
    return Response(
        content=json.dumps(response_data, default=str),
        media_type="application/json",
        headers={"ETag": etag}
    )

@app.get("/api/dashboard/summary")
async def get_dashboard_summary(
    org_id: str = Depends(require_tenant),
    response: Response = None
):
    """Dashboard summary filtrado por tenant"""
    
    tenant = db.tenants[org_id]
    metrics = db.metrics_by_tenant.get(org_id, {})
    
    # Calcular métricas específicas del tenant
    tenant_invoices = [i for i in db.invoices.values() if i.tenant_id == org_id]
    open_invoices = [i for i in tenant_invoices if i.status == PaymentStatus.PENDING]
    overdue_invoices = [i for i in open_invoices if i.due_date < date.today()]
    
    summary = {
        "tenant": {
            "id": tenant.id,
            "display_name": tenant.display_name,
            "status": tenant.status,
            "environment": tenant.environment
        },
        "metrics": {
            "invoices": {
                "total": len(tenant_invoices),
                "open": len(open_invoices),
                "overdue": len(overdue_invoices),
                "paid": tenant.invoices_paid,
                "total_amount": sum(i.amount for i in open_invoices)
            },
            "throughput": {
                "messages_per_second": metrics.get("messages_per_second", 0),
                "webhooks_per_second": metrics.get("webhooks_per_second", 0),
                "wa_delivery_rate": metrics.get("wa_delivery_rate", 0),
                "p95_latency": metrics.get("p95_latency", 0)
            },
            "queues": {
                "depth": metrics.get("queue_depth", 0),
                "dlq_count": metrics.get("dlq_count", 0)
            },
            "catalog": {
                "size": tenant.catalog_size,
                "last_import": tenant.last_import.isoformat() if tenant.last_import else None
            },
            "customers": {
                "active": tenant.active_customers
            }
        },
        "updated_at": datetime.now().isoformat()
    }
    
    # Generar ETag único por tenant
    etag = hashlib.md5(f"{org_id}:{summary['updated_at']}".encode()).hexdigest()
    response.headers["ETag"] = etag
    response.headers["Cache-Control"] = "private, max-age=60"
    
    return summary

@app.get("/api/invoices")
async def list_invoices(
    org_id: str = Depends(require_tenant),
    status: Optional[PaymentStatus] = None,
    limit: int = Query(50, ge=1, le=500)
):
    """Lista invoices filtrados por tenant"""
    
    # Filtrar solo invoices del tenant
    invoices = [
        i for i in db.invoices.values()
        if i.tenant_id == org_id
    ]
    
    if status:
        invoices = [i for i in invoices if i.status == status]
    
    # Ordenar por fecha de vencimiento
    invoices.sort(key=lambda x: x.due_date)
    
    return {
        "invoices": [i.dict() for i in invoices[:limit]],
        "total": len(invoices),
        "tenant_id": org_id
    }

@app.get("/api/dunning/pipeline")
async def get_dunning_pipeline(
    org_id: str = Depends(require_tenant),
    simulated_date: Optional[str] = None
):
    """Pipeline de dunning filtrado por tenant"""
    
    # Time Machine
    if simulated_date:
        target_date = datetime.fromisoformat(simulated_date).date()
    else:
        target_date = date.today()
    
    # Solo invoices del tenant
    tenant_invoices = [
        i for i in db.invoices.values()
        if i.tenant_id == org_id and i.status == PaymentStatus.PENDING
    ]
    
    pipeline = {stage.value: [] for stage in DunningStage}
    
    for invoice in tenant_invoices:
        days_until_due = (invoice.due_date - target_date).days
        
        if days_until_due == 3:
            pipeline[DunningStage.T_MINUS_3.value].append(invoice.dict())
        elif days_until_due == 1:
            pipeline[DunningStage.T_MINUS_1.value].append(invoice.dict())
        elif days_until_due == 0:
            pipeline[DunningStage.DUE.value].append(invoice.dict())
        elif days_until_due == -1:
            pipeline[DunningStage.T_PLUS_1.value].append(invoice.dict())
        elif days_until_due == -3:
            pipeline[DunningStage.T_PLUS_3.value].append(invoice.dict())
        elif days_until_due == -7:
            pipeline[DunningStage.T_PLUS_7.value].append(invoice.dict())
        elif days_until_due == -15:
            pipeline[DunningStage.T_PLUS_15.value].append(invoice.dict())
        elif days_until_due <= -30:
            pipeline[DunningStage.T_PLUS_30.value].append(invoice.dict())
    
    return {
        "tenant_id": org_id,
        "simulated_date": target_date.isoformat(),
        "pipeline": pipeline,
        "summary": {
            "total": sum(len(v) for v in pipeline.values()),
            "amount": sum(sum(i["amount"] for i in v) for v in pipeline.values())
        }
    }

@app.post("/api/golden-flows/run")
async def run_golden_flow(
    flow_name: str = Body(...),
    test_mode: bool = Body(True),
    org_id: str = Depends(require_tenant)
):
    """Ejecuta golden flow para el tenant actual"""
    
    flow_id = f"FLOW-{org_id[:3].upper()}-{int(time.time())}"
    steps = []
    
    # Los steps dependen del tenant para mostrar diferencias
    tenant = db.tenants[org_id]
    
    if flow_name == "pdf_to_payment":
        steps = [
            {
                "step": "catalog_import",
                "status": "success",
                "duration_ms": random.randint(3000, 8000),
                "result": {"rows": tenant.catalog_size, "auto_map_rate": 0.85}
            },
            {
                "step": "quote_creation",
                "status": "success",
                "duration_ms": random.randint(100, 300),
                "result": {"items": 5, "total": random.uniform(1000, 5000)}
            },
            {
                "step": "payment_confirmation",
                "status": "success",
                "duration_ms": random.randint(500, 1500),
                "result": {"method": "card", "success": True}
            }
        ]
    
    return {
        "flow_id": flow_id,
        "flow_name": flow_name,
        "tenant_id": org_id,
        "status": "PASS",
        "steps": steps,
        "total_duration_ms": sum(s.get("duration_ms", 0) for s in steps)
    }

@app.get("/api/health")
async def health_check():
    """Health check global del sistema"""
    return {
        "status": "healthy",
        "timestamp": datetime.now(),
        "version": "2.0.0",
        "tenants_loaded": len(db.tenants),
        "services": {
            "api": "healthy",
            "database": "healthy",
            "groq": "healthy"
        }
    }

# ==================== DASHBOARD HTML ====================

@app.get("/control-tower-v2", response_class=HTMLResponse)
async def serve_dashboard():
    """Sirve el dashboard V2 con contexto de tenant"""
    
    dashboard_path = Path(__file__).parent / "control_tower_dashboard_v2.html"
    
    if dashboard_path.exists():
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    
    # Dashboard inline si no existe el archivo
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Control Tower V2</title>
    </head>
    <body>
        <h1>Control Tower V2</h1>
        <p>Create control_tower_dashboard_v2.html for the full experience</p>
    </body>
    </html>
    """)

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🎮 ORKESTA CONTROL TOWER V2")
    print("   Multi-tenant con Aislamiento Completo")
    print("="*60)
    print("\n📊 Sistema con contexto de tenant aislado")
    print("🔒 Requiere header X-Org-Id en todas las llamadas")
    print("\n✨ 3 Tenants Cargados:")
    print("   - equipo-automotriz-javaz (Production)")
    print("   - lb-productions (Production)")
    print("   - clinica-salud-plus (Trial)")
    print("\n📍 Access Points:")
    print("   - Dashboard: http://localhost:8002/control-tower-v2")
    print("   - API Docs: http://localhost:8002/docs")
    print("   - Health: http://localhost:8002/api/health")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8002)