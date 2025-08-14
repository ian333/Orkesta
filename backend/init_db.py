"""
Script para inicializar la base de datos
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models import init_db, SessionLocal, Organization, User
from passlib.context import CryptContext
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password):
    return pwd_context.hash(password)

def create_demo_data():
    """Crear datos de demostración"""
    db = SessionLocal()
    
    try:
        # Verificar si ya existe data
        existing_org = db.query(Organization).first()
        if existing_org:
            logger.info("La base de datos ya contiene datos")
            return
        
        # Crear organización demo
        demo_org = Organization(
            name="Consultorio Demo",
            type="consultorio",
            phone="+525512345678",
            email="demo@clienteos.mx",
            address="Calle Principal 123, CDMX"
        )
        db.add(demo_org)
        db.flush()
        
        # Crear usuario demo
        demo_user = User(
            organization_id=demo_org.id,
            email="demo@clienteos.mx",
            password_hash=get_password_hash("demo123"),
            name="Usuario Demo",
            phone="+525512345678",
            role="admin"
        )
        db.add(demo_user)
        
        db.commit()
        logger.info("✅ Datos de demostración creados")
        logger.info("📧 Email: demo@clienteos.mx")
        logger.info("🔑 Password: demo123")
        
    except Exception as e:
        logger.error(f"Error creando datos de demo: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("Inicializando base de datos...")
    init_db()
    create_demo_data()
    logger.info("✅ Base de datos lista")