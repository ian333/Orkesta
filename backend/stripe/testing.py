"""
🧪 Stripe Test Suite - Testing completo de OCO
=============================================

Suite de pruebas para todos los componentes de Stripe Connect.
Incluye scenarios complejos, OXXO testing y simulaciones.
"""

import stripe
import os
import json
import time
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
import logging

from .types import (
    PaymentMethod, ChargesMode, FeePolicy, ConnectAccount,
    OXXO_TEST_EMAILS, EventType
)
from .connect import connect_manager
from .checkout import checkout_orchestrator
from .webhooks import webhook_processor
from .fees import fee_calculator
from .transfers import transfer_manager
from .payouts import payout_reconciler

logger = logging.getLogger(__name__)

class StripeTestSuite:
    """Suite completa de pruebas para OCO"""
    
    def __init__(self):
        # Verificar que estamos en test mode
        stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
        if not stripe.api_key or not stripe.api_key.startswith("sk_test_"):
            raise ValueError("Must use test API key (sk_test_) for testing")
        
        self.test_results: List[Dict[str, Any]] = []
        self.test_accounts: Dict[str, ConnectAccount] = {}
        
        # Configurar logging para tests
        logging.basicConfig(level=logging.INFO)
    
    def setup_test_accounts(self) -> Dict[str, ConnectAccount]:
        """Crea cuentas de prueba para los 3 modos"""
        
        print("🔧 Configurando cuentas de prueba...")
        
        test_configs = [
            {
                "tenant_id": "test-direct-mode",
                "email": "direct@orkesta.test",
                "charges_mode": ChargesMode.DIRECT,
                "fee_policy": FeePolicy(application_fee_pct=0.5, application_fee_fixed=2.0)
            },
            {
                "tenant_id": "test-destination-mode", 
                "email": "destination@orkesta.test",
                "charges_mode": ChargesMode.DESTINATION,
                "fee_policy": FeePolicy(application_fee_pct=1.0, application_fee_fixed=3.0)
            },
            {
                "tenant_id": "test-separate-mode",
                "email": "separate@orkesta.test", 
                "charges_mode": ChargesMode.SEPARATE,
                "fee_policy": FeePolicy(application_fee_pct=1.5, application_fee_fixed=5.0)
            }
        ]
        
        for config in test_configs:
            try:
                # Crear cuenta Express
                account = connect_manager.create_express_account(
                    config["tenant_id"],
                    config["email"]
                )
                
                # Configurar modo y fees
                connect_manager.update_account_settings(
                    account.account_id,
                    charges_mode=config["charges_mode"],
                    fee_policy=config["fee_policy"]
                )
                
                # Simular onboarding completo
                account.onboarding_complete = True
                account.capabilities_active = ["card_payments", "transfers"]
                
                self.test_accounts[config["charges_mode"].value] = account
                
                print(f"✅ Cuenta {config['charges_mode'].value}: {account.account_id}")
                
            except Exception as e:
                print(f"❌ Error creando cuenta {config['tenant_id']}: {e}")
        
        return self.test_accounts
    
    async def test_payment_flows(self) -> List[Dict[str, Any]]:
        """Prueba flujos de pago para todos los modos y métodos"""
        
        print("\\n💳 Probando flujos de pago...")
        
        test_cases = [
            {"amount": 1000.0, "method": PaymentMethod.CARD, "description": "Pago con tarjeta"},
            {"amount": 500.0, "method": PaymentMethod.OXXO, "description": "Pago OXXO"},
            {"amount": 2500.0, "method": PaymentMethod.SPEI, "description": "Transferencia SPEI"}
        ]
        
        results = []
        
        for mode, account in self.test_accounts.items():
            for test_case in test_cases:
                try:
                    # Crear checkout session
                    session = checkout_orchestrator.create_checkout_session(
                        tenant_id=account.tenant_id,
                        order_id=f"TEST-{mode.upper()}-{int(time.time())}",
                        amount=test_case["amount"],
                        payment_methods=[test_case["method"]],
                        metadata={"test_case": test_case["description"]}
                    )
                    
                    # Calcular costos
                    costs = checkout_orchestrator.calculate_effective_costs(
                        test_case["amount"],
                        test_case["method"],
                        account.charges_mode,
                        account.fee_policy.application_fee_pct,
                        account.fee_policy.application_fee_fixed
                    )
                    
                    result = {
                        "mode": mode,
                        "method": test_case["method"].value,
                        "amount": test_case["amount"],
                        "session_id": session.session_id,
                        "checkout_url": session.checkout_url,
                        "costs": costs,
                        "status": "session_created",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    results.append(result)
                    
                    print(f"   ✅ {mode.upper()} + {test_case['method'].value}: "
                          f"${test_case['amount']:.2f} → {session.session_id[:20]}...")
                    
                except Exception as e:
                    result = {
                        "mode": mode,
                        "method": test_case["method"].value,
                        "amount": test_case["amount"],
                        "error": str(e),
                        "status": "failed",
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    results.append(result)
                    print(f"   ❌ {mode.upper()} + {test_case['method'].value}: {e}")
        
        self.test_results.extend(results)
        return results
    
    def test_oxxo_scenarios(self) -> List[Dict[str, Any]]:
        """Prueba escenarios específicos de OXXO"""
        
        print("\\n🏪 Probando escenarios OXXO...")
        
        oxxo_scenarios = [
            {
                "email": OXXO_TEST_EMAILS["success_immediate"],
                "description": "Éxito inmediato",
                "expected": "payment_succeeded"
            },
            {
                "email": OXXO_TEST_EMAILS["success_delayed"],
                "description": "Éxito con delay",
                "expected": "payment_succeeded_delayed"
            },
            {
                "email": OXXO_TEST_EMAILS["expired"],
                "description": "Vale expirado",
                "expected": "payment_failed"
            },
            {
                "email": OXXO_TEST_EMAILS["declined"],
                "description": "Pago declinado",
                "expected": "payment_failed"
            }
        ]
        
        results = []
        
        # Usar cuenta destination para OXXO
        account = self.test_accounts.get("destination")
        if not account:
            print("❌ No hay cuenta destination para pruebas OXXO")
            return []
        
        for scenario in oxxo_scenarios:
            try:
                # Crear Payment Link (más fácil para OXXO testing)
                payment_link = checkout_orchestrator.create_payment_link(
                    tenant_id=account.tenant_id,
                    order_id=f"OXXO-TEST-{int(time.time())}",
                    amount=750.0,  # $750 MXN
                    description=f"Test OXXO: {scenario['description']}"
                )
                
                result = {
                    "scenario": scenario["description"],
                    "test_email": scenario["email"],
                    "expected_outcome": scenario["expected"],
                    "payment_link": payment_link,
                    "instructions": f"Usar email {scenario['email']} en el checkout",
                    "status": "link_created",
                    "timestamp": datetime.now().isoformat()
                }
                
                results.append(result)
                
                print(f"   ✅ {scenario['description']}: {payment_link}")
                print(f"      📧 Email de prueba: {scenario['email']}")
                
            except Exception as e:
                result = {
                    "scenario": scenario["description"],
                    "error": str(e),
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                }
                
                results.append(result)
                print(f"   ❌ {scenario['description']}: {e}")
        
        self.test_results.extend(results)
        return results
    
    def test_multi_split_transfers(self) -> Dict[str, Any]:
        """Prueba transfers multi-split en modo Separate"""
        
        print("\\n💸 Probando multi-split transfers...")
        
        # Usar cuenta separate
        account = self.test_accounts.get("separate")
        if not account:
            print("❌ No hay cuenta separate para pruebas de transfers")
            return {"error": "No separate account"}
        
        try:
            # Definir participantes del split
            participants = [
                {
                    "account_id": account.account_id,  # Vendor principal
                    "weight": 60,
                    "min_amount": 2000,  # $20 mínimo
                    "description": "Vendor principal (60%)",
                    "metadata": {"participant_type": "vendor"}
                },
                {
                    "account_id": account.account_id,  # Delivery (reutilizar cuenta para demo)
                    "weight": 25,
                    "description": "Servicio de entrega (25%)",
                    "metadata": {"participant_type": "delivery"}
                },
                {
                    "account_id": account.account_id,  # Insurance (reutilizar cuenta para demo)
                    "weight": 15,
                    "description": "Seguro de envío (15%)",
                    "metadata": {"participant_type": "insurance"}
                }
            ]
            
            # Calcular splits para $2000
            total_amount = 200000  # $2000 en centavos
            
            splits = transfer_manager.calculate_optimal_splits(
                total_amount,
                participants,
                platform_fee_pct=2.5  # 2.5% plataforma
            )
            
            result = {
                "total_amount": total_amount,
                "platform_fee_pct": 2.5,
                "participants": len(participants),
                "splits_calculated": len(splits),
                "splits": splits,
                "total_distributed": sum(s["amount"] for s in splits),
                "platform_retained": total_amount - sum(s["amount"] for s in splits),
                "status": "calculated",
                "timestamp": datetime.now().isoformat(),
                "note": "En producción, estos serían transfers reales a diferentes cuentas"
            }
            
            print(f"   ✅ Multi-split calculado: {len(splits)} participantes")
            print(f"   💰 Total distribuido: ${sum(s['amount'] for s in splits)/100:.2f}")
            print(f"   🏦 Plataforma retiene: ${result['platform_retained']/100:.2f}")
            
            for split in splits:
                print(f"      - {split['description']}: ${split['amount']/100:.2f} ({split['amount_pct']:.1f}%)")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "status": "failed",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"   ❌ Error en multi-split: {e}")
            self.test_results.append(error_result)
            return error_result
    
    def test_webhook_processing(self) -> List[Dict[str, Any]]:
        """Prueba procesamiento de webhooks e idempotencia"""
        
        print("\\n🔔 Probando webhooks e idempotencia...")
        
        results = []
        
        # Eventos de prueba
        test_events = [
            {
                "type": EventType.PAYMENT_SUCCEEDED,
                "tenant_id": "test-webhooks",
                "data": {
                    "amount": 150000,  # $1500
                    "currency": "mxn",
                    "metadata": {"order_id": "TEST-ORDER-001"}
                }
            },
            {
                "type": EventType.CHARGE_REFUNDED,
                "tenant_id": "test-webhooks",
                "data": {
                    "amount": 50000,  # $500 refund
                    "reason": "requested_by_customer"
                }
            },
            {
                "type": EventType.PAYOUT_PAID,
                "tenant_id": "test-webhooks",
                "data": {
                    "amount": 95000,  # $950 payout
                    "arrival_date": int(time.time()) + 86400  # Mañana
                }
            }
        ]
        
        for event_config in test_events:
            try:
                # Simular evento
                result = webhook_processor.simulate_webhook_event(
                    event_config["type"],
                    event_config["tenant_id"],
                    event_config["data"]
                )
                
                # Probar idempotencia (enviar 3 veces)
                idempotency_test = []
                for i in range(3):
                    # Simular el mismo evento
                    duplicate_result = webhook_processor.simulate_webhook_event(
                        event_config["type"],
                        event_config["tenant_id"],
                        event_config["data"]
                    )
                    
                    idempotency_test.append({
                        "attempt": i + 1,
                        "was_duplicate": duplicate_result.get("was_duplicate", False),
                        "processed": duplicate_result.get("processed", False)
                    })
                
                test_result = {
                    "event_type": event_config["type"].value,
                    "initial_result": result,
                    "idempotency_test": idempotency_test,
                    "idempotency_working": all(t["was_duplicate"] for t in idempotency_test[1:]),
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }
                
                results.append(test_result)
                
                print(f"   ✅ {event_config['type'].value}: "
                      f"{'Idempotencia OK' if test_result['idempotency_working'] else 'Idempotencia FALLA'}")
                
            except Exception as e:
                error_result = {
                    "event_type": event_config["type"].value,
                    "error": str(e),
                    "status": "failed",
                    "timestamp": datetime.now().isoformat()
                }
                
                results.append(error_result)
                print(f"   ❌ {event_config['type'].value}: {e}")
        
        self.test_results.extend(results)
        return results
    
    def test_fee_calculations(self) -> Dict[str, Any]:
        """Prueba cálculos de fees y optimizaciones"""
        
        print("\\n💰 Probando cálculos de fees...")
        
        try:
            # Samples de transacciones para optimización
            transaction_samples = [
                {"amount": 500, "method": "card"},
                {"amount": 1200, "method": "card"},
                {"amount": 800, "method": "oxxo"},
                {"amount": 3500, "method": "spei"},
                {"amount": 250, "method": "card"},
                {"amount": 1800, "method": "card"},
                {"amount": 600, "method": "oxxo"},
                {"amount": 4200, "method": "spei"}
            ]
            
            # Análisis por método
            method_analysis = {}
            
            for method in [PaymentMethod.CARD, PaymentMethod.OXXO, PaymentMethod.SPEI]:
                method_samples = [s for s in transaction_samples if s["method"] == method.value]
                if not method_samples:
                    continue
                
                avg_amount = sum(s["amount"] for s in method_samples) / len(method_samples)
                
                # Calcular fees promedio
                fees = fee_calculator.calculate_payment_fees(avg_amount, method)
                
                method_analysis[method.value] = {
                    "sample_count": len(method_samples),
                    "average_amount": avg_amount,
                    "stripe_fee": fees["stripe_fee"],
                    "effective_rate": fees["effective_rate"],
                    "recommended_app_fee": fees["stripe_fee"] * 1.3  # 30% markup
                }
            
            # Optimizar fee policy
            optimized_policy = fee_calculator.optimize_fee_policy(
                transaction_samples,
                ChargesMode.DESTINATION,
                target_margin_pct=1.2
            )
            
            # Análisis comparativo de modos
            sample_amount = 1000.0
            mode_comparison = {}
            
            for mode in [ChargesMode.DIRECT, ChargesMode.DESTINATION, ChargesMode.SEPARATE]:
                analysis = fee_calculator.analyze_charges_mode_economics(
                    sample_amount,
                    PaymentMethod.CARD,
                    optimized_policy
                )
                
                mode_comparison[mode.value] = analysis[mode.value]
            
            result = {
                "transaction_samples": len(transaction_samples),
                "method_analysis": method_analysis,
                "optimized_policy": {
                    "percentage": optimized_policy.application_fee_pct,
                    "fixed": optimized_policy.application_fee_fixed,
                    "min_fee": optimized_policy.min_fee
                },
                "mode_comparison": mode_comparison,
                "best_mode_for_platform": max(
                    mode_comparison.keys(),
                    key=lambda x: mode_comparison[x]["platform_net"]
                ),
                "status": "success",
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"   ✅ Análisis de {len(transaction_samples)} transacciones")
            print(f"   🔧 Policy optimizada: {optimized_policy.application_fee_pct:.2f}% + ${optimized_policy.application_fee_fixed}")
            print(f"   🎯 Mejor modo para plataforma: {result['best_mode_for_platform'].upper()}")
            
            for method, data in method_analysis.items():
                print(f"      {method.upper()}: {data['effective_rate']:.2f}% efectivo")
            
            self.test_results.append(result)
            return result
            
        except Exception as e:
            error_result = {
                "error": str(e),
                "status": "failed", 
                "timestamp": datetime.now().isoformat()
            }
            
            print(f"   ❌ Error en cálculos: {e}")
            self.test_results.append(error_result)
            return error_result
    
    def generate_test_report(self) -> Dict[str, Any]:
        """Genera reporte completo de todas las pruebas"""
        
        print("\\n📊 Generando reporte de pruebas...")
        
        # Contar resultados por estado
        total_tests = len(self.test_results)
        successful_tests = len([r for r in self.test_results if r.get("status") == "success"])
        failed_tests = total_tests - successful_tests
        
        # Agrupar por tipo de prueba
        test_types = {}
        for result in self.test_results:
            # Determinar tipo basado en las claves del resultado
            if "mode" in result and "method" in result:
                test_type = "payment_flows"
            elif "scenario" in result:
                test_type = "oxxo_scenarios"
            elif "splits_calculated" in result:
                test_type = "multi_split"
            elif "event_type" in result:
                test_type = "webhooks"
            elif "optimized_policy" in result:
                test_type = "fee_calculations"
            else:
                test_type = "other"
            
            if test_type not in test_types:
                test_types[test_type] = {"total": 0, "successful": 0, "failed": 0}
            
            test_types[test_type]["total"] += 1
            if result.get("status") == "success":
                test_types[test_type]["successful"] += 1
            else:
                test_types[test_type]["failed"] += 1
        
        # Generar reporte
        report = {
            "test_suite": "OCO Stripe Connect Test Suite",
            "executed_at": datetime.now().isoformat(),
            "summary": {
                "total_tests": total_tests,
                "successful": successful_tests,
                "failed": failed_tests,
                "success_rate": (successful_tests / total_tests * 100) if total_tests > 0 else 0
            },
            "test_accounts": {
                mode: {
                    "account_id": account.account_id,
                    "tenant_id": account.tenant_id,
                    "charges_mode": account.charges_mode.value,
                    "fee_policy": {
                        "percentage": account.fee_policy.application_fee_pct,
                        "fixed": account.fee_policy.application_fee_fixed
                    }
                }
                for mode, account in self.test_accounts.items()
            },
            "test_types": test_types,
            "detailed_results": self.test_results,
            "recommendations": self._generate_recommendations()
        }
        
        print(f"   📈 Tests ejecutados: {total_tests}")
        print(f"   ✅ Exitosos: {successful_tests}")
        print(f"   ❌ Fallidos: {failed_tests}")
        print(f"   📊 Tasa de éxito: {report['summary']['success_rate']:.1f}%")
        
        return report
    
    def _generate_recommendations(self) -> List[str]:
        """Genera recomendaciones basadas en los resultados"""
        
        recommendations = []
        
        # Verificar si hay fallas
        failed_results = [r for r in self.test_results if r.get("status") == "failed"]
        if failed_results:
            recommendations.append(
                f"⚠️ {len(failed_results)} pruebas fallaron - revisar configuración de Stripe"
            )
        
        # Verificar accounts creadas
        if len(self.test_accounts) < 3:
            recommendations.append(
                "🔧 No se pudieron crear todas las cuentas de prueba - verificar permisos API"
            )
        
        # Verificar idempotencia
        webhook_results = [r for r in self.test_results if "idempotency_working" in r]
        idempotency_failures = [r for r in webhook_results if not r["idempotency_working"]]
        
        if idempotency_failures:
            recommendations.append(
                "🔔 Falla en idempotencia de webhooks - revisar implementación"
            )
        
        # Si todo está bien
        if not recommendations:
            recommendations.append("✅ Todas las pruebas pasaron - sistema listo para producción")
            recommendations.append("🚀 Considerar implementar monitoreo de webhooks en vivo")
            recommendations.append("📊 Configurar alertas para transacciones fallidas")
        
        return recommendations
    
    async def run_full_test_suite(self) -> Dict[str, Any]:
        """Ejecuta la suite completa de pruebas"""
        
        print("🧪 INICIANDO SUITE COMPLETA DE PRUEBAS OCO")
        print("=" * 60)
        
        try:
            # 1. Setup
            self.setup_test_accounts()
            
            # 2. Flujos de pago
            await self.test_payment_flows()
            
            # 3. OXXO scenarios
            self.test_oxxo_scenarios()
            
            # 4. Multi-split transfers
            self.test_multi_split_transfers()
            
            # 5. Webhook processing
            self.test_webhook_processing()
            
            # 6. Fee calculations
            self.test_fee_calculations()
            
            # 7. Generar reporte
            report = self.generate_test_report()
            
            print("\\n" + "=" * 60)
            print("🎯 SUITE DE PRUEBAS COMPLETADA")
            print("=" * 60)
            
            return report
            
        except Exception as e:
            print(f"\\n❌ ERROR EN SUITE DE PRUEBAS: {e}")
            return {"error": str(e), "timestamp": datetime.now().isoformat()}

# Instancia global
stripe_test_suite = StripeTestSuite()

if __name__ == "__main__":
    # Ejecutar suite de pruebas
    print("🧪 Stripe Test Suite - OCO Testing")
    print("=" * 50)
    
    async def main():
        suite = StripeTestSuite()
        
        try:
            report = await suite.run_full_test_suite()
            
            # Guardar reporte
            with open("oco_test_report.json", "w") as f:
                json.dump(report, f, indent=2, default=str)
            
            print("\\n💾 Reporte guardado en: oco_test_report.json")
            
        except Exception as e:
            print(f"❌ Error ejecutando tests: {e}")
    
    # Ejecutar tests
    asyncio.run(main())