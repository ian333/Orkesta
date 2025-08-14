"""
Router de Citas (para consultorios)
"""
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, timedelta

from ..models import get_db, Appointment, Client, User
from .auth import get_current_user

router = APIRouter()

# Schemas
class AppointmentCreate(BaseModel):
    client_id: int
    date: datetime
    duration_minutes: int = 30
    service: str
    price: float
    notes: Optional[str] = None

class AppointmentUpdate(BaseModel):
    date: Optional[datetime] = None
    duration_minutes: Optional[int] = None
    service: Optional[str] = None
    price: Optional[float] = None
    status: Optional[str] = None
    notes: Optional[str] = None

class AppointmentResponse(BaseModel):
    id: int
    client_id: int
    client_name: str
    date: datetime
    duration_minutes: int
    service: str
    price: float
    status: str
    notes: Optional[str]
    reminder_sent: bool

# Endpoints
@router.post("/", response_model=AppointmentResponse)
async def create_appointment(
    appointment_data: AppointmentCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nueva cita"""
    
    # Verificar que el cliente existe
    client = db.query(Client).filter(
        Client.id == appointment_data.client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Verificar disponibilidad
    existing = db.query(Appointment).filter(
        Appointment.organization_id == current_user.organization_id,
        Appointment.date == appointment_data.date,
        Appointment.status != "cancelled"
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe una cita en ese horario")
    
    appointment = Appointment(
        organization_id=current_user.organization_id,
        **appointment_data.dict()
    )
    
    db.add(appointment)
    db.commit()
    db.refresh(appointment)
    
    return {
        **appointment.__dict__,
        "client_name": client.name
    }

@router.get("/", response_model=List[AppointmentResponse])
async def get_appointments(
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    status: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener citas"""
    
    query = db.query(Appointment).filter(
        Appointment.organization_id == current_user.organization_id
    )
    
    if date_from:
        query = query.filter(Appointment.date >= date_from)
    
    if date_to:
        query = query.filter(Appointment.date <= date_to)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    appointments = query.order_by(Appointment.date).all()
    
    return [
        {
            **app.__dict__,
            "client_name": app.client.name if app.client else "Unknown"
        }
        for app in appointments
    ]

@router.get("/today")
async def get_today_appointments(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener citas de hoy"""
    
    today = datetime.now().date()
    tomorrow = today + timedelta(days=1)
    
    appointments = db.query(Appointment).filter(
        Appointment.organization_id == current_user.organization_id,
        Appointment.date >= today,
        Appointment.date < tomorrow,
        Appointment.status != "cancelled"
    ).order_by(Appointment.date).all()
    
    return [
        {
            "id": app.id,
            "time": app.date.strftime("%I:%M %p"),
            "client": app.client.name if app.client else "Unknown",
            "service": app.service,
            "duration": app.duration_minutes,
            "status": app.status
        }
        for app in appointments
    ]

@router.put("/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: int,
    appointment_data: AppointmentUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar cita"""
    
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.organization_id == current_user.organization_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    # Actualizar campos
    for field, value in appointment_data.dict(exclude_unset=True).items():
        setattr(appointment, field, value)
    
    db.commit()
    db.refresh(appointment)
    
    return {
        **appointment.__dict__,
        "client_name": appointment.client.name if appointment.client else "Unknown"
    }

@router.post("/{appointment_id}/confirm")
async def confirm_appointment(
    appointment_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Confirmar cita"""
    
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.organization_id == current_user.organization_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    appointment.status = "confirmed"
    db.commit()
    
    # Aquí podrías enviar confirmación por WhatsApp
    
    return {"message": "Cita confirmada"}

@router.post("/{appointment_id}/cancel")
async def cancel_appointment(
    appointment_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancelar cita"""
    
    appointment = db.query(Appointment).filter(
        Appointment.id == appointment_id,
        Appointment.organization_id == current_user.organization_id
    ).first()
    
    if not appointment:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    appointment.status = "cancelled"
    if reason:
        appointment.notes = f"Cancelada: {reason}"
    
    db.commit()
    
    # Aquí podrías notificar al cliente por WhatsApp
    
    return {"message": "Cita cancelada"}

@router.get("/available-slots")
async def get_available_slots(
    date: datetime,
    duration_minutes: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener horarios disponibles"""
    
    # Configuración de horario de trabajo (esto podría venir de settings)
    work_start = 9  # 9 AM
    work_end = 18   # 6 PM
    
    # Obtener citas del día
    date_start = date.replace(hour=0, minute=0, second=0)
    date_end = date_start + timedelta(days=1)
    
    existing_appointments = db.query(Appointment).filter(
        Appointment.organization_id == current_user.organization_id,
        Appointment.date >= date_start,
        Appointment.date < date_end,
        Appointment.status != "cancelled"
    ).all()
    
    # Generar slots disponibles
    available_slots = []
    current_time = date.replace(hour=work_start, minute=0)
    end_time = date.replace(hour=work_end, minute=0)
    
    while current_time < end_time:
        # Verificar si el slot está disponible
        is_available = True
        slot_end = current_time + timedelta(minutes=duration_minutes)
        
        for app in existing_appointments:
            app_end = app.date + timedelta(minutes=app.duration_minutes)
            if (current_time < app_end and slot_end > app.date):
                is_available = False
                break
        
        if is_available:
            available_slots.append({
                "start": current_time.strftime("%I:%M %p"),
                "end": slot_end.strftime("%I:%M %p"),
                "datetime": current_time.isoformat()
            })
        
        current_time += timedelta(minutes=30)
    
    return {"date": date.date(), "available_slots": available_slots}