"""
📊 CONTROL TOWER ENHANCED API - Dashboard con TODA la información
===============================================================

API mejorada del Control Tower con datos mucho más detallados:
- Métricas de agentes inteligentes
- Estado del contexto compartido
- Análisis de Stripe Connect
- Flujos de conversación
- Sugerencias de agentes
- Telemetría completa
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

# Imports de nuestros módulos
from orkesta_shared_context import get_shared_context, context_manager
from orkesta_smart_agents import orchestrator
from orkesta_stripe.connect import connect_manager
from orkesta_stripe.checkout import checkout_orchestrator
from orkesta_stripe.fees import fee_calculator
from orkesta_stripe.webhooks import webhook_processor
from orkesta_stripe.types import ChargesMode, PaymentMethod

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
    return tenant_id

# ==================== APLICACIÓN ====================

app = FastAPI(
    title="Orkesta Control Tower Enhanced",
    description="Dashboard empresarial con información completa del sistema",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==================== DATOS DEMO AVANZADOS ====================

def generate_enhanced_demo_data():
    """Genera datos demo súper completos"""
    
    tenants_data = {
        "equipo-automotriz-javaz": {
            "display_name": "Equipo Automotriz JAvaz",
            "industry": "Automotriz",
            "plan": "Enterprise",
            "status": "active",
            "created_at": "2024-06-15",
            "mrr": 12500.00,
            "usage": {
                "messages_sent": 45230,
                "orders_processed": 1247,
                "catalog_size": 2340,
                "active_customers": 423,
                "ai_calls": 8934,
                "storage_mb": 1450
            },
            "features": {
                "ai_agents": True,
                "stripe_connect": True,
                "voice_assistant": True,
                "advanced_analytics": True,
                "whatsapp_api": True,
                "telegram_api": False
            },
            "health": {
                "uptime_pct": 99.8,
                "avg_response_time": 234,
                "error_rate": 0.02,
                "last_incident": "2025-07-28"
            },
            "team": {
                "users": 8,
                "admins": 2,
                "api_keys": 3,
                "webhooks": 5
            }
        },
        "lb-productions": {
            "display_name": "LB Productions",
            "industry": "Media & Entertainment",
            "plan": "Professional",
            "status": "active",
            "created_at": "2024-09-20",
            "mrr": 4200.00,
            "usage": {
                "messages_sent": 18950,
                "orders_processed": 289,
                "catalog_size": 156,
                "active_customers": 89,
                "ai_calls": 3421,
                "storage_mb": 678
            },
            "features": {
                "ai_agents": True,
                "stripe_connect": True,
                "voice_assistant": False,
                "advanced_analytics": True,
                "whatsapp_api": True,
                "telegram_api": True
            },
            "health": {
                "uptime_pct": 99.9,
                "avg_response_time": 189,
                "error_rate": 0.01,
                "last_incident": "2025-06-12"
            },
            "team": {
                "users": 3,
                "admins": 1,
                "api_keys": 2,
                "webhooks": 3
            }
        },
        "clinica-salud-plus": {
            "display_name": "Clínica Salud Plus",
            "industry": "Healthcare",
            "plan": "Starter",
            "status": "trial",
            "created_at": "2025-01-02",
            "mrr": 850.00,
            "usage": {
                "messages_sent": 5678,
                "orders_processed": 156,
                "catalog_size": 340,
                "active_customers": 67,
                "ai_calls": 1234,
                "storage_mb": 234
            },
            "features": {
                "ai_agents": True,
                "stripe_connect": False,
                "voice_assistant": False,
                "advanced_analytics": False,
                "whatsapp_api": True,
                "telegram_api": False
            },
            "health": {
                "uptime_pct": 98.5,
                "avg_response_time": 267,
                "error_rate": 0.05,
                "last_incident": "2025-08-10"
            },
            "team": {
                "users": 2,
                "admins": 1,
                "api_keys": 1,
                "webhooks": 2
            }
        }
    }
    
    return tenants_data

DEMO_DATA = generate_enhanced_demo_data()

# ==================== ENDPOINTS PRINCIPALES ====================

@app.get("/api/tenants")
async def list_all_tenants():
    """Lista todos los tenants con información básica"""
    return {
        "tenants": [
            {
                "id": tenant_id,
                "display_name": data["display_name"],
                "industry": data["industry"],
                "plan": data["plan"],
                "status": data["status"],
                "mrr": data["mrr"]
            }
            for tenant_id, data in DEMO_DATA.items()
        ]
    }

@app.get("/api/dashboard/overview")
async def get_dashboard_overview(org_id: str = Depends(require_tenant)):
    """Dashboard overview súper completo"""
    
    if org_id not in DEMO_DATA:
        raise HTTPException(status_code=404, detail=f"Tenant {org_id} not found")
    
    tenant_data = DEMO_DATA[org_id]
    
    # Obtener contexto compartido
    ctx = get_shared_context(org_id)
    
    # Métricas de agentes
    pending_suggestions = orchestrator.get_pending_suggestions(org_id)
    
    # Métricas de tiempo real (simuladas)
    realtime_metrics = {
        "current_active_sessions": random.randint(3, 15),
        "messages_last_hour": random.randint(45, 120),
        "orders_last_hour": random.randint(2, 8),
        "ai_calls_last_hour": random.randint(20, 60),
        "revenue_last_hour": random.uniform(500, 2500),
        "queue_depth": random.randint(0, 25),
        "avg_response_time_ms": random.randint(150, 400),
        "error_count_last_hour": random.randint(0, 3),
        "webhook_events_pending": random.randint(0, 5)
    }
    
    # Breakdown de uso por feature
    feature_usage = {
        "ai_chat": {
            "calls_today": random.randint(50, 200),
            "avg_response_time": random.randint(800, 1500),
            "tokens_consumed": random.randint(50000, 150000),
            "cost_today": random.uniform(15, 45)
        },
        "stripe_connect": {
            "transactions_today": random.randint(5, 25),
            "volume_today": random.uniform(2000, 15000),
            "fees_collected": random.uniform(50, 300),
            "failed_payments": random.randint(0, 3)
        },
        "whatsapp_api": {
            "messages_sent": random.randint(80, 300),
            "delivery_rate": random.uniform(0.95, 0.99),
            "cost_today": random.uniform(8, 25),
            "template_approvals": random.randint(0, 2)
        }
    }
    
    # Análisis de crecimiento
    growth_metrics = {
        "mrr_growth": random.uniform(-5, 25),
        "customer_growth": random.uniform(0, 15),
        "usage_growth": random.uniform(-10, 30),
        "churn_risk": random.uniform(0, 15)
    }
    
    # Top productos/servicios
    top_products = [
        {"name": "Tubo PVC 3/4\"", "orders": 45, "revenue": 3825.00},
        {"name": "Cable calibre 12", "orders": 32, "revenue": 2140.50},
        {"name": "Cemento Portland", "orders": 28, "revenue": 4200.00},
        {"name": "Varilla 3/8\"", "orders": 22, "revenue": 1980.75},
        {"name": "Pintura vinílica", "orders": 18, "revenue": 1575.25}
    ]
    
    # Alertas y notificaciones
    alerts = []
    
    if realtime_metrics["error_count_last_hour"] > 2:
        alerts.append({
            "type": "warning",
            "title": "Errores elevados",
            "message": f"{realtime_metrics['error_count_last_hour']} errores en la última hora",
            "action": "review_logs"
        })
    
    if tenant_data["health"]["uptime_pct"] < 99.5:
        alerts.append({
            "type": "critical",
            "title": "Uptime bajo",
            "message": f"Uptime: {tenant_data['health']['uptime_pct']}%",
            "action": "check_infrastructure"
        })
    
    if len(pending_suggestions) > 5:
        alerts.append({
            "type": "info",
            "title": "Sugerencias de agentes",
            "message": f"{len(pending_suggestions)} sugerencias pendientes de revisión",
            "action": "review_suggestions"
        })
    
    overview = {
        "tenant": {
            "id": org_id,
            "display_name": tenant_data["display_name"],
            "industry": tenant_data["industry"],
            "plan": tenant_data["plan"],
            "status": tenant_data["status"],
            "created_at": tenant_data["created_at"],
            "days_active": (datetime.now() - datetime.fromisoformat(tenant_data["created_at"])).days
        },
        "financial": {
            "mrr": tenant_data["mrr"],
            "revenue_today": realtime_metrics["revenue_last_hour"] * 24,
            "revenue_mtd": tenant_data["mrr"] * 0.8,  # Estimado
            "growth_rate": growth_metrics["mrr_growth"],
            "churn_risk": growth_metrics["churn_risk"]
        },
        "usage": {
            **tenant_data["usage"],
            "usage_growth": growth_metrics["usage_growth"],
            "storage_usage_pct": (tenant_data["usage"]["storage_mb"] / 2000) * 100,
            "plan_limits": {
                "messages_monthly": 100000 if tenant_data["plan"] == "Enterprise" else 50000,
                "ai_calls_monthly": 20000 if tenant_data["plan"] == "Enterprise" else 10000,
                "storage_gb": 5 if tenant_data["plan"] == "Enterprise" else 2
            }
        },
        "realtime": realtime_metrics,
        "feature_usage": feature_usage,
        "health": {
            **tenant_data["health"],
            "status": "healthy" if tenant_data["health"]["uptime_pct"] > 99.5 else "degraded",
            "incidents_mtd": random.randint(0, 2)
        },
        "team": tenant_data["team"],
        "features": tenant_data["features"],
        "top_products": top_products,
        "ai_agents": {
            "total_suggestions": len(ctx.agent_suggestions),
            "pending_suggestions": len(pending_suggestions),
            "auto_approved_today": random.randint(5, 15),
            "confidence_avg": random.uniform(0.7, 0.95)
        },
        "alerts": alerts,
        "context_stats": {
            "products_count": len(ctx.catalog["products"]),
            "clients_count": len(ctx.clients),
            "orders_count": len(ctx.orders),
            "context_version": ctx.version,
            "last_updated": datetime.now().isoformat()
        },
        "updated_at": datetime.now().isoformat()
    }
    
    return overview

@app.get("/api/dashboard/agents")
async def get_agents_dashboard(org_id: str = Depends(require_tenant)):
    """Dashboard específico de agentes inteligentes"""
    
    ctx = get_shared_context(org_id)
    suggestions = orchestrator.get_pending_suggestions(org_id)
    
    # Simular métricas de cada agente
    agents_metrics = {
        "CatalogMapper": {
            "suggestions_total": random.randint(15, 45),
            "suggestions_approved": random.randint(12, 40),
            "avg_confidence": random.uniform(0.85, 0.95),
            "processing_time_avg": random.randint(1200, 3000),
            "last_active": datetime.now() - timedelta(minutes=random.randint(5, 60)),
            "success_rate": random.uniform(0.88, 0.97)
        },
        "AliasNormalizer": {
            "duplicates_detected": random.randint(8, 25),
            "duplicates_merged": random.randint(6, 20),
            "units_normalized": random.randint(12, 30),
            "avg_confidence": random.uniform(0.78, 0.92),
            "last_active": datetime.now() - timedelta(minutes=random.randint(10, 120)),
            "success_rate": random.uniform(0.82, 0.94)
        },
        "PriceResolver": {
            "price_calculations": random.randint(234, 678),
            "discounts_applied": random.randint(45, 156),
            "overrides_suggested": random.randint(3, 12),
            "avg_response_time": random.randint(45, 150),
            "last_active": datetime.now() - timedelta(minutes=random.randint(1, 30)),
            "accuracy_rate": random.uniform(0.94, 0.99)
        },
        "QuoteBuilder": {
            "quotes_generated": random.randint(34, 89),
            "conversion_rate": random.uniform(0.65, 0.85),
            "avg_items_per_quote": random.uniform(3.2, 6.8),
            "extraction_accuracy": random.uniform(0.88, 0.96),
            "last_active": datetime.now() - timedelta(minutes=random.randint(2, 45)),
            "completeness_score": random.uniform(0.85, 0.94)
        }
    }
    
    # Sugerencias por tipo
    suggestions_by_type = {}
    for suggestion in suggestions:
        stype = suggestion["type"]
        if stype not in suggestions_by_type:
            suggestions_by_type[stype] = []
        suggestions_by_type[stype].append(suggestion)
    
    # Actividad reciente de agentes
    recent_activity = [
        {
            "agent": "PriceResolver",
            "action": "Aplicó descuento VIP a cliente premium",
            "timestamp": datetime.now() - timedelta(minutes=5),
            "result": "success",
            "impact": "Descuento $150 aplicado"
        },
        {
            "agent": "QuoteBuilder", 
            "action": "Generó cotización desde chat",
            "timestamp": datetime.now() - timedelta(minutes=12),
            "result": "success",
            "impact": "5 productos, $2,340 total"
        },
        {
            "agent": "AliasNormalizer",
            "action": "Detectó productos duplicados",
            "timestamp": datetime.now() - timedelta(minutes=25),
            "result": "pending_review",
            "impact": "3 productos similares encontrados"
        },
        {
            "agent": "CatalogMapper",
            "action": "Mapeó importación Excel",
            "timestamp": datetime.now() - timedelta(hours=1),
            "result": "success", 
            "impact": "150 productos importados (85% auto-map)"
        }
    ]
    
    return {
        "agents_overview": {
            "total_agents": len(agents_metrics),
            "active_agents": sum(1 for m in agents_metrics.values() if (datetime.now() - m["last_active"]).seconds < 3600),
            "total_suggestions": len(ctx.agent_suggestions),
            "pending_suggestions": len(suggestions),
            "avg_confidence": sum(m["avg_confidence"] for m in agents_metrics.values()) / len(agents_metrics)
        },
        "agents_metrics": agents_metrics,
        "suggestions": {
            "by_type": suggestions_by_type,
            "recent": suggestions[-10:] if suggestions else [],
            "high_confidence": [s for s in suggestions if s.get("confidence", 0) > 0.9]
        },
        "recent_activity": recent_activity,
        "performance": {
            "total_actions_24h": sum(
                random.randint(10, 50) for _ in agents_metrics
            ),
            "success_rate_24h": random.uniform(0.92, 0.98),
            "avg_processing_time": random.randint(800, 1500),
            "cost_per_action": random.uniform(0.05, 0.15)
        },
        "context_health": {
            "version": ctx.version,
            "products": len(ctx.catalog["products"]),
            "clients": len(ctx.clients),
            "orders": len(ctx.orders),
            "suggestions": len(ctx.agent_suggestions),
            "last_context_update": datetime.now().isoformat()
        }
    }

@app.get("/api/dashboard/stripe")
async def get_stripe_dashboard(org_id: str = Depends(require_tenant)):
    """Dashboard específico de Stripe Connect"""
    
    # Simular datos de Stripe Connect
    stripe_accounts = 1  # Simular 1 cuenta por tenant
    
    # Métricas financieras
    financial_metrics = {
        "volume_24h": random.uniform(5000, 25000),
        "volume_mtd": random.uniform(50000, 250000),
        "transactions_24h": random.randint(15, 75),
        "transactions_mtd": random.randint(150, 750),
        "avg_transaction": random.uniform(200, 800),
        "conversion_rate": random.uniform(0.85, 0.95),
        "refund_rate": random.uniform(0.02, 0.08)
    }
    
    # Fees breakdown
    fees_analysis = {
        "stripe_fees_24h": financial_metrics["volume_24h"] * 0.036 + (financial_metrics["transactions_24h"] * 3),
        "app_fees_24h": financial_metrics["volume_24h"] * 0.008,  # 0.8% app fee
        "connect_costs_monthly": 35 + (financial_metrics["volume_mtd"] * 0.0025) + (financial_metrics["transactions_mtd"] * 0.25),
        "net_revenue_24h": financial_metrics["volume_24h"] * 0.008 - (financial_metrics["volume_24h"] * 0.036),
    }
    
    # Métodos de pago breakdown
    payment_methods = {
        "card": {
            "volume_pct": random.uniform(60, 80),
            "transactions": int(financial_metrics["transactions_24h"] * random.uniform(0.6, 0.8)),
            "avg_fee_rate": 3.6,
            "success_rate": random.uniform(0.92, 0.97)
        },
        "oxxo": {
            "volume_pct": random.uniform(15, 25),
            "transactions": int(financial_metrics["transactions_24h"] * random.uniform(0.15, 0.25)),
            "avg_fee_rate": 3.6,
            "success_rate": random.uniform(0.88, 0.94)
        },
        "spei": {
            "volume_pct": random.uniform(5, 15),
            "transactions": int(financial_metrics["transactions_24h"] * random.uniform(0.05, 0.15)),
            "avg_fee_rate": 2.5,
            "success_rate": random.uniform(0.94, 0.99)
        }
    }
    
    # Transacciones recientes (simuladas)
    recent_transactions = []
    for i in range(10):
        amount = random.uniform(100, 3000)
        method = random.choice(["card", "oxxo", "spei"])
        status = random.choice(["succeeded", "succeeded", "succeeded", "pending", "failed"])
        
        recent_transactions.append({
            "id": f"pi_test_{int(time.time())}_{i}",
            "amount": amount,
            "currency": "MXN",
            "method": method,
            "status": status,
            "customer": f"Customer #{random.randint(100, 999)}",
            "created": datetime.now() - timedelta(minutes=random.randint(5, 1440)),
            "fees": amount * 0.036 + 3 if method == "card" else amount * 0.025 + 5
        })
    
    # Webhook events
    webhook_events = [
        {
            "type": "payment_intent.succeeded",
            "count_24h": random.randint(45, 120),
            "last_received": datetime.now() - timedelta(minutes=random.randint(5, 60)),
            "processing_time_avg": random.randint(150, 500)
        },
        {
            "type": "charge.refunded",
            "count_24h": random.randint(1, 8),
            "last_received": datetime.now() - timedelta(hours=random.randint(1, 12)),
            "processing_time_avg": random.randint(200, 400)
        },
        {
            "type": "payout.paid",
            "count_24h": random.randint(0, 2),
            "last_received": datetime.now() - timedelta(hours=random.randint(12, 48)),
            "processing_time_avg": random.randint(300, 600)
        }
    ]
    
    # Health checks
    health_status = {
        "api_status": "operational",
        "webhook_delivery": random.uniform(0.95, 0.99),
        "avg_response_time": random.randint(150, 400),
        "error_rate_24h": random.uniform(0.01, 0.05),
        "last_incident": datetime.now() - timedelta(days=random.randint(5, 30))
    }
    
    return {
        "stripe_overview": {
            "accounts_connected": stripe_accounts,
            "capabilities_active": ["card_payments", "transfers", "oxxo_payments"],
            "onboarding_complete": True,
            "charges_mode": "direct",
            "environment": "sandbox"
        },
        "financial": financial_metrics,
        "fees": {
            **fees_analysis,
            "effective_rate": (fees_analysis["stripe_fees_24h"] / financial_metrics["volume_24h"]) * 100,
            "margin_rate": (fees_analysis["net_revenue_24h"] / financial_metrics["volume_24h"]) * 100
        },
        "payment_methods": payment_methods,
        "recent_transactions": recent_transactions,
        "webhooks": {
            "events": webhook_events,
            "total_events_24h": sum(e["count_24h"] for e in webhook_events),
            "processing_health": "good" if all(e["processing_time_avg"] < 1000 for e in webhook_events) else "slow"
        },
        "health": health_status,
        "recommendations": [
            "Considerar activar SPEI para reducir fees" if payment_methods["spei"]["volume_pct"] < 10 else None,
            "Revisar tasa de refunds elevada" if financial_metrics["refund_rate"] > 0.06 else None,
            "Optimizar webhooks - tiempo de procesamiento alto" if any(e["processing_time_avg"] > 800 for e in webhook_events) else None
        ]
    }

@app.get("/api/dashboard/conversations")
async def get_conversations_dashboard(org_id: str = Depends(require_tenant)):
    """Dashboard de conversaciones y chat"""
    
    # Métricas de conversaciones
    conv_metrics = {
        "total_conversations": random.randint(45, 120),
        "active_conversations": random.randint(8, 25),
        "completed_conversations": random.randint(35, 95),
        "avg_conversation_length": random.randint(8, 20),
        "avg_response_time": random.randint(1.2, 4.5),
        "resolution_rate": random.uniform(0.78, 0.92),
        "customer_satisfaction": random.uniform(4.1, 4.8)
    }
    
    # Breakdown por canal
    channels = {
        "whatsapp": {
            "conversations": int(conv_metrics["total_conversations"] * 0.6),
            "avg_response_time": random.uniform(45, 120),
            "delivery_rate": random.uniform(0.94, 0.98),
            "engagement_rate": random.uniform(0.65, 0.85)
        },
        "web_chat": {
            "conversations": int(conv_metrics["total_conversations"] * 0.3),
            "avg_response_time": random.uniform(30, 90),
            "delivery_rate": 0.99,
            "engagement_rate": random.uniform(0.70, 0.90)
        },
        "telegram": {
            "conversations": int(conv_metrics["total_conversations"] * 0.1),
            "avg_response_time": random.uniform(60, 150),
            "delivery_rate": random.uniform(0.92, 0.96),
            "engagement_rate": random.uniform(0.60, 0.80)
        }
    }
    
    # Intents más frecuentes
    top_intents = [
        {"intent": "product_search", "count": random.randint(45, 89), "success_rate": random.uniform(0.85, 0.95)},
        {"intent": "price_inquiry", "count": random.randint(32, 67), "success_rate": random.uniform(0.90, 0.98)},
        {"intent": "quotation_request", "count": random.randint(28, 54), "success_rate": random.uniform(0.75, 0.88)},
        {"intent": "order_status", "count": random.randint(22, 43), "success_rate": random.uniform(0.88, 0.95)},
        {"intent": "complaint", "count": random.randint(8, 18), "success_rate": random.uniform(0.60, 0.80)},
        {"intent": "support", "count": random.randint(15, 32), "success_rate": random.uniform(0.70, 0.85)}
    ]
    
    # Conversaciones recientes activas
    active_conversations = []
    for i in range(8):
        last_message = datetime.now() - timedelta(minutes=random.randint(1, 30))
        
        active_conversations.append({
            "id": f"conv_{random.randint(1000, 9999)}",
            "customer": f"Cliente #{random.randint(100, 999)}",
            "channel": random.choice(["whatsapp", "web_chat", "telegram"]),
            "status": random.choice(["active", "waiting_customer", "waiting_agent"]),
            "last_message": last_message,
            "duration_minutes": random.randint(5, 45),
            "message_count": random.randint(4, 20),
            "current_intent": random.choice([i["intent"] for i in top_intents]),
            "agent_assigned": random.choice(["AI", "Human", "Hybrid"])
        })
    
    # Escalations
    escalations = {
        "total_24h": random.randint(3, 12),
        "to_human": random.randint(2, 8),
        "to_supervisor": random.randint(0, 3),
        "common_reasons": [
            {"reason": "Complex pricing inquiry", "count": random.randint(2, 5)},
            {"reason": "Complaint handling", "count": random.randint(1, 4)},
            {"reason": "Technical issue", "count": random.randint(0, 2)},
            {"reason": "Custom quotation", "count": random.randint(1, 3)}
        ]
    }
    
    # Performance por agente
    ai_performance = {
        "resolution_rate": random.uniform(0.75, 0.88),
        "escalation_rate": random.uniform(0.08, 0.18),
        "customer_satisfaction": random.uniform(4.0, 4.6),
        "avg_handling_time": random.uniform(3.5, 8.2),
        "cost_per_conversation": random.uniform(0.15, 0.45)
    }
    
    return {
        "overview": conv_metrics,
        "channels": channels,
        "intents": {
            "top_intents": top_intents,
            "intent_distribution": {intent["intent"]: intent["count"] for intent in top_intents},
            "avg_confidence": random.uniform(0.82, 0.94)
        },
        "active_conversations": active_conversations,
        "escalations": escalations,
        "ai_performance": ai_performance,
        "trends": {
            "conversation_volume_trend": random.uniform(-5, 25),
            "resolution_rate_trend": random.uniform(-2, 8),
            "satisfaction_trend": random.uniform(-0.1, 0.3),
            "response_time_trend": random.uniform(-15, 5)
        },
        "recommendations": [
            "Entrenar IA en manejo de quejas" if ai_performance["escalation_rate"] > 0.15 else None,
            "Optimizar respuestas para WhatsApp" if channels["whatsapp"]["avg_response_time"] > 90 else None,
            "Revisar intent classification" if any(i["success_rate"] < 0.8 for i in top_intents) else None
        ]
    }

@app.get("/api/dashboard/system")
async def get_system_dashboard(org_id: str = Depends(require_tenant)):
    """Dashboard de sistema y telemetría"""
    
    # Métricas de infraestructura
    infrastructure = {
        "api_uptime": random.uniform(99.5, 99.9),
        "database_performance": {
            "query_time_avg": random.uniform(25, 85),
            "connection_pool": f"{random.randint(8, 15)}/20",
            "cache_hit_rate": random.uniform(0.85, 0.95)
        },
        "memory_usage": {
            "used_mb": random.randint(512, 1024),
            "total_mb": 2048,
            "usage_pct": random.uniform(25, 50)
        },
        "cpu_usage": {
            "current_pct": random.uniform(15, 45),
            "avg_24h": random.uniform(20, 35),
            "peak_24h": random.uniform(60, 85)
        }
    }
    
    # Logs y errores
    logging_metrics = {
        "total_logs_24h": random.randint(15000, 45000),
        "error_logs_24h": random.randint(25, 120),
        "warning_logs_24h": random.randint(180, 450),
        "critical_logs_24h": random.randint(0, 5),
        "log_levels": {
            "info": random.uniform(0.75, 0.85),
            "warning": random.uniform(0.10, 0.18),
            "error": random.uniform(0.02, 0.08),
            "critical": random.uniform(0, 0.02)
        }
    }
    
    # APIs externas
    external_apis = {
        "groq": {
            "status": "operational",
            "response_time": random.randint(300, 800),
            "calls_24h": random.randint(234, 567),
            "error_rate": random.uniform(0.01, 0.05),
            "quota_used": random.uniform(0.4, 0.8)
        },
        "stripe": {
            "status": "operational",
            "response_time": random.randint(150, 400),
            "calls_24h": random.randint(89, 234),
            "error_rate": random.uniform(0.005, 0.02),
            "quota_used": random.uniform(0.1, 0.3)
        },
        "whatsapp": {
            "status": random.choice(["operational", "degraded"]),
            "response_time": random.randint(200, 600),
            "calls_24h": random.randint(145, 389),
            "error_rate": random.uniform(0.02, 0.08),
            "quota_used": random.uniform(0.3, 0.7)
        }
    }
    
    # Backups y seguridad
    backup_security = {
        "last_backup": datetime.now() - timedelta(hours=random.randint(1, 6)),
        "backup_size_mb": random.randint(250, 500),
        "backup_status": "success",
        "failed_login_attempts": random.randint(0, 8),
        "api_rate_limits": {
            "current_requests_min": random.randint(45, 120),
            "limit_requests_min": 1000,
            "throttled_requests": random.randint(0, 5)
        },
        "ssl_certificate": {
            "status": "valid",
            "expires": datetime.now() + timedelta(days=random.randint(60, 300))
        }
    }
    
    # Alerts activas
    active_alerts = []
    
    if infrastructure["cpu_usage"]["current_pct"] > 80:
        active_alerts.append({
            "level": "warning",
            "component": "CPU",
            "message": f"CPU usage high: {infrastructure['cpu_usage']['current_pct']:.1f}%",
            "since": datetime.now() - timedelta(minutes=random.randint(5, 30))
        })
    
    if external_apis["whatsapp"]["status"] == "degraded":
        active_alerts.append({
            "level": "warning",
            "component": "WhatsApp API",
            "message": "Degraded performance detected",
            "since": datetime.now() - timedelta(minutes=random.randint(10, 60))
        })
    
    if logging_metrics["critical_logs_24h"] > 0:
        active_alerts.append({
            "level": "critical",
            "component": "Application",
            "message": f"{logging_metrics['critical_logs_24h']} critical errors in 24h",
            "since": datetime.now() - timedelta(hours=random.randint(1, 12))
        })
    
    return {
        "infrastructure": infrastructure,
        "logging": logging_metrics,
        "external_apis": external_apis,
        "backup_security": backup_security,
        "active_alerts": active_alerts,
        "performance_trends": {
            "response_time_trend": random.uniform(-10, 15),
            "error_rate_trend": random.uniform(-20, 10),
            "uptime_trend": random.uniform(-0.1, 0.2),
            "throughput_trend": random.uniform(-5, 20)
        },
        "capacity_planning": {
            "current_capacity_usage": random.uniform(0.4, 0.7),
            "projected_growth": random.uniform(0.1, 0.3),
            "scale_up_trigger": 0.8,
            "recommendations": [
                "Consider adding cache layer" if infrastructure["database_performance"]["cache_hit_rate"] < 0.9 else None,
                "Monitor CPU usage closely" if infrastructure["cpu_usage"]["current_pct"] > 40 else None,
                "Review API quotas" if any(api["quota_used"] > 0.7 for api in external_apis.values()) else None
            ]
        }
    }

# ==================== DASHBOARD HTML ====================

@app.get("/control-tower-enhanced", response_class=HTMLResponse)
async def serve_enhanced_dashboard():
    """Sirve el dashboard enhanced HTML"""
    
    dashboard_path = Path(__file__).parent / "control_tower_enhanced_dashboard.html"
    
    if dashboard_path.exists():
        with open(dashboard_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    
    # Dashboard básico si no existe el archivo
    return HTMLResponse(content="""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Orkesta Control Tower Enhanced</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #0a0e27; color: white; }
            .container { max-width: 1200px; margin: 0 auto; }
            .card { background: #1e2341; padding: 20px; margin: 20px 0; border-radius: 8px; border: 1px solid #2d3561; }
            h1 { color: #3b82f6; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 Orkesta Control Tower Enhanced</h1>
            <div class="card">
                <h2>Dashboard Mejorado</h2>
                <p>El dashboard enhanced está siendo construido...</p>
                <p><strong>APIs disponibles:</strong></p>
                <ul>
                    <li>GET /api/dashboard/overview - Vista general completa</li>
                    <li>GET /api/dashboard/agents - Dashboard de agentes IA</li>
                    <li>GET /api/dashboard/stripe - Dashboard de Stripe Connect</li>
                    <li>GET /api/dashboard/conversations - Dashboard de conversaciones</li>
                    <li>GET /api/dashboard/system - Telemetría de sistema</li>
                </ul>
                <p>Para el dashboard completo, crea el archivo control_tower_enhanced_dashboard.html</p>
            </div>
        </div>
    </body>
    </html>
    """)

# ==================== MAIN ====================

if __name__ == "__main__":
    import uvicorn
    
    print("\\n" + "="*70)
    print("📊 ORKESTA CONTROL TOWER ENHANCED")
    print("   Dashboard empresarial con información COMPLETA")
    print("="*70)
    print("\\n🚀 Características:")
    print("   📈 Métricas financieras detalladas")
    print("   🤖 Estado de agentes inteligentes")
    print("   💳 Analytics de Stripe Connect completo")
    print("   💬 Dashboard de conversaciones")
    print("   🔧 Telemetría de sistema")
    print("   📊 Alertas y recomendaciones")
    print("\\n📍 Access Points:")
    print("   - Enhanced Dashboard: http://localhost:8003/control-tower-enhanced")
    print("   - Overview API: http://localhost:8003/api/dashboard/overview")
    print("   - Agents API: http://localhost:8003/api/dashboard/agents")
    print("   - Stripe API: http://localhost:8003/api/dashboard/stripe")
    print("   - Conversations API: http://localhost:8003/api/dashboard/conversations")
    print("   - System API: http://localhost:8003/api/dashboard/system")
    print("   - API Docs: http://localhost:8003/docs")
    print("="*70 + "\\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8003)