"""
💰 Payout Reconciler - Conciliación de pagos y payouts
=====================================================

Reconcilia payouts de Stripe Connect con transacciones.
Genera reportes de conciliación y detecta discrepancias.
"""

import stripe
import os
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any, Tuple
import logging
from collections import defaultdict

from .types import PayoutSummary, StripeConnectFees, STRIPE_MX_FEES
from .connect import connect_manager

logger = logging.getLogger(__name__)

class PayoutReconciler:
    """Reconciliador de payouts con conciliación automática"""
    
    def __init__(self):
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key:
            raise ValueError("STRIPE_SECRET_KEY not found in environment")
        
        self.stripe_fees = STRIPE_MX_FEES
        
        # Storage de reconciliaciones (en prod usar DB)
        self.payout_summaries: Dict[str, PayoutSummary] = {}
        self.reconciliation_reports: List[Dict[str, Any]] = []
    
    def fetch_payout_data(self, connect_account_id: str, 
                         start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Obtiene datos de payouts desde Stripe para un período.
        
        Returns:
            {
                "payouts": [...],
                "charges": [...], 
                "refunds": [...],
                "disputes": [...]
            }
        """
        
        try:
            start_timestamp = int(datetime.combine(start_date, datetime.min.time()).timestamp())
            end_timestamp = int(datetime.combine(end_date, datetime.max.time()).timestamp())
            
            # Obtener payouts
            payouts = stripe.Payout.list(
                stripe_account=connect_account_id,
                created={
                    "gte": start_timestamp,
                    "lte": end_timestamp
                },
                limit=100
            )
            
            # Obtener charges del período
            charges = stripe.Charge.list(
                stripe_account=connect_account_id,
                created={
                    "gte": start_timestamp,
                    "lte": end_timestamp
                },
                limit=100
            )
            
            # Obtener refunds
            refunds = stripe.Refund.list(
                stripe_account=connect_account_id,
                created={
                    "gte": start_timestamp,
                    "lte": end_timestamp
                },
                limit=100
            )
            
            # Obtener disputes
            disputes = stripe.Dispute.list(
                stripe_account=connect_account_id,
                created={
                    "gte": start_timestamp,
                    "lte": end_timestamp
                },
                limit=100
            )
            
            logger.info(f"Fetched payout data for {connect_account_id}: "
                       f"{len(payouts.data)} payouts, {len(charges.data)} charges")
            
            return {
                "payouts": payouts.data,
                "charges": charges.data,
                "refunds": refunds.data,
                "disputes": disputes.data
            }
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to fetch payout data: {e}")
            raise Exception(f"Stripe error: {e.user_message}")
    
    def reconcile_payout(self, payout_id: str, connect_account_id: str,
                        tenant_id: str) -> PayoutSummary:
        """
        Reconcilia un payout específico con sus transacciones.
        
        Returns:
            PayoutSummary con todos los cálculos y discrepancias
        """
        
        try:
            # Obtener payout de Stripe
            payout = stripe.Payout.retrieve(payout_id, stripe_account=connect_account_id)
            
            # Obtener período del payout
            arrival_date = datetime.fromtimestamp(payout.arrival_date)
            
            # Estimar período basado en schedule (simplificado)
            if payout.type == "bank_account":
                # Payouts bancarios típicamente cubren 1-7 días
                period_start = arrival_date - timedelta(days=7)
            else:
                period_start = arrival_date - timedelta(days=1)
            
            period_end = arrival_date
            
            # Obtener transacciones del período
            payout_data = self.fetch_payout_data(
                connect_account_id, 
                period_start.date(), 
                period_end.date()
            )
            
            # Crear summary inicial
            summary = PayoutSummary(
                payout_id=payout_id,
                tenant_id=tenant_id,
                connect_account_id=connect_account_id,
                period_start=period_start,
                period_end=period_end,
                status=payout.status,
                arrival_date=arrival_date
            )
            
            # Calcular componentes
            self._calculate_payout_components(summary, payout_data, payout)
            
            # Verificar conciliación
            actual_payout = payout.amount  # Monto real del payout
            summary.reconciliation_diff = summary.net_amount - actual_payout
            summary.reconciled = abs(summary.reconciliation_diff) <= 100  # Tolerancia 1 peso
            
            if summary.reconciled:
                summary.reconciled_at = datetime.now()
                logger.info(f"Payout {payout_id} reconciled successfully")
            else:
                logger.warning(f"Payout {payout_id} reconciliation failed: "
                             f"diff ${summary.reconciliation_diff/100:.2f}")
            
            # Guardar summary
            self.payout_summaries[payout_id] = summary
            
            return summary
            
        except stripe.error.StripeError as e:
            logger.error(f"Failed to reconcile payout: {e}")
            raise Exception(f"Stripe error: {e.user_message}")
    
    def _calculate_payout_components(self, summary: PayoutSummary, 
                                   payout_data: Dict[str, Any],
                                   payout: Any):
        """Calcula todos los componentes del payout"""
        
        charges = payout_data["charges"]
        refunds = payout_data["refunds"]
        disputes = payout_data["disputes"]
        
        # Calcular ventas brutas
        for charge in charges:
            if charge.paid and not charge.refunded:
                summary.gross_amount += charge.amount
                summary.transactions.append(charge.payment_intent)
                
                # Calcular fees de Stripe
                stripe_fee = sum(fee.amount for fee in charge.balance_transaction.fee_details)
                summary.stripe_fees += stripe_fee
                
                # Application fees (si los hay)
                if hasattr(charge, 'application_fee_amount') and charge.application_fee_amount:
                    summary.application_fees += charge.application_fee_amount
        
        # Calcular refunds
        for refund in refunds:
            summary.refunds += refund.amount
        
        # Calcular disputes
        for dispute in disputes:
            if dispute.status in ["warning_needs_response", "warning_under_review", "warning_closed", "needs_response", "under_review", "charge_refunded", "lost"]:
                summary.disputes += dispute.amount
        
        # Ajustes (diferencias no explicadas)
        # En un sistema real, esto vendría de otros eventos de Stripe
        summary.adjustments = 0
        
        # Calcular neto
        summary.calculate_net()
        
        logger.debug(f"Payout components calculated: "
                    f"gross=${summary.gross_amount/100:.2f}, "
                    f"fees=${summary.stripe_fees/100:.2f}, "
                    f"net=${summary.net_amount/100:.2f}")
    
    def generate_reconciliation_report(self, tenant_id: str,
                                     start_date: date, end_date: date) -> Dict[str, Any]:
        """
        Genera reporte de conciliación para un tenant en un período.
        """
        
        # Obtener payouts del tenant en el período
        tenant_payouts = [
            summary for summary in self.payout_summaries.values()
            if (summary.tenant_id == tenant_id and 
                start_date <= summary.period_start.date() <= end_date)
        ]
        
        if not tenant_payouts:
            return {
                "tenant_id": tenant_id,
                "period": {"start": start_date.isoformat(), "end": end_date.isoformat()},
                "summary": {"total_payouts": 0, "reconciled": 0, "discrepancies": 0},
                "payouts": []
            }
        
        # Calcular totales
        total_gross = sum(p.gross_amount for p in tenant_payouts)
        total_fees = sum(p.stripe_fees for p in tenant_payouts)
        total_app_fees = sum(p.application_fees for p in tenant_payouts)
        total_refunds = sum(p.refunds for p in tenant_payouts)
        total_disputes = sum(p.disputes for p in tenant_payouts)
        total_net = sum(p.net_amount for p in tenant_payouts)
        
        reconciled_count = sum(1 for p in tenant_payouts if p.reconciled)
        discrepancy_count = len(tenant_payouts) - reconciled_count
        
        # Discrepancias por investigar
        discrepancies = [
            {
                "payout_id": p.payout_id,
                "difference": p.reconciliation_diff,
                "difference_mxn": p.reconciliation_diff / 100,
                "status": "needs_investigation" if abs(p.reconciliation_diff) > 1000 else "minor"
            }
            for p in tenant_payouts if not p.reconciled
        ]
        
        # Calcular effective rates
        effective_stripe_rate = (total_fees / total_gross * 100) if total_gross > 0 else 0
        effective_app_rate = (total_app_fees / total_gross * 100) if total_gross > 0 else 0
        
        report = {
            "tenant_id": tenant_id,
            "period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat(),
                "days": (end_date - start_date).days
            },
            "summary": {
                "total_payouts": len(tenant_payouts),
                "reconciled": reconciled_count,
                "discrepancies": discrepancy_count,
                "reconciliation_rate": reconciled_count / len(tenant_payouts) * 100
            },
            "financials": {
                "gross_amount": total_gross,
                "stripe_fees": total_fees,
                "application_fees": total_app_fees,
                "refunds": total_refunds,
                "disputes": total_disputes,
                "net_amount": total_net,
                "effective_stripe_rate": effective_stripe_rate,
                "effective_app_rate": effective_app_rate
            },
            "discrepancies": discrepancies,
            "payouts": [
                {
                    "payout_id": p.payout_id,
                    "period_start": p.period_start.isoformat(),
                    "period_end": p.period_end.isoformat(),
                    "gross_amount": p.gross_amount,
                    "net_amount": p.net_amount,
                    "reconciled": p.reconciled,
                    "difference": p.reconciliation_diff,
                    "transactions_count": len(p.transactions)
                }
                for p in tenant_payouts
            ],
            "generated_at": datetime.now().isoformat()
        }
        
        # Guardar reporte
        self.reconciliation_reports.append(report)
        
        logger.info(f"Generated reconciliation report for {tenant_id}: "
                   f"{len(tenant_payouts)} payouts, {reconciled_count} reconciled")
        
        return report
    
    def calculate_connect_costs(self, tenant_id: str, month: date) -> Dict[str, Any]:
        """
        Calcula costos de Stripe Connect para un tenant en un mes.
        """
        
        # Obtener cuentas del tenant
        accounts = connect_manager.list_accounts_by_tenant(tenant_id)
        active_accounts = len([a for a in accounts if a.onboarding_complete])
        
        # Obtener payouts del mes
        month_start = month.replace(day=1)
        next_month = (month_start + timedelta(days=32)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        
        monthly_payouts = [
            summary for summary in self.payout_summaries.values()
            if (summary.tenant_id == tenant_id and
                month_start.date() <= summary.arrival_date.date() <= month_end.date())
        ]
        
        # Calcular volumen y número de payouts
        monthly_volume = sum(p.net_amount for p in monthly_payouts) / 100  # En MXN
        payout_count = len(monthly_payouts)
        
        # Calcular costos usando las tarifas de Stripe MX
        costs = self.stripe_fees.calculate_connect_monthly_cost(
            active_accounts, monthly_volume, payout_count
        )
        
        # Agregar detalles del tenant
        costs.update({
            "tenant_id": tenant_id,
            "month": month.isoformat(),
            "active_accounts": active_accounts,
            "total_accounts": len(accounts),
            "monthly_volume": monthly_volume,
            "payout_count": payout_count,
            "average_payout": monthly_volume / payout_count if payout_count > 0 else 0,
            "cost_per_peso": costs["total_monthly_cost"] / monthly_volume if monthly_volume > 0 else 0
        })
        
        return costs
    
    def get_payout_summary(self, payout_id: str) -> Optional[PayoutSummary]:
        """Obtiene summary de un payout"""
        return self.payout_summaries.get(payout_id)
    
    def list_unreconciled_payouts(self, tenant_id: str = None) -> List[PayoutSummary]:
        """Lista payouts no reconciliados"""
        
        unreconciled = [
            summary for summary in self.payout_summaries.values()
            if not summary.reconciled
        ]
        
        if tenant_id:
            unreconciled = [s for s in unreconciled if s.tenant_id == tenant_id]
        
        # Ordenar por diferencia (mayor primero)
        unreconciled.sort(key=lambda x: abs(x.reconciliation_diff), reverse=True)
        
        return unreconciled
    
    def export_reconciliation_data(self, tenant_id: str, 
                                 start_date: date, end_date: date) -> Dict[str, Any]:
        """Exporta datos de conciliación para análisis externo"""
        
        tenant_payouts = [
            summary for summary in self.payout_summaries.values()
            if (summary.tenant_id == tenant_id and 
                start_date <= summary.period_start.date() <= end_date)
        ]
        
        export_data = {
            "metadata": {
                "tenant_id": tenant_id,
                "period_start": start_date.isoformat(),
                "period_end": end_date.isoformat(),
                "export_date": datetime.now().isoformat(),
                "total_payouts": len(tenant_payouts)
            },
            "payouts": [summary.dict() for summary in tenant_payouts],
            "summary_stats": {
                "total_volume": sum(p.gross_amount for p in tenant_payouts),
                "total_fees": sum(p.stripe_fees for p in tenant_payouts),
                "reconciliation_rate": len([p for p in tenant_payouts if p.reconciled]) / len(tenant_payouts) * 100 if tenant_payouts else 0
            }
        }
        
        return export_data

# Instancia global
payout_reconciler = PayoutReconciler()

if __name__ == "__main__":
    # Ejemplo de uso del reconciliador
    print("💰 Payout Reconciler - Test de Conciliación")
    print("=" * 50)
    
    reconciler = PayoutReconciler()
    
    # Simular datos de un payout para demostración
    demo_tenant = "lb-productions"
    demo_account = "acct_demo_connect"
    
    try:
        # Calcular costos Connect para el mes actual
        current_month = date.today().replace(day=1)
        
        connect_costs = reconciler.calculate_connect_costs(demo_tenant, current_month)
        
        print(f"\\n💳 Costos Stripe Connect para {demo_tenant}:")
        print(f"   Cuentas activas: {connect_costs['active_accounts']}")
        print(f"   Volumen mensual: ${connect_costs['monthly_volume']:,.2f} MXN")
        print(f"   Payouts del mes: {connect_costs['payout_count']}")
        print(f"\\n💰 Desglose de costos:")
        print(f"   Fee por cuentas activas: ${connect_costs['active_accounts_fee']:.2f}")
        print(f"   Fee por volumen (0.25%): ${connect_costs['payout_percentage_fee']:.2f}")
        print(f"   Fee por payouts ($12 c/u): ${connect_costs['payout_fixed_fee']:.2f}")
        print(f"   TOTAL MENSUAL: ${connect_costs['total_monthly_cost']:.2f}")
        
        # Simular reconciliación
        print(f"\\n🔍 Ejemplo de reconciliación:")
        print(f"   Costo por peso procesado: ${connect_costs['cost_per_peso']:.4f}")
        print(f"   Costo por cuenta: ${connect_costs['cost_per_account']:.2f}")
        
        # Generar reporte demo
        start_date = current_month
        end_date = current_month + timedelta(days=30)
        
        print(f"\\n📊 Para generar reporte real:")
        print(f"   Período: {start_date} a {end_date}")
        print(f"   Usar: reconciler.generate_reconciliation_report('{demo_tenant}', start_date, end_date)")
        
        print("\\n✅ Test de reconciliación completado")
        print("💡 Para datos reales, conecta con cuentas Stripe activas")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Configura variables de entorno de Stripe para tests completos")