"""
🔔 Webhook Processor - Procesamiento idempotente de eventos Stripe
================================================================

Maneja webhooks de Stripe Connect con verificación de firma,
idempotencia exacta-una-vez y dispatch a handlers específicos.
"""

import stripe
import hashlib
import hmac
import os
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
import logging

from .types import (
    WebhookEvent, EventType, CRITICAL_WEBHOOK_EVENTS,
    ConnectAccount, CheckoutSession
)

logger = logging.getLogger(__name__)

class WebhookProcessor:
    """Procesador de webhooks con idempotencia y verificación de firma"""
    
    def __init__(self):
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        if not self.webhook_secret:
            logger.warning("STRIPE_WEBHOOK_SECRET not set - signature verification disabled")
        
        # Storage de eventos procesados (en prod usar DB)
        self.processed_events: Dict[str, WebhookEvent] = {}
        
        # Handlers por tipo de evento
        self.event_handlers: Dict[EventType, List[Callable]] = {}
        
        # Registro de errores por evento
        self.error_log: List[Dict[str, Any]] = []
        
        # Configurar handlers por defecto
        self._setup_default_handlers()
    
    def _setup_default_handlers(self):
        """Configura handlers por defecto para eventos críticos"""
        
        self.register_handler(EventType.PAYMENT_SUCCEEDED, self._handle_payment_succeeded)
        self.register_handler(EventType.PAYMENT_FAILED, self._handle_payment_failed)
        self.register_handler(EventType.CHARGE_REFUNDED, self._handle_charge_refunded)
        self.register_handler(EventType.CHARGE_DISPUTE_CREATED, self._handle_dispute_created)
        self.register_handler(EventType.PAYOUT_PAID, self._handle_payout_paid)
        self.register_handler(EventType.PAYOUT_FAILED, self._handle_payout_failed)
        self.register_handler(EventType.ACCOUNT_UPDATED, self._handle_account_updated)
    
    def verify_webhook_signature(self, payload: str, signature: str) -> bool:
        """
        Verifica la firma del webhook de Stripe.
        Previene ataques de replay y falsificación.
        """
        
        if not self.webhook_secret:
            logger.warning("Webhook signature verification skipped - no secret configured")
            return True
        
        try:
            # Extraer timestamp y signature del header
            elements = signature.split(',')
            timestamp = None
            signatures = []
            
            for element in elements:
                if element.startswith('t='):
                    timestamp = element[2:]
                elif element.startswith('v1='):
                    signatures.append(element[3:])
            
            if not timestamp or not signatures:
                logger.error("Invalid signature format")
                return False
            
            # Verificar que el timestamp no sea muy antiguo (5 minutos)
            webhook_time = int(timestamp)
            current_time = int(time.time())
            
            if current_time - webhook_time > 300:  # 5 minutos
                logger.error(f"Webhook timestamp too old: {current_time - webhook_time}s")
                return False
            
            # Crear signature esperada
            signed_payload = f"{timestamp}.{payload}"
            expected_signature = hmac.new(
                self.webhook_secret.encode('utf-8'),
                signed_payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Verificar contra todas las signatures (por si hay múltiples)
            for sig in signatures:
                if hmac.compare_digest(expected_signature, sig):
                    return True
            
            logger.error("Webhook signature verification failed")
            return False
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    def process_webhook(self, payload: str, signature: str = None,
                       stripe_account: str = None) -> Dict[str, Any]:
        """
        Procesa un webhook de Stripe con idempotencia garantizada.
        
        Returns:
            {
                "event_id": "evt_...",
                "processed": True/False,
                "was_duplicate": True/False,
                "handlers_executed": 3,
                "errors": []
            }
        """
        
        try:
            # Verificar firma si está configurada
            if signature and not self.verify_webhook_signature(payload, signature):
                return {"error": "Invalid webhook signature", "processed": False}
            
            # Parsear evento
            event_data = json.loads(payload)
            event_id = event_data.get("id")
            event_type = event_data.get("type")
            
            if not event_id or not event_type:
                return {"error": "Invalid event format", "processed": False}
            
            # Verificar idempotencia
            if event_id in self.processed_events:
                existing_event = self.processed_events[event_id]
                logger.info(f"Duplicate webhook received: {event_id}")
                
                return {
                    "event_id": event_id,
                    "processed": existing_event.processed,
                    "was_duplicate": True,
                    "first_processed_at": existing_event.processed_at.isoformat() if existing_event.processed_at else None,
                    "handlers_executed": 0,
                    "errors": []
                }
            
            # Crear registro del evento
            webhook_event = WebhookEvent(
                event_id=event_id,
                event_type=EventType(event_type) if event_type in [e.value for e in EventType] else event_type,
                tenant_id=self._extract_tenant_id(event_data),
                stripe_account_id=stripe_account,
                data=event_data,
                idempotency_key=self._generate_idempotency_key(event_id, event_data),
                received_at=datetime.now()
            )
            
            # Guardar inmediatamente para idempotencia
            self.processed_events[event_id] = webhook_event
            
            # Procesar evento
            result = self._process_event(webhook_event)
            
            # Actualizar estado
            webhook_event.processed = result["success"]
            webhook_event.processed_at = datetime.now() if result["success"] else None
            webhook_event.attempts += 1
            
            if result["errors"]:
                webhook_event.last_error = str(result["errors"])
                self.error_log.append({
                    "event_id": event_id,
                    "errors": result["errors"],
                    "timestamp": datetime.now().isoformat()
                })
            
            return {
                "event_id": event_id,
                "processed": result["success"],
                "was_duplicate": False,
                "handlers_executed": result["handlers_executed"],
                "errors": result["errors"]
            }
            
        except Exception as e:
            logger.error(f"Error processing webhook: {e}")
            return {"error": str(e), "processed": False}
    
    def _extract_tenant_id(self, event_data: Dict[str, Any]) -> str:
        """Extrae tenant_id del metadata del evento"""
        
        # Buscar en varios lugares donde puede estar el tenant_id
        search_paths = [
            ["data", "object", "metadata", "tenant_id"],
            ["data", "object", "payment_intent", "metadata", "tenant_id"],
            ["data", "object", "transfer_data", "metadata", "tenant_id"],
            ["data", "object", "charges", "data", 0, "metadata", "tenant_id"],
            ["account"]  # Para eventos de account.updated
        ]
        
        for path in search_paths:
            current = event_data
            try:
                for key in path:
                    if isinstance(current, list):
                        current = current[key]
                    else:
                        current = current.get(key)
                    
                    if current is None:
                        break
                
                if current and isinstance(current, str):
                    return current
                    
            except (KeyError, IndexError, TypeError):
                continue
        
        return "unknown"
    
    def _generate_idempotency_key(self, event_id: str, event_data: Dict[str, Any]) -> str:
        """Genera clave de idempotencia única"""
        
        # Usar event_id + hash del contenido crítico
        critical_data = {
            "id": event_id,
            "type": event_data.get("type"),
            "created": event_data.get("created"),
            "data_id": event_data.get("data", {}).get("object", {}).get("id")
        }
        
        content_hash = hashlib.md5(
            json.dumps(critical_data, sort_keys=True).encode()
        ).hexdigest()
        
        return f"{event_id}-{content_hash[:8]}"
    
    def _process_event(self, webhook_event: WebhookEvent) -> Dict[str, Any]:
        """Procesa un evento ejecutando todos sus handlers"""
        
        event_type = webhook_event.event_type
        handlers = self.event_handlers.get(event_type, [])
        
        if not handlers:
            logger.warning(f"No handlers registered for event type: {event_type}")
            return {
                "success": True,  # No es error si no hay handlers
                "handlers_executed": 0,
                "errors": []
            }
        
        executed = 0
        errors = []
        
        for handler in handlers:
            try:
                handler(webhook_event)
                executed += 1
                logger.debug(f"Handler {handler.__name__} executed successfully for {webhook_event.event_id}")
                
            except Exception as e:
                error_msg = f"Handler {handler.__name__} failed: {e}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        success = len(errors) == 0
        
        return {
            "success": success,
            "handlers_executed": executed,
            "errors": errors
        }
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """Registra un handler para un tipo de evento"""
        
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        
        self.event_handlers[event_type].append(handler)
        logger.info(f"Registered handler {handler.__name__} for {event_type.value}")
    
    def unregister_handler(self, event_type: EventType, handler: Callable):
        """Desregistra un handler"""
        
        if event_type in self.event_handlers:
            try:
                self.event_handlers[event_type].remove(handler)
                logger.info(f"Unregistered handler {handler.__name__} for {event_type.value}")
            except ValueError:
                logger.warning(f"Handler {handler.__name__} not found for {event_type.value}")
    
    # ==================== HANDLERS POR DEFECTO ====================
    
    def _handle_payment_succeeded(self, event: WebhookEvent):
        """Handler para payment_intent.succeeded"""
        
        payment_intent = event.data.get("data", {}).get("object", {})
        amount = payment_intent.get("amount", 0) / 100  # Convertir de centavos
        currency = payment_intent.get("currency", "mxn").upper()
        
        metadata = payment_intent.get("metadata", {})
        order_id = metadata.get("order_id")
        tenant_id = metadata.get("tenant_id", event.tenant_id)
        
        logger.info(f"Payment succeeded: {amount} {currency} for order {order_id} (tenant: {tenant_id})")
        
        # Aquí se integraría con orkesta_shared_context para actualizar la orden
        # Por ahora solo loggeamos
        
        # TODO: Actualizar orden en contexto compartido
        # ctx = get_shared_context(tenant_id)
        # ctx.update_order_status(order_id, OrderStatus.CONFIRMED, payment_intent_id=payment_intent.get("id"))
    
    def _handle_payment_failed(self, event: WebhookEvent):
        """Handler para payment_intent.payment_failed"""
        
        payment_intent = event.data.get("data", {}).get("object", {})
        failure_reason = payment_intent.get("last_payment_error", {}).get("message", "Unknown")
        
        metadata = payment_intent.get("metadata", {})
        order_id = metadata.get("order_id")
        tenant_id = metadata.get("tenant_id", event.tenant_id)
        
        logger.warning(f"Payment failed for order {order_id}: {failure_reason}")
        
        # TODO: Notificar fallo y liberar stock reservado
    
    def _handle_charge_refunded(self, event: WebhookEvent):
        """Handler para charge.refunded"""
        
        charge = event.data.get("data", {}).get("object", {})
        refund_amount = 0
        
        refunds = charge.get("refunds", {}).get("data", [])
        if refunds:
            refund_amount = sum(r.get("amount", 0) for r in refunds) / 100
        
        logger.info(f"Charge refunded: ${refund_amount:.2f}")
        
        # TODO: Crear entrada en ledger y notificar
    
    def _handle_dispute_created(self, event: WebhookEvent):
        """Handler para charge.dispute.created"""
        
        dispute = event.data.get("data", {}).get("object", {})
        amount = dispute.get("amount", 0) / 100
        reason = dispute.get("reason", "unknown")
        
        logger.warning(f"Dispute created: ${amount:.2f} - Reason: {reason}")
        
        # TODO: Crear alerta crítica y proceso de respuesta
    
    def _handle_payout_paid(self, event: WebhookEvent):
        """Handler para payout.paid"""
        
        payout = event.data.get("data", {}).get("object", {})
        amount = payout.get("amount", 0) / 100
        currency = payout.get("currency", "mxn").upper()
        arrival_date = payout.get("arrival_date")
        
        logger.info(f"Payout paid: {amount} {currency} - Arrival: {arrival_date}")
        
        # TODO: Actualizar conciliación de payouts
    
    def _handle_payout_failed(self, event: WebhookEvent):
        """Handler para payout.failed"""
        
        payout = event.data.get("data", {}).get("object", {})
        failure_message = payout.get("failure_message", "Unknown error")
        
        logger.error(f"Payout failed: {failure_message}")
        
        # TODO: Crear alerta crítica
    
    def _handle_account_updated(self, event: WebhookEvent):
        """Handler para account.updated"""
        
        account = event.data.get("data", {}).get("object", {})
        account_id = account.get("id")
        details_submitted = account.get("details_submitted", False)
        charges_enabled = account.get("charges_enabled", False)
        
        logger.info(f"Account updated: {account_id} - Details: {details_submitted}, Charges: {charges_enabled}")
        
        # TODO: Actualizar estado en connect_manager
    
    # ==================== UTILIDADES ====================
    
    def get_event_status(self, event_id: str) -> Optional[Dict[str, Any]]:
        """Obtiene estado de procesamiento de un evento"""
        
        if event_id not in self.processed_events:
            return None
        
        event = self.processed_events[event_id]
        
        return {
            "event_id": event.event_id,
            "event_type": event.event_type.value if isinstance(event.event_type, EventType) else event.event_type,
            "tenant_id": event.tenant_id,
            "processed": event.processed,
            "processed_at": event.processed_at.isoformat() if event.processed_at else None,
            "attempts": event.attempts,
            "last_error": event.last_error,
            "received_at": event.received_at.isoformat(),
            "idempotency_key": event.idempotency_key
        }
    
    def list_recent_events(self, limit: int = 50, 
                          event_type: EventType = None,
                          tenant_id: str = None) -> List[Dict[str, Any]]:
        """Lista eventos recientes con filtros opcionales"""
        
        events = list(self.processed_events.values())
        
        # Filtrar por tipo
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        
        # Filtrar por tenant
        if tenant_id:
            events = [e for e in events if e.tenant_id == tenant_id]
        
        # Ordenar por fecha recibida (más reciente primero)
        events.sort(key=lambda x: x.received_at, reverse=True)
        
        # Limitar resultados
        events = events[:limit]
        
        return [self.get_event_status(e.event_id) for e in events]
    
    def get_error_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Obtiene resumen de errores en las últimas N horas"""
        
        since = datetime.now() - timedelta(hours=hours)
        recent_errors = [
            error for error in self.error_log
            if datetime.fromisoformat(error["timestamp"]) > since
        ]
        
        # Contar por tipo de error
        error_counts = {}
        for error in recent_errors:
            for err_msg in error["errors"]:
                error_type = err_msg.split(":")[0] if ":" in err_msg else "unknown"
                error_counts[error_type] = error_counts.get(error_type, 0) + 1
        
        return {
            "period_hours": hours,
            "total_errors": len(recent_errors),
            "error_types": error_counts,
            "latest_errors": recent_errors[-10:] if recent_errors else []
        }
    
    def test_idempotency(self, event_id: str, payload: str, times: int = 3) -> List[Dict[str, Any]]:
        """Prueba idempotencia enviando el mismo evento múltiples veces"""
        
        results = []
        
        for i in range(times):
            result = self.process_webhook(payload)
            results.append({
                "attempt": i + 1,
                "result": result,
                "was_duplicate": result.get("was_duplicate", False)
            })
        
        return results
    
    def simulate_webhook_event(self, event_type: EventType, 
                             tenant_id: str,
                             custom_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simula un evento de webhook para testing"""
        
        event_id = f"evt_test_{int(time.time())}_{event_type.value.replace('.', '_')}"
        
        base_event = {
            "id": event_id,
            "object": "event",
            "api_version": "2020-08-27",
            "created": int(time.time()),
            "type": event_type.value,
            "livemode": False,
            "pending_webhooks": 1,
            "request": {"id": None, "idempotency_key": None},
            "data": {
                "object": {
                    "id": f"test_obj_{int(time.time())}",
                    "metadata": {
                        "tenant_id": tenant_id,
                        "simulated": "true"
                    },
                    **(custom_data or {})
                }
            }
        }
        
        payload = json.dumps(base_event)
        return self.process_webhook(payload)

# Instancia global
webhook_processor = WebhookProcessor()

if __name__ == "__main__":
    # Ejemplo de uso y testing
    print("🔔 Webhook Processor - Test de Idempotencia")
    print("=" * 50)
    
    processor = WebhookProcessor()
    
    # Simular evento de pago exitoso
    result1 = processor.simulate_webhook_event(
        EventType.PAYMENT_SUCCEEDED,
        "test-tenant",
        {
            "amount": 100000,  # $1000 en centavos
            "currency": "mxn",
            "status": "succeeded",
            "metadata": {
                "order_id": "ORD-TEST-001",
                "tenant_id": "test-tenant"
            }
        }
    )
    
    print(f"\\n✅ Evento simulado:")
    print(f"   Event ID: {result1['event_id']}")
    print(f"   Procesado: {result1['processed']}")
    print(f"   Handlers ejecutados: {result1['handlers_executed']}")
    
    # Probar idempotencia
    print(f"\\n🔄 Probando idempotencia...")
    
    # Crear payload de prueba
    test_payload = json.dumps({
        "id": "evt_test_idempotency",
        "type": "payment_intent.succeeded",
        "data": {
            "object": {
                "id": "pi_test",
                "amount": 50000,
                "metadata": {"tenant_id": "test-tenant"}
            }
        }
    })
    
    # Enviar 3 veces
    idempotency_results = processor.test_idempotency("evt_test_idempotency", test_payload, 3)
    
    for i, result in enumerate(idempotency_results, 1):
        print(f"   Intento {i}: {'Duplicado' if result['was_duplicate'] else 'Procesado'}")
    
    # Resumen de errores
    error_summary = processor.get_error_summary(1)
    print(f"\\n📊 Errores última hora: {error_summary['total_errors']}")
    
    # Eventos recientes
    recent = processor.list_recent_events(5)
    print(f"\\n📋 Eventos recientes: {len(recent)}")
    
    print("\\n✅ Test de webhooks completado")