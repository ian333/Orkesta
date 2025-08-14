"""
Router de WhatsApp - Ventas del sistema y gestión de clientes
"""
from fastapi import APIRouter, HTTPException, Request, Response
from sqlalchemy.orm import Session
from typing import Dict, Any
from pydantic import BaseModel
import httpx
import os
import logging
from datetime import datetime
import json

from ..models import get_db, Client, WhatsAppConversation, Organization, Invoice
from ..services.ai_agent import WhatsAppAIAgent

logger = logging.getLogger(__name__)

router = APIRouter()

# Configuración WhatsApp
WA_TOKEN = os.getenv("WA_ACCESS_TOKEN")
WA_PHONE_NUMBER_ID = os.getenv("WA_PHONE_NUMBER_ID")
WA_VERIFY_TOKEN = os.getenv("WA_VERIFY_TOKEN", "clienteos_verify_token")

# Agente AI para procesar mensajes
ai_agent = WhatsAppAIAgent()

# ========== SCHEMAS ==========

class WhatsAppMessage(BaseModel):
    to: str
    message: str
    type: str = "text"

class WebhookData(BaseModel):
    entry: list

# ========== WEBHOOKS DE WHATSAPP ==========

@router.get("/webhook")
async def verify_webhook(hub_mode: str = "", hub_verify_token: str = "", hub_challenge: str = ""):
    """Verificación del webhook de WhatsApp"""
    if hub_mode == "subscribe" and hub_verify_token == WA_VERIFY_TOKEN:
        logger.info("WhatsApp webhook verified")
        return Response(content=hub_challenge)
    raise HTTPException(status_code=403, detail="Verification failed")

@router.post("/webhook")
async def receive_message(request: Request, db: Session = Depends(get_db)):
    """Recibir mensajes de WhatsApp"""
    try:
        data = await request.json()
        
        # Procesar mensajes entrantes
        if "entry" in data:
            for entry in data["entry"]:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    
                    # Procesar mensajes
                    if "messages" in value:
                        for message in value["messages"]:
                            await process_incoming_message(message, db)
                    
                    # Procesar estados de mensajes
                    if "statuses" in value:
                        for status in value["statuses"]:
                            logger.info(f"Message status update: {status}")
        
        return {"status": "ok"}
        
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return {"status": "error", "message": str(e)}

async def process_incoming_message(message: dict, db: Session):
    """Procesar mensaje entrante"""
    try:
        phone = message["from"]
        text = message.get("text", {}).get("body", "")
        message_type = message["type"]
        
        logger.info(f"Message from {phone}: {text}")
        
        # Buscar o crear conversación
        conversation = db.query(WhatsAppConversation).filter(
            WhatsAppConversation.phone_number == phone
        ).first()
        
        if not conversation:
            conversation = WhatsAppConversation(
                phone_number=phone,
                last_message=text,
                last_message_at=datetime.utcnow(),
                status="active"
            )
            db.add(conversation)
        else:
            conversation.last_message = text
            conversation.last_message_at = datetime.utcnow()
        
        # Buscar si es cliente existente
        client = db.query(Client).filter(Client.phone == phone).first()
        
        # Procesar con IA según contexto
        response = await ai_agent.process_message(
            phone=phone,
            message=text,
            is_client=client is not None,
            context=conversation.context or {}
        )
        
        # Actualizar contexto de la conversación
        conversation.context = response.get("context", {})
        
        # Si es un lead interesado, marcarlo
        if response.get("is_interested"):
            conversation.is_lead = True
            conversation.lead_status = "interested"
        
        db.commit()
        
        # Enviar respuesta
        await send_whatsapp_message(phone, response["reply"])
        
        # Si necesita acción humana
        if response.get("needs_human"):
            await notify_admin(phone, text, response.get("reason"))
        
    except Exception as e:
        logger.error(f"Error processing message: {e}")

# ========== ENVÍO DE MENSAJES ==========

async def send_whatsapp_message(to: str, message: str):
    """Enviar mensaje de WhatsApp"""
    try:
        url = f"https://graph.facebook.com/v18.0/{WA_PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {WA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": message}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
        logger.info(f"Message sent to {to}")
        return response.json()
        
    except Exception as e:
        logger.error(f"Error sending WhatsApp message: {e}")
        raise

@router.post("/send-message")
async def send_message_endpoint(message: WhatsAppMessage):
    """Endpoint para enviar mensajes manualmente"""
    try:
        result = await send_whatsapp_message(message.to, message.message)
        return {"status": "sent", "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ========== PLANTILLAS DE MENSAJES ==========

@router.post("/send-template")
async def send_template_message(
    to: str,
    template_name: str,
    parameters: Dict[str, Any] = {}
):
    """Enviar mensaje con plantilla aprobada"""
    try:
        url = f"https://graph.facebook.com/v18.0/{WA_PHONE_NUMBER_ID}/messages"
        
        headers = {
            "Authorization": f"Bearer {WA_TOKEN}",
            "Content-Type": "application/json"
        }
        
        # Construir componentes de la plantilla
        components = []
        if parameters:
            body_params = [{"type": "text", "text": v} for v in parameters.values()]
            components.append({
                "type": "body",
                "parameters": body_params
            })
        
        data = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {"code": "es_MX"},
                "components": components
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            response.raise_for_status()
            
        return {"status": "sent", "result": response.json()}
        
    except Exception as e:
        logger.error(f"Error sending template: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== CAMPAÑAS Y BROADCASTS ==========

@router.post("/broadcast")
async def send_broadcast(
    organization_id: int,
    message: str,
    filter_criteria: Dict[str, Any] = {},
    db: Session = Depends(get_db)
):
    """Enviar mensaje masivo a clientes"""
    try:
        # Obtener clientes según criterios
        query = db.query(Client).filter(
            Client.organization_id == organization_id,
            Client.wa_opted_in == True
        )
        
        # Aplicar filtros adicionales
        if filter_criteria.get("has_debt"):
            query = query.filter(Client.total_debt > 0)
        
        if filter_criteria.get("days_overdue"):
            # Aquí agregarías lógica para filtrar por días de vencimiento
            pass
        
        clients = query.all()
        
        sent_count = 0
        failed_count = 0
        
        for client in clients:
            try:
                # Personalizar mensaje
                personalized_message = message.replace("{name}", client.name)
                personalized_message = personalized_message.replace("{debt}", f"${client.total_debt:.2f}")
                
                await send_whatsapp_message(client.phone, personalized_message)
                sent_count += 1
                
                # Esperar un poco entre mensajes para no saturar
                import asyncio
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Failed to send to {client.phone}: {e}")
                failed_count += 1
        
        return {
            "total": len(clients),
            "sent": sent_count,
            "failed": failed_count
        }
        
    except Exception as e:
        logger.error(f"Broadcast error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ========== GESTIÓN DE LEADS ==========

@router.get("/leads")
async def get_leads(db: Session = Depends(get_db)):
    """Obtener leads interesados en ClienteOS"""
    leads = db.query(WhatsAppConversation).filter(
        WhatsAppConversation.is_lead == True,
        WhatsAppConversation.lead_status != "closed"
    ).all()
    
    return [{
        "phone": lead.phone_number,
        "last_message": lead.last_message,
        "last_contact": lead.last_message_at,
        "status": lead.lead_status,
        "context": lead.context
    } for lead in leads]

@router.post("/leads/{phone}/update-status")
async def update_lead_status(
    phone: str,
    status: str,
    notes: str = "",
    db: Session = Depends(get_db)
):
    """Actualizar estado de un lead"""
    conversation = db.query(WhatsAppConversation).filter(
        WhatsAppConversation.phone_number == phone
    ).first()
    
    if not conversation:
        raise HTTPException(status_code=404, detail="Lead no encontrado")
    
    conversation.lead_status = status
    if notes:
        context = conversation.context or {}
        context["notes"] = notes
        conversation.context = context
    
    db.commit()
    
    return {"status": "updated", "new_status": status}

# ========== FUNCIONES AUXILIARES ==========

async def notify_admin(phone: str, message: str, reason: str):
    """Notificar al administrador que se necesita atención humana"""
    # Aquí podrías enviar un email, SMS o notificación push
    logger.info(f"Admin notification needed for {phone}: {reason}")
    
    # También podrías enviar un mensaje de WhatsApp al admin
    admin_message = f"""
    ⚠️ Atención requerida:
    
    Cliente: {phone}
    Mensaje: {message}
    Razón: {reason}
    
    Por favor revisa la conversación.
    """
    
    # await send_whatsapp_message(ADMIN_PHONE, admin_message)