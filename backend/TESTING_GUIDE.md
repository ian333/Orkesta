# 🧪 GUÍA COMPLETA DE TESTING - ORKESTA

## 🚀 **INICIO RÁPIDO**

### 1. **Setup del Entorno**
```bash
# 1. Activar virtual environment
source venv/bin/activate

# 2. Verificar .env (debe existir con tus keys)
ls -la .env

# 3. Test rápido del sistema
python test_orkesta_quick.py
```

### 2. **Levantar el Servidor**
```bash
# Opción 1: Launcher automático
python run_orkesta.py

# Opción 2: Directo con uvicorn
uvicorn control_tower_enhanced_api:app --reload --host 0.0.0.0 --port 8000
```

### 3. **URLs del Sistema**
- 🏠 **API Base**: http://localhost:8000
- 📊 **Control Tower**: http://localhost:8000/dashboard/overview  
- 🧪 **Lab de Simulación**: http://localhost:8000/simulation/lab
- 💳 **Stripe Connect**: http://localhost:8000/api/connect/accounts
- 📖 **Documentación**: http://localhost:8000/docs

---

## 🧠 **TESTING DEL CEREBRO COMPARTIDO**

### Test del Contexto
```bash
# Test básico del contexto compartido
python orkesta_shared_context.py

# Output esperado:
# 🧠 Orkesta Shared Context - Cerebro Colectivo
# ✅ Contexto creado para test-tenant
# 📦 Productos: 1
# 👥 Clientes: 1
# 🛒 Órdenes: 1
```

### APIs del Contexto
```bash
# Crear contexto para tenant
curl -X POST "http://localhost:8000/api/context/test-tenant/products" \
  -H "X-Org-Id: test-tenant" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "p_001",
    "sku": "TEST-001",
    "name": "Producto Test",
    "aliases": ["test", "prueba"],
    "brand": "TestBrand",
    "unit": "pieza",
    "pricing": {
      "lists": {"lista_base": {"MXN": 100.0}},
      "overrides": []
    }
  }'

# Buscar productos
curl "http://localhost:8000/api/context/test-tenant/products/search?q=test" \
  -H "X-Org-Id: test-tenant"
```

---

## 🤖 **TESTING DE AGENTES INTELIGENTES**

### Test de Agentes
```bash
# Test de colaboración de agentes
curl -X POST "http://localhost:8000/api/agents/test-tenant/catalog/map" \
  -H "X-Org-Id: test-tenant" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "tubo pvc 3/4 pulgada",
    "context": {"client_id": "c_test"}
  }'

# Test de resolución de precios
curl -X POST "http://localhost:8000/api/agents/test-tenant/pricing/resolve" \
  -H "X-Org-Id: test-tenant" \
  -H "Content-Type: application/json" \
  -d '{
    "product_id": "p_001",
    "quantity": 5,
    "client_id": "c_test"
  }'
```

### Test de Sugerencias
```bash
# Ver sugerencias pendientes
curl "http://localhost:8000/api/agents/test-tenant/suggestions" \
  -H "X-Org-Id: test-tenant"

# Aprobar sugerencia
curl -X POST "http://localhost:8000/api/agents/test-tenant/suggestions/SUGG-123/approve" \
  -H "X-Org-Id: test-tenant"
```

---

## 💳 **TESTING DE STRIPE CONNECT**

### Setup de Stripe
```bash
# Verificar cuentas existentes
curl "http://localhost:8000/api/connect/accounts" \
  -H "X-Org-Id: test-tenant"

# Crear nueva cuenta Connect
curl -X POST "http://localhost:8000/api/connect/accounts" \
  -H "X-Org-Id: test-tenant" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@empresa.mx",
    "charges_mode": "direct",
    "pricing_mode": "platform_handles"
  }'
```

### Test de Pagos
```bash
# Crear checkout session (Modo Direct)
curl -X POST "http://localhost:8000/api/connect/checkout/direct" \
  -H "X-Org-Id: test-tenant" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000.0,
    "order_id": "ORD-001",
    "success_url": "http://localhost:3000/success",
    "cancel_url": "http://localhost:3000/cancel"
  }'

# Test de fees
curl -X POST "http://localhost:8000/api/connect/fees/calculate" \
  -H "X-Org-Id: test-tenant" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1000.0,
    "charges_mode": "direct"
  }'
```

---

## 📊 **TESTING DEL CONTROL TOWER**

### Dashboard Overview
```bash
# Métricas generales del tenant
curl "http://localhost:8000/api/dashboard/overview" \
  -H "X-Org-Id: test-tenant"

# Métricas de agentes
curl "http://localhost:8000/api/dashboard/agents" \
  -H "X-Org-Id: test-tenant"

# Métricas de Stripe
curl "http://localhost:8000/api/dashboard/stripe" \
  -H "X-Org-Id: test-tenant"
```

### Conversaciones
```bash
# Estado de conversaciones
curl "http://localhost:8000/api/dashboard/conversations" \
  -H "X-Org-Id: test-tenant"

# Métricas del sistema
curl "http://localhost:8000/api/dashboard/system" \
  -H "X-Org-Id: test-tenant"
```

---

## 🧪 **TESTING AVANZADO**

### Test Suite Completo
```bash
# Ejecutar todas las pruebas
python orkesta_comprehensive_test_suite.py

# Test del laboratorio de simulación
python orkesta_simulation_lab.py
```

### Test de Stripe (Archivo renombrado)
```bash
# Test básico de Stripe (arreglar importaciones primero)
export $(cat .env | grep -v "^#" | xargs)
python orkesta_stripe/tests/test_stripe_basic_functions.py
```

### Test de Conversaciones
```bash
# Test de flujos conversacionales
curl -X POST "http://localhost:8000/api/conversations/test-tenant/start" \
  -H "X-Org-Id: test-tenant" \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "quote_request",
    "client_phone": "+5255123456789",
    "message": "Necesito cotizar tubos PVC"
  }'
```

---

## 🚨 **TROUBLESHOOTING**

### Problemas Comunes

1. **Error de importación `stripe`**
   ```bash
   # El módulo se renombró a orkesta_stripe
   # Verificar que todas las importaciones usen orkesta_stripe.*
   ```

2. **Error de variables de entorno**
   ```bash
   # Verificar que .env existe y tiene las keys
   cat .env | grep STRIPE_SECRET_KEY
   cat .env | grep AZURE_OPENAI_KEY
   ```

3. **Error de puerto ocupado**
   ```bash
   # Matar procesos en puerto 8000
   sudo kill -9 $(sudo lsof -t -i:8000)
   ```

4. **Error de dependencias**
   ```bash
   # Reinstalar dependencias
   pip install -r requirements.txt
   ```

### Verificaciones de Estado

```bash
# 1. Verificar que el servidor está arriba
curl http://localhost:8000/health

# 2. Verificar contexto compartido
curl "http://localhost:8000/api/context/test-tenant/status" \
  -H "X-Org-Id: test-tenant"

# 3. Verificar agentes
curl "http://localhost:8000/api/agents/test-tenant/status" \
  -H "X-Org-Id: test-tenant"

# 4. Verificar Stripe
curl "http://localhost:8000/api/connect/status" \
  -H "X-Org-Id: test-tenant"
```

---

## ✅ **CHECKLIST DE TESTING COMPLETO**

- [ ] ✅ Contexto compartido funciona
- [ ] ✅ Agentes inteligentes colaboran
- [ ] ✅ Stripe Connect configurado
- [ ] ✅ Control Tower muestra métricas
- [ ] ✅ APIs responden correctamente
- [ ] ✅ Multi-tenant isolation funciona
- [ ] ✅ Testing suite completa pasa
- [ ] ✅ Simulación lab funciona

---

**🎯 Si todos los ✅ están marcados, ¡el sistema Orkesta está funcionando perfectamente!**