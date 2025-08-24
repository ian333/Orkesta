"""
Continuous Learning Engine - Aprendizaje continuo con IA
Aprende de cada transacción, decisión y resultado para mejorar continuamente
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import json

class LearningEventType(Enum):
    DECISION_MADE = "decision_made"
    PAYMENT_COMPLETED = "payment_completed" 
    FRAUD_DETECTED = "fraud_detected"
    CUSTOMER_FEEDBACK = "customer_feedback"
    BUSINESS_OUTCOME = "business_outcome"

@dataclass
class LearningEvent:
    event_type: LearningEventType
    timestamp: datetime
    data: Dict[str, Any]
    context: Dict[str, Any]
    outcome: Optional[Dict[str, Any]] = None
    labels: Optional[List[str]] = None

class ContinuousLearningEngine:
    """Motor de aprendizaje continuo - Cerebro que evoluciona"""
    
    def __init__(self):
        self.pattern_learner = PatternLearner()
        self.outcome_tracker = OutcomeTracker()
        self.model_updater = ModelUpdater()
        self.feedback_processor = FeedbackProcessor()
        
    async def record_interaction(self, request_data, decision, context):
        """Registra cada interacción para aprendizaje"""
        
        event = LearningEvent(
            event_type=LearningEventType.DECISION_MADE,
            timestamp=datetime.now(),
            data=request_data,
            context=context,
            outcome={"decision": asdict(decision)}
        )
        
        # Procesar en paralelo
        await asyncio.gather(
            self.pattern_learner.learn_from_event(event),
            self.outcome_tracker.track_decision(event),
            self._schedule_model_update(event)
        )
    
    async def learn_from_outcome(self, original_event_id: str, actual_outcome: Dict[str, Any]):
        """Aprende del resultado real vs predicción"""
        
        outcome_event = LearningEvent(
            event_type=LearningEventType.BUSINESS_OUTCOME,
            timestamp=datetime.now(),
            data={"original_event_id": original_event_id},
            context={},
            outcome=actual_outcome
        )
        
        await self.outcome_tracker.record_outcome(outcome_event)
        await self.model_updater.update_from_outcome(outcome_event)
    
    async def process_feedback(self, feedback_data: Dict[str, Any]):
        """Procesa feedback de usuarios/clientes"""
        
        feedback_event = LearningEvent(
            event_type=LearningEventType.CUSTOMER_FEEDBACK,
            timestamp=datetime.now(),
            data=feedback_data,
            context={}
        )
        
        await self.feedback_processor.process_feedback(feedback_event)
        
    async def _schedule_model_update(self, event):
        """Programa actualización de modelos"""
        # En producción, esto sería asíncrono con cola de trabajos
        if self._should_trigger_model_update(event):
            await self.model_updater.trigger_update()
    
    def _should_trigger_model_update(self, event) -> bool:
        """Determina si se debe actualizar el modelo"""
        # Actualizar cada 1000 eventos o si hay fraude detectado
        return (
            event.event_type == LearningEventType.FRAUD_DETECTED or
            self.pattern_learner.get_event_count() % 1000 == 0
        )


class PatternLearner:
    """Aprende patrones de comportamiento y fraude"""
    
    def __init__(self):
        self.event_count = 0
        self.patterns = {
            'successful_transactions': [],
            'failed_transactions': [],
            'fraud_attempts': [],
            'customer_behaviors': []
        }
    
    async def learn_from_event(self, event: LearningEvent):
        """Aprende patrones de cada evento"""
        self.event_count += 1
        
        # Extraer características clave
        features = self._extract_features(event)
        
        # Clasificar el patrón
        pattern_type = self._classify_pattern(event, features)
        
        # Almacenar para aprendizaje
        if pattern_type in self.patterns:
            self.patterns[pattern_type].append({
                'timestamp': event.timestamp,
                'features': features,
                'outcome': event.outcome
            })
            
        # Limpiar patrones antiguos
        await self._cleanup_old_patterns()
    
    def _extract_features(self, event: LearningEvent) -> Dict[str, Any]:
        """Extrae características clave del evento"""
        
        features = {
            'amount': event.data.get('amount', 0),
            'payment_method': event.data.get('payment_method', 'unknown'),
            'channel': event.context.get('channel', 'unknown'),
            'hour_of_day': event.timestamp.hour,
            'day_of_week': event.timestamp.weekday(),
            'customer_age_days': event.context.get('customer_age_days', 0),
            'previous_transactions': event.context.get('total_transactions', 0)
        }
        
        # Características de verificación
        if 'verification_result' in event.context:
            vr = event.context['verification_result']
            features.update({
                'verification_confidence': getattr(vr, 'confidence', 0),
                'verification_flags_count': len(getattr(vr, 'flags', [])),
                'verification_level': str(getattr(vr, 'level', 'unknown'))
            })
        
        return features
    
    def _classify_pattern(self, event: LearningEvent, features: Dict[str, Any]) -> str:
        """Clasifica el tipo de patrón"""
        
        if event.event_type == LearningEventType.FRAUD_DETECTED:
            return 'fraud_attempts'
            
        if event.outcome and event.outcome.get('decision', {}).get('type') == 'approve':
            return 'successful_transactions'
        elif event.outcome and event.outcome.get('decision', {}).get('type') == 'reject':
            return 'failed_transactions'
        else:
            return 'customer_behaviors'
    
    async def _cleanup_old_patterns(self):
        """Limpia patrones antiguos para evitar acumulación"""
        cutoff_date = datetime.now() - timedelta(days=90)  # 90 días
        
        for pattern_type in self.patterns:
            self.patterns[pattern_type] = [
                p for p in self.patterns[pattern_type] 
                if p['timestamp'] > cutoff_date
            ]
    
    def get_event_count(self) -> int:
        return self.event_count


class OutcomeTracker:
    """Rastrea resultados reales vs predicciones"""
    
    def __init__(self):
        self.pending_outcomes = {}  # Decisiones esperando resultado
        self.completed_outcomes = []  # Resultados confirmados
        
    async def track_decision(self, event: LearningEvent):
        """Rastrea una decisión para verificar resultado futuro"""
        
        if event.event_type == LearningEventType.DECISION_MADE:
            decision_id = f"{event.timestamp.isoformat()}_{hash(str(event.data))}"
            
            self.pending_outcomes[decision_id] = {
                'decision': event.outcome.get('decision'),
                'timestamp': event.timestamp,
                'data': event.data,
                'context': event.context,
                'expected_outcome': self._predict_outcome(event)
            }
    
    async def record_outcome(self, outcome_event: LearningEvent):
        """Registra el resultado real"""
        
        original_event_id = outcome_event.data.get('original_event_id')
        
        if original_event_id in self.pending_outcomes:
            original = self.pending_outcomes.pop(original_event_id)
            
            self.completed_outcomes.append({
                'original_decision': original,
                'actual_outcome': outcome_event.outcome,
                'accuracy': self._calculate_accuracy(original, outcome_event.outcome),
                'completed_at': outcome_event.timestamp
            })
    
    def _predict_outcome(self, event: LearningEvent) -> Dict[str, Any]:
        """Predice el resultado esperado"""
        decision = event.outcome.get('decision', {})
        
        if decision.get('type') == 'approve':
            return {'expected': 'success', 'confidence': decision.get('confidence', 0.5)}
        elif decision.get('type') == 'reject':
            return {'expected': 'prevented_loss', 'confidence': decision.get('confidence', 0.5)}
        else:
            return {'expected': 'review_needed', 'confidence': decision.get('confidence', 0.5)}
    
    def _calculate_accuracy(self, original, actual_outcome) -> float:
        """Calcula precisión de la predicción"""
        expected = original['expected_outcome']['expected']
        actual = actual_outcome.get('result', 'unknown')
        
        # Mapeo simple de resultados
        accuracy_map = {
            ('success', 'completed'): 1.0,
            ('success', 'failed'): 0.0,
            ('prevented_loss', 'fraud_confirmed'): 1.0,
            ('prevented_loss', 'false_positive'): 0.0,
            ('review_needed', 'manual_approved'): 0.8,
            ('review_needed', 'manual_rejected'): 0.8
        }
        
        return accuracy_map.get((expected, actual), 0.5)


class ModelUpdater:
    """Actualiza modelos ML basado en aprendizaje"""
    
    def __init__(self):
        self.last_update = datetime.now()
        self.update_frequency = timedelta(hours=6)  # Actualizar cada 6 horas
        
    async def update_from_outcome(self, outcome_event: LearningEvent):
        """Actualiza modelos basado en resultado real"""
        
        # En producción, esto dispararia reentrenamiento de modelos ML
        print(f"[ML Update] Aprendiendo de resultado: {outcome_event.outcome}")
        
        # Simular actualización de pesos/parámetros
        await self._update_decision_weights(outcome_event)
        await self._update_risk_models(outcome_event)
    
    async def trigger_update(self):
        """Dispara actualización programada de modelos"""
        
        if datetime.now() - self.last_update > self.update_frequency:
            await self._full_model_retrain()
            self.last_update = datetime.now()
    
    async def _update_decision_weights(self, outcome_event: LearningEvent):
        """Actualiza pesos del motor de decisiones"""
        # Implementar actualización incremental de pesos
        pass
    
    async def _update_risk_models(self, outcome_event: LearningEvent):
        """Actualiza modelos de riesgo"""
        # Implementar actualización de modelos de riesgo
        pass
    
    async def _full_model_retrain(self):
        """Reentrenamiento completo de modelos"""
        print(f"[ML Retrain] Iniciando reentrenamiento completo de modelos...")
        # Implementar reentrenamiento completo


class FeedbackProcessor:
    """Procesa feedback de usuarios y clientes"""
    
    async def process_feedback(self, feedback_event: LearningEvent):
        """Procesa feedback para mejora continua"""
        
        feedback_data = feedback_event.data
        feedback_type = feedback_data.get('type', 'general')
        
        if feedback_type == 'decision_quality':
            await self._process_decision_feedback(feedback_data)
        elif feedback_type == 'user_experience':
            await self._process_ux_feedback(feedback_data)
        elif feedback_type == 'payment_experience':
            await self._process_payment_feedback(feedback_data)
        
    async def _process_decision_feedback(self, feedback_data):
        """Procesa feedback sobre calidad de decisiones"""
        rating = feedback_data.get('rating', 3)  # 1-5
        decision_id = feedback_data.get('decision_id')
        
        if rating <= 2:
            # Decisión mal calificada - ajustar modelos
            print(f"[Feedback] Decisión {decision_id} mal calificada ({rating}/5)")
            
    async def _process_ux_feedback(self, feedback_data):
        """Procesa feedback de experiencia de usuario"""
        channel = feedback_data.get('channel', 'unknown')
        satisfaction = feedback_data.get('satisfaction', 3)
        
        if satisfaction <= 2:
            print(f"[Feedback] Baja satisfacción en {channel}: {satisfaction}/5")
            
    async def _process_payment_feedback(self, feedback_data):
        """Procesa feedback de experiencia de pago"""
        payment_method = feedback_data.get('payment_method', 'unknown')
        success_rating = feedback_data.get('success_rating', 3)
        
        if success_rating <= 2:
            print(f"[Feedback] Problemas con {payment_method}: {success_rating}/5")