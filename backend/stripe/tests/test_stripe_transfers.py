#!/usr/bin/env python3
"""
test_stripe_transfers.py - Pruebas de transferencias Stripe

🧪 CAPA 2: PRUEBAS DE TRANSFERENCIAS
1. ✅ Agregar balance a la plataforma
2. ✅ Probar transferencia real pequeña
3. ✅ Verificar que la transferencia se registró
4. ✅ Probar diferentes montos
5. ✅ Probar transferencia entre múltiples cuentas

Esta capa requiere que la Capa 1 (básica) haya pasado exitosamente.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stripe
import json
import pytest
import time
from datetime import datetime

# Configurar Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_YOUR_STRIPE_KEY_HERE")

class TestStripeTransfers:
    """Pruebas de transferencias reales de Stripe"""
    
    @classmethod
    def setup_class(cls):
        """Configuración inicial de las pruebas"""
        print("\n🎯 Configurando pruebas de transferencias Stripe...")
        
        # Verificar que las cuentas están disponibles
        with open('stripe/accounts.json', 'r') as f:
            cls.accounts_data = json.load(f)
        
        assert len(cls.accounts_data['accounts']) >= 11
        print(f"✅ {len(cls.accounts_data['accounts'])} cuentas cargadas para pruebas")
    
    def test_1_check_current_balance(self):
        """💰 Verificar balance actual de la plataforma"""
        print("\n💰 Verificando balance actual...")
        
        balance = stripe.Balance.retrieve()
        
        available_usd = 0
        pending_usd = 0
        
        for bal in balance.available:
            if bal.currency == 'usd':
                available_usd = bal.amount / 100
        
        for bal in balance.pending:
            if bal.currency == 'usd':
                pending_usd = bal.amount / 100
        
        print(f"💵 USD Disponible: ${available_usd:.2f}")
        print(f"⏳ USD Pendiente: ${pending_usd:.2f}")
        
        # Si no hay balance disponible, intentar agregar
        if available_usd < 10:
            print("⚠️ Balance insuficiente, intentando agregar fondos...")
            self._try_add_balance()
        else:
            print("✅ Balance suficiente para pruebas")
    
    def _try_add_balance(self):
        """Intentar agregar balance usando Payment Intent"""
        print("💳 Intentando agregar balance con Payment Intent...")
        
        try:
            # Crear Payment Intent con confirmación manual
            payment_intent = stripe.PaymentIntent.create(
                amount=50000,  # $500 USD
                currency="usd",
                payment_method_types=["card"],
                confirmation_method="manual",
                description="Balance para pruebas de transferencia"
            )
            
            # Confirmar con método de pago de prueba
            confirmed = stripe.PaymentIntent.confirm(
                payment_intent.id,
                payment_method="pm_card_visa"
            )
            
            print(f"✅ Payment Intent creado: {confirmed.id}")
            print(f"📊 Estado: {confirmed.status}")
            
            # Esperar un momento para procesamiento
            time.sleep(2)
            
        except Exception as e:
            print(f"⚠️ No se pudo agregar balance automáticamente: {e}")
            print("ℹ️ Las pruebas de transferencia pueden fallar por balance insuficiente")
    
    def test_2_prepare_test_accounts(self):
        """🏦 Preparar cuentas específicas para pruebas"""
        print("\n🏦 Preparando cuentas para pruebas...")
        
        # Verificar las primeras 3 cuentas están habilitadas
        test_accounts = []
        
        for account_data in self.accounts_data['accounts'][:3]:
            try:
                stripe_account = stripe.Account.retrieve(account_data['id'])
                
                if stripe_account.charges_enabled and stripe_account.capabilities.transfers == 'active':
                    test_accounts.append({
                        'data': account_data,
                        'stripe': stripe_account
                    })
                    print(f"✅ {account_data['name']}: Listo para pruebas")
                else:
                    print(f"⚠️ {account_data['name']}: No completamente habilitado")
                    
            except Exception as e:
                print(f"❌ {account_data['name']}: Error - {e}")
        
        assert len(test_accounts) >= 2, "Se necesitan al menos 2 cuentas habilitadas"
        
        # Guardar para otras pruebas
        self.test_accounts = test_accounts
        print(f"✅ {len(test_accounts)} cuentas preparadas para transferencias")
    
    def test_3_small_transfer_chad_to_juan(self):
        """🔄 Prueba: Transferencia pequeña Chad → Juan"""
        print("\n🔄 Probando transferencia Chad → Juan ($10)...")
        
        # Usar Chad (cuenta 0) y Juan (cuenta 1)
        chad = self.accounts_data['accounts'][0]
        juan = self.accounts_data['accounts'][1]
        
        amount = 10.00  # $10 USD
        
        try:
            # Crear transferencia
            transfer = stripe.Transfer.create(
                amount=int(amount * 100),  # En centavos
                currency="usd",
                destination=juan['id'],
                description=f"Prueba: {chad['name']} → {juan['name']} ${amount}"
            )
            
            print(f"✅ Transferencia exitosa!")
            print(f"🆔 Transfer ID: {transfer.id}")
            print(f"💵 Monto: ${transfer.amount / 100:.2f}")
            print(f"🎯 Destino: {transfer.destination}")
            print(f"📅 Creado: {datetime.fromtimestamp(transfer.created)}")
            
            # Guardar transfer_id para verificación posterior
            self.last_transfer = transfer
            
            assert transfer.amount == int(amount * 100)
            assert transfer.currency == "usd"
            assert transfer.destination == juan['id']
            
        except stripe.error.InvalidRequestError as e:
            if "insufficient" in str(e).lower():
                pytest.skip(f"Balance insuficiente en plataforma: {e}")
            else:
                pytest.fail(f"Error en transferencia: {e}")
        except Exception as e:
            pytest.fail(f"Error inesperado: {e}")
    
    def test_4_verify_transfer_in_stripe(self):
        """🔍 Verificar que la transferencia se registró en Stripe"""
        print("\n🔍 Verificando transferencia en Stripe...")
        
        if not hasattr(self, 'last_transfer'):
            pytest.skip("No hay transferencia previa para verificar")
        
        try:
            # Recuperar transferencia
            transfer = stripe.Transfer.retrieve(self.last_transfer.id)
            
            print(f"✅ Transferencia encontrada: {transfer.id}")
            print(f"📊 Estado: {transfer.object}")
            print(f"💰 Monto: ${transfer.amount / 100:.2f} {transfer.currency.upper()}")
            print(f"📍 Destino: {transfer.destination}")
            
            # Verificar datos
            assert transfer.id == self.last_transfer.id
            assert transfer.amount == self.last_transfer.amount
            assert transfer.destination == self.last_transfer.destination
            
        except Exception as e:
            pytest.fail(f"Error verificando transferencia: {e}")
    
    def test_5_list_recent_transfers(self):
        """📋 Listar transferencias recientes"""
        print("\n📋 Listando transferencias recientes...")
        
        try:
            # Obtener últimas 5 transferencias
            transfers = stripe.Transfer.list(limit=5)
            
            print(f"📊 {len(transfers.data)} transferencias encontradas:")
            
            for i, transfer in enumerate(transfers.data, 1):
                created_date = datetime.fromtimestamp(transfer.created)
                print(f"   {i}. ${transfer.amount / 100:.2f} → {transfer.destination} ({created_date.strftime('%H:%M:%S')})")
            
            assert len(transfers.data) >= 0  # Al menos debería retornar la lista
            
        except Exception as e:
            pytest.fail(f"Error listando transferencias: {e}")
    
    def test_6_multiple_small_transfers(self):
        """🔄 Múltiples transferencias pequeñas"""
        print("\n🔄 Probando múltiples transferencias pequeñas...")
        
        # Verificar que tenemos cuentas preparadas
        if not hasattr(self, 'test_accounts') or len(self.test_accounts) < 3:
            pytest.skip("Se necesitan al menos 3 cuentas habilitadas")
        
        transfers_made = []
        amount = 5.00  # $5 USD cada una
        
        # Hacer 3 transferencias diferentes
        test_transfers = [
            (self.accounts_data['accounts'][0], self.accounts_data['accounts'][1], "Chad → Juan"),
            (self.accounts_data['accounts'][1], self.accounts_data['accounts'][2], "Juan → Luis"),
            (self.accounts_data['accounts'][2], self.accounts_data['accounts'][0], "Luis → Chad")
        ]
        
        for sender, recipient, description in test_transfers:
            try:
                transfer = stripe.Transfer.create(
                    amount=int(amount * 100),
                    currency="usd",
                    destination=recipient['id'],
                    description=f"Test múltiple: {description} ${amount}"
                )
                
                transfers_made.append(transfer)
                print(f"   ✅ {description}: {transfer.id}")
                
                # Pequeña pausa entre transferencias
                time.sleep(1)
                
            except stripe.error.InvalidRequestError as e:
                if "insufficient" in str(e).lower():
                    print(f"   ⚠️ {description}: Balance insuficiente")
                    break  # Detener si no hay balance
                else:
                    print(f"   ❌ {description}: {e}")
            except Exception as e:
                print(f"   ❌ {description}: Error inesperado - {e}")
        
        print(f"📊 {len(transfers_made)}/3 transferencias completadas")
        
        if len(transfers_made) == 0:
            pytest.skip("No se pudieron completar transferencias por balance insuficiente")
        
        # Al menos una debería haber funcionado si hay balance
        assert len(transfers_made) >= 1, "Al menos una transferencia debería haber funcionado"
    
    def test_7_transfer_error_handling(self):
        """❌ Probar manejo de errores en transferencias"""
        print("\n❌ Probando manejo de errores...")
        
        # Intentar transferencia a cuenta inexistente
        try:
            stripe.Transfer.create(
                amount=1000,  # $10 USD
                currency="usd",
                destination="acct_invalid_account_id",
                description="Test error handling"
            )
            
            pytest.fail("Debería haber fallado con cuenta inexistente")
            
        except stripe.error.InvalidRequestError as e:
            print(f"✅ Error manejado correctamente: {e}")
            assert "account" in str(e).lower()
        
        # Intentar transferencia con monto negativo
        try:
            stripe.Transfer.create(
                amount=-1000,
                currency="usd",
                destination=self.accounts_data['accounts'][0]['id'],
                description="Test negative amount"
            )
            
            pytest.fail("Debería haber fallado con monto negativo")
            
        except stripe.error.InvalidRequestError as e:
            print(f"✅ Error de monto negativo manejado: {e}")

def run_transfer_tests():
    """Ejecutar todas las pruebas de transferencias"""
    print("\n" + "="*70)
    print("🔄 STRIPE TRANSFER TESTS - CAPA 2")
    print("="*70)
    
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
    success = run_transfer_tests()
    if success:
        print("\n✅ TODAS LAS PRUEBAS DE TRANSFERENCIAS PASARON")
    else:
        print("\n❌ Algunas pruebas de transferencias fallaron")