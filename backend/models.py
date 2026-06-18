from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from backend.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    language = Column(String, default="de")  # "de" or "en"
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    subscription_tier = Column(String, default="free")  # free, basic, premium

    questionnaire = relationship("QuestionnaireResponse", back_populates="user", uselist=False)
    health_data = relationship("HealthData", back_populates="user")
    recommendations = relationship("Recommendation", back_populates="user")


class QuestionnaireResponse(Base):
    __tablename__ = "questionnaire_responses"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Basic info
    age = Column(Integer)
    gender = Column(String)
    height_cm = Column(Float)
    weight_kg = Column(Float)
    
    # Lifestyle
    activity_level = Column(String)  # sedentary, light, moderate, active, very_active
    sleep_hours = Column(Float)
    stress_level = Column(String)  # low, moderate, high
    smoking = Column(Boolean, default=False)
    alcohol_frequency = Column(String)  # never, rarely, moderate, frequent
    
    # Diet
    diet_type = Column(String)  # omnivore, vegetarian, vegan, pescatarian, keto, paleo
    meals_per_day = Column(Integer)
    water_intake_liters = Column(Float)
    
    # Health goals
    goals = Column(JSON)  # ["energy", "sleep", "immunity", "muscle", "weight_loss", ...]
    
    # Allergies & intolerances
    allergies = Column(JSON)  # ["gluten", "lactose", "soy", "nuts", ...]
    
    # Preferences
    preferred_form = Column(String)  # capsule, tablet, powder, liquid, gummy
    budget_monthly = Column(Float)
    food_budget_monthly = Column(Float)  # monthly food/grocery budget in EUR
    prefer_organic = Column(Boolean, default=False)
    prefer_fairtrade = Column(Boolean, default=False)
    
    # Medical
    existing_conditions = Column(JSON)  # ["diabetes", "thyroid", ...]
    current_medications = Column(JSON)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="questionnaire")


class HealthData(Base):
    __tablename__ = "health_data"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    source = Column(String)  # "smartwatch", "fitness_app", "lab_results", "manual"
    data_type = Column(String)  # "steps", "sleep", "heart_rate", "blood_test", ...
    value = Column(JSON)
    recorded_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="health_data")


class Supplement(Base):
    __tablename__ = "supplements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    brand = Column(String)
    category = Column(String)  # vitamin, mineral, amino_acid, herbal, omega, probiotic
    
    # Product details
    ingredients = Column(JSON)
    dosage = Column(String)
    form = Column(String)  # capsule, tablet, powder, liquid, gummy
    serving_size = Column(String)
    servings_per_container = Column(Integer)
    
    # Pricing
    price = Column(Float)
    currency = Column(String, default="EUR")
    shop_url = Column(String)
    shop_name = Column(String)
    
    # Quality
    certifications = Column(JSON)  # ["organic", "fairtrade", "gmp", "nsf", ...]
    allergens = Column(JSON)  # ["gluten", "soy", "dairy", ...]
    is_vegan = Column(Boolean, default=False)
    is_organic = Column(Boolean, default=False)
    
    # Scientific backing
    evidence_level = Column(String)  # "strong", "moderate", "emerging", "limited"
    description_de = Column(Text)
    description_en = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    supplements = Column(JSON)  # List of supplement IDs with dosage recommendations
    reasoning = Column(JSON)  # Explanation for each recommendation
    score = Column(Float)  # Overall match score
    
    created_at = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="recommendations")
