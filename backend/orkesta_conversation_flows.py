"""
💬 Orkesta Conversation Flows - Conversaciones complejas y largas
=================================================================

Sistema de conversaciones avanzadas con memoria y contexto.
Para crear "el mejor agente de ventas" con flujos sofisticados.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from orkesta_shared_context import get_shared_context, OrkestaSharedContext
from orkesta_smart_agents import (
    CatalogMapperAgent, AliasNormalizerAgent, 
    PriceResolverAgent, QuoteBuilderAgent
)

logger = logging.getLogger(__name__)

class ConversationStage(Enum):
    """Etapas de la conversación"""
    GREETING = "greeting"
    DISCOVERY = "discovery"
    PRODUCT_EXPLORATION = "product_exploration"
    NEEDS_ANALYSIS = "needs_analysis"
    QUOTE_BUILDING = "quote_building"
    OBJECTION_HANDLING = "objection_handling"
    CLOSING = "closing"
    PAYMENT_PROCESSING = "payment_processing"
    FOLLOW_UP = "follow_up"
    COMPLETED = "completed"

class ConversationIntent(Enum):
    """Intenciones detectadas en la conversación"""
    BROWSE_CATALOG = "browse_catalog"
    PRICE_INQUIRY = "price_inquiry"
    BULK_ORDER = "bulk_order"
    CUSTOM_QUOTE = "custom_quote"
    TECHNICAL_SUPPORT = "technical_support"
    PAYMENT_QUESTION = "payment_question"
    DELIVERY_INQUIRY = "delivery_inquiry"
    COMPLAINT = "complaint"
    UPSELL_OPPORTUNITY = "upsell_opportunity"
    PRICE_OBJECTION = "price_objection"
    COMPETITOR_COMPARISON = "competitor_comparison"

@dataclass
class ConversationTurn:
    """Un turno en la conversación"""
    timestamp: datetime
    speaker: str  # "customer" | "agent"
    message: str
    intent: Optional[ConversationIntent]
    entities: Dict[str, Any]  # Productos, cantidades, precios mencionados
    sentiment: str  # "positive" | "neutral" | "negative"
    confidence: float
    stage: ConversationStage
    agent_reasoning: str = ""

@dataclass
class ConversationContext:
    """Contexto completo de una conversación"""
    conversation_id: str
    tenant_id: str
    customer_id: str
    channel: str  # "whatsapp" | "web" | "phone" | "email"
    started_at: datetime
    last_activity: datetime
    current_stage: ConversationStage
    customer_profile: Dict[str, Any]
    conversation_summary: str
    identified_needs: List[str]
    discussed_products: List[Dict[str, Any]]
    current_quote: Optional[Dict[str, Any]]
    objections_raised: List[str]
    sentiment_history: List[Tuple[datetime, str]]
    turns: List[ConversationTurn]
    metadata: Dict[str, Any]

class ConversationEngine:
    """Motor de conversaciones complejas"""
    
    def __init__(self):
        # Storage de conversaciones activas (en prod usar DB)
        self.active_conversations: Dict[str, ConversationContext] = {}
        
        # Agentes especializados
        self.catalog_agent = CatalogMapperAgent()
        self.alias_agent = AliasNormalizerAgent()
        self.price_agent = PriceResolverAgent()
        self.quote_agent = QuoteBuilderAgent()
        
        # Templates de respuesta por etapa
        self.response_templates = self._load_response_templates()
        
        # Reglas de transición entre etapas
        self.stage_transitions = self._setup_stage_transitions()
    
    def start_conversation(self, tenant_id: str, customer_id: str, 
                         channel: str = "web",
                         customer_profile: Dict[str, Any] = None) -> str:
        """Inicia una nueva conversación"""
        
        conversation_id = f"conv_{tenant_id}_{customer_id}_{int(time.time())}"
        
        context = ConversationContext(
            conversation_id=conversation_id,
            tenant_id=tenant_id,
            customer_id=customer_id,
            channel=channel,
            started_at=datetime.now(),
            last_activity=datetime.now(),
            current_stage=ConversationStage.GREETING,
            customer_profile=customer_profile or {},
            conversation_summary="",
            identified_needs=[],
            discussed_products=[],
            current_quote=None,
            objections_raised=[],
            sentiment_history=[],
            turns=[],
            metadata={}
        )
        
        self.active_conversations[conversation_id] = context
        
        logger.info(f"Started conversation {conversation_id} for tenant {tenant_id}")
        
        return conversation_id
    
    async def process_customer_message(self, conversation_id: str, 
                                     message: str) -> Dict[str, Any]:
        """Procesa un mensaje del cliente y genera respuesta inteligente"""
        
        if conversation_id not in self.active_conversations:
            raise ValueError(f"Conversation {conversation_id} not found")
        
        context = self.active_conversations[conversation_id]
        
        # 1. Análisis del mensaje
        analysis = await self._analyze_message(message, context)
        
        # 2. Crear turno del cliente
        customer_turn = ConversationTurn(
            timestamp=datetime.now(),
            speaker="customer",
            message=message,
            intent=analysis["intent"],
            entities=analysis["entities"],
            sentiment=analysis["sentiment"],
            confidence=analysis["confidence"],
            stage=context.current_stage
        )
        
        context.turns.append(customer_turn)
        context.last_activity = datetime.now()
        
        # 3. Actualizar historial de sentimiento
        context.sentiment_history.append(
            (datetime.now(), analysis["sentiment"])
        )
        
        # 4. Determinar transición de etapa
        new_stage = self._determine_stage_transition(context, analysis)
        if new_stage != context.current_stage:
            logger.info(f"Conversation {conversation_id} transitioning: "
                       f"{context.current_stage.value} → {new_stage.value}")
            context.current_stage = new_stage
        
        # 5. Ejecutar acciones basadas en intención
        actions_result = await self._execute_intent_actions(context, analysis)
        
        # 6. Generar respuesta inteligente
        agent_response = await self._generate_agent_response(context, analysis, actions_result)
        
        # 7. Crear turno del agente
        agent_turn = ConversationTurn(
            timestamp=datetime.now(),
            speaker="agent",
            message=agent_response["message"],
            intent=None,
            entities={},
            sentiment="positive",  # El agente siempre es positivo
            confidence=agent_response["confidence"],
            stage=context.current_stage,
            agent_reasoning=agent_response["reasoning"]
        )
        
        context.turns.append(agent_turn)
        
        # 8. Actualizar resumen de conversación
        context.conversation_summary = self._update_conversation_summary(context)
        
        return {
            "conversation_id": conversation_id,
            "agent_message": agent_response["message"],
            "current_stage": context.current_stage.value,
            "customer_sentiment": analysis["sentiment"],
            "detected_intent": analysis["intent"].value if analysis["intent"] else None,
            "suggested_actions": agent_response.get("suggested_actions", []),
            "conversation_health": self._assess_conversation_health(context),
            "next_best_actions": self._suggest_next_actions(context),
            "metadata": {
                "turn_count": len(context.turns),
                "conversation_duration": str(datetime.now() - context.started_at),
                "products_discussed": len(context.discussed_products),
                "quote_value": context.current_quote.get("total", 0) if context.current_quote else 0
            }
        }
    
    async def _analyze_message(self, message: str, 
                             context: ConversationContext) -> Dict[str, Any]:
        """Análisis avanzado del mensaje del cliente"""
        
        # Obtener contexto compartido para análisis
        shared_context = get_shared_context(context.tenant_id)
        
        # Detección de intención usando patrones
        intent = self._detect_intent(message, context)
        
        # Extracción de entidades (productos, cantidades, precios)
        entities = await self._extract_entities(message, context, shared_context)
        
        # Análisis de sentimiento
        sentiment = self._analyze_sentiment(message, context)
        
        # Confianza del análisis
        confidence = self._calculate_analysis_confidence(message, intent, entities)
        
        return {
            "intent": intent,
            "entities": entities,
            "sentiment": sentiment,
            "confidence": confidence,
            "key_phrases": self._extract_key_phrases(message),
            "urgency": self._detect_urgency(message),
            "complexity": self._assess_message_complexity(message)
        }
    
    def _detect_intent(self, message: str, context: ConversationContext) -> Optional[ConversationIntent]:
        """Detecta la intención del mensaje"""
        
        message_lower = message.lower()
        
        # Patrones de intención por palabras clave
        intent_patterns = {
            ConversationIntent.BROWSE_CATALOG: [
                "catálogo", "productos", "que tienen", "que venden", "opciones",
                "disponible", "inventario", "lista", "ver productos"
            ],
            ConversationIntent.PRICE_INQUIRY: [
                "precio", "costo", "cuanto", "cuánto", "vale", "tarifa",
                "cotización", "presupuesto", "cuota"
            ],
            ConversationIntent.BULK_ORDER: [
                "mayoreo", "volumen", "cantidad", "piezas", "docenas", 
                "lote", "pedido grande", "al por mayor"
            ],
            ConversationIntent.CUSTOM_QUOTE: [
                "cotización", "presupuesto", "personalizado", "especial",
                "a medida", "particular", "específico"
            ],
            ConversationIntent.TECHNICAL_SUPPORT: [
                "ayuda", "problema", "no funciona", "error", "soporte",
                "asistencia", "configurar", "instalar"
            ],
            ConversationIntent.PAYMENT_QUESTION: [
                "pago", "forma de pago", "tarjeta", "efectivo", "transferencia",
                "meses sin intereses", "financiamiento", "crédito"
            ],
            ConversationIntent.DELIVERY_INQUIRY: [
                "entrega", "envío", "delivery", "cuando llega", "tiempo",
                "domicilio", "dirección", "logística"
            ],
            ConversationIntent.COMPLAINT: [
                "queja", "problema", "mal servicio", "defectuoso", "reclamo",
                "insatisfecho", "molesto", "decepcionado"
            ],
            ConversationIntent.PRICE_OBJECTION: [
                "muy caro", "expensive", "más barato", "descuento", "oferta",
                "competencia", "mejor precio", "no puedo pagar"
            ],
            ConversationIntent.COMPETITOR_COMPARISON: [
                "competencia", "otros proveedores", "mercado libre", "amazon",
                "comparar", "mejor opción", "alternativa"
            ]
        }
        
        # Encontrar la intención con más coincidencias
        best_intent = None
        max_matches = 0
        
        for intent, patterns in intent_patterns.items():
            matches = sum(1 for pattern in patterns if pattern in message_lower)
            if matches > max_matches:
                max_matches = matches
                best_intent = intent
        
        # Considerar el contexto de la conversación
        if best_intent is None and context.current_stage == ConversationStage.QUOTE_BUILDING:
            if any(word in message_lower for word in ["sí", "si", "acepto", "ok", "adelante"]):
                best_intent = ConversationIntent.CUSTOM_QUOTE
        
        return best_intent
    
    async def _extract_entities(self, message: str, context: ConversationContext,
                               shared_context: OrkestaSharedContext) -> Dict[str, Any]:
        """Extrae entidades del mensaje (productos, cantidades, etc.)"""
        
        entities = {
            "products": [],
            "quantities": [],
            "prices": [],
            "locations": [],
            "dates": [],
            "contact_info": []
        }
        
        # Buscar productos mencionados
        catalog = shared_context.get_catalog()
        message_lower = message.lower()
        
        for product in catalog:
            product_name = product.get("name", "").lower()
            # Buscar menciones exactas y parciales
            if product_name in message_lower or any(
                alias.lower() in message_lower 
                for alias in product.get("aliases", [])
            ):
                entities["products"].append({
                    "id": product["id"],
                    "name": product["name"],
                    "category": product.get("category"),
                    "price": product.get("price"),
                    "mentioned_as": product_name  # Como fue mencionado
                })
        
        # Extraer cantidades usando patrones
        import re
        
        quantity_patterns = [
            r'(\d+)\s*(piezas?|unidades?|docenas?|lotes?)',
            r'(\d+)\s*de\s+',
            r'necesito\s+(\d+)',
            r'quiero\s+(\d+)',
            r'(\d+)\s*[a-zA-Z]+'
        ]
        
        for pattern in quantity_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                try:
                    qty = int(match[0] if isinstance(match, tuple) else match)
                    entities["quantities"].append(qty)
                except ValueError:
                    continue
        
        # Extraer precios mencionados
        price_patterns = [
            r'\$\s*(\d+(?:,\d{3})*(?:\.\d{2})?)',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*pesos',
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)\s*mxn'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, message_lower)
            for match in matches:
                try:
                    # Limpiar formato de precio
                    price_str = match.replace(',', '')
                    price = float(price_str)
                    entities["prices"].append(price)
                except ValueError:
                    continue
        
        return entities
    
    def _analyze_sentiment(self, message: str, context: ConversationContext) -> str:
        """Análisis de sentimiento del mensaje"""
        
        message_lower = message.lower()
        
        positive_indicators = [
            "excelente", "perfecto", "genial", "fantástico", "me gusta",
            "muy bien", "interesante", "gracias", "bueno", "sí", "si",
            "adelante", "acepto", "ok", "perfect", "great"
        ]
        
        negative_indicators = [
            "malo", "terrible", "horrible", "no me gusta", "problema",
            "molesto", "caro", "expensive", "no", "nunca", "jamás",
            "cancelar", "no quiero", "mal servicio", "defectuoso"
        ]
        
        positive_score = sum(1 for indicator in positive_indicators if indicator in message_lower)
        negative_score = sum(1 for indicator in negative_indicators if indicator in message_lower)
        
        # Considerar historial de sentimiento
        recent_sentiment = [
            sentiment for timestamp, sentiment in context.sentiment_history[-3:]
        ]
        
        if positive_score > negative_score:
            return "positive"
        elif negative_score > positive_score:
            return "negative"
        elif recent_sentiment.count("negative") >= 2:
            return "negative"  # Escalating negativity
        else:
            return "neutral"
    
    def _determine_stage_transition(self, context: ConversationContext, 
                                  analysis: Dict[str, Any]) -> ConversationStage:
        """Determina si debe cambiar la etapa de conversación"""
        
        current_stage = context.current_stage
        intent = analysis["intent"]
        sentiment = analysis["sentiment"]
        
        # Reglas de transición basadas en intención y contexto
        transitions = self.stage_transitions.get(current_stage, {})
        
        # Transición por intención
        if intent and intent in transitions:
            return transitions[intent]
        
        # Transiciones automáticas por tiempo o condiciones
        conversation_duration = datetime.now() - context.started_at
        
        if current_stage == ConversationStage.GREETING:
            if len(context.turns) >= 2:  # Después de saludo inicial
                if intent in [ConversationIntent.BROWSE_CATALOG, ConversationIntent.PRICE_INQUIRY]:
                    return ConversationStage.PRODUCT_EXPLORATION
                else:
                    return ConversationStage.DISCOVERY
        
        elif current_stage == ConversationStage.DISCOVERY:
            if context.identified_needs:
                return ConversationStage.PRODUCT_EXPLORATION
        
        elif current_stage == ConversationStage.PRODUCT_EXPLORATION:
            if len(context.discussed_products) >= 2:
                return ConversationStage.NEEDS_ANALYSIS
        
        elif current_stage == ConversationStage.NEEDS_ANALYSIS:
            if intent == ConversationIntent.CUSTOM_QUOTE:
                return ConversationStage.QUOTE_BUILDING
        
        elif current_stage == ConversationStage.QUOTE_BUILDING:
            if sentiment == "negative" and intent == ConversationIntent.PRICE_OBJECTION:
                return ConversationStage.OBJECTION_HANDLING
            elif context.current_quote and sentiment == "positive":
                return ConversationStage.CLOSING
        
        elif current_stage == ConversationStage.OBJECTION_HANDLING:
            if sentiment == "positive":
                return ConversationStage.QUOTE_BUILDING
        
        elif current_stage == ConversationStage.CLOSING:
            if intent == ConversationIntent.PAYMENT_QUESTION:
                return ConversationStage.PAYMENT_PROCESSING
        
        return current_stage  # No hay transición
    
    async def _execute_intent_actions(self, context: ConversationContext,
                                    analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Ejecuta acciones basadas en la intención detectada"""
        
        intent = analysis["intent"]
        entities = analysis["entities"]
        result = {"actions_taken": [], "data": {}}
        
        shared_context = get_shared_context(context.tenant_id)
        
        if intent == ConversationIntent.BROWSE_CATALOG:
            # Obtener catálogo filtrado
            catalog = shared_context.get_catalog()
            result["data"]["catalog"] = catalog[:10]  # Primeros 10 productos
            result["actions_taken"].append("catalog_retrieved")
        
        elif intent == ConversationIntent.PRICE_INQUIRY:
            # Buscar precios de productos mencionados
            if entities["products"]:
                prices = []
                for product in entities["products"]:
                    price_info = await self.price_agent.resolve_price(
                        context.tenant_id, product["id"], 
                        entities["quantities"][0] if entities["quantities"] else 1
                    )
                    prices.append(price_info)
                
                result["data"]["prices"] = prices
                result["actions_taken"].append("prices_calculated")
        
        elif intent == ConversationIntent.CUSTOM_QUOTE:
            # Construir cotización
            if entities["products"]:
                quote = await self.quote_agent.build_quote(
                    context.tenant_id,
                    entities["products"],
                    entities["quantities"] if entities["quantities"] else [1] * len(entities["products"])
                )
                
                context.current_quote = quote
                result["data"]["quote"] = quote
                result["actions_taken"].append("quote_built")
        
        elif intent == ConversationIntent.BULK_ORDER:
            # Manejar pedido de volumen
            if entities["products"] and entities["quantities"]:
                # Calcular descuentos por volumen
                bulk_pricing = await self._calculate_bulk_pricing(
                    context.tenant_id, entities["products"], entities["quantities"]
                )
                result["data"]["bulk_pricing"] = bulk_pricing
                result["actions_taken"].append("bulk_pricing_calculated")
        
        elif intent == ConversationIntent.COMPETITOR_COMPARISON:
            # Preparar comparación con competencia
            comparison = self._prepare_competitive_analysis(entities["products"])
            result["data"]["competitive_analysis"] = comparison
            result["actions_taken"].append("competitive_analysis_prepared")
        
        # Actualizar contexto basado en las acciones
        if entities["products"]:
            for product in entities["products"]:
                if product not in context.discussed_products:
                    context.discussed_products.append(product)
        
        return result
    
    async def _generate_agent_response(self, context: ConversationContext,
                                     analysis: Dict[str, Any],
                                     actions_result: Dict[str, Any]) -> Dict[str, Any]:
        """Genera respuesta inteligente del agente"""
        
        stage = context.current_stage
        intent = analysis["intent"]
        sentiment = analysis["sentiment"]
        entities = analysis["entities"]
        
        # Obtener template base para la etapa actual
        template = self.response_templates.get(stage, {})
        
        # Personalizar respuesta basada en intención y sentimiento
        response_parts = []
        reasoning_parts = []
        
        # 1. Reconocimiento/Empatía
        if sentiment == "negative":
            response_parts.append("Entiendo tu preocupación.")
            reasoning_parts.append("Customer shows negative sentiment - addressing with empathy")
        elif sentiment == "positive":
            response_parts.append("¡Excelente!")
            reasoning_parts.append("Customer is positive - reinforcing good mood")
        
        # 2. Respuesta específica a la intención
        if intent == ConversationIntent.BROWSE_CATALOG:
            catalog_data = actions_result.get("data", {}).get("catalog", [])
            if catalog_data:
                response_parts.append(f"Tenemos {len(catalog_data)} productos principales que podrían interesarte:")
                for product in catalog_data[:3]:  # Mostrar solo 3
                    response_parts.append(f"• {product['name']} - ${product.get('price', 'Consultar')}")
                reasoning_parts.append("Showing relevant products from catalog")
            else:
                response_parts.append("Permíteme mostrarte nuestro catálogo de productos.")
        
        elif intent == ConversationIntent.PRICE_INQUIRY:
            if entities["products"]:
                prices_data = actions_result.get("data", {}).get("prices", [])
                if prices_data:
                    response_parts.append("Aquí tienes los precios:")
                    for price_info in prices_data:
                        response_parts.append(f"• {price_info['product_name']}: ${price_info['final_price']}")
                reasoning_parts.append("Providing requested pricing information")
            else:
                response_parts.append("¿Qué productos te interesan para cotizar?")
        
        elif intent == ConversationIntent.CUSTOM_QUOTE:
            quote_data = actions_result.get("data", {}).get("quote")
            if quote_data:
                response_parts.append(f"He preparado una cotización por ${quote_data['total']:,.2f}")
                response_parts.append("¿Te gustaría revisar los detalles?")
                reasoning_parts.append("Built custom quote based on discussed products")
            else:
                response_parts.append("Perfecto, voy a preparar una cotización personalizada.")
        
        elif intent == ConversationIntent.PRICE_OBJECTION:
            # Manejo de objeciones de precio
            response_parts.append("Entiendo que el precio es importante.")
            response_parts.append("Déjame explicarte el valor que incluye y ver opciones para ajustarnos a tu presupuesto.")
            reasoning_parts.append("Handling price objection with value proposition")
        
        # 3. Preguntas de seguimiento inteligentes
        follow_up = self._generate_smart_follow_up(context, intent, stage)
        if follow_up:
            response_parts.append(follow_up)
            reasoning_parts.append("Adding intelligent follow-up question")
        
        # 4. Llamada a la acción basada en la etapa
        cta = self._generate_stage_cta(stage, context)
        if cta:
            response_parts.append(cta)
            reasoning_parts.append("Including stage-appropriate call-to-action")
        
        # Ensamblar respuesta final
        final_message = " ".join(response_parts)
        
        # Sugerir acciones para el agente humano (si es necesario)
        suggested_actions = self._suggest_agent_actions(context, analysis)
        
        return {
            "message": final_message,
            "confidence": 0.85,  # Base confidence
            "reasoning": " | ".join(reasoning_parts),
            "suggested_actions": suggested_actions,
            "response_type": "intelligent_contextual"
        }
    
    def _generate_smart_follow_up(self, context: ConversationContext,
                                intent: ConversationIntent,
                                stage: ConversationStage) -> Optional[str]:
        """Genera preguntas de seguimiento inteligentes"""
        
        follow_ups = {
            ConversationStage.DISCOVERY: [
                "¿Para qué tipo de proyecto o uso necesitas estos productos?",
                "¿Cuál es tu presupuesto aproximado?",
                "¿Hay algún requerimiento específico que deba considerar?"
            ],
            ConversationStage.PRODUCT_EXPLORATION: [
                "¿Te gustaría conocer más detalles de algún producto en particular?",
                "¿Qué características son más importantes para ti?",
                "¿Manejas pedidos regulares o es una compra única?"
            ],
            ConversationStage.NEEDS_ANALYSIS: [
                "¿Necesitas algún servicio adicional como instalación o capacitación?",
                "¿Qué plazo de entrega manejas?",
                "¿Hay otros productos complementarios que te interesen?"
            ],
            ConversationStage.QUOTE_BUILDING: [
                "¿Te gustaría ajustar alguna cantidad?",
                "¿Necesitas opciones de financiamiento?",
                "¿Prefieres que revisemos alternativas en diferentes rangos de precio?"
            ]
        }
        
        stage_questions = follow_ups.get(stage, [])
        if stage_questions:
            # Seleccionar pregunta basada en el contexto
            import random
            return random.choice(stage_questions)
        
        return None
    
    def _generate_stage_cta(self, stage: ConversationStage, 
                          context: ConversationContext) -> Optional[str]:
        """Genera llamada a la acción apropiada para la etapa"""
        
        ctas = {
            ConversationStage.GREETING: "¿En qué puedo ayudarte hoy?",
            ConversationStage.DISCOVERY: "Cuéntame más sobre lo que necesitas.",
            ConversationStage.PRODUCT_EXPLORATION: "¿Te gustaría que preparemos una cotización?",
            ConversationStage.QUOTE_BUILDING: "¿Procedemos con esta cotización?",
            ConversationStage.CLOSING: "¿Quieres que procesemos el pedido?",
            ConversationStage.PAYMENT_PROCESSING: "Te ayudo con las opciones de pago."
        }
        
        return ctas.get(stage)
    
    def _suggest_agent_actions(self, context: ConversationContext,
                             analysis: Dict[str, Any]) -> List[str]:
        """Sugiere acciones para agente humano si es necesario"""
        
        suggestions = []
        
        # Si hay sentimiento muy negativo
        if analysis["sentiment"] == "negative":
            negative_count = sum(1 for _, s in context.sentiment_history[-3:] if s == "negative")
            if negative_count >= 2:
                suggestions.append("escalate_to_human")
                suggestions.append("offer_manager_call")
        
        # Si la cotización es muy alta
        if context.current_quote and context.current_quote.get("total", 0) > 50000:
            suggestions.append("manager_approval_needed")
        
        # Si hay competencia mencionada
        if analysis["intent"] == ConversationIntent.COMPETITOR_COMPARISON:
            suggestions.append("prepare_competitive_analysis")
        
        # Si es bulk order
        if analysis["intent"] == ConversationIntent.BULK_ORDER:
            suggestions.append("check_inventory_availability")
            suggestions.append("consider_volume_discount")
        
        return suggestions
    
    def _assess_conversation_health(self, context: ConversationContext) -> Dict[str, Any]:
        """Evalúa la salud de la conversación"""
        
        # Analizar tendencia de sentimiento
        recent_sentiments = [s for _, s in context.sentiment_history[-5:]]
        positive_ratio = recent_sentiments.count("positive") / len(recent_sentiments) if recent_sentiments else 0
        
        # Duración de conversación
        duration = datetime.now() - context.started_at
        duration_minutes = duration.total_seconds() / 60
        
        # Engagement score
        turns_count = len(context.turns)
        avg_response_time = duration_minutes / (turns_count / 2) if turns_count > 0 else 0
        
        # Health score
        health_score = 0.0
        health_factors = []
        
        # Factor: Sentimiento positivo
        health_score += positive_ratio * 30
        health_factors.append(f"Sentiment: {positive_ratio:.1%} positive")
        
        # Factor: Productos discutidos
        if context.discussed_products:
            health_score += min(len(context.discussed_products) * 10, 30)
            health_factors.append(f"Products discussed: {len(context.discussed_products)}")
        
        # Factor: Cotización construida
        if context.current_quote:
            health_score += 25
            health_factors.append("Quote built")
        
        # Factor: Duración apropiada
        if 5 <= duration_minutes <= 30:
            health_score += 15
            health_factors.append("Good duration")
        
        health_level = "excellent" if health_score >= 80 else \
                      "good" if health_score >= 60 else \
                      "fair" if health_score >= 40 else "poor"
        
        return {
            "health_score": health_score,
            "health_level": health_level,
            "factors": health_factors,
            "positive_sentiment_ratio": positive_ratio,
            "conversation_duration_minutes": duration_minutes,
            "engagement_level": "high" if turns_count >= 8 else "medium" if turns_count >= 4 else "low"
        }
    
    def _suggest_next_actions(self, context: ConversationContext) -> List[str]:
        """Sugiere las mejores próximas acciones"""
        
        stage = context.current_stage
        actions = []
        
        if stage == ConversationStage.DISCOVERY:
            actions.extend([
                "Ask about specific needs",
                "Explore budget range", 
                "Identify decision makers"
            ])
        
        elif stage == ConversationStage.PRODUCT_EXPLORATION:
            actions.extend([
                "Present top 3 products",
                "Explain key benefits",
                "Show price comparisons"
            ])
        
        elif stage == ConversationStage.QUOTE_BUILDING:
            actions.extend([
                "Present detailed quote",
                "Highlight value proposition",
                "Offer payment options"
            ])
        
        elif stage == ConversationStage.OBJECTION_HANDLING:
            actions.extend([
                "Address price concerns",
                "Show competitive advantages",
                "Offer alternatives"
            ])
        
        elif stage == ConversationStage.CLOSING:
            actions.extend([
                "Create urgency",
                "Confirm next steps",
                "Process order"
            ])
        
        # Acciones basadas en contexto
        if not context.discussed_products:
            actions.append("Show product catalog")
        
        if not context.current_quote and len(context.discussed_products) >= 2:
            actions.append("Build custom quote")
        
        if context.current_quote and context.current_stage != ConversationStage.CLOSING:
            actions.append("Present quote")
        
        return actions[:5]  # Top 5 acciones
    
    def _load_response_templates(self) -> Dict[ConversationStage, Dict[str, str]]:
        """Carga templates de respuesta por etapa"""
        
        return {
            ConversationStage.GREETING: {
                "default": "¡Hola! Soy tu asistente de ventas especializado. ¿En qué puedo ayudarte hoy?",
                "returning": "¡Hola de nuevo! Me da mucho gusto verte. ¿Cómo puedo ayudarte esta vez?",
                "vip": "¡Hola! Es un placer atenderte. Como cliente VIP, tengo acceso a ofertas especiales para ti."
            },
            ConversationStage.DISCOVERY: {
                "default": "Perfecto, cuéntame más sobre lo que necesitas para poder ayudarte mejor.",
                "technical": "Entiendo que buscas algo específico. ¿Puedes darme más detalles técnicos?",
                "budget": "Excelente, ¿tienes un rango de presupuesto en mente?"
            },
            ConversationStage.PRODUCT_EXPLORATION: {
                "default": "Basado en lo que me comentas, estos productos podrían ser perfectos:",
                "comparison": "Te muestro las opciones que mejor se adaptan a tus necesidades:",
                "alternatives": "También tengo estas alternativas que podrían interesarte:"
            }
        }
    
    def _setup_stage_transitions(self) -> Dict[ConversationStage, Dict[ConversationIntent, ConversationStage]]:
        """Configura reglas de transición entre etapas"""
        
        return {
            ConversationStage.GREETING: {
                ConversationIntent.BROWSE_CATALOG: ConversationStage.PRODUCT_EXPLORATION,
                ConversationIntent.PRICE_INQUIRY: ConversationStage.PRODUCT_EXPLORATION,
                ConversationIntent.TECHNICAL_SUPPORT: ConversationStage.DISCOVERY,
                ConversationIntent.COMPLAINT: ConversationStage.DISCOVERY
            },
            ConversationStage.DISCOVERY: {
                ConversationIntent.BROWSE_CATALOG: ConversationStage.PRODUCT_EXPLORATION,
                ConversationIntent.CUSTOM_QUOTE: ConversationStage.QUOTE_BUILDING,
                ConversationIntent.BULK_ORDER: ConversationStage.NEEDS_ANALYSIS
            },
            ConversationStage.PRODUCT_EXPLORATION: {
                ConversationIntent.PRICE_INQUIRY: ConversationStage.QUOTE_BUILDING,
                ConversationIntent.CUSTOM_QUOTE: ConversationStage.QUOTE_BUILDING,
                ConversationIntent.COMPETITOR_COMPARISON: ConversationStage.OBJECTION_HANDLING
            },
            ConversationStage.QUOTE_BUILDING: {
                ConversationIntent.PRICE_OBJECTION: ConversationStage.OBJECTION_HANDLING,
                ConversationIntent.PAYMENT_QUESTION: ConversationStage.PAYMENT_PROCESSING
            },
            ConversationStage.OBJECTION_HANDLING: {
                ConversationIntent.CUSTOM_QUOTE: ConversationStage.QUOTE_BUILDING,
                ConversationIntent.PRICE_INQUIRY: ConversationStage.QUOTE_BUILDING
            }
        }
    
    def _calculate_analysis_confidence(self, message: str, 
                                     intent: Optional[ConversationIntent],
                                     entities: Dict[str, Any]) -> float:
        """Calcula confianza del análisis"""
        
        confidence = 0.5  # Base confidence
        
        # Boost por intención detectada
        if intent:
            confidence += 0.2
        
        # Boost por entidades extraídas
        if entities["products"]:
            confidence += 0.1
        if entities["quantities"]:
            confidence += 0.1
        if entities["prices"]:
            confidence += 0.1
        
        # Reducir por mensaje muy corto o ambiguo
        if len(message.split()) < 3:
            confidence -= 0.2
        
        return min(confidence, 1.0)
    
    def _extract_key_phrases(self, message: str) -> List[str]:
        """Extrae frases clave del mensaje"""
        
        # Simplificado - en producción usar NLP más avanzado
        words = message.lower().split()
        key_phrases = []
        
        # Buscar frases importantes
        important_patterns = [
            "necesito", "quiero", "busco", "precio", "cuanto",
            "cuando", "donde", "como", "mejor", "barato"
        ]
        
        for pattern in important_patterns:
            if pattern in message.lower():
                key_phrases.append(pattern)
        
        return key_phrases
    
    def _detect_urgency(self, message: str) -> str:
        """Detecta nivel de urgencia en el mensaje"""
        
        urgent_indicators = [
            "urgente", "rápido", "ya", "hoy", "inmediato",
            "emergencia", "prisa", "necesito ya"
        ]
        
        high_priority = [
            "importante", "prioridad", "fecha límite"
        ]
        
        message_lower = message.lower()
        
        if any(indicator in message_lower for indicator in urgent_indicators):
            return "high"
        elif any(indicator in message_lower for indicator in high_priority):
            return "medium"
        else:
            return "low"
    
    def _assess_message_complexity(self, message: str) -> str:
        """Evalúa complejidad del mensaje"""
        
        word_count = len(message.split())
        
        if word_count > 30:
            return "high"
        elif word_count > 10:
            return "medium"
        else:
            return "low"
    
    def _update_conversation_summary(self, context: ConversationContext) -> str:
        """Actualiza resumen de la conversación"""
        
        summary_parts = []
        
        # Información básica
        summary_parts.append(f"Customer: {context.customer_id}")
        summary_parts.append(f"Stage: {context.current_stage.value}")
        summary_parts.append(f"Duration: {str(datetime.now() - context.started_at)}")
        
        # Productos discutidos
        if context.discussed_products:
            products = [p["name"] for p in context.discussed_products]
            summary_parts.append(f"Products: {', '.join(products[:3])}")
        
        # Estado de cotización
        if context.current_quote:
            summary_parts.append(f"Quote: ${context.current_quote['total']:,.2f}")
        
        # Sentimiento general
        recent_sentiments = [s for _, s in context.sentiment_history[-3:]]
        if recent_sentiments:
            sentiment_summary = max(set(recent_sentiments), key=recent_sentiments.count)
            summary_parts.append(f"Sentiment: {sentiment_summary}")
        
        return " | ".join(summary_parts)
    
    async def _calculate_bulk_pricing(self, tenant_id: str, 
                                    products: List[Dict[str, Any]],
                                    quantities: List[int]) -> Dict[str, Any]:
        """Calcula precios especiales por volumen"""
        
        # Simplificado - en producción integrar con sistema de precios
        bulk_discounts = {
            10: 0.05,   # 5% descuento por 10+ unidades
            50: 0.10,   # 10% descuento por 50+ unidades
            100: 0.15,  # 15% descuento por 100+ unidades
            500: 0.20   # 20% descuento por 500+ unidades
        }
        
        pricing_result = []
        
        for i, product in enumerate(products):
            qty = quantities[i] if i < len(quantities) else 1
            base_price = product.get("price", 0)
            
            # Determinar descuento
            discount = 0
            for min_qty, discount_pct in sorted(bulk_discounts.items(), reverse=True):
                if qty >= min_qty:
                    discount = discount_pct
                    break
            
            final_price = base_price * (1 - discount)
            total = final_price * qty
            
            pricing_result.append({
                "product_id": product["id"],
                "product_name": product["name"],
                "quantity": qty,
                "base_price": base_price,
                "discount_pct": discount * 100,
                "final_price": final_price,
                "total": total
            })
        
        total_order = sum(item["total"] for item in pricing_result)
        
        return {
            "items": pricing_result,
            "total_order": total_order,
            "total_discount": sum(item["total"] - (item["base_price"] * item["quantity"]) for item in pricing_result),
            "discount_applied": any(item["discount_pct"] > 0 for item in pricing_result)
        }
    
    def _prepare_competitive_analysis(self, products: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepara análisis competitivo"""
        
        # Datos simulados de competencia
        competitive_advantages = [
            "Mejor calidad de materiales",
            "Garantía extendida incluida",
            "Soporte técnico 24/7",
            "Entrega más rápida",
            "Mejor relación precio-calidad",
            "Experiencia de 15+ años en el mercado"
        ]
        
        return {
            "our_advantages": competitive_advantages[:3],
            "price_positioning": "Competitive with superior value",
            "unique_selling_points": [
                "Garantía de satisfacción 100%",
                "Instalación gratuita incluida",
                "Capacitación sin costo adicional"
            ]
        }
    
    def get_conversation_analytics(self, tenant_id: str, 
                                 days: int = 30) -> Dict[str, Any]:
        """Obtiene analytics de conversaciones"""
        
        since = datetime.now() - timedelta(days=days)
        
        # Filtrar conversaciones del tenant en el período
        tenant_conversations = [
            conv for conv in self.active_conversations.values()
            if conv.tenant_id == tenant_id and conv.started_at > since
        ]
        
        if not tenant_conversations:
            return {
                "tenant_id": tenant_id,
                "period_days": days,
                "total_conversations": 0
            }
        
        # Calcular métricas
        total_conversations = len(tenant_conversations)
        completed_sales = sum(1 for conv in tenant_conversations 
                            if conv.current_stage == ConversationStage.COMPLETED)
        
        # Conversion rate
        conversion_rate = (completed_sales / total_conversations * 100) if total_conversations > 0 else 0
        
        # Duración promedio
        avg_duration = sum(
            (conv.last_activity - conv.started_at).total_seconds() 
            for conv in tenant_conversations
        ) / total_conversations / 60  # En minutos
        
        # Distribución por etapa
        stage_distribution = {}
        for stage in ConversationStage:
            count = sum(1 for conv in tenant_conversations if conv.current_stage == stage)
            stage_distribution[stage.value] = count
        
        # Productos más discutidos
        all_products = []
        for conv in tenant_conversations:
            all_products.extend([p["name"] for p in conv.discussed_products])
        
        from collections import Counter
        top_products = Counter(all_products).most_common(5)
        
        # Sentimiento promedio
        all_sentiments = []
        for conv in tenant_conversations:
            all_sentiments.extend([s for _, s in conv.sentiment_history])
        
        sentiment_distribution = Counter(all_sentiments)
        
        return {
            "tenant_id": tenant_id,
            "period_days": days,
            "total_conversations": total_conversations,
            "completed_sales": completed_sales,
            "conversion_rate": conversion_rate,
            "average_duration_minutes": avg_duration,
            "stage_distribution": stage_distribution,
            "top_products_discussed": [{"product": p[0], "mentions": p[1]} for p in top_products],
            "sentiment_distribution": dict(sentiment_distribution),
            "health_metrics": {
                "avg_turns_per_conversation": sum(len(conv.turns) for conv in tenant_conversations) / total_conversations,
                "conversations_with_quotes": sum(1 for conv in tenant_conversations if conv.current_quote),
                "objections_handled": sum(len(conv.objections_raised) for conv in tenant_conversations)
            }
        }
    
    def export_conversation_data(self, conversation_id: str) -> Dict[str, Any]:
        """Exporta datos completos de una conversación"""
        
        if conversation_id not in self.active_conversations:
            return {"error": "Conversation not found"}
        
        context = self.active_conversations[conversation_id]
        
        return {
            "conversation_metadata": asdict(context),
            "turns": [asdict(turn) for turn in context.turns],
            "analytics": {
                "health": self._assess_conversation_health(context),
                "summary": context.conversation_summary,
                "stage_progression": [turn.stage.value for turn in context.turns],
                "sentiment_timeline": context.sentiment_history
            }
        }

# Instancia global
conversation_engine = ConversationEngine()

if __name__ == "__main__":
    # Demo de conversación compleja
    print("💬 Orkesta Conversation Engine - Demo Complejo")
    print("=" * 60)
    
    async def demo_complex_conversation():
        engine = ConversationEngine()
        
        # Iniciar conversación para demo
        tenant_id = "demo-tenant"
        customer_id = "customer-vip-001"
        
        conv_id = engine.start_conversation(
            tenant_id, 
            customer_id,
            channel="whatsapp",
            customer_profile={
                "name": "Ana García",
                "company": "TechStart MX",
                "tier": "VIP",
                "purchase_history": ["computers", "software"]
            }
        )
        
        print(f"🚀 Conversación iniciada: {conv_id}")
        
        # Simular flujo complejo de mensajes
        messages = [
            "Hola, necesito cotizar equipos de cómputo para mi empresa",
            "Somos una startup de 25 empleados, necesitamos laptops y monitores",
            "¿Qué opciones tienen en laptops empresariales?",
            "Los HP EliteBook se ven bien, ¿cuánto costarían 25 unidades?",
            "Es un poco caro, ¿tienen opciones más económicas?",
            "¿Y si pedimos solo 20 laptops y 30 monitores?",
            "Me interesa, ¿pueden mandar la cotización formal?"
        ]
        
        for i, message in enumerate(messages, 1):
            print(f"\n--- Turno {i} ---")
            print(f"Cliente: {message}")
            
            response = await engine.process_customer_message(conv_id, message)
            
            print(f"Agente: {response['agent_message']}")
            print(f"Etapa: {response['current_stage']}")
            print(f"Sentimiento: {response['customer_sentiment']}")
            print(f"Salud: {response['conversation_health']['health_level']}")
            
            # Simular delay
            await asyncio.sleep(0.5)
        
        # Mostrar analytics finales
        print(f"\n📊 Analytics de conversación:")
        analytics = engine.get_conversation_analytics(tenant_id)
        print(f"Tasa de conversión: {analytics['conversion_rate']:.1f}%")
        print(f"Duración promedio: {analytics['average_duration_minutes']:.1f} min")
        
        # Exportar datos
        export_data = engine.export_conversation_data(conv_id)
        print(f"\n💾 Datos exportados: {len(export_data['turns'])} turnos")
        
        print("\n✅ Demo de conversación compleja completado")
    
    # Ejecutar demo
    asyncio.run(demo_complex_conversation())