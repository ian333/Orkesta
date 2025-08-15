"""
🧠 ORKESTA SHARED CONTEXT - Cerebro Colectivo de Agentes
=======================================================

Contexto único que comparten TODOS los agentes de Orkesta.
Cada tenant tiene su propio contexto aislado pero consistente.

Regla de oro: NINGÚN agente hace nada fuera de este contexto.
Todo pasa por aquí: catálogo, clientes, órdenes, pagos, políticas.
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from enum import Enum
import hashlib
import threading
from pathlib import Path

class ChargesMode(str, Enum):
    DIRECT = "direct"              # Conectado paga fees, app fee separado
    DESTINATION = "destination"    # Plataforma paga fees, transfiere neto
    SEPARATE = "separate"         # Multi-split, plataforma maneja todo

class PricingMode(str, Enum):
    STRIPE_HANDLES = "stripe_handles_pricing"  # Revenue share con Stripe
    PLATFORM_HANDLES = "platform_handles_pricing"  # Nosotros fijamos markup

class PayoutSchedule(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly" 
    MONTHLY = "monthly"

class MessageChannel(str, Enum):
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    SMS = "sms"
    EMAIL = "email"

class OrderStatus(str, Enum):
    DRAFT = "draft"              # En construcción por agente
    QUOTED = "quoted"            # Cotización enviada, esperando respuesta
    RESERVED = "reserved"        # Stock reservado, esperando pago
    CONFIRMED = "confirmed"      # Pago exitoso, listo para fulfillment
    FULFILLED = "fulfilled"      # Entregado al cliente
    CANCELLED = "cancelled"      # Cancelado por timeout o solicitud
    REFUNDED = "refunded"        # Reembolsado parcial/total

@dataclass
class ConnectConfig:
    """Configuración Stripe Connect por tenant"""
    account_id: str                           # acct_1234567890
    pricing_mode: PricingMode                 # stripe_handles | platform_handles
    charges_mode: ChargesMode                 # direct | destination | separate
    payout_schedule: PayoutSchedule           # daily | weekly | monthly
    fee_policy: Dict[str, Union[float, int]]  # {"application_fee_pct": 0.6, "application_fee_fixed": 2}
    onboarding_complete: bool = False
    capabilities_active: List[str] = None
    
    def __post_init__(self):
        if self.capabilities_active is None:
            self.capabilities_active = []

@dataclass
class ProductPricing:
    """Estructura de precios por producto"""
    lists: Dict[str, Dict[str, Union[float, int]]]  # {"lista_base": {"MXN": 85.00, "iva_pct": 16}}
    overrides: List[Dict[str, Any]]                  # [{"client_id": "c_777", "MXN": 77.00}]
    currency: str = "MXN"
    
@dataclass
class Product:
    """Producto en catálogo con metadatos completos"""
    product_id: str                    # p_123
    sku: str                          # TUBO-PVC-19MM-SCH40
    aliases: List[str]                # ["tubo pvc 3/4", "pvc 19 mm sch40"]
    name: str                         # Tubo PVC 19mm SCH40
    brand: str                        # AquaFlow
    unit: str                         # pieza, metro, caja, etc
    attributes: Dict[str, str]        # {"largo": "6m", "cedula": "40"}
    pricing: ProductPricing
    stock: Dict[str, int]             # {"default": 240, "reorder_point": 50}
    active: bool = True
    created_at: datetime = None
    updated_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

@dataclass 
class Client:
    """Cliente del tenant con datos de contacto y preferencias"""
    client_id: str                    # c_777
    name: str                         # Taller Pepe
    phones: List[str]                 # ["+52..."]
    emails: List[str] = None
    tags: List[str] = None            # ["vip", "moroso"]
    optins: Dict[str, bool] = None    # {"wa": true, "sms": true, "email": true}
    preferences: Dict[str, Any] = None # {"payment_method": "oxxo", "delivery": "pickup"}
    created_at: datetime = None
    
    def __post_init__(self):
        if self.emails is None:
            self.emails = []
        if self.tags is None:
            self.tags = []
        if self.optins is None:
            self.optins = {"wa": True, "sms": True, "email": True}
        if self.preferences is None:
            self.preferences = {}
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class OrderItem:
    """Item individual en una orden"""
    product_id: str
    sku: str
    name: str                         # Para display
    quantity: int
    unit_price: float                 # Precio final aplicado (con descuentos)
    unit_price_list: float           # Precio de lista original
    total_price: float               # quantity * unit_price
    discount_applied: float = 0      # Descuento en MXN aplicado
    
@dataclass
class Order:
    """Orden completa con items, cliente y estado"""
    order_id: str                    # ORD-2025-001234
    tenant_id: str                   # lb-productions
    client_id: str                   # c_777
    status: OrderStatus              # draft, quoted, reserved, etc
    items: List[OrderItem]
    subtotal: float                  # Suma de items sin IVA
    tax_amount: float                # IVA
    total_amount: float              # subtotal + tax_amount
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None  # Para reservas con TTL
    payment_intent_id: Optional[str] = None  # Stripe Payment Intent
    checkout_url: Optional[str] = None       # Link de pago
    notes: str = ""                  # Comentarios del cliente/vendedor
    agent_context: Dict[str, Any] = None  # Estado del agente que maneja la orden
    
    def __post_init__(self):
        if self.agent_context is None:
            self.agent_context = {}

@dataclass
class Invoice:
    """Factura generada desde una orden confirmada"""
    invoice_id: str                  # INV-2025-001234
    order_id: str                    # Referencia a la orden
    tenant_id: str
    client_id: str
    amount: float
    due_date: datetime
    status: str                      # pending, paid, overdue, cancelled
    dunning_stage: str               # T-3, T-1, DUE, T+1, etc
    payment_link: Optional[str] = None
    created_at: datetime = None
    paid_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class LedgerEntry:
    """Entrada contable en el ledger"""
    entry_id: str
    tenant_id: str
    timestamp: datetime
    event_type: str                  # payment, fee, payout, refund, dispute
    amount: float
    currency: str = "MXN"
    stripe_payment_intent_id: Optional[str] = None
    stripe_charge_id: Optional[str] = None
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}

@dataclass
class AgentSuggestion:
    """Sugerencia de un agente que requiere confirmación"""
    suggestion_id: str
    agent_name: str                  # CatalogMapper, PriceResolver, etc
    suggestion_type: str             # merge_skus, price_override, alias_add
    description: str                 # Descripción human-readable
    confidence: float                # 0.0 - 1.0
    data: Dict[str, Any]            # Datos específicos de la sugerencia
    requires_approval: bool
    approved: Optional[bool] = None
    approved_by: Optional[str] = None
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()

@dataclass
class MessagingPolicies:
    """Políticas de mensajería por tenant"""
    dnd_hours: Dict[str, int] = None      # {"start": 23, "end": 7}
    one_per_24h_per_debt_per_channel: bool = True
    max_attempts_per_stage: int = 3
    fallback_sequence: List[MessageChannel] = None
    
    def __post_init__(self):
        if self.dnd_hours is None:
            self.dnd_hours = {"start": 23, "end": 7}
        if self.fallback_sequence is None:
            self.fallback_sequence = [MessageChannel.WHATSAPP, MessageChannel.SMS, MessageChannel.EMAIL]

@dataclass
class TenantPolicies:
    """Políticas operativas del tenant"""
    messaging: MessagingPolicies
    reserve_ttl_minutes: int = 20      # TTL para reservas de stock
    auto_approve_threshold: float = 0.85  # Umbral para auto-aprobar sugerencias
    max_order_amount: float = 50000    # Límite de orden sin aprobación manual
    
    def __post_init__(self):
        if isinstance(self.messaging, dict):
            self.messaging = MessagingPolicies(**self.messaging)

class OrkestaSharedContext:
    """
    Contexto compartido por tenant - El cerebro colectivo de todos los agentes.
    Thread-safe con locks para operaciones críticas.
    """
    
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        self.version = datetime.now().isoformat()
        self._lock = threading.RLock()
        
        # Perfil organizacional
        self.org_profile = {
            "display_name": f"Tenant {tenant_id}",
            "industry": "retail/b2b",
            "created_at": datetime.now().isoformat()
        }
        
        # Configuración Stripe Connect
        self.connect: Optional[ConnectConfig] = None
        
        # Catálogo de productos
        self.catalog = {
            "version": datetime.now().isoformat(),
            "products": {},  # product_id -> Product
            "aliases_index": {},  # alias -> product_id (para búsqueda rápida)
            "mapping_templates": {}  # Para imports
        }
        
        # Clientes
        self.clients = {}  # client_id -> Client
        
        # Órdenes activas
        self.orders = {}  # order_id -> Order
        
        # Facturas
        self.invoices = {}  # invoice_id -> Invoice
        
        # Ledger contable
        self.ledger = {
            "journal_cursor": 0,
            "entries": {}  # entry_id -> LedgerEntry
        }
        
        # Sugerencias de agentes pendientes
        self.agent_suggestions = {}  # suggestion_id -> AgentSuggestion
        
        # Políticas operativas
        self.policies = TenantPolicies(
            messaging=MessagingPolicies()
        )
        
        # Cache para búsquedas frecuentes
        self._search_cache = {}
        self._cache_ttl = 300  # 5 minutos
        
    def update_version(self):
        """Actualiza la versión del contexto"""
        with self._lock:
            self.version = datetime.now().isoformat()
            self._search_cache.clear()
    
    # ==================== STRIPE CONNECT ====================
    
    def set_connect_config(self, account_id: str, pricing_mode: PricingMode, 
                          charges_mode: ChargesMode, fee_policy: Dict[str, Any]):
        """Configura Stripe Connect para el tenant"""
        with self._lock:
            self.connect = ConnectConfig(
                account_id=account_id,
                pricing_mode=pricing_mode,
                charges_mode=charges_mode,
                payout_schedule=PayoutSchedule.WEEKLY,
                fee_policy=fee_policy
            )
            self.update_version()
    
    def get_application_fee(self, amount: float) -> int:
        """Calcula el application fee en centavos según la política"""
        if not self.connect or not self.connect.fee_policy:
            return 0
        
        fee_pct = self.connect.fee_policy.get("application_fee_pct", 0)
        fee_fixed = self.connect.fee_policy.get("application_fee_fixed", 0)
        
        fee_amount = (amount * fee_pct / 100) + fee_fixed
        return int(fee_amount * 100)  # Convertir a centavos
    
    # ==================== CATÁLOGO ====================
    
    def add_product(self, product: Product) -> bool:
        """Agrega un producto al catálogo"""
        with self._lock:
            self.catalog["products"][product.product_id] = product
            
            # Indexar aliases para búsqueda rápida
            for alias in product.aliases:
                alias_normalized = alias.lower().strip()
                self.catalog["aliases_index"][alias_normalized] = product.product_id
            
            # Indexar SKU también
            self.catalog["aliases_index"][product.sku.lower()] = product.product_id
            
            self.update_version()
            return True
    
    def find_products(self, query: str, limit: int = 10) -> List[Product]:
        """Búsqueda fuzzy de productos por nombre, SKU o alias"""
        cache_key = f"search:{query.lower()}:{limit}"
        
        # Verificar cache
        if cache_key in self._search_cache:
            cached_result, cached_time = self._search_cache[cache_key]
            if time.time() - cached_time < self._cache_ttl:
                return cached_result
        
        query_normalized = query.lower().strip()
        results = []
        
        # Búsqueda exacta en aliases
        if query_normalized in self.catalog["aliases_index"]:
            product_id = self.catalog["aliases_index"][query_normalized]
            if product_id in self.catalog["products"]:
                results.append(self.catalog["products"][product_id])
        
        # Búsqueda fuzzy en nombres y aliases
        if len(results) < limit:
            for product in self.catalog["products"].values():
                if product in results:
                    continue
                
                # Buscar en nombre
                if query_normalized in product.name.lower():
                    results.append(product)
                    continue
                
                # Buscar en aliases
                for alias in product.aliases:
                    if query_normalized in alias.lower():
                        results.append(product)
                        break
        
        results = results[:limit]
        
        # Cache del resultado
        self._search_cache[cache_key] = (results, time.time())
        
        return results
    
    def get_product_price(self, product_id: str, client_id: str = None) -> Optional[float]:
        """Obtiene el precio de un producto para un cliente específico"""
        if product_id not in self.catalog["products"]:
            return None
        
        product = self.catalog["products"][product_id]
        
        # Verificar overrides por cliente
        if client_id:
            for override in product.pricing.overrides:
                if override.get("client_id") == client_id:
                    return override.get("MXN", 0)
        
        # Precio de lista base
        if "lista_base" in product.pricing.lists:
            return product.pricing.lists["lista_base"].get("MXN", 0)
        
        return None
    
    # ==================== CLIENTES ====================
    
    def add_client(self, client: Client) -> bool:
        """Agrega un cliente"""
        with self._lock:
            self.clients[client.client_id] = client
            self.update_version()
            return True
    
    def find_client_by_phone(self, phone: str) -> Optional[Client]:
        """Busca un cliente por número de teléfono"""
        for client in self.clients.values():
            if phone in client.phones:
                return client
        return None
    
    # ==================== ÓRDENES ====================
    
    def create_order(self, client_id: str, agent_name: str = None) -> str:
        """Crea una nueva orden en estado DRAFT"""
        with self._lock:
            order_id = f"ORD-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(self.orders):04d}"
            
            order = Order(
                order_id=order_id,
                tenant_id=self.tenant_id,
                client_id=client_id,
                status=OrderStatus.DRAFT,
                items=[],
                subtotal=0.0,
                tax_amount=0.0,
                total_amount=0.0,
                created_at=datetime.now(),
                updated_at=datetime.now(),
                agent_context={"created_by": agent_name or "unknown"}
            )
            
            self.orders[order_id] = order
            self.update_version()
            return order_id
    
    def add_item_to_order(self, order_id: str, product_id: str, quantity: int, 
                         client_id: str = None) -> bool:
        """Agrega un item a una orden"""
        if order_id not in self.orders:
            return False
        
        product = self.catalog["products"].get(product_id)
        if not product:
            return False
        
        with self._lock:
            order = self.orders[order_id]
            
            # Calcular precio
            unit_price_list = self.get_product_price(product_id)
            unit_price = self.get_product_price(product_id, client_id) or unit_price_list
            
            if unit_price is None:
                return False
            
            # Crear item
            item = OrderItem(
                product_id=product_id,
                sku=product.sku,
                name=product.name,
                quantity=quantity,
                unit_price=unit_price,
                unit_price_list=unit_price_list or unit_price,
                total_price=unit_price * quantity,
                discount_applied=(unit_price_list - unit_price) * quantity if unit_price_list else 0
            )
            
            order.items.append(item)
            
            # Recalcular totales
            self._recalculate_order_totals(order)
            
            self.update_version()
            return True
    
    def _recalculate_order_totals(self, order: Order):
        """Recalcula totales de una orden"""
        order.subtotal = sum(item.total_price for item in order.items)
        order.tax_amount = order.subtotal * 0.16  # IVA 16%
        order.total_amount = order.subtotal + order.tax_amount
        order.updated_at = datetime.now()
    
    def update_order_status(self, order_id: str, status: OrderStatus, 
                           payment_intent_id: str = None, checkout_url: str = None) -> bool:
        """Actualiza el estado de una orden"""
        if order_id not in self.orders:
            return False
        
        with self._lock:
            order = self.orders[order_id]
            order.status = status
            order.updated_at = datetime.now()
            
            if payment_intent_id:
                order.payment_intent_id = payment_intent_id
            if checkout_url:
                order.checkout_url = checkout_url
            
            # Si se reserva, establecer TTL
            if status == OrderStatus.RESERVED:
                order.expires_at = datetime.now() + timedelta(minutes=self.policies.reserve_ttl_minutes)
            
            self.update_version()
            return True
    
    def get_active_orders(self, client_id: str = None) -> List[Order]:
        """Obtiene órdenes activas (no finalizadas)"""
        active_statuses = [OrderStatus.DRAFT, OrderStatus.QUOTED, OrderStatus.RESERVED]
        
        orders = []
        for order in self.orders.values():
            if order.status in active_statuses:
                if client_id is None or order.client_id == client_id:
                    orders.append(order)
        
        return sorted(orders, key=lambda x: x.updated_at, reverse=True)
    
    # ==================== SUGERENCIAS DE AGENTES ====================
    
    def add_agent_suggestion(self, agent_name: str, suggestion_type: str, 
                           description: str, confidence: float, data: Dict[str, Any]) -> str:
        """Agrega una sugerencia de agente"""
        with self._lock:
            suggestion_id = f"SUGG-{int(time.time())}-{len(self.agent_suggestions):04d}"
            
            suggestion = AgentSuggestion(
                suggestion_id=suggestion_id,
                agent_name=agent_name,
                suggestion_type=suggestion_type,
                description=description,
                confidence=confidence,
                data=data,
                requires_approval=confidence < self.policies.auto_approve_threshold
            )
            
            self.agent_suggestions[suggestion_id] = suggestion
            
            # Auto-aprobar si confidence es alta
            if not suggestion.requires_approval:
                suggestion.approved = True
                suggestion.approved_by = "auto_system"
            
            self.update_version()
            return suggestion_id
    
    def get_pending_suggestions(self) -> List[AgentSuggestion]:
        """Obtiene sugerencias pendientes de aprobación"""
        return [s for s in self.agent_suggestions.values() 
                if s.requires_approval and s.approved is None]
    
    # ==================== LEDGER ====================
    
    def add_ledger_entry(self, event_type: str, amount: float, metadata: Dict[str, Any] = None) -> str:
        """Agrega entrada al ledger"""
        with self._lock:
            self.ledger["journal_cursor"] += 1
            entry_id = f"LED-{self.tenant_id}-{self.ledger['journal_cursor']:06d}"
            
            entry = LedgerEntry(
                entry_id=entry_id,
                tenant_id=self.tenant_id,
                timestamp=datetime.now(),
                event_type=event_type,
                amount=amount,
                metadata=metadata or {}
            )
            
            self.ledger["entries"][entry_id] = entry
            self.update_version()
            return entry_id
    
    # ==================== SERIALIZACIÓN ====================
    
    def to_dict(self) -> Dict[str, Any]:
        """Convierte el contexto a diccionario serializable"""
        def convert_dataclass(obj):
            if hasattr(obj, '__dict__'):
                return asdict(obj)
            return obj
        
        return {
            "tenant_id": self.tenant_id,
            "version": self.version,
            "org_profile": self.org_profile,
            "connect": convert_dataclass(self.connect) if self.connect else None,
            "catalog": {
                "version": self.catalog["version"],
                "products": {k: convert_dataclass(v) for k, v in self.catalog["products"].items()},
                "aliases_index": self.catalog["aliases_index"],
                "mapping_templates": self.catalog["mapping_templates"]
            },
            "clients": {k: convert_dataclass(v) for k, v in self.clients.items()},
            "orders": {k: convert_dataclass(v) for k, v in self.orders.items()},
            "invoices": {k: convert_dataclass(v) for k, v in self.invoices.items()},
            "ledger": {
                "journal_cursor": self.ledger["journal_cursor"],
                "entries": {k: convert_dataclass(v) for k, v in self.ledger["entries"].items()}
            },
            "agent_suggestions": {k: convert_dataclass(v) for k, v in self.agent_suggestions.items()},
            "policies": convert_dataclass(self.policies)
        }
    
    def save_to_file(self, filepath: str = None):
        """Guarda el contexto a archivo JSON"""
        if filepath is None:
            filepath = f"orkesta_context_{self.tenant_id}.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, default=str, ensure_ascii=False)

# ==================== CONTEXT MANAGER GLOBAL ====================

class OrkestaContextManager:
    """Manager global de contextos por tenant"""
    
    def __init__(self):
        self._contexts: Dict[str, OrkestaSharedContext] = {}
        self._lock = threading.RLock()
    
    def get_context(self, tenant_id: str) -> OrkestaSharedContext:
        """Obtiene o crea contexto para un tenant"""
        if tenant_id not in self._contexts:
            with self._lock:
                if tenant_id not in self._contexts:
                    self._contexts[tenant_id] = OrkestaSharedContext(tenant_id)
        
        return self._contexts[tenant_id]
    
    def list_tenants(self) -> List[str]:
        """Lista todos los tenants con contexto activo"""
        return list(self._contexts.keys())

# Instancia global del manager
context_manager = OrkestaContextManager()

def get_shared_context(tenant_id: str) -> OrkestaSharedContext:
    """Función helper para obtener contexto compartido"""
    return context_manager.get_context(tenant_id)

if __name__ == "__main__":
    # Ejemplo de uso
    print("🧠 Orkesta Shared Context - Cerebro Colectivo")
    print("=" * 50)
    
    # Crear contexto para tenant de prueba
    ctx = get_shared_context("test-tenant")
    
    # Configurar Stripe Connect
    ctx.set_connect_config(
        account_id="acct_test123",
        pricing_mode=PricingMode.PLATFORM_HANDLES,
        charges_mode=ChargesMode.DIRECT,
        fee_policy={"application_fee_pct": 0.6, "application_fee_fixed": 2}
    )
    
    # Agregar producto de ejemplo
    product = Product(
        product_id="p_tubo_pvc_001",
        sku="TUBO-PVC-19MM-SCH40",
        aliases=["tubo pvc 3/4", "pvc 19mm", "tubo 3/4 pulgada"],
        name="Tubo PVC 19mm SCH40",
        brand="AquaFlow",
        unit="pieza",
        attributes={"largo": "6m", "cedula": "40", "color": "blanco"},
        pricing=ProductPricing(
            lists={"lista_base": {"MXN": 85.00, "iva_pct": 16}},
            overrides=[]
        ),
        stock={"default": 240, "reorder_point": 50}
    )
    
    ctx.add_product(product)
    
    # Agregar cliente
    client = Client(
        client_id="c_taller_pepe",
        name="Taller Pepe",
        phones=["+5255123456789"],
        emails=["pepe@taller.mx"],
        tags=["vip", "construccion"]
    )
    
    ctx.add_client(client)
    
    # Crear orden
    order_id = ctx.create_order(client.client_id, "SalesAgent")
    ctx.add_item_to_order(order_id, product.product_id, 5, client.client_id)
    
    print(f"✅ Contexto creado para {ctx.tenant_id}")
    print(f"📦 Productos: {len(ctx.catalog['products'])}")
    print(f"👥 Clientes: {len(ctx.clients)}")
    print(f"🛒 Órdenes: {len(ctx.orders)}")
    print(f"💰 Application fee para $1000: ${ctx.get_application_fee(1000)/100:.2f}")
    
    # Buscar productos
    results = ctx.find_products("tubo pvc")
    print(f"🔍 Búsqueda 'tubo pvc': {len(results)} resultados")
    
    # Guardar contexto
    ctx.save_to_file()
    print(f"💾 Contexto guardado en orkesta_context_{ctx.tenant_id}.json")