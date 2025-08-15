"""
🔤 Types & Models para OCO
=========================

Modelos de datos, enums y tipos para Stripe Connect.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
import json

class ChargesMode(str, Enum):
    """Modos de cargo en Stripe Connect"""
    DIRECT = "direct"              # Conectado paga fees, app fee separado
    DESTINATION = "destination"    # Plataforma paga fees, transfiere neto  
    SEPARATE = "separate"         # Multi-split, plataforma maneja todo

class PricingMode(str, Enum):
    """Modos de pricing"""
    STRIPE_HANDLES = "stripe_handles_pricing"    # Revenue share con Stripe
    PLATFORM_HANDLES = "platform_handles_pricing"  # Nosotros fijamos markup

class PayoutSchedule(str, Enum):
    """Frecuencia de payouts"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"

class PaymentMethod(str, Enum):
    """Métodos de pago soportados en MX"""
    CARD = "card"
    OXXO = "oxxo"
    SPEI = "spei"  # Transferencia bancaria

class EventType(str, Enum):
    """Tipos de eventos de webhooks"""
    PAYMENT_SUCCEEDED = "payment_intent.succeeded"
    PAYMENT_FAILED = "payment_intent.payment_failed"
    CHARGE_REFUNDED = "charge.refunded"
    CHARGE_DISPUTE_CREATED = "charge.dispute.created"
    PAYOUT_PAID = "payout.paid"
    PAYOUT_FAILED = "payout.failed"
    ACCOUNT_UPDATED = "account.updated"

@dataclass
class FeePolicy:
    """Política de fees para application_fee_amount"""
    application_fee_pct: float = 0.6    # 0.6%
    application_fee_fixed: float = 2.0  # $2 MXN fijo
    min_fee: float = 5.0                # Fee mínimo
    max_fee: Optional[float] = None     # Fee máximo (opcional)
    
    def calculate(self, amount: float) -> int:
        """Calcula el fee en centavos"""
        fee = (amount * self.application_fee_pct / 100) + self.application_fee_fixed
        
        if fee < self.min_fee:
            fee = self.min_fee
        if self.max_fee and fee > self.max_fee:
            fee = self.max_fee
            
        return int(fee * 100)  # Convertir a centavos

@dataclass
class ConnectAccount:
    """Cuenta Stripe Connect"""
    account_id: str
    tenant_id: str
    email: str
    country: str = "MX"
    currency: str = "MXN"
    charges_mode: ChargesMode = ChargesMode.DIRECT
    pricing_mode: PricingMode = PricingMode.PLATFORM_HANDLES
    payout_schedule: PayoutSchedule = PayoutSchedule.WEEKLY
    fee_policy: FeePolicy = field(default_factory=FeePolicy)
    
    # Estado de onboarding
    onboarding_complete: bool = False
    capabilities_active: List[str] = field(default_factory=list)
    requirements_pending: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte a diccionario serializable"""
        return {
            "account_id": self.account_id,
            "tenant_id": self.tenant_id,
            "email": self.email,
            "country": self.country,
            "currency": self.currency,
            "charges_mode": self.charges_mode.value,
            "pricing_mode": self.pricing_mode.value,
            "payout_schedule": self.payout_schedule.value,
            "fee_policy": {
                "application_fee_pct": self.fee_policy.application_fee_pct,
                "application_fee_fixed": self.fee_policy.application_fee_fixed,
                "min_fee": self.fee_policy.min_fee,
                "max_fee": self.fee_policy.max_fee
            },
            "onboarding_complete": self.onboarding_complete,
            "capabilities_active": self.capabilities_active,
            "requirements_pending": self.requirements_pending,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat()
        }

@dataclass
class CheckoutSession:
    """Sesión de checkout de Stripe"""
    session_id: str
    tenant_id: str
    order_id: str
    payment_intent_id: Optional[str] = None
    
    # Detalles del pago
    amount: float                    # En MXN
    currency: str = "MXN"
    payment_methods: List[PaymentMethod] = field(default_factory=lambda: [PaymentMethod.CARD])
    
    # Connect settings
    connect_account_id: str
    charges_mode: ChargesMode
    application_fee_amount: int = 0  # En centavos
    
    # URLs
    success_url: str
    cancel_url: str
    checkout_url: Optional[str] = None
    
    # Estado
    status: str = "pending"  # pending, complete, expired
    expires_at: Optional[datetime] = None
    
    # Metadata
    metadata: Dict[str, str] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

@dataclass  
class Transfer:
    """Transfer para modo Separate"""
    transfer_id: str
    tenant_id: str
    connect_account_id: str
    amount: int              # En centavos
    currency: str = "MXN"
    source_transaction: Optional[str] = None  # Charge ID origen
    description: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)
    status: str = "pending"  # pending, paid, failed, canceled, reversed
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class WebhookEvent:
    """Evento de webhook procesado"""
    event_id: str
    event_type: EventType
    tenant_id: str
    stripe_account_id: Optional[str] = None
    
    # Datos del evento
    data: Dict[str, Any] = field(default_factory=dict)
    
    # Procesamiento
    processed: bool = False
    processed_at: Optional[datetime] = None
    idempotency_key: str = ""
    attempts: int = 0
    last_error: Optional[str] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.now)
    received_at: datetime = field(default_factory=datetime.now)

@dataclass
class PayoutSummary:
    """Resumen de payout para conciliación"""
    payout_id: str
    tenant_id: str
    connect_account_id: str
    
    # Período del payout
    period_start: datetime
    period_end: datetime
    
    # Montos (en centavos)
    gross_amount: int = 0        # Total de ventas
    stripe_fees: int = 0         # Fees de Stripe (3.6% + $3)
    application_fees: int = 0    # Nuestros fees
    refunds: int = 0            # Reembolsos
    disputes: int = 0           # Contracargos
    adjustments: int = 0        # Ajustes varios
    net_amount: int = 0         # Neto transferido
    
    # Estado
    status: str = "pending"      # pending, paid, failed
    arrival_date: Optional[datetime] = None
    
    # Transacciones incluidas
    transactions: List[str] = field(default_factory=list)  # Payment Intent IDs
    
    # Conciliación
    reconciled: bool = False
    reconciled_at: Optional[datetime] = None
    reconciliation_diff: int = 0  # Diferencia encontrada
    
    created_at: datetime = field(default_factory=datetime.now)
    
    def calculate_net(self):
        """Calcula el neto esperado"""
        self.net_amount = (
            self.gross_amount 
            - self.stripe_fees 
            - self.application_fees 
            - self.refunds 
            - self.disputes 
            + self.adjustments
        )

@dataclass
class StripeConnectFees:
    """Estructura de fees de Stripe Connect MX"""
    
    # Fees de pagos (por transacción)
    card_domestic_pct: float = 3.6      # 3.6% tarjetas nacionales
    card_domestic_fixed: float = 3.0    # $3 MXN fijo
    card_international_pct: float = 4.1  # +0.5% internacional
    currency_conversion_pct: float = 2.0 # +2% conversión moneda
    
    oxxo_pct: float = 3.6               # 3.6% OXXO
    oxxo_fixed: float = 3.0             # $3 MXN fijo
    oxxo_limit: float = 10000.0         # Límite $10,000 por vale
    
    spei_pct: float = 2.5               # 2.5% SPEI (estimado)
    spei_fixed: float = 5.0             # $5 MXN fijo
    
    # Fees de Connect (por cuenta activa)
    connect_active_monthly: float = 35.0    # $35 MXN/mes por cuenta activa
    connect_payout_pct: float = 0.25       # 0.25% del monto del payout
    connect_payout_fixed: float = 12.0     # $12 MXN por payout
    
    def calculate_payment_fee(self, amount: float, method: PaymentMethod, 
                            is_international: bool = False, 
                            has_conversion: bool = False) -> float:
        """Calcula el fee de pago según método y condiciones"""
        
        if method == PaymentMethod.CARD:
            pct = self.card_domestic_pct
            fixed = self.card_domestic_fixed
            
            if is_international:
                pct = self.card_international_pct
            if has_conversion:
                pct += self.currency_conversion_pct
                
        elif method == PaymentMethod.OXXO:
            if amount > self.oxxo_limit:
                raise ValueError(f"OXXO limit exceeded: ${amount:.2f} > ${self.oxxo_limit:.2f}")
            pct = self.oxxo_pct
            fixed = self.oxxo_fixed
            
        elif method == PaymentMethod.SPEI:
            pct = self.spei_pct
            fixed = self.spei_fixed
            
        else:
            raise ValueError(f"Unknown payment method: {method}")
        
        return (amount * pct / 100) + fixed
    
    def calculate_connect_monthly_cost(self, active_accounts: int, 
                                     monthly_payout_volume: float,
                                     monthly_payouts: int) -> Dict[str, float]:
        """Calcula costos mensuales de Connect"""
        
        active_cost = active_accounts * self.connect_active_monthly
        payout_pct_cost = monthly_payout_volume * self.connect_payout_pct / 100
        payout_fixed_cost = monthly_payouts * self.connect_payout_fixed
        
        total = active_cost + payout_pct_cost + payout_fixed_cost
        
        return {
            "active_accounts_fee": active_cost,
            "payout_percentage_fee": payout_pct_cost,
            "payout_fixed_fee": payout_fixed_cost,
            "total_monthly_cost": total
        }

# Configuración global de fees MX
STRIPE_MX_FEES = StripeConnectFees()

# Emails de prueba para OXXO (test mode)
OXXO_TEST_EMAILS = {
    "success_immediate": "success@stripe.com",
    "success_delayed": "success_delayed@stripe.com", 
    "expired": "expired@stripe.com",
    "declined": "declined@stripe.com"
}

# Eventos de webhook importantes
CRITICAL_WEBHOOK_EVENTS = [
    EventType.PAYMENT_SUCCEEDED,
    EventType.PAYMENT_FAILED,
    EventType.CHARGE_REFUNDED,
    EventType.CHARGE_DISPUTE_CREATED,
    EventType.PAYOUT_PAID,
    EventType.PAYOUT_FAILED
]