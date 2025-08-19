#!/bin/bash
# setup-android-wsl.sh - Script para configurar Android Studio + WSL + Expo

set -e

echo "🚀 Configurando Android Studio + WSL para Orkesta Frontend..."

# Detectar usuario de Windows
USER_NAME=$(ls /mnt/c/Users/ | grep -v Public | head -1)
ANDROID_SDK="/mnt/c/Users/$USER_NAME/AppData/Local/Android/Sdk"

echo "👤 Usuario detectado: $USER_NAME"
echo "📁 Android SDK: $ANDROID_SDK"

# Verificar que existe el SDK
if [ ! -d "$ANDROID_SDK" ]; then
    echo "❌ Error: Android SDK no encontrado en $ANDROID_SDK"
    echo "   Instala Android Studio y configura el SDK primero"
    exit 1
fi

# Configurar variables de entorno
echo "⚙️  Configurando variables de entorno..."
export ANDROID_HOME="$ANDROID_SDK"
export PATH="$PATH:$ANDROID_HOME/emulator:$ANDROID_HOME/platform-tools"

# Configurar ADB
echo "🔧 Configurando ADB..."

# Crear enlace simbólico para adb
if [ ! -f "/usr/local/bin/adb" ]; then
    echo "   Creando enlace simbólico /usr/local/bin/adb..."
    sudo ln -sf "$ANDROID_SDK/platform-tools/adb.exe" /usr/local/bin/adb
else
    echo "   ✅ Enlace /usr/local/bin/adb ya existe"
fi

# Copiar adb sin extensión para Expo
if [ ! -f "$ANDROID_SDK/platform-tools/adb" ]; then
    echo "   Copiando adb sin extensión para Expo..."
    cp /usr/local/bin/adb "$ANDROID_SDK/platform-tools/adb"
else
    echo "   ✅ ADB sin extensión ya existe"
fi

# Verificar conexión con emulador
echo "📱 Verificando conexión con emulador..."
if adb devices | grep -q "device"; then
    echo "   ✅ Emulador conectado:"
    adb devices
else
    echo "   ⚠️  No se detectó emulador. Asegúrate de que esté ejecutándose."
fi

# Obtener IP de WSL
WSL_IP=$(hostname -I | awk '{print $1}')
echo "🌐 IP de WSL: $WSL_IP"

# Información de conexión
echo ""
echo "📋 CONFIGURACIÓN COMPLETADA"
echo "=========================="
echo "🔧 Variables configuradas:"
echo "   ANDROID_HOME=$ANDROID_HOME"
echo "   ADB disponible en: /usr/local/bin/adb"
echo ""
echo "🚀 Para iniciar el proyecto:"
echo "   export ANDROID_HOME=\"$ANDROID_SDK\""
echo "   npx expo start --port 8083"
echo ""
echo "📱 En Expo Go del emulador usar:"
echo "   exp://$WSL_IP:8083"
echo ""
echo "🎉 ¡Configuración completada exitosamente!"

# Preguntar si quiere iniciar el servidor ahora
read -p "¿Quieres iniciar el servidor Expo ahora? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🚀 Iniciando servidor Expo en puerto 8083..."
    echo "📱 Usar en emulador: exp://$WSL_IP:8083"
    npx expo start --port 8083
fi