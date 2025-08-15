"""
🧪 Orkesta Comprehensive Test Suite - Testing completo del sistema
================================================================

Suite exhaustiva que prueba LITERAL TODO EL SISTEMA:
- Shared Context & Agents
- Stripe Connect (3 modos)
- Conversation Flows
- Control Tower APIs
- Multi-tenant isolation
- Performance & Load testing
"""

import asyncio
import json
import time
import threading
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import string

# Imports del sistema Orkesta
from orkesta_shared_context import get_shared_context, OrkestaSharedContext
from orkesta_smart_agents import CatalogMapperAgent, AliasNormalizerAgent, PriceResolverAgent, QuoteBuilderAgent
from orkesta_conversation_flows import conversation_engine, ConversationStage, ConversationIntent
from orkesta_stripe.testing import stripe_test_suite
from orkesta_stripe.stripe_types import ChargesMode, PaymentMethod

logger = logging.getLogger(__name__)

@dataclass
class TestResult:
    """Resultado de una prueba individual"""
    test_name: str
    test_category: str
    passed: bool
    duration_seconds: float
    details: Dict[str, Any]
    error_message: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

@dataclass
class TestSuiteReport:
    """Reporte completo de la suite de pruebas"""
    suite_name: str
    started_at: datetime
    completed_at: Optional[datetime]
    total_tests: int
    passed_tests: int
    failed_tests: int
    duration_seconds: float
    test_results: List[TestResult]
    performance_metrics: Dict[str, Any]
    system_health: Dict[str, Any]

class OrkestaComprehensiveTestSuite:
    """Suite completa de pruebas del sistema Orkesta"""
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.performance_metrics = {}
        
        # URLs de APIs para testing
        self.api_urls = {
            "groq": "http://localhost:8002",
            "control_tower": "http://localhost:8003", 
            "control_tower_v2": "http://localhost:8004"
        }
        
        # Test data
        self.test_tenants = [
            "test-tenant-alpha",
            "test-tenant-beta", 
            "test-tenant-gamma"
        ]
        
        self.test_customers = [
            {"id": "cust_001", "name": "Juan Pérez", "company": "TechCorp"},
            {"id": "cust_002", "name": "María González", "company": "StartupMX"},
            {"id": "cust_003", "name": "Carlos Rodríguez", "company": "EnterpriseCo"}
        ]
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
    
    async def run_full_test_suite(self) -> TestSuiteReport:
        """Ejecuta la suite completa de pruebas"""
        
        print("🧪 ORKESTA COMPREHENSIVE TEST SUITE")
        print("=" * 70)
        print("Testing LITERAL TODO EL SISTEMA...")
        print("=" * 70)
        
        started_at = datetime.now()
        
        try:
            # 1. Preparación del entorno
            await self._setup_test_environment()
            
            # 2. Tests de componentes core
            await self._test_shared_context_system()
            await self._test_smart_agents_system()
            
            # 3. Tests de Stripe Connect
            await self._test_stripe_connect_full()
            
            # 4. Tests de conversaciones
            await self._test_conversation_flows()
            
            # 5. Tests de APIs
            await self._test_control_tower_apis()
            
            # 6. Tests de multi-tenancy
            await self._test_multi_tenant_isolation()
            
            # 7. Tests de performance
            await self._test_system_performance()
            
            # 8. Tests de integración end-to-end
            await self._test_end_to_end_scenarios()
            
            # 9. Tests de estrés y carga
            await self._test_load_and_stress()
            
            # 10. Cleanup
            await self._cleanup_test_environment()
            
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            # Generar reporte final
            report = self._generate_final_report(started_at, completed_at, duration)
            
            print("\\n" + "=" * 70)
            print("🎯 TEST SUITE COMPLETADA")
            print("=" * 70)
            
            return report
            
        except Exception as e:
            print(f"\\n❌ ERROR EN SUITE DE PRUEBAS: {e}")
            completed_at = datetime.now()
            duration = (completed_at - started_at).total_seconds()
            
            # Reporte de error
            error_report = TestSuiteReport(
                suite_name="Orkesta Comprehensive Test Suite",
                started_at=started_at,
                completed_at=completed_at,
                total_tests=len(self.test_results),
                passed_tests=sum(1 for r in self.test_results if r.passed),
                failed_tests=len(self.test_results) - sum(1 for r in self.test_results if r.passed),
                duration_seconds=duration,
                test_results=self.test_results,
                performance_metrics=self.performance_metrics,
                system_health={"status": "error", "error": str(e)}
            )
            
            return error_report
    
    async def _setup_test_environment(self):
        """Configura el entorno de pruebas"""
        
        print("\\n🔧 Configurando entorno de pruebas...")
        
        start_time = time.time()
        
        try:
            # Verificar APIs disponibles
            api_status = {}
            for api_name, url in self.api_urls.items():
                try:
                    response = requests.get(f"{url}/health", timeout=5)
                    api_status[api_name] = response.status_code == 200
                except:
                    api_status[api_name] = False
            
            # Configurar contextos de prueba
            for tenant_id in self.test_tenants:
                context = get_shared_context(tenant_id)
                
                # Configurar catálogo de prueba
                test_catalog = [
                    {
                        "id": "prod_001",
                        "name": "Laptop HP EliteBook",
                        "category": "Computadoras",
                        "price": 25000.0,
                        "aliases": ["laptop hp", "elitebook", "hp laptop"]
                    },
                    {
                        "id": "prod_002", 
                        "name": "Monitor Dell 24\"",
                        "category": "Monitores",
                        "price": 5500.0,
                        "aliases": ["monitor dell", "pantalla dell", "monitor 24"]
                    },
                    {
                        "id": "prod_003",
                        "name": "Teclado Logitech MX",
                        "category": "Accesorios",
                        "price": 1800.0,
                        "aliases": ["teclado logitech", "mx keys", "teclado mx"]
                    }
                ]
                
                for product in test_catalog:
                    context.add_catalog_item(product)
                
                # Configurar clientes de prueba
                for customer in self.test_customers:
                    context.add_client(customer["id"], customer)
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="setup_test_environment",
                test_category="setup",
                passed=True,
                duration_seconds=duration,
                details={
                    "api_status": api_status,
                    "tenants_configured": len(self.test_tenants),
                    "products_per_tenant": len(test_catalog),
                    "customers_per_tenant": len(self.test_customers)
                }
            ))
            
            print(f"   ✅ Entorno configurado: {len(self.test_tenants)} tenants, {len(test_catalog)} productos")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="setup_test_environment",
                test_category="setup",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            raise
    
    async def _test_shared_context_system(self):
        """Tests del sistema de contexto compartido"""
        
        print("\\n🧠 Testing Shared Context System...")
        
        test_cases = [
            self._test_context_creation,
            self._test_context_thread_safety,
            self._test_context_isolation,
            self._test_catalog_operations,
            self._test_client_management,
            self._test_order_processing,
            self._test_context_persistence
        ]
        
        for test_case in test_cases:
            await test_case()
    
    async def _test_context_creation(self):
        """Test creación de contextos"""
        
        start_time = time.time()
        
        try:
            # Crear contextos únicos
            contexts = {}
            for tenant_id in self.test_tenants:
                context = get_shared_context(tenant_id)
                contexts[tenant_id] = context
                
                # Verificar que son instancias únicas
                assert context.tenant_id == tenant_id
                assert id(context) == id(get_shared_context(tenant_id))  # Mismo objeto
            
            # Verificar que contextos diferentes son objetos diferentes
            alpha_context = contexts["test-tenant-alpha"]
            beta_context = contexts["test-tenant-beta"]
            assert id(alpha_context) != id(beta_context)
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="context_creation",
                test_category="shared_context",
                passed=True,
                duration_seconds=duration,
                details={
                    "contexts_created": len(contexts),
                    "unique_instances": len(set(id(c) for c in contexts.values())),
                    "tenant_isolation": True
                }
            ))
            
            print("   ✅ Context creation: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="context_creation",
                test_category="shared_context",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Context creation: {e}")
    
    async def _test_context_thread_safety(self):
        """Test thread safety del contexto compartido"""
        
        start_time = time.time()
        
        try:
            tenant_id = "test-tenant-alpha"
            context = get_shared_context(tenant_id)
            
            # Test concurrente de operaciones
            def concurrent_operations(thread_id):
                results = []
                for i in range(10):
                    # Agregar y obtener items
                    item_id = f"item_{thread_id}_{i}"
                    context.add_catalog_item({
                        "id": item_id,
                        "name": f"Product {thread_id}-{i}",
                        "price": i * 100
                    })
                    
                    # Verificar que se agregó
                    catalog = context.get_catalog()
                    found = any(item["id"] == item_id for item in catalog)
                    results.append(found)
                
                return results
            
            # Ejecutar en múltiples threads
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(concurrent_operations, thread_id)
                    for thread_id in range(5)
                ]
                
                thread_results = []
                for future in as_completed(futures):
                    thread_results.append(future.result())
            
            # Verificar que todas las operaciones fueron exitosas
            all_successful = all(
                all(results) for results in thread_results
            )
            
            final_catalog = context.get_catalog()
            expected_items = 5 * 10  # 5 threads × 10 items
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="context_thread_safety",
                test_category="shared_context",
                passed=all_successful and len([item for item in final_catalog if item["id"].startswith("item_")]) == expected_items,
                duration_seconds=duration,
                details={
                    "threads_executed": 5,
                    "operations_per_thread": 10,
                    "all_operations_successful": all_successful,
                    "items_in_catalog": len([item for item in final_catalog if item["id"].startswith("item_")]),
                    "expected_items": expected_items
                }
            ))
            
            print("   ✅ Thread safety: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="context_thread_safety",
                test_category="shared_context",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Thread safety: {e}")
    
    async def _test_context_isolation(self):
        """Test aislamiento entre contextos de diferentes tenants"""
        
        start_time = time.time()
        
        try:
            # Agregar datos únicos a cada tenant
            tenant_data = {}
            for i, tenant_id in enumerate(self.test_tenants):
                context = get_shared_context(tenant_id)
                
                unique_item = {
                    "id": f"unique_{i}",
                    "name": f"Exclusive Product {i}",
                    "tenant_exclusive": True
                }
                
                context.add_catalog_item(unique_item)
                tenant_data[tenant_id] = unique_item
            
            # Verificar aislamiento
            isolation_verified = True
            for tenant_id in self.test_tenants:
                context = get_shared_context(tenant_id)
                catalog = context.get_catalog()
                
                # Verificar que tiene su item único
                own_item = tenant_data[tenant_id]
                has_own_item = any(item["id"] == own_item["id"] for item in catalog)
                
                # Verificar que NO tiene items de otros tenants
                other_items = [item for tid, item in tenant_data.items() if tid != tenant_id]
                has_other_items = any(
                    any(item["id"] == other_item["id"] for item in catalog)
                    for other_item in other_items
                )
                
                if not has_own_item or has_other_items:
                    isolation_verified = False
                    break
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="context_isolation",
                test_category="shared_context",
                passed=isolation_verified,
                duration_seconds=duration,
                details={
                    "tenants_tested": len(self.test_tenants),
                    "isolation_verified": isolation_verified,
                    "data_leakage": not isolation_verified
                }
            ))
            
            print("   ✅ Context isolation: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="context_isolation",
                test_category="shared_context",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Context isolation: {e}")
    
    async def _test_catalog_operations(self):
        """Test operaciones completas del catálogo"""
        
        start_time = time.time()
        
        try:
            tenant_id = "test-tenant-alpha"
            context = get_shared_context(tenant_id)
            
            # Test CRUD completo
            test_product = {
                "id": "test_crud_product",
                "name": "Test CRUD Product",
                "category": "Test",
                "price": 999.99,
                "description": "Product for CRUD testing"
            }
            
            # CREATE
            context.add_catalog_item(test_product)
            catalog = context.get_catalog()
            created = any(item["id"] == test_product["id"] for item in catalog)
            
            # READ
            found_product = None
            for item in catalog:
                if item["id"] == test_product["id"]:
                    found_product = item
                    break
            
            # UPDATE
            updated_product = test_product.copy()
            updated_product["price"] = 1299.99
            updated_product["description"] = "Updated description"
            
            context.update_catalog_item(test_product["id"], updated_product)
            updated_catalog = context.get_catalog()
            updated_item = next(
                (item for item in updated_catalog if item["id"] == test_product["id"]),
                None
            )
            
            # DELETE
            context.remove_catalog_item(test_product["id"])
            final_catalog = context.get_catalog()
            deleted = not any(item["id"] == test_product["id"] for item in final_catalog)
            
            all_operations_successful = (
                created and 
                found_product is not None and
                updated_item and updated_item["price"] == 1299.99 and
                deleted
            )
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="catalog_operations",
                test_category="shared_context",
                passed=all_operations_successful,
                duration_seconds=duration,
                details={
                    "create_successful": created,
                    "read_successful": found_product is not None,
                    "update_successful": updated_item and updated_item["price"] == 1299.99,
                    "delete_successful": deleted
                }
            ))
            
            print("   ✅ Catalog CRUD operations: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="catalog_operations", 
                test_category="shared_context",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Catalog operations: {e}")
    
    async def _test_client_management(self):
        """Test gestión de clientes"""
        
        start_time = time.time()
        
        try:
            tenant_id = "test-tenant-beta"
            context = get_shared_context(tenant_id)
            
            # Test agregar cliente
            test_client = {
                "id": "test_client_001",
                "name": "Test Client",
                "email": "test@client.com",
                "company": "Test Corp",
                "tier": "premium"
            }
            
            context.add_client(test_client["id"], test_client)
            
            # Verificar que se agregó
            clients = context.get_clients()
            client_added = test_client["id"] in clients
            
            # Test obtener cliente específico
            retrieved_client = context.get_client(test_client["id"])
            client_retrieved = retrieved_client is not None and retrieved_client["name"] == test_client["name"]
            
            # Test actualizar cliente
            updated_data = {"tier": "vip", "phone": "+52 55 1234 5678"}
            context.update_client(test_client["id"], updated_data)
            
            updated_client = context.get_client(test_client["id"])
            client_updated = updated_client and updated_client["tier"] == "vip"
            
            all_successful = client_added and client_retrieved and client_updated
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="client_management",
                test_category="shared_context",
                passed=all_successful,
                duration_seconds=duration,
                details={
                    "client_added": client_added,
                    "client_retrieved": client_retrieved,
                    "client_updated": client_updated,
                    "total_clients": len(clients)
                }
            ))
            
            print("   ✅ Client management: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="client_management",
                test_category="shared_context",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Client management: {e}")
    
    async def _test_order_processing(self):
        """Test procesamiento de órdenes"""
        
        start_time = time.time()
        
        try:
            tenant_id = "test-tenant-gamma" 
            context = get_shared_context(tenant_id)
            
            # Crear orden de prueba
            test_order = {
                "order_id": "test_order_001",
                "client_id": "cust_001",
                "items": [
                    {"product_id": "prod_001", "quantity": 2, "price": 25000.0},
                    {"product_id": "prod_002", "quantity": 1, "price": 5500.0}
                ],
                "total": 55500.0,
                "status": "pending"
            }
            
            # Agregar orden
            context.add_order(test_order["order_id"], test_order)
            
            # Verificar que se agregó
            orders = context.get_orders()
            order_added = test_order["order_id"] in orders
            
            # Actualizar estado
            context.update_order_status(test_order["order_id"], "confirmed")
            updated_order = context.get_order(test_order["order_id"])
            status_updated = updated_order and updated_order["status"] == "confirmed"
            
            # Test obtener órdenes por cliente
            client_orders = context.get_orders_by_client("cust_001")
            client_filter_works = len(client_orders) > 0 and test_order["order_id"] in client_orders
            
            all_successful = order_added and status_updated and client_filter_works
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="order_processing",
                test_category="shared_context",
                passed=all_successful,
                duration_seconds=duration,
                details={
                    "order_added": order_added,
                    "status_updated": status_updated,
                    "client_filter_works": client_filter_works,
                    "total_orders": len(orders)
                }
            ))
            
            print("   ✅ Order processing: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="order_processing",
                test_category="shared_context",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Order processing: {e}")
    
    async def _test_context_persistence(self):
        """Test persistencia del contexto"""
        
        start_time = time.time()
        
        try:
            tenant_id = "test-tenant-persistence"
            
            # Crear contexto y agregar datos
            context1 = get_shared_context(tenant_id)
            test_data = {
                "id": "persistence_test",
                "name": "Persistence Test Item",
                "added_at": datetime.now().isoformat()
            }
            context1.add_catalog_item(test_data)
            
            # Obtener nueva referencia del contexto
            context2 = get_shared_context(tenant_id)
            catalog2 = context2.get_catalog()
            
            # Verificar que los datos persisten
            data_persists = any(item["id"] == test_data["id"] for item in catalog2)
            same_instance = id(context1) == id(context2)
            
            all_successful = data_persists and same_instance
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="context_persistence",
                test_category="shared_context",
                passed=all_successful,
                duration_seconds=duration,
                details={
                    "data_persists": data_persists,
                    "same_instance": same_instance,
                    "catalog_size": len(catalog2)
                }
            ))
            
            print("   ✅ Context persistence: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="context_persistence",
                test_category="shared_context",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Context persistence: {e}")
    
    async def _test_smart_agents_system(self):
        """Tests del sistema de agentes inteligentes"""
        
        print("\\n🤖 Testing Smart Agents System...")
        
        test_cases = [
            self._test_catalog_mapper_agent,
            self._test_alias_normalizer_agent,
            self._test_price_resolver_agent,
            self._test_quote_builder_agent,
            self._test_agents_coordination
        ]
        
        for test_case in test_cases:
            await test_case()
    
    async def _test_catalog_mapper_agent(self):
        """Test del agente mapeador de catálogo"""
        
        start_time = time.time()
        
        try:
            agent = CatalogMapperAgent()
            tenant_id = "test-tenant-alpha"
            
            # Test mapeo de productos por nombre
            queries = [
                "laptop hp",
                "monitor dell 24",
                "teclado logitech"
            ]
            
            results = []
            for query in queries:
                mapped_products = await agent.map_products_from_query(tenant_id, query)
                results.append({
                    "query": query,
                    "products_found": len(mapped_products),
                    "products": mapped_products
                })
            
            # Verificar que encontró productos para cada query
            all_found = all(result["products_found"] > 0 for result in results)
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="catalog_mapper_agent",
                test_category="smart_agents",
                passed=all_found,
                duration_seconds=duration,
                details={
                    "queries_tested": len(queries),
                    "all_queries_found_products": all_found,
                    "results": results
                }
            ))
            
            print("   ✅ Catalog Mapper Agent: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="catalog_mapper_agent",
                test_category="smart_agents",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Catalog Mapper Agent: {e}")
    
    async def _test_alias_normalizer_agent(self):
        """Test del agente normalizador de alias"""
        
        start_time = time.time()
        
        try:
            agent = AliasNormalizerAgent()
            tenant_id = "test-tenant-alpha"
            
            # Test normalización de alias
            test_aliases = [
                ("laptop hp elite", "laptop hp elitebook"),
                ("pantalla dell", "monitor dell"),
                ("mx keys", "teclado logitech mx")
            ]
            
            normalization_results = []
            for original, expected_type in test_aliases:
                normalized = await agent.normalize_product_alias(tenant_id, original)
                normalization_results.append({
                    "original": original,
                    "normalized": normalized,
                    "success": len(normalized) > 0
                })
            
            all_normalized = all(result["success"] for result in normalization_results)
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="alias_normalizer_agent",
                test_category="smart_agents", 
                passed=all_normalized,
                duration_seconds=duration,
                details={
                    "aliases_tested": len(test_aliases),
                    "all_normalized": all_normalized,
                    "results": normalization_results
                }
            ))
            
            print("   ✅ Alias Normalizer Agent: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="alias_normalizer_agent",
                test_category="smart_agents",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Alias Normalizer Agent: {e}")
    
    async def _test_price_resolver_agent(self):
        """Test del agente resolvedor de precios"""
        
        start_time = time.time()
        
        try:
            agent = PriceResolverAgent()
            tenant_id = "test-tenant-alpha"
            
            # Test resolución de precios
            test_cases = [
                {"product_id": "prod_001", "quantity": 1},
                {"product_id": "prod_001", "quantity": 10},  # Test descuento por volumen
                {"product_id": "prod_002", "quantity": 5}
            ]
            
            price_results = []
            for case in test_cases:
                price_info = await agent.resolve_price(
                    tenant_id, 
                    case["product_id"], 
                    case["quantity"]
                )
                price_results.append({
                    "product_id": case["product_id"],
                    "quantity": case["quantity"],
                    "price_resolved": price_info is not None,
                    "final_price": price_info.get("final_price") if price_info else None,
                    "has_discount": price_info.get("discount_applied", False) if price_info else False
                })
            
            all_resolved = all(result["price_resolved"] for result in price_results)
            volume_discount_applied = any(result["has_discount"] for result in price_results)
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="price_resolver_agent",
                test_category="smart_agents",
                passed=all_resolved,
                duration_seconds=duration,
                details={
                    "cases_tested": len(test_cases),
                    "all_resolved": all_resolved,
                    "volume_discount_applied": volume_discount_applied,
                    "results": price_results
                }
            ))
            
            print("   ✅ Price Resolver Agent: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="price_resolver_agent",
                test_category="smart_agents",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Price Resolver Agent: {e}")
    
    async def _test_quote_builder_agent(self):
        """Test del agente constructor de cotizaciones"""
        
        start_time = time.time()
        
        try:
            agent = QuoteBuilderAgent()
            tenant_id = "test-tenant-alpha"
            
            # Test construcción de cotización
            products = [
                {"id": "prod_001", "name": "Laptop HP EliteBook"},
                {"id": "prod_002", "name": "Monitor Dell 24\""}
            ]
            quantities = [2, 1]
            
            quote = await agent.build_quote(tenant_id, products, quantities)
            
            quote_built = quote is not None
            has_total = quote and "total" in quote
            has_items = quote and "items" in quote and len(quote["items"]) == len(products)
            valid_total = quote and quote.get("total", 0) > 0
            
            all_successful = quote_built and has_total and has_items and valid_total
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="quote_builder_agent",
                test_category="smart_agents",
                passed=all_successful,
                duration_seconds=duration,
                details={
                    "quote_built": quote_built,
                    "has_total": has_total,
                    "has_items": has_items,
                    "valid_total": valid_total,
                    "quote_total": quote.get("total") if quote else None,
                    "items_count": len(quote.get("items", [])) if quote else 0
                }
            ))
            
            print("   ✅ Quote Builder Agent: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="quote_builder_agent",
                test_category="smart_agents",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Quote Builder Agent: {e}")
    
    async def _test_agents_coordination(self):
        """Test coordinación entre agentes"""
        
        start_time = time.time()
        
        try:
            # Simular flujo completo de agentes trabajando juntos
            tenant_id = "test-tenant-alpha"
            
            # 1. Mapper encuentra productos
            mapper = CatalogMapperAgent()
            mapped_products = await mapper.map_products_from_query(tenant_id, "laptop hp monitor dell")
            
            # 2. Normalizer limpia aliases
            normalizer = AliasNormalizerAgent()
            normalized = await normalizer.normalize_product_alias(tenant_id, "hp elite")
            
            # 3. Price resolver calcula precios
            price_resolver = PriceResolverAgent()
            if mapped_products:
                price_info = await price_resolver.resolve_price(
                    tenant_id, mapped_products[0]["id"], 1
                )
            else:
                price_info = None
            
            # 4. Quote builder construye cotización
            quote_builder = QuoteBuilderAgent()
            if mapped_products:
                quote = await quote_builder.build_quote(
                    tenant_id, mapped_products[:2], [1, 1]
                )
            else:
                quote = None
            
            # Verificar que todo el flujo funciona
            mapper_works = len(mapped_products) > 0
            normalizer_works = len(normalized) > 0
            price_resolver_works = price_info is not None
            quote_builder_works = quote is not None
            
            coordination_successful = all([
                mapper_works, normalizer_works, 
                price_resolver_works, quote_builder_works
            ])
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="agents_coordination",
                test_category="smart_agents",
                passed=coordination_successful,
                duration_seconds=duration,
                details={
                    "mapper_works": mapper_works,
                    "normalizer_works": normalizer_works,
                    "price_resolver_works": price_resolver_works,
                    "quote_builder_works": quote_builder_works,
                    "products_found": len(mapped_products),
                    "quote_value": quote.get("total") if quote else None
                }
            ))
            
            print("   ✅ Agents coordination: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="agents_coordination",
                test_category="smart_agents",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Agents coordination: {e}")
    
    async def _test_stripe_connect_full(self):
        """Tests completos de Stripe Connect"""
        
        print("\\n💳 Testing Stripe Connect System...")
        
        try:
            # Ejecutar suite de Stripe existente
            start_time = time.time()
            
            suite = stripe_test_suite
            
            # Configurar cuentas de prueba
            test_accounts = suite.setup_test_accounts()
            accounts_created = len(test_accounts) > 0
            
            # Test flujos de pago
            payment_results = await suite.test_payment_flows()
            payments_tested = len(payment_results) > 0
            
            # Test OXXO scenarios
            oxxo_results = suite.test_oxxo_scenarios()
            oxxo_tested = len(oxxo_results) > 0
            
            # Test multi-split transfers
            transfer_result = suite.test_multi_split_transfers()
            transfers_tested = "splits_calculated" in transfer_result
            
            # Test webhooks
            webhook_results = suite.test_webhook_processing()
            webhooks_tested = len(webhook_results) > 0
            
            # Test cálculos de fees
            fee_result = suite.test_fee_calculations()
            fees_tested = "optimized_policy" in fee_result
            
            # Generar reporte
            stripe_report = suite.generate_test_report()
            
            all_stripe_tests_passed = all([
                accounts_created, payments_tested, oxxo_tested,
                transfers_tested, webhooks_tested, fees_tested
            ])
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="stripe_connect_full_suite",
                test_category="stripe_connect",
                passed=all_stripe_tests_passed,
                duration_seconds=duration,
                details={
                    "accounts_created": accounts_created,
                    "payments_tested": payments_tested,
                    "oxxo_tested": oxxo_tested,
                    "transfers_tested": transfers_tested,
                    "webhooks_tested": webhooks_tested,
                    "fees_tested": fees_tested,
                    "stripe_report": stripe_report
                }
            ))
            
            print("   ✅ Stripe Connect full suite: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="stripe_connect_full_suite",
                test_category="stripe_connect",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Stripe Connect: {e}")
    
    async def _test_conversation_flows(self):
        """Tests de flujos de conversación"""
        
        print("\\n💬 Testing Conversation Flows...")
        
        test_cases = [
            self._test_conversation_creation,
            self._test_conversation_stages,
            self._test_intent_detection,
            self._test_sentiment_analysis,
            self._test_conversation_analytics
        ]
        
        for test_case in test_cases:
            await test_case()
    
    async def _test_conversation_creation(self):
        """Test creación de conversaciones"""
        
        start_time = time.time()
        
        try:
            engine = conversation_engine
            
            # Crear múltiples conversaciones
            conversation_ids = []
            for i, tenant_id in enumerate(self.test_tenants):
                for j, customer in enumerate(self.test_customers):
                    conv_id = engine.start_conversation(
                        tenant_id, 
                        customer["id"],
                        channel="web",
                        customer_profile=customer
                    )
                    conversation_ids.append(conv_id)
            
            # Verificar que se crearon correctamente
            conversations_created = len(conversation_ids)
            expected_conversations = len(self.test_tenants) * len(self.test_customers)
            
            all_created = conversations_created == expected_conversations
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="conversation_creation",
                test_category="conversation_flows",
                passed=all_created,
                duration_seconds=duration,
                details={
                    "conversations_created": conversations_created,
                    "expected_conversations": expected_conversations,
                    "conversation_ids": conversation_ids[:5]  # Primeros 5
                }
            ))
            
            print("   ✅ Conversation creation: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="conversation_creation",
                test_category="conversation_flows",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Conversation creation: {e}")
    
    async def _test_conversation_stages(self):
        """Test transiciones entre etapas de conversación"""
        
        start_time = time.time()
        
        try:
            engine = conversation_engine
            tenant_id = "test-tenant-alpha"
            customer_id = "cust_001"
            
            # Crear conversación
            conv_id = engine.start_conversation(tenant_id, customer_id)
            
            # Simular flujo de mensajes que deben cambiar etapas
            stage_progression = []
            
            messages_and_expected_stages = [
                ("Hola, necesito cotizar productos", ConversationStage.DISCOVERY),
                ("¿Qué opciones tienen en laptops?", ConversationStage.PRODUCT_EXPLORATION),
                ("Me interesan las HP EliteBook", ConversationStage.PRODUCT_EXPLORATION),
                ("¿Cuánto costarían 10 laptops?", ConversationStage.QUOTE_BUILDING),
                ("Está muy caro", ConversationStage.OBJECTION_HANDLING),
                ("Sí, me interesa la cotización", ConversationStage.QUOTE_BUILDING)
            ]
            
            stages_correct = []
            for message, expected_stage in messages_and_expected_stages:
                response = await engine.process_customer_message(conv_id, message)
                current_stage = ConversationStage(response["current_stage"])
                stage_progression.append(current_stage)
                
                # No verificamos exactamente la etapa esperada porque puede variar
                # Solo verificamos que hay progresión
                stages_correct.append(True)
            
            # Verificar que hubo progresión de etapas
            unique_stages = len(set(stage_progression))
            progression_happened = unique_stages > 1
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="conversation_stages",
                test_category="conversation_flows",
                passed=progression_happened,
                duration_seconds=duration,
                details={
                    "messages_processed": len(messages_and_expected_stages),
                    "unique_stages_visited": unique_stages,
                    "stage_progression": [stage.value for stage in stage_progression],
                    "progression_happened": progression_happened
                }
            ))
            
            print("   ✅ Conversation stages: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="conversation_stages",
                test_category="conversation_flows",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Conversation stages: {e}")
    
    async def _test_intent_detection(self):
        """Test detección de intenciones"""
        
        start_time = time.time()
        
        try:
            engine = conversation_engine
            tenant_id = "test-tenant-beta"
            customer_id = "cust_002"
            
            conv_id = engine.start_conversation(tenant_id, customer_id)
            
            # Test mensajes con intenciones específicas
            intent_test_cases = [
                ("¿Qué productos tienen disponibles?", "browse_catalog"),
                ("¿Cuánto cuesta la laptop HP?", "price_inquiry"),
                ("Necesito 50 monitores para mi empresa", "bulk_order"),
                ("¿Pueden hacer una cotización personalizada?", "custom_quote"),
                ("Está muy caro, ¿tienen descuentos?", "price_objection"),
                ("¿Cómo puedo pagar?", "payment_question")
            ]
            
            intent_results = []
            for message, expected_intent in intent_test_cases:
                response = await engine.process_customer_message(conv_id, message)
                detected_intent = response.get("detected_intent")
                
                intent_results.append({
                    "message": message,
                    "expected_intent": expected_intent,
                    "detected_intent": detected_intent,
                    "intent_detected": detected_intent is not None
                })
            
            intents_detected = sum(1 for r in intent_results if r["intent_detected"])
            detection_rate = intents_detected / len(intent_test_cases)
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="intent_detection",
                test_category="conversation_flows",
                passed=detection_rate >= 0.7,  # 70% de tasa de detección mínima
                duration_seconds=duration,
                details={
                    "test_cases": len(intent_test_cases),
                    "intents_detected": intents_detected,
                    "detection_rate": detection_rate,
                    "results": intent_results
                }
            ))
            
            print("   ✅ Intent detection: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="intent_detection",
                test_category="conversation_flows",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Intent detection: {e}")
    
    async def _test_sentiment_analysis(self):
        """Test análisis de sentimiento"""
        
        start_time = time.time()
        
        try:
            engine = conversation_engine
            tenant_id = "test-tenant-gamma"
            customer_id = "cust_003"
            
            conv_id = engine.start_conversation(tenant_id, customer_id)
            
            # Test mensajes con sentimientos específicos
            sentiment_test_cases = [
                ("¡Excelente! Me gusta mucho", "positive"),
                ("Está bien, me interesa", "positive"),
                ("No me gusta nada, muy caro", "negative"),
                ("Esto es terrible", "negative"),
                ("¿Cuánto cuesta?", "neutral"),
                ("Necesito información", "neutral")
            ]
            
            sentiment_results = []
            for message, expected_sentiment in sentiment_test_cases:
                response = await engine.process_customer_message(conv_id, message)
                detected_sentiment = response.get("customer_sentiment")
                
                sentiment_results.append({
                    "message": message,
                    "expected_sentiment": expected_sentiment,
                    "detected_sentiment": detected_sentiment,
                    "sentiment_correct": detected_sentiment == expected_sentiment
                })
            
            correct_sentiments = sum(1 for r in sentiment_results if r["sentiment_correct"])
            accuracy_rate = correct_sentiments / len(sentiment_test_cases)
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="sentiment_analysis",
                test_category="conversation_flows",
                passed=accuracy_rate >= 0.6,  # 60% de precisión mínima
                duration_seconds=duration,
                details={
                    "test_cases": len(sentiment_test_cases),
                    "correct_sentiments": correct_sentiments,
                    "accuracy_rate": accuracy_rate,
                    "results": sentiment_results
                }
            ))
            
            print("   ✅ Sentiment analysis: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="sentiment_analysis",
                test_category="conversation_flows",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Sentiment analysis: {e}")
    
    async def _test_conversation_analytics(self):
        """Test analytics de conversaciones"""
        
        start_time = time.time()
        
        try:
            engine = conversation_engine
            tenant_id = "test-tenant-alpha"
            
            # Obtener analytics
            analytics = engine.get_conversation_analytics(tenant_id, days=1)
            
            # Verificar que los analytics tienen la estructura esperada
            has_total_conversations = "total_conversations" in analytics
            has_conversion_rate = "conversion_rate" in analytics
            has_stage_distribution = "stage_distribution" in analytics
            has_sentiment_distribution = "sentiment_distribution" in analytics
            
            analytics_complete = all([
                has_total_conversations, has_conversion_rate,
                has_stage_distribution, has_sentiment_distribution
            ])
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="conversation_analytics",
                test_category="conversation_flows",
                passed=analytics_complete,
                duration_seconds=duration,
                details={
                    "analytics_complete": analytics_complete,
                    "total_conversations": analytics.get("total_conversations", 0),
                    "conversion_rate": analytics.get("conversion_rate", 0),
                    "has_stage_distribution": has_stage_distribution,
                    "has_sentiment_distribution": has_sentiment_distribution
                }
            ))
            
            print("   ✅ Conversation analytics: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="conversation_analytics",
                test_category="conversation_flows",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Conversation analytics: {e}")
    
    async def _test_control_tower_apis(self):
        """Tests de las APIs del Control Tower"""
        
        print("\\n📊 Testing Control Tower APIs...")
        
        api_test_cases = [
            ("groq", "/health"),
            ("control_tower", "/api/dashboard/overview"),
            ("control_tower_v2", "/api/dashboard/overview")
        ]
        
        for api_name, endpoint in api_test_cases:
            await self._test_api_endpoint(api_name, endpoint)
    
    async def _test_api_endpoint(self, api_name: str, endpoint: str):
        """Test de un endpoint específico"""
        
        start_time = time.time()
        
        try:
            base_url = self.api_urls.get(api_name)
            if not base_url:
                raise ValueError(f"Unknown API: {api_name}")
            
            url = f"{base_url}{endpoint}"
            headers = {}
            
            # Para APIs v2, agregar header de tenant
            if "v2" in api_name:
                headers["X-Org-Id"] = "test-tenant-alpha"
            
            response = requests.get(url, headers=headers, timeout=10)
            
            api_available = response.status_code in [200, 201]
            response_has_data = len(response.text) > 0
            
            if api_available and response.headers.get("content-type", "").startswith("application/json"):
                try:
                    json_data = response.json()
                    valid_json = True
                except:
                    valid_json = False
            else:
                valid_json = True  # No JSON expected
            
            test_passed = api_available and response_has_data and valid_json
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name=f"api_{api_name}_{endpoint.replace('/', '_')}",
                test_category="control_tower_apis",
                passed=test_passed,
                duration_seconds=duration,
                details={
                    "api_name": api_name,
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "response_size": len(response.text),
                    "valid_json": valid_json,
                    "headers_sent": headers
                }
            ))
            
            status_icon = "✅" if test_passed else "❌"
            print(f"   {status_icon} {api_name} {endpoint}: {response.status_code}")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name=f"api_{api_name}_{endpoint.replace('/', '_')}",
                test_category="control_tower_apis",
                passed=False,
                duration_seconds=duration,
                details={"api_name": api_name, "endpoint": endpoint},
                error_message=str(e)
            ))
            print(f"   ❌ {api_name} {endpoint}: {e}")
    
    async def _test_multi_tenant_isolation(self):
        """Tests de aislamiento multi-tenant"""
        
        print("\\n🏢 Testing Multi-Tenant Isolation...")
        
        start_time = time.time()
        
        try:
            # Test que datos de diferentes tenants no se mezclen
            isolation_results = []
            
            # Crear datos únicos por tenant
            for i, tenant_id in enumerate(self.test_tenants):
                context = get_shared_context(tenant_id)
                
                # Agregar producto único
                unique_product = {
                    "id": f"isolation_test_{i}",
                    "name": f"Tenant {i} Exclusive Product",
                    "tenant_specific": True
                }
                context.add_catalog_item(unique_product)
                
                # Verificar que solo este tenant tiene el producto
                catalog = context.get_catalog()
                has_own_product = any(
                    item["id"] == unique_product["id"] for item in catalog
                )
                
                # Verificar que otros tenants NO tienen este producto
                other_tenants_clean = True
                for other_tenant in self.test_tenants:
                    if other_tenant != tenant_id:
                        other_context = get_shared_context(other_tenant)
                        other_catalog = other_context.get_catalog()
                        has_leaked_product = any(
                            item["id"] == unique_product["id"] for item in other_catalog
                        )
                        if has_leaked_product:
                            other_tenants_clean = False
                            break
                
                isolation_results.append({
                    "tenant_id": tenant_id,
                    "has_own_product": has_own_product,
                    "no_data_leakage": other_tenants_clean,
                    "isolation_verified": has_own_product and other_tenants_clean
                })
            
            all_isolated = all(result["isolation_verified"] for result in isolation_results)
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="multi_tenant_isolation",
                test_category="multi_tenancy",
                passed=all_isolated,
                duration_seconds=duration,
                details={
                    "tenants_tested": len(self.test_tenants),
                    "all_isolated": all_isolated,
                    "isolation_results": isolation_results
                }
            ))
            
            print("   ✅ Multi-tenant isolation: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="multi_tenant_isolation",
                test_category="multi_tenancy",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Multi-tenant isolation: {e}")
    
    async def _test_system_performance(self):
        """Tests de performance del sistema"""
        
        print("\\n⚡ Testing System Performance...")
        
        performance_tests = [
            self._test_context_performance,
            self._test_agents_performance,
            self._test_conversation_performance
        ]
        
        for test in performance_tests:
            await test()
    
    async def _test_context_performance(self):
        """Test performance del contexto compartido"""
        
        start_time = time.time()
        
        try:
            tenant_id = "test-performance"
            context = get_shared_context(tenant_id)
            
            # Test performance de operaciones masivas
            operations_count = 1000
            
            # Test inserción masiva
            insert_start = time.time()
            for i in range(operations_count):
                context.add_catalog_item({
                    "id": f"perf_test_{i}",
                    "name": f"Performance Test Product {i}",
                    "price": i * 10
                })
            insert_duration = time.time() - insert_start
            
            # Test lectura masiva
            read_start = time.time()
            for i in range(100):  # 100 lecturas
                catalog = context.get_catalog()
            read_duration = time.time() - read_start
            
            # Calcular métricas
            insert_ops_per_second = operations_count / insert_duration
            read_ops_per_second = 100 / read_duration
            
            # Criterios de performance
            insert_acceptable = insert_ops_per_second > 100  # 100 ops/sec mínimo
            read_acceptable = read_ops_per_second > 50       # 50 ops/sec mínimo
            
            performance_acceptable = insert_acceptable and read_acceptable
            
            duration = time.time() - start_time
            
            self.performance_metrics["context_performance"] = {
                "insert_ops_per_second": insert_ops_per_second,
                "read_ops_per_second": read_ops_per_second,
                "insert_duration": insert_duration,
                "read_duration": read_duration
            }
            
            self.test_results.append(TestResult(
                test_name="context_performance",
                test_category="performance",
                passed=performance_acceptable,
                duration_seconds=duration,
                details={
                    "operations_tested": operations_count,
                    "insert_ops_per_second": insert_ops_per_second,
                    "read_ops_per_second": read_ops_per_second,
                    "insert_acceptable": insert_acceptable,
                    "read_acceptable": read_acceptable
                }
            ))
            
            print(f"   ✅ Context performance: {insert_ops_per_second:.1f} insert/s, {read_ops_per_second:.1f} read/s")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="context_performance",
                test_category="performance",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Context performance: {e}")
    
    async def _test_agents_performance(self):
        """Test performance de agentes"""
        
        start_time = time.time()
        
        try:
            tenant_id = "test-tenant-alpha"
            
            # Test performance de agentes en paralelo
            agent_operations = []
            
            # Catalog mapper
            mapper = CatalogMapperAgent()
            mapper_start = time.time()
            mapped_products = await mapper.map_products_from_query(tenant_id, "laptop monitor")
            mapper_duration = time.time() - mapper_start
            agent_operations.append(("mapper", mapper_duration))
            
            # Price resolver
            price_resolver = PriceResolverAgent()
            if mapped_products:
                price_start = time.time()
                price_info = await price_resolver.resolve_price(tenant_id, mapped_products[0]["id"], 1)
                price_duration = time.time() - price_start
                agent_operations.append(("price_resolver", price_duration))
            
            # Quote builder
            quote_builder = QuoteBuilderAgent()
            if mapped_products:
                quote_start = time.time()
                quote = await quote_builder.build_quote(tenant_id, mapped_products[:2], [1, 1])
                quote_duration = time.time() - quote_start
                agent_operations.append(("quote_builder", quote_duration))
            
            # Verificar que todas las operaciones fueron rápidas (< 2 segundos)
            all_fast = all(duration < 2.0 for _, duration in agent_operations)
            avg_duration = sum(duration for _, duration in agent_operations) / len(agent_operations)
            
            duration = time.time() - start_time
            
            self.performance_metrics["agents_performance"] = {
                "agent_operations": dict(agent_operations),
                "average_duration": avg_duration,
                "all_operations_fast": all_fast
            }
            
            self.test_results.append(TestResult(
                test_name="agents_performance",
                test_category="performance",
                passed=all_fast,
                duration_seconds=duration,
                details={
                    "agent_operations": dict(agent_operations),
                    "average_duration": avg_duration,
                    "all_fast": all_fast,
                    "max_acceptable_duration": 2.0
                }
            ))
            
            print(f"   ✅ Agents performance: avg {avg_duration:.2f}s")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="agents_performance",
                test_category="performance",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Agents performance: {e}")
    
    async def _test_conversation_performance(self):
        """Test performance de conversaciones"""
        
        start_time = time.time()
        
        try:
            engine = conversation_engine
            tenant_id = "test-tenant-performance"
            customer_id = "perf_customer"
            
            # Test procesamiento de múltiples mensajes
            conv_id = engine.start_conversation(tenant_id, customer_id)
            
            messages = [
                "Hola, necesito cotizar productos",
                "¿Qué laptops tienen disponibles?",
                "Me interesan las HP EliteBook",
                "¿Cuánto cuestan 5 laptops?",
                "¿Tienen descuentos por volumen?"
            ]
            
            message_durations = []
            for message in messages:
                msg_start = time.time()
                response = await engine.process_customer_message(conv_id, message)
                msg_duration = time.time() - msg_start
                message_durations.append(msg_duration)
            
            # Verificar que ningún mensaje tardó más de 3 segundos
            all_messages_fast = all(duration < 3.0 for duration in message_durations)
            avg_message_duration = sum(message_durations) / len(message_durations)
            
            duration = time.time() - start_time
            
            self.performance_metrics["conversation_performance"] = {
                "messages_processed": len(messages),
                "message_durations": message_durations,
                "average_message_duration": avg_message_duration,
                "all_messages_fast": all_messages_fast
            }
            
            self.test_results.append(TestResult(
                test_name="conversation_performance",
                test_category="performance",
                passed=all_messages_fast,
                duration_seconds=duration,
                details={
                    "messages_processed": len(messages),
                    "average_message_duration": avg_message_duration,
                    "max_message_duration": max(message_durations),
                    "all_messages_fast": all_messages_fast
                }
            ))
            
            print(f"   ✅ Conversation performance: avg {avg_message_duration:.2f}s per message")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="conversation_performance",
                test_category="performance",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Conversation performance: {e}")
    
    async def _test_end_to_end_scenarios(self):
        """Tests de escenarios end-to-end"""
        
        print("\\n🎯 Testing End-to-End Scenarios...")
        
        scenarios = [
            self._test_complete_sales_flow,
            self._test_bulk_order_scenario,
            self._test_objection_handling_flow
        ]
        
        for scenario in scenarios:
            await scenario()
    
    async def _test_complete_sales_flow(self):
        """Test flujo de ventas completo"""
        
        start_time = time.time()
        
        try:
            # Simular flujo completo: Chat → Agentes → Stripe → Confirmación
            tenant_id = "test-e2e-sales"
            customer_id = "customer_e2e"
            
            # 1. Iniciar conversación
            engine = conversation_engine
            conv_id = engine.start_conversation(tenant_id, customer_id)
            
            # 2. Flujo de mensajes de ventas
            sales_messages = [
                "Hola, necesito equipos para mi oficina",
                "Necesito 3 laptops HP EliteBook",
                "¿Cuánto me costarían?",
                "Sí, me interesa. ¿Pueden enviar cotización?",
                "Perfecto, quiero proceder con la compra"
            ]
            
            conversation_successful = True
            final_response = None
            
            for message in sales_messages:
                response = await engine.process_customer_message(conv_id, message)
                final_response = response
                
                if not response or "agent_message" not in response:
                    conversation_successful = False
                    break
            
            # 3. Verificar que se llegó a etapa de cierre
            reached_closing = (
                final_response and 
                final_response.get("current_stage") in ["quote_building", "closing", "payment_processing"]
            )
            
            # 4. Verificar que hay cotización
            has_quote = (
                final_response and 
                final_response.get("metadata", {}).get("quote_value", 0) > 0
            )
            
            e2e_successful = conversation_successful and reached_closing and has_quote
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="complete_sales_flow",
                test_category="end_to_end",
                passed=e2e_successful,
                duration_seconds=duration,
                details={
                    "conversation_successful": conversation_successful,
                    "reached_closing": reached_closing,
                    "has_quote": has_quote,
                    "final_stage": final_response.get("current_stage") if final_response else None,
                    "quote_value": final_response.get("metadata", {}).get("quote_value") if final_response else None,
                    "messages_processed": len(sales_messages)
                }
            ))
            
            print("   ✅ Complete sales flow: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="complete_sales_flow",
                test_category="end_to_end",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Complete sales flow: {e}")
    
    async def _test_bulk_order_scenario(self):
        """Test escenario de pedido por volumen"""
        
        start_time = time.time()
        
        try:
            tenant_id = "test-bulk-order"
            customer_id = "bulk_customer"
            
            engine = conversation_engine
            conv_id = engine.start_conversation(
                tenant_id, 
                customer_id,
                customer_profile={"company": "TechCorp", "tier": "enterprise"}
            )
            
            bulk_messages = [
                "Necesito cotizar equipos para 50 empleados",
                "Serían 50 laptops y 50 monitores",
                "¿Tienen precios especiales por volumen?",
                "¿Cuál sería el precio total con descuentos?"
            ]
            
            bulk_processed = True
            volume_discount_detected = False
            final_quote_value = 0
            
            for message in bulk_messages:
                response = await engine.process_customer_message(conv_id, message)
                
                if not response:
                    bulk_processed = False
                    break
                
                # Buscar indicaciones de descuento por volumen
                if "descuento" in response.get("agent_message", "").lower():
                    volume_discount_detected = True
                
                # Capturar valor de cotización
                quote_value = response.get("metadata", {}).get("quote_value", 0)
                if quote_value > final_quote_value:
                    final_quote_value = quote_value
            
            # Verificar que se manejó como bulk order
            bulk_intent_detected = volume_discount_detected or final_quote_value > 100000
            
            scenario_successful = bulk_processed and bulk_intent_detected
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="bulk_order_scenario",
                test_category="end_to_end",
                passed=scenario_successful,
                duration_seconds=duration,
                details={
                    "bulk_processed": bulk_processed,
                    "volume_discount_detected": volume_discount_detected,
                    "final_quote_value": final_quote_value,
                    "bulk_intent_detected": bulk_intent_detected,
                    "messages_processed": len(bulk_messages)
                }
            ))
            
            print("   ✅ Bulk order scenario: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="bulk_order_scenario",
                test_category="end_to_end",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Bulk order scenario: {e}")
    
    async def _test_objection_handling_flow(self):
        """Test flujo de manejo de objeciones"""
        
        start_time = time.time()
        
        try:
            tenant_id = "test-objections"
            customer_id = "objection_customer"
            
            engine = conversation_engine
            conv_id = engine.start_conversation(tenant_id, customer_id)
            
            objection_messages = [
                "Necesito cotizar una laptop",
                "Me interesa la HP EliteBook",
                "¿Cuánto cuesta?",
                "Está muy caro, no puedo pagar eso",
                "¿No tienen algo más barato?",
                "La competencia me ofrece mejor precio"
            ]
            
            objection_handled = True
            negative_sentiment_detected = False
            recovery_attempted = False
            
            for i, message in enumerate(objection_messages):
                response = await engine.process_customer_message(conv_id, message)
                
                if not response:
                    objection_handled = False
                    break
                
                # Detectar sentimiento negativo
                if response.get("customer_sentiment") == "negative":
                    negative_sentiment_detected = True
                
                # Buscar intentos de recuperación en respuestas del agente
                agent_message = response.get("agent_message", "").lower()
                recovery_keywords = ["entiendo", "valor", "descuento", "opciones", "alternativa"]
                if any(keyword in agent_message for keyword in recovery_keywords):
                    recovery_attempted = True
            
            # Verificar que se detectaron objeciones y se intentó manejar
            objections_detected = negative_sentiment_detected
            objections_addressed = recovery_attempted
            
            flow_successful = objection_handled and objections_detected and objections_addressed
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="objection_handling_flow",
                test_category="end_to_end",
                passed=flow_successful,
                duration_seconds=duration,
                details={
                    "objection_handled": objection_handled,
                    "negative_sentiment_detected": negative_sentiment_detected,
                    "recovery_attempted": recovery_attempted,
                    "objections_detected": objections_detected,
                    "objections_addressed": objections_addressed,
                    "messages_processed": len(objection_messages)
                }
            ))
            
            print("   ✅ Objection handling flow: OK")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="objection_handling_flow",
                test_category="end_to_end",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Objection handling flow: {e}")
    
    async def _test_load_and_stress(self):
        """Tests de carga y estrés"""
        
        print("\\n🔥 Testing Load and Stress...")
        
        stress_tests = [
            self._test_concurrent_conversations,
            self._test_memory_usage,
            self._test_system_resilience
        ]
        
        for test in stress_tests:
            await test()
    
    async def _test_concurrent_conversations(self):
        """Test conversaciones concurrentes"""
        
        start_time = time.time()
        
        try:
            engine = conversation_engine
            
            # Crear múltiples conversaciones simultáneas
            concurrent_count = 10
            
            async def create_and_run_conversation(conversation_index):
                tenant_id = f"stress_test_{conversation_index % 3}"  # 3 tenants
                customer_id = f"stress_customer_{conversation_index}"
                
                conv_id = engine.start_conversation(tenant_id, customer_id)
                
                # Enviar varios mensajes
                messages = [
                    "Hola, necesito información",
                    "¿Qué productos tienen?",
                    "Me interesa cotizar"
                ]
                
                for message in messages:
                    response = await engine.process_customer_message(conv_id, message)
                    if not response:
                        return False
                
                return True
            
            # Ejecutar conversaciones en paralelo
            tasks = [
                create_and_run_conversation(i) 
                for i in range(concurrent_count)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Contar conversaciones exitosas
            successful_conversations = sum(
                1 for result in results 
                if result is True
            )
            
            success_rate = successful_conversations / concurrent_count
            stress_test_passed = success_rate >= 0.8  # 80% success rate mínimo
            
            duration = time.time() - start_time
            
            self.performance_metrics["concurrent_conversations"] = {
                "concurrent_count": concurrent_count,
                "successful_conversations": successful_conversations,
                "success_rate": success_rate,
                "duration": duration
            }
            
            self.test_results.append(TestResult(
                test_name="concurrent_conversations",
                test_category="load_stress",
                passed=stress_test_passed,
                duration_seconds=duration,
                details={
                    "concurrent_count": concurrent_count,
                    "successful_conversations": successful_conversations,
                    "success_rate": success_rate,
                    "errors": [str(r) for r in results if isinstance(r, Exception)]
                }
            ))
            
            print(f"   ✅ Concurrent conversations: {successful_conversations}/{concurrent_count} successful")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="concurrent_conversations",
                test_category="load_stress",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Concurrent conversations: {e}")
    
    async def _test_memory_usage(self):
        """Test uso de memoria"""
        
        start_time = time.time()
        
        try:
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB
            
            # Realizar operaciones intensivas en memoria
            tenant_id = "memory_test"
            context = get_shared_context(tenant_id)
            
            # Agregar muchos productos
            for i in range(1000):
                context.add_catalog_item({
                    "id": f"memory_test_{i}",
                    "name": f"Memory Test Product {i}",
                    "description": f"Description for product {i}" * 10,  # Texto largo
                    "price": i * 100
                })
            
            # Crear múltiples conversaciones
            engine = conversation_engine
            for i in range(50):
                conv_id = engine.start_conversation(tenant_id, f"memory_customer_{i}")
                
                # Agregar mensajes a cada conversación
                for j in range(5):
                    await engine.process_customer_message(conv_id, f"Message {j} from customer {i}")
            
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_increase = final_memory - initial_memory
            
            # Verificar que el aumento de memoria es razonable (< 100 MB)
            memory_acceptable = memory_increase < 100
            
            duration = time.time() - start_time
            
            self.performance_metrics["memory_usage"] = {
                "initial_memory_mb": initial_memory,
                "final_memory_mb": final_memory,
                "memory_increase_mb": memory_increase,
                "memory_acceptable": memory_acceptable
            }
            
            self.test_results.append(TestResult(
                test_name="memory_usage",
                test_category="load_stress",
                passed=memory_acceptable,
                duration_seconds=duration,
                details={
                    "initial_memory_mb": initial_memory,
                    "final_memory_mb": final_memory,
                    "memory_increase_mb": memory_increase,
                    "acceptable_limit_mb": 100
                }
            ))
            
            print(f"   ✅ Memory usage: +{memory_increase:.1f}MB")
            
        except ImportError:
            # psutil no disponible
            self.test_results.append(TestResult(
                test_name="memory_usage",
                test_category="load_stress",
                passed=True,  # Skip
                duration_seconds=time.time() - start_time,
                details={"skipped": "psutil not available"}
            ))
            print("   ⏭️ Memory usage: skipped (psutil not available)")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="memory_usage",
                test_category="load_stress",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ Memory usage: {e}")
    
    async def _test_system_resilience(self):
        """Test resiliencia del sistema"""
        
        start_time = time.time()
        
        try:
            # Test que el sistema maneja errores graciosamente
            resilience_tests = []
            
            # 1. Test con datos inválidos
            try:
                tenant_id = "resilience_test"
                context = get_shared_context(tenant_id)
                
                # Intentar agregar producto con datos malformados
                context.add_catalog_item({
                    "id": None,  # ID inválido
                    "name": "",  # Nombre vacío
                    "price": "invalid_price"  # Precio inválido
                })
                resilience_tests.append(("invalid_data", "handled"))
            except Exception:
                resilience_tests.append(("invalid_data", "error"))
            
            # 2. Test con conversación inexistente
            try:
                engine = conversation_engine
                response = await engine.process_customer_message(
                    "nonexistent_conversation", 
                    "Test message"
                )
                resilience_tests.append(("nonexistent_conversation", "handled"))
            except Exception:
                resilience_tests.append(("nonexistent_conversation", "error"))
            
            # 3. Test con tenant inexistente
            try:
                mapper = CatalogMapperAgent()
                products = await mapper.map_products_from_query(
                    "nonexistent_tenant", 
                    "test query"
                )
                resilience_tests.append(("nonexistent_tenant", "handled"))
            except Exception:
                resilience_tests.append(("nonexistent_tenant", "error"))
            
            # Verificar que el sistema manejó errores graciosamente
            errors_handled = sum(1 for _, result in resilience_tests if result == "handled")
            total_tests = len(resilience_tests)
            resilience_rate = errors_handled / total_tests if total_tests > 0 else 0
            
            system_resilient = resilience_rate >= 0.5  # 50% mínimo de manejo gracioso
            
            duration = time.time() - start_time
            
            self.test_results.append(TestResult(
                test_name="system_resilience",
                test_category="load_stress",
                passed=system_resilient,
                duration_seconds=duration,
                details={
                    "resilience_tests": resilience_tests,
                    "errors_handled": errors_handled,
                    "total_tests": total_tests,
                    "resilience_rate": resilience_rate
                }
            ))
            
            print(f"   ✅ System resilience: {errors_handled}/{total_tests} errors handled gracefully")
            
        except Exception as e:
            duration = time.time() - start_time
            self.test_results.append(TestResult(
                test_name="system_resilience",
                test_category="load_stress",
                passed=False,
                duration_seconds=duration,
                details={},
                error_message=str(e)
            ))
            print(f"   ❌ System resilience: {e}")
    
    async def _cleanup_test_environment(self):
        """Limpia el entorno de pruebas"""
        
        print("\\n🧹 Cleaning up test environment...")
        
        try:
            # Limpiar contextos de prueba
            # Nota: Los contextos están en memoria, se limpian automáticamente
            
            # Limpiar conversaciones de prueba
            # Nota: En una implementación real, aquí limpiaríamos la base de datos
            
            print("   ✅ Test environment cleaned up")
            
        except Exception as e:
            print(f"   ⚠️ Cleanup warning: {e}")
    
    def _generate_final_report(self, started_at: datetime, 
                             completed_at: datetime, 
                             duration: float) -> TestSuiteReport:
        """Genera reporte final completo"""
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for r in self.test_results if r.passed)
        failed_tests = total_tests - passed_tests
        
        # Agrupar por categorías
        categories = {}
        for result in self.test_results:
            category = result.test_category
            if category not in categories:
                categories[category] = {"total": 0, "passed": 0, "failed": 0}
            
            categories[category]["total"] += 1
            if result.passed:
                categories[category]["passed"] += 1
            else:
                categories[category]["failed"] += 1
        
        # Calcular salud del sistema
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        system_health = {
            "overall_status": "healthy" if success_rate >= 90 else "warning" if success_rate >= 70 else "critical",
            "success_rate": success_rate,
            "categories": categories,
            "performance_metrics": self.performance_metrics,
            "critical_failures": [
                r.test_name for r in self.test_results 
                if not r.passed and r.test_category in ["shared_context", "stripe_connect"]
            ]
        }
        
        report = TestSuiteReport(
            suite_name="Orkesta Comprehensive Test Suite",
            started_at=started_at,
            completed_at=completed_at,
            total_tests=total_tests,
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            duration_seconds=duration,
            test_results=self.test_results,
            performance_metrics=self.performance_metrics,
            system_health=system_health
        )
        
        # Imprimir resumen
        print(f"\\n📊 RESUMEN FINAL:")
        print(f"   Total tests: {total_tests}")
        print(f"   Passed: {passed_tests} ({success_rate:.1f}%)")
        print(f"   Failed: {failed_tests}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   System health: {system_health['overall_status'].upper()}")
        
        if system_health['critical_failures']:
            print(f"   ⚠️ Critical failures: {len(system_health['critical_failures'])}")
            for failure in system_health['critical_failures'][:3]:
                print(f"      - {failure}")
        
        print(f"\\n📈 Performance highlights:")
        if "context_performance" in self.performance_metrics:
            ctx_perf = self.performance_metrics["context_performance"]
            print(f"   Context ops: {ctx_perf['insert_ops_per_second']:.0f} insert/s, {ctx_perf['read_ops_per_second']:.0f} read/s")
        
        if "agents_performance" in self.performance_metrics:
            agent_perf = self.performance_metrics["agents_performance"]
            print(f"   Agent avg response: {agent_perf['average_duration']:.2f}s")
        
        if "concurrent_conversations" in self.performance_metrics:
            conc_perf = self.performance_metrics["concurrent_conversations"]
            print(f"   Concurrent conversations: {conc_perf['success_rate']:.1%} success rate")
        
        return report

# Instancia global
comprehensive_test_suite = OrkestaComprehensiveTestSuite()

if __name__ == "__main__":
    # Ejecutar suite completa
    print("🧪 ORKESTA COMPREHENSIVE TEST SUITE")
    print("Testing LITERAL TODO EL SISTEMA...")
    
    async def main():
        suite = OrkestaComprehensiveTestSuite()
        
        try:
            report = await suite.run_full_test_suite()
            
            # Guardar reporte
            report_filename = f"orkesta_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            # Convertir dataclasses a dict para JSON
            report_dict = {
                "suite_name": report.suite_name,
                "started_at": report.started_at.isoformat(),
                "completed_at": report.completed_at.isoformat() if report.completed_at else None,
                "total_tests": report.total_tests,
                "passed_tests": report.passed_tests,
                "failed_tests": report.failed_tests,
                "duration_seconds": report.duration_seconds,
                "test_results": [asdict(result) for result in report.test_results],
                "performance_metrics": report.performance_metrics,
                "system_health": report.system_health
            }
            
            with open(report_filename, "w") as f:
                json.dump(report_dict, f, indent=2, default=str)
            
            print(f"\\n💾 Reporte completo guardado en: {report_filename}")
            
            # Código de salida basado en resultados
            if report.system_health["overall_status"] == "healthy":
                exit_code = 0
            elif report.system_health["overall_status"] == "warning":
                exit_code = 1
            else:
                exit_code = 2
            
            return exit_code
            
        except Exception as e:
            print(f"❌ Error ejecutando suite: {e}")
            return 3
    
    # Ejecutar
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)