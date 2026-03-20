from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

# Esquemas para User
class UserBase(BaseModel):
    email: Optional[str] = None
    name: Optional[str] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None

class User(UserBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

# Esquemas para Question
class QuestionBase(BaseModel):
    text: str
    question_type: str
    options: List[str]
    correct_answer: Optional[str] = None
    difficulty: float = 1.0

class QuestionCreate(QuestionBase):
    pass

class Question(QuestionBase):
    id: int
    
    class Config:
        orm_mode = True

# Esquemas para Answer/Response
class AnswerBase(BaseModel):
    questionId: int
    answer: str
    time_ms: int | None = None  # tiempo que tardó el usuario en contestar (ms)

class Answer(AnswerBase):
    pass

class AnswerList(BaseModel):
    answers: List[Answer]

# Esquemas para Result
class ResultBase(BaseModel):
    user_id: int
    iq_score: int
    strengths: str  # JSON serializado
    weaknesses: str  # JSON serializado
    detailed_report: str  # JSON serializado
    certificate_url: Optional[str] = None

class ResultCreate(ResultBase):
    pass

class Result(ResultBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True

class ResultResponse(BaseModel):
    iq_score: int
    strengths: List[str]
    weaknesses: List[str]
    detailed_report: Dict[str, Any]
    certificate_url: Optional[str] = None

# Esquemas para Payment
class PaypalPayment(BaseModel):
    orderID: str
    user_id: int
    amount: float = 1.0
    currency: str = "USD"
    status: str = "completed"

class PaymentBase(BaseModel):
    user_id: int
    paypal_order_id: str
    amount: float
    currency: str = "USD"
    status: str

class PaymentCreate(PaymentBase):
    pass

class Payment(PaymentBase):
    id: int
    created_at: datetime
    
    class Config:
        orm_mode = True
