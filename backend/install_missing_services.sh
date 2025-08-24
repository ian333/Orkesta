#!/bin/bash

echo "🔧 INSTALACIÓN DE SERVICIOS FALTANTES PARA ORKESTA"
echo "=================================================="

# 1. Verificar si estamos en WSL
if grep -q Microsoft /proc/version; then
    echo "✅ Detectado: WSL (Windows Subsystem for Linux)"
    IS_WSL=true
else
    IS_WSL=false
fi

# 2. Instalar PostgreSQL localmente (sin Docker)
echo ""
echo "📦 PostgreSQL:"
if command -v psql &> /dev/null; then
    echo "✅ PostgreSQL ya instalado"
else
    echo "❌ PostgreSQL no encontrado"
    echo "Para instalar ejecuta:"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install postgresql postgresql-contrib"
    echo "  sudo service postgresql start"
fi

# 3. Instalar Redis localmente
echo ""
echo "📦 Redis:"
if command -v redis-server &> /dev/null; then
    echo "✅ Redis ya instalado"
    redis-server --version
else
    echo "❌ Redis no encontrado"
    echo "Para instalar ejecuta:"
    echo "  sudo apt-get install redis-server"
    echo "  sudo service redis-server start"
fi

# 4. Instalar Tesseract OCR
echo ""
echo "📦 Tesseract OCR:"
if command -v tesseract &> /dev/null; then
    echo "✅ Tesseract ya instalado"
    tesseract --version | head -1
else
    echo "❌ Tesseract no encontrado"
    echo "Para instalar ejecuta:"
    echo "  sudo apt-get install tesseract-ocr tesseract-ocr-spa"
fi

# 5. Instalar Google Chrome (para Selenium)
echo ""
echo "📦 Google Chrome:"
if command -v google-chrome &> /dev/null; then
    echo "✅ Google Chrome ya instalado"
    google-chrome --version
else
    echo "❌ Google Chrome no encontrado"
    echo "Para instalar ejecuta:"
    echo "  wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -"
    echo "  sudo sh -c 'echo \"deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main\" >> /etc/apt/sources.list.d/google.list'"
    echo "  sudo apt-get update"
    echo "  sudo apt-get install google-chrome-stable"
fi

# 6. Verificar ChromeDriver
echo ""
echo "📦 ChromeDriver:"
if [ -f "$HOME/.cache/selenium/chromedriver/linux64/*/chromedriver" ]; then
    echo "✅ ChromeDriver encontrado en caché de Selenium"
else
    echo "⚠️ ChromeDriver no encontrado, se descargará automáticamente con webdriver-manager"
fi

# 7. Crear base de datos de prueba si PostgreSQL está instalado
echo ""
echo "🗄️ Base de datos de prueba:"
if command -v psql &> /dev/null; then
    # Verificar si PostgreSQL está corriendo
    if pg_isready &> /dev/null; then
        echo "✅ PostgreSQL está corriendo"
        
        # Crear usuario y base de datos de prueba
        sudo -u postgres psql -c "CREATE USER orkesta WITH PASSWORD 'orkesta_password_2024';" 2>/dev/null && echo "✅ Usuario 'orkesta' creado" || echo "⚠️ Usuario 'orkesta' ya existe"
        sudo -u postgres psql -c "CREATE DATABASE orkesta_test OWNER orkesta;" 2>/dev/null && echo "✅ Base de datos 'orkesta_test' creada" || echo "⚠️ Base de datos 'orkesta_test' ya existe"
        sudo -u postgres psql -c "CREATE DATABASE orkesta OWNER orkesta;" 2>/dev/null && echo "✅ Base de datos 'orkesta' creada" || echo "⚠️ Base de datos 'orkesta' ya existe"
        
        # Instalar pgvector
        sudo -u postgres psql -d orkesta -c "CREATE EXTENSION IF NOT EXISTS vector;" 2>/dev/null && echo "✅ Extension pgvector instalada" || echo "⚠️ pgvector requiere instalación manual"
    else
        echo "❌ PostgreSQL no está corriendo. Inicia con: sudo service postgresql start"
    fi
else
    echo "❌ PostgreSQL no instalado"
fi

# 8. Usar SQLite como alternativa
echo ""
echo "💾 SQLite (alternativa a PostgreSQL):"
echo "✅ SQLite está incluido en Python, listo para usar"
echo "   Base de datos: ./orkesta.db"

# 9. Resumen final
echo ""
echo "=================================================="
echo "📊 RESUMEN:"
echo ""

# Contar servicios disponibles
SERVICES_OK=0
SERVICES_MISSING=0

for cmd in psql redis-server tesseract google-chrome; do
    if command -v $cmd &> /dev/null; then
        ((SERVICES_OK++))
    else
        ((SERVICES_MISSING++))
    fi
done

echo "✅ Servicios disponibles: $SERVICES_OK"
echo "❌ Servicios faltantes: $SERVICES_MISSING"

if [ $SERVICES_MISSING -eq 0 ]; then
    echo ""
    echo "🎉 ¡Todo listo! Puedes ejecutar los tests reales."
else
    echo ""
    echo "⚠️ Instala los servicios faltantes para pruebas completas."
    echo "   O usa las alternativas disponibles (SQLite, etc.)"
fi

echo "=================================================="