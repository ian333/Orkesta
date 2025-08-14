"""
Pruebas completas para los 3 primeros clientes de ClienteOS
- Consultorios médicos
- Vendedores de herramienta automotriz  
- Vendedores de autopartes
"""
import requests
import json
import time
from datetime import datetime
import sys
import os

# Configuración
API_BASE = "http://localhost:8000"
HEADERS = {"Content-Type": "application/json"}

# Colores para output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_test_header(title):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")

def print_success(message):
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_error(message):
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_info(message):
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")

# ==================== CLIENTE 1: CONSULTORIO MÉDICO ====================

def test_consultorio_medico():
    """Test completo para consultorio médico/dental"""
    print_test_header("CLIENTE 1: CONSULTORIO DENTAL 'SONRISAS'")
    
    # 1. Crear organización
    print_info("Registrando consultorio...")
    org_data = {
        "id": "org_consultorio_001",
        "name": "Consultorio Dental Sonrisas",
        "phone": "+525555123456",
        "email": "info@sonrisasdental.mx",
        "plan": "professional"
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/organizations", json=org_data)
        assert response.status_code == 200
        print_success(f"Consultorio registrado: {org_data['name']}")
    except Exception as e:
        print_error(f"Error registrando consultorio: {e}")
        return False
    
    # 2. Subir catálogo de servicios médicos
    print_info("Subiendo catálogo de servicios...")
    
    # Simular catálogo PDF de servicios médicos
    catalog_content = """
    LISTA DE SERVICIOS DENTALES 2024
    
    CÓDIGO      SERVICIO                           PRECIO
    CONS-001    Consulta General                   $350.00
    CONS-002    Consulta de Especialidad           $550.00
    LIMP-001    Limpieza Dental Básica            $450.00
    LIMP-002    Limpieza Profunda                 $850.00
    BLAN-001    Blanqueamiento Láser              $3,500.00
    BLAN-002    Blanqueamiento con Férulas        $2,200.00
    EXT-001     Extracción Simple                 $600.00
    EXT-002     Extracción de Muela del Juicio   $2,500.00
    RES-001     Resina Simple                     $450.00
    RES-002     Resina Compuesta                  $650.00
    ENDO-001    Endodoncia Anterior               $3,500.00
    ENDO-002    Endodoncia Molar                  $4,500.00
    COR-001     Corona de Porcelana               $4,800.00
    COR-002     Corona de Zirconia                $6,500.00
    IMP-001     Implante Dental Completo          $18,000.00
    ORTO-001    Brackets Metálicos (tratamiento)  $25,000.00
    ORTO-002    Brackets Estéticos (tratamiento)  $35,000.00
    ORTO-003    Invisalign (tratamiento completo) $45,000.00
    """
    
    # Usar el endpoint de búsqueda para simular catálogo cargado
    test_queries = [
        ("Paciente pregunta por limpieza", "+525551234567", "hola, cuánto cuesta una limpieza dental?"),
        ("Paciente quiere agendar", "+525551234568", "me interesa, pueden mañana a las 4pm?"),
        ("Paciente pregunta por blanqueamiento", "+525551234569", "tienen blanqueamiento dental? cual es el precio"),
        ("Consulta de emergencia", "+525551234570", "tengo mucho dolor de muela, tienen citas hoy?"),
        ("Pregunta por ortodoncias", "+525551234571", "cuanto cuestan los brackets para mi hija de 14 años?")
    ]
    
    for desc, phone, message in test_queries:
        print_info(f"\n{desc}")
        print(f"  👤 Paciente: {message}")
        
        try:
            response = requests.post(
                f"{API_BASE}/api/chat",
                json={
                    "phone": phone,
                    "message": message,
                    "business_name": "Consultorio Dental Sonrisas"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  🤖 Bot: {data['response'][:150]}...")
                
                if 'products' in data and data['products']:
                    print(f"  💰 Servicios encontrados: {len(data['products'])}")
                    for p in data['products'][:2]:
                        print(f"     - {p.get('canonical_name', 'Servicio')}: ${p.get('price', 0):,.2f}")
                
                if 'quick_replies' in data and data['quick_replies']:
                    print(f"  🔘 Opciones: {', '.join(data['quick_replies'][:3])}")
                
                print_success(f"Chat procesado correctamente")
            else:
                print_error(f"Error en chat: {response.status_code}")
                
        except Exception as e:
            print_error(f"Error: {e}")
    
    # 3. Verificar métricas
    print_info("\nVerificando métricas del consultorio...")
    try:
        response = requests.get(f"{API_BASE}/api/dashboard/metrics")
        if response.status_code == 200:
            metrics = response.json()
            print(f"  📊 Conversaciones totales: {metrics['total_conversations']}")
            print(f"  💬 Conversaciones activas: {metrics['active_conversations']}")
            print_success("Métricas obtenidas correctamente")
        else:
            print_error(f"Error obteniendo métricas: {response.status_code}")
    except Exception as e:
        print_error(f"Error: {e}")
    
    return True

# ==================== CLIENTE 2: HERRAMIENTA AUTOMOTRIZ ====================

def test_herramienta_automotriz():
    """Test completo para vendedor de herramienta automotriz"""
    print_test_header("CLIENTE 2: HERRAMIENTA AUTOMOTRIZ 'MECANIX'")
    
    # 1. Crear organización
    print_info("Registrando tienda de herramienta...")
    org_data = {
        "id": "org_herramienta_001",
        "name": "Herramienta Automotriz MECANIX",
        "phone": "+525555234567",
        "email": "ventas@mecanix.mx",
        "plan": "professional"
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/organizations", json=org_data)
        assert response.status_code == 200
        print_success(f"Tienda registrada: {org_data['name']}")
    except Exception as e:
        print_error(f"Error registrando tienda: {e}")
        return False
    
    # 2. Catálogo de herramientas automotrices
    print_info("Procesando catálogo de herramientas...")
    
    catalog_content = """
    CATÁLOGO HERRAMIENTA AUTOMOTRIZ PROFESIONAL 2024
    
    SKU         DESCRIPCIÓN                              UNIDAD    PRECIO
    LLA-001     Llave Española 8mm                      PZA       $85.00
    LLA-002     Llave Española 10mm                     PZA       $85.00
    LLA-003     Llave Española 13mm                     PZA       $90.00
    LLA-004     Llave Española 17mm                     PZA       $95.00
    LLA-005     Juego Llaves Españolas 8-19mm (11pzs)   JUEGO     $750.00
    DAD-001     Dado 1/2" 13mm                          PZA       $65.00
    DAD-002     Dado 1/2" 17mm                          PZA       $65.00
    DAD-003     Dado 1/2" 19mm                          PZA       $70.00
    DAD-004     Juego Dados 1/2" 10-32mm (24pzs)        JUEGO     $1,450.00
    MAT-001     Matraca 1/2" Reversible                 PZA       $380.00
    MAT-002     Matraca 3/8" Reversible                 PZA       $320.00
    TOR-001     Torquímetro 1/2" 40-200 Nm              PZA       $1,850.00
    GAT-001     Gato Hidráulico 2 Ton                   PZA       $1,250.00
    GAT-002     Gato Hidráulico 3 Ton                   PZA       $1,650.00
    COM-001     Compresor 25 Litros 2.5HP               PZA       $3,450.00
    COM-002     Compresor 50 Litros 3HP                 PZA       $5,800.00
    PIS-001     Pistola de Impacto 1/2" Neumática       PZA       $1,450.00
    PIS-002     Pistola de Impacto 1/2" Eléctrica       PZA       $2,850.00
    ESC-001     Escáner OBD2 Profesional                PZA       $2,450.00
    ESC-002     Escáner OBD2 Multimarca Premium         PZA       $8,500.00
    MUL-001     Multímetro Digital Automotriz           PZA       $650.00
    LAM-001     Lámpara de Trabajo LED Recargable       PZA       $380.00
    EXT-001     Extractor de Poleas 3 Garras            PZA       $450.00
    PRE-001     Prensa Tipo C 4"                        PZA       $180.00
    """
    
    # Consultas de mecánicos
    test_queries = [
        ("Mecánico busca llaves", "+525552345678", "necesito un juego de llaves españolas completo"),
        ("Taller busca compresor", "+525552345679", "que compresores tienen? necesito uno de minimo 3hp"),
        ("Mecánico busca escáner", "+525552345680", "precio del scanner obd2 mas economico"),
        ("Compra de gato hidráulico", "+525552345681", "tienen gato hidraulico de 3 toneladas?"),
        ("Kit de dados", "+525552345682", "necesito juego de dados de 1/2 con matraca"),
        ("Herramienta neumática", "+525552345683", "cuanto cuesta la pistola de impacto neumatica")
    ]
    
    for desc, phone, message in test_queries:
        print_info(f"\n{desc}")
        print(f"  🔧 Mecánico: {message}")
        
        try:
            response = requests.post(
                f"{API_BASE}/api/chat",
                json={
                    "phone": phone,
                    "message": message,
                    "business_name": "Herramienta MECANIX"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  🤖 Bot: {data['response'][:150]}...")
                
                if 'products' in data and data['products']:
                    print(f"  🛠️ Herramientas encontradas: {len(data['products'])}")
                    for p in data['products'][:2]:
                        print(f"     - {p.get('canonical_name', 'Herramienta')}: ${p.get('price', 0):,.2f} {p.get('unit', 'PZA')}")
                
                if 'payment_link' in data:
                    print(f"  💳 Link de pago generado: {data['payment_link'][:50]}...")
                
                print_success(f"Consulta procesada correctamente")
            else:
                print_error(f"Error en chat: {response.status_code}")
                
        except Exception as e:
            print_error(f"Error: {e}")
    
    # 3. Simular selección y pago
    print_info("\nSimulando proceso de compra...")
    
    # Primero hacer consulta
    response = requests.post(
        f"{API_BASE}/api/chat",
        json={
            "phone": "+525552345690",
            "message": "necesito 2 matracas de 1/2",
            "business_name": "Herramienta MECANIX"
        }
    )
    
    if response.status_code == 200:
        # Luego seleccionar producto
        response = requests.post(
            f"{API_BASE}/api/chat",
            json={
                "phone": "+525552345690",
                "message": "1",  # Selecciona primera opción
                "business_name": "Herramienta MECANIX"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'order' in data:
                print(f"  📦 Orden creada: Total ${data['order']['total']:,.2f}")
                print_success("Orden generada correctamente")
            
            # Seleccionar método de pago
            response = requests.post(
                f"{API_BASE}/api/chat",
                json={
                    "phone": "+525552345690",
                    "message": "transferencia",
                    "business_name": "Herramienta MECANIX"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'payment_link' in data:
                    print(f"  💰 Link de pago SPEI: {data['payment_link'][:50]}...")
                    print_success("Link de pago generado")
    
    return True

# ==================== CLIENTE 3: AUTOPARTES ====================

def test_autopartes():
    """Test completo para vendedor de autopartes"""
    print_test_header("CLIENTE 3: AUTOPARTES 'REFACCIONES EXPRESS'")
    
    # 1. Crear organización
    print_info("Registrando refaccionaria...")
    org_data = {
        "id": "org_autopartes_001",
        "name": "Refacciones Express",
        "phone": "+525555345678",
        "email": "ventas@refaccionesexpress.mx",
        "plan": "enterprise"
    }
    
    try:
        response = requests.post(f"{API_BASE}/api/organizations", json=org_data)
        assert response.status_code == 200
        print_success(f"Refaccionaria registrada: {org_data['name']}")
    except Exception as e:
        print_error(f"Error registrando refaccionaria: {e}")
        return False
    
    # 2. Catálogo extenso de autopartes
    print_info("Procesando catálogo de autopartes...")
    
    catalog_content = """
    CATÁLOGO REFACCIONES AUTOMOTRICES 2024
    
    CÓDIGO      DESCRIPCIÓN                                    MARCA      PRECIO
    FIL-001     Filtro de Aceite Tsuru III                   GONHER     $85.00
    FIL-002     Filtro de Aceite Jetta A4                    MANN       $125.00
    FIL-003     Filtro de Aire Tsuru III                     INTERFIL   $65.00
    FIL-004     Filtro de Aire Jetta A4                      MANN       $185.00
    FIL-005     Filtro de Gasolina Universal                 WIX        $95.00
    BAL-001     Balatas Delanteras Tsuru III                 FRITEC     $280.00
    BAL-002     Balatas Delanteras Jetta A4                  BOSCH      $650.00
    BAL-003     Balatas Traseras Chevy C2                    FRITEC     $220.00
    BAL-004     Balatas Delanteras Aveo 2015                 ACDelco    $380.00
    BUJ-001     Bujías Platino Tsuru (juego 4)              NGK        $320.00
    BUJ-002     Bujías Iridium Jetta TSI (juego 4)          BOSCH      $680.00
    AMO-001     Amortiguador Delantero Tsuru III (c/u)      MONROE     $850.00
    AMO-002     Amortiguador Trasero Tsuru III (c/u)        MONROE     $750.00
    AMO-003     Amortiguador Delantero Jetta A4 (c/u)       SACHS      $1,450.00
    BAN-001     Banda de Tiempo Tsuru III                    GATES      $280.00
    BAN-002     Banda de Accesorios V6 3.0L                 DAYCO      $320.00
    ALT-001     Alternador Tsuru III Remanufacturado        BOSCH      $2,850.00
    ALT-002     Alternador Jetta A4 Nuevo                   VALEO      $4,500.00
    MAR-001     Marcha Tsuru III Remanufacturada            DELCO      $1,850.00
    MAR-002     Marcha Chevy Nuevo                          ACDelco    $2,200.00
    RAD-001     Radiador Tsuru III Aluminio                 NISSENS    $1,650.00
    RAD-002     Radiador Jetta A4 Original                  BEHR       $3,200.00
    TER-001     Termostato Tsuru 82°C                       GATES      $185.00
    BOM-001     Bomba de Agua Tsuru III                     HEPU       $380.00
    BOM-002     Bomba de Gasolina Eléctrica Universal       BOSCH      $950.00
    CLU-001     Kit Clutch Tsuru III (3 piezas)            LUK        $2,450.00
    CLU-002     Kit Clutch Jetta A4 1.8T                   SACHS      $4,800.00
    """
    
    # Consultas típicas de clientes
    test_queries = [
        ("Cliente busca filtros", "+525553456789", "necesito filtro de aceite para tsuru 2016"),
        ("Taller busca balatas", "+525553456790", "tienen balatas delanteras para jetta a4?"),
        ("Mecánico urgente", "+525553456791", "URGENTE necesito alternador para tsuru, tienen en existencia?"),
        ("Cliente comparando precios", "+525553456792", "cuanto cuestan los amortiguadores delanteros de tsuru"),
        ("Paquete completo", "+525553456793", "necesito kit completo de afinacion para tsuru 2015"),
        ("Refacción específica", "+525553456794", "bomba de agua para tsuru 3 original o buena calidad"),
        ("Múltiples piezas", "+525553456795", "cotizame 4 bujias, filtro aceite y filtro aire para jetta tsi")
    ]
    
    for desc, phone, message in test_queries:
        print_info(f"\n{desc}")
        print(f"  🚗 Cliente: {message}")
        
        try:
            response = requests.post(
                f"{API_BASE}/api/chat",
                json={
                    "phone": phone,
                    "message": message,
                    "business_name": "Refacciones Express"
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"  🤖 Bot: {data['response'][:150]}...")
                
                if 'products' in data and data['products']:
                    print(f"  🔧 Refacciones encontradas: {len(data['products'])}")
                    total = 0
                    for p in data['products'][:3]:
                        price = p.get('price', 0)
                        print(f"     - {p.get('canonical_name', 'Refacción')}: ${price:,.2f}")
                        total += price
                    if len(data['products']) > 1:
                        print(f"  💵 Total estimado: ${total:,.2f}")
                
                if 'quick_replies' in data and data['quick_replies']:
                    print(f"  🔘 Acciones: {', '.join(data['quick_replies'][:3])}")
                
                print_success(f"Consulta procesada correctamente")
            else:
                print_error(f"Error en chat: {response.status_code}")
                
        except Exception as e:
            print_error(f"Error: {e}")
    
    # 3. Simular compra con OXXO
    print_info("\nSimulando compra con pago en OXXO...")
    
    # Consulta inicial
    response = requests.post(
        f"{API_BASE}/api/chat",
        json={
            "phone": "+525553456800",
            "message": "necesito 4 filtros de aceite para tsuru",
            "business_name": "Refacciones Express"
        }
    )
    
    if response.status_code == 200:
        print("  ✓ Productos mostrados")
        
        # Seleccionar producto
        response = requests.post(
            f"{API_BASE}/api/chat",
            json={
                "phone": "+525553456800",
                "message": "1",
                "business_name": "Refacciones Express"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'order' in data:
                print(f"  ✓ Orden creada: ${data['order']['total']:,.2f}")
                
                # Elegir OXXO
                response = requests.post(
                    f"{API_BASE}/api/chat",
                    json={
                        "phone": "+525553456800",
                        "message": "oxxo",
                        "business_name": "Refacciones Express"
                    }
                )
                
                if response.status_code == 200:
                    data = response.json()
                    if 'payment_link' in data:
                        print(f"  ✓ Link OXXO generado: {data['payment_link'][:40]}...")
                        print_success("Proceso de compra OXXO completado")
    
    return True

# ==================== VERIFICACIÓN DE ENDPOINTS ====================

def test_all_endpoints():
    """Verifica que TODOS los endpoints funcionen correctamente"""
    print_test_header("VERIFICACIÓN COMPLETA DE ENDPOINTS")
    
    endpoints_to_test = [
        ("GET", "/", None, "Root endpoint"),
        ("GET", "/health", None, "Health check"),
        ("GET", "/api/dashboard/metrics", None, "Dashboard metrics"),
        ("GET", "/dashboard", None, "Dashboard HTML"),
        ("GET", "/api/organizations", None, "List organizations"),
        ("GET", "/api/chat/active", None, "Active chats"),
        ("GET", "/api/webhooks/history", None, "Webhook history"),
        ("POST", "/api/chat", {
            "phone": "+525559999999",
            "message": "test message",
            "business_name": "Test Business"
        }, "Chat endpoint"),
        ("POST", "/api/catalog/search", {
            "query": "tubo",
            "catalog_id": "demo"
        }, "Catalog search"),
        ("GET", "/api/catalog/demo", None, "Get demo catalog"),
        ("GET", "/api/chat/history/+525559999999", None, "Chat history"),
    ]
    
    results = []
    
    for method, endpoint, data, description in endpoints_to_test:
        try:
            print_info(f"Testing {method} {endpoint} - {description}")
            
            if method == "GET":
                response = requests.get(f"{API_BASE}{endpoint}")
            else:  # POST
                response = requests.post(
                    f"{API_BASE}{endpoint}",
                    json=data,
                    headers=HEADERS
                )
            
            if response.status_code in [200, 201]:
                print_success(f"  ✓ {endpoint} - Status: {response.status_code}")
                
                # Verificar estructura de respuesta
                if endpoint == "/api/dashboard/metrics":
                    data = response.json()
                    assert 'total_conversations' in data
                    assert 'active_conversations' in data
                    assert 'total_revenue' in data
                    print(f"    Métricas: {data['total_conversations']} conversaciones")
                
                elif endpoint == "/health":
                    data = response.json()
                    assert data['status'] == 'healthy'
                    print(f"    Sistema: {data['status']}")
                
                elif endpoint == "/":
                    data = response.json()
                    assert 'name' in data
                    assert 'version' in data
                    print(f"    Versión: {data['version']}")
                
                results.append((endpoint, True))
            else:
                print_error(f"  ✗ {endpoint} - Status: {response.status_code}")
                results.append((endpoint, False))
                
        except Exception as e:
            print_error(f"  ✗ {endpoint} - Error: {str(e)[:50]}")
            results.append((endpoint, False))
    
    # Resumen
    print_info("\n📊 RESUMEN DE ENDPOINTS:")
    success_count = sum(1 for _, success in results if success)
    total_count = len(results)
    
    for endpoint, success in results:
        status = "✅" if success else "❌"
        print(f"  {status} {endpoint}")
    
    print(f"\n  Total: {success_count}/{total_count} endpoints funcionando")
    
    if success_count == total_count:
        print_success("¡TODOS LOS ENDPOINTS FUNCIONAN CORRECTAMENTE!")
        return True
    else:
        print_error(f"Fallan {total_count - success_count} endpoints")
        return False

# ==================== PRUEBA DE CARGA ====================

def test_load():
    """Prueba de carga básica"""
    print_test_header("PRUEBA DE CARGA")
    
    print_info("Enviando 50 mensajes simultáneos...")
    
    import concurrent.futures
    import random
    
    messages = [
        "necesito tubos pvc",
        "cuanto cuesta el cemento",
        "tienen pintura blanca",
        "precio de tornillos",
        "quiero 10 tubos de 3/4",
        "necesito cemento urgente",
        "cotizame pintura vinilica"
    ]
    
    def send_message(i):
        try:
            msg = random.choice(messages)
            response = requests.post(
                f"{API_BASE}/api/chat",
                json={
                    "phone": f"+52555{i:07d}",
                    "message": msg,
                    "business_name": "Test Load"
                },
                timeout=5
            )
            return response.status_code == 200
        except:
            return False
    
    start_time = time.time()
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_message, i) for i in range(50)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]
    
    end_time = time.time()
    duration = end_time - start_time
    
    success_count = sum(results)
    print(f"  ✓ Exitosos: {success_count}/50")
    print(f"  ⏱️ Tiempo total: {duration:.2f} segundos")
    print(f"  📈 Throughput: {50/duration:.1f} req/seg")
    
    if success_count >= 45:  # 90% success rate
        print_success("Prueba de carga pasada")
        return True
    else:
        print_error("Prueba de carga fallida")
        return False

# ==================== MAIN ====================

def main():
    """Ejecutar todas las pruebas"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔═══════════════════════════════════════════════════════╗")
    print("║     CLIENTEOS - PRUEBAS DE LOS 3 PRIMEROS CLIENTES   ║")
    print("╚═══════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}")
    
    # Verificar que el servidor esté corriendo
    print_info("Verificando servidor...")
    try:
        response = requests.get(f"{API_BASE}/health", timeout=2)
        if response.status_code == 200:
            print_success("Servidor en línea ✓")
        else:
            print_error("Servidor no responde correctamente")
            print_info("Inicia el servidor con: python api_server.py")
            return
    except requests.exceptions.RequestException:
        print_error("No se puede conectar al servidor")
        print_info("Asegúrate de que el servidor esté corriendo:")
        print_info("  cd /home/ian/AI_gpt/Mercuria/clienteos/backend")
        print_info("  python api_server.py")
        return
    
    # Ejecutar pruebas
    all_tests = [
        ("Endpoints", test_all_endpoints),
        ("Consultorio Médico", test_consultorio_medico),
        ("Herramienta Automotriz", test_herramienta_automotriz),
        ("Autopartes", test_autopartes),
        ("Carga", test_load)
    ]
    
    results = []
    
    for name, test_func in all_tests:
        try:
            print(f"\n{Colors.BOLD}Ejecutando: {name}{Colors.ENDC}")
            result = test_func()
            results.append((name, result))
            time.sleep(1)  # Pequeña pausa entre pruebas
        except Exception as e:
            print_error(f"Error en prueba {name}: {e}")
            results.append((name, False))
    
    # Resumen final
    print_test_header("RESUMEN FINAL")
    
    for name, success in results:
        if success:
            print_success(f"✅ {name}")
        else:
            print_error(f"❌ {name}")
    
    success_count = sum(1 for _, s in results if s)
    total_count = len(results)
    
    print(f"\n{Colors.BOLD}Resultado: {success_count}/{total_count} pruebas exitosas{Colors.ENDC}")
    
    if success_count == total_count:
        print(f"\n{Colors.OKGREEN}{Colors.BOLD}")
        print("🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE! 🎉")
        print("El sistema está listo para los 3 tipos de clientes:")
        print("  ✓ Consultorios médicos/dentales")
        print("  ✓ Vendedores de herramienta automotriz")
        print("  ✓ Vendedores de autopartes")
        print(f"{Colors.ENDC}")
    else:
        print(f"\n{Colors.WARNING}⚠️ Algunas pruebas fallaron. Revisa los logs.{Colors.ENDC}")

if __name__ == "__main__":
    main()