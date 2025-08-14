"""
Agente de Ventas para WhatsApp - Vende productos del catálogo
"""
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum
from datetime import datetime, timedelta
import logging
import json
import re

logger = logging.getLogger(__name__)

class ConversationState(Enum):
    """Estados de la conversación de venta"""
    GREETING = "greeting"
    BROWSING = "browsing"
    PRODUCT_SELECTED = "product_selected"
    QUANTITY_CONFIRM = "quantity_confirm"
    PAYMENT_METHOD = "payment_method"
    COLLECTING_INFO = "collecting_info"
    PAYMENT_SENT = "payment_sent"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

class CustomerIntent(Enum):
    """Intenciones detectadas del cliente"""
    GREETING = "greeting"
    PRODUCT_QUERY = "product_query"
    PRICE_QUERY = "price_query"
    CONFIRM_PURCHASE = "confirm_purchase"
    PAYMENT_METHOD = "payment_method"
    CANCEL = "cancel"
    HELP = "help"
    COMPLAINT = "complaint"
    UNKNOWN = "unknown"

class SalesAgent:
    """
    Agente inteligente de ventas por WhatsApp
    Maneja todo el flujo de venta desde saludo hasta cobro
    """
    
    def __init__(self, catalog_agent=None):
        self.catalog_agent = catalog_agent
        self.conversations = {}  # phone -> conversation_state
        
        # Patrones para detectar intención
        self.intent_patterns = {
            CustomerIntent.GREETING: [
                r'\b(hola|buenos días|buenas tardes|buenas noches|que tal|saludos)\b',
                r'^(hey|hi|hello)',
                r'\b(buen día)\b'
            ],
            CustomerIntent.PRODUCT_QUERY: [
                r'\b(necesito|quiero|busco|tienen|venden|hay)\b.*\b(producto|material|pieza)',
                r'\b(cuanto cuesta|precio de|cotizar)\b',
                r'\b(cemento|tubo|tornillo|pintura|cable|foco)\b',  # Productos específicos
                r'\b\d+\s*(piezas?|kilos?|metros?|litros?)\b'
            ],
            CustomerIntent.PRICE_QUERY: [
                r'\b(precio|costo|cuánto|cuanto)\b',
                r'\b(vale|cuesta|sale)\b',
                r'[$¢]\s*\d+'
            ],
            CustomerIntent.CONFIRM_PURCHASE: [
                r'\b(sí|si|ok|dale|va|perfecto|adelante|confirmo)\b',
                r'^[1-3]$',  # Selección de opción
                r'\b(quiero ese|lo llevo|me lo llevo)\b'
            ],
            CustomerIntent.PAYMENT_METHOD: [
                r'\b(tarjeta|oxxo|transferencia|spei|efectivo)\b',
                r'\b(pagar|pago)\b'
            ],
            CustomerIntent.CANCEL: [
                r'\b(no|cancelar|mejor no|después|luego)\b',
                r'\b(no gracias|no quiero)\b'
            ],
            CustomerIntent.HELP: [
                r'\b(ayuda|help|información|info)\b',
                r'\b(cómo|como|qué|que)\s+(funciona|hago|pago)',
                r'[?¿]'
            ]
        }
        
        # Respuestas predefinidas
        self.responses = {
            'greeting': [
                "¡Hola! 👋 Bienvenido a {business_name}",
                "¿En qué puedo ayudarte hoy?",
                "Puedes preguntarme por cualquier producto de nuestro catálogo"
            ],
            'help': [
                "📚 *Cómo comprar:*",
                "1️⃣ Dime qué producto necesitas",
                "2️⃣ Te muestro opciones con precios",
                "3️⃣ Eliges y te envío link de pago",
                "4️⃣ Pagas con tarjeta, OXXO o transferencia",
                "",
                "Ejemplo: 'necesito 10 tubos pvc de 3/4'"
            ],
            'payment_methods': [
                "💳 *Métodos de pago disponibles:*",
                "• Tarjeta de crédito/débito (inmediato)",
                "• OXXO (se refleja en 24-48 hrs)",
                "• Transferencia SPEI (inmediato)",
                "",
                "Todos los pagos son 100% seguros con Stripe"
            ],
            'order_confirmed': [
                "✅ *¡Pedido confirmado!*",
                "",
                "📋 *Resumen:*",
                "{order_summary}",
                "",
                "💰 *Total a pagar: ${total:,.2f} MXN*",
                "",
                "Te envío el link de pago en un momento..."
            ],
            'payment_link': [
                "💳 *Link de pago seguro:*",
                "{payment_link}",
                "",
                "⏰ El link es válido por 72 horas",
                "📧 Recibirás confirmación por email",
                "",
                "¿Tienes alguna pregunta?"
            ]
        }
    
    def detect_intent(self, message: str) -> CustomerIntent:
        """
        Detecta la intención del mensaje del cliente
        """
        message_lower = message.lower()
        
        # Orden de prioridad para la detección
        priority_order = [
            CustomerIntent.GREETING,
            CustomerIntent.CANCEL,
            CustomerIntent.CONFIRM_PURCHASE,
            CustomerIntent.PAYMENT_METHOD,
            CustomerIntent.PRICE_QUERY,  # Antes que PRODUCT_QUERY
            CustomerIntent.PRODUCT_QUERY,
            CustomerIntent.HELP
        ]
        
        for intent in priority_order:
            patterns = self.intent_patterns.get(intent, [])
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    return intent
        
        # Si tiene números y productos, probablemente es query
        if re.search(r'\d+', message) and len(message.split()) > 2:
            return CustomerIntent.PRODUCT_QUERY
        
        return CustomerIntent.UNKNOWN
    
    def get_conversation_state(self, phone: str) -> Dict:
        """
        Obtiene o crea el estado de conversación
        """
        if phone not in self.conversations:
            self.conversations[phone] = {
                'state': ConversationState.GREETING,
                'context': {
                    'started_at': datetime.now(),
                    'messages': [],
                    'selected_products': [],
                    'customer_info': {},
                    'order': None
                }
            }
        
        # Limpiar conversaciones viejas (>24 hrs)
        conv = self.conversations[phone]
        if datetime.now() - conv['context']['started_at'] > timedelta(hours=24):
            conv['state'] = ConversationState.GREETING
            conv['context'] = {
                'started_at': datetime.now(),
                'messages': [],
                'selected_products': [],
                'customer_info': {},
                'order': None
            }
        
        return conv
    
    def process_message(
        self,
        phone: str,
        message: str,
        business_name: str = "Ferretería",
        catalog: List[Dict] = None
    ) -> Dict[str, Any]:
        """
        Procesa mensaje de WhatsApp y genera respuesta
        """
        # Obtener estado de conversación
        conversation = self.get_conversation_state(phone)
        conversation['context']['messages'].append({
            'from': 'customer',
            'text': message,
            'timestamp': datetime.now()
        })
        
        # Detectar intención
        intent = self.detect_intent(message)
        
        # Procesar según estado e intención
        response = self._handle_conversation(
            conversation,
            intent,
            message,
            business_name,
            catalog
        )
        
        # Guardar respuesta
        conversation['context']['messages'].append({
            'from': 'bot',
            'text': response['text'],
            'timestamp': datetime.now()
        })
        
        # Actualizar estado
        self.conversations[phone] = conversation
        
        return response
    
    def _handle_conversation(
        self,
        conversation: Dict,
        intent: CustomerIntent,
        message: str,
        business_name: str,
        catalog: List[Dict]
    ) -> Dict:
        """
        Maneja la conversación según estado e intención
        """
        state = conversation['state']
        context = conversation['context']
        
        # Estado: GREETING
        if state == ConversationState.GREETING:
            if intent == CustomerIntent.GREETING:
                response_text = '\n'.join(self.responses['greeting'])
                response_text = response_text.replace('{business_name}', business_name)
                conversation['state'] = ConversationState.BROWSING
                
                return {
                    'text': response_text,
                    'quick_replies': ['Ver catálogo', 'Hacer pedido', 'Ayuda']
                }
            
            elif intent == CustomerIntent.PRODUCT_QUERY:
                # Saltar directo a búsqueda
                return self._handle_product_query(conversation, message, catalog)
        
        # Estado: BROWSING
        elif state == ConversationState.BROWSING:
            if intent == CustomerIntent.PRODUCT_QUERY:
                return self._handle_product_query(conversation, message, catalog)
            
            elif intent == CustomerIntent.HELP:
                return {
                    'text': '\n'.join(self.responses['help']),
                    'quick_replies': ['Ver catálogo', 'Métodos de pago']
                }
        
        # Estado: PRODUCT_SELECTED
        elif state == ConversationState.PRODUCT_SELECTED:
            if intent == CustomerIntent.CONFIRM_PURCHASE or message.strip() in ['1', '2', '3']:
                return self._handle_product_selection(conversation, message, catalog)
            
            elif intent == CustomerIntent.CANCEL:
                conversation['state'] = ConversationState.BROWSING
                return {
                    'text': 'No hay problema. ¿Necesitas algo más?',
                    'quick_replies': ['Ver otro producto', 'Ayuda']
                }
        
        # Estado: PAYMENT_METHOD
        elif state == ConversationState.PAYMENT_METHOD:
            return self._handle_payment_method(conversation, message)
        
        # Default: Ayuda
        return {
            'text': 'No entendí tu mensaje. ¿En qué puedo ayudarte?',
            'quick_replies': ['Ver catálogo', 'Hacer pedido', 'Ayuda']
        }
    
    def _handle_product_query(
        self,
        conversation: Dict,
        message: str,
        catalog: List[Dict]
    ) -> Dict:
        """
        Busca productos y genera respuesta
        """
        if not self.catalog_agent or not catalog:
            return {
                'text': 'Lo siento, no tengo acceso al catálogo en este momento.',
                'error': True
            }
        
        # Extraer cantidad del mensaje
        quantity, clean_message = self.catalog_agent.extract_quantity_from_message(message)
        
        # Buscar productos
        products = self.catalog_agent.search_products(clean_message, catalog)
        
        if not products:
            return {
                'text': ('No encontré ese producto 😕\n'
                        '¿Podrías ser más específico?\n\n'
                        'Ejemplos:\n'
                        '• "tubo pvc 3/4"\n'
                        '• "cemento gris 50kg"\n'
                        '• "pintura blanca"'),
                'quick_replies': ['Ver catálogo', 'Ayuda']
            }
        
        # Guardar productos encontrados en contexto
        conversation['context']['found_products'] = products
        conversation['context']['requested_quantity'] = quantity
        conversation['state'] = ConversationState.PRODUCT_SELECTED
        
        # Generar respuesta con productos
        response_text = self.catalog_agent.generate_whatsapp_response(products, quantity)
        
        return {
            'text': response_text,
            'products': products[:3],
            'quick_replies': ['1', '2', '3', 'Buscar otro']
        }
    
    def _handle_product_selection(
        self,
        conversation: Dict,
        message: str,
        catalog: List[Dict]
    ) -> Dict:
        """
        Maneja la selección de producto
        """
        products = conversation['context'].get('found_products', [])
        quantity = conversation['context'].get('requested_quantity', 1)
        
        # Determinar qué producto seleccionó
        selection = None
        if message.strip() in ['1', '2', '3']:
            index = int(message.strip()) - 1
            if index < len(products):
                selection = products[index]
        
        if not selection:
            return {
                'text': 'Por favor selecciona 1, 2 o 3',
                'quick_replies': ['1', '2', '3', 'Buscar otro']
            }
        
        # Calcular total
        unit_price = selection['price']
        total = unit_price * quantity
        
        # Guardar en orden
        conversation['context']['order'] = {
            'items': [{
                'product': selection,
                'quantity': quantity,
                'unit_price': unit_price,
                'total': total
            }],
            'subtotal': total,
            'tax': total * 0.16,  # IVA
            'total': total * 1.16
        }
        
        # Generar resumen
        order_summary = (
            f"• {selection['canonical_name']}\n"
            f"  {quantity} x ${unit_price:,.2f} = ${total:,.2f}"
        )
        
        response_text = '\n'.join(self.responses['order_confirmed'])
        response_text = response_text.replace('{order_summary}', order_summary)
        response_text = response_text.replace('{total}', f"{total * 1.16:,.2f}")
        
        conversation['state'] = ConversationState.PAYMENT_METHOD
        
        return {
            'text': response_text,
            'order': conversation['context']['order'],
            'quick_replies': ['Pagar con tarjeta', 'OXXO', 'Transferencia']
        }
    
    def _handle_payment_method(
        self,
        conversation: Dict,
        message: str
    ) -> Dict:
        """
        Maneja selección de método de pago
        """
        message_lower = message.lower()
        
        # Detectar método
        method = None
        if 'tarjeta' in message_lower:
            method = 'card'
        elif 'oxxo' in message_lower:
            method = 'oxxo'
        elif 'transfer' in message_lower or 'spei' in message_lower:
            method = 'spei'
        
        if not method:
            return {
                'text': '\n'.join(self.responses['payment_methods']),
                'quick_replies': ['Tarjeta', 'OXXO', 'Transferencia SPEI']
            }
        
        # Guardar método
        conversation['context']['payment_method'] = method
        conversation['state'] = ConversationState.PAYMENT_SENT
        
        # Generar link de pago (simulado)
        payment_link = f"https://pay.clienteos.mx/p/{hash(conversation['context']['started_at'])}"
        
        response_text = '\n'.join(self.responses['payment_link'])
        response_text = response_text.replace('{payment_link}', payment_link)
        
        return {
            'text': response_text,
            'payment_link': payment_link,
            'payment_method': method,
            'needs_payment': True
        }
    
    def get_analytics(self) -> Dict:
        """
        Obtiene métricas de las conversaciones
        """
        total_conversations = len(self.conversations)
        completed = sum(1 for c in self.conversations.values() 
                       if c['state'] == ConversationState.COMPLETED)
        abandoned = sum(1 for c in self.conversations.values()
                       if c['state'] == ConversationState.ABANDONED)
        
        return {
            'total_conversations': total_conversations,
            'completed_sales': completed,
            'abandoned_carts': abandoned,
            'conversion_rate': (completed / total_conversations * 100) if total_conversations > 0 else 0,
            'active_conversations': total_conversations - completed - abandoned
        }