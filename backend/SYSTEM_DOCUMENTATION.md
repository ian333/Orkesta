# 📚 Documentación Completa del Sistema Orkesta/ClienteOS

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────┐
│                     CONTROL TOWER (8001)                     │
│  Dashboard Multi-tenant Empresarial - Gestión y Telemetría   │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                   API PRINCIPAL (8000)                       │
│     Cliente Groq - Chat IA - Ventas - Catálogo              │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                    AGENTES INTELIGENTES                      │
│  Orchestrator - Catalog - Sales - Dunning - Quotation       │
└─────────────────────────────────────────────────────────────┘
                              ↕
┌─────────────────────────────────────────────────────────────┐
│                         SERVICIOS                            │
│   Groq LLM - WhatsApp - Telegram - Stripe - Webhooks        │
└─────────────────────────────────────────────────────────────┘
```

## 📁 Estructura de Directorios

```
/clienteos/backend/
├── 📂 agents/                    # Agentes antiguos (legacy)
│   ├── catalog_agent.py          # Búsqueda de productos simple
│   └── sales_agent.py            # Conversación de ventas básica
│
├── 📂 orkesta_agents/            # Agentes con LangChain
│   ├── __init__.py
│   ├── orchestrator.py           # Orquestador principal con intents
│   ├── catalog_agent.py          # Búsqueda inteligente con Groq
│   └── sales_agent.py            # Ventas conversacionales con memoria
│
├── 📂 auth_system/               # Sistema de autenticación
│   └── (vacío actualmente)
│
├── 📂 payment_system/            # Sistema de pagos
│   └── (vacío actualmente)
│
├── 📂 test_audio/                # Archivos de audio de prueba
│   └── README.md
│
├── 📄 API Servers
│   ├── api_server.py             # Server principal con Azure/LangChain
│   ├── api_server_groq.py        # Server optimizado con Groq
│   └── control_tower_api.py      # API del Control Tower empresarial
│
├── 📄 Dashboards HTML
│   ├── dashboard_advanced.html   # Dashboard con gestión de conversaciones
│   ├── dashboard_enhanced.html   # Dashboard mejorado con métricas
│   └── control_tower_dashboard.html # Control Tower empresarial
│
├── 📄 Sistemas Core
│   ├── orkesta_multi_agent.py    # Sistema multi-agente completo
│   ├── orkesta_agents_groq.py    # Sistema optimizado para Groq
│   ├── llm_fallback_system.py    # Sistema de fallback inteligente
│   └── groq_simple_test.py       # Test simple de Groq
│
├── 📄 Tests y Utilidades
│   ├── test_scenarios.py         # Suite completa de pruebas
│   ├── test_groq.py              # Pruebas de Groq
│   ├── test_agents_direct.py     # Test directo de agentes
│   ├── test_complete_system.py   # Test del sistema completo
│   └── test_orkesta_e2e.py       # Test end-to-end
│
├── 📄 Documentación
│   ├── DOCUMENTATION.md          # Índice de documentación
│   ├── LANGCHAIN_RESEARCH.md     # Investigación de LangChain
│   ├── LLM_FALLBACK_RESEARCH.md  # Investigación de fallback
│   └── SYSTEM_DOCUMENTATION.md   # Este archivo
│
└── 📄 Configuración
    ├── .env.groq                  # API keys de Groq
    ├── requirements.txt           # Dependencias Python
    └── models.py                  # Modelos de datos

```

## 🤖 Agentes del Sistema

### 1. **OrchestratorAgent** (orkesta_agents/orchestrator.py)
- **Propósito**: Analizar intención y enrutar a agente especializado
- **LLM**: Groq Llama 3.1 8B
- **Herramientas**:
  - `analyze_intent`: Detecta intención del usuario
  - `get_customer_context`: Obtiene contexto del cliente
  - `route_to_agent`: Enruta al agente apropiado
- **Intents detectados**: greeting, product_search, purchase, quotation, complaint, support

### 2. **CatalogAgent** (orkesta_agents/catalog_agent.py)
- **Propósito**: Búsqueda inteligente de productos
- **LLM**: Groq Gemma 2 9B
- **Capacidades**:
  - Búsqueda fuzzy con tolerancia a errores
  - Detección de sinónimos y variantes
  - Recomendaciones basadas en contexto
  - Normalización de unidades y medidas

### 3. **SalesAgent** (orkesta_agents/sales_agent.py)
- **Propósito**: Gestión completa del proceso de venta
- **LLM**: Groq Llama 3.3 70B
- **Estados**: greeting → discovery → proposal → negotiation → closing → completed
- **Herramientas**:
  - `buscar_productos`: Búsqueda en catálogo
  - `crear_cotizacion`: Genera cotizaciones
  - `aplicar_descuento`: Gestiona descuentos
  - `generar_link_pago`: Crea links de pago
  - `procesar_pago`: Confirma pagos

### 4. **DunningAgent** (Por implementar)
- **Propósito**: Cobranza automatizada
- **Capacidades planeadas**:
  - Recordatorios en T-3, T-1, T+1, T+3
  - Fallback automático entre canales
  - Personalización de mensajes
  - A/B testing de horarios

### 5. **QuotationAgent** (Por implementar)
- **Propósito**: Generación de cotizaciones
- **Capacidades planeadas**:
  - Cálculo automático de totales
  - Descuentos por volumen
  - Vigencia configurable
  - Exportación PDF/Excel

## 📊 Tablas y Modelos de Datos

### Tabla: **tenants**
```python
{
    "id": str,                    # Slug único (equipo-automotriz-javaz)
    "display_name": str,          # Nombre para UI
    "status": str,                # active, trial, suspended, churned
    "environment": str,           # sandbox, production
    "created_at": datetime,
    "whatsapp": {
        "status": str,            # sandbox, production, inactive
        "templates": int,         # Número de plantillas aprobadas
        "phone": str              # Número de WhatsApp Business
    },
    "telegram": {
        "status": str,
        "bot_token": str
    },
    "psp": {                      # Payment Service Provider
        "status": str,            # test, production
        "provider": str,          # stripe, mercadopago
        "account_id": str
    },
    "catalog_size": int,          # SKUs en catálogo
    "last_import": datetime,
    "active_customers": int,
    "open_invoices": int,
    "dunning_enabled": bool,
    "errors_24h": int
}
```

### Tabla: **invoices**
```python
{
    "id": str,                    # INV-XXXX
    "tenant_id": str,             # FK a tenants
    "customer_id": str,           # CUST-XXXX
    "amount": float,
    "due_date": date,
    "status": str,                # pending, processing, succeeded, failed, refunded, partial
    "dunning_stage": str,         # T-3, T-1, DUE, T+1, T+3, T+7, T+15, T+30, WRITE_OFF
    "payment_link": str,
    "created_at": datetime,
    "paid_at": datetime,
    "metadata": dict
}
```

### Tabla: **catalog_items**
```python
{
    "id": str,
    "tenant_id": str,
    "sku": str,
    "name": str,
    "canonical_name": str,        # Nombre normalizado
    "aliases": list[str],         # Sinónimos y variantes
    "price": float,
    "unit": str,                  # PZA, KG, M, L, etc
    "category": str,
    "tags": list[str],
    "stock": int,
    "min_stock": int,
    "active": bool,
    "created_at": datetime,
    "updated_at": datetime
}
```

### Tabla: **conversations**
```python
{
    "id": str,
    "tenant_id": str,
    "customer_id": str,
    "channel": str,               # whatsapp, telegram, web
    "state": str,                 # active, paused, completed
    "messages": list[{
        "role": str,              # user, assistant, system
        "content": str,
        "timestamp": datetime,
        "metadata": dict
    }],
    "created_at": datetime,
    "updated_at": datetime,
    "agent_id": str,              # Agente que maneja la conversación
    "context": dict               # Contexto acumulado
}
```

### Tabla: **webhooks**
```python
{
    "id": str,
    "event_type": str,            # payment_succeeded, payment_failed, etc
    "tenant_id": str,
    "data": dict,
    "signature": str,
    "idempotency_key": str,       # Para evitar duplicados
    "received_at": datetime,
    "processed": bool,
    "attempts": int,
    "last_attempt": datetime,
    "error": str
}
```

### Tabla: **dunning_rules**
```python
{
    "id": str,
    "tenant_id": str,
    "stage": str,                 # T-3, T-1, DUE, etc
    "channel": str,               # whatsapp, telegram, email, sms
    "template": str,              # Plantilla del mensaje
    "hour": int,                  # 0-23
    "enabled": bool,
    "throttle_hours": int,        # Horas entre mensajes
    "fallback_channel": str,      # Canal alternativo si falla
    "success_rate": float,
    "last_sent": datetime
}
```

### Tabla: **audit_logs**
```python
{
    "id": str,
    "actor_id": str,              # Usuario o sistema que realizó la acción
    "tenant_id": str,
    "entity_type": str,           # tenant, invoice, catalog_item, etc
    "entity_id": str,
    "action": str,                # create, update, delete, impersonate
    "diff": dict,                 # {"before": {...}, "after": {...}}
    "timestamp": datetime,
    "ip_address": str,
    "user_agent": str
}
```

## 🔌 APIs y Endpoints

### Control Tower API (Puerto 8001)

#### Overview
- `GET /api/overview` - Métricas globales multi-tenant
- `GET /api/health` - Health check de servicios

#### Tenants
- `GET /api/tenants` - Lista de tenants
- `GET /api/tenants/{tenant_id}` - Detalles de tenant
- `POST /api/tenants/{tenant_id}/impersonate` - Impersonar tenant

#### Imports
- `POST /api/imports/upload` - Cargar catálogo PDF/Excel/Foto
- `GET /api/imports/{import_id}` - Estado de importación

#### Dunning
- `GET /api/dunning/pipeline` - Pipeline de cobranza
- `POST /api/dunning/send` - Enviar recordatorio
- `GET /api/dunning/rules` - Reglas de dunning

#### Payments
- `POST /api/payments/create-link` - Crear link de pago
- `POST /api/payments/simulate-webhook` - Simular webhook PSP
- `GET /api/payments/transactions` - Historial de pagos

#### Webhooks
- `GET /api/webhooks/stream` - Stream de webhooks
- `POST /api/webhooks/test-idempotency` - Test de deduplicación

#### Golden Flows
- `POST /api/golden-flows/run` - Ejecutar flow automatizado
- `GET /api/golden-flows/results` - Resultados de flows

#### Time Machine
- `POST /api/time-machine/set` - Configurar fecha simulada
- `GET /api/time-machine/current` - Fecha actual simulada

### Cliente API (Puerto 8000)

#### Chat
- `POST /api/chat` - Procesar mensaje de chat
- `GET /api/chat/history/{phone}` - Historial de conversación
- `GET /api/chat/active` - Conversaciones activas

#### Catalog
- `POST /api/catalog/upload` - Subir catálogo
- `GET /api/catalog/{catalog_id}` - Obtener catálogo
- `POST /api/catalog/search` - Buscar productos
- `POST /api/catalog/normalize` - Normalizar productos

#### Dashboard
- `GET /api/dashboard/metrics` - Métricas del dashboard
- `GET /dashboard` - Dashboard HTML

## 🚀 Configuración y Deployment

### Variables de Entorno Requeridas
```bash
# Groq (Principal)
GROQ_API_KEY=gsk_xxxxx

# Azure OpenAI (Fallback)
AZURE_OPENAI_ENDPOINT=https://xxx.cognitiveservices.azure.com/
AZURE_OPENAI_KEY=xxx
AZURE_OPENAI_DEPLOYMENT=gpt-4o-mini

# WhatsApp Business
WHATSAPP_API_KEY=xxx
WHATSAPP_PHONE_ID=xxx

# Stripe
STRIPE_SECRET_KEY=sk_test_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Database (Futuro)
DATABASE_URL=postgresql://user:pass@localhost/orkesta
```

### Comandos de Inicio
```bash
# Control Tower
cd backend && python control_tower_api.py  # Puerto 8001

# Cliente API
cd backend && python api_server_groq.py    # Puerto 8000

# Con Ollama local (fallback)
ollama serve
ollama pull llama3.1:8b
```

### Puertos Utilizados
- **8000**: API Cliente con Groq
- **8001**: Control Tower
- **11434**: Ollama (opcional)
- **7880**: LiveKit (opcional)

## 📈 Métricas y KPIs

### Métricas de Sistema
- **Throughput**: 45-65 msgs/seg (WhatsApp)
- **Webhooks**: 5-15/seg
- **P95 Latency**: < 250ms
- **Uptime**: 99.95%
- **Error Rate**: < 0.02%

### Métricas de Negocio
- **Mapeo automático**: ≥ 80% accuracy
- **Q→C Time**: ≤ 2 minutos
- **Dunning effectiveness**: > 82%
- **Collection rate**: > 73%
- **Deduplication**: 100%

## 🧪 Testing

### Golden Flows Automatizados
1. **PDF→Payment**: Importar → Cotizar → Link → Pago
2. **Dunning+Fallback**: WA falla → SMS backup
3. **Partial Payment**: Tarjeta + OXXO
4. **Ticket→RMA**: Queja → Return → Crédito

### Criterios de Aceptación
- Multi-tenant switching < 1s
- Import 1k SKUs < 10 min
- Quote to payment < 2 min
- Webhook p95 < 5s
- Message queue drain @ 60 mps

## 🔒 Seguridad

### Autenticación
- JWT tokens con refresh
- Session tokens para impersonación
- API keys por tenant

### Autorización
- RBAC por tenant
- Permisos granulares por módulo
- Auditoría completa de acciones

### Protección de Datos
- PII enmascarado en logs
- Encryption at rest (futuro)
- HTTPS only en producción

## 🛠️ Mantenimiento

### Logs
- Structured logging con timestamps
- Log levels: DEBUG, INFO, WARN, ERROR
- Rotation diaria

### Monitoring
- Health checks cada 30s
- Alertas por degradación
- Dashboards en Grafana (futuro)

### Backups
- Snapshot diario (futuro)
- Point-in-time recovery
- Test de restore mensual

## 📝 Notas Importantes

1. **Sistema actual usa base de datos en memoria** - Los datos se pierden al reiniciar
2. **Groq es el LLM principal** - Azure OpenAI como fallback
3. **3 tenants demo precargados** - Listos para testing
4. **Kill Switch implementado** - Pausa envíos reales manteniendo sandbox
5. **Time Machine funcional** - Simula fechas para testing de dunning

## 🎯 Roadmap

### Corto Plazo (1-2 semanas)
- [ ] Persistencia en PostgreSQL
- [ ] WebSocket para actualizaciones real-time
- [ ] Emulador WhatsApp/Telegram completo
- [ ] Tests E2E automatizados

### Mediano Plazo (1-2 meses)
- [ ] Multi-idioma (ES, EN, PT)
- [ ] Analytics dashboard
- [ ] Integración con CRM
- [ ] Mobile app

### Largo Plazo (3-6 meses)
- [ ] ML para predicción de pagos
- [ ] Voice assistant
- [ ] Marketplace de integraciones
- [ ] White-label solution

---

**Última actualización**: 2025-01-14
**Versión**: 1.0.0
**Mantenedor**: Equipo Orkesta