"""
🛒 Checkout Orchestrator - Los 3 Modos de Stripe Connect
======================================================

Direct: Conectado paga fees, app fee separado
Destination: Plataforma paga fees, transfiere neto
Separate: Multi-split, plataforma maneja todo
"""

import stripe
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
import logging
from urllib.parse import urlencode

from .types import (
    CheckoutSession, ChargesMode, PaymentMethod, 
    ConnectAccount, FeePolicy, STRIPE_MX_FEES
)
from .connect import connect_manager
from .fees import FeeCalculator

logger = logging.getLogger(__name__)

class CheckoutOrchestrator:
    """Orquestador de checkout con los 3 modos de Connect"""
    
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY not found in environment")
        
        self.fee_calculator = FeeCalculator()
        self.base_url = os.getenv("ORKESTA_BASE_URL", "https://orkesta.mx")
        
        # Storage temporal (en prod usar DB)
        self.sessions: Dict[str, CheckoutSession] = {}
    
    def create_checkout_session(self, 
                              tenant_id: str,
                              order_id: str,
                              amount: float,
                              currency: str = "MXN",
                              payment_methods: List[PaymentMethod] = None,
                              success_url: str = None,
                              cancel_url: str = None,
                              metadata: Dict[str, str] = None) -> CheckoutSession:
        """
        Crea sesión de checkout según la configuración del tenant.
        Determina automáticamente el modo (Direct/Destination/Separate).
        """
        
        if payment_methods is None:
            payment_methods = [PaymentMethod.CARD, PaymentMethod.OXXO]
        
        # Obtener cuenta Connect del tenant
        accounts = connect_manager.list_accounts_by_tenant(tenant_id)
        if not accounts:
            raise ValueError(f"No Connect account found for tenant {tenant_id}")
        
        account = accounts[0]  # Usar primera cuenta activa
        
        if not account.onboarding_complete:
            raise ValueError(f"Connect account {account.account_id} onboarding not complete")
        
        # Configurar URLs por defecto
        if success_url is None:
            success_url = f"{self.base_url}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}"
        if cancel_url is None:
            cancel_url = f"{self.base_url}/checkout/cancel"
        
        # Calcular application fee
        app_fee_amount = account.fee_policy.calculate(amount)
        
        # Crear sesión según modo
        if account.charges_mode == ChargesMode.DIRECT:
            session = self._create_direct_session(
                account, order_id, amount, currency, payment_methods,
                success_url, cancel_url, app_fee_amount, metadata
            )
        elif account.charges_mode == ChargesMode.DESTINATION:
            session = self._create_destination_session(
                account, order_id, amount, currency, payment_methods,
                success_url, cancel_url, app_fee_amount, metadata
            )
        elif account.charges_mode == ChargesMode.SEPARATE:
            session = self._create_separate_session(
                account, order_id, amount, currency, payment_methods,
                success_url, cancel_url, app_fee_amount, metadata
            )
        else:
            raise ValueError(f"Unknown charges mode: {account.charges_mode}")
        
        # Guardar sesión
        self.sessions[session.session_id] = session
        
        logger.info(f"Created {account.charges_mode.value} checkout session {session.session_id}")
        
        return session
    
    def _create_direct_session(self, account: ConnectAccount, order_id: str,
                             amount: float, currency: str, payment_methods: List[PaymentMethod],
                             success_url: str, cancel_url: str, app_fee_amount: int,
                             metadata: Dict[str, str] = None) -> CheckoutSession:
        """
        Modo DIRECT: El conectado paga los fees de Stripe.
        Nosotros cobramos application_fee_amount separado.
        """
        
        try:
            # Configurar métodos de pago
            stripe_payment_methods = []
            if PaymentMethod.CARD in payment_methods:
                stripe_payment_methods.append("card")
            if PaymentMethod.OXXO in payment_methods:
                stripe_payment_methods.append("oxxo")
            
            # Crear sesión de checkout
            stripe_session = stripe.checkout.Session.create(
                payment_method_types=stripe_payment_methods,
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {
                            "name": f"Orden {order_id}",
                            "description": f"Pago para tenant {account.tenant_id}"
                        },
                        "unit_amount": int(amount * 100)  # Convertir a centavos
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                
                # CONFIGURACIÓN DIRECT
                payment_intent_data={
                    "on_behalf_of": account.account_id,  # Cargo en nombre del conectado
                    "transfer_data": {
                        "destination": account.account_id  # Transferir al conectado
                    },
                    "application_fee_amount": app_fee_amount,  # Nuestro fee
                    "metadata": {
                        "order_id": order_id,
                        "tenant_id": account.tenant_id,
                        "charges_mode": "direct",
                        **(metadata or {})
                    }
                },
                
                metadata={
                    "order_id": order_id,
                    "tenant_id": account.tenant_id,
                    "charges_mode": "direct"
                },
                
                expires_at=int((datetime.now() + timedelta(hours=1)).timestamp())
            )
            
            session = CheckoutSession(
                session_id=stripe_session.id,
                tenant_id=account.tenant_id,
                order_id=order_id,
                amount=amount,
                currency=currency,
                payment_methods=payment_methods,
                connect_account_id=account.account_id,
                charges_mode=ChargesMode.DIRECT,
                application_fee_amount=app_fee_amount,
                success_url=success_url,
                cancel_url=cancel_url,
                checkout_url=stripe_session.url,
                expires_at=datetime.fromtimestamp(stripe_session.expires_at),
                metadata=metadata or {}
            )
            
            return session
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create direct session: {e}")
            raise Exception(f"Stripe error: {e.user_message}")
    
    def _create_destination_session(self, account: ConnectAccount, order_id: str,
                                  amount: float, currency: str, payment_methods: List[PaymentMethod],
                                  success_url: str, cancel_url: str, app_fee_amount: int,
                                  metadata: Dict[str, str] = None) -> CheckoutSession:
        """
        Modo DESTINATION: Nosotros pagamos los fees de Stripe.
        Transferimos el neto al conectado, menos nuestro fee.
        """
        
        try:
            stripe_payment_methods = []
            if PaymentMethod.CARD in payment_methods:
                stripe_payment_methods.append("card")
            if PaymentMethod.OXXO in payment_methods:
                stripe_payment_methods.append("oxxo")
            
            stripe_session = stripe.checkout.Session.create(
                payment_method_types=stripe_payment_methods,
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {
                            "name": f"Orden {order_id}",
                            "description": f"Pago para tenant {account.tenant_id}"
                        },
                        "unit_amount": int(amount * 100)
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                
                # CONFIGURACIÓN DESTINATION
                payment_intent_data={
                    "transfer_data": {
                        "destination": account.account_id,
                        # El amount se transfiere automáticamente menos app fee
                        "amount": int(amount * 100) - app_fee_amount
                    },
                    "application_fee_amount": app_fee_amount,
                    "metadata": {
                        "order_id": order_id,
                        "tenant_id": account.tenant_id,
                        "charges_mode": "destination",
                        **(metadata or {})
                    }
                },
                
                metadata={
                    "order_id": order_id,
                    "tenant_id": account.tenant_id,
                    "charges_mode": "destination"
                },
                
                expires_at=int((datetime.now() + timedelta(hours=1)).timestamp())
            )
            
            session = CheckoutSession(
                session_id=stripe_session.id,
                tenant_id=account.tenant_id,
                order_id=order_id,
                amount=amount,
                currency=currency,
                payment_methods=payment_methods,
                connect_account_id=account.account_id,
                charges_mode=ChargesMode.DESTINATION,
                application_fee_amount=app_fee_amount,
                success_url=success_url,
                cancel_url=cancel_url,
                checkout_url=stripe_session.url,
                expires_at=datetime.fromtimestamp(stripe_session.expires_at),
                metadata=metadata or {}
            )
            
            return session
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create destination session: {e}")
            raise Exception(f"Stripe error: {e.user_message}")
    
    def _create_separate_session(self, account: ConnectAccount, order_id: str,
                               amount: float, currency: str, payment_methods: List[PaymentMethod],
                               success_url: str, cancel_url: str, app_fee_amount: int,
                               metadata: Dict[str, str] = None) -> CheckoutSession:
        """
        Modo SEPARATE: Cobramos en nuestra cuenta.
        Después hacemos transfers manuales a uno o más conectados.
        """
        
        try:
            stripe_payment_methods = []
            if PaymentMethod.CARD in payment_methods:
                stripe_payment_methods.append("card")
            if PaymentMethod.OXXO in payment_methods:
                stripe_payment_methods.append("oxxo")
            
            # En modo separate, NO especificamos transfer_data ni on_behalf_of
            # Todo se queda en nuestra cuenta hasta que hagamos transfers
            stripe_session = stripe.checkout.Session.create(
                payment_method_types=stripe_payment_methods,
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {
                            "name": f"Orden {order_id}",
                            "description": f"Pago para tenant {account.tenant_id} (Separate mode)"
                        },
                        "unit_amount": int(amount * 100)
                    },
                    "quantity": 1
                }],
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                
                # CONFIGURACIÓN SEPARATE
                payment_intent_data={
                    "metadata": {
                        "order_id": order_id,
                        "tenant_id": account.tenant_id,
                        "charges_mode": "separate",
                        "connect_account_id": account.account_id,
                        "app_fee_amount": str(app_fee_amount),
                        **(metadata or {})
                    }
                },
                
                metadata={
                    "order_id": order_id,
                    "tenant_id": account.tenant_id,
                    "charges_mode": "separate"
                },
                
                expires_at=int((datetime.now() + timedelta(hours=1)).timestamp())
            )
            
            session = CheckoutSession(
                session_id=stripe_session.id,
                tenant_id=account.tenant_id,
                order_id=order_id,
                amount=amount,
                currency=currency,
                payment_methods=payment_methods,
                connect_account_id=account.account_id,
                charges_mode=ChargesMode.SEPARATE,
                application_fee_amount=app_fee_amount,
                success_url=success_url,
                cancel_url=cancel_url,
                checkout_url=stripe_session.url,
                expires_at=datetime.fromtimestamp(stripe_session.expires_at),
                metadata=metadata or {}
            )
            
            return session
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create separate session: {e}")
            raise Exception(f"Stripe error: {e.user_message}")
    
    def get_session(self, session_id: str) -> Optional[CheckoutSession]:
        """Obtiene una sesión por ID"""
        return self.sessions.get(session_id)
    
    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Obtiene estado actual de una sesión desde Stripe.
        Incluye payment_intent, customer y line_items.
        """
        try:
            stripe_session = stripe.checkout.Session.retrieve(
                session_id,
                expand=['payment_intent', 'customer', 'line_items']
            )
            
            # Actualizar sesión local si existe
            if session_id in self.sessions:
                local_session = self.sessions[session_id]
                local_session.status = stripe_session.status
                local_session.payment_intent_id = stripe_session.payment_intent
            
            return {
                "session_id": stripe_session.id,
                "status": stripe_session.status,
                "payment_status": stripe_session.payment_status,
                "amount_total": stripe_session.amount_total,
                "currency": stripe_session.currency,
                "customer": stripe_session.customer,
                "payment_intent": stripe_session.payment_intent,
                "metadata": stripe_session.metadata,
                "created": stripe_session.created,
                "expires_at": stripe_session.expires_at
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to get session status: {e}")
            return {"error": str(e)}
    
    def create_payment_link(self, tenant_id: str, order_id: str, amount: float,
                          description: str = None, currency: str = "MXN") -> str:
        """
        Crea Payment Link (alternativa a Checkout Session).
        Útil para enviar por WhatsApp/email.
        """
        
        # Obtener cuenta Connect
        accounts = connect_manager.list_accounts_by_tenant(tenant_id)
        if not accounts:
            raise ValueError(f"No Connect account found for tenant {tenant_id}")
        
        account = accounts[0]
        app_fee_amount = account.fee_policy.calculate(amount)
        
        try:
            link = stripe.PaymentLink.create(
                line_items=[{
                    "price_data": {
                        "currency": currency.lower(),
                        "product_data": {
                            "name": description or f"Orden {order_id}",
                            "description": f"Tenant: {tenant_id}"
                        },
                        "unit_amount": int(amount * 100)
                    },
                    "quantity": 1
                }],
                
                # Configurar según modo del tenant
                payment_intent_data={
                    "on_behalf_of": account.account_id if account.charges_mode == ChargesMode.DIRECT else None,
                    "transfer_data": {
                        "destination": account.account_id,
                        "amount": int(amount * 100) - app_fee_amount if account.charges_mode == ChargesMode.DESTINATION else None
                    } if account.charges_mode != ChargesMode.SEPARATE else None,
                    "application_fee_amount": app_fee_amount if account.charges_mode != ChargesMode.SEPARATE else None,
                    "metadata": {
                        "order_id": order_id,
                        "tenant_id": tenant_id,
                        "charges_mode": account.charges_mode.value
                    }
                } if account.charges_mode != ChargesMode.SEPARATE else {
                    "metadata": {
                        "order_id": order_id,
                        "tenant_id": tenant_id,
                        "charges_mode": "separate",
                        "connect_account_id": account.account_id,
                        "app_fee_amount": str(app_fee_amount)
                    }
                },
                
                metadata={
                    "order_id": order_id,
                    "tenant_id": tenant_id,
                    "charges_mode": account.charges_mode.value
                }
            )
            
            logger.info(f"Created payment link for tenant {tenant_id}, order {order_id}")
            
            return link.url
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to create payment link: {e}")
            raise Exception(f"Stripe error: {e.user_message}")
    
    def expire_session(self, session_id: str) -> bool:
        """Expira una sesión manualmente"""
        try:
            stripe.checkout.Session.expire(session_id)
            
            if session_id in self.sessions:
                self.sessions[session_id].status = "expired"
            
            logger.info(f"Expired session {session_id}")
            return True
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to expire session: {e}")
            return False
    
    def list_sessions_by_tenant(self, tenant_id: str) -> List[CheckoutSession]:
        """Lista sesiones de un tenant"""
        return [
            session for session in self.sessions.values()
            if session.tenant_id == tenant_id
        ]
    
    def calculate_effective_costs(self, amount: float, payment_method: PaymentMethod,
                                charges_mode: ChargesMode, app_fee_pct: float = 0.6,
                                app_fee_fixed: float = 2.0) -> Dict[str, float]:
        """
        Calcula costos efectivos para el conectado según modo.
        Útil para mostrar breakdown transparente.
        """
        
        # Fees de Stripe según método
        stripe_fee = STRIPE_MX_FEES.calculate_payment_fee(amount, payment_method)
        
        # Application fee
        app_fee = (amount * app_fee_pct / 100) + app_fee_fixed
        
        if charges_mode == ChargesMode.DIRECT:
            # Conectado paga stripe_fee, nosotros cobramos app_fee separado
            conectado_receives = amount - stripe_fee - app_fee
            plataforma_pays = 0
            plataforma_receives = app_fee
            
        elif charges_mode == ChargesMode.DESTINATION:
            # Nosotros pagamos stripe_fee, transferimos amount - app_fee
            conectado_receives = amount - app_fee
            plataforma_pays = stripe_fee
            plataforma_receives = app_fee - stripe_fee  # Puede ser negativo!
            
        elif charges_mode == ChargesMode.SEPARATE:
            # Nosotros cobramos todo, transferimos manualmente
            conectado_receives = amount - app_fee  # Depende del transfer manual
            plataforma_pays = stripe_fee
            plataforma_receives = app_fee - stripe_fee
        
        return {
            "amount": amount,
            "stripe_fee": stripe_fee,
            "app_fee": app_fee,
            "conectado_receives": conectado_receives,
            "plataforma_pays": plataforma_pays,
            "plataforma_receives": plataforma_receives,
            "charges_mode": charges_mode.value,
            "payment_method": payment_method.value
        }

# Instancia global
checkout_orchestrator = CheckoutOrchestrator()

if __name__ == "__main__":
    # Ejemplo de uso de los 3 modos
    print("🛒 Checkout Orchestrator - Test de 3 Modos")
    print("=" * 50)
    
    orchestrator = CheckoutOrchestrator()
    
    # Simular cuentas Connect para cada modo
    from .types import ConnectAccount, ChargesMode, FeePolicy
    
    # Cuenta DIRECT
    account_direct = ConnectAccount(
        account_id="acct_direct_test",
        tenant_id="ferreteria-mx",
        email="test@ferreteria.mx",
        charges_mode=ChargesMode.DIRECT,
        fee_policy=FeePolicy(application_fee_pct=0.6, application_fee_fixed=2.0),
        onboarding_complete=True
    )
    
    # Cuenta DESTINATION  
    account_dest = ConnectAccount(
        account_id="acct_dest_test",
        tenant_id="refacciones-auto",
        email="test@refacciones.mx",
        charges_mode=ChargesMode.DESTINATION,
        fee_policy=FeePolicy(application_fee_pct=0.8, application_fee_fixed=3.0),
        onboarding_complete=True
    )
    
    # Cuenta SEPARATE
    account_sep = ConnectAccount(
        account_id="acct_sep_test", 
        tenant_id="clinica-salud",
        email="test@clinica.mx",
        charges_mode=ChargesMode.SEPARATE,
        fee_policy=FeePolicy(application_fee_pct=1.0, application_fee_fixed=5.0),
        onboarding_complete=True
    )
    
    # Agregar a connect_manager (simulado)
    connect_manager.accounts[account_direct.account_id] = account_direct
    connect_manager.accounts[account_dest.account_id] = account_dest
    connect_manager.accounts[account_sep.account_id] = account_sep
    
    amount = 1000.0  # $1000 MXN
    
    try:
        print("\\n📊 Análisis de costos por modo:")
        
        for account in [account_direct, account_dest, account_sep]:
            costs = orchestrator.calculate_effective_costs(
                amount, PaymentMethod.CARD, account.charges_mode,
                account.fee_policy.application_fee_pct,
                account.fee_policy.application_fee_fixed
            )
            
            print(f"\\n{account.charges_mode.value.upper()}:")
            print(f"  Conectado recibe: ${costs['conectado_receives']:.2f}")
            print(f"  Plataforma paga: ${costs['plataforma_pays']:.2f}")
            print(f"  Plataforma recibe: ${costs['plataforma_receives']:.2f}")
        
        print("\\n✅ Análisis completado")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Configura las variables de entorno de Stripe")