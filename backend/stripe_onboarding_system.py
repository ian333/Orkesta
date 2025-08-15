#!/usr/bin/env python3
"""
🏗️ STRIPE CONNECT ONBOARDING SYSTEM
===================================

Sistema para completar el onboarding de cuentas Connect usando Stripe-hosted onboarding.
Según la documentación de Stripe, esta es la opción más simple y recomendada.
"""

import stripe
import json
import logging
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

class StripeOnboardingManager:
    """Manager para onboarding hosted de Stripe Connect"""
    
    def __init__(self):
        self.accounts_file = "orkesta_stripe/accounts.json"
        
    def load_accounts(self):
        """Cargar cuentas desde el archivo JSON"""
        try:
            with open(self.accounts_file, 'r') as f:
                data = json.load(f)
            return data.get("accounts", [])
        except Exception as e:
            logger.error(f"Error cargando cuentas: {e}")
            return []
    
    def create_onboarding_link(self, account_id, account_name):
        """
        Crear Account Link para onboarding hosted de Stripe
        
        Esto genera una URL donde el usuario puede completar el onboarding
        directamente en los servidores de Stripe con nuestro branding.
        """
        try:
            logger.info(f"🔗 Creando link de onboarding para {account_name} ({account_id})")
            
            # Crear Account Link para onboarding
            account_link = stripe.AccountLink.create(
                account=account_id,
                refresh_url=f"https://localhost:8000/reauth/{account_id}",  # URL si necesita reautenticarse
                return_url=f"https://localhost:8000/onboarding/success/{account_id}",  # URL de éxito
                type="account_onboarding",  # Tipo específico para onboarding
                # Agregar metadata para tracking
                collect="eventually_due"  # Recopilar solo información requerida
            )
            
            logger.info(f"✅ Link creado: {account_link.url}")
            logger.info(f"⏱️ Expira en: {account_link.expires_at}")
            
            return {
                "account_id": account_id,
                "account_name": account_name,
                "onboarding_url": account_link.url,
                "expires_at": account_link.expires_at,
                "created_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Error creando link para {account_name}: {e}")
            return None
    
    def create_all_onboarding_links(self):
        """Crear links de onboarding para todas las cuentas"""
        accounts = self.load_accounts()
        
        if not accounts:
            logger.error("No se encontraron cuentas para onboarding")
            return []
        
        logger.info(f"🚀 Creando links de onboarding para {len(accounts)} cuentas")
        
        onboarding_links = []
        for account in accounts:
            link_data = self.create_onboarding_link(
                account["id"], 
                account["name"]
            )
            if link_data:
                onboarding_links.append(link_data)
        
        # Guardar links en archivo
        self.save_onboarding_links(onboarding_links)
        return onboarding_links
    
    def save_onboarding_links(self, links):
        """Guardar links de onboarding en archivo JSON"""
        filename = "orkesta_stripe/onboarding_links.json"
        
        data = {
            "created_at": datetime.now().isoformat(),
            "total_accounts": len(links),
            "links": links
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"💾 Links guardados en {filename}")
    
    def check_onboarding_status(self, account_id):
        """Verificar estado de onboarding de una cuenta"""
        try:
            account = stripe.Account.retrieve(account_id)
            
            # Verificar requirements
            requirements = account.requirements
            currently_due = requirements.currently_due if requirements else []
            eventually_due = requirements.eventually_due if requirements else []
            
            status = {
                "account_id": account_id,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "details_submitted": account.details_submitted,
                "currently_due": currently_due,
                "eventually_due": eventually_due,
                "is_complete": len(currently_due) == 0 and account.charges_enabled
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error verificando status de {account_id}: {e}")
            return None
    
    def check_all_accounts_status(self):
        """Verificar estado de onboarding de todas las cuentas"""
        accounts = self.load_accounts()
        
        logger.info(f"📊 Verificando estado de {len(accounts)} cuentas")
        print("\n" + "="*80)
        print("🔍 ESTADO DE ONBOARDING DE CUENTAS STRIPE CONNECT")
        print("="*80)
        
        completed_count = 0
        for account in accounts:
            status = self.check_onboarding_status(account["id"])
            if status:
                status_icon = "✅" if status["is_complete"] else "⏳"
                print(f"{status_icon} {account['name']}")
                print(f"   ID: {account['id']}")
                print(f"   Charges: {status['charges_enabled']}")
                print(f"   Payouts: {status['payouts_enabled']}")
                print(f"   Details: {status['details_submitted']}")
                
                if status["currently_due"]:
                    print(f"   📋 Pendientes: {', '.join(status['currently_due'])}")
                
                if status["is_complete"]:
                    completed_count += 1
                print()
        
        print(f"📈 Progreso: {completed_count}/{len(accounts)} cuentas completadas")
        print("="*80)
        
        return completed_count
    
    def generate_onboarding_instructions(self):
        """Generar instrucciones de onboarding para el usuario"""
        links_file = "orkesta_stripe/onboarding_links.json"
        
        try:
            with open(links_file, 'r') as f:
                data = json.load(f)
            
            links = data.get("links", [])
            
            print("\n" + "🎯" + "="*79)
            print("INSTRUCCIONES DE ONBOARDING - STRIPE CONNECT")
            print("="*80)
            print("Para completar la configuración de las cuentas Connect, sigue estos pasos:")
            print()
            
            for i, link in enumerate(links, 1):
                print(f"{i}. {link['account_name']}")
                print(f"   🔗 URL: {link['onboarding_url']}")
                print(f"   ⏱️ Válida hasta: {link['expires_at']}")
                print()
            
            print("📝 INSTRUCCIONES:")
            print("1. Abre cada URL en tu navegador")
            print("2. Completa el formulario de onboarding de Stripe")
            print("3. Usa datos de prueba (Stripe te dará opciones)")
            print("4. Una vez completado, ejecuta el check de estado")
            print()
            print("🔧 COMANDO PARA VERIFICAR:")
            print("python stripe_onboarding_system.py --check-status")
            print("="*80)
            
        except Exception as e:
            logger.error(f"Error generando instrucciones: {e}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Sistema de Onboarding Stripe Connect')
    parser.add_argument('--create-links', action='store_true', help='Crear links de onboarding')
    parser.add_argument('--check-status', action='store_true', help='Verificar estado de onboarding')
    parser.add_argument('--instructions', action='store_true', help='Mostrar instrucciones')
    
    args = parser.parse_args()
    
    manager = StripeOnboardingManager()
    
    if args.create_links:
        links = manager.create_all_onboarding_links()
        if links:
            print(f"\n✅ {len(links)} links de onboarding creados exitosamente!")
            manager.generate_onboarding_instructions()
    
    elif args.check_status:
        manager.check_all_accounts_status()
    
    elif args.instructions:
        manager.generate_onboarding_instructions()
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()