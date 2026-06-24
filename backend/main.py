from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import engine, Base, ensure_database_schema
from backend.routes.auth_routes import router as auth_router
from backend.routes.questionnaire_routes import router as questionnaire_router
from backend.routes.supplement_routes import router as supplement_router
from backend.routes.health_routes import router as health_router
from backend.routes.meal_routes import router as meal_router
from backend.routes.chat_routes import router as chat_router

# Create tables
Base.metadata.create_all(bind=engine)
ensure_database_schema()

app = FastAPI(
    title="NutriMatch API",
    description="Personalized supplement recommendation platform",
    version="1.0.0",
)

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(questionnaire_router)
app.include_router(supplement_router)
app.include_router(health_router)
app.include_router(meal_router)
app.include_router(chat_router)


@app.get("/api/health-check")
def health_check():
    return {"status": "ok", "version": "1.0.0"}
