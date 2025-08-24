"""
Business Flows - Flujos de negocio inteligentes
Orquesta los flujos críticos del negocio con IA integrada
"""

from .cash_flow import CashFlowManager
from .collections import IntelligentCollections
from .sales import AutonomousSales

__all__ = ['CashFlowManager', 'IntelligentCollections', 'AutonomousSales']

class BusinessFlowOrchestrator:
    """Orquestador principal de flujos de negocio"""
    
    def __init__(self, core_engine):
        self.core = core_engine
        self.cash_flow = CashFlowManager(core_engine)
        self.collections = IntelligentCollections(core_engine)
        self.sales = AutonomousSales(core_engine)
        
    async def route_request(self, request_type: str, data: dict, context: dict):
        """Rutea requests a los flujos apropiados"""
        
        if request_type.startswith('cash_flow'):
            return await self.cash_flow.handle_request(data, context)
        elif request_type.startswith('collection'):
            return await self.collections.handle_request(data, context)  
        elif request_type.startswith('sales'):
            return await self.sales.handle_request(data, context)
        else:
            # Flujo genérico con verificación IA
            return await self.core.process_request(data, context)