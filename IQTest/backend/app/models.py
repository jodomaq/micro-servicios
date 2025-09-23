from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base  # Cambiado para importación correcta en producción

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    responses = relationship("Response", back_populates="user")
    results = relationship("Result", back_populates="user")
    payments = relationship("Payment", back_populates="user")

class Question(Base):
    __tablename__ = "questions"
    
    id = Column(Integer, primary_key=True, index=True)
    text = Column(Text, nullable=False)
    question_type = Column(String(50), nullable=False)  # verbal, logical, numerical, etc.
    options = Column(Text, nullable=True)  # JSON serializado de opciones
    correct_answer = Column(String(255), nullable=True)
    difficulty = Column(Float, default=1.0)
    
    # Relaciones
    responses = relationship("Response", back_populates="question")

class Response(Base):
    __tablename__ = "responses"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer = Column(String(255), nullable=False)
    # Nota: Eliminado response_time_ms para compatibilidad con esquemas existentes
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="responses")
    question = relationship("Question", back_populates="responses")

class Result(Base):
    __tablename__ = "results"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    iq_score = Column(Integer, nullable=False)
    strengths = Column(Text, nullable=True)
    weaknesses = Column(Text, nullable=True)
    detailed_report = Column(Text, nullable=True)  # JSON serializado
    certificate_url = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="results")

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    paypal_order_id = Column(String(255), nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="MXN")
    status = Column(String(50), nullable=False)  # completed, pending, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    user = relationship("User", back_populates="payments")
