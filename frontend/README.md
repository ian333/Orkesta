# 📱 Orkesta Frontend - React Native

Frontend móvil para el sistema Orkesta de agentes de ventas inteligentes con "cerebro compartido".

## 🚀 Setup Rápido

### 1. Instalar dependencias
```bash
npm install
```

### 2. Configurar variables de entorno
```bash
cp .env.example .env
# Editar .env con tus configuraciones
```

### 3. Ejecutar la app
```bash
# Para Android
npm run android

# Para iOS (requiere macOS)
npm run ios

# Para Web
npm run web

# Para desarrollo con Expo
npm run start
```

## 📱 Plataformas Soportadas

- ✅ Android (recomendado)
- ✅ iOS 
- ✅ Web (para pruebas)
- ✅ Expo Go (desarrollo)

## 🏗️ Arquitectura

### Estructura de Carpetas
```
src/
├── components/       # Componentes reutilizables
│   ├── common/      # Componentes generales
│   ├── forms/       # Formularios
│   └── cards/       # Tarjetas de datos
├── screens/         # Pantallas de la app
│   ├── auth/        # Login, registro
│   ├── dashboard/   # Dashboard, conversaciones
│   ├── catalog/     # Catálogo de productos
│   ├── orders/      # Órdenes y cotizaciones
│   └── settings/    # Configuraciones
├── navigation/      # Navegación de la app
├── services/        # APIs y servicios
├── contexts/        # Context providers
├── hooks/           # Custom hooks
├── types/           # TypeScript types
├── utils/           # Utilidades
└── constants/       # Constantes
```

### Stack Tecnológico
- ⚛️ **React Native** con Expo
- 🟦 **TypeScript** para type safety
- 🧭 **React Navigation** para navegación
- 🔄 **React Query** para state management
- 🌐 **Axios** para llamadas HTTP
- 🎨 **React Native Paper** para UI components
- 💾 **AsyncStorage** para persistencia local

## 🎯 Funcionalidades Principales

### 🧠 Contexto Compartido (Shared Brain)
- Productos sincronizados entre agentes
- Clientes centralizados por tenant
- Órdenes con estado en tiempo real

### 🤖 Agentes Inteligentes
- Mapeo de catálogo con IA
- Resolución automática de precios
- Construcción de cotizaciones inteligentes
- Sugerencias automáticas

### 💬 Conversaciones
- Chat en tiempo real con clientes
- Análisis de sentimiento automático
- Flujos conversacionales avanzados
- Métricas de salud de conversación

### 💳 Stripe Connect
- Múltiples modos de pago
- Cálculo automático de fees
- Checkout integrado
- Dashboard financiero

### 📊 Dashboard en Tiempo Real
- Métricas de ventas
- Performance de agentes
- Estado de Stripe
- Analytics de conversaciones

## 🔧 Desarrollo

### Scripts Disponibles
```bash
# Desarrollo
npm run start          # Iniciar Expo
npm run android        # Android dev
npm run ios           # iOS dev
npm run web           # Web dev

# Construcción
npm run build         # Build de producción

# Linting y formato
npm run lint          # ESLint
npm run type-check    # TypeScript check
```

### Configuración del Backend
Asegúrate de que el backend Orkesta esté ejecutándose:

```bash
# En el directorio backend/
python run_orkesta.py

# APIs disponibles:
# - http://localhost:8000 (API principal)
# - http://localhost:8003 (Control Tower)
# - http://localhost:8004 (Control Tower v2)
```

## 📱 Pantallas Principales

### 🔐 Autenticación
- Login con credenciales demo
- Gestión de sesión con AsyncStorage
- Multi-tenant support

### 🏠 Dashboard
- Métricas en tiempo real
- Cards con información clave
- Acciones rápidas

### 📦 Catálogo
- Lista de productos
- Búsqueda inteligente
- Detalles de producto

### 📋 Órdenes
- Lista de órdenes por estado
- Creación de nuevas órdenes
- Seguimiento de cotizaciones

### 💬 Conversaciones
- Chat con clientes
- Estados de conversación
- Análisis de sentimiento

### ⚙️ Configuraciones
- Perfil de usuario
- Configuraciones de app
- Logout seguro

## 🔌 Conexión con Backend APIs

### Headers Requeridos
```typescript
{
  'Content-Type': 'application/json',
  'X-Org-Id': 'tenant-id',        // Multi-tenant
  'Authorization': 'Bearer token'  // Autenticación
}
```

### Endpoints Principales
- `/api/context/{tenant}/products` - Productos
- `/api/agents/{tenant}/catalog/map` - Mapeo IA
- `/api/conversations/{tenant}` - Conversaciones
- `/api/dashboard/overview` - Métricas
- `/api/connect/accounts` - Stripe

## 🐛 Debug y Testing

### Debug en Desarrollo
```bash
# Logs de React Native
npx react-native log-android  # Android logs
npx react-native log-ios      # iOS logs

# Expo debugging
npm run start -- --clear      # Clear cache
```

### Conectar con Dispositivo Físico
1. Instalar Expo Go en tu dispositivo
2. Escanear QR code desde terminal
3. Hot reload automático habilitado

## 🚀 Deployment

### Build para Android
```bash
# APK de desarrollo
eas build --platform android --profile development

# APK de producción
eas build --platform android --profile production
```

### Build para iOS
```bash
# Simulador
eas build --platform ios --profile development

# App Store
eas build --platform ios --profile production
```

## 📱 Compatibilidad Android Studio & WSL

El proyecto está configurado para trabajar con Android Studio desde WSL:

1. **SDK requerido**: API 21+ (Android 5.0+)
2. **Gradle**: Configurado automáticamente
3. **Hot reload**: Funciona out-of-the-box
4. **Debugging**: Compatible con React Native Debugger

### Configuración WSL + Android Studio

#### 1. Variables de Entorno WSL
```bash
# Variables de entorno para WSL (apuntan a Windows)
export ANDROID_HOME="/mnt/c/Users/[TU_USUARIO]/AppData/Local/Android/Sdk"
export PATH="$PATH:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools"
```

#### 2. Configurar ADB para WSL
```bash
# Crear enlace simbólico para adb
sudo ln -sf "/mnt/c/Users/[TU_USUARIO]/AppData/Local/Android/Sdk/platform-tools/adb.exe" /usr/local/bin/adb

# Copiar adb sin extensión para Expo
cp /usr/local/bin/adb "/mnt/c/Users/[TU_USUARIO]/AppData/Local/Android/Sdk/platform-tools/adb"

# Verificar configuración
adb devices  # Debe mostrar: emulator-5554 device
```

#### 3. Conexión Emulador + WSL
```bash
# Obtener IP de WSL
hostname -I | awk '{print $1}'  # Ejemplo: 172.25.127.1

# Ejecutar servidor Expo
export ANDROID_HOME="/mnt/c/Users/[TU_USUARIO]/AppData/Local/Android/Sdk"
npx expo start --port 8083

# En Expo Go del emulador, usar:
exp://[IP_WSL]:8083  # Ejemplo: exp://172.25.127.1:8083
```

#### 4. Solución de Problemas Comunes

**Error: "adb: command not found"**
- Verificar variables de entorno
- Asegurar que existe `/usr/local/bin/adb`
- Reiniciar terminal WSL

**Error: "Failed to download remote update"**
- Usar IP de WSL en lugar de `127.0.0.1`
- Verificar conectividad: `exp://[IP_WSL]:puerto`
- Limpiar caché: `npx expo start --clear`

**Error: "Java.io.IOException"**
- Problema de conectividad WSL ↔ Android
- Solución: usar IP WSL directa

#### 5. Script de Setup Automático
```bash
#!/bin/bash
# setup-android-wsl.sh

# Configurar variables
USER_NAME=$(ls /mnt/c/Users/ | grep -v Public | head -1)
ANDROID_SDK="/mnt/c/Users/$USER_NAME/AppData/Local/Android/Sdk"

# Exportar variables
export ANDROID_HOME="$ANDROID_SDK"
export PATH="$PATH:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools"

# Configurar adb
sudo ln -sf "$ANDROID_SDK/platform-tools/adb.exe" /usr/local/bin/adb
cp /usr/local/bin/adb "$ANDROID_SDK/platform-tools/adb"

# Obtener IP WSL
WSL_IP=$(hostname -I | awk '{print $1}')
echo "🚀 IP WSL: $WSL_IP"
echo "📱 Usar en emulador: exp://$WSL_IP:8083"

# Iniciar servidor
npx expo start --port 8083
```

## 🎯 Próximos Pasos

1. ✅ Setup base completado
2. ✅ Configuración WSL + Android Studio
3. ✅ Conexión exitosa con emulador Android
4. 🔄 Testing con backend real
5. 📱 Refinamiento de UI/UX
6. 🚀 Deploy a stores
7. 📈 Analytics y monitoreo

### 🔧 Setup Rápido WSL
```bash
# Ejecutar script de configuración automática
chmod +x setup-android-wsl.sh
./setup-android-wsl.sh
```

---

**🎉 ¡El frontend de Orkesta está listo para desarrollo!**

Conecta con el backend existente y comienza a desarrollar las funcionalidades específicas para tu negocio.