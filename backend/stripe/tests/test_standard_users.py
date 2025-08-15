#!/usr/bin/env python3
"""
test_standard_users.py - Pruebas estandarizadas con los 11 usuarios oficiales

🎯 PROPÓSITO:
- Usar SIEMPRE los mismos 11 usuarios
- Casos de prueba consistentes y repetibles  
- Verificar que transacciones entre usuarios funcionan
- Baseline para desarrollo de agentes IA

✅ USUARIOS OFICIALES:
Chad, Juan, Luis, Pedro, Maria, Ana, Carlos, Sofia, Miguel, Elena, Roberto
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import stripe
import json
import pytest
from datetime import datetime

# Configurar Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_YOUR_STRIPE_KEY_HERE")

class TestStandardUsers:
    """Pruebas con usuarios estandarizados - SIEMPRE usar estos"""
    
    @classmethod
    def setup_class(cls):
        """Cargar usuarios estándar"""
        with open('stripe/accounts.json', 'r') as f:
            data = json.load(f)
        cls.users = data['accounts']
        
        # Mapeo estándar - SIEMPRE usar estos índices
        cls.chad = cls.users[0]    # Chad Martinez
        cls.juan = cls.users[1]    # Juan Perez
        cls.luis = cls.users[2]    # Luis Garcia  
        cls.pedro = cls.users[3]   # Pedro Ramirez
        cls.maria = cls.users[4]   # Maria Lopez
        cls.ana = cls.users[5]     # Ana Rodriguez
        cls.carlos = cls.users[6]  # Carlos Mendoza
        cls.sofia = cls.users[7]   # Sofia Herrera
        cls.miguel = cls.users[8]  # Miguel Torres
        cls.elena = cls.users[9]   # Elena Morales
        cls.roberto = cls.users[10] # Roberto Silva
        
        print(f"\n👥 Cargados {len(cls.users)} usuarios estándar")
    
    def test_01_usuarios_correctos(self):
        """Verificar que tenemos exactamente los 11 usuarios correctos"""
        
        expected_names = [
            "Chad Martinez", "Juan Perez", "Luis Garcia", "Pedro Ramirez", "Maria Lopez",
            "Ana Rodriguez", "Carlos Mendoza", "Sofia Herrera", "Miguel Torres", 
            "Elena Morales", "Roberto Silva"
        ]
        
        assert len(self.users) == 11, f"Deben ser 11 usuarios, encontrados {len(self.users)}"
        
        for i, expected_name in enumerate(expected_names):
            actual_name = self.users[i]['name']
            assert actual_name == expected_name, f"Usuario {i}: esperado {expected_name}, encontrado {actual_name}"
        
        print("✅ Los 11 usuarios estándar están correctos")
    
    def test_02_todos_usuarios_habilitados(self):
        """Verificar que todos los usuarios están habilitados en Stripe"""
        
        enabled_count = 0
        
        for user in self.users:
            try:
                account = stripe.Account.retrieve(user['id'])
                
                is_enabled = (
                    account.charges_enabled and 
                    account.capabilities.transfers == 'active'
                )
                
                if is_enabled:
                    enabled_count += 1
                    print(f"   ✅ {user['name']}: Habilitado")
                else:
                    print(f"   ❌ {user['name']}: Deshabilitado")
                    
            except Exception as e:
                print(f"   ❌ {user['name']}: Error - {e}")
        
        assert enabled_count == 11, f"Todos los usuarios deben estar habilitados, solo {enabled_count}/11 están activos"
    
    def test_03_caso_principal_chad_juan(self):
        """Caso principal: Chad paga a Juan por pintar"""
        
        print("\n🎯 Caso principal: Chad → Juan $200")
        
        # Verificar balance previo de Juan
        juan_balance_before = stripe.Balance.retrieve(stripe_account=self.juan['id'])
        balance_before = juan_balance_before.available[0].amount / 100
        
        # Ejecutar transferencia
        transfer = stripe.Transfer.create(
            amount=20000,  # $200 USD
            currency='usd',
            destination=self.juan['id'],
            description="TEST: Chad paga a Juan por pintar casa"
        )
        
        assert transfer.amount == 20000
        assert transfer.destination == self.juan['id']
        
        # Verificar que Juan recibió el dinero
        juan_balance_after = stripe.Balance.retrieve(stripe_account=self.juan['id'])
        balance_after = juan_balance_after.available[0].amount / 100
        
        assert balance_after > balance_before, "Juan debería tener más dinero después del pago"
        
        print(f"✅ Chad → Juan $200: {transfer.id}")
        print(f"💰 Juan balance: ${balance_before:.2f} → ${balance_after:.2f}")
    
    def test_04_caso_subcontrato_juan_luis(self):
        """Caso subcontrato: Juan paga a Luis por ayuda"""
        
        print("\n🔧 Caso subcontrato: Juan → Luis $75")
        
        luis_balance_before = stripe.Balance.retrieve(stripe_account=self.luis['id'])
        balance_before = luis_balance_before.available[0].amount / 100
        
        transfer = stripe.Transfer.create(
            amount=7500,  # $75 USD
            currency='usd',
            destination=self.luis['id'],
            description="TEST: Juan paga a Luis por ayudar con pintura"
        )
        
        luis_balance_after = stripe.Balance.retrieve(stripe_account=self.luis['id'])
        balance_after = luis_balance_after.available[0].amount / 100
        
        assert balance_after > balance_before
        
        print(f"✅ Juan → Luis $75: {transfer.id}")
        print(f"💰 Luis balance: ${balance_before:.2f} → ${balance_after:.2f}")
    
    def test_05_caso_freelancer_ana_sofia(self):
        """Caso freelancer: Ana paga a Sofia por diseño"""
        
        print("\n🎨 Caso freelancer: Ana → Sofia $100")
        
        sofia_balance_before = stripe.Balance.retrieve(stripe_account=self.sofia['id'])
        balance_before = sofia_balance_before.available[0].amount / 100
        
        transfer = stripe.Transfer.create(
            amount=10000,  # $100 USD
            currency='usd',
            destination=self.sofia['id'],
            description="TEST: Ana paga a Sofia por diseño de logo"
        )
        
        sofia_balance_after = stripe.Balance.retrieve(stripe_account=self.sofia['id'])
        balance_after = sofia_balance_after.available[0].amount / 100
        
        assert balance_after > balance_before
        
        print(f"✅ Ana → Sofia $100: {transfer.id}")
        print(f"💰 Sofia balance: ${balance_before:.2f} → ${balance_after:.2f}")
    
    def test_06_caso_comercio_pedro_luis(self):
        """Caso comercio: Pedro vende materiales a Luis"""
        
        print("\n🛒 Caso comercio: Pedro → Luis $150")
        
        luis_balance_before = stripe.Balance.retrieve(stripe_account=self.luis['id'])
        balance_before = luis_balance_before.available[0].amount / 100
        
        transfer = stripe.Transfer.create(
            amount=15000,  # $150 USD
            currency='usd',
            destination=self.luis['id'],
            description="TEST: Pedro vende materiales a Luis"
        )
        
        luis_balance_after = stripe.Balance.retrieve(stripe_account=self.luis['id'])
        balance_after = luis_balance_after.available[0].amount / 100
        
        assert balance_after > balance_before
        
        print(f"✅ Pedro → Luis $150: {transfer.id}")
        print(f"💰 Luis balance: ${balance_before:.2f} → ${balance_after:.2f}")
    
    def test_07_caso_emprendedora_maria(self):
        """Caso emprendedora: Maria hace transacciones diversas"""
        
        print("\n💼 Caso emprendedora: Maria → Carlos $80")
        
        carlos_balance_before = stripe.Balance.retrieve(stripe_account=self.carlos['id'])
        balance_before = carlos_balance_before.available[0].amount / 100
        
        transfer = stripe.Transfer.create(
            amount=8000,  # $80 USD
            currency='usd',
            destination=self.carlos['id'],
            description="TEST: Maria compra en tienda de Carlos"
        )
        
        carlos_balance_after = stripe.Balance.retrieve(stripe_account=self.carlos['id'])
        balance_after = carlos_balance_after.available[0].amount / 100
        
        assert balance_after > balance_before
        
        print(f"✅ Maria → Carlos $80: {transfer.id}")
        print(f"💰 Carlos balance: ${balance_before:.2f} → ${balance_after:.2f}")
    
    def test_08_verificar_balances_finales(self):
        """Verificar que todos los balances son consistentes"""
        
        print("\n💰 Balances finales de todos los usuarios:")
        
        total_balance = 0
        
        for user in self.users:
            try:
                balance = stripe.Balance.retrieve(stripe_account=user['id'])
                available = balance.available[0].amount / 100 if balance.available else 0
                total_balance += available
                
                print(f"   👤 {user['name']:<15}: ${available:>8.2f}")
                
                # Verificar que nadie tiene balance negativo
                assert available >= 0, f"{user['name']} no puede tener balance negativo"
                
            except Exception as e:
                print(f"   ❌ {user['name']}: Error - {e}")
        
        print(f"\n💰 Balance total del ecosistema: ${total_balance:.2f}")
        
        # El balance total debe ser positivo
        assert total_balance > 0, "El ecosistema debe tener balance positivo"
    
    def test_09_mapeo_nombres_ids(self):
        """Verificar mapeo correcto de nombres a IDs para comandos de voz"""
        
        print("\n🎤 Verificando mapeo para comandos de voz:")
        
        # Mapeo que usarán los agentes de IA
        user_map = {
            'chad': self.chad['id'],
            'juan': self.juan['id'],
            'luis': self.luis['id'],
            'pedro': self.pedro['id'],
            'maria': self.maria['id'],
            'ana': self.ana['id'],
            'carlos': self.carlos['id'],
            'sofia': self.sofia['id'],
            'miguel': self.miguel['id'],
            'elena': self.elena['id'],
            'roberto': self.roberto['id']
        }
        
        # Verificar que todos los IDs existen
        for name, stripe_id in user_map.items():
            try:
                account = stripe.Account.retrieve(stripe_id)
                print(f"   ✅ {name:>8} → {stripe_id}")
                assert account.id == stripe_id
            except Exception as e:
                pytest.fail(f"Error verificando {name}: {e}")
        
        # Guardar mapeo para uso de agentes
        with open('stripe/user_map.json', 'w') as f:
            json.dump({
                'created_at': datetime.now().isoformat(),
                'user_map': user_map,
                'description': 'Mapeo de nombres a Stripe IDs para comandos de voz'
            }, f, indent=2)
        
        print(f"💾 Mapeo guardado en stripe/user_map.json")

def run_standard_tests():
    """Ejecutar todas las pruebas estándar"""
    print("\n" + "="*70)
    print("👥 PRUEBAS ESTANDARIZADAS - 11 USUARIOS OFICIALES")
    print("="*70)
    
    import subprocess
    
    result = subprocess.run([
        'python', '-m', 'pytest',
        __file__,
        '-v', '-s', '--tb=short'
    ], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("⚠️ Warnings:")
        print(result.stderr)
    
    return result.returncode == 0

if __name__ == "__main__":
    success = run_standard_tests()
    if success:
        print("\n✅ TODAS LAS PRUEBAS ESTÁNDAR PASARON")
        print("🎯 Los 11 usuarios están listos para desarrollo")
    else:
        print("\n❌ Algunas pruebas estándar fallaron")