"""
AI Verification Engine - Verificación multicapa con IA
Verifica CADA transacción, mensaje, decisión en tiempo real
"""

import asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class VerificationLevel(Enum):
    BASIC = "basic"           # Verificación básica
    ENHANCED = "enhanced"     # Verificación con ML
    DEEP = "deep"            # Verificación profunda con IA
    CRITICAL = "critical"    # Máxima verificación para transacciones grandes

@dataclass
class VerificationResult:
    is_valid: bool
    confidence: float  # 0.0 - 1.0
    level: VerificationLevel
    reason: Optional[str] = None
    flags: List[str] = None
    additional_checks_needed: List[str] = None

class AIVerificationEngine:
    """Motor de verificación con IA - CORE de seguridad"""
    
    def __init__(self):
        self.risk_models = {}
        self.pattern_detection = PatternDetector()
        self.anomaly_detector = AnomalyDetector()
        
    async def verify_input(self, data: Dict[Any, Any], context: Dict[str, Any]) -> VerificationResult:
        """Verificación multicapa de entrada"""
        
        # Determinar nivel de verificación requerido
        verification_level = self._determine_verification_level(data, context)
        
        # Ejecutar verificaciones en paralelo
        checks = await asyncio.gather(
            self._verify_data_integrity(data),
            self._verify_business_rules(data, context),
            self._verify_ml_patterns(data, context),
            self._verify_anomalies(data, context)
        )
        
        return self._consolidate_results(checks, verification_level)
    
    def _determine_verification_level(self, data, context) -> VerificationLevel:
        """Determina el nivel de verificación necesario"""
        
        # Transacciones de alto valor = verificación crítica
        if context.get('transaction_amount', 0) > 50000:  # +50k MXN
            return VerificationLevel.CRITICAL
            
        # WhatsApp commerce = verificación enhanced
        if context.get('channel') == 'whatsapp':
            return VerificationLevel.ENHANCED
            
        # Nuevos clientes = verificación deep
        if context.get('customer_age_days', float('inf')) < 30:
            return VerificationLevel.DEEP
            
        return VerificationLevel.BASIC
    
    async def _verify_data_integrity(self, data) -> Dict:
        """Verifica integridad de datos"""
        flags = []
        
        # Campos obligatorios
        required_fields = data.get('_required_fields', [])
        for field in required_fields:
            if field not in data:
                flags.append(f"missing_required_field_{field}")
        
        # Formato de datos
        if 'phone' in data and not self._is_valid_mexican_phone(data['phone']):
            flags.append("invalid_phone_format")
            
        if 'email' in data and not self._is_valid_email(data['email']):
            flags.append("invalid_email_format")
            
        return {
            "type": "integrity",
            "valid": len(flags) == 0,
            "flags": flags,
            "confidence": 1.0 if len(flags) == 0 else 0.0
        }
    
    async def _verify_business_rules(self, data, context) -> Dict:
        """Verifica reglas de negocio"""
        flags = []
        confidence = 1.0
        
        # Límites de transacción
        amount = data.get('amount', 0)
        if amount > context.get('daily_limit', 100000):  # 100k MXN diario
            flags.append("exceeds_daily_limit")
            confidence = 0.2
            
        # Horarios permitidos
        current_hour = datetime.now().hour
        if current_hour < 6 or current_hour > 22:  # 6 AM - 10 PM
            flags.append("outside_business_hours")
            confidence *= 0.8
            
        return {
            "type": "business_rules",
            "valid": len(flags) == 0,
            "flags": flags,
            "confidence": confidence
        }
    
    async def _verify_ml_patterns(self, data, context) -> Dict:
        """Verificación con ML patterns"""
        # Aquí iría la integración con modelos ML reales
        # Por ahora, simulamos detección de patrones
        
        suspicious_patterns = []
        confidence = 0.95
        
        # Detectar patrones de fraude conocidos
        if self.pattern_detection.detect_fraud_pattern(data, context):
            suspicious_patterns.append("known_fraud_pattern")
            confidence = 0.1
            
        # Detectar comportamiento inusual
        if self.pattern_detection.detect_unusual_behavior(data, context):
            suspicious_patterns.append("unusual_behavior")
            confidence *= 0.6
            
        return {
            "type": "ml_patterns",
            "valid": len(suspicious_patterns) == 0,
            "flags": suspicious_patterns,
            "confidence": confidence
        }
    
    async def _verify_anomalies(self, data, context) -> Dict:
        """Detección de anomalías"""
        anomalies = []
        confidence = 0.9
        
        # Detectar anomalías en el monto
        if self.anomaly_detector.is_amount_anomaly(data.get('amount', 0), context):
            anomalies.append("amount_anomaly")
            confidence *= 0.7
            
        # Detectar anomalías de ubicación
        if self.anomaly_detector.is_location_anomaly(data.get('location'), context):
            anomalies.append("location_anomaly")
            confidence *= 0.8
            
        return {
            "type": "anomalies",
            "valid": len(anomalies) == 0,
            "flags": anomalies,
            "confidence": confidence
        }
    
    def _consolidate_results(self, checks, level) -> VerificationResult:
        """Consolida todos los resultados de verificación"""
        all_flags = []
        min_confidence = 1.0
        is_valid = True
        
        for check in checks:
            if not check['valid']:
                is_valid = False
            all_flags.extend(check['flags'])
            min_confidence = min(min_confidence, check['confidence'])
            
        # Ajustar confianza según el nivel
        if level == VerificationLevel.CRITICAL and min_confidence < 0.99:
            is_valid = False
            
        return VerificationResult(
            is_valid=is_valid,
            confidence=min_confidence,
            level=level,
            reason=self._generate_reason(all_flags, is_valid),
            flags=all_flags
        )
    
    def _generate_reason(self, flags, is_valid):
        """Genera razón human-readable"""
        if is_valid:
            return "Verificación exitosa"
            
        if 'known_fraud_pattern' in flags:
            return "Patrón de fraude detectado"
        if 'exceeds_daily_limit' in flags:
            return "Excede límite diario permitido"
        if 'missing_required_field' in ' '.join(flags):
            return "Faltan campos requeridos"
            
        return f"Verificación falló: {len(flags)} problemas detectados"
    
    def _is_valid_mexican_phone(self, phone):
        """Valida teléfono mexicano"""
        import re
        # +52 1 (área) numero o +52 (área) numero
        pattern = r'^\+52[1-9][0-9]{9,10}$'
        return bool(re.match(pattern, str(phone).replace(' ', '').replace('-', '')))
    
    def _is_valid_email(self, email):
        """Valida email"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, str(email)))


class PatternDetector:
    """Detector de patrones con ML"""
    
    def detect_fraud_pattern(self, data, context):
        """Detecta patrones conocidos de fraude"""
        # Implementar detección real de fraude
        return False
        
    def detect_unusual_behavior(self, data, context):
        """Detecta comportamiento inusual del usuario"""
        # Implementar detección de comportamiento
        return False


class AnomalyDetector:
    """Detector de anomalías"""
    
    def is_amount_anomaly(self, amount, context):
        """Detecta si el monto es anómalo para este usuario"""
        avg_amount = context.get('user_avg_amount', 1000)
        return amount > avg_amount * 10  # 10x el promedio
        
    def is_location_anomaly(self, location, context):
        """Detecta si la ubicación es anómala"""
        # Implementar detección de ubicación
        return False