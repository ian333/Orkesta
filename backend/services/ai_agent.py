"""
Agente de IA para WhatsApp usando Azure OpenAI
Maneja ventas del sistema y soporte a clientes
"""
from typing import Dict, Any, Optional
import os
import logging
from datetime import datetime
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

class WhatsAppAIAgent:
    """
    Agente inteligente que procesa mensajes de WhatsApp
    - Vende ClienteOS a nuevos clientes
    - Ayuda a clientes existentes con cobros y citas
    """
    
    def __init__(self):
        # Configurar Azure OpenAI
        self.client = AzureOpenAI(
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_KEY"),
            api_version=os.getenv("AZURE_OPENAI_API_VERSION")
        )
        self.deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
    
    async def process_message(
        self,
        phone: str,
        message: str,
        is_client: bool,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Procesar mensaje y generar respuesta
        """
        try:
            # Determinar el tipo de conversación
            if not is_client:
                # Es un lead potencial - vender ClienteOS
                return await self._handle_sales_conversation(phone, message, context)
            else:
                # Es un cliente existente - soporte
                return await self._handle_client_support(phone, message, context)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "reply": "Disculpa, tuve un problema procesando tu mensaje. Un agente te contactará pronto.",
                "needs_human": True,
                "reason": f"Error: {str(e)}"
            }
    
    async def _handle_sales_conversation(
        self,
        phone: str,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manejar conversación de ventas para ClienteOS
        """
        # Construir prompt para ventas
        system_prompt = """
        Eres un vendedor experto de ClienteOS, un sistema de gestión para negocios mexicanos.
        
        ClienteOS ayuda a:
        - Gestionar cobros y pagos con links de pago (Stripe, MercadoPago)
        - Enviar recordatorios automáticos por WhatsApp
        - Manejar citas (ideal para consultorios)
        - Control de finanzas del negocio
        - Todo desde WhatsApp o nuestra app móvil
        
        Precios:
        - Plan Básico: $399 MXN/mes (hasta 100 clientes)
        - Plan Pro: $799 MXN/mes (hasta 500 clientes)
        - Plan Empresarial: $1,499 MXN/mes (clientes ilimitados)
        
        Beneficios clave:
        - Reduce morosidad hasta 40%
        - Ahorra 10+ horas semanales
        - Pagos con tarjeta, OXXO, transferencia
        - Sin comisiones ocultas (solo las del procesador)
        
        Tu objetivo es:
        1. Identificar el tipo de negocio del cliente
        2. Mostrar cómo ClienteOS resuelve sus problemas específicos
        3. Ofrecer una demo gratuita
        4. Cerrar la venta o agendar llamada
        
        Sé amigable, profesional y enfócate en los beneficios.
        Si mencionan la competencia, destaca que somos más económicos y especializados en México.
        """
        
        # Obtener historial de conversación
        conversation_history = context.get("history", [])
        
        # Agregar mensaje actual
        conversation_history.append({"role": "user", "content": message})
        
        # Limitar historial a últimos 10 mensajes
        if len(conversation_history) > 10:
            conversation_history = conversation_history[-10:]
        
        # Llamar a Azure OpenAI
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        reply = response.choices[0].message.content
        
        # Agregar respuesta al historial
        conversation_history.append({"role": "assistant", "content": reply})
        
        # Detectar si el cliente está interesado
        is_interested = any(word in message.lower() for word in [
            "precio", "costo", "demo", "prueba", "interesa", "más información",
            "agendar", "llamada", "contratar", "sí", "quiero"
        ])
        
        # Detectar si necesita intervención humana
        needs_human = any(word in message.lower() for word in [
            "hablar con alguien", "persona", "humano", "llamar", "teléfono"
        ])
        
        return {
            "reply": reply,
            "context": {"history": conversation_history},
            "is_interested": is_interested,
            "needs_human": needs_human,
            "reason": "Cliente solicitó contacto humano" if needs_human else None
        }
    
    async def _handle_client_support(
        self,
        phone: str,
        message: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Manejar soporte para clientes existentes
        """
        system_prompt = """
        Eres un asistente de soporte para clientes de ClienteOS.
        
        Puedes ayudar con:
        - Consultar saldos y adeudos
        - Generar links de pago
        - Agendar citas (para consultorios)
        - Consultar historial de pagos
        - Información sobre servicios y precios
        
        Si el cliente pregunta por:
        - Saldo: Indícale que puede consultarlo en la app o solicitar que un agente lo revise
        - Pago: Ofrece generar un link de pago
        - Cita: Pregunta fecha y hora deseada
        - Problemas técnicos: Escala a soporte humano
        
        Sé amable, eficiente y resolutivo.
        """
        
        conversation_history = context.get("history", [])
        conversation_history.append({"role": "user", "content": message})
        
        # Detectar intención
        intent = self._detect_intent(message)
        
        # Agregar contexto de intención al prompt
        if intent:
            conversation_history.append({
                "role": "system", 
                "content": f"El cliente parece querer: {intent}"
            })
        
        response = self.client.chat.completions.create(
            model=self.deployment,
            messages=[
                {"role": "system", "content": system_prompt},
                *conversation_history[-10:]  # Últimos 10 mensajes
            ],
            temperature=0.6,
            max_tokens=250
        )
        
        reply = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": reply})
        
        # Determinar si necesita acción específica
        needs_human = intent in ["complaint", "technical_issue", "urgent"]
        
        return {
            "reply": reply,
            "context": {"history": conversation_history, "intent": intent},
            "needs_human": needs_human,
            "reason": f"Intent detected: {intent}" if needs_human else None,
            "intent": intent
        }
    
    def _detect_intent(self, message: str) -> Optional[str]:
        """
        Detectar la intención del mensaje
        """
        message_lower = message.lower()
        
        intents = {
            "payment": ["pagar", "pago", "deuda", "adeudo", "saldo", "cuenta"],
            "appointment": ["cita", "agendar", "consulta", "horario", "disponible"],
            "complaint": ["queja", "problema", "mal", "error", "no funciona"],
            "information": ["información", "precio", "servicio", "cómo", "qué"],
            "greeting": ["hola", "buenos", "buenas", "hey", "saludos"],
            "technical_issue": ["error", "bug", "no puedo", "falla", "problema técnico"],
            "urgent": ["urgente", "emergencia", "ahora", "inmediato"]
        }
        
        for intent, keywords in intents.items():
            if any(keyword in message_lower for keyword in keywords):
                return intent
        
        return None
    
    def generate_payment_link_message(self, client_name: str, amount: float, link: str) -> str:
        """
        Generar mensaje con link de pago
        """
        return f"""
Hola {client_name} 👋

Tu link de pago está listo:

💳 Monto a pagar: ${amount:.2f} MXN
🔗 Link: {link}

Puedes pagar con:
• Tarjeta de crédito/débito
• OXXO
• Transferencia

El link es válido por 7 días.

¿Necesitas ayuda? Solo responde a este mensaje.

Gracias por tu preferencia 🙏
"""
    
    def generate_appointment_reminder(
        self,
        client_name: str,
        date: datetime,
        service: str
    ) -> str:
        """
        Generar recordatorio de cita
        """
        return f"""
Recordatorio de Cita 📅

Hola {client_name},

Te recordamos tu cita:

📍 Servicio: {service}
📅 Fecha: {date.strftime('%d de %B')}
🕐 Hora: {date.strftime('%I:%M %p')}

Por favor confirma tu asistencia respondiendo:
✅ SÍ para confirmar
❌ NO para cancelar

Si necesitas reagendar, indícanos la nueva fecha deseada.

¡Te esperamos!
"""