import os
from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker
from datetime import datetime

# Read from env so Docker can override it
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/lostnfound.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Item(Base):
    __tablename__ = "items"

    id           = Column(Integer, primary_key=True, index=True)
    code         = Column(String(20), unique=True, index=True, nullable=False)
    title        = Column(String(200), nullable=False)
    description  = Column(Text, nullable=True)
    status       = Column(String(10), nullable=False, default="FOUND")
    location     = Column(String(300), nullable=True)
    image_url    = Column(String(500), nullable=True)
    reporter_name = Column(String(200), nullable=True)
    reporter_contact = Column(String(50), nullable=True)
    is_approved = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)
    updated_at   = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"

    id            = Column(Integer, primary_key=True, index=True)
    username      = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at    = Column(DateTime, default=datetime.utcnow)


class ClaimRequest(Base):
    __tablename__ = "claim_requests"

    id               = Column(Integer, primary_key=True, index=True)
    item_id          = Column(Integer, nullable=False) # Hubungkan ke ID barang
    claimer_name     = Column(String(200), nullable=False)
    claimer_class    = Column(String(50), nullable=False)
    contact_number   = Column(String(20), nullable=False)
    proof_description = Column(Text, nullable=False)
    proof_image_url = Column(String(500), nullable=True)
    status           = Column(String(20), default="PENDING") # PENDING, APPROVED, REJECTED
    rfid_uid         = Column(String(100), nullable=True)
    created_at       = Column(DateTime, default=datetime.utcnow)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Make sure the data directory exists when using a path-based SQLite URL
    if DATABASE_URL.startswith("sqlite:///./data/"):
        os.makedirs("data", exist_ok=True)
    Base.metadata.create_all(bind=engine)
