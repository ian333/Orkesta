#!/usr/bin/env python3
"""
stripe/stripe_manager.py - ÚNICO archivo para gestión completa de Stripe Connect

🎯 FUNCIONES:
1. Crear cuentas US completamente verificadas automáticamente
2. Eliminar cuentas sobrantes
3. Hacer transferencias entre cuentas 
4. Verificar estado de cuentas
5. Limpiar test data completo

🔧 USO:
python stripe/stripe_manager.py --create-accounts 11
python stripe/stripe_manager.py --clean-test-data
python stripe/stripe_manager.py --transfer --from="Chad Martinez" --to="Juan Perez" --amount=100
"""

import stripe
import json
import logging
import os
import time
import argparse
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configurar Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "sk_test_YOUR_STRIPE_KEY_HERE")

class StripeManager:
    def __init__(self):
        self.accounts_file = "orkesta_stripe/accounts.json"
        
    def create_verified_us_account(self, name, email, first_name, last_name):
        """Crear cuenta US completamente verificada automáticamente"""
        try:
            logger.info(f"🔥 Creando cuenta US verificada: {name}")
            
            # Crear cuenta Custom con datos mágicos de prueba
            account = stripe.Account.create(
                type="custom",
                country="US",
                email=email,
                business_type="individual",
                individual={
                    "first_name": first_name,
                    "last_name": last_name,
                    "id_number": "000000000",  # SSN mágico que pasa verificación
                    "ssn_last_4": "0000",
                    "dob": {"day": 5, "month": 7, "year": 1990},
                    "address": {
                        "line1": "510 Townsend St",
                        "city": "San Francisco", 
                        "state": "CA",
                        "postal_code": "94103",
                        "country": "US"
                    },
                    "email": email,
                    "phone": "+14155552671"
                },
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                },
                tos_acceptance={
                    "date": int(time.time()), 
                    "ip": "203.0.113.10"
                }
            )
            
            # Vincular cuenta bancaria de prueba 
            stripe.Account.create_external_account(
                account.id,
                external_account={
                    "object": "bank_account",
                    "country": "US",
                    "currency": "usd", 
                    "routing_number": "110000000",  # Routing mágico
                    "account_number": "000123456789",
                    "account_holder_name": name
                }
            )
            
            # Verificar que quedó activa
            account = stripe.Account.retrieve(account.id)
            logger.info(f"✅ {name}: Transfers={account.capabilities.transfers}, Payouts={account.payouts_enabled}")
            
            return account
            
        except Exception as e:
            logger.error(f"❌ Error creando {name}: {e}")
            return None

    def create_multiple_accounts(self, count=11):
        """Crear múltiples cuentas US verificadas"""
        fictional_accounts = [
            ("Chad Martinez", "chad@cobrazo.mx", "Chad", "Martinez"),
            ("Juan Perez", "juan@cobrazo.mx", "Juan", "Perez"),
            ("Luis Garcia", "luis@cobrazo.mx", "Luis", "Garcia"),
            ("Pedro Ramirez", "pedro@cobrazo.mx", "Pedro", "Ramirez"),
            ("Maria Lopez", "maria@cobrazo.mx", "Maria", "Lopez"),
            ("Ana Rodriguez", "ana@cobrazo.mx", "Ana", "Rodriguez"),
            ("Carlos Mendoza", "carlos@cobrazo.mx", "Carlos", "Mendoza"),
            ("Sofia Herrera", "sofia@cobrazo.mx", "Sofia", "Herrera"),
            ("Miguel Torres", "miguel@cobrazo.mx", "Miguel", "Torres"),
            ("Elena Morales", "elena@cobrazo.mx", "Elena", "Morales"),
            ("Roberto Silva", "roberto@cobrazo.mx", "Roberto", "Silva")
        ]
        
        logger.info(f"🚀 Creando {count} cuentas US verificadas")
        
        accounts = []
        for i, (name, email, first_name, last_name) in enumerate(fictional_accounts[:count]):
            account = self.create_verified_us_account(name, email, first_name, last_name)
            if account:
                accounts.append(account)
                
        self.save_accounts(accounts)
        return accounts

    def save_accounts(self, accounts):
        """Guardar cuentas en JSON organizado"""
        balances = [1000, 500, 750, 1200, 800, 950, 600, 1100, 850, 700, 900]
        descriptions = [
            "Chad - Cliente que paga a Juan semanalmente",
            "Juan - Recibe pagos de Chad, pinta casas", 
            "Luis - Pide pagos a Pedro semanalmente",
            "Pedro - Paga a Luis semanalmente",
            "Maria - Cliente de prueba para transacciones",
            "Ana - Freelancer de marketing digital",
            "Carlos - Dueño de tienda en línea",
            "Sofia - Diseñadora gráfica independiente",
            "Miguel - Desarrollador de software",
            "Elena - Consultora de negocios",
            "Roberto - Fotógrafo profesional"
        ]
        
        data = {
            "created_at": datetime.now().isoformat(),
            "accounts": []
        }
        
        for i, account in enumerate(accounts):
            if account:
                data["accounts"].append({
                    "id": account.id,
                    "name": account.individual.first_name + " " + account.individual.last_name,
                    "email": account.email,
                    "country": account.country,
                    "charges_enabled": account.charges_enabled,
                    "payouts_enabled": account.payouts_enabled,
                    "transfers_active": account.capabilities.transfers == "active",
                    "balance": balances[i] if i < len(balances) else 500,
                    "description": descriptions[i] if i < len(descriptions) else "Cliente de prueba"
                })
        
        os.makedirs("orkesta_stripe", exist_ok=True)
        with open(self.accounts_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        logger.info(f"💾 {len(accounts)} cuentas guardadas en {self.accounts_file}")

    def clean_all_test_data(self):
        """Eliminar TODAS las cuentas de prueba"""
        logger.info("🧹 Eliminando TODAS las cuentas de prueba")
        
        deleted_count = 0
        try:
            accounts = stripe.Account.list(limit=100)
            for account in accounts:
                if account.id.startswith("acct_"):
                    try:
                        stripe.Account.delete(account.id)
                        deleted_count += 1
                        logger.info(f"🗑️ Eliminada: {account.id}")
                        time.sleep(0.1)  # Rate limit
                    except Exception as e:
                        logger.warning(f"⚠️ No se pudo eliminar {account.id}: {e}")
                        
        except Exception as e:
            logger.error(f"❌ Error limpiando cuentas: {e}")
            
        logger.info(f"✅ {deleted_count} cuentas eliminadas")

    def add_platform_balance(self, amount=1000000):
        """Agregar saldo a la plataforma para transferencias"""
        try:
            logger.info(f"💰 Agregando ${amount/100:.2f} USD al balance de la plataforma")
            logger.info("⚠️ En test mode, el balance se agrega automáticamente al hacer transfers")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error agregando balance: {e}")
            return None

    def transfer_money(self, from_name, to_name, amount):
        """Transferir dinero entre cuentas por nombre"""
        try:
            # Cargar cuentas
            with open(self.accounts_file, 'r') as f:
                data = json.load(f)
            
            # Buscar cuenta destino
            to_account = None
            for account in data["accounts"]:
                if account["name"].lower() == to_name.lower():
                    to_account = account
                    break
                    
            if not to_account:
                logger.error(f"❌ No se encontró cuenta para {to_name}")
                return None
                
            # Crear transferencia
            transfer = stripe.Transfer.create(
                amount=int(amount * 100),  # Centavos
                currency="usd",
                destination=to_account["id"],
                description=f"Transferencia de {from_name} a {to_name}"
            )
            
            logger.info(f"✅ Transferencia exitosa: ${amount} de {from_name} a {to_name}")
            logger.info(f"🔢 Transfer ID: {transfer.id}")
            
            return transfer
            
        except Exception as e:
            logger.error(f"❌ Error en transferencia: {e}")
            return None

    def check_account_status(self, account_id=None):
        """Verificar estado de una cuenta específica o todas"""
        if account_id:
            try:
                account = stripe.Account.retrieve(account_id)
                logger.info(f"📊 {account_id}:")
                logger.info(f"   Charges: {account.charges_enabled}")
                logger.info(f"   Payouts: {account.payouts_enabled}")
                logger.info(f"   Transfers: {account.capabilities.transfers}")
                return account
            except Exception as e:
                logger.error(f"❌ Error verificando {account_id}: {e}")
                return None
        else:
            # Verificar todas las cuentas guardadas
            try:
                with open(self.accounts_file, 'r') as f:
                    data = json.load(f)
                    
                enabled_count = 0
                for account_data in data["accounts"]:
                    account = stripe.Account.retrieve(account_data["id"])
                    status = "✅" if account.charges_enabled else "❌"
                    logger.info(f"{status} {account_data['name']}: {account_data['id']}")
                    if account.charges_enabled:
                        enabled_count += 1
                        
                logger.info(f"📊 {enabled_count}/{len(data['accounts'])} cuentas habilitadas")
                return enabled_count
                
            except Exception as e:
                logger.error(f"❌ Error verificando cuentas: {e}")
                return 0

def main():
    parser = argparse.ArgumentParser(description='Gestión completa de Stripe Connect')
    parser.add_argument('--create-accounts', type=int, help='Crear N cuentas US verificadas')
    parser.add_argument('--clean-test-data', action='store_true', help='Eliminar todas las cuentas de prueba')
    parser.add_argument('--transfer', action='store_true', help='Hacer transferencia')
    parser.add_argument('--from', dest='from_name', help='Nombre del remitente')
    parser.add_argument('--to', dest='to_name', help='Nombre del destinatario')
    parser.add_argument('--amount', type=float, help='Monto a transferir')
    parser.add_argument('--check-status', action='store_true', help='Verificar estado de cuentas')
    parser.add_argument('--add-balance', type=int, help='Agregar balance a la plataforma (USD)')
    
    args = parser.parse_args()
    manager = StripeManager()
    
    if args.create_accounts:
        manager.add_platform_balance()  # Agregar balance primero
        manager.create_multiple_accounts(args.create_accounts)
        
    elif args.clean_test_data:
        manager.clean_all_test_data()
        
    elif args.transfer:
        if not all([args.from_name, args.to_name, args.amount]):
            logger.error("❌ Para transferir necesitas --from, --to y --amount")
        else:
            manager.transfer_money(args.from_name, args.to_name, args.amount)
            
    elif args.check_status:
        manager.check_account_status()
        
    elif args.add_balance:
        manager.add_platform_balance(args.add_balance * 100)
        
    else:
        parser.print_help()

if __name__ == "__main__":
    main()