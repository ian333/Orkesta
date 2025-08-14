"""
Router de Pagos con Stripe
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timedelta
from pydantic import BaseModel
import stripe
import os
import logging

from ..models import get_db, Client, Invoice, Payment, Organization

logger = logging.getLogger(__name__)

# Configurar Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

router = APIRouter()

# ========== SCHEMAS ==========

class CreateInvoiceRequest(BaseModel):
    client_id: int
    amount: float
    description: str
    due_date: Optional[datetime] = None

class PaymentLinkResponse(BaseModel):
    url: str
    invoice_id: int
    amount: float
    expires_at: Optional[datetime] = None

class PaymentStatus(BaseModel):
    invoice_id: int
    status: str
    amount_paid: float
    payment_date: Optional[datetime] = None

# ========== ENDPOINTS ==========

@router.post("/create-invoice")
async def create_invoice(
    request: CreateInvoiceRequest,
    db: Session = Depends(get_db)
):
    """Crear una factura/cuenta por cobrar"""
    try:
        # Obtener cliente
        client = db.query(Client).filter(Client.id == request.client_id).first()
        if not client:
            raise HTTPException(status_code=404, detail="Cliente no encontrado")
        
        # Crear factura
        invoice = Invoice(
            organization_id=client.organization_id,
            client_id=client.id,
            amount=request.amount,
            description=request.description,
            due_date=request.due_date or datetime.utcnow() + timedelta(days=7),
            status="pending",
            number=f"INV-{datetime.now().strftime('%Y%m%d')}-{client.id}"
        )
        
        db.add(invoice)
        db.commit()
        db.refresh(invoice)
        
        # Actualizar deuda del cliente
        client.total_debt += request.amount
        db.commit()
        
        return {
            "invoice_id": invoice.id,
            "number": invoice.number,
            "amount": invoice.amount,
            "due_date": invoice.due_date,
            "status": invoice.status
        }
        
    except Exception as e:
        logger.error(f"Error creating invoice: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/create-payment-link/{invoice_id}")
async def create_payment_link(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Crear link de pago con Stripe"""
    try:
        # Obtener factura
        invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
        if not invoice:
            raise HTTPException(status_code=404, detail="Factura no encontrada")
        
        # Obtener cliente y organización
        client = db.query(Client).filter(Client.id == invoice.client_id).first()
        org = db.query(Organization).filter(Organization.id == invoice.organization_id).first()
        
        # Crear sesión de checkout en Stripe
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'mxn',
                    'product_data': {
                        'name': f'Pago para {org.name}',
                        'description': invoice.description or f'Factura #{invoice.number}',
                    },
                    'unit_amount': int(invoice.amount * 100),  # Stripe usa centavos
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'http://localhost:8000/payment-success?invoice_id={invoice_id}',
            cancel_url=f'http://localhost:8000/payment-cancelled',
            metadata={
                'invoice_id': str(invoice_id),
                'client_id': str(client.id),
                'organization_id': str(org.id)
            },
            customer_email=client.email,
        )
        
        # Guardar link en la factura
        invoice.payment_link = checkout_session.url
        invoice.stripe_payment_intent_id = checkout_session.payment_intent
        db.commit()
        
        return PaymentLinkResponse(
            url=checkout_session.url,
            invoice_id=invoice.id,
            amount=invoice.amount,
            expires_at=datetime.fromtimestamp(checkout_session.expires_at)
        )
        
    except stripe.error.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=f"Error de Stripe: {str(e)}")
    except Exception as e:
        logger.error(f"Error creating payment link: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/webhook")
async def stripe_webhook(request: dict, db: Session = Depends(get_db)):
    """Procesar webhooks de Stripe"""
    try:
        # En producción, verificar la firma del webhook
        event = request
        
        # Procesar según el tipo de evento
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            
            # Obtener metadata
            invoice_id = int(session['metadata']['invoice_id'])
            
            # Actualizar factura
            invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
            if invoice:
                invoice.status = 'paid'
                invoice.paid_at = datetime.utcnow()
                
                # Crear registro de pago
                payment = Payment(
                    invoice_id=invoice_id,
                    client_id=invoice.client_id,
                    amount=session['amount_total'] / 100,
                    method='card',
                    stripe_charge_id=session['payment_intent'],
                    status='completed'
                )
                db.add(payment)
                
                # Actualizar deuda del cliente
                client = db.query(Client).filter(Client.id == invoice.client_id).first()
                if client:
                    client.total_debt -= invoice.amount
                    client.balance += invoice.amount
                
                db.commit()
                
                logger.info(f"Payment processed for invoice {invoice_id}")
        
        return {"status": "success"}
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/invoice/{invoice_id}/status")
async def get_payment_status(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Obtener estado de pago de una factura"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    # Obtener pagos asociados
    payments = db.query(Payment).filter(Payment.invoice_id == invoice_id).all()
    total_paid = sum(p.amount for p in payments)
    
    return PaymentStatus(
        invoice_id=invoice.id,
        status=invoice.status,
        amount_paid=total_paid,
        payment_date=invoice.paid_at
    )

@router.get("/pending-invoices")
async def get_pending_invoices(
    organization_id: int,
    db: Session = Depends(get_db)
):
    """Obtener facturas pendientes de una organización"""
    invoices = db.query(Invoice).filter(
        Invoice.organization_id == organization_id,
        Invoice.status.in_(['pending', 'overdue'])
    ).all()
    
    return [{
        "id": inv.id,
        "client_name": inv.client.name if inv.client else "Unknown",
        "amount": inv.amount,
        "due_date": inv.due_date,
        "status": inv.status,
        "days_overdue": (datetime.utcnow() - inv.due_date).days if inv.due_date < datetime.utcnow() else 0
    } for inv in invoices]

@router.post("/send-payment-reminder/{invoice_id}")
async def send_payment_reminder(
    invoice_id: int,
    db: Session = Depends(get_db)
):
    """Enviar recordatorio de pago por WhatsApp/SMS"""
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(status_code=404, detail="Factura no encontrada")
    
    client = invoice.client
    
    # Aquí integrarías con WhatsApp Business API o Twilio
    message = f"""
    Hola {client.name},
    
    Te recordamos que tienes un pago pendiente de ${invoice.amount:.2f} MXN.
    
    Puedes pagar aquí: {invoice.payment_link}
    
    Gracias por tu preferencia.
    """
    
    # Por ahora solo simulamos el envío
    logger.info(f"Reminder sent to {client.phone}: {message}")
    
    return {
        "status": "sent",
        "recipient": client.phone,
        "invoice_id": invoice_id
    }