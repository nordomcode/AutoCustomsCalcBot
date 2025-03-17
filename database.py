from sqlalchemy import create_engine, Column, Integer, String, DateTime, Numeric, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

# Создаем URL для подключения к базе данных
DATABASE_URL = f"postgresql://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}@{os.getenv('POSTGRES_HOST')}/{os.getenv('POSTGRES_DB')}"

# Создаем движок SQLAlchemy
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    telegram_id = Column(Integer, primary_key=True)
    username = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Calculation(Base):
    __tablename__ = "calculations"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, ForeignKey("users.telegram_id"))
    vehicle_type = Column(String(50))
    engine_type = Column(String(50))
    price = Column(Numeric(15, 2))
    currency = Column(String(10))
    age_category = Column(String(50))
    calculation_result = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

# Создаем таблицы
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 