from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import QuestionnaireResponse
from backend.routes.auth_routes import get_current_user
from backend.services.meal_planner import generate_meal_plan

router = APIRouter(prefix="/api/meals", tags=["meals"])


@router.get("/plan")
def get_daily_meal_plan(
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    questionnaire = db.query(QuestionnaireResponse).filter(
        QuestionnaireResponse.user_id == user.id
    ).first()

    if not questionnaire:
        raise HTTPException(status_code=400, detail="Please complete the questionnaire first")

    plan = generate_meal_plan(questionnaire)
    return plan
