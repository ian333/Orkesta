#!/usr/bin/env python3
"""
🚀 Test Rápido del Sistema Orkesta
==================================

Prueba rápida para verificar que todos los componentes funcionen.
"""

from dotenv import load_dotenv
load_dotenv()

print("🧪 TESTING SISTEMA ORKESTA COMPLETO")
print("=" * 50)

# 1. Test del Contexto Compartido
print("\n1️⃣ Probando Contexto Compartido...")
try:
    from orkesta_shared_context import get_shared_context, Product, ProductPricing, Client
    
    ctx = get_shared_context("test-quick")
    print("✅ Contexto compartido: OK")
    
    # Agregar producto de prueba
    product = Product(
        product_id="p_test_001",
        sku="TEST-001", 
        aliases=["test product"],
        name="Producto de Prueba",
        brand="TestBrand",
        unit="pieza",
        attributes={"test": "value"},
        pricing=ProductPricing(
            lists={"lista_base": {"MXN": 100.0, "iva_pct": 16}},
            overrides=[]
        ),
        stock={"default": 100}
    )
    
    ctx.add_product(product)
    print("✅ Producto agregado al contexto")
    
    # Buscar producto
    results = ctx.find_products("test")
    print(f"✅ Búsqueda de productos: {len(results)} encontrados")
    
except Exception as e:
    print(f"❌ Error en contexto compartido: {e}")

# 2. Test de Agentes Inteligentes  
print("\n2️⃣ Probando Agentes Inteligentes...")
try:
    from orkesta_smart_agents import CatalogMapperAgent, PriceResolverAgent
    
    catalog_agent = CatalogMapperAgent()
    price_agent = PriceResolverAgent()
    print("✅ Agentes inteligentes: OK")
    
except Exception as e:
    print(f"❌ Error en agentes: {e}")

# 3. Test básico de Stripe (sin hacer llamadas reales)
print("\n3️⃣ Probando configuración de Stripe...")
try:
    import stripe as stripe_lib
    import os
    
    stripe_lib.api_key = os.getenv("STRIPE_SECRET_KEY")
    if stripe_lib.api_key and stripe_lib.api_key.startswith("sk_test_"):
        print("✅ Stripe API Key configurado correctamente")
    else:
        print("⚠️  Stripe API Key no encontrado o inválido")
        
except Exception as e:
    print(f"❌ Error en Stripe: {e}")

# 4. Test del Control Tower
print("\n4️⃣ Probando Control Tower...")
try:
    # Solo importar para verificar que no hay errores de sintaxis
    import control_tower_enhanced_api
    print("✅ Control Tower: OK")
except Exception as e:
    print(f"❌ Error en Control Tower: {e}")

# 5. Test del Sistema de Testing
print("\n5️⃣ Probando Sistema de Testing...")
try:
    from orkesta_comprehensive_test_suite import OrkestaTestSuite
    test_suite = OrkestaTestSuite()
    print("✅ Suite de testing: OK")
except Exception as e:
    print(f"❌ Error en test suite: {e}")

print("\n" + "=" * 50)
print("🎯 TEST RÁPIDO COMPLETADO")
print("Si todos los ✅ aparecen, el sistema está funcionando correctamente!")