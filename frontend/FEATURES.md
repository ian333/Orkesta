## 1) Resumen
**Orkesta** es una super-app ligera para **cobrar, pagar y gestionar catálogo** desde el móvil:
- Genera **cobros** por **link/QR** (tipo Mercado Pago) usando **Stripe Checkout/Payment Links**.
- Permite **pagar a proveedores** (Stripe **Connect / Payouts**).
- Integra **catálogo** (productos/servicios), **cotizaciones** con **PDF** y envío por **chat/WhatsApp**.
- Incluye **chat** in-app para conversar con clientes y un **agente** que arma cotizaciones desde el catálogo.

---

## 2) Públicos y roles
- **Admin**: configura catálogo, precios, impuestos, proveedores, medios de pago, políticas.
- **Vendedor/Cajero**: genera links/QR, cotiza, confirma pagos, gestiona pedidos.
- **Cliente**: recibe link/QR; paga; puede chatear y recibir PDF de cotización/recibo.
- **Proveedor**: recibe pagos de la plataforma (Connect).

---

## 3) Módulos y features (MVP → v1.0)

### 3.1 Cobros (Checkout/Links/QR)
- Crear **link de pago** con monto fijo o a partir de ítems del catálogo.
- Mostrar **QR** en la app (render de la URL).
- Abrir Checkout en **WebBrowser/WebView** (Expo).
- Webhook Stripe → actualizar pedido: `PENDING → PAID / FAILED`.
- Historial de cobros y estado en tiempo real.

### 3.2 Catálogo
- CRUD de **productos/servicios** (nombre, SKU, categoría, descripción, precio, impuestos, imágenes).
- Sincronización con **Stripe Products/Prices** (opcional).
- Búsqueda y filtros básicos.

### 3.3 Cotizaciones
- Construcción de cotización desde catálogo (ítems, cantidades, descuentos, impuestos).
- Generación de **PDF** (plantilla corporativa).
- Envío por **chat/WhatsApp** con **link de pago** adjunto.
- Estados: *Draft* → *Enviada* → *Aceptada* → *Pagada*.

### 3.4 Pagos a proveedores (Payouts)
- Onboarding **Connect Express** (KYC) de proveedores.
- **Destination charges** o **transfers** según necesidad.
- Programación de **payouts** manuales/automáticos.
- Historial y conciliación.

### 3.5 Chat y comunicaciones
- Chat **in-app** (WebSocket/long polling).
- **WhatsApp Business Cloud API** para enviar cotizaciones, links de pago y estatus.
- Plantillas de mensaje (aprobaciones, recordatorios, pagos recibidos).

### 3.6 Gastos / Inventario / Ventas (MVP básico)
- **Gastos**: registro manual con categoría, adjuntos y total.
- **Inventario**: existencias mínimas, alertas.
- **Ventas**: listado de pedidos/cobros; filtros por fecha/estado.

### 3.7 Recibos / Documentos
- Recibo de cobro (PDF) y, opcionalmente, **Invoice de Stripe**.
- Almacenamiento de PDFs (S3 o equivalente).

### 3.8 Agente (fase 2)
- RAG sobre catálogo: sugiere ítems, arma cotización, aplica reglas de pricing.
- Redacción de mensajes (WhatsApp/Chat) y generación de PDF.
- Revisión/aprobación humana antes de enviar (guardrails).

---

## 4) Flujos principales

### 4.1 Cobro por link/QR
1. Vendedor selecciona ítems/monto → **crear Checkout Session**.  
2. App muestra **QR** y/o abre URL.  
3. Cliente paga → **webhook** marca pedido **PAID** → notificación al vendedor/cliente.

### 4.2 Payout a proveedor
1. Proveedor completa **onboarding Connect**.  
2. Venta asociada a proveedor → se crea **charge/transfer**.  
3. **Payout** al banco del proveedor (manual o automático).  

### 4.3 Cotización por chat
1. Cliente pide cotización (chat/WhatsApp).  
2. Agente sugiere ítems; vendedor confirma.  
3. Backend genera **PDF** y **link de pago** → se envían por el canal.  
4. Al pagar, cotización → **convertida a venta**.

---

## 5) Requisitos técnicos

### Frontend (mobile)
- **React Native (Expo)**, `@react-navigation/*`, `expo-web-browser`, `react-native-qrcode-svg`.
- Integración **Stripe**: `stripe-react-native` (PaymentSheet) o **Checkout URL** (MVP).
- Estado global (Context/Zustand) y almacenamiento local (AsyncStorage).

### Backend
- **FastAPI (Python)**, **PostgreSQL**, **SQLAlchemy**.
- **Stripe SDK** (pagos, Checkout, Connect, webhooks).
- **WeasyPrint/ReportLab** (PDFs).
- **S3** (minio/AWS) para adjuntos.
- **WhatsApp Cloud API** (opcional en MVP).

### Infra
- Contenedores (Docker) para backend y DB.
- Webhook público (ngrok durante desarrollo).

---

## 6) Seguridad y cumplimiento
- **PCI**: usar **Checkout / Payment Links / PaymentSheet** (no capturamos PAN) → SAQ-A.  
- **Connect**: cumplir KYC/AML de Stripe; verificación de proveedores.  
- Gestión de secretos por entorno; firma de **webhooks**.  
- Trazabilidad: logs de estados y auditoría de cambios.

---

## 7) Modelo de datos (mínimo)

- products(id, name, sku, description, image_url, tax_rate, active)
- prices(id, product_id, currency, unit_amount, active)
- customers(id, name, email, phone, whatsapp_opt_in)
- orders(id, customer_id, status, total_amount, stripe_session_id, created_at)
- order_items(order_id, product_id, qty, unit_amount)
- vendors(id, name, stripe_account_id, kyc_status)
- payouts(id, vendor_id, amount, status, transfer_id, payout_id)
- quotes(id, customer_id, status, pdf_url, total_amount, created_at)
- quote_items(quote_id, product_id, qty, unit_amount, discount)
- messages(id, channel, customer_id, body, quote_id, metadata_json, created_at)
- expenses(id, category, amount, note, attachment_url, created_at)
- inventory(product_id, stock, min_stock, location)

## 8) Configuración (.env ejemplo)
# Backend
- STRIPE_SECRET_KEY=sk_live_xxx
- STRIPE_WEBHOOK_SECRET=whsec_xxx
- BACKEND_URL=https://api.orkesta.com
- DATABASE_URL=postgresql+psycopg://user:pass@host:5432/orkesta
- S3_ENDPOINT=https://s3.example.com
- S3_BUCKET=orkesta-docs
- S3_ACCESS_KEY=...
- S3_SECRET_KEY=...
- WHATSAPP_TOKEN=EAAbc...
- WHATSAPP_PHONE_NUMBER_ID=1234567890
- ENABLE_STRIPE_CONNECT=true

# Frontend (Expo)
- EXPO_PUBLIC_API_URL=https://api.orkesta.com
- EXPO_PUBLIC_STRIPE_PUBLISHABLE_KEY=pk_live_xxx

## 9) Métricas (KPIs iniciales)

- Tasa de conversión de cotización→pago.
- % pagos por link/QR vs. otros métodos.
- Tiempo medio cotización→pago.
- Volumen y valor de payouts a proveedores.
- LTV por cliente, frecuencia de compra.
- Tasa de recuperación en carritos/cotizaciones abandonadas.

## 10) Roadmap

**Fase 1 (MVP)** 

- Cobro con Checkout URL + QR, webhooks y recibo PDF básico.
- Catálogo CRUD y ventas básicas.
- Chat in-app sencillo.
- Gastos/inventario mínimos.
- WhatsApp: envío de link de pago (opcional).

**Fase 2**

- Agente para cotizaciones (RAG + plantillas PDF).
- Stripe Connect (onboarding + payouts).
- Catálogo avanzado (variantes, combos, impuestos por región).
- Reportes y panel de métricas.

**Fase 3**

- PaymentSheet nativo (si aplica).
- Tap-to-Pay/Terminal (pagos presenciales).
- Roles/permisos y auditoría granular.

## 11) Criterios de aceptación (extracto)

**Cobro por link/QR**

- Al crear cobro, backend devuelve session.url.
- App muestra QR funcional y botón “Abrir Checkout”.
- Al pagar, webhook cambia estado del pedido a PAID y notifica UI.
- Queda registro en historial con hora, importe, método, buyer.

**Cotización**

- Se puede armar cotización con ítems del catálogo, descuentos y totales.
- Genera PDF con logo, folio y validez.
- Envía por chat/WhatsApp con link de pago.
- Al pagar, la cotización pasa a Pagada y se genera recibo.

**Payouts (Connect)**

- Proveedor completa onboarding y queda verified.
- Venta a proveedor crea charge/transfer correctamente.
- Payout manual/auto reflejado en historial.

## 12) Navegación (App)

**Tabs: Inicio | Catálogo | Agenda | Chat**

- Inicio: Balance, acciones (Ingresar/Transferir/Cobrar), accesos (Clientes/Ventas/Gastos/Inventario/Cotización/Recibo).
- Cobrar: generar link/QR, abrir checkout, ver estado.
- Chat: lista de conversaciones y envío de cotizaciones.
- Catálogo: listado, búsqueda, detalle, agregar al carrito/cotización.

---

## 13) Estado Actual del Frontend (✅ COMPLETADO)

### 📱 Setup React Native Completado
- ✅ **Expo + React Native + TypeScript** configurado
- ✅ **Estructura completa** de componentes y pantallas
- ✅ **Navegación** Tab + Stack con React Navigation
- ✅ **Sistema de autenticación** con AsyncStorage
- ✅ **Integración APIs** backend Orkesta (Context API)
- ✅ **State management** con React Query + Context

### 🛠 Configuración Técnica WSL + Android
- ✅ **Android Studio + WSL** configuración completa
- ✅ **ADB configurado** para emulador desde WSL
- ✅ **Conexión exitosa** emulador usando IP WSL (`172.25.127.1:8083`)
- ✅ **Script automatizado** `setup-android-wsl.sh`
- ✅ **Hot reload** funcionando correctamente

### 🎯 Pantallas Implementadas
- ✅ **LoginScreen** - Autenticación con demo credentials
- ✅ **DashboardScreen** - Métricas y acciones principales
- ✅ **CatalogScreen** - Lista de productos con búsqueda
- ✅ **OrdersScreen** - Gestión de órdenes y cotizaciones
- ✅ **ConversationsScreen** - Chat con clientes
- ✅ **SettingsScreen** - Configuraciones y logout

### 🔧 Servicios y APIs
- ✅ **ApiService** - Cliente HTTP con interceptors
- ✅ **OrkestaApi** - Endpoints específicos del backend
- ✅ **AuthContext** - Gestión de sesión y tokens
- ✅ **Multi-tenant** - Headers X-Org-Id configurados

### 📚 Documentación
- ✅ **README.md** completo con setup WSL-Android
- ✅ **Troubleshooting** para errores comunes
- ✅ **Scripts de configuración** automatizados
- ✅ **Guías paso a paso** para desarrollo

### 🚀 Próximos Desarrollos (Fase 1 MVP)
- 🔄 **Integración Stripe** - PaymentSheet y Checkout URLs
- 🔄 **Generación QR** - Links de pago con react-native-qrcode-svg
- 🔄 **Chat en tiempo real** - WebSocket/long polling
- 🔄 **Generación PDF** - Cotizaciones y recibos
- 🔄 **WhatsApp Business** - Envío de links y cotizaciones

### 📊 Métricas de Desarrollo
- **32 archivos** creados en estructura frontend
- **12,983 líneas** de código base implementadas
- **5 pantallas principales** con navegación completa
- **3 servicios** de APIs configurados
- **1 script** de setup automatizado WSL-Android

---

## 14) Comandos de Desarrollo

### Setup Inicial
```bash
# Clonar repositorio
git clone git@github.com:ian333/Orkesta.git
cd Orkesta/frontend

# Configurar Android + WSL (automático)
chmod +x setup-android-wsl.sh
./setup-android-wsl.sh

# Instalar dependencias
npm install

# Iniciar desarrollo
npm start
# En emulador usar: exp://[IP_WSL]:8083
```

### Scripts Disponibles
```bash
npm start          # Servidor Expo general
npm run android    # Específico para Android
npm run web        # Desarrollo web
npm run lint       # ESLint
npm run type-check # TypeScript validation
```