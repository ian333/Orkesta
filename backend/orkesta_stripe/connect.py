"""
🔗 Stripe Connect Manager
========================

Maneja cuentas Connect: creación, onboarding y estado.
"""

import stripe
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import logging

from .types import ConnectAccount, ChargesMode, PricingMode, PayoutSchedule, FeePolicy

logger = logging.getLogger(__name__)

class StripeConnectManager:
    """Manager para cuentas Stripe Connect"""
    
    def __init__(self):
        # Configurar Stripe
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY not found in environment")
        
        self.client_id = os.getenv("STRIPE_CLIENT_ID")  # Para OAuth flow
        self.platform_account_id = os.getenv("PLATFORM_ACCOUNT_ID", "acct_platform")
        
        # Storage en memoria (en prod usar DB)
        self.accounts: Dict[str, ConnectAccount] = {}
        
    def create_express_account(self, tenant_id: str, email: str, 
                             country: str = "MX") -> ConnectAccount:
        """
        Crea una cuenta Express Connect.
        Express es más rápida de configurar que Standard.
        """
        try:
            # Crear cuenta en Stripe
            account = stripe.Account.create(
                type="express",
                country=country,
                email=email,
                capabilities={
                    "card_payments": {"requested": True},
                    "transfers": {"requested": True},
                    # Capabilities específicas para MX
                    "oxxo_payments": {"requested": True} if country == "MX" else None,
                    "sepa_debit_payments": {"requested": False}  # No para MX
                },
                business_type="individual",  # Simplificar para demo
                metadata={
                    "tenant_id": tenant_id,
                    "orkesta_integration": "true",
                    "created_by": "oco_connect_manager"
                }
            )
            
            # Crear registro local
            connect_account = ConnectAccount(
                account_id=account.id,
                tenant_id=tenant_id,
                email=email,
                country=country,
                currency="MXN" if country == "MX" else "USD"
            )
            
            # Guardar en storage
            self.accounts[account.id] = connect_account
            
            logger.info(f"Created Express account {account.id} for tenant {tenant_id}")
            
            return connect_account
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Express account: {e}")
            raise Exception(f"Stripe Connect error: {e.user_message}")
    
    def create_standard_account(self, tenant_id: str, email: str, 
                              country: str = "MX") -> ConnectAccount:
        """
        Crea una cuenta Standard Connect.
        Standard da más control pero requiere más configuración.
        """
        try:
            account = stripe.Account.create(
                type="standard",
                country=country,
                email=email,
                metadata={
                    "tenant_id": tenant_id,
                    "orkesta_integration": "true",
                    "created_by": "oco_connect_manager"
                }
            )
            
            connect_account = ConnectAccount(
                account_id=account.id,
                tenant_id=tenant_id,
                email=email,
                country=country,
                currency="MXN" if country == "MX" else "USD"
            )
            
            self.accounts[account.id] = connect_account
            
            logger.info(f"Created Standard account {account.id} for tenant {tenant_id}")
            
            return connect_account
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create Standard account: {e}")
            raise Exception(f"Stripe Connect error: {e.user_message}")
    
    def create_onboarding_link(self, account_id: str, 
                             return_url: str, refresh_url: str) -> str:
        """
        Crea link de onboarding para completar configuración.
        El usuario será redirigido aquí para completar su perfil.
        """
        try:
            link = stripe.AccountLink.create(
                account=account_id,
                return_url=return_url,
                refresh_url=refresh_url,
                type="account_onboarding"
            )
            
            logger.info(f"Created onboarding link for account {account_id}")
            
            return link.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create onboarding link: {e}")
            raise Exception(f"Stripe Connect error: {e.user_message}")
    
    def get_account_status(self, account_id: str) -> Dict[str, Any]:
        """
        Obtiene estado detallado de una cuenta Connect.
        Incluye capabilities, requirements y balance.
        """
        try:
            # Obtener account de Stripe
            account = stripe.Account.retrieve(account_id)
            
            # Obtener balance si está disponible
            balance = None
            try:
                balance = stripe.Balance.retrieve(stripe_account=account_id)
            except:
                pass  # Balance puede no estar disponible durante onboarding
            
            # Actualizar registro local
            if account_id in self.accounts:
                local_account = self.accounts[account_id]
                local_account.onboarding_complete = account.details_submitted
                local_account.capabilities_active = [
                    cap for cap, status in account.capabilities.items() 
                    if status == "active"
                ]
                local_account.requirements_pending = account.requirements.currently_due
                local_account.updated_at = datetime.now()
            
            status = {
                "account_id": account.id,
                "details_submitted": account.details_submitted,
                "charges_enabled": account.charges_enabled,
                "payouts_enabled": account.payouts_enabled,
                "capabilities": dict(account.capabilities),
                "requirements": {
                    "currently_due": account.requirements.currently_due,
                    "eventually_due": account.requirements.eventually_due,
                    "past_due": account.requirements.past_due,
                    "pending_verification": account.requirements.pending_verification
                },
                "balance": {
                    "available": [bal.dict() for bal in balance.available] if balance else [],
                    "pending": [bal.dict() for bal in balance.pending] if balance else []
                } if balance else None,
                "business_profile": account.business_profile.dict() if account.business_profile else None,
                "metadata": account.metadata
            }
            
            return status
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get account status: {e}")
            raise Exception(f"Stripe Connect error: {e.user_message}")
    
    def update_account_settings(self, account_id: str, 
                              charges_mode: ChargesMode = None,
                              pricing_mode: PricingMode = None,
                              payout_schedule: PayoutSchedule = None,
                              fee_policy: FeePolicy = None) -> bool:
        """
        Actualiza configuración de una cuenta Connect.
        """
        if account_id not in self.accounts:
            return False
        
        account = self.accounts[account_id]
        
        if charges_mode:
            account.charges_mode = charges_mode
        if pricing_mode:
            account.pricing_mode = pricing_mode
        if payout_schedule:
            account.payout_schedule = payout_schedule
        if fee_policy:
            account.fee_policy = fee_policy
        
        account.updated_at = datetime.now()
        
        # También actualizar en Stripe si es necesario
        try:
            if payout_schedule:
                stripe.Account.modify(
                    account_id,
                    settings={
                        "payouts": {
                            "schedule": {
                                "interval": payout_schedule.value
                            }
                        }
                    }
                )
        except stripe.error.StripeError as e:
            logger.warning(f"Failed to update Stripe account settings: {e}")
        
        logger.info(f"Updated settings for account {account_id}")
        return True
    
    def list_accounts_by_tenant(self, tenant_id: str) -> List[ConnectAccount]:
        """Lista todas las cuentas de un tenant"""
        return [
            account for account in self.accounts.values() 
            if account.tenant_id == tenant_id
        ]
    
    def get_account(self, account_id: str) -> Optional[ConnectAccount]:
        """Obtiene cuenta por ID"""
        return self.accounts.get(account_id)
    
    def delete_account(self, account_id: str) -> bool:
        """
        Elimina una cuenta Connect.
        CUIDADO: Esta operación es irreversible.
        """
        try:
            # Eliminar de Stripe
            stripe.Account.delete(account_id)
            
            # Eliminar de storage local
            if account_id in self.accounts:
                del self.accounts[account_id]
            
            logger.warning(f"Deleted account {account_id}")
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to delete account: {e}")
            return False
    
    def simulate_account_update_webhook(self, account_id: str) -> Dict[str, Any]:
        """
        Simula webhook de account.updated para testing.
        Útil para probar flujos de onboarding.
        """
        try:
            account = stripe.Account.retrieve(account_id)
            
            # Simular evento de webhook
            webhook_event = {
                "id": f"evt_test_{int(datetime.now().timestamp())}",
                "object": "event",
                "type": "account.updated",
                "data": {
                    "object": account
                },
                "created": int(datetime.now().timestamp()),
                "livemode": False,
                "account": account_id
            }
            
            logger.info(f"Simulated account.updated webhook for {account_id}")
            
            return webhook_event
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to simulate webhook: {e}")
            return {}
    
    def get_capabilities_status(self, account_id: str) -> Dict[str, str]:
        """
        Obtiene estado de capabilities para una cuenta.
        Útil para debugging de onboarding.
        """
        try:
            account = stripe.Account.retrieve(account_id)
            return dict(account.capabilities)
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get capabilities: {e}")
            return {}
    
    def export_accounts(self) -> List[Dict[str, Any]]:
        """Exporta todas las cuentas para backup/debug"""
        return [account.to_dict() for account in self.accounts.values()]
    
    def import_accounts(self, accounts_data: List[Dict[str, Any]]) -> int:
        """Importa cuentas desde backup"""
        imported = 0
        for account_data in accounts_data:
            try:
                # Recrear fee_policy
                fee_data = account_data.get("fee_policy", {})
                fee_policy = FeePolicy(
                    application_fee_pct=fee_data.get("application_fee_pct", 0.6),
                    application_fee_fixed=fee_data.get("application_fee_fixed", 2.0),
                    min_fee=fee_data.get("min_fee", 5.0),
                    max_fee=fee_data.get("max_fee")
                )
                
                account = ConnectAccount(
                    account_id=account_data["account_id"],
                    tenant_id=account_data["tenant_id"],
                    email=account_data["email"],
                    country=account_data.get("country", "MX"),
                    currency=account_data.get("currency", "MXN"),
                    charges_mode=ChargesMode(account_data.get("charges_mode", "direct")),
                    pricing_mode=PricingMode(account_data.get("pricing_mode", "platform_handles_pricing")),
                    payout_schedule=PayoutSchedule(account_data.get("payout_schedule", "weekly")),
                    fee_policy=fee_policy,
                    onboarding_complete=account_data.get("onboarding_complete", False),
                    capabilities_active=account_data.get("capabilities_active", []),
                    requirements_pending=account_data.get("requirements_pending", [])
                )
                
                self.accounts[account.account_id] = account
                imported += 1
                
            except Exception as e:
                logger.error(f"Failed to import account {account_data.get('account_id')}: {e}")
        
        logger.info(f"Imported {imported} accounts")
        return imported

# Instancia global
connect_manager = StripeConnectManager()

if __name__ == "__main__":
    # Ejemplo de uso
    print("🔗 Stripe Connect Manager - Test")
    print("=" * 40)
    
    manager = StripeConnectManager()
    
    # En un entorno real, estos datos vendrían del tenant
    tenant_id = "lb-productions"
    email = "admin@lb-productions.com"
    
    try:
        # Crear cuenta Express
        account = manager.create_express_account(tenant_id, email)
        print(f"✅ Created account: {account.account_id}")
        
        # Crear link de onboarding
        onboarding_url = manager.create_onboarding_link(
            account.account_id,
            return_url="https://orkesta.mx/connect/return",
            refresh_url="https://orkesta.mx/connect/refresh"
        )
        print(f"🔗 Onboarding URL: {onboarding_url}")
        
        # Obtener estado
        status = manager.get_account_status(account.account_id)
        print(f"📊 Account status: {status['details_submitted']}")
        print(f"⚡ Charges enabled: {status['charges_enabled']}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Asegúrate de tener STRIPE_SECRET_KEY configurado")