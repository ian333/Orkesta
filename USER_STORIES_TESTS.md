# ClienteOS + Catálogo IQ - Historias de Usuario y Casos de Prueba

## 🎯 Visión del Producto
**ClienteOS**: Convierte catálogos PDF en ventas por WhatsApp + cobros inteligentes para PyMEs mexicanas

---

## 📚 EPIC 1: CATÁLOGO IQ (PDF → Ventas)

### US-001: Subir Catálogo PDF
**Como** ferretero  
**Quiero** subir mi catálogo PDF de 500 productos  
**Para** no recapturar todo manualmente

**Casos de Prueba:**
```python
def test_upload_pdf_catalog():
    # Given: PDF de ferretería con tabla de productos
    pdf_file = "catalogo_truper_2024.pdf"
    
    # When: Subo el PDF
    response = upload_catalog(pdf_file)
    
    # Then: Sistema detecta columnas automáticamente
    assert response.detected_columns == ["codigo", "descripcion", "unidad", "precio"]
    assert response.total_rows == 523
    assert response.confidence_score > 0.8
```

**Criterios de Aceptación:**
- ✅ Acepta PDF hasta 50MB
- ✅ Detecta tablas automáticamente
- ✅ Muestra preview de primeras 10 filas
- ✅ Permite mapear columnas manualmente si falla auto-detección

---

### US-002: Normalizar Productos Duplicados
**Como** refaccionario  
**Quiero** que el sistema detecte productos duplicados  
**Para** tener un catálogo limpio sin repeticiones

**Casos de Prueba:**
```python
def test_normalize_duplicates():
    # Given: Productos con nombres similares
    products = [
        {"name": "TUBO PVC 3/4", "price": 45.00},
        {"name": "Tubo PVC 3/4 pulgadas", "price": 45.50},
        {"name": "TUBO P.V.C. 3/4\"", "price": 44.00}
    ]
    
    # When: Normalizo
    normalized = normalize_products(products)
    
    # Then: Detecta como mismo producto
    assert len(normalized.groups) == 1
    assert normalized.canonical_name == "Tubo PVC 3/4\""
    assert normalized.avg_price == 44.83
```

---

### US-003: Cliente Pregunta por WhatsApp
**Como** cliente de ferretería  
**Quiero** preguntar "necesito 10 tubos pvc 3/4"  
**Para** recibir precio y poder pagar inmediatamente

**Casos de Prueba:**
```python
def test_whatsapp_product_query():
    # Given: Mensaje de WhatsApp
    message = {
        "from": "+525512345678",
        "body": "buenos dias necesito 10 tubos pvc de 3/4"
    }
    
    # When: Proceso mensaje
    response = process_whatsapp_message(message)
    
    # Then: Responde con productos y precios
    assert len(response.products) >= 1
    assert response.products[0]["name"] == "Tubo PVC 3/4\""
    assert response.products[0]["unit_price"] == 45.00
    assert response.products[0]["total"] == 450.00
    assert response.payment_link != None
    assert "OXXO" in response.payment_methods
```

---

## 💰 EPIC 2: COTIZACIÓN → COBRO

### US-004: Generar Link de Pago con OXXO
**Como** dueño de ferretería  
**Quiero** enviar link de pago que acepte OXXO  
**Para** que clientes sin tarjeta puedan pagar

**Casos de Prueba:**
```python
def test_create_payment_link_oxxo():
    # Given: Cotización aprobada
    quote = {
        "client_id": "CL001",
        "items": [
            {"sku": "TUB001", "qty": 10, "price": 45.00}
        ],
        "total": 450.00
    }
    
    # When: Genero link
    payment_link = create_payment_link(quote, methods=["card", "oxxo", "spei"])
    
    # Then: Link incluye métodos mexicanos
    assert payment_link.url.startswith("https://pay.clienteos.mx/")
    assert payment_link.expires_in_hours == 72  # OXXO necesita más tiempo
    assert payment_link.methods == ["card", "oxxo", "spei"]
    assert payment_link.reference_oxxo != None  # Referencia para OXXO
```

---

### US-005: Recordatorio T-3 (3 días antes)
**Como** sistema  
**Quiero** enviar recordatorio 3 días antes del vencimiento  
**Para** reducir morosidad

**Casos de Prueba:**
```python
def test_reminder_t_minus_3():
    # Given: Factura que vence en 3 días
    invoice = {
        "id": "INV001",
        "client_phone": "+525512345678",
        "amount": 1500.00,
        "due_date": datetime.now() + timedelta(days=3),
        "client_wa_optin": True
    }
    
    # When: Cron ejecuta a las 10am
    reminders_sent = send_t3_reminders()
    
    # Then: Envía por WhatsApp con link
    assert len(reminders_sent) == 1
    assert reminders_sent[0].channel == "whatsapp"
    assert "vence en 3 días" in reminders_sent[0].message
    assert reminders_sent[0].payment_link != None
```

---

## 📄 EPIC 3: ÓRDENES DE COMPRA PDF

### US-006: Leer Orden de Compra de Cliente
**Como** vendedor  
**Quiero** que el sistema lea la OC en PDF que me mandó el cliente  
**Para** no teclear 50 productos manualmente

**Casos de Prueba:**
```python
def test_read_purchase_order_pdf():
    # Given: OC de Home Depot con 50 items
    po_pdf = "OC_HomeDepot_2024_001.pdf"
    
    # When: Proceso la OC
    order = process_purchase_order(po_pdf)
    
    # Then: Extrae productos y los mapea
    assert order.detected_items == 50
    assert order.matched_items == 47  # 94% match
    assert order.unmatched_items == [
        {"line": 23, "description": "TORNILLO GALV 1/4", "suggestion": "TORN001"},
        {"line": 35, "description": "CINTA AISLAR", "suggestion": "CIN003"},
        {"line": 48, "description": "CONTACTO DUPLEX", "suggestion": None}
    ]
    assert order.total_amount == 25430.00
```

---

## 🔄 EPIC 4: MULTI-LISTA DE PRECIOS

### US-007: Precio Diferente por Cliente
**Como** dueño  
**Quiero** dar precio especial a mis 3 mejores clientes  
**Para** mantener su lealtad

**Casos de Prueba:**
```python
def test_customer_specific_pricing():
    # Given: Cliente VIP
    client = {"id": "CL001", "category": "VIP", "volume": "high"}
    product = {"sku": "TUB001", "list_price": 45.00}
    
    # When: Calculo precio
    price = calculate_price(product, client)
    
    # Then: Aplica descuento automático
    assert price.base == 45.00
    assert price.discount_percent == 15  # VIP discount
    assert price.final == 38.25
    assert price.rule_applied == "VIP_HIGH_VOLUME"
```

---

## 🤖 EPIC 5: AGENTE CONVERSACIONAL

### US-008: Entender Sinónimos y Typos
**Como** cliente  
**Quiero** escribir "tuerca 1/2" o "tuerca media"  
**Para** encontrar el mismo producto

**Casos de Prueba:**
```python
def test_synonym_matching():
    # Given: Diferentes formas de pedir lo mismo
    queries = [
        "tuerca 1/2",
        "tuerca media pulgada",
        "tuerca de 1/2\"",
        "tuerca 1/2 in",
        "tuerca hexagonal 1/2"
    ]
    
    # When: Busco cada variante
    results = [search_product(q) for q in queries]
    
    # Then: Todas encuentran el mismo SKU
    skus = [r[0].sku for r in results if r]
    assert len(set(skus)) == 1  # Mismo SKU
    assert skus[0] == "TUER012"
```

---

## 📊 EPIC 6: ANALYTICS Y REPORTES

### US-009: Ver Productos Más Vendidos
**Como** dueño  
**Quiero** ver qué productos se venden más por WhatsApp  
**Para** mantener stock de lo que más sale

**Casos de Prueba:**
```python
def test_top_products_report():
    # Given: Ventas del último mes
    date_range = {
        "from": "2024-01-01",
        "to": "2024-01-31"
    }
    
    # When: Genero reporte
    report = generate_top_products(date_range)
    
    # Then: Muestra top con métricas
    assert len(report.products) == 10
    assert report.products[0] == {
        "sku": "CEM001",
        "name": "Cemento Cruz Azul 50kg",
        "units_sold": 450,
        "revenue": 67500.00,
        "avg_order_size": 5,
        "main_channel": "whatsapp"  # 80% vino por WA
    }
```

---

## 🧪 CASOS DE PRUEBA END-TO-END

### E2E-001: Flujo Completo Ferretería
```python
def test_e2e_ferreteria_flow():
    # 1. Ferretero sube catálogo PDF
    catalog_id = upload_pdf("catalogo_truper.pdf")
    map_columns(catalog_id, {"codigo": "sku", "desc": "name"})
    
    # 2. Cliente pregunta por WhatsApp
    wa_message = receive_whatsapp("necesito 5kg de cemento")
    response = process_message(wa_message)
    assert "Cemento Cruz Azul" in response.text
    
    # 3. Cliente acepta y paga en OXXO
    payment_link = response.payment_link
    payment = simulate_oxxo_payment(payment_link, reference="28193746")
    
    # 4. Sistema confirma pago
    webhook = process_stripe_webhook(payment)
    assert webhook.status == "paid"
    
    # 5. Cliente recibe confirmación
    confirmation = get_sent_messages(wa_message.from)
    assert "Pago recibido" in confirmation[-1].text
    assert confirmation[-1].has_receipt == True
```

### E2E-002: Flujo Consultorio Dental
```python
def test_e2e_consultorio_flow():
    # 1. Consultorio sube lista de tratamientos
    catalog = upload_excel("tratamientos_dental.xlsx")
    
    # 2. Paciente pregunta por WhatsApp
    wa_msg = receive_whatsapp("cuanto cuesta una limpieza dental?")
    response = process_message(wa_msg)
    assert "Limpieza dental: $450" in response.text
    assert "Agendar cita" in response.buttons
    
    # 3. Paciente agenda y paga 50% anticipo
    appointment = book_appointment(response.appointment_link)
    payment = pay_deposit(appointment, amount=225.00, method="card")
    
    # 4. Recordatorio día anterior
    reminder = get_reminder(appointment, t="T-1")
    assert reminder.sent_via == "whatsapp"
    assert "mañana a las 3:00 PM" in reminder.text
```

---

## 🔍 MÉTRICAS DE ÉXITO

### KPIs a Medir
```python
def test_success_metrics():
    metrics = calculate_monthly_metrics()
    
    # Tiempo de alta de catálogo
    assert metrics.avg_catalog_upload_time < 15  # minutos
    
    # Conversión WhatsApp → Venta
    assert metrics.wa_to_sale_conversion > 0.25  # 25%
    
    # Reducción en días de cobro
    assert metrics.dso_reduction > 7  # días
    
    # Precisión de matching en OC
    assert metrics.po_matching_accuracy > 0.85  # 85%
    
    # Satisfacción del cliente
    assert metrics.nps_score > 40
```

---

## 🚀 SETUP DE PRUEBAS

```bash
# Instalar dependencias
pip install pytest pytest-asyncio httpx

# Correr todas las pruebas
pytest tests/ -v

# Correr solo catálogo
pytest tests/test_catalog.py -v

# Correr con coverage
```

---

## 📝 NOTAS IMPORTANTES

1. **WhatsApp Sandbox**: Usar números de prueba de Meta
2. **Stripe Test Mode**: Usar tarjetas de prueba y OXXO test
3. **PDFs de Prueba**: Tener 5 catálogos reales anonimizados
4. **Datos de Prueba**: Mínimo 100 productos, 20 clientes, 50 transacciones

---

**ClienteOS + Catálogo IQ** - Convierte PDFs en ventas 🚀