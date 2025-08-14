# ClienteOS - Sistema de Gestión para PyMEs 🚀

Sistema completo de gestión de negocios con cobros, citas, finanzas y ventas por WhatsApp.

## ✅ Estado Actual

### Backend FastAPI ✓
- **API REST corriendo en**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **Base de datos PostgreSQL** inicializada con datos demo
- **Usuario demo**: demo@clienteos.mx / demo123

### Módulos Implementados ✓
1. **Sistema de Cobros con Stripe** 
   - Links de pago automáticos
   - Webhooks para conciliación
   - Múltiples métodos: tarjeta, OXXO, SPEI

2. **WhatsApp Business Integration**
   - Agente IA con Azure OpenAI
   - Venta automatizada del sistema
   - Soporte a clientes existentes
   - Recordatorios automáticos

3. **Gestión de Consultorios**
   - Sistema de citas
   - Disponibilidad automática
   - Recordatorios de citas

4. **Dashboard y Finanzas**
   - Métricas en tiempo real
   - Reportes financieros
   - Control de morosidad

5. **App Móvil React Native** ✓
   - Login funcional
   - Dashboard con métricas
   - Gestión de clientes
   - Sistema de cobros

## 🚀 Cómo Ejecutar

### Backend (Ya está corriendo)
```bash
cd clienteos/backend
source venv/bin/activate
python main.py
```
API disponible en: http://localhost:8000

### App Móvil
```bash
cd clienteos/mobile
npm install
npx expo start
```
Escanea el código QR con Expo Go en tu teléfono.

### Docker (Producción)
```bash
cd clienteos
docker-compose up -d
```

## 📱 Características Principales

### Para Negocios
- **Cobros Inteligentes**: Links de pago con Stripe
- **WhatsApp Automatizado**: Recordatorios y cobranza
- **Gestión de Clientes**: CRM simple y efectivo
- **Citas**: Sistema completo para consultorios
- **Finanzas**: Control total del negocio

### Para Vender ClienteOS
- **Bot de WhatsApp**: Vende el sistema automáticamente
- **Detección de Leads**: Identifica clientes interesados
- **Respuestas Inteligentes**: Azure OpenAI responde dudas
- **Escalación Humana**: Notifica cuando necesitas intervenir

## 💰 Modelo de Negocio

### Precios
- **Básico**: $399 MXN/mes (100 clientes)
- **Pro**: $799 MXN/mes (500 clientes)  
- **Empresarial**: $1,499 MXN/mes (ilimitado)

### Comisiones (Passthrough)
- Stripe: ~3.6% + $3 MXN
- OXXO: ~3.6% + $3 MXN
- WhatsApp: Por mensaje enviado

## 🔧 Configuración

### Variables de Entorno (.env)
```env
# Ya configuradas con tus keys:
STRIPE_SECRET_KEY=sk_test_51Rw6pc...
AZURE_OPENAI_KEY=4WxRVd3RmDIY71...
AZURE_OPENAI_ENDPOINT=https://cobrazo-agents...

# Necesitas configurar:
WA_ACCESS_TOKEN=tu_token_whatsapp
WA_PHONE_NUMBER_ID=tu_numero_id
```

### WhatsApp Business
1. Crea app en Meta for Developers
2. Configura webhook: https://tu-dominio.com/api/whatsapp/webhook
3. Agrega token de verificación en .env

### Cloudflare Tunnel (Opcional)
```bash
./setup-tunnel.sh
```

## 📊 Arquitectura

```
clienteos/
├── backend/          # FastAPI + Python
│   ├── models.py     # SQLAlchemy models
│   ├── routers/      # API endpoints
│   ├── services/     # Business logic
│   └── main.py       # Server entry
├── mobile/           # React Native + Expo
│   └── App.tsx       # Main app
├── docker-compose.yml
└── README.md
```

## 🎯 Próximos Pasos

1. **Configurar WhatsApp Business API**
   - Obtener access token de Meta
   - Configurar webhooks
   - Aprobar plantillas de mensajes

2. **Producción con Cloudflare**
   - Ejecutar setup-tunnel.sh
   - Configurar dominios
   - SSL automático

3. **Mejoras Sugeridas**
   - Integrar MercadoPago y Conekta
   - Sistema de facturación CFDI
   - App nativa iOS/Android
   - Analytics avanzados

## 🤖 Agentes IA Incluidos

- **PaymentAgent**: Decide mejor método de pago
- **WhatsAppAgent**: Vende y da soporte
- **CollectionAgent**: Estrategias de cobranza
- **AnalyticsAgent**: Insights del negocio

## 📞 Soporte

- API Docs: http://localhost:8000/docs
- Estado: http://localhost:8000/health
- Demo: demo@clienteos.mx / demo123

---

**ClienteOS** - Gestión inteligente para PyMEs mexicanas 🇲🇽
