"""
🎯 Orkesta Simulation Lab - Laboratorio de simulación multi-tenant
=================================================================

Laboratorio completo para simular escenarios complejos:
- Multi-tenant con fees reales
- Simulación de carga de trabajo
- Testing de marketplace scenarios
- Performance under load
- Revenue optimization
"""

import asyncio
import json
import time
import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Imports del sistema Orkesta
from orkesta_shared_context import get_shared_context, OrkestaSharedContext
from orkesta_smart_agents import CatalogMapperAgent, AliasNormalizerAgent, PriceResolverAgent, QuoteBuilderAgent
from orkesta_conversation_flows import conversation_engine, ConversationStage, ConversationIntent
from orkesta_comprehensive_test_suite import comprehensive_test_suite
from orkesta_stripe.types import ChargesMode, PaymentMethod, FeePolicy
from orkesta_stripe.checkout import checkout_orchestrator
from orkesta_stripe.fees import fee_calculator

logger = logging.getLogger(__name__)

class SimulationScenario(Enum):
    """Tipos de escenarios de simulación"""
    MARKETPLACE_RUSH = "marketplace_rush"
    ENTERPRISE_BULK = "enterprise_bulk"
    SMALL_BUSINESS = "small_business"
    SEASONAL_SPIKE = "seasonal_spike"
    COMPETITIVE_PRESSURE = "competitive_pressure"
    TECHNICAL_SUPPORT = "technical_support"
    CROSS_SELLING = "cross_selling"
    RETENTION_CAMPAIGN = "retention_campaign"

@dataclass
class TenantSimulationProfile:
    """Perfil de simulación para un tenant"""
    tenant_id: str
    business_type: str  # "marketplace", "enterprise", "smb", "startup"
    monthly_volume: float  # Volumen mensual esperado en MXN
    transaction_frequency: str  # "high", "medium", "low"
    customer_tier_distribution: Dict[str, float]  # % por tier
    product_categories: List[str]
    pricing_strategy: str  # "premium", "competitive", "budget"
    charges_mode: ChargesMode
    fee_policy: FeePolicy
    target_margin: float
    growth_rate: float  # % crecimiento mensual
    seasonality_factor: float  # Factor estacional
    competition_pressure: float  # 0-1, presión competitiva

@dataclass
class CustomerSimulationProfile:
    """Perfil de simulación para un cliente"""
    customer_id: str
    tenant_id: str
    customer_type: str  # "individual", "smb", "enterprise"
    tier: str  # "basic", "premium", "vip", "enterprise"
    avg_order_value: float
    purchase_frequency: int  # órdenes por mes
    price_sensitivity: float  # 0-1, sensibilidad al precio
    loyalty_score: float  # 0-1, lealtad
    preferred_categories: List[str]
    conversation_style: str  # "direct", "detailed", "price_focused", "relationship"
    objection_likelihood: float  # 0-1, probabilidad de objeciones

@dataclass
class SimulationEvent:
    """Evento durante la simulación"""
    timestamp: datetime
    event_type: str
    tenant_id: str
    customer_id: Optional[str]
    details: Dict[str, Any]
    revenue: float
    costs: float
    margin: float

@dataclass
class SimulationResult:
    """Resultado de una simulación"""
    scenario: SimulationScenario
    started_at: datetime
    duration_seconds: float
    tenants_simulated: int
    customers_simulated: int
    conversations_generated: int
    orders_processed: int
    total_revenue: float
    total_costs: float
    total_margin: float
    conversion_rate: float
    avg_order_value: float
    events: List[SimulationEvent]
    performance_metrics: Dict[str, Any]
    insights: List[str]

class OrkestaSimulationLab:
    """Laboratorio de simulación completo"""
    
    def __init__(self):
        self.simulation_events: List[SimulationEvent] = []
        self.tenant_profiles: Dict[str, TenantSimulationProfile] = {}
        self.customer_profiles: Dict[str, CustomerSimulationProfile] = {}
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        
        # Métricas de performance
        self.performance_tracker = {
            "response_times": [],
            "memory_usage": [],
            "concurrent_operations": 0,
            "error_count": 0
        }
    
    def setup_marketplace_simulation(self) -> Dict[str, TenantSimulationProfile]:
        """Configura simulación de marketplace con múltiples tenants"""
        
        print("🎭 Configurando simulación de marketplace...")
        
        # Definir perfiles de tenants diversos
        tenant_configs = [
            {
                "tenant_id": "electronics-pro",
                "business_type": "marketplace",
                "monthly_volume": 2500000.0,  # $2.5M MXN
                "transaction_frequency": "high",
                "customer_tier_distribution": {"basic": 0.6, "premium": 0.3, "vip": 0.1},
                "product_categories": ["electronics", "computers", "accessories"],
                "pricing_strategy": "competitive",
                "charges_mode": ChargesMode.DESTINATION,
                "target_margin": 1.8,
                "growth_rate": 0.15,
                "seasonality_factor": 1.2,
                "competition_pressure": 0.7
            },
            {
                "tenant_id": "enterprise-solutions",
                "business_type": "enterprise",
                "monthly_volume": 5000000.0,  # $5M MXN
                "transaction_frequency": "medium",
                "customer_tier_distribution": {"premium": 0.4, "vip": 0.4, "enterprise": 0.2},
                "product_categories": ["enterprise_software", "hardware", "services"],
                "pricing_strategy": "premium",
                "charges_mode": ChargesMode.SEPARATE,
                "target_margin": 2.5,
                "growth_rate": 0.08,
                "seasonality_factor": 1.0,
                "competition_pressure": 0.4
            },
            {
                "tenant_id": "startup-central",
                "business_type": "smb",
                "monthly_volume": 800000.0,  # $800K MXN
                "transaction_frequency": "medium",
                "customer_tier_distribution": {"basic": 0.7, "premium": 0.25, "vip": 0.05},
                "product_categories": ["software", "tools", "consulting"],
                "pricing_strategy": "budget",
                "charges_mode": ChargesMode.DIRECT,
                "target_margin": 1.2,
                "growth_rate": 0.25,
                "seasonality_factor": 0.9,
                "competition_pressure": 0.8
            },
            {
                "tenant_id": "luxury-tech",
                "business_type": "premium",
                "monthly_volume": 1200000.0,  # $1.2M MXN
                "transaction_frequency": "low",
                "customer_tier_distribution": {"vip": 0.6, "enterprise": 0.4},
                "product_categories": ["premium_tech", "custom_solutions"],
                "pricing_strategy": "premium",
                "charges_mode": ChargesMode.DESTINATION,
                "target_margin": 3.0,
                "growth_rate": 0.05,
                "seasonality_factor": 1.1,
                "competition_pressure": 0.3
            }
        ]
        
        # Crear perfiles de tenants
        for config in tenant_configs:
            # Calcular fee policy optimizada
            fee_policy = fee_calculator.optimize_fee_policy(
                sample_transactions=[
                    {"amount": config["monthly_volume"] / 100, "method": "card"}
                    for _ in range(10)
                ],
                config["charges_mode"],
                config["target_margin"]
            )
            
            profile = TenantSimulationProfile(
                tenant_id=config["tenant_id"],
                business_type=config["business_type"],
                monthly_volume=config["monthly_volume"],
                transaction_frequency=config["transaction_frequency"],
                customer_tier_distribution=config["customer_tier_distribution"],
                product_categories=config["product_categories"],
                pricing_strategy=config["pricing_strategy"],
                charges_mode=config["charges_mode"],
                fee_policy=fee_policy,
                target_margin=config["target_margin"],
                growth_rate=config["growth_rate"],
                seasonality_factor=config["seasonality_factor"],
                competition_pressure=config["competition_pressure"]
            )
            
            self.tenant_profiles[config["tenant_id"]] = profile
            
            # Configurar contexto del tenant
            self._setup_tenant_context(profile)
        
        print(f"   ✅ {len(tenant_configs)} tenants configurados")
        return self.tenant_profiles
    
    def _setup_tenant_context(self, profile: TenantSimulationProfile):
        """Configura el contexto específico de un tenant"""
        
        context = get_shared_context(profile.tenant_id)
        
        # Catálogo específico por categorías
        catalog_templates = {
            "electronics": [
                {"name": "iPhone 15 Pro", "base_price": 25000, "category": "smartphones"},
                {"name": "Samsung Galaxy S24", "base_price": 22000, "category": "smartphones"},
                {"name": "iPad Air", "base_price": 15000, "category": "tablets"},
                {"name": "AirPods Pro", "base_price": 6000, "category": "audio"}
            ],
            "computers": [
                {"name": "MacBook Pro M3", "base_price": 45000, "category": "laptops"},
                {"name": "Dell XPS 13", "base_price": 35000, "category": "laptops"},
                {"name": "HP EliteBook", "base_price": 28000, "category": "laptops"},
                {"name": "Surface Studio", "base_price": 55000, "category": "workstations"}
            ],
            "enterprise_software": [
                {"name": "Office 365 Enterprise", "base_price": 15000, "category": "productivity"},
                {"name": "Adobe Creative Suite", "base_price": 25000, "category": "design"},
                {"name": "Salesforce CRM", "base_price": 35000, "category": "crm"},
                {"name": "Microsoft Azure Credits", "base_price": 50000, "category": "cloud"}
            ],
            "premium_tech": [
                {"name": "Tesla Model S Plaid Computer", "base_price": 150000, "category": "automotive"},
                {"name": "Apple Vision Pro", "base_price": 80000, "category": "ar_vr"},
                {"name": "Custom Workstation Build", "base_price": 120000, "category": "custom"},
                {"name": "Enterprise AI Solution", "base_price": 200000, "category": "ai"}
            ]
        }
        
        # Agregar productos relevantes
        product_id = 1
        for category in profile.product_categories:
            if category in catalog_templates:
                for template in catalog_templates[category]:
                    # Ajustar precio según estrategia
                    price_multiplier = {
                        "premium": 1.2,
                        "competitive": 1.0,
                        "budget": 0.8
                    }.get(profile.pricing_strategy, 1.0)
                    
                    product = {
                        "id": f"{profile.tenant_id}_prod_{product_id:03d}",
                        "name": template["name"],
                        "category": template["category"],
                        "price": template["base_price"] * price_multiplier,
                        "tenant_id": profile.tenant_id,
                        "aliases": [
                            template["name"].lower(),
                            template["category"],
                            " ".join(template["name"].split()[:2]).lower()
                        ]
                    }
                    
                    context.add_catalog_item(product)
                    product_id += 1
    
    def generate_customer_profiles(self, customers_per_tenant: int = 20) -> Dict[str, CustomerSimulationProfile]:
        """Genera perfiles de clientes para simulación"""
        
        print(f"👥 Generando {customers_per_tenant} clientes por tenant...")
        
        customer_types = {
            "individual": {"avg_order": 5000, "frequency": 2, "price_sensitivity": 0.8},
            "smb": {"avg_order": 25000, "frequency": 4, "price_sensitivity": 0.6},
            "enterprise": {"avg_order": 100000, "frequency": 6, "price_sensitivity": 0.3}
        }
        
        conversation_styles = ["direct", "detailed", "price_focused", "relationship"]
        
        for tenant_profile in self.tenant_profiles.values():
            for i in range(customers_per_tenant):
                # Seleccionar tipo de cliente basado en distribución
                tier_choice = random.choices(
                    list(tenant_profile.customer_tier_distribution.keys()),
                    weights=list(tenant_profile.customer_tier_distribution.values())
                )[0]
                
                # Tipo de cliente basado en tier
                if tier_choice == "enterprise":
                    customer_type = "enterprise"
                elif tier_choice in ["vip", "premium"]:
                    customer_type = random.choice(["smb", "enterprise"])
                else:
                    customer_type = "individual"
                
                customer_base = customer_types[customer_type]
                
                customer_id = f"{tenant_profile.tenant_id}_customer_{i:03d}"
                
                # Ajustar por competencia y estrategia de pricing
                pricing_adjustment = {
                    "premium": 1.3,
                    "competitive": 1.0,
                    "budget": 0.7
                }.get(tenant_profile.pricing_strategy, 1.0)
                
                profile = CustomerSimulationProfile(
                    customer_id=customer_id,
                    tenant_id=tenant_profile.tenant_id,
                    customer_type=customer_type,
                    tier=tier_choice,
                    avg_order_value=customer_base["avg_order"] * pricing_adjustment,
                    purchase_frequency=customer_base["frequency"],
                    price_sensitivity=customer_base["price_sensitivity"] + tenant_profile.competition_pressure * 0.2,
                    loyalty_score=random.uniform(0.3, 0.9),
                    preferred_categories=random.sample(
                        tenant_profile.product_categories, 
                        min(2, len(tenant_profile.product_categories))
                    ),
                    conversation_style=random.choice(conversation_styles),
                    objection_likelihood=customer_base["price_sensitivity"] * 0.6
                )
                
                self.customer_profiles[customer_id] = profile
        
        print(f"   ✅ {len(self.customer_profiles)} perfiles de clientes generados")
        return self.customer_profiles
    
    async def run_scenario_simulation(self, scenario: SimulationScenario, 
                                    duration_minutes: int = 30,
                                    concurrency_level: int = 10) -> SimulationResult:
        """Ejecuta simulación de un escenario específico"""
        
        print(f"\\n🎬 Ejecutando simulación: {scenario.value}")
        print(f"   Duración: {duration_minutes} minutos")
        print(f"   Concurrencia: {concurrency_level} operaciones simultáneas")
        
        started_at = datetime.now()
        simulation_start = time.time()
        
        # Configurar parámetros específicos del escenario
        scenario_params = self._get_scenario_parameters(scenario)
        
        # Limpiar eventos previos
        self.simulation_events.clear()
        
        try:
            # Ejecutar simulación basada en el escenario
            if scenario == SimulationScenario.MARKETPLACE_RUSH:
                await self._simulate_marketplace_rush(duration_minutes, concurrency_level, scenario_params)
            
            elif scenario == SimulationScenario.ENTERPRISE_BULK:
                await self._simulate_enterprise_bulk(duration_minutes, concurrency_level, scenario_params)
            
            elif scenario == SimulationScenario.SMALL_BUSINESS:
                await self._simulate_small_business(duration_minutes, concurrency_level, scenario_params)
            
            elif scenario == SimulationScenario.SEASONAL_SPIKE:
                await self._simulate_seasonal_spike(duration_minutes, concurrency_level, scenario_params)
            
            elif scenario == SimulationScenario.COMPETITIVE_PRESSURE:
                await self._simulate_competitive_pressure(duration_minutes, concurrency_level, scenario_params)
            
            else:
                # Simulación genérica
                await self._simulate_generic_scenario(duration_minutes, concurrency_level, scenario_params)
            
            duration_seconds = time.time() - simulation_start
            
            # Calcular métricas finales
            result = self._calculate_simulation_results(
                scenario, started_at, duration_seconds
            )
            
            print(f"\\n✅ Simulación completada:")
            print(f"   Conversaciones: {result.conversations_generated}")
            print(f"   Órdenes: {result.orders_processed}")
            print(f"   Revenue: ${result.total_revenue:,.2f}")
            print(f"   Margen: ${result.total_margin:,.2f}")
            print(f"   Conversión: {result.conversion_rate:.1%}")
            
            return result
            
        except Exception as e:
            print(f"❌ Error en simulación: {e}")
            duration_seconds = time.time() - simulation_start
            
            # Retornar resultado parcial en caso de error
            return SimulationResult(
                scenario=scenario,
                started_at=started_at,
                duration_seconds=duration_seconds,
                tenants_simulated=len(self.tenant_profiles),
                customers_simulated=len(self.customer_profiles),
                conversations_generated=0,
                orders_processed=0,
                total_revenue=0.0,
                total_costs=0.0,
                total_margin=0.0,
                conversion_rate=0.0,
                avg_order_value=0.0,
                events=self.simulation_events,
                performance_metrics=self.performance_tracker,
                insights=["Simulation failed with error: " + str(e)]
            )
    
    def _get_scenario_parameters(self, scenario: SimulationScenario) -> Dict[str, Any]:
        """Obtiene parámetros específicos para cada escenario"""
        
        params = {
            SimulationScenario.MARKETPLACE_RUSH: {
                "traffic_multiplier": 3.0,
                "conversion_boost": 1.5,
                "price_sensitivity_increase": 0.2,
                "urgency_factor": 0.8,
                "customer_distribution": {"basic": 0.7, "premium": 0.25, "vip": 0.05}
            },
            
            SimulationScenario.ENTERPRISE_BULK: {
                "traffic_multiplier": 0.5,
                "conversion_boost": 2.0,
                "avg_order_multiplier": 5.0,
                "decision_time_increase": 2.0,
                "customer_distribution": {"enterprise": 0.6, "vip": 0.3, "premium": 0.1}
            },
            
            SimulationScenario.SMALL_BUSINESS: {
                "traffic_multiplier": 1.5,
                "conversion_boost": 1.2,
                "price_sensitivity_increase": 0.3,
                "support_requests_increase": 2.0,
                "customer_distribution": {"basic": 0.6, "premium": 0.3, "vip": 0.1}
            },
            
            SimulationScenario.SEASONAL_SPIKE: {
                "traffic_multiplier": 4.0,
                "conversion_boost": 1.8,
                "system_stress_factor": 2.5,
                "inventory_pressure": 0.7,
                "customer_distribution": {"basic": 0.5, "premium": 0.35, "vip": 0.15}
            },
            
            SimulationScenario.COMPETITIVE_PRESSURE: {
                "traffic_multiplier": 1.0,
                "conversion_penalty": 0.8,
                "price_objections_increase": 2.0,
                "loyalty_test_factor": 0.6,
                "customer_distribution": {"basic": 0.6, "premium": 0.3, "vip": 0.1}
            }
        }
        
        return params.get(scenario, {
            "traffic_multiplier": 1.0,
            "conversion_boost": 1.0,
            "customer_distribution": {"basic": 0.6, "premium": 0.3, "vip": 0.1}
        })
    
    async def _simulate_marketplace_rush(self, duration_minutes: int, 
                                       concurrency_level: int, 
                                       params: Dict[str, Any]):
        """Simula rush de marketplace (Black Friday style)"""
        
        print("   🛒 Simulando rush de marketplace...")
        
        # Incrementar tráfico según parámetros
        traffic_multiplier = params.get("traffic_multiplier", 3.0)
        total_interactions = int(len(self.customer_profiles) * traffic_multiplier)
        
        # Crear tareas concurrentes
        tasks = []
        
        for i in range(total_interactions):
            # Seleccionar cliente aleatorio
            customer_profile = random.choice(list(self.customer_profiles.values()))
            
            # Aumentar urgencia en rush
            urgency_boost = params.get("urgency_factor", 0.8)
            
            task = self._simulate_customer_interaction(
                customer_profile, 
                urgency_level=urgency_boost,
                scenario_params=params
            )
            tasks.append(task)
            
            # Controlar concurrencia
            if len(tasks) >= concurrency_level:
                # Ejecutar batch
                await asyncio.gather(*tasks[:concurrency_level], return_exceptions=True)
                tasks = tasks[concurrency_level:]
                
                # Simular delay entre batches
                await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Ejecutar tareas restantes
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _simulate_enterprise_bulk(self, duration_minutes: int,
                                      concurrency_level: int,
                                      params: Dict[str, Any]):
        """Simula órdenes enterprise de volumen"""
        
        print("   🏢 Simulando órdenes enterprise...")
        
        # Filtrar solo clientes enterprise
        enterprise_customers = [
            profile for profile in self.customer_profiles.values()
            if profile.customer_type == "enterprise" or profile.tier == "enterprise"
        ]
        
        # Simular conversaciones más largas y complejas
        tasks = []
        
        for customer_profile in enterprise_customers:
            # Enterprise tiene conversaciones más detalladas
            task = self._simulate_complex_enterprise_flow(customer_profile, params)
            tasks.append(task)
            
            # Batch processing
            if len(tasks) >= min(concurrency_level, 5):  # Menos concurrencia para enterprise
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
                await asyncio.sleep(random.uniform(1, 3))  # Más tiempo entre conversaciones
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _simulate_small_business(self, duration_minutes: int,
                                     concurrency_level: int,
                                     params: Dict[str, Any]):
        """Simula interacciones de pequeñas empresas"""
        
        print("   🏪 Simulando pequeñas empresas...")
        
        # Filtrar clientes SMB
        smb_customers = [
            profile for profile in self.customer_profiles.values()
            if profile.customer_type in ["individual", "smb"]
        ]
        
        # SMB tiene más preguntas de soporte y price sensitivity
        tasks = []
        
        for customer_profile in smb_customers:
            # Aumentar probabilidad de price objections
            modified_profile = customer_profile
            modified_profile.price_sensitivity *= 1.3
            modified_profile.objection_likelihood *= 1.5
            
            task = self._simulate_customer_interaction(
                modified_profile,
                support_focus=True,
                scenario_params=params
            )
            tasks.append(task)
            
            if len(tasks) >= concurrency_level:
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
                await asyncio.sleep(random.uniform(0.2, 1.0))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _simulate_seasonal_spike(self, duration_minutes: int,
                                     concurrency_level: int,
                                     params: Dict[str, Any]):
        """Simula pico estacional con estrés del sistema"""
        
        print("   🎄 Simulando pico estacional...")
        
        # Incremento masivo de tráfico
        traffic_multiplier = params.get("traffic_multiplier", 4.0)
        stress_factor = params.get("system_stress_factor", 2.5)
        
        # Simular carga progresiva
        total_customers = len(self.customer_profiles)
        waves = 5  # 5 oleadas de tráfico
        
        for wave in range(waves):
            print(f"     Oleada {wave + 1}/{waves}")
            
            # Incrementar intensidad por oleada
            wave_intensity = (wave + 1) / waves
            customers_this_wave = int(total_customers * traffic_multiplier * wave_intensity)
            
            # Seleccionar clientes para esta oleada
            wave_customers = random.sample(
                list(self.customer_profiles.values()),
                min(customers_this_wave, len(self.customer_profiles))
            )
            
            # Procesar oleada con alta concurrencia
            tasks = []
            for customer_profile in wave_customers:
                task = self._simulate_customer_interaction(
                    customer_profile,
                    urgency_level=0.9,  # Alta urgencia
                    scenario_params=params
                )
                tasks.append(task)
                
                # Procesar en batches grandes
                if len(tasks) >= concurrency_level * 2:
                    await asyncio.gather(*tasks, return_exceptions=True)
                    tasks = []
                    # Menos delay entre batches para simular rush
                    await asyncio.sleep(random.uniform(0.05, 0.2))
            
            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)
            
            # Pausa entre oleadas
            await asyncio.sleep(random.uniform(2, 5))
    
    async def _simulate_competitive_pressure(self, duration_minutes: int,
                                           concurrency_level: int,
                                           params: Dict[str, Any]):
        """Simula presión competitiva con más objeciones"""
        
        print("   ⚔️ Simulando presión competitiva...")
        
        # Todos los clientes con mayor price sensitivity
        modified_customers = []
        for customer_profile in self.customer_profiles.values():
            modified = customer_profile
            modified.price_sensitivity *= 1.4
            modified.objection_likelihood *= 2.0
            modified.loyalty_score *= 0.7
            modified_customers.append(modified)
        
        # Simular conversaciones con más objeciones
        tasks = []
        
        for customer_profile in modified_customers:
            task = self._simulate_customer_interaction(
                customer_profile,
                competitive_mode=True,
                scenario_params=params
            )
            tasks.append(task)
            
            if len(tasks) >= concurrency_level:
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
                await asyncio.sleep(random.uniform(0.3, 1.0))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _simulate_generic_scenario(self, duration_minutes: int,
                                       concurrency_level: int,
                                       params: Dict[str, Any]):
        """Simulación genérica balanceada"""
        
        print("   🎯 Simulando escenario genérico...")
        
        # Distribución normal de clientes
        customers_to_simulate = list(self.customer_profiles.values())
        random.shuffle(customers_to_simulate)
        
        tasks = []
        
        for customer_profile in customers_to_simulate:
            task = self._simulate_customer_interaction(
                customer_profile,
                scenario_params=params
            )
            tasks.append(task)
            
            if len(tasks) >= concurrency_level:
                await asyncio.gather(*tasks, return_exceptions=True)
                tasks = []
                await asyncio.sleep(random.uniform(0.5, 1.5))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _simulate_customer_interaction(self, customer_profile: CustomerSimulationProfile,
                                           urgency_level: float = 0.5,
                                           support_focus: bool = False,
                                           competitive_mode: bool = False,
                                           scenario_params: Dict[str, Any] = None) -> Dict[str, Any]:
        """Simula una interacción completa con un cliente"""
        
        interaction_start = time.time()
        
        try:
            # Trackear operaciones concurrentes
            self.performance_tracker["concurrent_operations"] += 1
            
            # Iniciar conversación
            conv_id = conversation_engine.start_conversation(
                customer_profile.tenant_id,
                customer_profile.customer_id,
                channel="web",
                customer_profile={
                    "tier": customer_profile.tier,
                    "type": customer_profile.customer_type,
                    "avg_order": customer_profile.avg_order_value
                }
            )
            
            # Generar flujo de mensajes basado en el perfil del cliente
            messages = self._generate_customer_messages(
                customer_profile, urgency_level, support_focus, competitive_mode
            )
            
            conversation_successful = True
            final_response = None
            order_value = 0.0
            
            # Procesar conversación
            for message in messages:
                try:
                    response = await conversation_engine.process_customer_message(conv_id, message)
                    final_response = response
                    
                    if not response:
                        conversation_successful = False
                        break
                    
                    # Capturar valor de cotización
                    quote_value = response.get("metadata", {}).get("quote_value", 0)
                    if quote_value > order_value:
                        order_value = quote_value
                    
                    # Simular delay del cliente
                    await asyncio.sleep(random.uniform(0.1, 0.3))
                    
                except Exception as e:
                    self.performance_tracker["error_count"] += 1
                    conversation_successful = False
                    break
            
            # Determinar si hubo conversión
            conversion_probability = self._calculate_conversion_probability(
                customer_profile, final_response, urgency_level, competitive_mode
            )
            
            converted = random.random() < conversion_probability
            
            # Calcular costos y revenue
            if converted and order_value > 0:
                tenant_profile = self.tenant_profiles[customer_profile.tenant_id]
                
                # Calcular fees usando el sistema de Stripe Connect
                costs = checkout_orchestrator.calculate_effective_costs(
                    order_value,
                    PaymentMethod.CARD,  # Asumir tarjeta por defecto
                    tenant_profile.charges_mode,
                    tenant_profile.fee_policy.application_fee_pct,
                    tenant_profile.fee_policy.application_fee_fixed
                )
                
                revenue = order_value
                total_costs = costs["total_cost"]
                margin = revenue - total_costs
                
                # Registrar evento de orden
                event = SimulationEvent(
                    timestamp=datetime.now(),
                    event_type="order_completed",
                    tenant_id=customer_profile.tenant_id,
                    customer_id=customer_profile.customer_id,
                    details={
                        "conversation_id": conv_id,
                        "conversion_probability": conversion_probability,
                        "customer_tier": customer_profile.tier,
                        "order_value": order_value,
                        "charges_mode": tenant_profile.charges_mode.value,
                        "costs_breakdown": costs
                    },
                    revenue=revenue,
                    costs=total_costs,
                    margin=margin
                )
                
                self.simulation_events.append(event)
            
            else:
                # Conversación sin conversión
                event = SimulationEvent(
                    timestamp=datetime.now(),
                    event_type="conversation_no_conversion",
                    tenant_id=customer_profile.tenant_id,
                    customer_id=customer_profile.customer_id,
                    details={
                        "conversation_id": conv_id,
                        "conversion_probability": conversion_probability,
                        "final_stage": final_response.get("current_stage") if final_response else None,
                        "messages_count": len(messages)
                    },
                    revenue=0.0,
                    costs=0.0,
                    margin=0.0
                )
                
                self.simulation_events.append(event)
            
            # Trackear performance
            interaction_duration = time.time() - interaction_start
            self.performance_tracker["response_times"].append(interaction_duration)
            
            return {
                "success": conversation_successful,
                "converted": converted,
                "order_value": order_value,
                "interaction_duration": interaction_duration
            }
            
        except Exception as e:
            self.performance_tracker["error_count"] += 1
            return {
                "success": False,
                "converted": False,
                "order_value": 0.0,
                "error": str(e)
            }
        
        finally:
            self.performance_tracker["concurrent_operations"] -= 1
    
    def _generate_customer_messages(self, customer_profile: CustomerSimulationProfile,
                                  urgency_level: float,
                                  support_focus: bool,
                                  competitive_mode: bool) -> List[str]:
        """Genera mensajes realistas basados en el perfil del cliente"""
        
        messages = []
        
        # Mensaje inicial basado en estilo de conversación
        if customer_profile.conversation_style == "direct":
            messages.append("Necesito cotizar productos para mi empresa")
        elif customer_profile.conversation_style == "detailed":
            messages.append("Hola, estoy buscando soluciones tecnológicas para mi negocio y me gustaría entender qué opciones tienen disponibles")
        elif customer_profile.conversation_style == "price_focused":
            messages.append("¿Tienen lista de precios? Busco la mejor relación precio-calidad")
        else:  # relationship
            messages.append("Buenos días, soy cliente recurrente y necesito revisar algunas opciones")
        
        # Mensaje sobre categorías preferidas
        if customer_profile.preferred_categories:
            category = random.choice(customer_profile.preferred_categories)
            messages.append(f"Me interesan especialmente productos de {category}")
        
        # Mensaje sobre cantidad basado en tier
        if customer_profile.tier == "enterprise":
            messages.append(f"Necesitaría cotizar para {random.randint(20, 100)} unidades")
        elif customer_profile.tier in ["vip", "premium"]:
            messages.append(f"Busco {random.randint(5, 20)} unidades de buena calidad")
        else:
            messages.append(f"Necesito {random.randint(1, 5)} unidades")
        
        # Mensajes de urgencia
        if urgency_level > 0.7:
            messages.append("Es urgente, necesito esto para esta semana")
        elif urgency_level > 0.4:
            messages.append("Tengo cierta prisa, ¿cuándo podrían entregar?")
        
        # Mensajes de soporte
        if support_focus:
            messages.append("¿Incluyen soporte técnico y capacitación?")
            messages.append("¿Cómo funciona la garantía?")
        
        # Mensajes competitivos
        if competitive_mode:
            messages.append("He visto opciones similares en otros proveedores")
            if customer_profile.price_sensitivity > 0.7:
                messages.append("¿Es su mejor precio? La competencia me ofrece menos")
        
        # Objeciones basadas en perfil
        if random.random() < customer_profile.objection_likelihood:
            if customer_profile.price_sensitivity > 0.6:
                messages.append("Me parece caro, ¿no tienen algo más económico?")
            else:
                messages.append("Necesito pensarlo, es una inversión importante")
        
        # Mensaje de cierre basado en loyalty
        if customer_profile.loyalty_score > 0.7 and random.random() < 0.8:
            messages.append("Si todo está bien, podemos proceder")
        elif customer_profile.loyalty_score > 0.4 and random.random() < 0.6:
            messages.append("¿Pueden enviarme la cotización formal?")
        else:
            messages.append("Voy a comparar opciones y les aviso")
        
        return messages
    
    def _calculate_conversion_probability(self, customer_profile: CustomerSimulationProfile,
                                        final_response: Optional[Dict[str, Any]],
                                        urgency_level: float,
                                        competitive_mode: bool) -> float:
        """Calcula probabilidad de conversión basada en múltiples factores"""
        
        # Base probability por tier
        base_probability = {
            "enterprise": 0.8,
            "vip": 0.7,
            "premium": 0.6,
            "basic": 0.4
        }.get(customer_profile.tier, 0.3)
        
        # Ajustes por factores
        probability = base_probability
        
        # Factor de lealtad
        probability *= (0.5 + customer_profile.loyalty_score * 0.5)
        
        # Factor de urgencia
        probability *= (0.8 + urgency_level * 0.3)
        
        # Factor de sensibilidad al precio
        probability *= (1.2 - customer_profile.price_sensitivity * 0.4)
        
        # Factor competitivo
        if competitive_mode:
            probability *= 0.7
        
        # Factor de respuesta del agente
        if final_response:
            conversation_health = final_response.get("conversation_health", {})
            health_level = conversation_health.get("health_level", "fair")
            
            health_multiplier = {
                "excellent": 1.3,
                "good": 1.1,
                "fair": 1.0,
                "poor": 0.6
            }.get(health_level, 1.0)
            
            probability *= health_multiplier
            
            # Si llegó a etapa de closing, boost significativo
            current_stage = final_response.get("current_stage", "")
            if current_stage in ["closing", "payment_processing"]:
                probability *= 1.5
            elif current_stage == "quote_building":
                probability *= 1.2
        
        # Mantener en rango válido
        return max(0.0, min(1.0, probability))
    
    async def _simulate_complex_enterprise_flow(self, customer_profile: CustomerSimulationProfile,
                                              params: Dict[str, Any]) -> Dict[str, Any]:
        """Simula flujo complejo específico para enterprise"""
        
        # Enterprise tiene conversaciones más largas y detalladas
        messages = [
            "Representamos una empresa Fortune 500 y necesitamos una solución integral",
            f"Requerimos equipamiento para {random.randint(100, 500)} empleados",
            "Necesitamos cotización detallada con términos de pago empresariales",
            "¿Manejan contratos anuales con descuentos por volumen?",
            "Requerimos instalación, configuración y capacitación incluidas",
            "¿Cuáles son los SLAs de soporte técnico?",
            "Necesitamos que el proyecto se complete en Q1 2024",
            "¿Pueden incluir garantía extendida y reemplazo inmediato?",
            "Si todo está conforme, podemos proceder con la orden de compra"
        ]
        
        return await self._simulate_customer_interaction(
            customer_profile,
            urgency_level=0.3,  # Enterprise toma más tiempo
            scenario_params=params
        )
    
    def _calculate_simulation_results(self, scenario: SimulationScenario,
                                    started_at: datetime,
                                    duration_seconds: float) -> SimulationResult:
        """Calcula resultados finales de la simulación"""
        
        # Métricas básicas
        total_events = len(self.simulation_events)
        order_events = [e for e in self.simulation_events if e.event_type == "order_completed"]
        conversation_events = [e for e in self.simulation_events if e.event_type in ["order_completed", "conversation_no_conversion"]]
        
        orders_processed = len(order_events)
        conversations_generated = len(conversation_events)
        
        # Métricas financieras
        total_revenue = sum(e.revenue for e in order_events)
        total_costs = sum(e.costs for e in order_events)
        total_margin = sum(e.margin for e in order_events)
        
        # Métricas de conversión
        conversion_rate = orders_processed / conversations_generated if conversations_generated > 0 else 0
        avg_order_value = total_revenue / orders_processed if orders_processed > 0 else 0
        
        # Métricas de performance
        avg_response_time = (
            sum(self.performance_tracker["response_times"]) / 
            len(self.performance_tracker["response_times"])
        ) if self.performance_tracker["response_times"] else 0
        
        max_concurrent = max(self.performance_tracker.get("concurrent_operations", 0), 0)
        error_rate = (
            self.performance_tracker["error_count"] / 
            total_events if total_events > 0 else 0
        )
        
        performance_metrics = {
            "avg_response_time_seconds": avg_response_time,
            "max_concurrent_operations": max_concurrent,
            "error_rate": error_rate,
            "total_errors": self.performance_tracker["error_count"],
            "throughput_per_second": total_events / duration_seconds if duration_seconds > 0 else 0
        }
        
        # Generar insights
        insights = self._generate_simulation_insights(
            scenario, order_events, performance_metrics, conversion_rate
        )
        
        return SimulationResult(
            scenario=scenario,
            started_at=started_at,
            duration_seconds=duration_seconds,
            tenants_simulated=len(self.tenant_profiles),
            customers_simulated=len(self.customer_profiles),
            conversations_generated=conversations_generated,
            orders_processed=orders_processed,
            total_revenue=total_revenue,
            total_costs=total_costs,
            total_margin=total_margin,
            conversion_rate=conversion_rate,
            avg_order_value=avg_order_value,
            events=self.simulation_events,
            performance_metrics=performance_metrics,
            insights=insights
        )
    
    def _generate_simulation_insights(self, scenario: SimulationScenario,
                                    order_events: List[SimulationEvent],
                                    performance_metrics: Dict[str, Any],
                                    conversion_rate: float) -> List[str]:
        """Genera insights automáticos de la simulación"""
        
        insights = []
        
        # Insights de performance
        if performance_metrics["avg_response_time_seconds"] > 2.0:
            insights.append("⚠️ Tiempo de respuesta alto: considera optimizar agentes")
        elif performance_metrics["avg_response_time_seconds"] < 0.5:
            insights.append("✅ Excelente tiempo de respuesta del sistema")
        
        if performance_metrics["error_rate"] > 0.05:
            insights.append("🔥 Alta tasa de errores: revisar estabilidad del sistema")
        elif performance_metrics["error_rate"] == 0:
            insights.append("💯 Sin errores durante la simulación")
        
        # Insights de conversión
        if conversion_rate > 0.7:
            insights.append("🎯 Excelente tasa de conversión: agentes funcionan bien")
        elif conversion_rate < 0.3:
            insights.append("📉 Baja conversión: revisar flujos de conversación")
        
        # Insights por tenant
        tenant_performance = {}
        for event in order_events:
            tenant_id = event.tenant_id
            if tenant_id not in tenant_performance:
                tenant_performance[tenant_id] = {"revenue": 0, "orders": 0, "margin": 0}
            
            tenant_performance[tenant_id]["revenue"] += event.revenue
            tenant_performance[tenant_id]["orders"] += 1
            tenant_performance[tenant_id]["margin"] += event.margin
        
        # Encontrar mejores performers
        if tenant_performance:
            best_revenue_tenant = max(tenant_performance.items(), key=lambda x: x[1]["revenue"])
            best_margin_tenant = max(tenant_performance.items(), key=lambda x: x[1]["margin"])
            
            insights.append(f"🏆 Mejor revenue: {best_revenue_tenant[0]} (${best_revenue_tenant[1]['revenue']:,.2f})")
            insights.append(f"💰 Mejor margen: {best_margin_tenant[0]} (${best_margin_tenant[1]['margin']:,.2f})")
        
        # Insights específicos por escenario
        if scenario == SimulationScenario.MARKETPLACE_RUSH:
            throughput = performance_metrics["throughput_per_second"]
            if throughput > 10:
                insights.append("🚀 Sistema maneja bien el rush de tráfico")
            else:
                insights.append("⚡ Considerar escalamiento para picos de tráfico")
        
        elif scenario == SimulationScenario.ENTERPRISE_BULK:
            avg_order = sum(e.revenue for e in order_events) / len(order_events) if order_events else 0
            if avg_order > 100000:
                insights.append("💼 Órdenes enterprise de alto valor procesadas exitosamente")
        
        elif scenario == SimulationScenario.COMPETITIVE_PRESSURE:
            if conversion_rate > 0.5:
                insights.append("🛡️ Sistema resistente a presión competitiva")
            else:
                insights.append("⚔️ Revisar estrategias de manejo de objeciones")
        
        return insights
    
    async def run_comprehensive_lab_test(self) -> Dict[str, Any]:
        """Ejecuta suite completa del laboratorio de simulación"""
        
        print("🔬 ORKESTA SIMULATION LAB - COMPREHENSIVE TEST")
        print("=" * 60)
        
        lab_start = time.time()
        
        # 1. Setup del laboratorio
        print("\\n🔧 Configurando laboratorio...")
        self.setup_marketplace_simulation()
        self.generate_customer_profiles(customers_per_tenant=25)
        
        # 2. Ejecutar suite de tests comprehensivos primero
        print("\\n🧪 Ejecutando suite de tests comprehensivos...")
        test_report = await comprehensive_test_suite.run_full_test_suite()
        
        # 3. Ejecutar simulaciones de escenarios
        simulation_results = {}
        
        scenarios_to_test = [
            (SimulationScenario.MARKETPLACE_RUSH, 10, 15),
            (SimulationScenario.ENTERPRISE_BULK, 8, 5),
            (SimulationScenario.SMALL_BUSINESS, 12, 10),
            (SimulationScenario.SEASONAL_SPIKE, 6, 20),
            (SimulationScenario.COMPETITIVE_PRESSURE, 10, 12)
        ]
        
        for scenario, duration, concurrency in scenarios_to_test:
            print(f"\\n🎬 Ejecutando {scenario.value}...")
            result = await self.run_scenario_simulation(scenario, duration, concurrency)
            simulation_results[scenario.value] = result
        
        # 4. Análisis consolidado
        lab_duration = time.time() - lab_start
        
        consolidated_analysis = self._generate_lab_analysis(
            test_report, simulation_results, lab_duration
        )
        
        # 5. Reporte final
        print("\\n" + "=" * 60)
        print("🎯 SIMULATION LAB COMPLETED")
        print("=" * 60)
        
        print(f"\\n📊 RESUMEN EJECUTIVO:")
        print(f"   Test suite: {test_report.passed_tests}/{test_report.total_tests} passed ({test_report.passed_tests/test_report.total_tests*100:.1f}%)")
        print(f"   Scenarios: {len(simulation_results)} completed")
        print(f"   Total duration: {lab_duration/60:.1f} minutes")
        print(f"   System health: {test_report.system_health['overall_status'].upper()}")
        
        # Revenue summary
        total_simulated_revenue = sum(r.total_revenue for r in simulation_results.values())
        total_simulated_margin = sum(r.total_margin for r in simulation_results.values())
        
        print(f"\\n💰 REVENUE SIMULATION:")
        print(f"   Total simulated revenue: ${total_simulated_revenue:,.2f}")
        print(f"   Total margin: ${total_simulated_margin:,.2f}")
        print(f"   Average margin rate: {total_simulated_margin/total_simulated_revenue*100:.1f}%")
        
        # Performance summary
        avg_conversion = sum(r.conversion_rate for r in simulation_results.values()) / len(simulation_results)
        print(f"\\n⚡ PERFORMANCE:")
        print(f"   Average conversion rate: {avg_conversion:.1%}")
        print(f"   System stability: {'EXCELLENT' if test_report.system_health['success_rate'] > 95 else 'GOOD' if test_report.system_health['success_rate'] > 80 else 'NEEDS_IMPROVEMENT'}")
        
        return {
            "lab_summary": {
                "duration_seconds": lab_duration,
                "test_suite_results": test_report,
                "simulation_results": simulation_results,
                "consolidated_analysis": consolidated_analysis
            },
            "executive_summary": {
                "system_health": test_report.system_health['overall_status'],
                "test_success_rate": test_report.passed_tests / test_report.total_tests,
                "scenarios_completed": len(simulation_results),
                "total_simulated_revenue": total_simulated_revenue,
                "total_simulated_margin": total_simulated_margin,
                "average_conversion_rate": avg_conversion,
                "key_insights": consolidated_analysis["key_insights"]
            }
        }
    
    def _generate_lab_analysis(self, test_report, simulation_results: Dict[str, Any], 
                             lab_duration: float) -> Dict[str, Any]:
        """Genera análisis consolidado del laboratorio"""
        
        # Análisis de correlaciones
        correlations = []
        
        # Correlación entre salud del sistema y performance de simulación
        system_health_score = test_report.system_health["success_rate"]
        avg_conversion = sum(r.conversion_rate for r in simulation_results.values()) / len(simulation_results)
        
        if system_health_score > 90 and avg_conversion > 0.6:
            correlations.append("✅ Sistema saludable correlaciona con alta conversión")
        elif system_health_score < 80 and avg_conversion < 0.4:
            correlations.append("⚠️ Problemas del sistema afectan conversión")
        
        # Análisis de performance bajo carga
        seasonal_spike = simulation_results.get("seasonal_spike")
        if seasonal_spike and seasonal_spike.performance_metrics["error_rate"] < 0.05:
            correlations.append("🔥 Sistema resistente a picos de carga")
        
        # Análisis de revenue por modo de Stripe
        revenue_by_mode = {}
        for result in simulation_results.values():
            for event in result.events:
                if event.event_type == "order_completed":
                    mode = event.details.get("charges_mode", "unknown")
                    if mode not in revenue_by_mode:
                        revenue_by_mode[mode] = 0
                    revenue_by_mode[mode] += event.revenue
        
        # Insights clave
        key_insights = []
        
        # Insight 1: Performance general
        if test_report.system_health["success_rate"] > 95:
            key_insights.append("🎯 Sistema extremadamente estable y confiable")
        elif test_report.system_health["success_rate"] > 85:
            key_insights.append("✅ Sistema estable con oportunidades de optimización")
        else:
            key_insights.append("⚠️ Sistema requiere mejoras de estabilidad")
        
        # Insight 2: Conversión
        if avg_conversion > 0.7:
            key_insights.append("🚀 Agentes de IA altamente efectivos para conversión")
        elif avg_conversion > 0.5:
            key_insights.append("📈 Agentes funcionan bien, hay margen de mejora")
        else:
            key_insights.append("🔧 Agentes requieren optimización para mejorar conversión")
        
        # Insight 3: Revenue
        total_revenue = sum(r.total_revenue for r in simulation_results.values())
        if total_revenue > 1000000:
            key_insights.append("💰 Potencial de revenue muy alto en escenarios reales")
        
        # Insight 4: Stripe Connect
        if revenue_by_mode:
            best_mode = max(revenue_by_mode.items(), key=lambda x: x[1])
            key_insights.append(f"💳 Modo Stripe más efectivo: {best_mode[0]} (${best_mode[1]:,.2f})")
        
        return {
            "correlations": correlations,
            "revenue_by_stripe_mode": revenue_by_mode,
            "key_insights": key_insights,
            "recommendations": [
                "Implementar monitoreo en tiempo real de métricas de conversión",
                "Configurar alertas automáticas para health del sistema",
                "Optimizar agentes basado en patrones de conversación exitosos",
                "Escalar infraestructura para manejar picos estacionales"
            ]
        }

# Instancia global
simulation_lab = OrkestaSimulationLab()

if __name__ == "__main__":
    # Ejecutar laboratorio completo
    print("🔬 ORKESTA SIMULATION LAB")
    print("Simulación completa multi-tenant con fees reales")
    
    async def main():
        lab = OrkestaSimulationLab()
        
        try:
            # Ejecutar laboratorio completo
            results = await lab.run_comprehensive_lab_test()
            
            # Guardar resultados
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_filename = f"orkesta_simulation_lab_results_{timestamp}.json"
            
            # Convertir resultados a formato JSON serializable
            json_results = {
                "lab_summary": {
                    "duration_seconds": results["lab_summary"]["duration_seconds"],
                    "consolidated_analysis": results["lab_summary"]["consolidated_analysis"]
                },
                "executive_summary": results["executive_summary"],
                "simulation_details": {
                    scenario: {
                        "scenario": result.scenario.value,
                        "conversations_generated": result.conversations_generated,
                        "orders_processed": result.orders_processed,
                        "total_revenue": result.total_revenue,
                        "total_margin": result.total_margin,
                        "conversion_rate": result.conversion_rate,
                        "performance_metrics": result.performance_metrics,
                        "insights": result.insights
                    }
                    for scenario, result in results["lab_summary"]["simulation_results"].items()
                }
            }
            
            with open(results_filename, "w") as f:
                json.dump(json_results, f, indent=2, default=str)
            
            print(f"\\n💾 Resultados completos guardados en: {results_filename}")
            
            # Código de salida basado en resultados
            executive = results["executive_summary"]
            if executive["system_health"] == "healthy" and executive["test_success_rate"] > 0.9:
                print("\\n🎉 LAB COMPLETADO CON ÉXITO TOTAL")
                return 0
            elif executive["test_success_rate"] > 0.8:
                print("\\n✅ LAB COMPLETADO CON ÉXITO")
                return 0
            else:
                print("\\n⚠️ LAB COMPLETADO CON OBSERVACIONES")
                return 1
            
        except Exception as e:
            print(f"❌ Error en laboratorio: {e}")
            return 2
    
    # Ejecutar
    import sys
    exit_code = asyncio.run(main())
    sys.exit(exit_code)