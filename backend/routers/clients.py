"""
Router de Gestión de Clientes
"""
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import pandas as pd
import io

from ..models import get_db, Client, Organization, User
from .auth import get_current_user

router = APIRouter()

# Schemas
class ClientCreate(BaseModel):
    name: str
    phone: str
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    birth_date: Optional[datetime] = None

class ClientUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    birth_date: Optional[datetime] = None

class ClientResponse(BaseModel):
    id: int
    name: str
    phone: str
    email: Optional[str]
    address: Optional[str]
    notes: Optional[str]
    balance: float
    total_debt: float
    created_at: datetime

# Endpoints
@router.post("/", response_model=ClientResponse)
async def create_client(
    client_data: ClientCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Crear nuevo cliente"""
    
    # Verificar si el teléfono ya existe en la organización
    existing = db.query(Client).filter(
        Client.organization_id == current_user.organization_id,
        Client.phone == client_data.phone
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="Ya existe un cliente con ese teléfono")
    
    client = Client(
        organization_id=current_user.organization_id,
        **client_data.dict()
    )
    
    db.add(client)
    db.commit()
    db.refresh(client)
    
    return client

@router.get("/", response_model=List[ClientResponse])
async def get_clients(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener lista de clientes"""
    
    query = db.query(Client).filter(
        Client.organization_id == current_user.organization_id
    )
    
    if search:
        query = query.filter(
            (Client.name.ilike(f"%{search}%")) |
            (Client.phone.ilike(f"%{search}%")) |
            (Client.email.ilike(f"%{search}%"))
        )
    
    clients = query.offset(skip).limit(limit).all()
    return clients

@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener cliente por ID"""
    
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    return client

@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: int,
    client_data: ClientUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Actualizar cliente"""
    
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Actualizar campos
    for field, value in client_data.dict(exclude_unset=True).items():
        setattr(client, field, value)
    
    client.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(client)
    
    return client

@router.delete("/{client_id}")
async def delete_client(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Eliminar cliente"""
    
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    db.delete(client)
    db.commit()
    
    return {"message": "Cliente eliminado"}

@router.post("/import")
async def import_clients(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Importar clientes desde CSV/Excel"""
    
    try:
        # Leer archivo
        contents = await file.read()
        
        if file.filename.endswith('.csv'):
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        elif file.filename.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(io.BytesIO(contents))
        else:
            raise HTTPException(status_code=400, detail="Formato de archivo no soportado")
        
        # Validar columnas requeridas
        required_columns = ['nombre', 'telefono']
        if not all(col in df.columns for col in required_columns):
            raise HTTPException(
                status_code=400,
                detail=f"El archivo debe contener las columnas: {', '.join(required_columns)}"
            )
        
        # Procesar clientes
        imported = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # Verificar si ya existe
                existing = db.query(Client).filter(
                    Client.organization_id == current_user.organization_id,
                    Client.phone == str(row['telefono'])
                ).first()
                
                if not existing:
                    client = Client(
                        organization_id=current_user.organization_id,
                        name=row['nombre'],
                        phone=str(row['telefono']),
                        email=row.get('email', None),
                        address=row.get('direccion', None),
                        notes=row.get('notas', None)
                    )
                    db.add(client)
                    imported += 1
                else:
                    errors.append(f"Fila {index + 2}: Teléfono {row['telefono']} ya existe")
                    
            except Exception as e:
                errors.append(f"Fila {index + 2}: {str(e)}")
        
        db.commit()
        
        return {
            "imported": imported,
            "total": len(df),
            "errors": errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{client_id}/balance")
async def get_client_balance(
    client_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener estado de cuenta del cliente"""
    
    client = db.query(Client).filter(
        Client.id == client_id,
        Client.organization_id == current_user.organization_id
    ).first()
    
    if not client:
        raise HTTPException(status_code=404, detail="Cliente no encontrado")
    
    # Calcular adeudos pendientes
    pending_invoices = [
        {
            "id": inv.id,
            "number": inv.number,
            "amount": inv.amount,
            "due_date": inv.due_date,
            "status": inv.status,
            "days_overdue": (datetime.utcnow() - inv.due_date).days if inv.due_date < datetime.utcnow() else 0
        }
        for inv in client.invoices if inv.status != 'paid'
    ]
    
    # Historial de pagos
    payment_history = [
        {
            "id": pay.id,
            "amount": pay.amount,
            "date": pay.created_at,
            "method": pay.method
        }
        for pay in client.payments
    ]
    
    return {
        "client": {
            "id": client.id,
            "name": client.name,
            "phone": client.phone
        },
        "balance": client.balance,
        "total_debt": client.total_debt,
        "pending_invoices": pending_invoices,
        "payment_history": payment_history
    }