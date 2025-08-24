"""
Cash Flow Management - Gestión inteligente de flujo de efectivo
PROBLEMA CRÍTICO #1 en LATAM: Gestión de efectivo en tiempo real
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class CashFlowRequestType(Enum):
    ADVANCE_REQUEST = "advance_request"        # Solicitud de adelanto
    PAYMENT_SCHEDULE = "payment_schedule"     # Programación de pago
    CASH_POSITION = "cash_position"           # Consulta de posición
    RECONCILIATION = "reconciliation"         # Conciliación

@dataclass
class CashFlowRequest:
    request_type: CashFlowRequestType
    business_id: str
    amount: float
    currency: str = "MXN"
    urgency: str = "normal"  # critical, high, normal, low
    requested_date: Optional[datetime] = None
    collateral: Optional[Dict] = None
    purpose: Optional[str] = None

class CashFlowManager:
    """Gestor inteligente de flujo de efectivo - CORE DE LATAM"""
    
    def __init__(self, core_engine):
        self.core = core_engine
        self.cash_analyzer = CashFlowAnalyzer()
        self.advance_processor = AdvanceProcessor()
        self.reconciliation_engine = ReconciliationEngine()
        
    async def handle_request(self, data: Dict[Any, Any], context: Dict[str, Any]):
        """Maneja todas las solicitudes de cash flow"""
        
        # Parsear request
        cash_request = self._parse_request(data)
        
        # Verificación IA obligatoria
        enhanced_context = await self._enhance_context(cash_request, context)
        verification_result = await self.core.verification.verify_input(
            data=data,
            context=enhanced_context
        )
        
        if not verification_result.is_valid:
            return {
                "status": "rejected",
                "reason": verification_result.reason,
                "request_id": context.get("request_id")
            }
        
        # Procesar según tipo
        if cash_request.request_type == CashFlowRequestType.ADVANCE_REQUEST:
            return await self._handle_advance_request(cash_request, enhanced_context)
        elif cash_request.request_type == CashFlowRequestType.PAYMENT_SCHEDULE:
            return await self._handle_payment_schedule(cash_request, enhanced_context)
        elif cash_request.request_type == CashFlowRequestType.CASH_POSITION:
            return await self._handle_cash_position(cash_request, enhanced_context)
        elif cash_request.request_type == CashFlowRequestType.RECONCILIATION:
            return await self._handle_reconciliation(cash_request, enhanced_context)
    
    async def _handle_advance_request(self, request: CashFlowRequest, context: Dict):
        """Maneja solicitudes de adelanto de efectivo"""
        
        # Análisis IA de capacidad de pago
        payment_capacity = await self.cash_analyzer.analyze_payment_capacity(
            request.business_id, 
            request.amount,
            context
        )
        
        # Decisión IA
        decision_data = {
            "type": "cash_flow_request",
            "amount": request.amount,
            "business_id": request.business_id,
            "urgency": request.urgency,
            "purpose": request.purpose
        }
        
        decision = await self.core.decisions.make_decision(
            decision_data, 
            {**context, "payment_capacity": payment_capacity},
            context.get("verification_result")
        )
        
        if decision.type.value == "approve":
            # Procesar adelanto
            advance_result = await self.advance_processor.process_advance(request, context)
            
            return {
                "status": "approved",
                "advance_amount": request.amount,
                "disbursement_date": advance_result.get("disbursement_date"),
                "repayment_schedule": advance_result.get("repayment_schedule"),
                "terms": advance_result.get("terms"),
                "request_id": context.get("request_id")
            }
        else:
            return {
                "status": decision.type.value,
                "reason": decision.reasoning,
                "alternative_options": await self._generate_alternatives(request, context),
                "request_id": context.get("request_id")
            }
    
    async def _handle_payment_schedule(self, request: CashFlowRequest, context: Dict):
        """Maneja programación de pagos"""
        
        # Analizar flujo de caja proyectado
        cash_projection = await self.cash_analyzer.project_cash_flow(
            request.business_id,
            days_ahead=30
        )
        
        # Optimizar fechas de pago
        optimal_dates = await self.cash_analyzer.optimize_payment_dates(
            request.amount,
            cash_projection,
            context
        )
        
        return {
            "status": "scheduled",
            "payment_dates": optimal_dates,
            "total_amount": request.amount,
            "projected_cash_impact": cash_projection,
            "recommendations": await self._generate_payment_recommendations(request, context),
            "request_id": context.get("request_id")
        }
    
    async def _handle_cash_position(self, request: CashFlowRequest, context: Dict):
        """Consulta posición de efectivo en tiempo real"""
        
        position = await self.cash_analyzer.get_current_position(request.business_id)
        projections = await self.cash_analyzer.project_cash_flow(request.business_id, 7)
        
        return {
            "status": "success",
            "current_position": position,
            "weekly_projection": projections,
            "liquidity_score": await self.cash_analyzer.calculate_liquidity_score(request.business_id),
            "alerts": await self.cash_analyzer.check_liquidity_alerts(request.business_id),
            "request_id": context.get("request_id")
        }
    
    async def _handle_reconciliation(self, request: CashFlowRequest, context: Dict):
        """Maneja conciliación de efectivo"""
        
        reconciliation = await self.reconciliation_engine.reconcile_cash_flow(
            request.business_id,
            context.get("period", "daily")
        )
        
        return {
            "status": "reconciled",
            "reconciliation_report": reconciliation,
            "discrepancies": reconciliation.get("discrepancies", []),
            "actions_required": reconciliation.get("actions_required", []),
            "request_id": context.get("request_id")
        }
    
    async def _enhance_context(self, request: CashFlowRequest, context: Dict) -> Dict:
        """Enriquece contexto con datos financieros"""
        
        enhanced = context.copy()
        
        # Datos financieros históricos
        financial_data = await self.cash_analyzer.get_financial_history(request.business_id)
        enhanced.update(financial_data)
        
        # Score de riesgo crediticio
        credit_score = await self.cash_analyzer.calculate_credit_score(request.business_id)
        enhanced["credit_score"] = credit_score
        
        # Análisis de estacionalidad
        seasonality = await self.cash_analyzer.analyze_seasonality(request.business_id)
        enhanced["seasonality"] = seasonality
        
        return enhanced
    
    def _parse_request(self, data: Dict) -> CashFlowRequest:
        """Parsea datos del request"""
        
        return CashFlowRequest(
            request_type=CashFlowRequestType(data.get("request_type", "advance_request")),
            business_id=data["business_id"],
            amount=float(data["amount"]),
            currency=data.get("currency", "MXN"),
            urgency=data.get("urgency", "normal"),
            requested_date=data.get("requested_date"),
            collateral=data.get("collateral"),
            purpose=data.get("purpose")
        )
    
    async def _generate_alternatives(self, request: CashFlowRequest, context: Dict) -> List[Dict]:
        """Genera alternativas cuando no se aprueba el adelanto"""
        
        alternatives = []
        
        # Adelanto menor
        if request.amount > 10000:
            alternatives.append({
                "type": "reduced_amount",
                "amount": min(request.amount * 0.5, 10000),
                "description": "Adelanto por menor monto con aprobación inmediata"
            })
        
        # Pago diferido
        alternatives.append({
            "type": "deferred_payment", 
            "delay_days": 7,
            "description": "Programar pago en 7 días con análisis adicional"
        })
        
        # Garantía adicional
        alternatives.append({
            "type": "additional_collateral",
            "requirements": ["bank_statements", "inventory_valuation"],
            "description": "Proporcionar garantía adicional para aprobación"
        })
        
        return alternatives
    
    async def _generate_payment_recommendations(self, request: CashFlowRequest, context: Dict) -> List[str]:
        """Genera recomendaciones de pago"""
        
        recommendations = []
        
        # Basado en flujo de caja
        if context.get("cash_flow_trend") == "declining":
            recommendations.append("Considerar pagos parciales para mantener liquidez")
            
        # Basado en estacionalidad
        if context.get("seasonality", {}).get("current_period") == "low_season":
            recommendations.append("Diferir pagos no críticos hasta temporada alta")
            
        # Basado en oportunidades
        if context.get("investment_opportunities"):
            recommendations.append("Evaluar retener efectivo para oportunidades de inversión")
            
        return recommendations


class CashFlowAnalyzer:
    """Analizador inteligente de flujo de efectivo"""
    
    async def analyze_payment_capacity(self, business_id: str, amount: float, context: Dict) -> Dict:
        """Analiza capacidad de pago con IA"""
        
        # Obtener datos históricos
        historical_data = await self._get_historical_cash_flow(business_id)
        
        # Calcular métricas clave
        avg_monthly_flow = sum(historical_data.get("monthly_flows", [])) / max(len(historical_data.get("monthly_flows", [1])), 1)
        
        debt_to_flow_ratio = context.get("current_debt", 0) / max(avg_monthly_flow, 1)
        
        capacity_score = self._calculate_capacity_score(
            amount, 
            avg_monthly_flow, 
            debt_to_flow_ratio,
            historical_data
        )
        
        return {
            "capacity_score": capacity_score,
            "avg_monthly_flow": avg_monthly_flow,
            "debt_to_flow_ratio": debt_to_flow_ratio,
            "recommended_max_advance": min(avg_monthly_flow * 0.3, 50000),  # 30% del flujo o 50k
            "risk_factors": self._identify_risk_factors(historical_data, context)
        }
    
    async def project_cash_flow(self, business_id: str, days_ahead: int) -> Dict:
        """Proyecta flujo de efectivo usando ML"""
        
        # En producción, usaría modelos ML reales
        # Por ahora, simulamos proyección
        
        base_flow = await self._get_current_flow_rate(business_id)
        seasonality_factor = await self._get_seasonality_factor(business_id)
        
        projections = []
        for day in range(1, days_ahead + 1):
            date = datetime.now() + timedelta(days=day)
            
            # Simulación simple de proyección
            daily_flow = base_flow * seasonality_factor * (0.9 + 0.2 * (day % 7) / 7)  # Variación semanal
            
            projections.append({
                "date": date.isoformat(),
                "projected_inflow": daily_flow * 1.1,
                "projected_outflow": daily_flow * 0.9,
                "net_flow": daily_flow * 0.2,
                "confidence": 0.85 - (day * 0.01)  # Menos confianza a futuro
            })
        
        return {
            "projections": projections,
            "total_net_flow": sum(p["net_flow"] for p in projections),
            "confidence_avg": sum(p["confidence"] for p in projections) / len(projections)
        }
    
    async def optimize_payment_dates(self, amount: float, cash_projection: Dict, context: Dict) -> List[Dict]:
        """Optimiza fechas de pago para maximizar flujo de caja"""
        
        projections = cash_projection.get("projections", [])
        
        optimal_dates = []
        remaining_amount = amount
        
        for projection in projections:
            if remaining_amount <= 0:
                break
                
            available_cash = projection["net_flow"]
            
            if available_cash > 0:
                payment_amount = min(remaining_amount, available_cash * 0.8)  # 80% del flujo disponible
                
                if payment_amount > 100:  # Mínimo $100 MXN por pago
                    optimal_dates.append({
                        "date": projection["date"],
                        "amount": payment_amount,
                        "confidence": projection["confidence"]
                    })
                    
                    remaining_amount -= payment_amount
        
        return optimal_dates
    
    async def get_current_position(self, business_id: str) -> Dict:
        """Obtiene posición actual de efectivo"""
        
        # En producción, conectaría con APIs bancarias reales
        return {
            "cash_on_hand": 25000.00,
            "bank_balances": {
                "checking": 45000.00,
                "savings": 120000.00
            },
            "pending_receivables": 78000.00,
            "pending_payables": 32000.00,
            "net_position": 236000.00,
            "last_updated": datetime.now().isoformat()
        }
    
    async def calculate_liquidity_score(self, business_id: str) -> float:
        """Calcula score de liquidez (0.0 - 1.0)"""
        
        position = await self.get_current_position(business_id)
        
        # Factores de liquidez
        cash_ratio = position["net_position"] / max(position["pending_payables"], 1)
        receivables_ratio = position["pending_receivables"] / max(position["pending_payables"], 1)
        
        liquidity_score = min((cash_ratio * 0.6 + receivables_ratio * 0.4) / 2, 1.0)
        
        return liquidity_score
    
    async def check_liquidity_alerts(self, business_id: str) -> List[Dict]:
        """Verifica alertas de liquidez"""
        
        alerts = []
        position = await self.get_current_position(business_id)
        liquidity_score = await self.calculate_liquidity_score(business_id)
        
        if liquidity_score < 0.3:
            alerts.append({
                "level": "critical",
                "message": "Liquidez crítica - Evaluar opciones de financiamiento",
                "action_required": True
            })
        elif liquidity_score < 0.5:
            alerts.append({
                "level": "warning", 
                "message": "Liquidez baja - Monitorear de cerca",
                "action_required": False
            })
        
        if position["pending_payables"] > position["net_position"]:
            alerts.append({
                "level": "warning",
                "message": "Cuentas por pagar exceden posición neta",
                "action_required": True
            })
        
        return alerts
    
    async def calculate_credit_score(self, business_id: str) -> float:
        """Calcula score crediticio del negocio"""
        
        # En producción, integraría con bureaus de crédito
        # Simulación basada en datos internos
        
        payment_history = await self._get_payment_history(business_id)
        financial_health = await self._assess_financial_health(business_id)
        
        # Componentes del score
        payment_score = payment_history.get("on_time_percentage", 0.5)
        stability_score = financial_health.get("stability_score", 0.5)
        growth_score = financial_health.get("growth_score", 0.5)
        
        credit_score = (payment_score * 0.5 + stability_score * 0.3 + growth_score * 0.2)
        
        return min(credit_score, 1.0)
    
    async def analyze_seasonality(self, business_id: str) -> Dict:
        """Analiza patrones estacionales del negocio"""
        
        # En producción, analizaría datos históricos reales
        
        current_month = datetime.now().month
        
        # Simulación de estacionalidad típica retail
        seasonal_patterns = {
            12: 1.4,  # Diciembre - temporada alta
            11: 1.2,  # Noviembre
            1: 0.8,   # Enero - temporada baja
            2: 0.7,   # Febrero
            3: 0.9,   # Marzo
            4: 1.0,   # Abril - normal
            5: 1.1,   # Mayo
            6: 0.9,   # Junio
            7: 0.8,   # Julio
            8: 0.9,   # Agosto
            9: 1.1,   # Septiembre
            10: 1.2   # Octubre
        }
        
        current_factor = seasonal_patterns.get(current_month, 1.0)
        
        return {
            "current_period": "high_season" if current_factor > 1.2 else "low_season" if current_factor < 0.8 else "normal_season",
            "seasonal_factor": current_factor,
            "next_peak_month": 12 if current_month < 12 else 12,
            "next_low_month": 2 if current_month not in [1, 2] else 2
        }
    
    # Métodos auxiliares privados
    
    def _calculate_capacity_score(self, requested_amount, avg_monthly_flow, debt_ratio, historical_data):
        """Calcula score de capacidad de pago"""
        
        # Ratio de cantidad solicitada vs flujo promedio
        amount_ratio = requested_amount / max(avg_monthly_flow, 1)
        
        # Score base
        if amount_ratio < 0.2:  # Menos del 20% del flujo mensual
            amount_score = 1.0
        elif amount_ratio < 0.5:  # Menos del 50%
            amount_score = 0.8
        elif amount_ratio < 1.0:  # Menos del 100%
            amount_score = 0.6
        else:
            amount_score = 0.3
        
        # Penalizar por deuda existente
        debt_penalty = max(0, debt_ratio - 0.5) * 0.5  # Penalizar si deuda > 50% del flujo
        
        final_score = max(0, amount_score - debt_penalty)
        
        return final_score
    
    def _identify_risk_factors(self, historical_data, context):
        """Identifica factores de riesgo"""
        
        risk_factors = []
        
        # Volatilidad del flujo
        flows = historical_data.get("monthly_flows", [])
        if len(flows) > 1:
            avg_flow = sum(flows) / len(flows)
            volatility = sum(abs(f - avg_flow) for f in flows) / len(flows) / avg_flow
            
            if volatility > 0.3:  # 30% de volatilidad
                risk_factors.append("high_cash_flow_volatility")
        
        # Tendencia negativa
        if len(flows) >= 3 and flows[-1] < flows[-3] * 0.8:
            risk_factors.append("declining_cash_flow_trend")
        
        # Deuda alta
        debt_ratio = context.get("current_debt", 0) / max(sum(flows)/len(flows) if flows else 1, 1)
        if debt_ratio > 0.8:
            risk_factors.append("high_debt_to_flow_ratio")
        
        return risk_factors
    
    async def _get_historical_cash_flow(self, business_id):
        """Obtiene datos históricos de flujo de caja"""
        # Simulación - en producción vendría de la base de datos
        return {
            "monthly_flows": [25000, 30000, 28000, 35000, 32000, 29000],
            "average_flow": 29833.33,
            "trend": "stable"
        }
    
    async def _get_current_flow_rate(self, business_id):
        """Obtiene tasa actual de flujo"""
        return 1000.0  # $1000 MXN diarios promedio
    
    async def _get_seasonality_factor(self, business_id):
        """Obtiene factor de estacionalidad actual"""
        return 1.0  # Factor neutral
    
    async def _get_payment_history(self, business_id):
        """Obtiene historial de pagos"""
        return {
            "total_payments": 24,
            "on_time_payments": 22,
            "on_time_percentage": 0.92
        }
    
    async def _assess_financial_health(self, business_id):
        """Evalúa salud financiera"""
        return {
            "stability_score": 0.85,
            "growth_score": 0.75
        }


class AdvanceProcessor:
    """Procesador de adelantos de efectivo"""
    
    async def process_advance(self, request: CashFlowRequest, context: Dict) -> Dict:
        """Procesa un adelanto aprobado"""
        
        # Generar términos del adelanto
        terms = self._generate_advance_terms(request, context)
        
        # Programar desembolso
        disbursement_date = self._calculate_disbursement_date(request, context)
        
        # Crear calendario de pagos
        repayment_schedule = self._create_repayment_schedule(request, terms, context)
        
        # En producción, aquí se haría la transferencia real
        # Por ahora, solo simulamos
        
        return {
            "disbursement_date": disbursement_date.isoformat(),
            "repayment_schedule": repayment_schedule,
            "terms": terms,
            "reference_number": f"ADV-{datetime.now().strftime('%Y%m%d')}-{hash(request.business_id) % 10000:04d}"
        }
    
    def _generate_advance_terms(self, request: CashFlowRequest, context: Dict) -> Dict:
        """Genera términos del adelanto"""
        
        credit_score = context.get("credit_score", 0.5)
        
        # Tasa basada en score crediticio
        base_rate = 0.12  # 12% anual base
        rate_adjustment = (1 - credit_score) * 0.08  # Hasta 8% adicional
        annual_rate = base_rate + rate_adjustment
        
        # Plazo basado en monto
        if request.amount <= 10000:
            term_days = 30
        elif request.amount <= 50000:
            term_days = 60
        else:
            term_days = 90
        
        return {
            "principal": request.amount,
            "annual_rate": annual_rate,
            "term_days": term_days,
            "fees": {
                "origination_fee": request.amount * 0.02,  # 2%
                "processing_fee": 500.00  # Fijo $500 MXN
            },
            "total_cost": self._calculate_total_cost(request.amount, annual_rate, term_days)
        }
    
    def _calculate_disbursement_date(self, request: CashFlowRequest, context: Dict) -> datetime:
        """Calcula fecha de desembolso"""
        
        if request.urgency == "critical":
            return datetime.now() + timedelta(hours=2)  # 2 horas
        elif request.urgency == "high":
            return datetime.now() + timedelta(hours=24)  # 24 horas
        else:
            return datetime.now() + timedelta(days=2)  # 2 días laborales
    
    def _create_repayment_schedule(self, request: CashFlowRequest, terms: Dict, context: Dict) -> List[Dict]:
        """Crea calendario de pagos"""
        
        principal = terms["principal"]
        term_days = terms["term_days"]
        total_cost = terms["total_cost"]
        
        # Pagos semanales
        num_payments = term_days // 7
        payment_amount = total_cost / num_payments
        
        schedule = []
        current_date = datetime.now() + timedelta(days=7)  # Primer pago en una semana
        
        for i in range(num_payments):
            schedule.append({
                "payment_number": i + 1,
                "due_date": current_date.isoformat(),
                "amount": payment_amount,
                "principal_portion": principal / num_payments,
                "interest_portion": payment_amount - (principal / num_payments)
            })
            
            current_date += timedelta(days=7)
        
        return schedule
    
    def _calculate_total_cost(self, principal: float, annual_rate: float, term_days: int) -> float:
        """Calcula costo total del adelanto"""
        
        # Interés simple para adelantos a corto plazo
        interest = principal * annual_rate * (term_days / 365)
        
        return principal + interest


class ReconciliationEngine:
    """Motor de conciliación de efectivo"""
    
    async def reconcile_cash_flow(self, business_id: str, period: str = "daily") -> Dict:
        """Reconcilia flujo de efectivo por período"""
        
        # Obtener transacciones del período
        transactions = await self._get_period_transactions(business_id, period)
        
        # Obtener saldos bancarios
        bank_balances = await self._get_bank_balances(business_id)
        
        # Calcular posición teórica vs real
        theoretical_position = self._calculate_theoretical_position(transactions)
        actual_position = sum(bank_balances.values())
        
        discrepancy = actual_position - theoretical_position
        
        # Identificar discrepancias
        discrepancies = await self._identify_discrepancies(
            theoretical_position, 
            actual_position, 
            transactions,
            bank_balances
        )
        
        return {
            "period": period,
            "theoretical_position": theoretical_position,
            "actual_position": actual_position,
            "discrepancy": discrepancy,
            "discrepancies": discrepancies,
            "reconciliation_items": await self._suggest_reconciliation_items(discrepancies),
            "actions_required": await self._suggest_actions(discrepancies)
        }
    
    async def _get_period_transactions(self, business_id: str, period: str) -> List[Dict]:
        """Obtiene transacciones del período"""
        # En producción, consultaría la base de datos real
        return [
            {"type": "inflow", "amount": 15000, "source": "sales"},
            {"type": "inflow", "amount": 8000, "source": "receivables"},
            {"type": "outflow", "amount": 5000, "source": "suppliers"},
            {"type": "outflow", "amount": 3000, "source": "payroll"}
        ]
    
    async def _get_bank_balances(self, business_id: str) -> Dict[str, float]:
        """Obtiene saldos bancarios actuales"""
        # En producción, consultaría APIs bancarias
        return {
            "bank_account_1": 45000.00,
            "bank_account_2": 12000.00,
            "petty_cash": 2000.00
        }
    
    def _calculate_theoretical_position(self, transactions: List[Dict]) -> float:
        """Calcula posición teórica basada en transacciones"""
        
        inflows = sum(t["amount"] for t in transactions if t["type"] == "inflow")
        outflows = sum(t["amount"] for t in transactions if t["type"] == "outflow")
        
        # Agregar saldo inicial (simulado)
        initial_balance = 44000.00
        
        return initial_balance + inflows - outflows
    
    async def _identify_discrepancies(self, theoretical, actual, transactions, balances) -> List[Dict]:
        """Identifica discrepancias específicas"""
        
        discrepancies = []
        
        total_discrepancy = actual - theoretical
        
        if abs(total_discrepancy) > 100:  # Discrepancia > $100 MXN
            discrepancies.append({
                "type": "position_discrepancy",
                "amount": total_discrepancy,
                "description": f"Diferencia entre posición teórica y real: ${total_discrepancy:,.2f}",
                "severity": "high" if abs(total_discrepancy) > 1000 else "medium"
            })
        
        # Verificar transacciones pendientes
        pending_items = await self._check_pending_items()
        for item in pending_items:
            discrepancies.append({
                "type": "pending_transaction",
                "amount": item["amount"],
                "description": f"Transacción pendiente: {item['description']}",
                "severity": "medium"
            })
        
        return discrepancies
    
    async def _check_pending_items(self) -> List[Dict]:
        """Verifica items pendientes"""
        # Simulación de items pendientes
        return [
            {"amount": 2500, "description": "Cheque pendiente de cobro"},
            {"amount": -800, "description": "Cargo bancario no registrado"}
        ]
    
    async def _suggest_reconciliation_items(self, discrepancies: List[Dict]) -> List[Dict]:
        """Sugiere items de conciliación"""
        
        suggestions = []
        
        for discrepancy in discrepancies:
            if discrepancy["type"] == "pending_transaction":
                suggestions.append({
                    "action": "register_transaction",
                    "amount": discrepancy["amount"],
                    "description": "Registrar transacción pendiente en sistema"
                })
            elif discrepancy["type"] == "position_discrepancy":
                suggestions.append({
                    "action": "investigate_discrepancy",
                    "amount": discrepancy["amount"],
                    "description": "Investigar origen de la discrepancia"
                })
        
        return suggestions
    
    async def _suggest_actions(self, discrepancies: List[Dict]) -> List[str]:
        """Sugiere acciones correctivas"""
        
        actions = []
        
        high_severity_count = sum(1 for d in discrepancies if d.get("severity") == "high")
        
        if high_severity_count > 0:
            actions.append("Revisar inmediatamente las discrepancias de alta severidad")
            
        if len(discrepancies) > 3:
            actions.append("Implementar controles adicionales de conciliación diaria")
            
        actions.append("Actualizar registros contables con items identificados")
        
        return actions