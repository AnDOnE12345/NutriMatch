from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    email: str
    password: str
    full_name: Optional[str] = None
    language: str = "de"


class LoginRequest(BaseModel):
    email: str
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    language: str
    subscription_tier: str
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


class QuestionnaireSubmit(BaseModel):
    age: Optional[int] = None
    gender: Optional[str] = None
    height_cm: Optional[float] = None
    weight_kg: Optional[float] = None
    activity_level: Optional[str] = None
    sleep_hours: Optional[float] = None
    stress_level: Optional[str] = None
    smoking: bool = False
    alcohol_frequency: Optional[str] = None
    diet_type: Optional[str] = None
    meals_per_day: Optional[int] = None
    water_intake_liters: Optional[float] = None
    goals: list[str] = []
    allergies: list[str] = []
    preferred_form: Optional[str] = None
    budget_monthly: Optional[float] = None
    food_budget_monthly: Optional[float] = None
    prefer_organic: bool = False
    prefer_fairtrade: bool = False
    existing_conditions: list[str] = []
    current_medications: list[str] = []


class HealthDataSubmit(BaseModel):
    source: str
    data_type: str
    value: dict
    recorded_at: Optional[datetime] = None


class ChatHistoryItem(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str = Field(min_length=1, max_length=2500)


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=800)
    provider: str = Field(default="local", pattern="^(local|gemini|groq)$")
    history: list[ChatHistoryItem] = Field(default_factory=list, max_length=8)


class SupplementResponse(BaseModel):
    id: int
    name: str
    brand: Optional[str]
    category: str
    form: Optional[str]
    price: Optional[float]
    currency: str
    shop_name: Optional[str]
    shop_url: Optional[str]
    is_vegan: bool
    is_organic: bool
    evidence_level: Optional[str]
    description_de: Optional[str]
    description_en: Optional[str]

    class Config:
        from_attributes = True


class RecommendationResponse(BaseModel):
    id: int
    supplements: list
    reasoning: dict
    score: float
    created_at: datetime

    class Config:
        from_attributes = True
