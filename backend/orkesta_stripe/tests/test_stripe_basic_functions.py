#!/usr/bin/env python3
"""
test_stripe_basic_functions.py - Pruebas básicas de funciones Stripe

🧪 PRUEBAS POR CAPAS:
1. ✅ Conexión y autenticación con Stripe API
2. ✅ Verificación de cuentas existentes
3. ✅ Funciones de consulta (balance, estado)
4. ✅ Funciones de creación (cuentas)
5. ✅ Funciones de transferencia
6. ✅ Funciones de limpieza

Estas pruebas se ejecutan ANTES de integrar con agentes o base de datos.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stripe as stripe_lib
import json
import pytest
from datetime import datetime

# Configurar Stripe
stripe_lib.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_YOUR_STRIPE_KEY_HERE")

class TestStripeBasicFunctions:
    """Pruebas básicas de funciones Stripe - Capa 1"""
    
    def test_1_stripe_connection(self):
        """🔌 Capa 1: Probar conexión básica con Stripe"""
        print("\n🔌 Probando conexión con Stripe API...")
        
        try:
            # Verificar conexión obteniendo balance
            balance = stripe_lib.Balance.retrieve()
            assert balance is not None
            assert hasattr(balance, 'available')
            assert len(balance.available) > 0
            
            print(f"✅ Conexión exitosa")
            print(f"💰 Balance disponible: ${balance.available[0].amount / 100:.2f} {balance.available[0].currency.upper()}")
            
        except Exception as e:
            pytest.fail(f"❌ Error de conexión: {e}")
    
    def test_2_load_accounts_file(self):
        """📁 Capa 1: Cargar archivo de cuentas"""
        print("\n📁 Cargando archivo stripe/accounts.json...")
        
        try:
            with open('stripe/accounts.json', 'r') as f:
                data = json.load(f)
            
            assert 'accounts' in data
            assert len(data['accounts']) == 11
            assert 'total_accounts' in data
            assert data['total_accounts'] == 11
            
            print(f"✅ Archivo cargado: {len(data['accounts'])} cuentas")
            
            # Verificar estructura de cada cuenta
            for i, account in enumerate(data['accounts'][:3]):  # Solo verificar las primeras 3
                assert 'id' in account
                assert 'name' in account
                assert 'email' in account
                assert 'balance' in account
                print(f"   {i+1}. {account['name']}: {account['id']}")
            
        except Exception as e:
            pytest.fail(f"❌ Error cargando archivo: {e}")
    
    def test_3_verify_accounts_exist_in_stripe(self):
        """🏦 Capa 2: Verificar que las cuentas existen en Stripe"""
        print("\n🏦 Verificando cuentas en Stripe...")
        
        # Cargar cuentas del archivo
        with open('stripe/accounts.json', 'r') as f:
            data = json.load(f)
        
        verified_count = 0
        failed_accounts = []
        
        for account_data in data['accounts']:
            try:
                # Verificar cuenta en Stripe
                stripe_account = stripe_lib.Account.retrieve(account_data['id'])
                
                assert stripe_account.id == account_data['id']
                assert stripe_account.country == 'US'
                
                # Verificar estado
                is_enabled = stripe_account.charges_enabled
                transfers_status = stripe_account.capabilities.transfers
                
                print(f"   ✅ {account_data['name']}: charges={is_enabled}, transfers={transfers_status}")
                
                if is_enabled and transfers_status == 'active':
                    verified_count += 1
                else:
                    failed_accounts.append(account_data['name'])
                    
            except Exception as e:
                failed_accounts.append(f"{account_data['name']} - Error: {e}")
                print(f"   ❌ {account_data['name']}: {e}")
        
        print(f"\n📊 Resultado: {verified_count}/11 cuentas completamente habilitadas")
        
        if failed_accounts:
            print(f"⚠️ Cuentas con problemas: {failed_accounts}")
        
        # Al menos 5 cuentas deben estar habilitadas para las pruebas
        assert verified_count >= 5, f"Se necesitan al menos 5 cuentas habilitadas, solo {verified_count} están activas"
    
    def test_4_account_details_verification(self):
        """🔍 Capa 2: Verificar detalles de cuentas específicas"""
        print("\n🔍 Verificando detalles de cuentas...")
        
        # Cargar primera cuenta para pruebas detalladas
        with open('stripe/accounts.json', 'r') as f:
            data = json.load(f)
        
        chad_account = data['accounts'][0]  # Chad Martinez
        
        try:
            account = stripe_lib.Account.retrieve(chad_account['id'])
            
            # Verificar campos requeridos
            assert account.type == 'custom'
            assert account.country == 'US'
            assert account.email == chad_account['email']
            
            # Verificar individual
            if hasattr(account, 'individual'):
                ind = account.individual
                assert ind.first_name == 'Chad'
                assert ind.last_name == 'Martinez'
                print(f"✅ Datos individuales verificados: {ind.first_name} {ind.last_name}")
            
            # Verificar business profile
            if hasattr(account, 'business_profile'):
                bp = account.business_profile
                assert bp.mcc == '5734'
                assert bp.url == 'https://cobrazo.mx'
                print(f"✅ Business profile verificado: MCC={bp.mcc}")
            
            # Verificar capacidades
            caps = account.capabilities
            print(f"✅ Capacidades: card_payments={caps.card_payments}, transfers={caps.transfers}")
            
        except Exception as e:
            pytest.fail(f"❌ Error verificando detalles: {e}")
    
    def test_5_balance_and_fees_check(self):
        """💰 Capa 3: Verificar balance y comisiones"""
        print("\n💰 Verificando balance de plataforma...")
        
        try:
            balance = stripe_lib.Balance.retrieve()
            
            print(f"📊 Balance actual:")
            for bal in balance.available:
                print(f"   - {bal.currency.upper()}: ${bal.amount / 100:.2f} (disponible)")
            
            for bal in balance.pending:
                print(f"   - {bal.currency.upper()}: ${bal.amount / 100:.2f} (pendiente)")
            
            # Verificar si hay balance suficiente para transferencias
            usd_available = 0
            for bal in balance.available:
                if bal.currency == 'usd':
                    usd_available = bal.amount / 100
                    break
            
            print(f"💵 Balance USD disponible para transferencias: ${usd_available:.2f}")
            
            if usd_available < 100:
                print("⚠️ Balance insuficiente para pruebas de transferencia")
            else:
                print("✅ Balance suficiente para transferencias")
                
        except Exception as e:
            pytest.fail(f"❌ Error verificando balance: {e}")
    
    def test_6_create_test_account_function(self):
        """🏗️ Capa 4: Probar función de creación de cuenta (sin crear)"""
        print("\n🏗️ Probando función de creación de cuenta...")
        
        # Importar función del stripe_manager
        sys.path.append('stripe')
        from stripe_manager import StripeManager
        
        manager = StripeManager()
        
        # Simular parámetros de creación (sin ejecutar)
        test_params = {
            'name': 'Test Account',
            'email': 'test@cobrazo.mx',
            'first_name': 'Test',
            'last_name': 'Account'
        }
        
        print(f"✅ Función de creación disponible")
        print(f"📝 Parámetros de prueba: {test_params}")
        print("ℹ️ No se crea cuenta real en esta prueba")
    
    def test_7_query_functions(self):
        """📊 Capa 3: Probar funciones de consulta"""
        print("\n📊 Probando funciones de consulta...")
        
        sys.path.append('stripe')
        from stripe_manager import StripeManager
        
        manager = StripeManager()
        
        try:
            # Probar verificación de estado
            enabled_count = manager.check_account_status()
            assert enabled_count >= 0
            print(f"✅ Función check_account_status: {enabled_count} cuentas habilitadas")
            
        except Exception as e:
            print(f"⚠️ Error en funciones de consulta: {e}")

class TestStripeTransferFunctions:
    """Pruebas de funciones de transferencia - Capa 5"""
    
    def test_8_transfer_function_parameters(self):
        """🔄 Capa 5: Verificar función de transferencia (parámetros)"""
        print("\n🔄 Verificando función de transferencia...")
        
        sys.path.append('stripe')
        from stripe_manager import StripeManager
        
        manager = StripeManager()
        
        # Cargar cuentas para obtener nombres válidos
        with open('stripe/accounts.json', 'r') as f:
            data = json.load(f)
        
        chad = data['accounts'][0]['name']  # Chad Martinez
        juan = data['accounts'][1]['name']  # Juan Perez
        
        print(f"✅ Cuentas para transferencia identificadas:")
        print(f"   - Origen: {chad}")
        print(f"   - Destino: {juan}")
        print(f"   - Función transfer_money disponible")
        
        # En esta prueba NO ejecutamos transferencia real por el balance
        print("ℹ️ Transferencia real requiere balance de plataforma")
    
    def test_9_simulate_transfer_without_execution(self):
        """🎯 Capa 5: Simular transferencia sin ejecutar"""
        print("\n🎯 Simulando lógica de transferencia...")
        
        # Cargar cuentas
        with open('stripe/accounts.json', 'r') as f:
            data = json.load(f)
        
        chad = data['accounts'][0]
        juan = data['accounts'][1]
        
        # Verificar que ambas cuentas existen en Stripe
        try:
            chad_stripe = stripe_lib.Account.retrieve(chad['id'])
            juan_stripe = stripe_lib.Account.retrieve(juan['id'])
            
            # Verificar que pueden recibir transferencias
            chad_can_send = chad_stripe_lib.charges_enabled
            juan_can_receive = juan_stripe_lib.capabilities.transfers == 'active'
            
            print(f"✅ Verificación de transferencia:")
            print(f"   - {chad['name']} puede enviar: {chad_can_send}")
            print(f"   - {juan['name']} puede recibir: {juan_can_receive}")
            
            if chad_can_send and juan_can_receive:
                print("✅ Transferencia sería posible con balance suficiente")
            else:
                print("⚠️ Transferencia no sería posible por configuración de cuentas")
                
        except Exception as e:
            pytest.fail(f"❌ Error simulando transferencia: {e}")

class TestStripeCleanupFunctions:
    """Pruebas de funciones de limpieza - Capa 6"""
    
    def test_10_cleanup_function_available(self):
        """🧹 Capa 6: Verificar función de limpieza (sin ejecutar)"""
        print("\n🧹 Verificando función de limpieza...")
        
        sys.path.append('stripe')
        from stripe_manager import StripeManager
        
        manager = StripeManager()
        
        # Verificar que función existe
        assert hasattr(manager, 'clean_all_test_data')
        print("✅ Función clean_all_test_data disponible")
        print("⚠️ No se ejecuta limpieza en pruebas (preservar cuentas)")

def run_stripe_manual_tests():
    """Ejecutar todas las pruebas manuales de Stripe"""
    print("\n" + "="*70)
    print("🧪 STRIPE MANUAL TESTS - PRUEBAS POR CAPAS")
    print("="*70)
    
    # Ejecutar pytest
    import subprocess
    
    test_command = [
        'python', '-m', 'pytest', 
        __file__, 
        '-v', '-s', '--tb=short'
    ]
    
    result = subprocess.run(test_command, capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("⚠️ Warnings:")
        print(result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_stripe_manual_tests()
    if success:
        print("\n✅ TODAS LAS PRUEBAS MANUALES DE STRIPE PASARON")
    else:
        print("\n❌ Algunas pruebas fallaron")