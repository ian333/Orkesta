"""
🚀 OCO - Orkesta Connect Orchestrator
====================================

Módulo completo de Stripe Connect para Orkesta.
Maneja los 3 modos: Direct, Destination, Separate.
Incluye fees, webhooks, payouts y conciliación.
"""

from .connect import StripeConnectManager
from .checkout import CheckoutOrchestrator  
from .transfers import TransferManager
from .fees import FeeCalculator
from .webhooks import WebhookProcessor
from .payouts import PayoutReconciler
from .testing import StripeTestSuite
from .types import *

__version__ = "1.0.0"
__all__ = [
    "StripeConnectManager",
    "CheckoutOrchestrator", 
    "TransferManager",
    "FeeCalculator",
    "WebhookProcessor",
    "PayoutReconciler",
    "StripeTestSuite"
]