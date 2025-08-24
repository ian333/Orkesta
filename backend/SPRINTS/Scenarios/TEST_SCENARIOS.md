# 🧪 ESCENARIOS DE PRUEBA - ORKESTA

> **IMPORTANTE**: Estos escenarios deben pasar ANTES de escribir código de producción.

## 🎯 FILOSOFÍA DE TESTING

**Test-First Development**: Definimos el comportamiento esperado antes de implementar.
Cada escenario representa un caso de uso REAL de un cliente.

## 📊 MATRIZ DE ESCENARIOS

| ID | Escenario | Prioridad | Sprint | Complejidad | Estado |
|----|-----------|-----------|--------|-------------|--------|
| S01 | Pedido simple por WhatsApp | 🔴 Alta | 1 | Baja | 🔄 |
| S02 | Pedido ambiguo requiere clarificación | 🔴 Alta | 1 | Media | 🔄 |
| S03 | Cliente sin crédito intenta comprar | 🔴 Alta | 2 | Media | ⏳ |
| S04 | Pago en efectivo con reconciliación | 🔴 Alta | 2 | Alta | ⏳ |
| S05 | Múltiples agentes colaboran en cotización | 🟡 Media | 2 | Alta | ⏳ |
| S06 | Cobranza escalada automática | 🟡 Media | 3 | Media | ⏳ |
| S07 | Inventario bajo trigger reorden | 🟡 Media | 3 | Media | ⏳ |
| S08 | Cliente abandona conversación | 🟢 Baja | 3 | Baja | ⏳ |
| S09 | Multi-tenant isolation | 🔴 Alta | 1 | Alta | 🔄 |
| S10 | Sistema bajo carga (1000 msg/seg) | 🟡 Media | 4 | Alta | ⏳ |

## 🔄 ESCENARIOS DETALLADOS

### 🎬 ESCENARIO S01: Pedido Simple por WhatsApp

**Actor**: Juan (Dueño de ferretería)
**Canal**: WhatsApp
**Contexto**: Cliente frecuente, buen historial de pago

#### Conversación:
```
Juan: "Hola, necesito 20 tubos PVC de 1/2 pulgada"
Bot: "Hola Juan! 👋 Encontré Tubo PVC 1/2" a $45.50 c/u. 
      Para 20 piezas serían $910.00. ¿Confirmo tu pedido?"
Juan: "Sí"
Bot: "✅ Pedido #ORD-2024-001 confirmado.
      Total: $910.00
      📍 Envío a tu dirección registrada
      💳 Link de pago: [link]
      ¿Necesitas factura?"
Juan: "No por ahora"
Bot: "Perfecto! Tu pedido está en proceso. Te avisaré cuando salga a reparto."
```

#### Verificaciones:
```python
def test_s01_pedido_simple():
    # Arrange
    customer = Customer(
        id="c_juan_001",
        name="Juan Pérez",
        credit_limit=50000,
        balance=0,
        history="excellent"
    )
    
    # Act
    conversation = ConversationEngine()
    responses = conversation.process_flow([
        "Hola, necesito 20 tubos PVC de 1/2 pulgada",
        "Sí",
        "No por ahora"
    ])
    
    # Assert
    assert len(responses) == 3
    assert "Tubo PVC 1/2" in responses[0]
    assert "$910.00" in responses[0]
    assert "ORD-2024" in responses[1]
    assert "link de pago" in responses[1].lower()
    
    # Verificar que se creó la orden
    order = Order.get_latest_for_customer(customer.id)
    assert order.status == "confirmed"
    assert order.total == 910.00
    assert len(order.items) == 1
    assert order.items[0].quantity == 20
```

### 🎬 ESCENARIO S02: Pedido Ambiguo Requiere Clarificación

**Actor**: María (Plomera independiente)
**Canal**: WhatsApp
**Contexto**: Cliente nueva, primer pedido

#### Conversación:
```
María: "Buenas, tienen tubos?"
Bot: "Hola! 👋 Sí, tenemos varios tipos de tubos. 
      ¿Qué tipo buscas?
      • PVC (1/2", 3/4", 1")
      • CPVC
      • Galvanizado
      • Cobre"
María: "pvc, el chico"
Bot: "Tenemos Tubo PVC 1/2" (el más pequeño) a $45.50.
      ¿Cuántas piezas necesitas?"
María: "mmm como 5"
Bot: "Perfecto! 5 piezas de Tubo PVC 1/2":
      • Precio unitario: $45.50
      • Total: $227.50
      ¿Confirmo tu pedido?"
María: "Está bien pero les pago cuando me los lleven"
Bot: "Entendido! Como es tu primera compra, necesito algunos datos:
      • Nombre completo
      • Dirección de entrega
      • Teléfono de contacto
      
      Manejamos pago contra entrega 💵
      ¿Me compartes tus datos?"
```

#### Verificaciones:
```python
def test_s02_pedido_ambiguo():
    # Arrange
    maría = Customer(type="new")
    
    # Act
    conversation = ConversationEngine()
    responses = conversation.process_flow([
        "Buenas, tienen tubos?",
        "pvc, el chico",
        "mmm como 5",
        "Está bien pero les pago cuando me los lleven"
    ])
    
    # Assert - Clarificación requerida
    assert "qué tipo" in responses[0].lower()
    assert "PVC" in responses[0]
    assert "CPVC" in responses[0]
    
    # Assert - Mapeo correcto
    assert "1/2" in responses[1]
    assert "más pequeño" in responses[1]
    
    # Assert - Cantidad interpretada
    assert responses[2].count("5") >= 1
    assert "227.50" in responses[2]
    
    # Assert - Manejo de pago contra entrega
    assert "primera compra" in responses[3]
    assert "datos" in responses[3].lower()
    assert "contra entrega" in responses[3]
```

### 🎬 ESCENARIO S03: Cliente Sin Crédito Intenta Comprar

**Actor**: Carlos (Constructor moroso)
**Canal**: WhatsApp  
**Contexto**: Debe $15,000, límite excedido hace 30 días

#### Conversación:
```
Carlos: "Necesito 100 blocks"
Bot: "Hola Carlos. Veo que tienes un saldo pendiente de $15,000 
      vencido hace 30 días. 
      
      Para procesar nuevos pedidos, necesitamos regularizar tu cuenta.
      
      Opciones:
      1️⃣ Pagar total ($15,000) - 5% descuento = $14,250
      2️⃣ Abono del 50% ($7,500) para reactivar crédito
      3️⃣ Plan de pagos: 3 mensualidades de $5,300
      
      ¿Cuál prefieres?"
Carlos: "No tengo ahora"
Bot: "Entiendo Carlos. Te puedo ofrecer:
      
      💵 Pago de contado con 10% descuento
      📱 Transferencia inmediata
      
      Para 100 blocks serían $1,250 - 10% = $1,125
      
      ¿Te interesa?"
Carlos: "Déjame ver y te aviso"
Bot: "Claro Carlos. Recuerda que:
      • Tu crédito se reactiva con un abono de $7,500
      • Con pago de contado tienes 10% descuento
      
      Estoy aquí cuando decidas. 
      
      💡 Tip: Otros clientes usan Kueski Pay para financiar."
```

#### Verificaciones:
```python
def test_s03_cliente_sin_credito():
    # Arrange
    carlos = Customer(
        id="c_carlos_001",
        balance=-15000,
        credit_limit=10000,
        days_overdue=30,
        status="blocked"
    )
    
    # Act
    responses = conversation.process_flow(
        customer=carlos,
        messages=["Necesito 100 blocks", "No tengo ahora", "Déjame ver y te aviso"]
    )
    
    # Assert - Bloqueo por crédito
    assert "saldo pendiente" in responses[0]
    assert "15,000" in responses[0]
    assert "30 días" in responses[0]
    
    # Assert - Opciones de pago
    assert "descuento" in responses[0]
    assert "plan de pagos" in responses[0].lower()
    
    # Assert - Alternativa de contado
    assert "contado" in responses[1]
    assert "10%" in responses[1]
    
    # Assert - No se creó orden
    orders = Order.get_for_customer(carlos.id, since="today")
    assert len(orders) == 0
```

### 🎬 ESCENARIO S04: Pago en Efectivo con Reconciliación

**Actor**: Ana (Tienda de barrio)
**Canal**: WhatsApp
**Contexto**: Prefiere pagar en OXXO

#### Conversación:
```
Ana: "Quiero pagar mi pedido de ayer"
Bot: "Hola Ana! Tu pedido #ORD-2024-002 por $3,450.00
      
      Opciones de pago:
      💳 Tarjeta (link): [url]
      🏪 OXXO: Referencia 2345-6789-0123
      📱 Transferencia:
         CLABE: 1234567890123456
         Ref: ORD2024002
      
      ¿Cómo prefieres pagar?"
Ana: "En oxxo"
Bot: "Perfecto! Para pagar en OXXO:
      
      📝 Referencia: 2345-6789-0123
      💰 Monto: $3,450.00
      ⏰ Vigencia: 48 horas
      
      📱 También te envié el código de barras por WhatsApp
      
      En cuanto OXXO confirme (5-10 min), te aviso."

[30 minutos después...]

Bot: "✅ Ana, recibimos tu pago!
      
      Pedido #ORD-2024-002
      Pagado: $3,450.00
      
      🚚 Tu pedido sale mañana a primera hora
      📄 Factura disponible en: [link]
      
      ¡Gracias por tu pago puntual! 🌟"
```

#### Verificaciones:
```python
def test_s04_pago_efectivo_oxxo():
    # Arrange
    ana = Customer(id="c_ana_001")
    order = Order(
        id="ORD-2024-002",
        customer_id=ana.id,
        total=3450.00,
        status="pending_payment"
    )
    
    # Act - Solicitud de pago
    response1 = conversation.process("Quiero pagar mi pedido de ayer")
    
    # Assert - Opciones de pago
    assert "OXXO" in response1
    assert "Referencia" in response1
    assert "CLABE" in response1
    
    # Act - Selección OXXO
    response2 = conversation.process("En oxxo")
    
    # Assert - Instrucciones OXXO
    assert "2345-6789-0123" in response2
    assert "48 horas" in response2
    assert "código de barras" in response2
    
    # Simular webhook de OXXO
    webhook = OXXOWebhook(
        reference="2345-6789-0123",
        amount=3450.00,
        status="paid",
        paid_at=datetime.now()
    )
    
    # Act - Procesar pago
    payment_processor.process_webhook(webhook)
    
    # Assert - Confirmación automática
    notifications = NotificationQueue.get_for_customer(ana.id)
    assert len(notifications) == 1
    assert "recibimos tu pago" in notifications[0]
    assert order.reload().status == "paid"
```

### 🎬 ESCENARIO S05: Múltiples Agentes Colaboran

**Actor**: Roberto (Empresa constructora)
**Canal**: WhatsApp
**Contexto**: Cliente premium, pedido grande

#### Flujo Interno de Agentes:
```
Roberto: "Necesito cotización para 500 m2 de piso cerámico"

[WhatsApp Agent → Orchestrator]
  Intent: "quote_request"
  Confidence: 0.95

[Orchestrator → Catalog Agent]
  Action: "search_products"
  Query: "piso cerámico"

[Catalog Agent → Orchestrator]
  Found: 5 products
  Best match: "Cerámico Portobello 60x60"

[Orchestrator → Inventory Agent]
  Check stock for 500m2 (≈140 cajas)

[Inventory Agent → Orchestrator]
  Stock: 89 cajas (warehouse A)
         63 cajas (warehouse B)
  Total: 152 cajas ✓

[Orchestrator → Pricing Agent]
  Calculate price for:
  - Customer: premium_segment
  - Quantity: 140 cajas
  - Product: ceramic_portobello

[Pricing Agent → Orchestrator]
  Base: $450/caja
  Volume discount: -15%
  Premium customer: -5%
  Final: $360/caja
  Total: $50,400

[Orchestrator → Quote Agent]
  Generate formal quote

[Quote Agent → WhatsApp Agent]
  PDF generated: quote_2024_003.pdf
  Valid for: 7 days

[WhatsApp Agent → Roberto]
Bot: "Roberto, preparé tu cotización:
      
      📋 Cotización #Q-2024-003
      • Cerámico Portobello 60x60
      • 140 cajas (504 m2)
      • Precio especial: $360/caja
      • Total: $50,400
      
      ✅ Incluye:
      - Descuento volumen 15%
      - Descuento cliente premium 5%
      - Entrega sin costo
      - Garantía extendida
      
      📄 PDF detallado: [link]
      ⏰ Vigencia: 7 días
      
      ¿Procedemos con el pedido?"
```

#### Verificaciones:
```python
def test_s05_colaboracion_agentes():
    # Arrange
    roberto = Customer(
        id="c_roberto_001",
        segment="premium",
        credit_limit=500000
    )
    
    # Act
    message = "Necesito cotización para 500 m2 de piso cerámico"
    
    # Verificar que cada agente fue llamado
    with patch.object(CatalogAgent, 'search') as mock_catalog:
        with patch.object(InventoryAgent, 'check') as mock_inventory:
            with patch.object(PricingAgent, 'calculate') as mock_pricing:
                with patch.object(QuoteAgent, 'generate') as mock_quote:
                    
                    response = orchestrator.process(message, roberto)
                    
                    # Assert - Todos los agentes participaron
                    mock_catalog.assert_called_once()
                    mock_inventory.assert_called_once()
                    mock_pricing.assert_called_once()
                    mock_quote.assert_called_once()
    
    # Assert - Respuesta correcta
    assert "Cerámico Portobello" in response
    assert "504 m2" in response  # Área real
    assert "$50,400" in response
    assert "15%" in response  # Descuento volumen
    assert "5%" in response   # Descuento premium
    
    # Assert - Quote generada
    quote = Quote.get_latest_for_customer(roberto.id)
    assert quote.total == 50400
    assert quote.valid_until > datetime.now()
```

### 🎬 ESCENARIO S09: Multi-Tenant Isolation

**Actor**: Sistema
**Contexto**: Verificar que los datos NUNCA se cruzan entre tenants

#### Test:
```python
def test_s09_multi_tenant_isolation():
    # Arrange - Crear 2 tenants
    tenant_a = Tenant(id="company-a")
    tenant_b = Tenant(id="company-b")
    
    # Crear productos con mismo SKU en ambos tenants
    product_a = Product(
        tenant_id="company-a",
        sku="TUBE-001",
        name="Tubo Marca A",
        price=100
    )
    
    product_b = Product(
        tenant_id="company-b",
        sku="TUBE-001",  # Mismo SKU!
        name="Tubo Marca B",
        price=200
    )
    
    # Act - Buscar desde cada contexto
    context_a = get_context("company-a")
    context_b = get_context("company-b")
    
    result_a = context_a.search_product("TUBE-001")
    result_b = context_b.search_product("TUBE-001")
    
    # Assert - Isolation completo
    assert result_a.name == "Tubo Marca A"
    assert result_a.price == 100
    assert result_b.name == "Tubo Marca B"
    assert result_b.price == 200
    
    # Intentar acceso cruzado (debe fallar)
    with pytest.raises(SecurityException):
        context_a.get_product(product_b.id)
    
    # Verificar que las conversaciones no se mezclan
    conv_a = Conversation(tenant_id="company-a", text="Hola")
    conv_b = Conversation(tenant_id="company-b", text="Hola")
    
    # Cada tenant solo ve sus conversaciones
    assert len(context_a.get_conversations()) == 1
    assert len(context_b.get_conversations()) == 1
    assert context_a.get_conversations()[0].id == conv_a.id
    assert context_b.get_conversations()[0].id == conv_b.id
```

## 🎭 ESCENARIOS DE ERROR

### E01: Timeout en Agente
```python
def test_e01_agent_timeout():
    # Simular que catalog agent no responde
    CatalogAgent.response_time = 10000  # 10 segundos
    
    message = "Buscar tubos PVC"
    
    # Debe activar fallback
    response = orchestrator.process(message, timeout=5000)
    
    assert "momento no puedo" in response
    assert "intenta en unos minutos" in response
    
    # Verificar que se loggeó el error
    assert len(error_logs) == 1
    assert error_logs[0].type == "AGENT_TIMEOUT"
```

### E02: LLM No Disponible
```python
def test_e02_llm_unavailable():
    # Simular Groq caído
    with patch.dict(os.environ, {"GROQ_API_KEY": ""}):
        
        agent = CatalogAgent()
        result = agent.search("tubos")
        
        # Debe usar fallback o cache
        assert result is not None
        assert result.source == "cache" or result.source == "fallback"
```

## 📈 ESCENARIOS DE PERFORMANCE

### P01: Carga Normal (100 msg/min)
```python
@pytest.mark.performance
async def test_p01_carga_normal():
    messages = generate_messages(100)
    
    start = time.time()
    results = await asyncio.gather(*[
        orchestrator.process(msg) for msg in messages
    ])
    duration = time.time() - start
    
    # Métricas esperadas
    assert duration < 60  # Menos de 1 minuto
    assert success_rate(results) > 0.98  # 98% success
    assert avg_latency(results) < 0.5  # 500ms promedio
```

### P02: Pico de Carga (1000 msg/min)
```python
@pytest.mark.performance
async def test_p02_pico_carga():
    # Simular Black Friday
    messages = generate_messages(1000)
    
    results = await load_test(messages, duration=60)
    
    # Sistema debe mantener SLA
    assert results.p95_latency < 2.0  # 2 segundos P95
    assert results.error_rate < 0.05  # 5% error máximo
    assert results.throughput > 900  # 900+ procesados
```

## ✅ CHECKLIST DE VALIDACIÓN

Antes de pasar a producción, TODOS estos escenarios deben:

- [ ] Ejecutarse automáticamente en CI/CD
- [ ] Pasar con > 95% de éxito
- [ ] Completarse en < 5 minutos (excepto performance)
- [ ] Generar métricas de cobertura
- [ ] Validar multi-tenancy
- [ ] Probar todos los agentes
- [ ] Simular errores comunes
- [ ] Verificar timeouts y retries

## 📊 MÉTRICAS DE CALIDAD

| Métrica | Target | Actual | Status |
|---------|--------|--------|--------|
| Cobertura de código | > 80% | - | ⏳ |
| Escenarios pasando | 100% | - | ⏳ |
| Tiempo de ejecución | < 5 min | - | ⏳ |
| Flaky tests | 0 | - | ⏳ |
| Performance P95 | < 2s | - | ⏳ |