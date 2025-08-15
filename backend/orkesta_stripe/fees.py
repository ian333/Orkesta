"""
💰 Fee Calculator para OCO
=========================

Calcula fees de Stripe Connect, application fees y costos efectivos.
Soporte completo para México con todos los métodos de pago.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import logging

from .types import (
    PaymentMethod, ChargesMode, FeePolicy, 
    STRIPE_MX_FEES, StripeConnectFees
)

logger = logging.getLogger(__name__)

class FeeCalculator:
    """Calculadora de fees para Stripe Connect"""
    
    def __init__(self):
        self.stripe_fees = STRIPE_MX_FEES
    
    def calculate_payment_fees(self, amount: float, method: PaymentMethod,
                             is_international: bool = False,
                             has_currency_conversion: bool = False) -> Dict[str, float]:
        """
        Calcula fees de pago según método y condiciones.
        
        Returns:
            {
                "amount": 1000.0,
                "method": "card",
                "stripe_fee": 39.0,  # 3.6% + $3
                "stripe_fee_pct": 3.6,
                "stripe_fee_fixed": 3.0,
                "net_amount": 961.0,
                "effective_rate": 3.9
            }
        """
        
        try:
            stripe_fee = self.stripe_fees.calculate_payment_fee(
                amount, method, is_international, has_currency_conversion
            )
            
            net_amount = amount - stripe_fee
            effective_rate = (stripe_fee / amount) * 100 if amount > 0 else 0
            
            # Obtener componentes del fee
            if method == PaymentMethod.CARD:
                base_pct = self.stripe_fees.card_domestic_pct
                base_fixed = self.stripe_fees.card_domestic_fixed
                
                if is_international:
                    base_pct = self.stripe_fees.card_international_pct
                if has_currency_conversion:
                    base_pct += self.stripe_fees.currency_conversion_pct
                    
            elif method == PaymentMethod.OXXO:
                base_pct = self.stripe_fees.oxxo_pct
                base_fixed = self.stripe_fees.oxxo_fixed
                
            elif method == PaymentMethod.SPEI:
                base_pct = self.stripe_fees.spei_pct
                base_fixed = self.stripe_fees.spei_fixed
            
            return {
                "amount": amount,
                "method": method.value,
                "stripe_fee": stripe_fee,
                "stripe_fee_pct": base_pct,
                "stripe_fee_fixed": base_fixed,
                "net_amount": net_amount,
                "effective_rate": effective_rate,
                "is_international": is_international,
                "has_currency_conversion": has_currency_conversion
            }
            
        except Exception as e:
            logger.error(f"Error calculating payment fees: {e}")
            raise
    
    def calculate_application_fee(self, amount: float, fee_policy: FeePolicy) -> Dict[str, Any]:
        """
        Calcula application fee según política.
        
        Returns:
            {
                "amount": 1000.0,
                "app_fee_amount": 8.0,    # $8 MXN
                "app_fee_cents": 800,     # 800 centavos
                "policy": {...},
                "breakdown": {...}
            }
        """
        
        app_fee_amount = fee_policy.calculate(amount) / 100  # Convertir de centavos
        
        # Breakdown del cálculo
        percentage_component = amount * fee_policy.application_fee_pct / 100
        fixed_component = fee_policy.application_fee_fixed
        
        before_limits = percentage_component + fixed_component
        
        # Aplicar límites
        after_min = max(before_limits, fee_policy.min_fee)
        final_amount = min(after_min, fee_policy.max_fee) if fee_policy.max_fee else after_min
        
        return {
            "amount": amount,
            "app_fee_amount": app_fee_amount,
            "app_fee_cents": int(app_fee_amount * 100),
            "policy": {
                "percentage": fee_policy.application_fee_pct,
                "fixed": fee_policy.application_fee_fixed,
                "min_fee": fee_policy.min_fee,
                "max_fee": fee_policy.max_fee
            },
            "breakdown": {
                "percentage_component": percentage_component,
                "fixed_component": fixed_component,
                "before_limits": before_limits,
                "after_min_limit": after_min,
                "final_amount": final_amount,
                "was_min_applied": before_limits < fee_policy.min_fee,
                "was_max_applied": fee_policy.max_fee and after_min > fee_policy.max_fee
            }
        }
    
    def calculate_connect_costs(self, active_accounts: int, 
                              monthly_payout_volume: float,
                              monthly_payouts: int) -> Dict[str, float]:
        """
        Calcula costos mensuales de Stripe Connect.
        
        Returns:
            {
                "active_accounts_fee": 105.0,      # 3 cuentas * $35
                "payout_percentage_fee": 62.5,     # $25k * 0.25%
                "payout_fixed_fee": 48.0,          # 4 payouts * $12
                "total_monthly_cost": 215.5,
                "cost_per_account": 71.83,
                "cost_per_payout": 53.88
            }
        """
        
        costs = self.stripe_fees.calculate_connect_monthly_cost(
            active_accounts, monthly_payout_volume, monthly_payouts
        )
        
        # Agregar métricas por unidad
        costs["cost_per_account"] = costs["total_monthly_cost"] / active_accounts if active_accounts > 0 else 0
        costs["cost_per_payout"] = costs["total_monthly_cost"] / monthly_payouts if monthly_payouts > 0 else 0
        
        return costs
    
    def analyze_charges_mode_economics(self, amount: float, payment_method: PaymentMethod,
                                     fee_policy: FeePolicy) -> Dict[str, Dict[str, float]]:
        """
        Analiza la economía de los 3 modos de charges para una transacción.
        
        Returns dict con análisis por modo: direct, destination, separate
        """
        
        # Calcular fees base
        payment_fees = self.calculate_payment_fees(amount, payment_method)
        app_fee_calc = self.calculate_application_fee(amount, fee_policy)
        
        stripe_fee = payment_fees["stripe_fee"]
        app_fee = app_fee_calc["app_fee_amount"]
        
        analysis = {}
        
        # MODO DIRECT
        # Conectado paga stripe fee, nosotros cobramos app fee separado
        direct_conectado_receives = amount - stripe_fee - app_fee
        direct_platform_cost = 0  # No pagamos fees de Stripe
        direct_platform_revenue = app_fee
        direct_platform_net = direct_platform_revenue - direct_platform_cost
        
        analysis["direct"] = {
            "conectado_receives": direct_conectado_receives,
            "platform_cost": direct_platform_cost,
            "platform_revenue": direct_platform_revenue,
            "platform_net": direct_platform_net,
            "stripe_fee_paid_by": "conectado",
            "recommended": direct_platform_net > 0
        }
        
        # MODO DESTINATION
        # Nosotros pagamos stripe fee, transferimos amount - app_fee
        dest_conectado_receives = amount - app_fee
        dest_platform_cost = stripe_fee
        dest_platform_revenue = app_fee
        dest_platform_net = dest_platform_revenue - dest_platform_cost
        
        analysis["destination"] = {
            "conectado_receives": dest_conectado_receives,
            "platform_cost": dest_platform_cost,
            "platform_revenue": dest_platform_revenue,
            "platform_net": dest_platform_net,
            "stripe_fee_paid_by": "platform",
            "recommended": dest_platform_net > 0
        }
        
        # MODO SEPARATE
        # Igual que destination, pero con flexibilidad de splits
        sep_conectado_receives = amount - app_fee  # Antes del transfer manual
        sep_platform_cost = stripe_fee
        sep_platform_revenue = app_fee
        sep_platform_net = sep_platform_revenue - sep_platform_cost
        
        analysis["separate"] = {
            "conectado_receives": sep_conectado_receives,
            "platform_cost": sep_platform_cost,
            "platform_revenue": sep_platform_revenue,
            "platform_net": sep_platform_net,
            "stripe_fee_paid_by": "platform",
            "recommended": sep_platform_net > 0,
            "flexibility": "multi_split_capable"
        }
        
        # Agregar resumen
        analysis["summary"] = {
            "amount": amount,
            "payment_method": payment_method.value,
            "stripe_fee": stripe_fee,
            "app_fee": app_fee,
            "best_mode_for_platform": max(analysis, key=lambda x: analysis[x]["platform_net"] if x != "summary" else -float('inf')),
            "best_mode_for_conectado": max(analysis, key=lambda x: analysis[x]["conectado_receives"] if x != "summary" else -float('inf'))
        }
        
        return analysis
    
    def calculate_breakeven_app_fee(self, amount: float, payment_method: PaymentMethod,
                                  charges_mode: ChargesMode) -> Dict[str, float]:
        """
        Calcula el application fee mínimo para que la plataforma no pierda dinero.
        Útil para modos destination y separate.
        """
        
        payment_fees = self.calculate_payment_fees(amount, payment_method)
        stripe_fee = payment_fees["stripe_fee"]
        
        if charges_mode == ChargesMode.DIRECT:
            # En direct, no pagamos stripe fees
            breakeven_fee = 0
            recommended_fee = 5  # Fee mínimo recomendado
            
        else:  # DESTINATION o SEPARATE
            # Necesitamos cubrir el stripe fee
            breakeven_fee = stripe_fee
            recommended_fee = stripe_fee * 1.3  # 30% markup sobre stripe fee
        
        breakeven_pct = (breakeven_fee / amount) * 100 if amount > 0 else 0
        recommended_pct = (recommended_fee / amount) * 100 if amount > 0 else 0
        
        return {
            "amount": amount,
            "payment_method": payment_method.value,
            "charges_mode": charges_mode.value,
            "stripe_fee": stripe_fee,
            "breakeven_app_fee": breakeven_fee,
            "breakeven_app_fee_pct": breakeven_pct,
            "recommended_app_fee": recommended_fee,
            "recommended_app_fee_pct": recommended_pct,
            "margin_at_recommended": recommended_fee - stripe_fee if charges_mode != ChargesMode.DIRECT else recommended_fee
        }
    
    def optimize_fee_policy(self, transaction_samples: List[Dict[str, Any]],
                          charges_mode: ChargesMode,
                          target_margin_pct: float = 1.5) -> FeePolicy:
        """
        Optimiza fee policy basado en muestras de transacciones históricas.
        
        transaction_samples: [
            {"amount": 1000, "method": "card"},
            {"amount": 500, "method": "oxxo"},
            ...
        ]
        """
        
        if not transaction_samples:
            return FeePolicy()  # Policy por defecto
        
        total_volume = 0
        total_stripe_fees = 0
        
        for sample in transaction_samples:
            amount = sample["amount"]
            method = PaymentMethod(sample["method"])
            
            payment_fees = self.calculate_payment_fees(amount, method)
            stripe_fee = payment_fees["stripe_fee"]
            
            total_volume += amount
            if charges_mode != ChargesMode.DIRECT:
                total_stripe_fees += stripe_fee
        
        # Calcular fee promedio que necesitamos cubrir
        avg_stripe_fee_pct = (total_stripe_fees / total_volume) * 100 if total_volume > 0 else 0
        
        # Agregar margen objetivo
        target_fee_pct = avg_stripe_fee_pct + target_margin_pct
        
        # Fee fijo conservador
        fixed_fee = 2.0
        
        # Fee mínimo para transacciones pequeñas
        min_fee = 5.0
        
        optimized_policy = FeePolicy(
            application_fee_pct=target_fee_pct,
            application_fee_fixed=fixed_fee,
            min_fee=min_fee,
            max_fee=None  # Sin límite máximo
        )
        
        logger.info(f"Optimized fee policy: {target_fee_pct:.2f}% + ${fixed_fee}")
        
        return optimized_policy
    
    def generate_fee_report(self, tenant_id: str, 
                          transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Genera reporte completo de fees para un tenant.
        """
        
        if not transactions:
            return {"error": "No transactions provided"}
        
        total_volume = 0
        total_stripe_fees = 0
        total_app_fees = 0
        method_breakdown = {}
        
        for tx in transactions:
            amount = tx["amount"]
            method = PaymentMethod(tx["method"])
            fee_policy = FeePolicy(**tx.get("fee_policy", {}))
            
            # Calcular fees
            payment_fees = self.calculate_payment_fees(amount, method)
            app_fee_calc = self.calculate_application_fee(amount, fee_policy)
            
            stripe_fee = payment_fees["stripe_fee"]
            app_fee = app_fee_calc["app_fee_amount"]
            
            total_volume += amount
            total_stripe_fees += stripe_fee
            total_app_fees += app_fee
            
            # Breakdown por método
            if method.value not in method_breakdown:
                method_breakdown[method.value] = {
                    "count": 0,
                    "volume": 0,
                    "stripe_fees": 0,
                    "app_fees": 0
                }
            
            method_breakdown[method.value]["count"] += 1
            method_breakdown[method.value]["volume"] += amount
            method_breakdown[method.value]["stripe_fees"] += stripe_fee
            method_breakdown[method.value]["app_fees"] += app_fee
        
        # Calcular métricas
        avg_transaction = total_volume / len(transactions)
        stripe_fee_rate = (total_stripe_fees / total_volume) * 100
        app_fee_rate = (total_app_fees / total_volume) * 100
        
        return {
            "tenant_id": tenant_id,
            "period": {
                "start": transactions[0].get("date", "unknown"),
                "end": transactions[-1].get("date", "unknown"),
                "transaction_count": len(transactions)
            },
            "volume": {
                "total": total_volume,
                "average_transaction": avg_transaction,
                "largest_transaction": max(tx["amount"] for tx in transactions),
                "smallest_transaction": min(tx["amount"] for tx in transactions)
            },
            "fees": {
                "total_stripe_fees": total_stripe_fees,
                "total_app_fees": total_app_fees,
                "stripe_fee_rate": stripe_fee_rate,
                "app_fee_rate": app_fee_rate,
                "net_revenue": total_app_fees - total_stripe_fees  # Solo válido para destination/separate
            },
            "method_breakdown": method_breakdown,
            "generated_at": datetime.now().isoformat()
        }

# Instancia global
fee_calculator = FeeCalculator()

if __name__ == "__main__":
    # Ejemplos de uso
    print("💰 Fee Calculator - Análisis Completo")
    print("=" * 50)
    
    calc = FeeCalculator()
    
    # Ejemplo 1: Análisis de fees por método
    amount = 1000.0
    
    print(f"\\n📊 Análisis para ${amount:.2f} MXN:")
    
    for method in [PaymentMethod.CARD, PaymentMethod.OXXO, PaymentMethod.SPEI]:
        fees = calc.calculate_payment_fees(amount, method)
        print(f"\\n{method.value.upper()}:")
        print(f"  Fee Stripe: ${fees['stripe_fee']:.2f} ({fees['effective_rate']:.2f}%)")
        print(f"  Neto: ${fees['net_amount']:.2f}")
    
    # Ejemplo 2: Comparación de modos
    fee_policy = FeePolicy(application_fee_pct=0.8, application_fee_fixed=3.0)
    
    print(f"\\n🔄 Comparación de modos (App fee: {fee_policy.application_fee_pct}% + ${fee_policy.application_fee_fixed}):")
    
    analysis = calc.analyze_charges_mode_economics(amount, PaymentMethod.CARD, fee_policy)
    
    for mode, data in analysis.items():
        if mode == "summary":
            continue
        print(f"\\n{mode.upper()}:")
        print(f"  Conectado recibe: ${data['conectado_receives']:.2f}")
        print(f"  Plataforma neto: ${data['platform_net']:.2f}")
        print(f"  Recomendado: {'✅' if data['recommended'] else '❌'}")
    
    print(f"\\n🎯 Mejor para plataforma: {analysis['summary']['best_mode_for_platform'].upper()}")
    print(f"🎯 Mejor para conectado: {analysis['summary']['best_mode_for_conectado'].upper()}")
    
    # Ejemplo 3: Optimización de policy
    samples = [
        {"amount": 500, "method": "card"},
        {"amount": 1500, "method": "card"},
        {"amount": 800, "method": "oxxo"},
        {"amount": 2000, "method": "spei"}
    ]
    
    optimized = calc.optimize_fee_policy(samples, ChargesMode.DESTINATION, target_margin_pct=1.2)
    
    print(f"\\n🔧 Fee policy optimizada:")
    print(f"  Porcentaje: {optimized.application_fee_pct:.2f}%")
    print(f"  Fijo: ${optimized.application_fee_fixed:.2f}")
    print(f"  Mínimo: ${optimized.min_fee:.2f}")
    
    print("\\n✅ Análisis completado")