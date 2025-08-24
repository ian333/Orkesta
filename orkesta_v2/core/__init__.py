"""
ORKESTA V2 - Core AI Engine
Motor central de inteligencia artificial para Orkesta

Este módulo contiene el cerebro de la aplicación:
- Verificación multicapa con IA
- Motor de decisiones autónomas
- Aprendizaje continuo y adaptación
"""

from .verification import AIVerificationEngine
from .decisions import DecisionEngine
from .learning import ContinuousLearningEngine

__all__ = ['AIVerificationEngine', 'DecisionEngine', 'ContinuousLearningEngine']

class OrkestaCore:
    """Orquestador principal del motor IA"""
    
    def __init__(self):
        self.verification = AIVerificationEngine()
        self.decisions = DecisionEngine()
        self.learning = ContinuousLearningEngine()
        
    async def process_request(self, request_data, context):
        """Procesa cualquier request con verificación IA multicapa"""
        # 1. Verificación de entrada
        verification_result = await self.verification.verify_input(request_data, context)
        
        if not verification_result.is_valid:
            return {"status": "rejected", "reason": verification_result.reason}
            
        # 2. Toma de decisión
        decision = await self.decisions.make_decision(request_data, context, verification_result)
        
        # 3. Aprendizaje continuo
        await self.learning.record_interaction(request_data, decision, context)
        
        return decision