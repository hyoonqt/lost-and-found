import os
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Text,
    DateTime,
    Boolean,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime
from dotenv import load_dotenv


load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/lostnfound.db")

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
    if "sqlite" in SQLALCHEMY_DATABASE_URL
    else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(String(10), nullable=False, default="FOUND")
    location = Column(String(300), nullable=True)
    image_url = Column(String(500), nullable=True)
    reporter_name = Column(String(200), nullable=True)
    reporter_contact = Column(String(50), nullable=True)
    is_approved = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ClaimRequest(Base):
    __tablename__ = "claim_requests"

    id = Column(Integer, primary_key=True, index=True)
    item_id = Column(Integer, nullable=False)
    claimer_name = Column(String(200), nullable=False)
    claimer_class = Column(String(50), nullable=False)
    contact_number = Column(String(20), nullable=False)
    proof_description = Column(Text, nullable=False)
    proof_image_url = Column(String(500), nullable=True)
    status = Column(String(20), default="PENDING")
    rfid_uid = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)
    rfid_uid = Column(String(100), unique=True, index=True, nullable=False)
    nis = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=True)
    grade_class = Column(String(50), nullable=True)
    contact = Column(String(50), nullable=True)


class ActivityLog(Base):
    __tablename__ = "activity_logs"

    id = Column(Integer, primary_key=True, index=True)
    activity_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


# INI MODEL YANG HILANG DI DATABASE.PY LOKALMU SEKARANG
class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    message = Column(String(255), nullable=False)
    is_read = Column(Boolean, default=False)
    link = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    if SQLALCHEMY_DATABASE_URL.startswith("sqlite:///./data/"):
        os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
