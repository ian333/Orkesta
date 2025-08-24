"""
Decision Engine - Motor de decisiones autónomas con IA
Toma decisiones inteligentes basadas en contexto y verificación
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class DecisionType(Enum):
    APPROVE = "approve"
    REJECT = "reject" 
    REVIEW = "review"
    ESCALATE = "escalate"
    MODIFY = "modify"

@dataclass
class Decision:
    type: DecisionType
    confidence: float
    reasoning: str
    actions: List[Dict[str, Any]]
    conditions: Optional[Dict[str, Any]] = None
    expiry: Optional[datetime] = None

class DecisionEngine:
    """Motor de decisiones autónomas - Cerebro de Orkesta"""
    
    def __init__(self):
        self.decision_rules = DecisionRuleEngine()
        self.context_analyzer = ContextAnalyzer()
        self.risk_calculator = RiskCalculator()
        
    async def make_decision(self, data: Dict[Any, Any], context: Dict[str, Any], verification_result) -> Decision:
        """Toma decisión inteligente basada en todos los factores"""
        
        # Analizar contexto completo
        context_analysis = await self.context_analyzer.analyze(data, context)
        
        # Calcular riesgo
        risk_score = await self.risk_calculator.calculate_risk(data, context, verification_result)
        
        # Aplicar reglas de decisión
        decision = await self.decision_rules.evaluate(data, context_analysis, risk_score, verification_result)
        
        return decision


class DecisionRuleEngine:
    """Motor de reglas de decisión inteligente"""
    
    async def evaluate(self, data, context_analysis, risk_score, verification_result) -> Decision:
        """Evalúa y toma decisión final"""
        
        # CASH FLOW MANAGEMENT - Prioridad #1
        if data.get('type') == 'cash_flow_request':
            return await self._decide_cash_flow(data, context_analysis, risk_score, verification_result)
            
        # WHATSAPP COMMERCE - Prioridad #2  
        elif data.get('channel') == 'whatsapp':
            return await self._decide_whatsapp_commerce(data, context_analysis, risk_score, verification_result)
            
        # PAYMENTS - Prioridad #3
        elif data.get('type') == 'payment':
            return await self._decide_payment(data, context_analysis, risk_score, verification_result)
            
        # Default decision
        else:
            return await self._decide_default(data, context_analysis, risk_score, verification_result)
    
    async def _decide_cash_flow(self, data, context_analysis, risk_score, verification_result) -> Decision:
        """Decisiones para Cash Flow Management"""
        
        amount = data.get('amount', 0)
        business_health = context_analysis.get('business_health_score', 0.5)
        payment_history = context_analysis.get('payment_history_score', 0.5)
        
        # Flujo de efectivo crítico - decisión inmediata
        if amount <= 10000 and business_health > 0.7 and payment_history > 0.6:
            return Decision(
                type=DecisionType.APPROVE,
                confidence=0.9,
                reasoning="Monto bajo, negocio saludable, buen historial de pagos",
                actions=[
                    {"type": "instant_approval", "amount": amount},
                    {"type": "send_whatsapp_confirmation"},
                    {"type": "schedule_payment", "date": datetime.now() + timedelta(days=1)}
                ]
            )
            
        # Monto medio - verificación adicional
        elif amount <= 50000:
            return Decision(
                type=DecisionType.REVIEW,
                confidence=0.75,
                reasoning="Monto medio requiere verificación adicional",
                actions=[
                    {"type": "request_additional_docs"},
                    {"type": "verify_bank_account"},
                    {"type": "schedule_review", "hours": 2}
                ],
                conditions={"max_review_time": "2_hours", "required_docs": ["bank_statement", "business_registration"]}
            )
            
        # Alto riesgo - escalamiento
        else:
            return Decision(
                type=DecisionType.ESCALATE,
                confidence=0.6,
                reasoning=f"Monto alto (${amount:,}), requiere aprobación manual",
                actions=[
                    {"type": "escalate_to_human", "priority": "high"},
                    {"type": "full_verification_required"},
                    {"type": "notify_risk_team"}
                ]
            )
    
    async def _decide_whatsapp_commerce(self, data, context_analysis, risk_score, verification_result) -> Decision:
        """Decisiones para WhatsApp Commerce"""
        
        message_type = data.get('message_type', 'text')
        customer_tier = context_analysis.get('customer_tier', 'new')
        
        # Cliente conocido + compra regular
        if customer_tier in ['gold', 'platinum'] and risk_score < 0.3:
            return Decision(
                type=DecisionType.APPROVE,
                confidence=0.95,
                reasoning="Cliente premium con bajo riesgo",
                actions=[
                    {"type": "process_order_immediately"},
                    {"type": "send_personalized_response"},
                    {"type": "offer_premium_shipping"},
                    {"type": "update_customer_profile"}
                ]
            )
            
        # Nuevo cliente - experiencia guiada
        elif customer_tier == 'new':
            return Decision(
                type=DecisionType.MODIFY,
                confidence=0.8,
                reasoning="Nuevo cliente, ofrecer experiencia guiada",
                actions=[
                    {"type": "send_welcome_flow"},
                    {"type": "request_basic_info"},
                    {"type": "offer_first_purchase_discount"},
                    {"type": "assign_ai_assistant"}
                ]
            )
            
        # Caso estándar
        else:
            return Decision(
                type=DecisionType.APPROVE,
                confidence=0.85,
                reasoning="Interacción estándar de WhatsApp",
                actions=[
                    {"type": "process_standard_flow"},
                    {"type": "verify_intent"},
                    {"type": "provide_options"}
                ]
            )
    
    async def _decide_payment(self, data, context_analysis, risk_score, verification_result) -> Decision:
        """Decisiones para pagos"""
        
        payment_method = data.get('payment_method', 'unknown')
        amount = data.get('amount', 0)
        
        # OXXO payments - siempre requieren verificación adicional
        if payment_method == 'oxxo':
            return Decision(
                type=DecisionType.REVIEW,
                confidence=0.9,
                reasoning="Pago OXXO requiere verificación de voucher",
                actions=[
                    {"type": "generate_oxxo_voucher"},
                    {"type": "send_payment_instructions"},
                    {"type": "monitor_payment_status"},
                    {"type": "auto_reconcile_on_confirmation"}
                ],
                expiry=datetime.now() + timedelta(days=3)  # 3 días para pagar
            )
            
        # Pagos en efectivo - verificación física
        elif payment_method == 'cash':
            return Decision(
                type=DecisionType.ESCALATE,
                confidence=0.7,
                reasoning="Pago en efectivo requiere verificación física",
                actions=[
                    {"type": "schedule_cash_collection"},
                    {"type": "assign_collection_agent"},
                    {"type": "verify_amount_physically"},
                    {"type": "issue_receipt"}
                ]
            )
            
        # Stripe/tarjetas - procesamiento normal
        elif payment_method == 'stripe':
            if risk_score < 0.4:
                return Decision(
                    type=DecisionType.APPROVE,
                    confidence=0.9,
                    reasoning="Pago con tarjeta de bajo riesgo",
                    actions=[
                        {"type": "process_stripe_payment"},
                        {"type": "send_confirmation"},
                        {"type": "update_accounting"}
                    ]
                )
            else:
                return Decision(
                    type=DecisionType.REVIEW,
                    confidence=0.6,
                    reasoning="Pago con tarjeta de alto riesgo",
                    actions=[
                        {"type": "additional_card_verification"},
                        {"type": "check_fraud_indicators"},
                        {"type": "manual_approval_if_needed"}
                    ]
                )
        
        # Método de pago desconocido
        else:
            return Decision(
                type=DecisionType.REJECT,
                confidence=0.95,
                reasoning=f"Método de pago no soportado: {payment_method}",
                actions=[
                    {"type": "send_supported_methods_list"},
                    {"type": "log_unsupported_request"}
                ]
            )
    
    async def _decide_default(self, data, context_analysis, risk_score, verification_result) -> Decision:
        """Decisión por defecto para casos no específicos"""
        
        if risk_score < 0.3 and verification_result.confidence > 0.8:
            return Decision(
                type=DecisionType.APPROVE,
                confidence=0.8,
                reasoning="Bajo riesgo, alta confianza en verificación",
                actions=[{"type": "process_standard"}]
            )
        elif risk_score > 0.7:
            return Decision(
                type=DecisionType.REJECT,
                confidence=0.9,
                reasoning="Alto riesgo detectado",
                actions=[{"type": "log_high_risk_attempt"}]
            )
        else:
            return Decision(
                type=DecisionType.REVIEW,
                confidence=0.6,
                reasoning="Requiere revisión manual",
                actions=[{"type": "queue_for_review"}]
            )


class ContextAnalyzer:
    """Analiza el contexto completo de la decisión"""
    
    async def analyze(self, data, context) -> Dict[str, Any]:
        """Análisis completo del contexto"""
        
        analysis = {}
        
        # Análisis del negocio
        analysis['business_health_score'] = await self._analyze_business_health(context)
        
        # Análisis del cliente
        analysis['customer_tier'] = await self._analyze_customer_tier(context)
        analysis['payment_history_score'] = await self._analyze_payment_history(context)
        
        # Análisis del mercado
        analysis['market_conditions'] = await self._analyze_market_conditions()
        
        # Análisis temporal
        analysis['time_factors'] = await self._analyze_time_factors()
        
        return analysis
    
    async def _analyze_business_health(self, context) -> float:
        """Analiza la salud del negocio"""
        # Factores: flujo de caja, ventas recientes, edad del negocio
        cash_flow_score = context.get('recent_cash_flow', 0) / 100000  # Normalizado
        sales_trend = context.get('sales_trend', 'stable')
        business_age = context.get('business_age_months', 0)
        
        score = 0.3  # Base
        score += min(cash_flow_score, 0.4)  # Máximo 0.4
        score += 0.2 if sales_trend == 'growing' else 0.1 if sales_trend == 'stable' else 0
        score += min(business_age / 24, 0.1)  # Máximo 0.1 (2 años)
        
        return min(score, 1.0)
    
    async def _analyze_customer_tier(self, context) -> str:
        """Determina el tier del cliente"""
        total_transactions = context.get('total_transactions', 0)
        total_volume = context.get('total_volume', 0)
        days_as_customer = context.get('customer_age_days', 0)
        
        if total_volume > 500000 and total_transactions > 50:  # 500k+ MXN, 50+ transacciones
            return 'platinum'
        elif total_volume > 100000 and total_transactions > 20:  # 100k+ MXN, 20+ transacciones  
            return 'gold'
        elif total_volume > 20000 and total_transactions > 5:   # 20k+ MXN, 5+ transacciones
            return 'silver'
        elif days_as_customer > 30:
            return 'bronze'
        else:
            return 'new'
    
    async def _analyze_payment_history(self, context) -> float:
        """Analiza el historial de pagos"""
        on_time_payments = context.get('on_time_payments', 0)
        total_payments = context.get('total_payments', 0)
        
        if total_payments == 0:
            return 0.5  # Neutral para nuevos clientes
            
        return min(on_time_payments / total_payments, 1.0)
    
    async def _analyze_market_conditions(self) -> Dict[str, Any]:
        """Analiza condiciones del mercado"""
        current_hour = datetime.now().hour
        
        return {
            'is_business_hours': 6 <= current_hour <= 22,
            'is_peak_hours': 9 <= current_hour <= 18,
            'day_of_week': datetime.now().weekday(),
            'is_weekend': datetime.now().weekday() >= 5
        }
    
    async def _analyze_time_factors(self) -> Dict[str, Any]:
        """Analiza factores temporales"""
        now = datetime.now()
        
        return {
            'current_hour': now.hour,
            'is_end_of_month': now.day >= 25,
            'is_beginning_of_month': now.day <= 5,
            'quarter': (now.month - 1) // 3 + 1
        }


class RiskCalculator:
    """Calculadora de riesgo inteligente"""
    
    async def calculate_risk(self, data, context, verification_result) -> float:
        """Calcula score de riesgo (0.0 = sin riesgo, 1.0 = máximo riesgo)"""
        
        risk_factors = []
        
        # Factor de verificación
        verification_risk = 1.0 - verification_result.confidence
        risk_factors.append(('verification', verification_risk, 0.3))
        
        # Factor de monto
        amount = data.get('amount', 0)
        amount_risk = min(amount / 100000, 1.0)  # Normalizado a 100k
        risk_factors.append(('amount', amount_risk, 0.25))
        
        # Factor de cliente
        customer_age = context.get('customer_age_days', 0)
        customer_risk = max(0, (30 - customer_age) / 30)  # Más riesgo = más nuevo
        risk_factors.append(('customer_age', customer_risk, 0.2))
        
        # Factor de ubicación
        location_risk = await self._calculate_location_risk(data, context)
        risk_factors.append(('location', location_risk, 0.15))
        
        # Factor temporal
        temporal_risk = await self._calculate_temporal_risk()
        risk_factors.append(('temporal', temporal_risk, 0.1))
        
        # Calcular riesgo ponderado
        total_risk = sum(risk * weight for _, risk, weight in risk_factors)
        
        return min(total_risk, 1.0)
    
    async def _calculate_location_risk(self, data, context) -> float:
        """Calcula riesgo basado en ubicación"""
        # Implementar análisis geográfico real
        user_location = data.get('location', {})
        
        # Por ahora, simulamos
        if user_location.get('country') != 'MX':
            return 0.8  # Alto riesgo fuera de México
            
        return 0.1  # Bajo riesgo en México
    
    async def _calculate_temporal_risk(self) -> float:
        """Calcula riesgo temporal"""
        current_hour = datetime.now().hour
        
        # Horarios fuera de lo normal = mayor riesgo
        if current_hour < 6 or current_hour > 22:
            return 0.4
            
        return 0.05  # Riesgo muy bajo en horarios normales