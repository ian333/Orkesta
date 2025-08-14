"""
Modelos de base de datos simplificados
"""
from sqlalchemy import create_engine, Column, String, Integer, Float, DateTime, Boolean, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime
import os

Base = declarative_base()

# ========== USUARIOS Y ORGANIZACIONES ==========

class Organization(Base):
    """Organización/Negocio que usa ClienteOS"""
    __tablename__ = "organizations"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    type = Column(String(50))  # consultorio, tienda, servicio, etc
    phone = Column(String(20))
    email = Column(String(100))
    address = Column(Text)
    
    # Configuración
    settings = Column(JSON, default={})
    stripe_account_id = Column(String(100))
    wa_connected = Column(Boolean, default=False)
    
    # Relaciones
    users = relationship("User", back_populates="organization")
    clients = relationship("Client", back_populates="organization")
    invoices = relationship("Invoice", back_populates="organization")
    appointments = relationship("Appointment", back_populates="organization")
    
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    """Usuarios del sistema"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    
    email = Column(String(100), unique=True, nullable=False)
    phone = Column(String(20))
    password_hash = Column(String(255))
    name = Column(String(100))
    role = Column(String(20), default="admin")  # admin, staff, viewer
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="users")

# ========== CLIENTES ==========

class Client(Base):
    """Clientes del negocio"""
    __tablename__ = "clients"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    email = Column(String(100))
    address = Column(Text)
    notes = Column(Text)
    
    # Para consultorios
    birth_date = Column(DateTime)
    medical_history = Column(JSON, default={})
    
    # Estado de cuenta
    balance = Column(Float, default=0.0)
    total_debt = Column(Float, default=0.0)
    
    # WhatsApp
    wa_opted_in = Column(Boolean, default=False)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="clients")
    invoices = relationship("Invoice", back_populates="client")
    payments = relationship("Payment", back_populates="client")
    appointments = relationship("Appointment", back_populates="client")

# ========== COBROS Y PAGOS ==========

class Invoice(Base):
    """Facturas/Cuentas por cobrar"""
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    
    number = Column(String(50))
    amount = Column(Float, nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)
    status = Column(String(20), default="pending")  # pending, paid, overdue, cancelled
    
    # Links de pago
    payment_link = Column(String(255))
    stripe_payment_intent_id = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime)
    
    organization = relationship("Organization", back_populates="invoices")
    client = relationship("Client", back_populates="invoices")
    payments = relationship("Payment", back_populates="invoice")

class Payment(Base):
    """Pagos recibidos"""
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    
    amount = Column(Float, nullable=False)
    method = Column(String(50))  # card, cash, transfer, oxxo
    reference = Column(String(100))
    stripe_charge_id = Column(String(100))
    
    status = Column(String(20), default="completed")
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    invoice = relationship("Invoice", back_populates="payments")
    client = relationship("Client", back_populates="payments")

# ========== CITAS (PARA CONSULTORIOS) ==========

class Appointment(Base):
    """Citas para consultorios"""
    __tablename__ = "appointments"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    client_id = Column(Integer, ForeignKey("clients.id"))
    
    date = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=30)
    service = Column(String(100))
    price = Column(Float)
    
    status = Column(String(20), default="scheduled")  # scheduled, confirmed, completed, cancelled
    notes = Column(Text)
    
    # Recordatorios
    reminder_sent = Column(Boolean, default=False)
    reminder_sent_at = Column(DateTime)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="appointments")
    client = relationship("Client", back_populates="appointments")

# ========== PRODUCTOS/SERVICIOS ==========

class Product(Base):
    """Productos o servicios que vende el negocio"""
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    
    name = Column(String(100), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    category = Column(String(50))
    
    # Para inventario
    stock = Column(Integer, default=0)
    min_stock = Column(Integer, default=0)
    
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# ========== FINANZAS ==========

class Transaction(Base):
    """Transacciones financieras del negocio"""
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    organization_id = Column(Integer, ForeignKey("organizations.id"))
    
    type = Column(String(20))  # income, expense
    category = Column(String(50))  # ventas, gastos_operativos, nomina, etc
    amount = Column(Float, nullable=False)
    description = Column(Text)
    date = Column(DateTime, default=datetime.utcnow)
    
    # Referencias
    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)

# ========== CONVERSACIONES WHATSAPP ==========

class WhatsAppConversation(Base):
    """Conversaciones de WhatsApp"""
    __tablename__ = "whatsapp_conversations"
    
    id = Column(Integer, primary_key=True)
    phone_number = Column(String(20), nullable=False)
    client_id = Column(Integer, ForeignKey("clients.id"), nullable=True)
    
    last_message = Column(Text)
    last_message_at = Column(DateTime)
    status = Column(String(20), default="active")  # active, closed, pending
    
    # Para ventas del sistema
    is_lead = Column(Boolean, default=False)
    lead_status = Column(String(20))  # interested, demo, negotiating, closed
    
    context = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)

# ========== CONFIGURACIÓN DE BASE DE DATOS ==========

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./orkesta.db")

# Detectar si es SQLite o PostgreSQL
if DATABASE_URL.startswith("sqlite"):
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """Obtener sesión de base de datos"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Inicializar base de datos"""
    Base.metadata.create_all(bind=engine)
    print("✅ Base de datos inicializada")