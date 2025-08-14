"""
Router de Dashboard y Reportes
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta
from typing import Optional

from ..models import get_db, Client, Invoice, Payment, Appointment, Transaction, User
from .auth import get_current_user

router = APIRouter()

@router.get("/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener resumen del dashboard"""
    
    org_id = current_user.organization_id
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    # Métricas de clientes
    total_clients = db.query(func.count(Client.id)).filter(
        Client.organization_id == org_id
    ).scalar()
    
    # Métricas de cobros
    total_debt = db.query(func.sum(Invoice.amount)).filter(
        Invoice.organization_id == org_id,
        Invoice.status == "pending"
    ).scalar() or 0
    
    # Cobros del mes
    monthly_collected = db.query(func.sum(Payment.amount)).join(Invoice).filter(
        Invoice.organization_id == org_id,
        Payment.created_at >= month_start
    ).scalar() or 0
    
    # Citas de hoy
    today_appointments = db.query(func.count(Appointment.id)).filter(
        Appointment.organization_id == org_id,
        func.date(Appointment.date) == today,
        Appointment.status != "cancelled"
    ).scalar()
    
    # Tasa de morosidad
    overdue_invoices = db.query(func.count(Invoice.id)).filter(
        Invoice.organization_id == org_id,
        Invoice.status == "pending",
        Invoice.due_date < datetime.utcnow()
    ).scalar()
    
    total_invoices = db.query(func.count(Invoice.id)).filter(
        Invoice.organization_id == org_id
    ).scalar()
    
    delinquency_rate = (overdue_invoices / total_invoices * 100) if total_invoices > 0 else 0
    
    return {
        "clients": {
            "total": total_clients,
            "new_this_month": 0  # TODO: Implementar
        },
        "finance": {
            "total_debt": total_debt,
            "monthly_collected": monthly_collected,
            "delinquency_rate": round(delinquency_rate, 2)
        },
        "appointments": {
            "today": today_appointments,
            "this_week": 0  # TODO: Implementar
        },
        "quick_stats": [
            {"label": "Clientes", "value": total_clients, "icon": "users"},
            {"label": "Por Cobrar", "value": f"${total_debt:,.2f}", "icon": "dollar"},
            {"label": "Citas Hoy", "value": today_appointments, "icon": "calendar"},
            {"label": "Morosidad", "value": f"{delinquency_rate:.1f}%", "icon": "alert"}
        ]
    }

@router.get("/revenue-chart")
async def get_revenue_chart(
    days: int = 30,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener gráfica de ingresos"""
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Obtener pagos por día
    payments = db.query(
        func.date(Payment.created_at).label("date"),
        func.sum(Payment.amount).label("amount")
    ).join(Invoice).filter(
        Invoice.organization_id == current_user.organization_id,
        Payment.created_at >= start_date
    ).group_by(func.date(Payment.created_at)).all()
    
    # Formatear para gráfica
    chart_data = []
    current_date = start_date.date()
    
    payment_dict = {p.date: p.amount for p in payments}
    
    while current_date <= end_date.date():
        chart_data.append({
            "date": current_date.isoformat(),
            "amount": payment_dict.get(current_date, 0)
        })
        current_date += timedelta(days=1)
    
    return {
        "labels": [d["date"] for d in chart_data],
        "data": [d["amount"] for d in chart_data],
        "total": sum(d["amount"] for d in chart_data)
    }

@router.get("/top-debtors")
async def get_top_debtors(
    limit: int = 10,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener principales deudores"""
    
    debtors = db.query(
        Client.id,
        Client.name,
        Client.phone,
        func.sum(Invoice.amount).label("total_debt"),
        func.count(Invoice.id).label("pending_invoices")
    ).join(Invoice).filter(
        Client.organization_id == current_user.organization_id,
        Invoice.status == "pending"
    ).group_by(Client.id).order_by(func.sum(Invoice.amount).desc()).limit(limit).all()
    
    return [
        {
            "client_id": d.id,
            "name": d.name,
            "phone": d.phone,
            "total_debt": d.total_debt,
            "pending_invoices": d.pending_invoices
        }
        for d in debtors
    ]

@router.get("/financial-report")
async def get_financial_report(
    month: Optional[int] = None,
    year: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener reporte financiero"""
    
    # Usar mes y año actuales si no se especifican
    if not month or not year:
        now = datetime.now()
        month = month or now.month
        year = year or now.year
    
    # Calcular rango de fechas
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Ingresos
    income = db.query(func.sum(Payment.amount)).join(Invoice).filter(
        Invoice.organization_id == current_user.organization_id,
        Payment.created_at >= start_date,
        Payment.created_at < end_date
    ).scalar() or 0
    
    # Gastos (si se registran en Transaction)
    expenses = db.query(func.sum(Transaction.amount)).filter(
        Transaction.organization_id == current_user.organization_id,
        Transaction.type == "expense",
        Transaction.date >= start_date,
        Transaction.date < end_date
    ).scalar() or 0
    
    # Facturas emitidas
    invoices_issued = db.query(func.sum(Invoice.amount)).filter(
        Invoice.organization_id == current_user.organization_id,
        Invoice.created_at >= start_date,
        Invoice.created_at < end_date
    ).scalar() or 0
    
    # Tasa de cobro
    invoices_paid = db.query(func.sum(Invoice.amount)).filter(
        Invoice.organization_id == current_user.organization_id,
        Invoice.status == "paid",
        Invoice.created_at >= start_date,
        Invoice.created_at < end_date
    ).scalar() or 0
    
    collection_rate = (invoices_paid / invoices_issued * 100) if invoices_issued > 0 else 0
    
    return {
        "period": f"{month}/{year}",
        "income": income,
        "expenses": expenses,
        "net_profit": income - expenses,
        "invoices_issued": invoices_issued,
        "collection_rate": round(collection_rate, 2),
        "breakdown": {
            "payment_methods": {
                "card": 0,  # TODO: Implementar desglose por método
                "cash": 0,
                "transfer": 0,
                "oxxo": 0
            }
        }
    }

@router.get("/activity-log")
async def get_activity_log(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtener log de actividad reciente"""
    
    # Por ahora, mostrar últimos pagos y citas
    recent_payments = db.query(Payment).join(Invoice).filter(
        Invoice.organization_id == current_user.organization_id
    ).order_by(Payment.created_at.desc()).limit(10).all()
    
    recent_appointments = db.query(Appointment).filter(
        Appointment.organization_id == current_user.organization_id
    ).order_by(Appointment.created_at.desc()).limit(10).all()
    
    activities = []
    
    for payment in recent_payments:
        activities.append({
            "type": "payment",
            "description": f"Pago recibido de ${payment.amount:.2f}",
            "client": payment.client.name if payment.client else "Unknown",
            "timestamp": payment.created_at
        })
    
    for appointment in recent_appointments:
        activities.append({
            "type": "appointment",
            "description": f"Cita agendada: {appointment.service}",
            "client": appointment.client.name if appointment.client else "Unknown",
            "timestamp": appointment.created_at
        })
    
    # Ordenar por timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return activities[:limit]